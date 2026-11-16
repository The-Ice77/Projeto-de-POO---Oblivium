# src/mechanics/combat/combat_ai.py
"""Controlador de rodadas, IA de turno dos inimigos, fuga e desfecho de combate."""

import random

from src.core.audio_manager import AudioManager
from src.entities.Boss import Boss
from src.entities.player import Player
from src.mechanics.combat.combat_narrator import CombatNarrator
from src.mechanics.rpg import SkillsRegistry
from src.utils.colors import (
    BARRA_MANA,
    BARRA_VIDA_INIMIGO,
    BARRA_VIDA_JOGADOR,
    TEXTO_ALERTA_COMBATE,
)


class CombatAIController:
    """Gerencia a ordem de turnos, decisões dos inimigos, tentativas de fuga e resolução pós-combate."""

    def __init__(self, screen):
        self.screen = screen

    def iniciar_nova_rodada(self):
        """Prepara a rodada mantendo a ordem consistente de turnos entre participantes vivos."""
        s = self.screen
        s.ordem_turnos = [p for p in s.ordem_turnos_base if getattr(p, "vivo", True)]
        s.indice_turno_atual = 0
        s._avancar_para_proximo_turno()

    def avancar_para_proximo_turno(self):
        """Avança a vez para a próxima entidade viva da fila."""
        s = self.screen

        # 1. Verifica se todos os inimigos foram derrotados
        inimigos_vivos = s._obter_inimigos_vivos()
        if not inimigos_vivos:
            s._finalizar_vitoria()
            return

        # 2. Verifica se o jogador foi derrotado
        if not getattr(s.jogador, "vivo", True) or s.jogador.vida_atual <= 0:
            s._finalizar_derrota()
            return

        # 3. Se a rodada acabou, começa nova rodada mantendo a consistência dos turnos
        if s.indice_turno_atual >= len(s.ordem_turnos):
            s._iniciar_nova_rodada()
            return

        entidade_atual = s.ordem_turnos[s.indice_turno_atual]

        # Pula entidades mortas
        if not getattr(entidade_atual, "vivo", True):
            s.indice_turno_atual += 1
            s._avancar_para_proximo_turno()
            return

        # Reseta postura temporária apenas no início do turno da própria entidade
        if hasattr(entidade_atual, "resetar_turno_combate"):
            entidade_atual.resetar_turno_combate()

        # 4. Processa Condições / DoT / CC no início do turno
        if hasattr(entidade_atual, "processar_condicoes_inicio_turno"):
            relatorios, impede_acao = entidade_atual.processar_condicoes_inicio_turno()
            for r in relatorios:
                if r.get("mensagem"):
                    s.adicionar_log(r["mensagem"])
                if r.get("dano", 0) > 0:
                    ex, ey = s._obter_posicao_combate(entidade_atual)
                    s.adicionar_texto_flutuante(f"-{r['dano']}", ex + 20, ey, TEXTO_ALERTA_COMBATE)
                    s.shake_timers[entidade_atual] = 8
                    if entidade_atual is s.jogador:
                        s._disparar_sangue_halia()

            if not getattr(entidade_atual, "vivo", True):
                if entidade_atual is not s.jogador and hasattr(entidade_atual, "animacoes"):
                    entidade_atual.morrer()
                    est_m = (
                        "dead"
                        if "dead" in entidade_atual.animacoes
                        else ("morte" if "morte" in entidade_atual.animacoes else "morrer")
                    )
                    if est_m in entidade_atual.animacoes:
                        entidade_atual.definir_estado(est_m)
                        if hasattr(entidade_atual.animacoes[est_m], "resetar"):
                            entidade_atual.animacoes[est_m].resetar()
                    s.alphas_morte[entidade_atual] = 255
                msg_morte = s._gerar_mensagem_morte_condicao(entidade_atual, relatorios)
                s.adicionar_log(msg_morte)
                s.indice_turno_atual += 1
                s._avancar_para_proximo_turno()
                return

            if entidade_atual is not s.jogador:
                self.verificar_e_anunciar_mudanca_fase(entidade_atual)

            if impede_acao:
                if getattr(entidade_atual, "preparando_sopro", False):
                    entidade_atual.preparando_sopro = False
                    s.adicionar_log(
                        f"{entidade_atual.nome} perdeu a concentração e teve o sopro interrompido!"
                    )
                # Dá tempo para o jogador ler que a entidade perdeu o turno
                s.timer_acao = s._ajustar_timer(70)
                s.estado_combate = "EXECUTANDO_ACAO"
                return

        # 5. Define se é turno do Jogador ou IA do Inimigo
        if entidade_atual is s.jogador:
            # Regeneração passiva natural de mana por turno da Grã-Maga
            if s.jogador.mana_atual < s.jogador.mana_maxima:
                attrs_jog = (
                    s.jogador.obter_atributos_efetivos()
                    if hasattr(s.jogador, "obter_atributos_efetivos")
                    else s.jogador.atributos
                )
                mana_reg = min(4, max(2, 2 + (attrs_jog.mod_sab // 2)))
                s.jogador.recuperar_mana(mana_reg)
                hx, hy = s._obter_posicao_combate(s.jogador)
                s.adicionar_texto_flutuante(f"+{mana_reg} MP", hx + 30, hy + 15, BARRA_MANA, duracao=60)

            s.estado_combate = "MENU_PRINCIPAL"
            s.indice_menu = 0
        else:
            # Regeneração passiva natural de mana por turno do Inimigo conforme os turnos avançam
            mana_atual = getattr(entidade_atual, "mana_atual", 0)
            mana_max = getattr(entidade_atual, "mana_maxima", 20)
            if mana_atual < mana_max and hasattr(entidade_atual, "recuperar_mana"):
                attrs_ini = (
                    entidade_atual.obter_atributos_efetivos()
                    if hasattr(entidade_atual, "obter_atributos_efetivos")
                    else getattr(entidade_atual, "atributos", None)
                )
                if attrs_ini and hasattr(attrs_ini, "calcular_regeneracao_mana"):
                    bonus_chefe = (
                        2
                        if (isinstance(entidade_atual, Boss) or getattr(entidade_atual, "eh_chefe", False))
                        else 0
                    )
                    mana_reg = attrs_ini.calcular_regeneracao_mana(base=3 + bonus_chefe)
                else:
                    mod_sab = getattr(attrs_ini, "mod_sab", 0) if attrs_ini else 0
                    mod_pre = getattr(attrs_ini, "mod_pre", 0) if attrs_ini else 0
                    bonus_chefe = (
                        2
                        if (isinstance(entidade_atual, Boss) or getattr(entidade_atual, "eh_chefe", False))
                        else 0
                    )
                    mana_reg = max(3, 3 + mod_sab + (mod_pre // 2) + bonus_chefe)

                mana_efetiva = min(mana_max - mana_atual, mana_reg)
                entidade_atual.recuperar_mana(mana_reg)
                ex, ey = s._obter_posicao_combate(entidade_atual)
                s.adicionar_texto_flutuante(f"+{int(mana_efetiva)} MP", ex + 30, ey + 15, BARRA_MANA, duracao=60)

            s.estado_combate = "TURNO_INIMIGO"
            s.timer_acao = s._ajustar_timer(55)

    def verificar_e_anunciar_mudanca_fase(self, entidade):
        """Aciona a Fase 2 em chefes <= 50% HP e anuncia no log e tela."""
        if (
            entidade is not None
            and getattr(entidade, "vivo", False)
            and hasattr(entidade, "verificar_mudanca_fase")
            and entidade.verificar_mudanca_fase()
        ):
            s = self.screen
            ex, ey = s._obter_posicao_combate(entidade)
            s.adicionar_log(
                f"✦ {entidade.nome} despertou sua FÚRIA (Fase 2)! (+15% de Poder)"
            )
            s.adicionar_texto_flutuante(
                "FASE 2: FÚRIA!", ex - 50, ey - 45, (255, 190, 70), duracao=95
            )
            s.shake_timers[entidade] = 16
            return True
        return False

    @staticmethod
    def selecionar_acao_inimigo(inimigo):
        """Seleciona a ação real do inimigo ou chefe usando regras do bestiário e custo de mana."""
        if hasattr(inimigo, "decidir_acao_ia"):
            return inimigo.decidir_acao_ia()

        kit = getattr(inimigo, "habilidades", ["garras_sombrias", "golpe_sombrio"])
        acoes_disponiveis = []
        for id_hab in kit:
            acao_cand = SkillsRegistry.get(id_hab)
            if acao_cand and acao_cand.pode_usar(inimigo):
                acoes_disponiveis.append(acao_cand)

        # IA Tática de Mana: se o monstro/chefe possui magias no kit, mas está sem mana suficiente,
        # possui uma chance de canalizar energia (Concentrar) para recarregar mana
        if hasattr(inimigo, "atributos") and (
            isinstance(inimigo, Boss)
            or getattr(inimigo, "eh_chefe", False)
            or getattr(inimigo.atributos, "intelecto", 0) >= 12
        ):
            tem_magia_kit = any(getattr(SkillsRegistry.get(h), "custo_mana", 0) > 0 for h in kit)
            if tem_magia_kit and getattr(inimigo, "mana_atual", 0) < 10 and random.random() < 0.25:
                foco_cand = SkillsRegistry.get("concentrar")
                if foco_cand:
                    acoes_disponiveis.append(foco_cand)

        if acoes_disponiveis:
            magias_com_custo = [a for a in acoes_disponiveis if a.custo_mana > 0]
            if magias_com_custo and random.random() < 0.65:
                return random.choice(magias_com_custo)
            return random.choice(acoes_disponiveis)

        return (
            SkillsRegistry.get("garras_sombrias")
            or SkillsRegistry.get("golpe_sombrio")
            or SkillsRegistry.get("investida_sombria")
            or SkillsRegistry.get("ataque_basico")
        )

    def executar_turno_inimigo(self, inimigo):
        """IA do inimigo: seleciona habilidade temática e executa contra Halia."""
        s = self.screen
        s.estado_combate = "EXECUTANDO_ACAO"
        s.timer_acao = s._ajustar_timer(75)

        decisao = self.selecionar_acao_inimigo(inimigo)
        if decisao == "PREPARAR_SOPRO":
            ix, iy = s._obter_posicao_combate(inimigo)
            s.adicionar_log(
                f"[!] {inimigo.nome} está inspirando chamas profundas... PREPARE-SE!"
            )
            s.adicionar_texto_flutuante(
                "PREPARANDO SOPRO!", ix - 50, iy - 50, (255, 200, 110), duracao=95
            )
            s.shake_timers[inimigo] = 14
            return
        acao = decisao

        # Alvo apropriado conforme o tipo da habilidade
        alvo_acao = (
            inimigo
            if getattr(acao, "tipo_alvo", "") in ["proprio", "aliado"]
            or getattr(acao, "alvo_tipo", "") in ["PROPRIO", "ALIADO"]
            else s.jogador
        )

        # Ativa animação de ataque no inimigo
        if hasattr(inimigo, "definir_estado") and hasattr(inimigo, "animacoes"):
            if "attack" in inimigo.animacoes or "ataque" in inimigo.animacoes:
                est_a = "attack" if "attack" in inimigo.animacoes else "ataque"
                inimigo.definir_estado(est_a)
                if hasattr(inimigo.animacoes[est_a], "resetar"):
                    inimigo.animacoes[est_a].resetar()

        resultado = acao.executar(inimigo, alvo_acao)

        nome_ini_l = str(getattr(inimigo, "nome", "")).lower()
        eh_dragao_ini = ("drag" in nome_ini_l or "ignis" in nome_ini_l)
        if eh_dragao_ini:
            s._tocar_sfx("rugido_monstro")
        elif "slime" in nome_ini_l:
            s._tocar_sfx("slime")
        if getattr(acao, "custo_mana", 0) > 0 or getattr(acao, "tipo", "").upper() == "MAGIA" or getattr(acao, "tipo_dano", "") == "MAGICO":
            s._tocar_sfx_elemento(getattr(acao, "elemento", "ARCANO"), eh_dragao=eh_dragao_ini)

        if resultado.get("mensagem"):
            s.adicionar_log(resultado["mensagem"])

        # Redundância imediata no Log: garante que 100% das ações e ataques dos inimigos e do Dragão aparecem no histórico
        for r_entry in resultado.get("resultados", []):
            r_data = r_entry.get("dados") if ("dados" in r_entry and isinstance(r_entry["dados"], dict)) else r_entry
            msg_alvo = r_data.get("mensagem")
            if not msg_alvo:
                alvo_obj = r_data.get("alvo", alvo_acao)
                alvo_nome = getattr(alvo_obj, "nome", "Halia")
                if r_data.get("errou"):
                    if r_data.get("motivo") == "esquiva":
                        msg_alvo = f"{inimigo.nome} usou {acao.nome}, mas {alvo_nome} se esquivou agilmente!"
                    else:
                        msg_alvo = f"{inimigo.nome} usou {acao.nome}, mas errou o ataque contra {alvo_nome}!"
                elif r_data.get("dano", 0) > 0:
                    crit_txt = " (CRÍTICO!)" if r_data.get("critico") else ""
                    dano_str = CombatNarrator.formatar_numero(r_data['dano'])
                    msg_alvo = f"{inimigo.nome} usou {acao.nome} em {alvo_nome} causando {dano_str} de dano{crit_txt}."
                elif r_data.get("cura", 0) > 0:
                    cura_str = CombatNarrator.formatar_numero(r_data['cura'])
                    msg_alvo = f"{inimigo.nome} usou {acao.nome} restaurando {cura_str} de vida."
            if msg_alvo:
                s.adicionar_log(msg_alvo)
                r_entry["_log_registrado"] = True
                r_data["_log_registrado"] = True

        # Feedback de mana recuperada e vulnerabilidade na própria entidade conjuradora
        mana_rec = float(resultado.get("mana_recuperada", 0) or 0)
        if mana_rec > 0:
            mana_fmt = CombatNarrator.formatar_numero(mana_rec)
            ix, iy = s._obter_posicao_combate(inimigo)
            s.adicionar_texto_flutuante(f"+{mana_fmt} MP", ix + 30, iy + 15, BARRA_MANA, duracao=80)

        if resultado.get("vulneravel"):
            ix, iy = s._obter_posicao_combate(inimigo)
            s.adicionar_texto_flutuante(
                CombatNarrator.obter_popup("vulneravel"), ix + 30, iy - 10, (240, 130, 130), duracao=80
            )

        def _aplicar_impacto_inimigo(alvo_r, r):
            if "dados" in r and isinstance(r["dados"], dict):
                r = r["dados"]
            if r.get("mensagem") and not r.get("_log_registrado") and r.get("mensagem") != resultado.get("mensagem"):
                s.adicionar_log(r["mensagem"])
                r["_log_registrado"] = True
            alvo_r = r.get("alvo", s.jogador)
            dano_r = float(r.get("dano", 0) or 0)
            cura_r = float(r.get("cura", 0) or 0)
            hx, hy = s._obter_posicao_combate(alvo_r) if alvo_r else (160, 160)

            if r.get("errou", False):
                motivo_erro = r.get("motivo", "erro")
                if motivo_erro == "esquiva":
                    s._tocar_sfx("esquiva")
                    texto_erro = CombatNarrator.obter_popup("esquivou")
                    cor_erro = (100, 210, 255)  # Cyan
                else:
                    s._tocar_sfx("ataque_erro")
                    texto_erro = CombatNarrator.obter_popup("errou")
                    cor_erro = (240, 160, 100)  # Âmbar
                s.adicionar_texto_flutuante(texto_erro, hx + 30, hy - 15, cor_erro, duracao=80)
                # Efeito visual suave de erro/falha (sem explosão de impacto ou tremor)
                elem_acao = getattr(acao, "elemento", "SOMBRA")
                s.efeitos_visuais.adicionar_dissipacao_erro(hx + 30, hy, elemento=elem_acao, motivo=motivo_erro)
            elif dano_r > 0:
                if alvo_r is s.jogador:
                    s._tocar_sfx("dano_halia")
                    s._disparar_sangue_halia()
                else:
                    s._tocar_sfx("dano_inimigo")
                if hasattr(alvo_r, "definir_estado") and hasattr(alvo_r, "animacoes"):
                    if not getattr(alvo_r, "vivo", True):
                        alvo_r.morrer()
                        est_m = (
                            "dead"
                            if "dead" in alvo_r.animacoes
                            else ("morte" if "morte" in alvo_r.animacoes else "morrer")
                        )
                        if est_m in alvo_r.animacoes:
                            alvo_r.definir_estado(est_m)
                            if hasattr(alvo_r.animacoes[est_m], "resetar"):
                                alvo_r.animacoes[est_m].resetar()
                        s.alphas_morte[alvo_r] = 255
                    elif "hurt" in alvo_r.animacoes or "dano" in alvo_r.animacoes:
                        est_h = "hurt" if "hurt" in alvo_r.animacoes else "dano"
                        alvo_r.definir_estado(est_h)
                        if hasattr(alvo_r.animacoes[est_h], "resetar"):
                            alvo_r.animacoes[est_h].resetar()

                dano_fmt = int(dano_r) if dano_r.is_integer() else f"{dano_r:.1f}"
                s.adicionar_texto_flutuante(f"-{dano_fmt}", hx + 30, hy, TEXTO_ALERTA_COMBATE)
                s.shake_timers[alvo_r] = 14
                # Feedback narrativo se Halia foi derrotada
                if alvo_r is s.jogador and not getattr(s.jogador, "vivo", True):
                    msg_morte = s._gerar_mensagem_morte_acao(s.jogador, acao)
                    s.adicionar_log(msg_morte)
            elif cura_r > 0:
                s._tocar_sfx("magia_cura")
                cura_fmt = int(cura_r) if cura_r.is_integer() else f"{cura_r:.1f}"
                cor_cura = BARRA_VIDA_JOGADOR if alvo_r is s.jogador else BARRA_VIDA_INIMIGO
                s.adicionar_texto_flutuante(f"+{cura_fmt}", hx + 30, hy - 10, cor_cura)

        eh_magia_inimigo = (
            getattr(acao, "custo_mana", 0) > 0
            or getattr(acao, "tipo", "").upper() == "MAGIA"
            or getattr(acao, "tipo_dano", "") == "MAGICO"
        )
        alvos_com_dados_inimigo = [r for r in resultado.get("resultados", []) if r.get("alvo", s.jogador)]

        if eh_magia_inimigo and alvos_com_dados_inimigo:
            s.timer_acao = s._ajustar_timer(75)
            s.efeitos_visuais.disparar_magia_aoe(
                acao, inimigo, alvos_com_dados_inimigo, on_impacto_alvo=_aplicar_impacto_inimigo
            )
        else:
            for r in resultado.get("resultados", []):
                _aplicar_impacto_inimigo(r.get("alvo", s.jogador), r)

    def tentar_fuga(self):
        """Calcula a probabilidade de fuga baseada na Destreza, quantidade e força dos inimigos."""
        s = self.screen
        inimigos_vivos = s._obter_inimigos_vivos()
        if not inimigos_vivos:
            s.estado_combate = "VITORIA"
            return

        # 1. Chefes e oponentes imponentes não permitem fuga
        hx, hy = s._obter_posicao_combate(s.jogador)
        for inimigo in inimigos_vivos:
            attrs_inimigo = (
                inimigo.obter_atributos_efetivos()
                if hasattr(inimigo, "obter_atributos_efetivos")
                else getattr(inimigo, "atributos", None)
            )
            if (
                isinstance(inimigo, Boss)
                or getattr(inimigo, "eh_chefe", False)
                or (attrs_inimigo is not None and attrs_inimigo.forca >= 28)
            ):
                s._tocar_sfx("ui_erro")
                s.adicionar_log(CombatNarrator.obter_mensagem("fuga_impossivel"))
                s.adicionar_texto_flutuante(
                    CombatNarrator.obter_popup("fuga_impossivel"),
                    hx + 20,
                    hy - 15,
                    TEXTO_ALERTA_COMBATE,
                    duracao=75,
                )
                s.timer_acao = s._ajustar_timer(60)
                s.estado_combate = "EXECUTANDO_ACAO"
                return

        # 2. Cálculo de chance baseado em Destreza, fadiga e quantidade de oponentes
        des_inimigos = sum(
            (i.obter_atributos_efetivos() if hasattr(i, "obter_atributos_efetivos") else getattr(i, "atributos", None)).destreza
            if hasattr(i, "atributos") or hasattr(i, "obter_atributos_efetivos") else 10
            for i in inimigos_vivos
        ) / max(1, len(inimigos_vivos))
        attrs_jog = s.jogador.obter_atributos_efetivos() if hasattr(s.jogador, "obter_atributos_efetivos") else s.jogador.atributos
        des_jogador = attrs_jog.destreza

        # Chance base: 45% + vantagem de destreza
        chance_fuga = 45.0 + ((des_jogador - des_inimigos) * 3.5)

        # Penalidade por múltiplos inimigos (-12% por inimigo adicional bloqueando o caminho)
        penalidade_cerco = (len(inimigos_vivos) - 1) * 12.0
        chance_fuga -= penalidade_cerco

        # Penalidade se a Halia estiver com vida baixa (< 30%) devido à exaustão física
        if s.jogador.vida_atual < (s.jogador.vida_maxima * 0.3):
            chance_fuga -= 10.0

        # Limites táticos: nunca 100% garantido nem totalmente impossível (12% min, 70% max)
        chance_fuga = max(12.0, min(70.0, chance_fuga))
        rolagem = random.uniform(0.0, 100.0)

        if rolagem <= chance_fuga:
            s._tocar_sfx("fuga")
            s.adicionar_log(CombatNarrator.obter_mensagem("fuga_sucesso"))
            s.estado_combate = "FUGIU"
        else:
            s._tocar_sfx("ui_erro")
            s.adicionar_texto_flutuante(
                CombatNarrator.obter_popup("fuga_falhou"),
                hx + 30,
                hy - 15,
                (245, 150, 80),
                duracao=75,
            )
            s.adicionar_log(CombatNarrator.obter_mensagem("fuga_falhou"))
            # Perde a ação do turno e os inimigos atacam em seguida
            s.timer_acao = s._ajustar_timer(65)
            s.estado_combate = "EXECUTANDO_ACAO"

    def finalizar_vitoria(self):
        """Distribui recompensas acumuladas de todos os inimigos e exibe banner."""
        s = self.screen
        if s.estado_combate == "VITORIA":
            return
        s.recompensas_vitoria = {"moedas": 0, "memorias": 0, "xp": 0}

        for inimigo in s.inimigos:
            rec = getattr(inimigo, "recompensas", {})
            s.recompensas_vitoria["moedas"] += rec.get("moedas", 10)
            s.recompensas_vitoria["memorias"] += rec.get("memorias", 0)
            s.recompensas_vitoria["xp"] += rec.get("xp", 15)

        # Entrega recompensas à Halia
        if hasattr(s.jogador, "ganhar_dinheiro"):
            s.jogador.ganhar_dinheiro(s.recompensas_vitoria["moedas"])
        if hasattr(s.jogador, "recuperar_memoria") and s.recompensas_vitoria["memorias"] > 0:
            s.jogador.recuperar_memoria(s.recompensas_vitoria["memorias"])
        if hasattr(s.jogador, "ganhar_xp") and s.recompensas_vitoria.get("xp", 0) > 0:
            s.jogador.ganhar_xp(s.recompensas_vitoria["xp"])

        s.adicionar_log(
            CombatNarrator.obter_mensagem(
                "vitoria",
                moedas=Player.formatar_valor_moedas(s.recompensas_vitoria["moedas"]),
                memorias=s.recompensas_vitoria["memorias"],
                xp=s.recompensas_vitoria.get("xp", 0),
            )
        )
        s.estado_combate = "VITORIA"
        if hasattr(s, "game") and hasattr(s.game, "conquistas") and s.game.conquistas:
            s.game.conquistas.desbloquear("primeiro_sangue")
            for inimigo in s.inimigos:
                if (
                    isinstance(inimigo, Boss)
                    or getattr(inimigo, "eh_chefe", False)
                    or "superior" in getattr(inimigo, "nome", "").lower()
                ):
                    s.game.conquistas.desbloquear("cacadora_abissal")
                    break
        audio = AudioManager.get_instance()
        if audio:
            audio.tocar_musica("vitoria", loop=0, fade_ms=120, salvar_anterior=False, contexto="resultado_combate")

    def finalizar_derrota(self):
        """Configura estado de derrota."""
        s = self.screen
        s.adicionar_log(CombatNarrator.obter_mensagem("derrota"))
        s.estado_combate = "DERROTA"
        audio = AudioManager.get_instance()
        if audio:
            audio.tocar_musica("derrota", loop=0, fade_ms=400, salvar_anterior=False, contexto="resultado_combate")

    def concluir_fechamento_combate(self):
        """Dispara os callbacks configurados ao encerrar e restaura a trilha apenas se necessário."""
        s = self.screen
        s.efeitos_visuais.limpar()
        if hasattr(s.jogador, "sair_combate"):
            s.jogador.sair_combate()

        audio = AudioManager.get_instance()
        token_combate = getattr(audio, "_token_combate", None) if audio else None
        estado_apos = s.estado_combate

        if estado_apos == "VITORIA" and callable(s.on_vitoria):
            s.on_vitoria()
        elif estado_apos == "DERROTA" and callable(s.on_derrota):
            s.on_derrota()
        elif estado_apos == "FUGIU" and callable(s.on_fuga):
            s.on_fuga()

        if audio:
            jogo = getattr(s, "game", None)
            if (
                jogo is not None
                and getattr(jogo, "nome_estado_atual", "") == "JOGANDO"
                and getattr(audio, "contexto_musica", "") in ("combate", "resultado_combate")
                and hasattr(jogo, "sincronizar_trilha_cenario")
            ):
                jogo.sincronizar_trilha_cenario(fade_ms=600)
            else:
                try:
                    audio.restaurar_musica_anterior(fade_ms=600, token_esperado=token_combate)
                except TypeError:
                    audio.restaurar_musica_anterior(fade_ms=600)
