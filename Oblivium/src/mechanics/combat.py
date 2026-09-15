# src/mechanics/combat.py
import pygame
import random
import math
import os
import sys

# Garante que a pasta raiz do projeto ('Oblivium') esteja no sys.path
_raiz_projeto = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _raiz_projeto not in sys.path:
    sys.path.insert(0, _raiz_projeto)

from src.mechanics.skills import SkillsRegistry
from src.mechanics.conditions import Condicao
from src.mechanics.grimorio import GrimorioHalia
from src.entities.Enemy import Enemy
from src.entities.Boss import Boss
from src.ui.ui_utils import (
    desenhar_painel_padrao, desenhar_barra_status_interpolada,
    quebrar_texto_em_linhas, desenhar_tooltip_formatado, desenhar_badge_status
)
from src.utils.colors import (
    UI_FUNDO_PADRAO, CINZA_CLARO, CINZA_ESCURO, UI_TEXTO_DESTAQUE, 
    UI_TEXTO_APAGADO, TXT_SISTEMA_NARRADOR, TXT_PENSAMENTO_INTERNO,
    NOME_HALIA, NOME_MALDICAO, TEXTO_ALERTA_COMBATE,
    BARRA_VIDA_JOGADOR, BARRA_VIDA_INIMIGO, BARRA_MANA, FUNDO_BARRA,
    BRANCO, PRETO, BOTAO_FECHAR_NORMAL, BOTAO_FECHAR_HOVER
)

