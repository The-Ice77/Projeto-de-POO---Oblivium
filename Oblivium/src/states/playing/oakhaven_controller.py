# src/states/playing/oakhaven_controller.py
import pygame
from src.entities.enemy_factory import EnemyFactory


class OakhavenController:
    """
    Controlador modular da Fase 1 em Oakhaven (Vila de Oakhaven, Orla Norte,
    ataque aéreo do dragão Ignis'Vahr, Oakhaven Destruída, Ninho do Dragão e Timeskip).
    Extraído de PlayingState mantendo 100% do comportamento original.
    """

    EVENTOS_DIALOGO_OAKHAVEN = (
        "cura_elara_missao",
        "cura_elara_destruida",
        "ir_patrulha_doran",
        "iniciar_cutscene_dormir_vila",
        "iniciar_amanhecer_ataque_dragao",
        "ir_para_ninho_dragao",
        "iniciar_climax_dragao_oakhaven",
        "iniciar_combate_dragao_oakhaven",
        "iniciar_flashback_sylvan_ninho",
        "retornar_oakhaven_vitoria",
        "iniciar_timeskip_final_oakhaven",
        "iniciar_partida_demo_oakhaven",
    )

    def __init__(self, game, playing_state):
        self.game = game
        self.playing_state = playing_state

    def processar_escolha_dialogo(self, opcao_atual):
        """Interpreta opções de diálogo específicas de Oakhaven e identifica ações pós-fala."""
        opt_id = opcao_atual.get("id")
        if opt_id == "recordar_amigos_monumento":
            self.game.caixa_dialogo.ativo = False
            self.game.caixa_dialogo.em_escolha = False
            seq_sylvan = self.game.caixa_dialogo.manager.obter_sequencia_linear(
                "flashback_memoria_2_sylvan"
            )
            self.game.flashback_monumento_ativo = True
            self.game.flashback_sistema.iniciar(seq_sylvan, tipo="acampamento", game=self.game)
            return {
                "interromper": True,
                "abrir_loja": False,
                "loja_id": None,
                "ir_patrulha": False,
            }
        elif opt_id == "sair_monumento":
            self.game.caixa_dialogo.ativo = False
            self.game.caixa_dialogo.em_escolha = False
            return {
                "interromper": True,
                "abrir_loja": False,
                "loja_id": None,
                "ir_patrulha": False,
            }

        abrir_loja = (
            opcao_atual.get("acao") == "abrir_loja"
            or opcao_atual.get("evento") == "abrir_loja"
        )
        ir_patrulha = (
            opcao_atual.get("acao") == "ir_patrulha_doran"
            or opcao_atual.get("evento") == "ir_patrulha_doran"
        )
        return {
            "interromper": False,
            "abrir_loja": abrir_loja,
            "loja_id": opcao_atual.get("loja_id") if abrir_loja else None,
            "ir_patrulha": ir_patrulha,
        }

    def abrir_loja_npc(self, loja_id_alvo=None):
        """Valida pré-requisitos de missão do NPC atual e abre a loja correspondente."""
        if not loja_id_alvo and hasattr(self.game, "npc_interagindo_atual") and self.game.npc_interagindo_atual:
            loja_id_alvo = getattr(self.game.npc_interagindo_atual, "loja_id", None)

        # Validação estrita de pré-requisitos da loja do NPC
        npc_atual = getattr(self.game, "npc_interagindo_atual", None)
        pode_abrir = True
        qm = getattr(self.game, "missoes", None)
        if npc_atual and hasattr(npc_atual, "pode_abrir_loja"):
            pode_abrir = npc_atual.pode_abrir_loja(qm)
        elif loja_id_alvo and qm and hasattr(qm, "missoes"):
            norm_l = str(loja_id_alvo).lower()
            if "forja" in norm_l or "torvald" in norm_l:
                pode_abrir = (qm.missoes.get("missao_pedra_forja", {}).get("status") == "CONCLUIDA")
            elif "botanica" in norm_l or "elara" in norm_l:
                pode_abrir = (qm.missoes.get("missao_ervas_medicinais", {}).get("status") == "CONCLUIDA")

        self.game.caixa_dialogo.ativo = False
        if pode_abrir:
            if hasattr(self.game, "missoes") and self.game.missoes:
                self.game.missoes.atualizar_progresso("conhecer_mercado", 1)
                self.game.missoes.atualizar_progresso("visitar_mercado", 1)
            if hasattr(self.game, "abrir_loja"):
                self.game.abrir_loja(loja_id_alvo)
            else:
                self.game.mudar_estado("LOJA")

    def executar_evento_dialogo(self, evt_pendente):
        """Executa um evento narrativo de fim de diálogo pertencente a Oakhaven."""
        if evt_pendente in ("cura_elara_missao", "cura_elara_destruida"):
            if hasattr(self.game, "halia") and self.game.halia:
                self.game.halia.restaurar_total()
            if evt_pendente == "cura_elara_missao" and hasattr(self.game, "missoes") and self.game.missoes:
                if self.game.missoes.missoes.get("missao_ervas_medicinais", {}).get("status") != "CONCLUIDA":
                    self.game.missoes.concluir_missao("missao_ervas_medicinais")
        elif evt_pendente == "ir_patrulha_doran":
            self.ir_para_patrulha_orla_norte()
        elif evt_pendente == "iniciar_cutscene_dormir_vila":
            qm = getattr(self.game, "missoes", None)
            if not qm or any(qm.missoes.get(mid, {}).get("status") != "CONCLUIDA" for mid in (
                "missao_boas_vindas", "missao_ronda_fronteiras"
            )):
                return
            self.game.caixa_dialogo.ativo = False
            if hasattr(self.playing_state, "cinematica_dragao"):
                self.playing_state.cinematica_dragao.iniciar_sono()
        elif evt_pendente == "iniciar_amanhecer_ataque_dragao":
            if hasattr(self.playing_state, "cinematica_dragao"):
                self.playing_state.cinematica_dragao.iniciar_ataque_aereo()
            else:
                self.iniciar_amanhecer_ataque_dragao()
        elif evt_pendente in ("ir_para_ninho_dragao", "iniciar_climax_dragao_oakhaven"):
            self.iniciar_climax_dragao_oakhaven()
        elif evt_pendente == "iniciar_combate_dragao_oakhaven":
            self.game.combate_climax_dragao = True
            self.game.iniciando_combate = True
            self.game.transicao.iniciar()
        elif evt_pendente == "iniciar_flashback_sylvan_ninho":
            if not self.game.dragao_derrotado or self.game.halia.fragmentos_memoria >= 2 or self.game.flashback_sistema.ativo:
                return
            self.game.etapa_epilogo = "FLASHBACK_SYLVAN_PENDENTE"
            seq_sylvan = self.game.caixa_dialogo.manager.obter_sequencia_linear("flashback_memoria_2_sylvan")
            self.game.flashback_sylvan_ativo = True
            self.game.flashback_sistema.iniciar(seq_sylvan, tipo="acampamento", game=self.game)
        elif evt_pendente == "retornar_oakhaven_vitoria":
            self.retornar_oakhaven_apos_vitoria()
        elif evt_pendente == "iniciar_timeskip_final_oakhaven":
            if not self.game.dragao_derrotado or self.game.estagio_memoria_apresentado < 2:
                return
            self.game.etapa_epilogo = "RECONSTRUCAO_PENDENTE"
            if hasattr(self.playing_state, "cutscene_reconstrucao"):
                self.playing_state.cutscene_reconstrucao.iniciar()
        elif evt_pendente == "iniciar_partida_demo_oakhaven":
            if hasattr(self.playing_state, "cutscene_reconstrucao"):
                self.playing_state.cutscene_reconstrucao.iniciar_partida()

    def processar_eventos_pos_avanco_dialogo(
        self, abrir_loja_apos=False, loja_id_alvo=None, ir_patrulha_apos=False
    ):
        """Processa os eventos de loja e roteiro imediatamente após proximo_texto()."""
        if self.game.caixa_dialogo.ativo:
            return
        evt_atual = getattr(self.game.caixa_dialogo.manager, "evento_pendente", None)
        if abrir_loja_apos or evt_atual == "abrir_loja":
            self.game.caixa_dialogo.manager.consumir_evento()
            self.abrir_loja_npc(loja_id_alvo)
        elif ir_patrulha_apos or (not self.game.caixa_dialogo.ativo and evt_atual == "ir_patrulha_doran"):
            self.game.caixa_dialogo.manager.consumir_evento()
            self.game.caixa_dialogo.ativo = False
            self.ir_para_patrulha_orla_norte()
        elif evt_atual == "cura_elara_missao":
            self.game.caixa_dialogo.manager.consumir_evento()
            self.executar_evento_dialogo("cura_elara_missao")
        elif not self.game.caixa_dialogo.ativo and evt_atual in (
            "iniciar_cutscene_dormir_vila",
            "iniciar_amanhecer_ataque_dragao",
            "ir_para_ninho_dragao",
            "iniciar_climax_dragao_oakhaven",
            "iniciar_combate_dragao_oakhaven",
            "iniciar_flashback_sylvan_ninho",
            "retornar_oakhaven_vitoria",
            "iniciar_timeskip_final_oakhaven",
            "iniciar_partida_demo_oakhaven",
        ):
            self.game.caixa_dialogo.manager.consumir_evento()
            self.game.caixa_dialogo.ativo = False
            self.executar_evento_dialogo(evt_atual)

    def verificar_gatilhos_zona(self):
        """Processa eventos pendentes, retorno do Ninho, diálogo pós-dragão e Orla Norte."""
        evt_pendente = getattr(self.game.caixa_dialogo.manager, "evento_pendente", None)
        if evt_pendente in self.EVENTOS_DIALOGO_OAKHAVEN:
            if self.game.caixa_dialogo.ativo:
                return
            self.game.caixa_dialogo.manager.consumir_evento()
            self.executar_evento_dialogo(evt_pendente)
            return True
        if evt_pendente == "abrir_loja":
            loja_id = self.game.caixa_dialogo.manager.loja_pendente
            self.game.caixa_dialogo.manager.consumir_evento()
            self.game.caixa_dialogo.manager.loja_pendente = None
            self.abrir_loja_npc(loja_id)
            return True
        if self.retomar_epilogo_pendente():
            return True

        # No Ninho do Dragão após a vitória ao amanhecer: caminhar até a trilha sul (y > 645) retorna a Oakhaven
        if self.game.mapa_casa.cenario_atual == "NINHO_DRAGAO" and getattr(
            self.game.mapa_casa.cenario_objeto, "dragao_derrotado", False
        ):
            if (
                self.game.halia.y > 645
                and self.game.estagio_memoria_apresentado >= 2
                and self.game.transicao.estado == "INATIVO"
                and not self.game.caixa_dialogo.ativo
            ):
                self.retornar_oakhaven_apos_vitoria()
                return

        # Após despertar da Memória 2 (Sylvan) no pós-clímax do Dragão em Oakhaven
        if getattr(self.game, "aguardando_dialogo_pos_dragao", False):
            despertar_inativo = (
                not hasattr(self.game, "tela_despertar")
                or self.game.tela_despertar.estado == "INATIVO"
            )
            if despertar_inativo and self.playing_state.memoria_anterior_registrada >= 2:
                self.game.aguardando_dialogo_pos_dragao = False
                self.game.caixa_dialogo.iniciar_dialogo("pos_vitoria_dragao_oakhaven")
                return

        # Segurança para despedida em Oakhaven restaurada caso seja retomada após load em DESPEDIDA_PENDENTE
        if (
            self.game.mapa_casa.cenario_atual == "OAKHAVEN"
            and getattr(self.game, "etapa_epilogo", "NAO_INICIADO") == "DESPEDIDA_PENDENTE"
            and not getattr(self.game, "despedida_demo_exibida", False)
            and not self.game.caixa_dialogo.ativo
            and not self.game.flashback_sistema.ativo
            and self.game.transicao.estado == "INATIVO"
            and not getattr(getattr(self.playing_state, "cutscene_reconstrucao", None), "ativo", False)
        ):
            self.game.despedida_demo_exibida = True
            self.game.caixa_dialogo.iniciar_dialogo("despedida_demo_oakhaven")
            return

        # Em ORLA_NORTE: onde o Guarda Doran levou Halia para enfrentar os 2 Batedores Demoníacos
        if self.game.mapa_casa.cenario_atual == "ORLA_NORTE":
            # Se Halia caminhar de volta pelo portão sul da clareira, retorna a Oakhaven
            if self.game.halia.y > 660 and not getattr(self.game, "combate_climax_dragao", False):
                self.game.inimigos_em_cena.clear()
                self.game.mapa_casa.carregar_cenario("OAKHAVEN")
                self.game.halia.x, self.game.halia.y = 1102, 245
                self.game.halia.direcao = "baixo"
                self.game.halia.mudar_estado("idle")
                self.playing_state.atualizar_camera(instantaneo=True)
                return

            # Se Halia se aproximar dos batedores na clareira da Orla Norte, inicia o combate de patrulha
            if self.game.inimigos_em_cena and not self.game.iniciando_combate:
                area_halia = pygame.Rect(
                    int(self.game.halia.x - 28),
                    int(self.game.halia.y - 28),
                    self.game.halia.largura + 56,
                    self.game.halia.altura + 56,
                )
                alguem_perto = any(
                    area_halia.colliderect(pygame.Rect(int(inim.x), int(inim.y), inim.largura, inim.altura))
                    for inim in self.game.inimigos_em_cena
                )
                em_revelacao_ativa = any(
                    getattr(inim, "revelando", False) or getattr(inim, "revelado", False)
                    for inim in self.game.inimigos_em_cena
                )
                if alguem_perto or em_revelacao_ativa:
                    ainda_revelando = False
                    for inim_alvo in self.game.inimigos_em_cena:
                        if getattr(inim_alvo, "eh_mimico", False) and not getattr(inim_alvo, "revelado", False):
                            if not getattr(inim_alvo, "revelando", False):
                                inim_alvo.iniciar_revelacao()
                            ainda_revelando = True
                    if not ainda_revelando:
                        self.game.iniciando_combate = True
                        self.game.transicao.iniciar()

    def retomar_epilogo_pendente(self):
        """Retoma os marcos pós-vitória sem repetir combate, memória ou recompensa."""
        if self.game.caixa_dialogo.ativo or not self.game.dragao_derrotado or self.game.halia.fragmentos_memoria >= 2:
            return False
        etapa = getattr(self.game, "etapa_epilogo", "NAO_INICIADO")
        if etapa == "POS_DRAGAO":
            self.game.caixa_dialogo.iniciar_dialogo("cena_pos_combate_ninho_dragao")
            return True
        if etapa == "FLASHBACK_SYLVAN_PENDENTE" and not self.game.flashback_sistema.ativo:
            self.executar_evento_dialogo("iniciar_flashback_sylvan_ninho")
            return True
        return False

    def processar_interacao_cenario(self, area_interacao):
        """Processa interações com NPCs, fauna e pontos de interesse de Oakhaven."""
        # Interações com NPCs do cenário ativo (ex: Oakhaven)
        for npc in getattr(self.game.mapa_casa, "npcs", []):
            r_npc = pygame.Rect(int(npc.x - 10), int(npc.y - 10), npc.largura + 20, npc.altura + 20)
            if area_interacao.colliderect(r_npc):
                self.game.npc_interagindo_atual = npc
                npc.virado_direita = (self.game.halia.x > npc.x)
                self.game.halia.virado_direita = (npc.x > self.game.halia.x)
                if hasattr(self.game, "missoes") and self.game.missoes:
                    if npc.npc_id in ("curandeira_elara", "ferreiro_torvald"):
                        self.game.missoes.atualizar_progresso("conhecer_mercado", 1)
                        self.game.missoes.atualizar_progresso("visitar_mercado", 1)
                npc.interagir(self.game)
                return True

        # Interação com Patusco (Easter Egg 1/7 no tufo de grama - desativado à noite pois ele já dorme)
        eh_noite = getattr(self.game, "oakhaven_noite", False)
        if not eh_noite:
            for animal in getattr(self.game.mapa_casa, "animais", []):
                if hasattr(animal, "interagir") and getattr(animal, "visivel", True):
                    r_anim = pygame.Rect(int(animal.x - 24), int(animal.y - 24), 48, 48)
                    if area_interacao.colliderect(r_anim):
                        animal.interagir(self.game)
                        return True

        # Interação com pontos de lore e objetos de missão no cenário (Monumento, Quadro, Rocha de Minério)
        for pt in getattr(self.game.mapa_casa, "pontos_interacao", []):
            if area_interacao.colliderect(pt["rect"]):
                if pt.get("id") == "rocha_minerio_torvald":
                    estado_missao = (
                        (self.game.missoes.obter_missao("missao_pedra_forja") or {}).get(
                            "status", "NAO_INICIADA"
                        )
                        if hasattr(self.game, "missoes") and self.game.missoes
                        else "NAO_INICIADA"
                    )
                    if estado_missao == "ATIVA" and not getattr(self.game, "pedra_torvald_quebrada", False):
                        self.playing_state.minigame_ferraria.iniciar()
                        return True
                    else:
                        self.game.caixa_dialogo.iniciar_dialogo(
                            [
                                {
                                    "autor": "Narrador",
                                    "texto": "Um grande bloco de minério bruto com veios metálicos azulados repousa no pátio da forja. O Ferreiro Torvald parece precisar de auxílio para parti-lo.",
                                }
                            ]
                        )
                        return True
                if "evento" in pt:
                    ev = pt["evento"]
                    if ev == "retornar_oakhaven_vitoria":
                        self.retornar_oakhaven_apos_vitoria()
                        return True
                    elif ev == "iniciar_climax_dragao_oakhaven":
                        self.iniciar_climax_dragao_oakhaven()
                        return True
                if pt.get("id") == "estatua_herois":
                    self.game.caixa_dialogo.iniciar_dialogo("monumento_herois")
                    return True
                if "dialogo" in pt:
                    self.game.caixa_dialogo.iniciar_dialogo(pt["dialogo"])
                    return True

        return False

    def entrar_em_oakhaven(self):
        """Transiciona Halia para a entrada sul da Vila de Oakhaven (Fase 1)."""
        self.game.pronto_viajar_oakhaven = False
        self.game.partindo_estrada2 = False
        self.game.mapa_casa.carregar_cenario("OAKHAVEN")
        self.game.carroceiro_visivel = False
        self.game.carroceiro_andando = False
        self.game.cena_inimigos_andando = False
        self.game.inimigos_em_cena.clear()
        self.game.halia.x, self.game.halia.y = 1102, 1320
        self.game.halia.direcao = "cima"
        self.game.halia.mudar_estado("idle")
        self.playing_state.atualizar_camera(instantaneo=True)

        if self.game.slot_atual:
            self.game.salvar_estado(self.game.slot_atual, tipo="autosave")

        pygame.event.clear()
        self.game.caixa_dialogo.iniciar_dialogo(
            [
                {
                    "autor": "Narrador",
                    "texto": "As cores suaves do entardecer tocam os telhados de Oakhaven. No centro da praça à frente, ergue-se um monumento de pedra onde o Ancião Aldous aguarda em silêncio.",
                }
            ]
        )
        self.game.transicao.estado = "CLAREANDO"

    def ir_para_patrulha_orla_norte(self):
        """
        O Guarda Doran conduz Halia pelo Portão Norte até a clareira da Orla Norte ('ORLA_NORTE'),
        onde os 2 Batedores Demoníacos estão escondidos.
        """
        self.game.mapa_casa.carregar_cenario("ORLA_NORTE")
        self.game.cena_inimigos_andando = False
        self.game.inimigos_em_cena.clear()
        self.game.halia.x, self.game.halia.y = 610, 520
        self.game.halia.direcao = "cima"
        self.game.halia.mudar_estado("idle")
        self.playing_state.atualizar_camera(instantaneo=True)

        if self.game.slot_atual:
            self.game.salvar_estado(self.game.slot_atual, tipo="autosave")

        batedor1 = EnemyFactory.criar("mimico", x=565, y=285, nome_custom="Mímico Batedor 1")
        batedor2 = EnemyFactory.criar("mimico", x=665, y=305, nome_custom="Mímico Batedor 2")
        for bat in (batedor1, batedor2):
            bat.velocidade = 0
            bat.virado_direita = False
            bat.direcao = "esquerda"
            bat.recompensas = {"moedas": 25, "memorias": 0, "xp": 45}
            bat.disfarcado = True
            bat.revelado = False
            bat.revelando = False
            bat.mudar_estado("corpo")
        self.game.inimigos_em_cena.extend([batedor1, batedor2])

        self.game.caixa_dialogo.iniciar_dialogo(
            [
                {
                    "autor": "Guarda Doran",
                    "texto": "Chegamos à clareira, Halia! Aqueles dois parecem corpos de soldados da patrulha caídos na grama... Mas sinto um miasma maligno no ar. Aproxime-se com cautela para investigar!",
                }
            ]
        )

    def iniciar_amanhecer_ataque_dragao(self):
        """
        Após o repouso noturno em Oakhaven, Halia acorda na calada da noite com
        Ignis'Vahr, o Dragão Vermelho Ancestral, atacando e destruindo a vila ('OAKHAVEN_DESTRUIDA').
        """
        self.game.oakhaven_noite = True
        self.game.oakhaven_destruida = True
        self.game.mapa_casa.carregar_cenario("OAKHAVEN_DESTRUIDA")
        self.game.cena_inimigos_andando = False
        self.game.inimigos_em_cena.clear()
        self.game.halia.x, self.game.halia.y = 1102, 660
        self.game.halia.direcao = "cima"
        self.game.halia.mudar_estado("idle")
        self.playing_state.atualizar_camera(instantaneo=True)

        if self.game.slot_atual:
            self.game.salvar_estado(self.game.slot_atual, tipo="autosave")

        if hasattr(self.game, "audio") and self.game.audio:
            self.game.audio.tocar_musica("ataque_dragao", loop=-1, fade_ms=800)

        self.game.caixa_dialogo.iniciar_dialogo("despertar_ataque_dragao_vila")

    def iniciar_climax_dragao_oakhaven(self):
        """
        Inicia o Clímax da Fase 1 no Ninho do Dragão ('NINHO_DRAGAO') durante a noite:
        Ignis'Vahr, o Dragão Vermelho Ancestral, aguarda nos penhascos vulcânicos, desencadeando
        a Crise de Ansiedade 1 (Trauma do Fogo) + Ancoragem Sensorial antes da Batalha de Chefe.
        """
        self.game.oakhaven_noite = True
        self.game.mapa_casa.carregar_cenario("NINHO_DRAGAO")
        self.game.cena_inimigos_andando = False
        self.game.inimigos_em_cena.clear()
        self.game.halia.x, self.game.halia.y = 610, 520
        self.game.halia.direcao = "cima"
        self.game.halia.mudar_estado("idle")
        self.playing_state.atualizar_camera(instantaneo=True)

        if self.game.slot_atual:
            self.game.salvar_estado(self.game.slot_atual, tipo="autosave")

        ninho = self.game.mapa_casa.cenario_objeto
        ninho.ninho_amanhecer = False
        ninho.dragao_derrotado = False
        ninho.inicializar_cenario()

        dragao = EnemyFactory.criar_boss(
            "dragao_vermelho", x=525, y=145, nome_custom="Ignis'Vahr, o Dragão Vermelho"
        )
        dragao.velocidade = 0
        dragao.virado_direita = False
        dragao.direcao = "esquerda"
        self.game.inimigos_em_cena.append(dragao)

        if hasattr(self.game, "audio") and self.game.audio:
            self.game.audio.tocar_musica("combate_dragao", loop=-1, fade_ms=800)

        self.game.caixa_dialogo.iniciar_dialogo("crise_ansiedade_dragao_oakhaven")

    def ir_para_ninho_dragao(self):
        """Alias semântico para transportar Halia de Oakhaven destruída até o Ninho do Dragão."""
        self.iniciar_climax_dragao_oakhaven()

    def retornar_oakhaven_apos_vitoria(self):
        """Transporta Halia de volta a Oakhaven após derrotar Ignis'Vahr e prepara o epílogo."""
        self.game.transicao.iniciar("Retornando vitoriosa a Oakhaven...")
        cenario_retorno = (
            "OAKHAVEN_DESTRUIDA" if getattr(self.game, "oakhaven_destruida", True) else "OAKHAVEN"
        )
        self.game.mapa_casa.carregar_cenario(cenario_retorno)
        self.game.halia.x, self.game.halia.y = 1102, 660
        self.game.halia.direcao = "cima"
        self.game.halia.mudar_estado("idle")
        self.playing_state.atualizar_camera(instantaneo=True)
        self.game.aguardando_dialogo_pos_dragao = True
        if getattr(self.game, "etapa_epilogo", "NAO_INICIADO") not in (
            "RECONSTRUCAO_PENDENTE",
            "DESPEDIDA_PENDENTE",
            "DEMO_CONCLUIDA",
        ):
            self.game.etapa_epilogo = "RECONSTRUCAO_PENDENTE"
        if self.game.slot_atual:
            self.game.salvar_estado(self.game.slot_atual, tipo="autosave")

    def concluir_flashback_sylvan_pos_dragao(self):
        """Concede a Memória 2 ao fim do flashback de Sylvan e aguarda TelaDespertarMemoria."""
        self.game.flashback_sylvan_ativo = False
        self.game.etapa_epilogo = "DESPERTAR_PENDENTE"
        halia = getattr(self.game, "halia", None)
        if halia and halia.fragmentos_memoria < 2:
            halia.recuperar_memoria(1, adiar_autosave=True)
        if hasattr(self.game, "mapa_casa") and self.game.mapa_casa:
            self.game.mapa_casa.carregar_cenario("NINHO_DRAGAO")
            ninho = getattr(self.game.mapa_casa, "cenario_objeto", None)
            if ninho:
                ninho.ninho_amanhecer = True
                ninho.dragao_derrotado = True
                if hasattr(ninho, "inicializar_cenario"):
                    ninho.inicializar_cenario()
        if halia:
            halia.x, halia.y = 610, 380
            halia.direcao = "cima"
            halia.mudar_estado("idle")
        if hasattr(self.playing_state, "atualizar_camera"):
            self.playing_state.atualizar_camera(instantaneo=True)
        if getattr(self.game, "slot_atual", None) and hasattr(self.game, "salvar_estado"):
            self.game.salvar_estado(self.game.slot_atual, tipo="autosave")

    def on_despertar_memoria_concluido(self, novo_estagio):
        """Dispara a narração de retorno após o encerramento do despertar da Memória 2."""
        if novo_estagio == 2 and getattr(self.game, "etapa_epilogo", "NAO_INICIADO") == "DESPERTAR_PENDENTE":
            self.game.etapa_epilogo = "RETORNO_VILA"
            if getattr(self.game, "slot_atual", None) and hasattr(self.game, "salvar_estado"):
                self.game.salvar_estado(self.game.slot_atual, tipo="autosave", silenciar_notificacao=True)
            if hasattr(self.game, "caixa_dialogo") and self.game.caixa_dialogo:
                self.game.caixa_dialogo.iniciar_dialogo(
                    [
                        {
                            "autor": "Narrador",
                            "texto": "O riso caloroso de Sylvan ainda ecoa como uma brasa acolhedora na memória de Halia. A força daquela amizade antiga dissipa suas dores. O dragão colossal jaz inerte sob a luz límpida da aurora. É hora de descer pela trilha sul e levar as boas notícias ao povo de Oakhaven.",
                        }
                    ]
                )

    def on_vitoria_combate_dragao(self):
        """Aplica o estado de amanhecer no Ninho do Dragão após derrotar Ignis'Vahr."""
        self.game.combate_climax_dragao = False
        self.game.inimigos_em_cena.clear()
        self.game.cena_inimigos_andando = False
        self.game.oakhaven_noite = False  # A longa noite de batalha terminou: rompe a alvorada!
        self.game.dragao_derrotado = True
        self.game.desespero_superado = True
        self.game.etapa_epilogo = "POS_DRAGAO"

        # Halia permanece no NINHO_DRAGAO contemplando exausta o corpo do dragão ao amanhecer
        self.game.mapa_casa.carregar_cenario("NINHO_DRAGAO")
        ninho = self.game.mapa_casa.cenario_objeto
        ninho.ninho_amanhecer = True
        ninho.dragao_derrotado = True
        ninho.inicializar_cenario()

        self.game.halia.x, self.game.halia.y = 610, 380
        self.game.halia.direcao = "cima"
        self.game.halia.mudar_estado("idle")
        self.playing_state.atualizar_camera(instantaneo=True)

        if hasattr(self.game, "audio") and self.game.audio:
            self.game.audio.tocar_ambiente("vento_suave", loop=-1, fade_ms=1000)

        self.game.mudar_estado("JOGANDO")
        self.game.caixa_dialogo.iniciar_dialogo("cena_pos_combate_ninho_dragao")

    def on_vitoria_combate_patrulha(self):
        """Finaliza a ronda na Orla Norte ao derrotar os Mímicos, marcando o anoitecer em Oakhaven."""
        self.game.inimigos_em_cena.clear()
        self.game.cena_inimigos_andando = False
        self.game.oakhaven_noite = True
        if hasattr(self.game, "missoes") and self.game.missoes:
            self.game.missoes.atualizar_progresso("derrotar_demonios", 2)
            self.game.missoes.atualizar_progresso("derrotar_sombras", 2)
        self.game.mapa_casa.carregar_cenario("OAKHAVEN")
        self.game.halia.x, self.game.halia.y = 1102, 265
        self.game.halia.direcao = "cima"
        self.game.halia.mudar_estado("idle")
        self.playing_state.atualizar_camera(instantaneo=True)
        if self.game.slot_atual:
            self.game.salvar_estado(self.game.slot_atual, tipo="autosave")
        self.game.mudar_estado("JOGANDO")
        self.game.caixa_dialogo.iniciar_dialogo(
            [
                {
                    "autor": "Guarda Doran",
                    "texto": "Excelente combate, Halia! Aqueles soldados caídos eram na verdade Mímicos ferozes disfarçados... Que emboscada hedionda! Já caiu a noite sobre Oakhaven quando retornamos — fale comigo aqui no Portão Norte para encerrarmos a ronda!",
                }
            ]
        )

    def on_fuga_combate_patrulha(self):
        """Retorna Halia para o Portão Norte de Oakhaven ao fugir de combate em Oakhaven/Orla Norte."""
        self.game.inimigos_em_cena.clear()
        self.game.mapa_casa.carregar_cenario("OAKHAVEN")
        self.game.halia.x, self.game.halia.y = 1102, 280
        self.playing_state.atualizar_camera(instantaneo=True)

    def desenhar_prompts(self, tela, area_interacao, tecla_interacao_str, desenhar_fn):
        """Desenha indicadores de interação para NPCs, fauna e pontos de interesse de Oakhaven."""
        if self.game.caixa_dialogo.ativo or self.game.flashback_sistema.ativo:
            return

        for npc in getattr(self.game.mapa_casa, "npcs", []):
            r_npc = pygame.Rect(int(npc.x - 10), int(npc.y - 10), npc.largura + 20, npc.altura + 20)
            if area_interacao.colliderect(r_npc):
                topo_y = npc.obter_topo_cabeca() if hasattr(npc, "obter_topo_cabeca") else int(npc.y - 42)
                prompt_y = int(topo_y - 34)
                desenhar_fn(
                    tela,
                    int(npc.x + npc.largura // 2),
                    prompt_y,
                    tecla=tecla_interacao_str,
                    acao=f"Falar com {npc.nome}",
                )
                return

        if not getattr(self.game, "oakhaven_noite", False):
            for animal in getattr(self.game.mapa_casa, "animais", []):
                if hasattr(animal, "interagir") and getattr(animal, "visivel", True):
                    r_anim = pygame.Rect(int(animal.x - 24), int(animal.y - 24), 48, 48)
                    if area_interacao.colliderect(r_anim):
                        desenhar_fn(
                            tela,
                            int(animal.x),
                            int(animal.y - 62),
                            tecla=tecla_interacao_str,
                            acao="para Acariciar Patusco",
                        )
                        return

        for pt in getattr(self.game.mapa_casa, "pontos_interacao", []):
            if area_interacao.colliderect(pt["rect"]):
                desenhar_fn(
                    tela,
                    pt["prompt_x"],
                    pt["prompt_y"],
                    tecla=tecla_interacao_str,
                    acao=pt["acao_texto"],
                )
                return

    def atualizar_cinematica_reconstrucao(self, dt):
        """Mantém entidades, câmera cinemática, filtro e ambiente vivos durante a reconstrução."""
        self.game.tempo_jogado += dt
        self.playing_state.cutscene_reconstrucao.atualizar(dt)
        cenario_obj = getattr(getattr(self.game, "mapa_casa", None), "cenario_objeto", None)
        if cenario_obj and hasattr(cenario_obj, "atualizar"):
            cenario_obj.atualizar(dt)
        if hasattr(self.game, "halia") and hasattr(self.game.halia, "atualizar_animacao"):
            self.game.halia.atualizar_animacao(dt)
        for npc_mapa in getattr(getattr(self.game, "mapa_casa", None), "npcs", []):
            if hasattr(npc_mapa, "atualizar_animacao"):
                npc_mapa.atualizar_animacao(dt)
        if hasattr(self.game, "filtro_memoria") and self.game.filtro_memoria:
            self.game.filtro_memoria.atualizar()
        if hasattr(self.game, "efeito_folhas") and self.game.efeito_folhas:
            self.game.efeito_folhas.atualizar(dt, 0.25)
        if (
            hasattr(self.game, "caixa_dialogo")
            and getattr(self.game.caixa_dialogo, "ativo", False)
            and not getattr(getattr(self.playing_state, "cutscene_reconstrucao", None), "ativo", False)
        ):
            self.game.caixa_dialogo.atualizar(dt)
        if getattr(self.game, "nome_estado_atual", "JOGANDO") == "JOGANDO":
            self.playing_state.atualizar_camera(dt=dt)

    def concluir_despertar_memoria(self, mem_alvo):
        """Consolida uma única vez a memória desperta, dispara pulso em tela e aciona epílogo."""
        ps = self.playing_state
        if (
            ps.memoria_anterior_registrada >= mem_alvo
            and getattr(self.game, "estagio_memoria_apresentado", mem_alvo) >= mem_alvo
        ):
            return
        ps.memoria_anterior_registrada = mem_alvo
        if hasattr(self.game, "estagio_memoria_apresentado"):
            self.game.estagio_memoria_apresentado = max(
                int(getattr(self.game, "estagio_memoria_apresentado", 0) or 0),
                mem_alvo,
            )
        if hasattr(self.game, "hud") and self.game.hud:
            self.game.hud.memorias_coletadas = getattr(self.game.halia, "fragmentos_memoria", mem_alvo)
        if hasattr(self.game, "filtro_memoria") and self.game.filtro_memoria:
            ox = int(self.game.halia.x - ps.camera_x + getattr(self.game.halia, "largura", 40) * 0.5)
            oy = int(self.game.halia.y - ps.camera_y + getattr(self.game.halia, "altura", 60) * 0.5)
            self.game.filtro_memoria.definir_estagio(
                mem_alvo,
                com_transicao_suave=True,
                pos_origem=(ox, oy),
            )
        if hasattr(self.game, "notificacoes") and self.game.notificacoes:
            self.game.notificacoes.notificar_memoria_desperta(mem_alvo)
        if hasattr(self.game, "conquistas") and self.game.conquistas and mem_alvo >= 1:
            self.game.conquistas.desbloquear("sincronia_2")
        self.on_despertar_memoria_concluido(mem_alvo)
