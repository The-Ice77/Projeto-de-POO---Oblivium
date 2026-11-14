# src/mechanics/combat/combat_screen.py
import pygame
import random
import os

from src.mechanics.skills import SkillsRegistry
from src.entities.Boss import Boss
from src.ui.ui_utils import quebrar_texto_em_linhas
from src.utils.colors import (
    TEXTO_ALERTA_COMBATE,
    BARRA_VIDA_JOGADOR, BARRA_VIDA_INIMIGO, BARRA_MANA, FUNDO_BARRA
)
from src.utils.resource_manager import ResourceManager
from src.core.audio_manager import AudioManager
from src.mechanics.combat.combat_narrator import CombatNarrator
from src.mechanics.combat.combat_renderer import CombatRenderer, TextoFlutuante
from src.mechanics.combat.combat_input import CombatInputHandler
from src.mechanics.combat.combat_effects import CombatVisualEffects
from src.mechanics.combat.combat_ai import CombatAIController


class CombatScreen:
    """
    Motor e Interface Gráfica de Combate por Turnos de Oblivium.
    - Submenu de Ataques Físicos dedicado na opção 'Atacar'.
    - Grimório Exclusivo da Halia na opção 'Magias'.
    - Quebra de linha automática (Word Wrap) no histórico de combate.
    - Pacing claro com tempo de assimilação e suporte a multiplicador de velocidade (1x, 1.5x, 2x).
    """
    def __init__(self, largura, altura):
        self.largura = largura
        self.altura = altura
        
        # Renderizador visual desacoplado (View)
        self.renderer = CombatRenderer(self)
        
        # Controlador de entradas e navegacao desacoplado (Input Handler)
        self.input_handler = CombatInputHandler(self)

        # Controlador de turnos, IA inimiga e desfecho de combate
        self.ai_controller = CombatAIController(self)
        
        # Fontes Consolidadas do Combate
        self.fonte_titulo = ResourceManager.carregar_fonte("sunday", 36)
        self.fonte_nomes = ResourceManager.carregar_fonte("sunday", 24)
        self.fonte_status = ResourceManager.carregar_fonte("contrail", 16)
        self.fonte_menu = ResourceManager.carregar_fonte("contrail", 20)
        self.fonte_log = ResourceManager.carregar_fonte("contrail", 18)
        self.fonte_dano = ResourceManager.carregar_fonte("sunday", 26)
        self.fonte_tooltip = ResourceManager.carregar_fonte("contrail", 16)
        
        # Estrutura do Menu Principal
        self.opcoes_menu_principal = ["Atacar", "Magias", "Concentrar", "Itens", "Fugir"]
        self.indice_menu = 0
        
        # Submenu de Ataques Físicos
        self.ataques_fisicos_disponiveis = []
        self.indice_ataque_fisico = 0

        # Submenu de Magias (Grimório da Halia)
        self.magias_disponiveis = []
        self.indice_magia = 0

        # Submenu de Concentrar (Ações Táticas: Foco Espiritual e Defender)
        self.opcoes_concentrar = []
        self.indice_concentrar = 0
        
        # Submenu de Itens Consumíveis de Combate
        self.itens_combate_disponiveis = []
        self.indice_item_combate = 0
        self.scroll_item_combate = 0
        self.item_combate_selecionado = None
        
        # Seleção de Alvo
        self.indice_alvo = 0
        self.acao_selecionada = None
        
        # Entidades e Fila de Turnos
        self.jogador = None
        self.inimigos = []
        self.ordem_turnos_base = []
        self.ordem_turnos = [] 
        self.indice_turno_atual = 0
        
        # Velocidade e Pacing de Combate
        self.velocidade_combate = 1.0  # 1.0 (Normal), 1.5 (Rápido), 2.0 (Ultra)
        
        # Callbacks Desacoplados
        self.on_vitoria = None
        self.on_derrota = None
        self.on_fuga = None
        
        # Estados do Motor de Combate:
        # "INATIVO", "MENU_PRINCIPAL", "SUBMENU_ATAQUE", "SUBMENU_MAGIA", 
        # "SUBMENU_CONCENTRAR", "SUBMENU_ITENS", "SELECIONANDO_ALVO", "EXECUTANDO_ACAO", "TURNO_INIMIGO", "VITORIA", "DERROTA", "FUGIU"
        self.estado_combate = "INATIVO"
        
        # Log e Mensagens de Batalha
        self.historico_log = []
        self.mensagem_atual = ""
        self.timer_acao = 0
        self.textos_flutuantes = []
        
        # Efeitos Visuais e Interpolação de Barras
        self.vidas_visuais = {}
        self.manas_visuais = {}
        self.shake_timers = {}
        self.tick_arena = 0
        
        # Efeitos Visuais de Sangue (Halia) e Morte de Inimigos
        self.efeitos_sangue = []
        self.alphas_morte = {}
        self._pastas_sangue = [f"efeitos/sangue/sangue_{i}" for i in range(1, 6)]
        self._cache_sangue_frames = None

        # Efeitos Visuais Mágicos (Projéteis Direcionados, Flashes e Explosões em Área)
        self.efeitos_visuais = CombatVisualEffects(self)

        # Hitboxes de Interação de Mouse
        self.rects_menu_principal = []
        self.rects_ataques_fisicos = []
        self.rects_magias = []
        self.rects_concentrar = []
        self.rects_itens_combate = []
        self.rects_inimigos = []
        self.rect_botao_voltar = pygame.Rect(0, 0, 0, 0)
        self.rect_scroll_cima = pygame.Rect(0, 0, 0, 0)
        self.rect_scroll_baixo = pygame.Rect(0, 0, 0, 0)
        self.rect_banner = pygame.Rect(0, 0, 0, 0)
        
        # Sistema de Rolagem (Scroll) nos Submenus de Ações
        self.scroll_ataque = 0
        self.scroll_magia = 0
        self.scroll_concentrar = 0
        self.ITENS_POR_PAGINA_SUBMENU = 4
        
        # Recompensas Acumuladas
        self.recompensas_vitoria = {"moedas": 0, "memorias": 0, "xp": 0}

    def _tocar_sfx(self, alias, volume_extra=1.0):
        """Dispara efeito sonoro via AudioManager com tolerância a falhas."""
        audio = AudioManager.get_instance()
        if audio:
            audio.tocar_sfx(alias, volume_extra=volume_extra)

    def definir_velocidade(self, fator_velocidade):
        """Define o multiplicador de velocidade de combate (1.0, 1.5, 2.0)."""
        self.velocidade_combate = max(0.5, float(fator_velocidade))

    def _ajustar_timer(self, duracao_base):
        """Calcula a duração em ticks considerando a velocidade do combate."""
        return max(15, int(duracao_base / self.velocidade_combate))

    def _obter_frames_sangue(self):
        """Carrega e armazena em cache as listas de frames das 5 variações de sangue."""
        if self._cache_sangue_frames is None:
            self._cache_sangue_frames = []
            for pasta in self._pastas_sangue:
                frames = ResourceManager.carregar_frames_pasta(pasta)
                if frames:
                    self._cache_sangue_frames.append(frames)
        return self._cache_sangue_frames

    def _disparar_sangue_halia(self):
        """Dispara animação de respingo de sangue sobre o torso de Halia ao sofrer dano."""
        banco = self._obter_frames_sangue()
        if not banco:
            return
        frames_escolhidos = random.choice(banco)
        self.efeitos_sangue.append({
            "frames": frames_escolhidos,
            "frame_atual": 0.0,
            "velocidade": 0.90,
            "offset_x": random.randint(-4, 4),
            "offset_y": random.randint(-4, 4)
        })

    # =========================================================================
    # INICIALIZAÇÃO DO COMBATE
    # =========================================================================

    def iniciar_combate(self, jogador, inimigos, on_vitoria=None, on_derrota=None, on_fuga=None):
        """Prepara e inicia uma nova sessão de combate."""
        self.jogador = jogador
        self.inimigos = [i for i in inimigos if getattr(i, 'vivo', True)]
        for inim in self.inimigos:
            if getattr(inim, 'eh_mimico', False):
                inim.finalizar_revelacao()
        self.on_vitoria = on_vitoria
        self.on_derrota = on_derrota
        self.on_fuga = on_fuga
        
        self.indice_menu = 0
        self.indice_ataque_fisico = 0
        self.indice_magia = 0
        self.indice_concentrar = 0
        self.indice_alvo = 0
        self.scroll_ataque = 0
        self.scroll_magia = 0
        self.scroll_concentrar = 0
        self.acao_selecionada = None
        self.textos_flutuantes.clear()
        self.historico_log.clear()
        self.shake_timers.clear()
        self.efeitos_sangue.clear()
        self.alphas_morte.clear()
        self.efeitos_visuais.limpar()

        # Inicia a trilha sonora de combate adequada ao perigo
        audio = AudioManager.get_instance()
        if audio:
            nomes_inimigos = " ".join([getattr(i, 'nome', '').lower() for i in self.inimigos])
            if "drag" in nomes_inimigos:
                audio.tocar_musica("combate_dragao")
            elif any(isinstance(i, Boss) or getattr(i, 'eh_chefe', False) or "superior" in getattr(i, 'nome', '').lower() for i in self.inimigos):
                audio.tocar_musica("combate_chefe")
            else:
                audio.tocar_musica("combate_comum")
        
        # Inicializa valores visuais de HP e MP
        self.vidas_visuais[self.jogador] = float(self.jogador.vida_atual)
        self.manas_visuais[self.jogador] = float(self.jogador.mana_atual)
        for inimigo in self.inimigos:
            self.vidas_visuais[inimigo] = float(inimigo.vida_atual)
            self.manas_visuais[inimigo] = float(getattr(inimigo, 'mana_atual', getattr(inimigo, 'mana_maxima', 20)))

        # Notifica jogador
        if hasattr(self.jogador, 'entrar_combate'):
            self.jogador.entrar_combate()

        # Carrega ações físicas, grimório, itens e grupo de concentração do jogador
        self._carregar_ataques_fisicos_jogador()
        self._carregar_magias_jogador()
        self._carregar_acoes_concentrar()
        self._carregar_itens_combate_jogador()

        # Estabelece a ordem de turnos base uma única vez no início do combate
        participantes = [self.jogador] + [i for i in self.inimigos if getattr(i, 'vivo', True)]
        self.ordem_turnos_base = sorted(
            participantes,
            key=lambda ent: ent.calcular_iniciativa() if hasattr(ent, 'calcular_iniciativa') else 10,
            reverse=True
        )

        self.adicionar_log(CombatNarrator.obter_mensagem("inicio_batalha"))
        self._iniciar_nova_rodada()

    def _carregar_ataques_fisicos_jogador(self):
        """Carrega a lista de ataques físicos disponíveis para a Halia."""
        self.ataques_fisicos_disponiveis.clear()
        ids_fisicos = getattr(self.jogador, 'ataques_fisicos', ["ataque_basico", "golpe_concentrado"])
        for id_f in ids_fisicos:
            acao = SkillsRegistry.get(id_f)
            if acao:
                self.ataques_fisicos_disponiveis.append(acao)

    def _carregar_magias_jogador(self):
        """Carrega a lista de magias desbloqueadas no Grimório da Halia."""
        self.magias_disponiveis.clear()
        if hasattr(self.jogador, 'atualizar_grimorio'):
            self.jogador.atualizar_grimorio()
        ids_magias = getattr(self.jogador, 'magias_desbloqueadas', ["bola_de_fogo", "levitar", "brisa_curativa"])
        for id_magia in ids_magias:
            acao = SkillsRegistry.get(id_magia)
            if acao:
                self.magias_disponiveis.append(acao)

    def _carregar_acoes_concentrar(self):
        """Carrega o grupo de ações táticas de Concentração (Foco Espiritual e Defender)."""
        self.opcoes_concentrar.clear()
        foco = SkillsRegistry.get("foco_espiritual")
        defesa = SkillsRegistry.get("defender")
        if foco:
            self.opcoes_concentrar.append(foco)
        if defesa:
            self.opcoes_concentrar.append(defesa)

    def _carregar_itens_combate_jogador(self):
        """Carrega os itens consumíveis elegíveis para uso durante a batalha."""
        self.itens_combate_disponiveis.clear()
        inv = getattr(self.jogador, 'inventario', None)
        if inv:
            for idx_real, item_slot in enumerate(inv.slots):
                item = item_slot.item
                if getattr(item, 'categoria', '') == "CONSUMIVEL" and getattr(item, 'usavel_combate', True):
                    self.itens_combate_disponiveis.append((idx_real, item_slot))

    def _iniciar_nova_rodada(self):
        """Prepara a rodada mantendo a ordem consistente de turnos entre participantes vivos."""
        return self.ai_controller.iniciar_nova_rodada()

    def _avancar_para_proximo_turno(self):
        """Avança a vez para a próxima entidade viva da fila."""
        return self.ai_controller.avancar_para_proximo_turno()

    # =========================================================================
    # PROCESSAMENTO DE EVENTOS E NAVEGAÇÃO (DELEGADO PARA CombatInputHandler)
    # =========================================================================

    def _ajustar_scroll_submenu(self, estado):
        """Garante que o item selecionado pelo teclado esteja sempre visível na janela de rolagem."""
        self.input_handler.ajustar_scroll_submenu(estado)

    def _rolar_submenu(self, estado, delta):
        """Rola a visualização do submenu para cima ou para baixo pelo mouse ou botões de seta."""
        self.input_handler.rolar_submenu(estado, delta)

    def processar_eventos(self, evento):
        """Processa eventos de mouse e teclado via CombatInputHandler."""
        self.input_handler.processar_eventos(evento)

    def _selecionar_opcao_menu_principal(self):
        """Encaminha seleção de opção do menu principal para CombatInputHandler."""
        self.input_handler.selecionar_opcao_menu_principal()

    def _selecionar_item_combate(self):
        """Encaminha seleção de item consumível para CombatInputHandler."""
        self.input_handler.selecionar_item_combate()

    def _executar_uso_item_suporte(self, item):
        """Executa consumível de cura ou suporte em Halia durante o combate."""
        pode, msg = item.pode_usar(self.jogador, em_combate=True)
        if not pode:
            self._tocar_sfx("ui_erro")
            self.adicionar_log(f"Aviso: {msg}")
            return

        inv = getattr(self.jogador, 'inventario', None)
        if inv:
            inv.remover_item(item.id, 1)

        self.estado_combate = "EXECUTANDO_ACAO"
        self.timer_acao = self._ajustar_timer(60)

        res = item.usar(self.jogador, em_combate=True)
        if res.get("mensagem"):
            self.adicionar_log(res["mensagem"])

        hx, hy = self._obter_posicao_combate(self.jogador)
        if res.get("tipo") == "CURA_HP" and res.get("valor", 0) > 0:
            self.adicionar_texto_flutuante(f"+{res['valor']}", hx + 30, hy - 10, BARRA_VIDA_JOGADOR)
        elif res.get("tipo") == "RESTAURA_MP" and res.get("valor", 0) > 0:
            self.adicionar_texto_flutuante(f"+{res['valor']} MP", hx + 30, hy - 10, BARRA_MANA)
        elif res.get("tipo") == "CURA_CONDICAO":
            self.adicionar_texto_flutuante(CombatNarrator.obter_popup("purificado"), hx + 10, hy - 10, (160, 230, 200))

    def _executar_uso_item_ofensivo(self, item, alvo):
        """Arremessa frasco ou item ofensivo em um inimigo durante a batalha."""
        inv = getattr(self.jogador, 'inventario', None)
        if inv:
            inv.remover_item(item.id, 1)

        self.item_combate_selecionado = None
        self.estado_combate = "EXECUTANDO_ACAO"
        self.timer_acao = self._ajustar_timer(65)

        res = item.usar(self.jogador, alvo=alvo, em_combate=True)
        if res.get("mensagem"):
            self.adicionar_log(res["mensagem"])

        dano = res.get("valor", 0)
        ax, ay = self._obter_posicao_combate(alvo)
        if dano > 0:
            self.shake_timers[alvo] = self._ajustar_timer(15)
            self.adicionar_texto_flutuante(f"-{dano}", ax + 20, ay - 10, (255, 100, 80))

        if not getattr(alvo, 'vivo', True):
            if hasattr(alvo, 'animacoes'):
                alvo.morrer()
                est_m = "dead" if "dead" in alvo.animacoes else ("morte" if "morte" in alvo.animacoes else "morrer")
                if est_m in alvo.animacoes:
                    alvo.definir_estado(est_m)
                    if hasattr(alvo.animacoes[est_m], 'resetar'):
                        alvo.animacoes[est_m].resetar()
            self.alphas_morte[alvo] = 255
            msg_morte = f"{alvo.nome} foi destruído pelo impacto de {item.nome}!"
            self.adicionar_log(msg_morte)
            self.adicionar_texto_flutuante(CombatNarrator.obter_popup("derrotado"), ax + 10, ay - 30, (255, 60, 60))

    def _selecionar_ataque_fisico(self):
        """Encaminha seleção de ataque físico para CombatInputHandler."""
        self.input_handler.selecionar_ataque_fisico()

    def _selecionar_acao_concentrar(self):
        """Encaminha seleção de ação de concentração para CombatInputHandler."""
        self.input_handler.selecionar_acao_concentrar()

    def _selecionar_magia_grimorio(self):
        """Encaminha seleção de magia para CombatInputHandler."""
        self.input_handler.selecionar_magia_grimorio()

    def _gerar_mensagem_morte_condicao(self, entidade, relatorios):
        """Gera mensagem contextual dramática quando a entidade morre por DoT no início do turno."""
        return CombatNarrator.gerar_mensagem_morte_condicao(entidade, relatorios, eh_jogador=(entidade is self.jogador))

    def _gerar_mensagem_morte_acao(self, alvo, acao):
        """Gera mensagem contextual dramática quando a entidade morre por um ataque/magia direta."""
        return CombatNarrator.gerar_mensagem_morte_acao(alvo, acao, eh_jogador=(alvo is self.jogador))

    def _executar_acao_jogador(self, acao, alvo):
        """Executa a ação escolhida pelo jogador com cálculo de dano e feedback."""
        if not acao:
            acao = SkillsRegistry.get("ataque_basico")

        self.estado_combate = "EXECUTANDO_ACAO"
        self.timer_acao = self._ajustar_timer(75)
        
        resultado = acao.executar(self.jogador, alvo)
        
        # 1. Trata mensagem única direta (ex: Foco, Defesa, Escudo)
        if resultado.get("mensagem"):
            self.adicionar_log(resultado["mensagem"])

        # Redundância imediata no Log: garante que 100% das ações e feitiços da Halia aparecem no histórico
        for r_entry in resultado.get("resultados", []):
            r_data = r_entry.get("dados") if ("dados" in r_entry and isinstance(r_entry["dados"], dict)) else r_entry
            msg_alvo = r_data.get("mensagem")
            if not msg_alvo:
                alvo_obj = r_data.get("alvo", alvo)
                alvo_nome = getattr(alvo_obj, "nome", "o inimigo")
                if r_data.get("errou"):
                    if r_data.get("motivo") == "esquiva":
                        msg_alvo = f"{self.jogador.nome} usou {acao.nome}, mas {alvo_nome} se esquivou agilmente!"
                    else:
                        msg_alvo = f"{self.jogador.nome} usou {acao.nome}, mas errou o ataque contra {alvo_nome}!"
                elif r_data.get("dano", 0) > 0:
                    crit_txt = " (CRÍTICO!)" if r_data.get("critico") else ""
                    msg_alvo = f"{self.jogador.nome} usou {acao.nome} em {alvo_nome} causando {r_data['dano']} de dano{crit_txt}."
                elif r_data.get("cura", 0) > 0:
                    msg_alvo = f"{self.jogador.nome} usou {acao.nome} restaurando {r_data['cura']} de vida."
            if msg_alvo:
                self.adicionar_log(msg_alvo)
                r_entry["_log_registrado"] = True
                r_data["_log_registrado"] = True

        hx, hy = self._obter_posicao_combate(self.jogador)
        cura_direta = float(resultado.get("cura", 0) or 0)
        if cura_direta > 0:
            self._tocar_sfx("item_pocao")
            cura_fmt = int(cura_direta) if cura_direta.is_integer() else f"{cura_direta:.1f}"
            self.adicionar_texto_flutuante(f"+{cura_fmt}", hx + 30, hy - 10, BARRA_VIDA_JOGADOR)
        
        mana_rec = float(resultado.get("mana_recuperada", 0) or 0)
        if mana_rec > 0:
            self._tocar_sfx("concentrar")
            mana_fmt = int(mana_rec) if mana_rec.is_integer() else f"{mana_rec:.1f}"
            self.adicionar_texto_flutuante(f"+{mana_fmt} MP", hx + 30, hy + 15, BARRA_MANA, duracao=80)
        if resultado.get("defendendo"):
            self._tocar_sfx("concentrar")
            self.adicionar_texto_flutuante(CombatNarrator.obter_popup("em_guarda"), hx + 30, hy - 10, (100, 210, 255), duracao=80)
        if resultado.get("vulneravel"):
            self.adicionar_texto_flutuante(CombatNarrator.obter_popup("vulneravel"), hx + 30, hy - 10, (240, 130, 130), duracao=80)

        # Conquista: Mente Inabalável (Foco Espiritual ou Defender)
        id_acao_atual = getattr(acao, 'id_acao', getattr(acao, 'id', ''))
        if id_acao_atual in ["foco_espiritual", "defender"] or getattr(acao, 'tipo', '').upper() == "FOCO" or resultado.get("defendendo") or mana_rec > 0:
            if hasattr(self, 'game') and hasattr(self.game, 'conquistas') and self.game.conquistas:
                self.game.conquistas.desbloquear("foco_espiritual")

        # Se for magia de ataque ou suporte
        if getattr(acao, 'custo_mana', 0) > 0 or getattr(acao, 'tipo', '').upper() == 'MAGIA':
            self._tocar_sfx("magia_cast")

        # Função de resolução de impacto individual nos alvos (chamada ao atingir ou imediata)
        def _aplicar_impacto_alvo(alvo_r, r):
            if "dados" in r and isinstance(r["dados"], dict):
                r = r["dados"]
            if r.get("mensagem") and not r.get("_log_registrado") and r.get("mensagem") != resultado.get("mensagem"):
                self.adicionar_log(r["mensagem"])
                r["_log_registrado"] = True
                
            dano_r = float(r.get("dano", 0) or 0)
            cura_r = float(r.get("cura", 0) or 0)
            ax, ay = self._obter_posicao_combate(alvo_r) if alvo_r else (self.largura - 350, 150)

            if r.get("errou", False) and alvo_r:
                motivo_erro = r.get("motivo", "erro")
                if motivo_erro == "esquiva":
                    self._tocar_sfx("esquiva")
                    texto_erro = CombatNarrator.obter_popup("esquivou")
                    cor_erro = (100, 210, 255) # Cyan
                else:
                    self._tocar_sfx("ataque_erro")
                    texto_erro = CombatNarrator.obter_popup("errou")
                    cor_erro = (240, 160, 100) # Âmbar
                self.adicionar_texto_flutuante(texto_erro, ax + 20, ay - 15, cor_erro, duracao=80)
                # Efeito visual suave de erro/falha (sem explosão de impacto ou tremor)
                elem_acao = getattr(acao, 'elemento', 'ARCANO')
                self.efeitos_visuais.adicionar_dissipacao_erro(ax + 20, ay, elemento=elem_acao, motivo=motivo_erro)
            elif dano_r > 0 and alvo_r:
                if r.get("critico", False):
                    self._tocar_sfx("ataque_critico")
                else:
                    self._tocar_sfx("ataque_acerto")
                self._tocar_sfx("dano_inimigo")

                dano_fmt = int(dano_r) if dano_r.is_integer() else f"{dano_r:.1f}"
                self.adicionar_texto_flutuante(f"-{dano_fmt}", ax + 20, ay, TEXTO_ALERTA_COMBATE)
                self.shake_timers[alvo_r] = 14
                # Ativa animação de dano ou morte no inimigo
                if hasattr(alvo_r, 'definir_estado') and hasattr(alvo_r, 'animacoes'):
                    if not getattr(alvo_r, 'vivo', True):
                        alvo_r.morrer()
                        est_m = "dead" if "dead" in alvo_r.animacoes else ("morte" if "morte" in alvo_r.animacoes else "morrer")
                        if est_m in alvo_r.animacoes:
                            alvo_r.definir_estado(est_m)
                            if hasattr(alvo_r.animacoes[est_m], 'resetar'):
                                alvo_r.animacoes[est_m].resetar()
                        self.alphas_morte[alvo_r] = 255
                    elif "hurt" in alvo_r.animacoes or "dano" in alvo_r.animacoes:
                        est_h = "hurt" if "hurt" in alvo_r.animacoes else "dano"
                        alvo_r.definir_estado(est_h)
                        if hasattr(alvo_r.animacoes[est_h], 'resetar'):
                            alvo_r.animacoes[est_h].resetar()

                if alvo_r is self.jogador:
                    self._disparar_sangue_halia()

                # Feedback narrativo se o alvo foi derrotado
                if not getattr(alvo_r, 'vivo', True):
                    msg_morte = self._gerar_mensagem_morte_acao(alvo_r, acao)
                    self.adicionar_log(msg_morte)
            elif cura_r > 0 and alvo_r:
                self._tocar_sfx("magia_cast")
                cura_fmt = int(cura_r) if cura_r.is_integer() else f"{cura_r:.1f}"
                self.adicionar_texto_flutuante(f"+{cura_fmt}", ax + 20, ay - 10, BARRA_VIDA_JOGADOR)

        # 2. Executa a apresentação visual: projéteis e explosões direcionadas em magias e AoE
        eh_aoe = (
            getattr(acao, 'alvo_tipo', '') in ["TODOS_INIMIGOS", "TODOS"] or
            getattr(acao, 'tipo_alvo', '') in ["todos_inimigos", "todos"] or
            len(resultado.get("resultados", [])) > 1
        )
        eh_magia = (
            getattr(acao, 'custo_mana', 0) > 0 or 
            getattr(acao, 'tipo', '').upper() == 'MAGIA' or 
            getattr(acao, 'tipo_dano', '') == 'MAGICO'
        )

        alvos_com_dados = [r for r in resultado.get("resultados", []) if r.get("alvo")]

        if (eh_aoe or eh_magia) and alvos_com_dados:
            if eh_aoe:
                self.timer_acao = self._ajustar_timer(85)
                self.efeitos_visuais.disparar_magia_aoe(
                    acao, self.jogador, alvos_com_dados, on_impacto_alvo=_aplicar_impacto_alvo
                )
            else:
                self.timer_acao = self._ajustar_timer(75)
                self.efeitos_visuais.disparar_magia_alvo(
                    acao, self.jogador, alvos_com_dados[0]["alvo"], alvos_com_dados[0], on_impacto_alvo=_aplicar_impacto_alvo
                )
        else:
            for r in resultado.get("resultados", []):
                _aplicar_impacto_alvo(r.get("alvo"), r)

    def _executar_turno_inimigo(self, inimigo):
        """IA do inimigo: seleciona habilidade temática e executa contra Halia."""
        return self.ai_controller.executar_turno_inimigo(inimigo)

    def _tentar_fuga(self):
        """Calcula a probabilidade de fuga baseada na Destreza, quantidade e força dos inimigos."""
        return self.ai_controller.tentar_fuga()

    # =========================================================================
    # ATUALIZAÇÃO DO MOTOR DE COMBATE
    # =========================================================================

    def atualizar(self):
        """Loop de atualização de timers, interpolação suave e turnos."""
        self.tick_arena += 1

        # Atualiza interpolação suave de HP e MP
        if self.jogador:
            v_atual = self.vidas_visuais.get(self.jogador, float(self.jogador.vida_atual))
            self.vidas_visuais[self.jogador] += (self.jogador.vida_atual - v_atual) * 0.18
            
            m_atual = self.manas_visuais.get(self.jogador, float(self.jogador.mana_atual))
            self.manas_visuais[self.jogador] += (self.jogador.mana_atual - m_atual) * 0.18

        for inimigo in self.inimigos:
            v_atual = self.vidas_visuais.get(inimigo, float(inimigo.vida_atual))
            self.vidas_visuais[inimigo] += (inimigo.vida_atual - v_atual) * 0.18
            
            m_atual = self.manas_visuais.get(inimigo, float(getattr(inimigo, 'mana_atual', 0)))
            self.manas_visuais[inimigo] += (getattr(inimigo, 'mana_atual', 0) - m_atual) * 0.18

        # Atualiza timers de tremor (shake)
        for ent in list(self.shake_timers.keys()):
            if self.shake_timers[ent] > 0:
                self.shake_timers[ent] -= 1
            else:
                del self.shake_timers[ent]

        # Atualiza textos flutuantes
        self.textos_flutuantes = [t for t in self.textos_flutuantes if t.atualizar()]

        # Atualiza efeitos visuais de sangue na Halia
        for ef in self.efeitos_sangue[:]:
            ef["frame_atual"] += ef["velocidade"]
            if int(ef["frame_atual"]) >= len(ef["frames"]):
                self.efeitos_sangue.remove(ef)

        # Atualiza efeitos visuais mágicos (projéteis direcionados e explosões)
        self.efeitos_visuais.atualizar(1.0)

        # Atualiza desvanecimento suave (fade out) dos monstros derrotados após término da animação de morte
        for inimigo in self.inimigos:
            if not getattr(inimigo, 'vivo', True):
                anim_m = inimigo.animacoes.get('dead') or inimigo.animacoes.get('morte') or inimigo.animacoes.get('morrer')
                esta_concluida = getattr(anim_m, 'concluida', False) if anim_m else True
                if esta_concluida:
                    alpha_atual = self.alphas_morte.get(inimigo, 255)
                    if alpha_atual > 0:
                        self.alphas_morte[inimigo] = max(0, alpha_atual - 5)

        # Execução de timer de leitura de ação
        if self.estado_combate == "EXECUTANDO_ACAO":
            if self.timer_acao > 0:
                self.timer_acao -= 1
            else:
                # Se Halia foi derrotada nesta ação, transiciona diretamente para DERROTA
                if not getattr(self.jogador, 'vivo', True) or self.jogador.vida_atual <= 0:
                    self._finalizar_derrota()
                    return self.estado_combate
                self.indice_turno_atual += 1
                self._avancar_para_proximo_turno()

        # Execução do turno do inimigo
        elif self.estado_combate == "TURNO_INIMIGO":
            if self.timer_acao > 0:
                self.timer_acao -= 1
            else:
                if not getattr(self.jogador, 'vivo', True) or self.jogador.vida_atual <= 0:
                    self._finalizar_derrota()
                    return self.estado_combate
                if self.indice_turno_atual < len(self.ordem_turnos):
                    inimigo_atual = self.ordem_turnos[self.indice_turno_atual]
                    self._executar_turno_inimigo(inimigo_atual)
                else:
                    self._avancar_para_proximo_turno()

        # Checagem de segurança geral de derrota
        if (not getattr(self.jogador, 'vivo', True) or self.jogador.vida_atual <= 0) and self.estado_combate not in ["DERROTA", "VITORIA", "FUGIU"]:
            if getattr(self, 'timer_acao', 0) <= 0:
                self._finalizar_derrota()

        return self.estado_combate

    # =========================================================================
    # RESOLUÇÃO DE BATALHA (VITÓRIA / DERROTA / RECOMPENSAS)
    # =========================================================================

    def _finalizar_vitoria(self):
        """Distribui recompensas acumuladas de todos os inimigos e exibe banner."""
        return self.ai_controller.finalizar_vitoria()

    def _finalizar_derrota(self):
        """Configura estado de derrota."""
        return self.ai_controller.finalizar_derrota()

    def _concluir_fechamento_combate(self):
        """Dispara os callbacks configurados ao encerrar e restaura a trilha do mapa."""
        return self.ai_controller.concluir_fechamento_combate()

    # =========================================================================
    # MÉTODOS DE LOG & QUEBRA DE LINHA (WORD WRAP)
    # =========================================================================

    def adicionar_log(self, mensagem):
        """Adiciona mensagens ao histórico aplicando quebra de linha com cores temáticas preservadas."""
        if not mensagem or not str(mensagem).strip():
            return
        mensagem = str(mensagem).strip()
        if self.mensagem_atual == mensagem and self.historico_log:
            return
        self.mensagem_atual = mensagem
        
        # 1. Determina a cor temática da mensagem completa
        msg_low = mensagem.lower()
        if "esquivou" in msg_low:
            cor_msg = (120, 210, 255) # Cyan
        elif "errou" in msg_low:
            cor_msg = (245, 170, 110) # Âmbar
        elif "crítico" in msg_low or "crítico" in mensagem or "CRÍTICO" in mensagem:
            cor_msg = (255, 220, 90)  # Dourado
        elif "recuperou" in msg_low or "curou" in msg_low or "regenerou" in msg_low:
            cor_msg = (110, 235, 130) # Verde
        elif any(w in msg_low for w in ["sucumbiu", "carbonizado", "desintegrado", "aniquilado", "estraçalhado", "derrotada", "derrotado", "sem vida"]):
            cor_msg = (255, 115, 115) # Vermelho suave dramático para derrotas / fatalidades
        elif "perdeu o turno" in msg_low or "atordoado" in msg_low:
            cor_msg = (245, 130, 180) # Magenta/Lilás
        else:
            cor_msg = None # Usa cor padrão (Branco para mais recente / Cinza claro para anteriores)

        # 2. Largura total disponível na seção de log (~760px)
        largura_util_log = 760
        linhas_quebradas = quebrar_texto_em_linhas(mensagem, self.fonte_log, largura_util_log)
        
        for linha in linhas_quebradas:
            self.historico_log.append({"texto": linha, "cor": cor_msg})

        # Mantém histórico em tamanho adequado para scroll visual limpo
        if len(self.historico_log) > 16:
            self.historico_log = self.historico_log[-16:]

    def adicionar_texto_flutuante(self, texto, x, y, cor=TEXTO_ALERTA_COMBATE, duracao=60):
        duracao_ajustada = self._ajustar_timer(duracao)
        self.textos_flutuantes.append(TextoFlutuante(texto, x, y, cor=cor, duracao=duracao_ajustada))

    def _obter_inimigos_vivos(self):
        return [i for i in self.inimigos if getattr(i, 'vivo', True)]

    def _obter_posicao_combate(self, entidade):
        """Retorna as coordenadas (x, y) de base na arena de combate para uma entidade."""
        if entidade is self.jogador:
            return 160, 160

        if entidade in self.inimigos:
            idx = self.inimigos.index(entidade)
            total = len(self.inimigos)
            if total == 1:
                return self.largura - 350, 150
            elif total == 2:
                return self.largura - 350, 65 if idx == 0 else 235
            else:
                if idx == 0:
                    return self.largura - 260, 48
                elif idx == 1:
                    return self.largura - 430, 155
                else:
                    return self.largura - 260, 262

        return getattr(entidade, 'x', 160), getattr(entidade, 'y', 160)

    # =========================================================================
    # RENDERIZAÇÃO GRÁFICA (DELEGADA PARA CombatRenderer)
    # =========================================================================

    def desenhar_barra(self, tela, x, y, valor_atual, valor_maximo, cor_barra, cor_fundo=FUNDO_BARRA, largura=180, altura=12):
        """Encaminha para o renderizador gráfico desacoplado."""
        self.renderer.desenhar_barra(tela, x, y, valor_atual, valor_maximo, cor_barra, cor_fundo=cor_fundo, largura=largura, altura=altura)

    def _desenhar_cabecalho_e_scrollbar_submenu(self, tela, painel_rect, largura_secao_menu, total_itens, scroll_atual, titulo=""):
        """Encaminha para o renderizador gráfico desacoplado."""
        self.renderer.desenhar_cabecalho_e_scrollbar_submenu(tela, painel_rect, largura_secao_menu, total_itens, scroll_atual, titulo=titulo)

    def desenhar(self, tela):
        """Renderiza a arena, personagens, HUDs, menus, submenus, tooltips e banners via CombatRenderer."""
        self.renderer.desenhar(tela)

    def _desenhar_tooltip_acao(self, tela, acao, x, y_bottom, largura_max=None):
        """Encaminha para o renderizador gráfico desacoplado."""
        self.renderer.desenhar_tooltip_acao(tela, acao, x, y_bottom, largura_max=largura_max)

    def _desenhar_banner_fim_combate(self, tela):
        """Encaminha para o renderizador gráfico desacoplado."""
        self.renderer.desenhar_banner_fim_combate(tela)