class TextoFlutuante:
    """Gerencia textos flutuantes de dano, cura ou status na tela de combate."""
    def __init__(self, texto, x, y, cor=TEXTO_ALERTA_COMBATE, duracao=60, velocidade_y=-1.3):
        self.texto = str(texto)
        self.x = float(x)
        self.y = float(y)
        self.cor = cor
        self.duracao = duracao
        self.vida = duracao
        self.velocidade_y = velocidade_y

    def atualizar(self):
        self.y += self.velocidade_y
        self.vida -= 1
        return self.vida > 0

    def desenhar(self, tela, fonte):
        if self.vida <= 0: return
        alpha = max(0, min(255, int((self.vida / self.duracao) * 255)))
        superficie = fonte.render(self.texto, True, self.cor)
        superficie.set_alpha(alpha)
        # Sombra suave para contraste
        sombra = fonte.render(self.texto, True, PRETO)
        sombra.set_alpha(int(alpha * 0.7))
        tela.blit(sombra, (int(self.x) + 2, int(self.y) + 2))
        tela.blit(superficie, (int(self.x), int(self.y)))


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
        
        # Fontes do Combate
        self.fonte_titulo = pygame.font.Font(None, 42)
        self.fonte_nomes = pygame.font.Font(None, 32)
        self.fonte_status = pygame.font.Font(None, 22)
        self.fonte_menu = pygame.font.Font(None, 30)
        self.fonte_log = pygame.font.Font(None, 24)
        self.fonte_dano = pygame.font.Font(None, 34)
        self.fonte_tooltip = pygame.font.Font(None, 22)
        
        # Estrutura do Menu Principal
        self.opcoes_menu_principal = ["Atacar", "Magias", "Concentrar", "Fugir"]
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
        # "SUBMENU_CONCENTRAR", "SELECIONANDO_ALVO", "EXECUTANDO_ACAO", "TURNO_INIMIGO", "VITORIA", "DERROTA", "FUGIU"
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
        
        # Hitboxes de Interação de Mouse
        self.rects_menu_principal = []
        self.rects_ataques_fisicos = []
        self.rects_magias = []
        self.rects_concentrar = []
        self.rects_inimigos = []
        self.rect_botao_voltar = pygame.Rect(0, 0, 0, 0)
        self.rect_banner = pygame.Rect(0, 0, 0, 0)
        
        # Recompensas Acumuladas
        self.recompensas_vitoria = {"moedas": 0, "memorias": 0, "xp": 0}

    def definir_velocidade(self, fator_velocidade):
        """Define o multiplicador de velocidade de combate (1.0, 1.5, 2.0)."""
        self.velocidade_combate = max(0.5, float(fator_velocidade))

    def _ajustar_timer(self, duracao_base):
        """Calcula a duração em ticks considerando a velocidade do combate."""
        return max(15, int(duracao_base / self.velocidade_combate))

    # =========================================================================
    # INICIALIZAÇÃO DO COMBATE
    # =========================================================================

    def iniciar_combate(self, jogador, inimigos, on_vitoria=None, on_derrota=None, on_fuga=None):
        """Prepara e inicia uma nova sessão de combate."""
        self.jogador = jogador
        self.inimigos = [i for i in inimigos if getattr(i, 'vivo', True)]
        self.on_vitoria = on_vitoria
        self.on_derrota = on_derrota
        self.on_fuga = on_fuga
        
        self.indice_menu = 0
        self.indice_ataque_fisico = 0
        self.indice_magia = 0
        self.indice_concentrar = 0
        self.indice_alvo = 0
        self.acao_selecionada = None
        self.textos_flutuantes.clear()
        self.historico_log.clear()
        self.shake_timers.clear()
        
        # Inicializa valores visuais de HP e MP
        self.vidas_visuais[self.jogador] = float(self.jogador.vida_atual)
        self.manas_visuais[self.jogador] = float(self.jogador.mana_atual)
        for inimigo in self.inimigos:
            self.vidas_visuais[inimigo] = float(inimigo.vida_atual)
            self.manas_visuais[inimigo] = float(getattr(inimigo, 'mana_atual', getattr(inimigo, 'mana_maxima', 20)))

        # Notifica jogador
        if hasattr(self.jogador, 'entrar_combate'):
            self.jogador.entrar_combate()

        # Carrega ações físicas, grimório e grupo de concentração do jogador
        self._carregar_ataques_fisicos_jogador()
        self._carregar_magias_jogador()
        self._carregar_acoes_concentrar()

        # Estabelece a ordem de turnos base uma única vez no início do combate
        participantes = [self.jogador] + [i for i in self.inimigos if getattr(i, 'vivo', True)]
        self.ordem_turnos_base = sorted(
            participantes,
            key=lambda ent: ent.calcular_iniciativa() if hasattr(ent, 'calcular_iniciativa') else 10,
            reverse=True
        )

        self.adicionar_log("A batalha começou!")
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

    def _iniciar_nova_rodada(self):
        """Prepara a rodada mantendo a ordem consistente de turnos entre participantes vivos."""
        self.ordem_turnos = [p for p in self.ordem_turnos_base if getattr(p, 'vivo', True)]
        self.indice_turno_atual = 0
        self._avancar_para_proximo_turno()

    def _avancar_para_proximo_turno(self):
        """Avança a vez para a próxima entidade viva da fila."""
        # 1. Verifica se todos os inimigos foram derrotados
        inimigos_vivos = self._obter_inimigos_vivos()
        if not inimigos_vivos:
            self._finalizar_vitoria()
            return

        # 2. Verifica se o jogador foi derrotado
        if not getattr(self.jogador, 'vivo', True) or self.jogador.vida_atual <= 0:
            self._finalizar_derrota()
            return

        # 3. Se a rodada acabou, começa nova rodada mantendo a consistência dos turnos
        if self.indice_turno_atual >= len(self.ordem_turnos):
            self._iniciar_nova_rodada()
            return

        entidade_atual = self.ordem_turnos[self.indice_turno_atual]
        
        # Pula entidades mortas
        if not getattr(entidade_atual, 'vivo', True):
            self.indice_turno_atual += 1
            self._avancar_para_proximo_turno()
            return

        # Reseta postura temporária apenas no início do turno da própria entidade
        if hasattr(entidade_atual, 'resetar_turno_combate'):
            entidade_atual.resetar_turno_combate()

        # 4. Processa Condições / DoT / CC no início do turno
        if hasattr(entidade_atual, 'processar_condicoes_inicio_turno'):
            relatorios, impede_acao = entidade_atual.processar_condicoes_inicio_turno()
            for r in relatorios:
                if r.get("mensagem"):
                    self.adicionar_log(r["mensagem"])
                if r.get("dano", 0) > 0:
                    self.adicionar_texto_flutuante(f"-{r['dano']}", entidade_atual.x + 20, entidade_atual.y, TEXTO_ALERTA_COMBATE)
                    self.shake_timers[entidade_atual] = 8

            if not getattr(entidade_atual, 'vivo', True):
                msg_morte = self._gerar_mensagem_morte_condicao(entidade_atual, relatorios)
                self.adicionar_log(msg_morte)
                self.indice_turno_atual += 1
                self._avancar_para_proximo_turno()
                return

            if impede_acao:
                # Dá tempo para o jogador ler que a entidade perdeu o turno
                self.timer_acao = self._ajustar_timer(70)
                self.estado_combate = "EXECUTANDO_ACAO"
                return

        # 5. Define se é turno do Jogador ou IA do Inimigo
        if entidade_atual is self.jogador:
            # Regeneração passiva natural de mana por turno da Grã-Maga
            if self.jogador.mana_atual < self.jogador.mana_maxima:
                mana_reg = max(4, 4 + self.jogador.atributos.mod_sab + (self.jogador.atributos.mod_pre // 2))
                self.jogador.recuperar_mana(mana_reg)
                self.adicionar_texto_flutuante(f"+{mana_reg} MP", self.jogador.x + 30, self.jogador.y + 15, BARRA_MANA, duracao=60)

            self.estado_combate = "MENU_PRINCIPAL"
            self.indice_menu = 0
        else:
            self.estado_combate = "TURNO_INIMIGO"
            self.timer_acao = self._ajustar_timer(55)

    # =========================================================================
    # PROCESSAMENTO DE EVENTOS (TECLADO E MOUSE)
    # =========================================================================

    def processar_eventos(self, evento):
        # 1. Movimento do Mouse (Hover)
        if evento.type == pygame.MOUSEMOTION:
            pos = evento.pos
            if self.estado_combate == "MENU_PRINCIPAL":
                for idx, r in enumerate(self.rects_menu_principal):
                    if r.collidepoint(pos):
                        self.indice_menu = idx
                        break

            elif self.estado_combate == "SUBMENU_ATAQUE":
                for idx, r in enumerate(self.rects_ataques_fisicos):
                    if r.collidepoint(pos):
                        self.indice_ataque_fisico = idx
                        break

            elif self.estado_combate == "SUBMENU_MAGIA":
                for idx, r in enumerate(self.rects_magias):
                    if r.collidepoint(pos):
                        self.indice_magia = idx
                        break

            elif self.estado_combate == "SUBMENU_CONCENTRAR":
                for idx, r in enumerate(self.rects_concentrar):
                    if r.collidepoint(pos):
                        self.indice_concentrar = idx
                        break

            elif self.estado_combate == "SELECIONANDO_ALVO":
                for idx, r in enumerate(self.rects_inimigos):
                    if r.collidepoint(pos):
                        self.indice_alvo = idx
                        break

        # 2. Clique do Mouse (Botão Esquerdo)
        elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            pos = evento.pos
            
            # Telas finais: Clique em qualquer lugar fecha
            if self.estado_combate in ["VITORIA", "DERROTA", "FUGIU"]:
                self._concluir_fechamento_combate()
                return

            if self.estado_combate == "MENU_PRINCIPAL":
                for idx, r in enumerate(self.rects_menu_principal):
                    if r.collidepoint(pos):
                        self.indice_menu = idx
                        self._selecionar_opcao_menu_principal()
                        return

            elif self.estado_combate == "SUBMENU_ATAQUE":
                if self.rect_botao_voltar.collidepoint(pos):
                    self.estado_combate = "MENU_PRINCIPAL"
                    return
                for idx, r in enumerate(self.rects_ataques_fisicos):
                    if r.collidepoint(pos):
                        self.indice_ataque_fisico = idx
                        self._selecionar_ataque_fisico()
                        return

            elif self.estado_combate == "SUBMENU_MAGIA":
                if self.rect_botao_voltar.collidepoint(pos):
                    self.estado_combate = "MENU_PRINCIPAL"
                    return
                for idx, r in enumerate(self.rects_magias):
                    if r.collidepoint(pos):
                        self.indice_magia = idx
                        self._selecionar_magia_grimorio()
                        return

            elif self.estado_combate == "SUBMENU_CONCENTRAR":
                if self.rect_botao_voltar.collidepoint(pos):
                    self.estado_combate = "MENU_PRINCIPAL"
                    return
                for idx, r in enumerate(self.rects_concentrar):
                    if r.collidepoint(pos):
                        self.indice_concentrar = idx
                        self._selecionar_acao_concentrar()
                        return

            elif self.estado_combate == "SELECIONANDO_ALVO":
                for idx, r in enumerate(self.rects_inimigos):
                    if r.collidepoint(pos):
                        self.indice_alvo = idx
                        inimigos_vivos = self._obter_inimigos_vivos()
                        if idx < len(inimigos_vivos):
                            self._executar_acao_jogador(self.acao_selecionada, inimigos_vivos[idx])
                        return

        # 3. Teclado
        elif evento.type == pygame.KEYDOWN:
            if self.estado_combate in ["VITORIA", "DERROTA", "FUGIU"]:
                if evento.key in [pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE]:
                    self._concluir_fechamento_combate()
                return

            if self.estado_combate == "MENU_PRINCIPAL":
                if evento.key in [pygame.K_UP, pygame.K_w]:
                    self.indice_menu = (self.indice_menu - 1) % len(self.opcoes_menu_principal)
                elif evento.key in [pygame.K_DOWN, pygame.K_s]:
                    self.indice_menu = (self.indice_menu + 1) % len(self.opcoes_menu_principal)
                elif evento.key in [pygame.K_RETURN, pygame.K_SPACE, pygame.K_e]:
                    self._selecionar_opcao_menu_principal()

            elif self.estado_combate == "SUBMENU_ATAQUE":
                if not self.ataques_fisicos_disponiveis:
                    self.estado_combate = "MENU_PRINCIPAL"
                    return
                if evento.key in [pygame.K_UP, pygame.K_w]:
                    self.indice_ataque_fisico = (self.indice_ataque_fisico - 1) % len(self.ataques_fisicos_disponiveis)
                elif evento.key in [pygame.K_DOWN, pygame.K_s]:
                    self.indice_ataque_fisico = (self.indice_ataque_fisico + 1) % len(self.ataques_fisicos_disponiveis)
                elif evento.key in [pygame.K_RETURN, pygame.K_SPACE, pygame.K_e]:
                    self._selecionar_ataque_fisico()
                elif evento.key == pygame.K_ESCAPE:
                    self.estado_combate = "MENU_PRINCIPAL"

            elif self.estado_combate == "SUBMENU_MAGIA":
                if not self.magias_disponiveis:
                    self.estado_combate = "MENU_PRINCIPAL"
                    return
                if evento.key in [pygame.K_UP, pygame.K_w]:
                    self.indice_magia = (self.indice_magia - 1) % len(self.magias_disponiveis)
                elif evento.key in [pygame.K_DOWN, pygame.K_s]:
                    self.indice_magia = (self.indice_magia + 1) % len(self.magias_disponiveis)
                elif evento.key in [pygame.K_RETURN, pygame.K_SPACE, pygame.K_e]:
                    self._selecionar_magia_grimorio()
                elif evento.key == pygame.K_ESCAPE:
                    self.estado_combate = "MENU_PRINCIPAL"

            elif self.estado_combate == "SUBMENU_CONCENTRAR":
                if not self.opcoes_concentrar:
                    self.estado_combate = "MENU_PRINCIPAL"
                    return
                if evento.key in [pygame.K_UP, pygame.K_w]:
                    self.indice_concentrar = (self.indice_concentrar - 1) % len(self.opcoes_concentrar)
                elif evento.key in [pygame.K_DOWN, pygame.K_s]:
                    self.indice_concentrar = (self.indice_concentrar + 1) % len(self.opcoes_concentrar)
                elif evento.key in [pygame.K_RETURN, pygame.K_SPACE, pygame.K_e]:
                    self._selecionar_acao_concentrar()
                elif evento.key == pygame.K_ESCAPE:
                    self.estado_combate = "MENU_PRINCIPAL"

            elif self.estado_combate == "SELECIONANDO_ALVO":
                inimigos_vivos = self._obter_inimigos_vivos()
                if not inimigos_vivos:
                    return

                if evento.key in [pygame.K_UP, pygame.K_w]:
                    self.indice_alvo = (self.indice_alvo - 1) % len(inimigos_vivos)
                elif evento.key in [pygame.K_DOWN, pygame.K_s]:
                    self.indice_alvo = (self.indice_alvo + 1) % len(inimigos_vivos)
                elif evento.key in [pygame.K_RETURN, pygame.K_SPACE, pygame.K_e]:
                    alvo = inimigos_vivos[self.indice_alvo]
                    self._executar_acao_jogador(self.acao_selecionada, alvo)
                elif evento.key == pygame.K_ESCAPE:
                    self.estado_combate = "MENU_PRINCIPAL"

    # =========================================================================
    # LÓGICA DE SELEÇÃO E EXECUÇÃO DE AÇÕES
    # =========================================================================

    def _selecionar_opcao_menu_principal(self):
        opcao = self.opcoes_menu_principal[self.indice_menu]

        if opcao == "Atacar":
            self._carregar_ataques_fisicos_jogador()
            self.estado_combate = "SUBMENU_ATAQUE"
            self.indice_ataque_fisico = 0

        elif opcao == "Magias":
            self._carregar_magias_jogador()
            self.estado_combate = "SUBMENU_MAGIA"
            self.indice_magia = 0

        elif opcao == "Concentrar":
            self._carregar_acoes_concentrar()
            self.estado_combate = "SUBMENU_CONCENTRAR"
            self.indice_concentrar = 0

        elif opcao == "Fugir":
            self._tentar_fuga()

    def _selecionar_ataque_fisico(self):
        """Seleciona o ataque físico do submenu para execução contra o alvo."""
        if not self.ataques_fisicos_disponiveis:
            return

        ataque = self.ataques_fisicos_disponiveis[self.indice_ataque_fisico]
        if ataque.custo_mana > 0 and self.jogador.mana_atual < ataque.custo_mana:
            self.adicionar_log(f"Mana insuficiente ({self.jogador.mana_atual}/{ataque.custo_mana} MP)!")
            return

        inimigos_vivos = self._obter_inimigos_vivos()
        if len(inimigos_vivos) == 1:
            self._executar_acao_jogador(ataque, inimigos_vivos[0])
        else:
            self.acao_selecionada = ataque
            self.estado_combate = "SELECIONANDO_ALVO"
            self.indice_alvo = 0

    def _selecionar_acao_concentrar(self):
        """Executa a ação tática de Concentração ou Defesa selecionada no submenu."""
        if not self.opcoes_concentrar:
            return
        acao = self.opcoes_concentrar[self.indice_concentrar]
        self._executar_acao_jogador(acao, self.jogador)

    def _selecionar_magia_grimorio(self):
        """Seleciona a magia do Grimório de Halia para execução contra o alvo ou em si mesma."""
        if not self.magias_disponiveis:
            return

        magia = self.magias_disponiveis[self.indice_magia]
        if self.jogador.mana_atual < magia.custo_mana:
            self.adicionar_log(f"Mana insuficiente ({self.jogador.mana_atual}/{magia.custo_mana} MP)!")
            return

        alvo_tipo_padrao = getattr(magia, 'tipo_alvo', getattr(magia, 'alvo_tipo', 'inimigo_unico')).lower()
        if alvo_tipo_padrao in ["aliado", "proprio"]:
            self._executar_acao_jogador(magia, self.jogador)
        elif alvo_tipo_padrao in ["todos_inimigos", "todos"]:
            self._executar_acao_jogador(magia, self.inimigos)
        else: # inimigo_unico
            inimigos_vivos = self._obter_inimigos_vivos()
            if len(inimigos_vivos) == 1:
                self._executar_acao_jogador(magia, inimigos_vivos[0])
            else:
                self.acao_selecionada = magia
                self.estado_combate = "SELECIONANDO_ALVO"
                self.indice_alvo = 0

    def _gerar_mensagem_morte_condicao(self, entidade, relatorios):
        """Gera mensagem contextual dramática quando a entidade morre por DoT no início do turno."""
        elementos_causadores = []
        ids_causadores = []
        for r in relatorios:
            cond = r.get("condicao")
            if cond:
                elementos_causadores.append(getattr(cond, 'elemento', '').upper())
                ids_causadores.append(getattr(cond, 'id_condicao', '').lower())
                
        eh_halia = (entidade is self.jogador)

        if "FOGO" in elementos_causadores or "queimadura" in ids_causadores:
            return "Halia sucumbiu enquanto ardia em chamas abrasadoras..." if eh_halia else f"{entidade.nome} sucumbiu e ardeu em chamas até o último suspiro!"
        elif "VENENO" in elementos_causadores or "veneno" in ids_causadores:
            return "Halia sucumbiu enquanto o veneno paralisava seus sentidos vitais..." if eh_halia else f"{entidade.nome} sucumbiu às toxinas corrosivas que dissolveram suas forças!"
        elif "FISICO" in elementos_causadores or "sangramento" in ids_causadores:
            return "Halia não resistiu à hemorragia profunda e desfaleceu..." if eh_halia else f"{entidade.nome} esvaiu-se em sangue até o último suspiro!"
        elif "GELO" in elementos_causadores or "congelado" in ids_causadores:
            return "Halia teve as forças congeladas pelo frio extremo e caiu..." if eh_halia else f"{entidade.nome} foi congelado até o núcleo e estilhaçou-se!"
        elif "SOMBRA" in elementos_causadores or "miasma" in ids_causadores:
            return "Halia foi tragada e consumida pela escuridão..." if eh_halia else f"{entidade.nome} foi consumido pelo miasma sombrio e desfez-se em poeira!"
        else:
            return "Halia sucumbiu aos ferimentos e desmaiou..." if eh_halia else f"{entidade.nome} sucumbiu aos efeitos que castigavam seu corpo!"

    def _gerar_mensagem_morte_acao(self, alvo, acao):
        """Gera mensagem contextual dramática quando a entidade morre por um ataque/magia direta."""
        eh_halia = (alvo is self.jogador)
        elemento = getattr(acao, 'elemento', 'FISICO').upper()
        tipo = getattr(acao, 'tipo', 'FISICO').upper()
        nome_acao = getattr(acao, 'nome', 'Golpe')

        if elemento == "FOGO":
            return "Halia não resistiu e sucumbiu enquanto ardia em chamas abrasadoras..." if eh_halia else f"{alvo.nome} foi carbonizado pelas chamas incandescentes!"
        elif elemento == "ARCANO":
            return "A essência mágica de Halia colapsou sob a pura ressonância arcana..." if eh_halia else f"{alvo.nome} foi desintegrado pela pura energia arcana!"
        elif elemento == "SOMBRA":
            return "Halia foi engolida pelo abismo das trevas e perdeu a consciência..." if eh_halia else f"{alvo.nome} foi devorado e aniquilado pelas sombras abissais!"
        elif elemento == "GELO":
            return "Halia congelou instantaneamente sob o impacto gélido e caiu..." if eh_halia else f"{alvo.nome} foi estilhaçado pelo frio mortal!"
        elif elemento in ["ELETRICO", "TROVAO", "RAIO"]:
            return "Halia sucumbiu após ser fulminada pela violenta descarga elétrica..." if eh_halia else f"{alvo.nome} foi eletrocutado e fulminado pelo raio!"
        elif tipo == "FISICO":
            return f"Halia não resistiu ao impacto fulminante de {nome_acao} e caiu..." if eh_halia else f"{alvo.nome} foi estraçalhado pelo golpe devastador de {nome_acao} e caiu sem vida!"
        else:
            return f"Halia foi derrotada por {nome_acao}..." if eh_halia else f"{alvo.nome} foi aniquilado em batalha!"

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

        cura_direta = float(resultado.get("cura", 0) or 0)
        if cura_direta > 0:
            cura_fmt = int(cura_direta) if cura_direta.is_integer() else f"{cura_direta:.1f}"
            self.adicionar_texto_flutuante(f"+{cura_fmt}", self.jogador.x + 30, self.jogador.y - 10, BARRA_VIDA_JOGADOR)
        
        mana_rec = float(resultado.get("mana_recuperada", 0) or 0)
        if mana_rec > 0:
            mana_fmt = int(mana_rec) if mana_rec.is_integer() else f"{mana_rec:.1f}"
            self.adicionar_texto_flutuante(f"+{mana_fmt} MP", self.jogador.x + 30, self.jogador.y + 15, BARRA_MANA, duracao=80)
        if resultado.get("defendendo"):
            self.adicionar_texto_flutuante("EM GUARDA!", self.jogador.x + 30, self.jogador.y - 10, (100, 210, 255), duracao=80)
        if resultado.get("vulneravel"):
            self.adicionar_texto_flutuante("VULNERÁVEL!", self.jogador.x + 30, self.jogador.y - 10, (240, 130, 130), duracao=80)

        # 2. Trata lista de resultados de alvos (ataques e magias)
        for r in resultado.get("resultados", []):
            if r.get("mensagem") and r.get("mensagem") != resultado.get("mensagem"):
                self.adicionar_log(r["mensagem"])
                
            alvo_r = r.get("alvo")
            dano_r = float(r.get("dano", 0) or 0)
            cura_r = float(r.get("cura", 0) or 0)

            if r.get("errou", False) and alvo_r:
                if r.get("motivo") == "esquiva":
                    texto_erro = "ESQUIVOU!"
                    cor_erro = (100, 210, 255) # Cyan
                else:
                    texto_erro = "ERROU!"
                    cor_erro = (240, 160, 100) # Âmbar
                self.adicionar_texto_flutuante(texto_erro, alvo_r.x + 20, alvo_r.y - 15, cor_erro, duracao=80)
            elif dano_r > 0 and alvo_r:
                dano_fmt = int(dano_r) if dano_r.is_integer() else f"{dano_r:.1f}"
                self.adicionar_texto_flutuante(f"-{dano_fmt}", alvo_r.x + 20, alvo_r.y, TEXTO_ALERTA_COMBATE)
                self.shake_timers[alvo_r] = 12
                # Feedback narrativo se o alvo foi derrotado
                if not getattr(alvo_r, 'vivo', True):
                    msg_morte = self._gerar_mensagem_morte_acao(alvo_r, acao)
                    self.adicionar_log(msg_morte)
            elif cura_r > 0 and alvo_r:
                cura_fmt = int(cura_r) if cura_r.is_integer() else f"{cura_r:.1f}"
                self.adicionar_texto_flutuante(f"+{cura_fmt}", alvo_r.x + 20, alvo_r.y - 10, BARRA_VIDA_JOGADOR)

    def _executar_turno_inimigo(self, inimigo):
        """IA do inimigo: seleciona habilidade temática e executa contra Halia."""
        self.estado_combate = "EXECUTANDO_ACAO"
        self.timer_acao = self._ajustar_timer(75)
        
        # Filtra habilidades que o inimigo tem mana para usar
        kit = getattr(inimigo, 'habilidades', ["garras_sombrias", "golpe_sombrio"])
        acoes_disponiveis = []
        for id_hab in kit:
            acao_cand = SkillsRegistry.get(id_hab)
            if acao_cand and acao_cand.pode_usar(inimigo):
                acoes_disponiveis.append(acao_cand)
                
        if acoes_disponiveis:
            magias_com_custo = [a for a in acoes_disponiveis if a.custo_mana > 0]
            if magias_com_custo and random.random() < 0.65:
                acao = random.choice(magias_com_custo)
            else:
                acao = random.choice(acoes_disponiveis)
        else:
            acao = SkillsRegistry.get("garras_sombrias") or SkillsRegistry.get("golpe_sombrio") or SkillsRegistry.get("investida_sombria") or SkillsRegistry.get("ataque_basico")

        resultado = acao.executar(inimigo, self.jogador)
        
        if resultado.get("mensagem"):
            self.adicionar_log(resultado["mensagem"])
            
        for r in resultado.get("resultados", []):
            if r.get("mensagem") and r.get("mensagem") != resultado.get("mensagem"):
                self.adicionar_log(r["mensagem"])
            dano_r = float(r.get("dano", 0) or 0)
            if r.get("errou", False):
                if r.get("motivo") == "esquiva":
                    texto_erro = "ESQUIVOU!"
                    cor_erro = (100, 210, 255) # Cyan
                else:
                    texto_erro = "ERROU!"
                    cor_erro = (240, 160, 100) # Âmbar
                self.adicionar_texto_flutuante(texto_erro, self.jogador.x + 30, self.jogador.y - 15, cor_erro, duracao=80)
            elif dano_r > 0:
                dano_fmt = int(dano_r) if dano_r.is_integer() else f"{dano_r:.1f}"
                self.adicionar_texto_flutuante(f"-{dano_fmt}", self.jogador.x + 30, self.jogador.y, TEXTO_ALERTA_COMBATE)
                self.shake_timers[self.jogador] = 12
                # Feedback narrativo se Halia foi derrotada
                if not getattr(self.jogador, 'vivo', True):
                    msg_morte = self._gerar_mensagem_morte_acao(self.jogador, acao)
                    self.adicionar_log(msg_morte)

    def _tentar_fuga(self):
        """Calcula a probabilidade de fuga baseada na Destreza, quantidade e força dos inimigos."""
        inimigos_vivos = self._obter_inimigos_vivos()
        if not inimigos_vivos:
            self.estado_combate = "VITORIA"
            return

        # 1. Chefes e oponentes imponentes não permitem fuga
        for inimigo in inimigos_vivos:
            if isinstance(inimigo, Boss) or getattr(inimigo, 'eh_chefe', False) or getattr(inimigo, 'atributos', None) and inimigo.atributos.forca >= 28:
                self.adicionar_log("Halia tentou recuar, mas a presenca imponente do inimigo impede qualquer fuga!")
                self.adicionar_texto_flutuante("FUGA IMPOSSÍVEL!", self.jogador.x + 20, self.jogador.y - 15, TEXTO_ALERTA_COMBATE, duracao=75)
                self.timer_acao = self._ajustar_timer(60)
                self.estado_combate = "EXECUTANDO_ACAO"
                return

        # 2. Cálculo de chance baseado em Destreza, fadiga e quantidade de oponentes
        des_inimigos = sum(getattr(i, 'atributos', None).destreza if hasattr(i, 'atributos') else 10 for i in inimigos_vivos) / max(1, len(inimigos_vivos))
        des_jogador = self.jogador.atributos.destreza
        
        # Chance base: 45% + vantagem de destreza
        chance_fuga = 45.0 + ((des_jogador - des_inimigos) * 3.5)
        
        # Penalidade por múltiplos inimigos (-12% por inimigo adicional bloqueando o caminho)
        penalidade_cerco = (len(inimigos_vivos) - 1) * 12.0
        chance_fuga -= penalidade_cerco

        # Penalidade se a Halia estiver com vida baixa (< 30%) devido à exaustão física
        if self.jogador.vida_atual < (self.jogador.vida_maxima * 0.3):
            chance_fuga -= 10.0

        # Limites táticos: nunca 100% garantido nem totalmente impossível (12% min, 70% max)
        chance_fuga = max(12.0, min(70.0, chance_fuga))
        rolagem = random.uniform(0.0, 100.0)

        if rolagem <= chance_fuga:
            self.adicionar_log("Halia recuou com agilidade e escapou do combate com sucesso!")
            self.estado_combate = "FUGIU"
        else:
            self.adicionar_texto_flutuante("FUGA FALHOU!", self.jogador.x + 30, self.jogador.y - 15, (245, 150, 80), duracao=75)
            self.adicionar_log("Tentativa de fuga falhou! Os inimigos bloquearam a passagem e cercaram Halia.")
            # Perde a ação do turno e os inimigos atacam em seguida
            self.timer_acao = self._ajustar_timer(65)
            self.estado_combate = "EXECUTANDO_ACAO"

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

        # Execução de timer de leitura de ação
        if self.estado_combate == "EXECUTANDO_ACAO":
            if self.timer_acao > 0:
                self.timer_acao -= 1
            else:
                self.indice_turno_atual += 1
                self._avancar_para_proximo_turno()

        # Execução do turno do inimigo
        elif self.estado_combate == "TURNO_INIMIGO":
            if self.timer_acao > 0:
                self.timer_acao -= 1
            else:
                if self.indice_turno_atual < len(self.ordem_turnos):
                    inimigo_atual = self.ordem_turnos[self.indice_turno_atual]
                    self._executar_turno_inimigo(inimigo_atual)
                else:
                    self._avancar_para_proximo_turno()

        return self.estado_combate

    # =========================================================================
    # RESOLUÇÃO DE BATALHA (VITÓRIA / DERROTA / RECOMPENSAS)
    # =========================================================================

    def _finalizar_vitoria(self):
        """Distribui recompensas acumuladas de todos os inimigos e exibe banner."""
        self.recompensas_vitoria = {"moedas": 0, "memorias": 0, "xp": 0}
        
        for inimigo in self.inimigos:
            rec = getattr(inimigo, 'recompensas', {})
            self.recompensas_vitoria["moedas"] += rec.get("moedas", 10)
            self.recompensas_vitoria["memorias"] += rec.get("memorias", 0)
            self.recompensas_vitoria["xp"] += rec.get("xp", 15)

        # Entrega recompensas à Halia
        if hasattr(self.jogador, 'ganhar_dinheiro'):
            self.jogador.ganhar_dinheiro(self.recompensas_vitoria["moedas"])
        if hasattr(self.jogador, 'recuperar_memoria') and self.recompensas_vitoria["memorias"] > 0:
            self.jogador.recuperar_memoria(self.recompensas_vitoria["memorias"])

        self.adicionar_log(f"Vitoria! Ganhou {self.recompensas_vitoria['moedas']} moedas e {self.recompensas_vitoria['memorias']} memoria(s).")
        self.estado_combate = "VITORIA"

    def _finalizar_derrota(self):
        """Configura estado de derrota."""
        self.adicionar_log("Halia sucumbiu e retornara ao ultimo checkpoint...")
        self.estado_combate = "DERROTA"

    def _concluir_fechamento_combate(self):
        """Dispara os callbacks configurados ao encerrar."""
        if hasattr(self.jogador, 'sair_combate'):
            self.jogador.sair_combate()

        if self.estado_combate == "VITORIA" and callable(self.on_vitoria):
            self.on_vitoria()
        elif self.estado_combate == "DERROTA" and callable(self.on_derrota):
            self.on_derrota()
        elif self.estado_combate == "FUGIU" and callable(self.on_fuga):
            self.on_fuga()

    # =========================================================================
    # MÉTODOS DE LOG & QUEBRA DE LINHA (WORD WRAP)
    # =========================================================================

    def adicionar_log(self, mensagem):
        """Adiciona mensagens ao histórico aplicando quebra de linha com cores temáticas preservadas."""
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

    # =========================================================================
    # RENDERIZAÇÃO GRÁFICA
    # =========================================================================

    def desenhar_barra(self, tela, x, y, valor_atual, valor_maximo, cor_barra, cor_fundo=FUNDO_BARRA, largura=180, altura=12):
        """Encaminha para o utilitário centralizado de UI."""
        desenhar_barra_status_interpolada(tela, x, y, valor_atual, valor_maximo, cor_barra, cor_fundo=cor_fundo, largura=largura, altura=altura)

    def desenhar(self, tela):
        """Renderiza a arena, personagens, HUDs, menus, submenus, tooltips e banners."""
        # 1. FUNDO PADRÃO ESCURO DE OBLIVIUM
        tela.fill(UI_FUNDO_PADRAO)
        
        # Linha horizontal sutil de horizonte
        pygame.draw.line(tela, CINZA_ESCURO, (0, 390), (self.largura, 390), 1)

        # 2. RENDERIZAR INIMIGOS (Lado Direito)
        self.rects_inimigos.clear()
        inimigos_vivos = self._obter_inimigos_vivos()
        total_inimigos = len(inimigos_vivos)

        for idx, inimigo in enumerate(inimigos_vivos):
            pos_x = self.largura - 350
            
            if total_inimigos == 1:
                pos_y = 150
            elif total_inimigos == 2:
                pos_y = 75 + (idx * 175)
            else:
                pos_y = 50 + (idx * 130)
            
            offset_shake_x = random.randint(-3, 3) if self.shake_timers.get(inimigo, 0) > 0 else 0
            offset_shake_y = random.randint(-2, 2) if self.shake_timers.get(inimigo, 0) > 0 else 0
            
            draw_x = pos_x + offset_shake_x
            draw_y = pos_y + offset_shake_y

            # Plataforma / Sombra sutil no chão
            pygame.draw.ellipse(tela, (22, 22, 26), (draw_x - 10, draw_y + 80, 100, 20))

            # Hitbox para clique de mouse
            rect_hitbox = pygame.Rect(draw_x - 10, draw_y - 25, 240, 125)
            self.rects_inimigos.append(rect_hitbox)

            # Cursor de Seleção de Alvo
            if self.estado_combate == "SELECIONANDO_ALVO" and idx == self.indice_alvo:
                cursor_txt = self.fonte_titulo.render(">", True, TXT_SISTEMA_NARRADOR)
                tela.blit(cursor_txt, (draw_x - 30, draw_y + 15))
                pygame.draw.rect(tela, TXT_SISTEMA_NARRADOR, rect_hitbox, 1)

            # Renderiza Imagem ou Bloco Colorido
            imagem = getattr(inimigo, 'imagem_atual', None)
            if imagem:
                img_combate = pygame.transform.scale(imagem, (inimigo.largura * 2, inimigo.altura * 2))
                tela.blit(img_combate, (draw_x, draw_y))
            else:
                rect_inimigo = pygame.Rect(draw_x, draw_y, getattr(inimigo, 'largura', 40) * 2, getattr(inimigo, 'altura', 40) * 2)
                cor_bloco = BRANCO if self.shake_timers.get(inimigo, 0) > 6 else getattr(inimigo, 'cor', (140, 40, 50))
                pygame.draw.rect(tela, cor_bloco, rect_inimigo)
                pygame.draw.rect(tela, CINZA_CLARO, rect_inimigo, 2)

            # Nome do Inimigo
            texto_nome = self.fonte_nomes.render(inimigo.nome, True, TEXTO_ALERTA_COMBATE)
            tela.blit(texto_nome, (draw_x, draw_y - 28))
            
            # Badges de Condições Ativas
            offset_icone_x = draw_x + texto_nome.get_width() + 8
            for cond in getattr(inimigo, 'condicoes', []):
                txt_badge = self.fonte_status.render(f"{cond.icone}:{cond.duracao}", True, TXT_SISTEMA_NARRADOR)
                tela.blit(txt_badge, (offset_icone_x, draw_y - 25))
                offset_icone_x += txt_badge.get_width() + 6

            # Barra de Vida Suave Interpolada
            base_bar_y = draw_y + (getattr(inimigo, 'altura', 40) * 2) + 16
            larg_bar_inimigo = 150
            alt_bar = 12
            vida_v = self.vidas_visuais.get(inimigo, float(inimigo.vida_atual))
            self.desenhar_barra(tela, draw_x, base_bar_y, vida_v, inimigo.vida_maxima, BARRA_VIDA_INIMIGO, largura=larg_bar_inimigo, altura=alt_bar)
            txt_hp = self.fonte_status.render(f"HP {int(vida_v)}/{inimigo.vida_maxima}", True, UI_TEXTO_DESTAQUE)
            tela.blit(txt_hp, (draw_x + larg_bar_inimigo + 10, base_bar_y - 2))

            # Barra de Mana Suave Interpolada do Monstro (Idêntico ao padrão visual de Halia)
            mana_max = getattr(inimigo, 'mana_maxima', 20)
            mana_v = self.manas_visuais.get(inimigo, float(getattr(inimigo, 'mana_atual', mana_max)))
            mp_bar_y = base_bar_y + 20
            self.desenhar_barra(tela, draw_x, mp_bar_y, mana_v, mana_max, BARRA_MANA, largura=larg_bar_inimigo, altura=alt_bar)
            txt_mp = self.fonte_status.render(f"MP {int(mana_v)}/{mana_max}", True, UI_TEXTO_DESTAQUE)
            tela.blit(txt_mp, (draw_x + larg_bar_inimigo + 10, mp_bar_y - 2))

        # 3. RENDERIZAR HALIA (Lado Esquerdo)
        halia_x, halia_y = 160, 160
        offset_h_x = random.randint(-3, 3) if self.shake_timers.get(self.jogador, 0) > 0 else 0
        offset_h_y = random.randint(-2, 2) if self.shake_timers.get(self.jogador, 0) > 0 else 0
        
        draw_hx = halia_x + offset_h_x
        draw_hy = halia_y + offset_h_y

        # Plataforma / Sombra sutil no chão sob Halia
        pygame.draw.ellipse(tela, (22, 22, 26), (draw_hx - 10, draw_hy + 90, 105, 22))

        # Imagem ou Bloco da Halia
        img_halia = getattr(self.jogador, 'imagem_atual', None)
        if img_halia:
            img_c = pygame.transform.scale(img_halia, (self.jogador.largura * 2, self.jogador.altura * 2))
            tela.blit(img_c, (draw_hx, draw_hy))
        else:
            rect_h = pygame.Rect(draw_hx, draw_hy, 75, 95)
            cor_h = BRANCO if self.shake_timers.get(self.jogador, 0) > 6 else (34, 139, 34)
            pygame.draw.rect(tela, cor_h, rect_h)
            pygame.draw.rect(tela, CINZA_CLARO, rect_h, 2)

        # Nome da Halia
        txt_halia = self.fonte_nomes.render(self.jogador.nome, True, NOME_HALIA)
        tela.blit(txt_halia, (draw_hx, draw_hy - 32))
        
        # Badges de Condições da Halia
        offset_h_badge = draw_hx + txt_halia.get_width() + 8
        for cond in getattr(self.jogador, 'condicoes', []):
            txt_badge_h = self.fonte_status.render(f"{cond.icone}:{cond.duracao}", True, TXT_SISTEMA_NARRADOR)
            tela.blit(txt_badge_h, (offset_h_badge, draw_hy - 30))
            offset_h_badge += txt_badge_h.get_width() + 6

        # Barras Interpoladas de HP e MP da Halia (Mesmo padrão visual, espessura e espaçamento)
        vida_h_v = self.vidas_visuais.get(self.jogador, float(self.jogador.vida_atual))
        mana_h_v = self.manas_visuais.get(self.jogador, float(self.jogador.mana_atual))
        larg_h_bar = 180
        alt_h_bar = 12
        base_h_bar_y = draw_hy + 105

        self.desenhar_barra(tela, draw_hx, base_h_bar_y, vida_h_v, self.jogador.vida_maxima, BARRA_VIDA_JOGADOR, largura=larg_h_bar, altura=alt_h_bar)
        tela.blit(self.fonte_status.render(f"HP {int(vida_h_v)}/{self.jogador.vida_maxima}", True, UI_TEXTO_DESTAQUE), (draw_hx + larg_h_bar + 10, base_h_bar_y - 2))

        self.desenhar_barra(tela, draw_hx, base_h_bar_y + 20, mana_h_v, self.jogador.mana_maxima, BARRA_MANA, largura=larg_h_bar, altura=alt_h_bar)
        tela.blit(self.fonte_status.render(f"MP {int(mana_h_v)}/{self.jogador.mana_maxima}", True, UI_TEXTO_DESTAQUE), (draw_hx + larg_h_bar + 10, base_h_bar_y + 18))

        # 4. PAINEL INFERIOR DE MENUS E COMBAT LOG
        altura_painel = 245
        painel_rect = pygame.Rect(40, self.altura - altura_painel - 20, self.largura - 80, altura_painel)
        pygame.draw.rect(tela, UI_FUNDO_PADRAO, painel_rect)
        pygame.draw.rect(tela, CINZA_CLARO, painel_rect, 2)

        # Divisão Interna: Seção de Ações (Esquerda 380px) | Seção de Log (Direita)
        largura_secao_menu = 380
        pygame.draw.line(tela, CINZA_ESCURO, (painel_rect.x + largura_secao_menu, painel_rect.y), (painel_rect.x + largura_secao_menu, painel_rect.bottom), 1)

        # RENDERIZAR MENU PRINCIPAL
        self.rects_menu_principal.clear()
        if self.estado_combate == "MENU_PRINCIPAL":
            for i, opcao in enumerate(self.opcoes_menu_principal):
                item_y = painel_rect.y + 14 + (i * 44)
                item_rect = pygame.Rect(painel_rect.x + 20, item_y, largura_secao_menu - 40, 38)
                self.rects_menu_principal.append(item_rect)
                
                if i == self.indice_menu:
                    pygame.draw.rect(tela, (28, 28, 34), item_rect)
                    pygame.draw.rect(tela, CINZA_CLARO, item_rect, 1)
                    cor = TXT_SISTEMA_NARRADOR
                    marcador = "> "
                else:
                    cor = CINZA_CLARO
                    marcador = "  "
                    
                txt = self.fonte_menu.render(f"{marcador}{opcao}", True, cor)
                tela.blit(txt, (item_rect.x + 14, item_rect.y + 6))

        # RENDERIZAR SUBMENU DE ATAQUES FÍSICOS
        self.rects_ataques_fisicos.clear()
        if self.estado_combate == "SUBMENU_ATAQUE":
            self.rect_botao_voltar = pygame.Rect(painel_rect.x + 20, painel_rect.y + 12, 100, 26)
            pygame.draw.rect(tela, (25, 25, 30), self.rect_botao_voltar)
            pygame.draw.rect(tela, CINZA_CLARO, self.rect_botao_voltar, 1)
            txt_voltar = self.fonte_status.render("< Voltar", True, UI_TEXTO_DESTAQUE)
            tela.blit(txt_voltar, (self.rect_botao_voltar.x + 14, self.rect_botao_voltar.y + 5))

            for i, ataque in enumerate(self.ataques_fisicos_disponiveis):
                item_y = painel_rect.y + 46 + (i * 44)
                item_rect = pygame.Rect(painel_rect.x + 20, item_y, largura_secao_menu - 40, 38)
                self.rects_ataques_fisicos.append(item_rect)
                
                if i == self.indice_ataque_fisico:
                    pygame.draw.rect(tela, (28, 28, 34), item_rect)
                    pygame.draw.rect(tela, CINZA_CLARO, item_rect, 1)
                    cor = TXT_SISTEMA_NARRADOR
                    marcador = "> "
                else:
                    cor = CINZA_CLARO
                    marcador = "  "
                    
                custo_str = f"({ataque.custo_mana} MP)" if ataque.custo_mana > 0 else ""
                txt = self.fonte_menu.render(f"{marcador}{ataque.nome} {custo_str}".strip(), True, cor)
                tela.blit(txt, (item_rect.x + 10, item_rect.y + 6))

        # RENDERIZAR SUBMENU DE MAGIAS
        self.rects_magias.clear()
        if self.estado_combate == "SUBMENU_MAGIA":
            self.rect_botao_voltar = pygame.Rect(painel_rect.x + 20, painel_rect.y + 12, 100, 26)
            pygame.draw.rect(tela, (25, 25, 30), self.rect_botao_voltar)
            pygame.draw.rect(tela, CINZA_CLARO, self.rect_botao_voltar, 1)
            txt_voltar = self.fonte_status.render("< Voltar", True, UI_TEXTO_DESTAQUE)
            tela.blit(txt_voltar, (self.rect_botao_voltar.x + 14, self.rect_botao_voltar.y + 5))

            for i, magia in enumerate(self.magias_disponiveis):
                item_y = painel_rect.y + 46 + (i * 44)
                item_rect = pygame.Rect(painel_rect.x + 20, item_y, largura_secao_menu - 40, 38)
                self.rects_magias.append(item_rect)
                
                if i == self.indice_magia:
                    pygame.draw.rect(tela, (28, 28, 34), item_rect)
                    pygame.draw.rect(tela, CINZA_CLARO, item_rect, 1)
                    cor = TXT_SISTEMA_NARRADOR
                    marcador = "> "
                else:
                    cor = CINZA_CLARO
                    marcador = "  "
                    
                custo_txt = f"({magia.custo_mana} MP)" if magia.custo_mana > 0 else "(Gratis)"
                txt = self.fonte_menu.render(f"{marcador}{magia.nome} {custo_txt}", True, cor)
                tela.blit(txt, (item_rect.x + 10, item_rect.y + 6))

        # RENDERIZAR SUBMENU DE CONCENTRAR
        self.rects_concentrar.clear()
        if self.estado_combate == "SUBMENU_CONCENTRAR":
            self.rect_botao_voltar = pygame.Rect(painel_rect.x + 20, painel_rect.y + 12, 100, 26)
            pygame.draw.rect(tela, (25, 25, 30), self.rect_botao_voltar)
            pygame.draw.rect(tela, CINZA_CLARO, self.rect_botao_voltar, 1)
            txt_voltar = self.fonte_status.render("< Voltar", True, UI_TEXTO_DESTAQUE)
            tela.blit(txt_voltar, (self.rect_botao_voltar.x + 14, self.rect_botao_voltar.y + 5))

            for i, acao in enumerate(self.opcoes_concentrar):
                item_y = painel_rect.y + 46 + (i * 44)
                item_rect = pygame.Rect(painel_rect.x + 20, item_y, largura_secao_menu - 40, 38)
                self.rects_concentrar.append(item_rect)
                
                if i == self.indice_concentrar:
                    pygame.draw.rect(tela, (28, 28, 34), item_rect)
                    pygame.draw.rect(tela, CINZA_CLARO, item_rect, 1)
                    cor = TXT_SISTEMA_NARRADOR
                    marcador = "> "
                else:
                    cor = CINZA_CLARO
                    marcador = "  "
                    
                sufixo = "(+MP)" if acao.id_acao == "foco_espiritual" else "(Guarda)"
                txt = self.fonte_menu.render(f"{marcador}{acao.nome} {sufixo}", True, cor)
                tela.blit(txt, (item_rect.x + 10, item_rect.y + 6))

        # RENDERIZAR SELEÇÃO DE ALVOS
        elif self.estado_combate == "SELECIONANDO_ALVO":
            txt_alvo = self.fonte_menu.render("Selecione o Inimigo Alvo:", True, TXT_SISTEMA_NARRADOR)
            tela.blit(txt_alvo, (painel_rect.x + 20, painel_rect.y + 15))
            
            inimigos_vivos = self._obter_inimigos_vivos()
            for i, inimigo in enumerate(inimigos_vivos):
                cor = TXT_SISTEMA_NARRADOR if i == self.indice_alvo else CINZA_CLARO
                marcador = "> " if i == self.indice_alvo else "  "
                txt_i = self.fonte_status.render(f"{marcador}{inimigo.nome} ({inimigo.vida_atual}/{inimigo.vida_maxima} HP)", True, cor)
                tela.blit(txt_i, (painel_rect.x + 20, painel_rect.y + 55 + (i * 32)))

        # RENDERIZAR COMBAT LOG (Seção Direita com Word Wrap e Cores Preservadas)
        pos_log_x = painel_rect.x + largura_secao_menu + 30
        pos_log_y = painel_rect.y + 16
        
        txt_cabecalho_log = self.fonte_status.render(f"HISTORICO DE COMBATE (Vel: {self.velocidade_combate}x)", True, UI_TEXTO_APAGADO)
        tela.blit(txt_cabecalho_log, (pos_log_x, pos_log_y))
        
        # Histórico exibe 6 linhas completas
        max_linhas = 6
        linhas_exibidas = self.historico_log[-max_linhas:]
        
        for idx, item in enumerate(linhas_exibidas):
            is_latest = (idx == len(linhas_exibidas) - 1)
            texto_linha = item.get("texto", "") if isinstance(item, dict) else str(item)
            cor_custom = item.get("cor", None) if isinstance(item, dict) else None
            
            if cor_custom:
                cor_linha = cor_custom
            elif is_latest:
                cor_linha = BRANCO
            else:
                cor_linha = CINZA_CLARO
                
            txt_linha = self.fonte_log.render(texto_linha, True, cor_linha)
            tela.blit(txt_linha, (pos_log_x, pos_log_y + 26 + (idx * 27)))

        # RENDERIZAR TOOLTIP FIXO NA PARTE INFERIOR (Sobrepondo o histórico somente se necessário)
        if self.estado_combate in ["SUBMENU_ATAQUE", "SUBMENU_MAGIA", "SUBMENU_CONCENTRAR"]:
            acao_sel = None
            if self.estado_combate == "SUBMENU_ATAQUE" and self.indice_ataque_fisico < len(self.ataques_fisicos_disponiveis):
                acao_sel = self.ataques_fisicos_disponiveis[self.indice_ataque_fisico]
            elif self.estado_combate == "SUBMENU_MAGIA" and self.indice_magia < len(self.magias_disponiveis):
                acao_sel = self.magias_disponiveis[self.indice_magia]
            elif self.estado_combate == "SUBMENU_CONCENTRAR" and self.indice_concentrar < len(self.opcoes_concentrar):
                acao_sel = self.opcoes_concentrar[self.indice_concentrar]

            if acao_sel:
                largura_tooltip = (painel_rect.right - 15) - (painel_rect.x + largura_secao_menu + 20)
                self._desenhar_tooltip_acao(
                    tela,
                    acao_sel,
                    painel_rect.x + largura_secao_menu + 20,
                    painel_rect.bottom - 12,
                    largura_max=largura_tooltip
                )

        # 5. RENDERIZAR NÚMEROS FLUTUANTES
        for tf in self.textos_flutuantes:
            tf.desenhar(tela, self.fonte_dano)

        # 6. TELAS ESPECIAIS (Banners de Vitória, Derrota e Fuga)
        if self.estado_combate in ["VITORIA", "DERROTA", "FUGIU"]:
            self._desenhar_banner_fim_combate(tela)

    def _desenhar_tooltip_acao(self, tela, acao, x, y_bottom, largura_max=None):
        """Desenha uma caixa descritiva elegante fixada na parte inferior do painel, sobrepondo o histórico."""
        if not acao:
            return

        tipo = getattr(acao, 'tipo', '').upper()
        elemento = getattr(acao, 'elemento', 'NEUTRO').upper()
        desc = getattr(acao, 'descricao', '')
        custo = getattr(acao, 'custo_mana', 0)
        custo_str = f" | Custo: {custo} MP" if custo > 0 else (" | Custo: Grátis" if tipo == "MAGICO" else "")

        if tipo == "MAGICO":
            detalhe = f"[{elemento}] {acao.nome}{custo_str} | Poder: {getattr(acao, 'poder_base', 0)} - {desc}"
        elif tipo == "FOCO":
            detalhe = f"[TÁTICO] {acao.nome} - {desc}"
        elif tipo == "DEFESA":
            detalhe = f"[TÁTICO] {acao.nome} - {desc}"
        elif tipo == "FISICO":
            detalhe = f"[FÍSICO] {acao.nome}{custo_str} | Poder: {getattr(acao, 'poder_base', 0)} - {desc}"
        else:
            detalhe = f"[{elemento}] {acao.nome} - {desc}"

        if largura_max is None:
            largura_max = self.largura - x - 40

        linhas_tt = quebrar_texto_em_linhas(detalhe, self.fonte_tooltip, largura_max - 24)
        if not linhas_tt:
            linhas_tt = [detalhe]

        altura_linha = 20
        altura_tt = max(42, 14 + (len(linhas_tt) * altura_linha))
        pos_y_tt = y_bottom - altura_tt

        rect_tt = pygame.Rect(x, pos_y_tt, largura_max, altura_tt)
        # Fundo opaco para sobrepor com nitidez as linhas de trás
        pygame.draw.rect(tela, (22, 22, 28), rect_tt)
        pygame.draw.rect(tela, CINZA_CLARO, rect_tt, 1)

        for i, l in enumerate(linhas_tt):
            cor_txt = UI_TEXTO_DESTAQUE if i == 0 else CINZA_CLARO
            txt_d = self.fonte_tooltip.render(l, True, cor_txt)
            tela.blit(txt_d, (rect_tt.x + 12, rect_tt.y + 7 + (i * altura_linha)))

    def _desenhar_banner_fim_combate(self, tela):
        overlay = pygame.Surface((self.largura, self.altura), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 195))
        tela.blit(overlay, (0, 0))

        largura_b, altura_b = 640, 260
        rx = (self.largura - largura_b) // 2
        ry = (self.altura - altura_b) // 2
        self.rect_banner = pygame.Rect(rx, ry, largura_b, altura_b)
        
        pygame.draw.rect(tela, UI_FUNDO_PADRAO, self.rect_banner)
        
        if self.estado_combate == "VITORIA":
            cor_borda = TXT_SISTEMA_NARRADOR
            titulo = "VITORIA!"
            msg1 = f"Recompensas: +{self.recompensas_vitoria['moedas']} Moedas | +{self.recompensas_vitoria['memorias']} Memoria(s)"
            msg2 = "Pressione [ENTER], [ESPACO] ou clique para continuar..."
        elif self.estado_combate == "DERROTA":
            cor_borda = TEXTO_ALERTA_COMBATE
            titulo = "DERROTA"
            msg1 = "Halia sucumbiu e foi resgatada ao ultimo checkpoint..."
            msg2 = "Pressione [ENTER] ou clique para reiniciar..."
        else: # FUGIU
            cor_borda = TXT_PENSAMENTO_INTERNO
            titulo = "ESCAPOU"
            msg1 = "Halia recuou com sucesso para um local seguro."
            msg2 = "Pressione [ENTER] ou clique para retornar..."

        pygame.draw.rect(tela, cor_borda, self.rect_banner, 2)

        txt_t = self.fonte_titulo.render(titulo, True, cor_borda)
        tela.blit(txt_t, (rx + (largura_b - txt_t.get_width()) // 2, ry + 35))

        txt_m1 = self.fonte_menu.render(msg1, True, UI_TEXTO_DESTAQUE)
        tela.blit(txt_m1, (rx + (largura_b - txt_m1.get_width()) // 2, ry + 105))

        txt_m2 = self.fonte_status.render(msg2, True, UI_TEXTO_APAGADO)
        tela.blit(txt_m2, (rx + (largura_b - txt_m2.get_width()) // 2, ry + 195))