# src/core/game.py
import pygame
from src.ui.menu import Menu
from src.ui.dialogue_box import DialogueBox  
from src.ui.intro import Intro
from src.entities.player import Player
from src.mechanics.attributes import Atributos
from src.mechanics.inventory import Inventario
from src.maps.map_loader import Mapa
from src.ui.transition import Transition
from src.entities.NPC import NPC
from src.ui.flashback import Flashback  
from src.mechanics.minigames import MinigameTiming, MinigameMash 
from src.mechanics.combat import CombatScreen
from src.core.save_manager import SaveManager
from src.ui.hud import HUD
from src.utils.filtro_memoria import FiltroMemoria
from src.ui.tela_despertar import TelaDespertarMemoria
from src.ui.notification_manager import NotificationManager
from src.utils.dev_commands import ComandosDev
from src.utils.animations import EfeitoFolhas
from src.utils.clima import EfeitoChuva
from src.core.audio_manager import AudioManager
from src.mechanics.achievement_manager import AchievementManager
from src.mechanics.quest_manager import QuestManager
from src.ui.quest_tracker import QuestTracker

# Importação dos Estados Estruturados
from src.states.menu_states import MenuState
from src.states.playing_states import PlayingState
from src.states.intro_states import IntroState
from src.states.combat_states import CombatState
from src.states.pause_states import PauseState
from src.states.credits_states import CreditsState
from src.states.settings_states import SettingsState
from src.states.controles_state import ControlesState
from src.states.slots_states import SlotsState
from src.states.inventory_states import InventoryState
from src.states.shop_states import ShopState
from src.states.selecao_controles_state import SelecaoControlesState
from src.states.conquistas_state import ConquistasState



class Game:
    def __init__(self):
        # --- Configurações de Janela e Clock ---
        self.LARGURA = 1280
        self.ALTURA = 720
        self.tela = pygame.display.set_mode((self.LARGURA, self.ALTURA))
        pygame.display.set_caption("Oblivium")
        self.clock = pygame.time.Clock()
        self.running = True

        # --- Componentes Globais Compartilhados ---
        self.menu = Menu()
        self.caixa_dialogo = DialogueBox(self.LARGURA) 
        self.intro = Intro(self.LARGURA, self.ALTURA)
        self.mapa_casa = Mapa(self, self.LARGURA, self.ALTURA)
        self.transicao = Transition(self.LARGURA, self.ALTURA)
        self.flashback_sistema = Flashback(self.LARGURA, self.ALTURA) 
        self.tela_despertar = TelaDespertarMemoria(self.LARGURA, self.ALTURA)
        self.tela_combate = CombatScreen(self.LARGURA, self.ALTURA)
        self.filtro_memoria = FiltroMemoria(self.LARGURA, self.ALTURA)
        self.efeito_folhas = EfeitoFolhas(self.LARGURA, self.ALTURA, quantidade_folhas=28)
        self.efeito_chuva = EfeitoChuva(self.LARGURA, self.ALTURA)
        self.mg_timing = MinigameTiming(self.LARGURA, self.ALTURA)
        self.mg_mash = MinigameMash(self.LARGURA, self.ALTURA)
        self.notificacoes = NotificationManager(self.LARGURA, self.ALTURA)
        self.conquistas = AchievementManager(self)
        self.missoes = QuestManager(self)
        self.quest_tracker = QuestTracker(self.LARGURA, self.ALTURA)
        self.dev_commands = ComandosDev(self)
        # --- CONFIGURAÇÕES DO JOGO ---
        self.config_velocidade_indice = 1  # 0: Lento, 1: Normal, 2: Rápido
        self.opcoes_velocidade = ["Lento", "Normal", "Rápido"]
        self.valores_velocidade = [0.5, 1.0, 2.5]
        
        self.config_velocidade_combate_indice = 0  # 0: 1.0x (Normal), 1: 1.5x (Rápido), 2: 2.0x (Ultra)
        self.opcoes_velocidade_combate = ["1.0x (Normal)", "1.5x (Rápido)", "2.0x (Ultra)"]
        self.valores_velocidade_combate = [1.0, 1.5, 2.0]
        
        # --- Configurações de Áudio por Área (0 a 100%) ---
        self.config_audio = 100            # Volume Geral (Master)
        self.config_audio_musica = 80      # Volume da Música de Fundo (BGM)
        self.config_audio_sfx = 90         # Volume dos Efeitos Sonoros (SFX)
        self.config_audio_ambiente = 75    # Volume dos Sons de Ambiente (BGS / Clima)
        
        self.audio = AudioManager(self)
        self.audio.definir_volume_master(self.config_audio)
        self.audio.definir_volume_musica(self.config_audio_musica)
        self.audio.definir_volume_sfx(self.config_audio_sfx)
        self.audio.definir_volume_ambiente(self.config_audio_ambiente)
        self.save_manager = SaveManager(self)
        self.tecla_interacao = pygame.K_e  # Tecla padrão para interagir
        self.redefinindo_tecla = False     # Flag para escutar a nova tecla
       # --- CONTROLE DE SAVES / SLOTS ---
        self.acao_slots = "SALVAR" 
        self.origem_slots = "PAUSE"
        self.slot_atual = None      # Memoriza o slot da sessão (1, 2 ou 3)
        self.tempo_jogado = 0.0     # Conta os segundos jogados
        self.fonte_indicador = pygame.font.Font(None, 24)
        self.itens_coletados = []   

        # -- Opções de Inventário
        self.hud = HUD(self.LARGURA, self.ALTURA)
        
        # --- Entidades Estáveis ---
        self.halia = Player("Halia", 100, 210, 280, 3, mana_maxima=50, dinheiro=0)
        self.carroceiro = NPC(nome="Carroceiro", x=1350, y=330, velocidade=2)

        # --- Flags Globais de Progresso e Cutscenes (Lidas pelo PlayingState) ---
        self.fechando_porta = False
        self.aguardando_fim_viagem = False
        self.investigou_pedras = False
        self.flashback_magia_concluido = False 
        
        # Controle de Magia/Animações
        self.magia_ativa = None          
        self.timer_magia = 0            
        self.distanciando_halia = False 
        self.bola_fogo_x = 0
        self.bola_fogo_y = 0
        self.bola_fogo_ativa = False    
        self.magia_usada_no_puzzle = None 
        self.magia_selecionada_temporaria = None 
        
        # Controle de Encontros de Combate no Overworld
        self.iniciando_combate = False
        self.cena_inimigos_andando = False
        self.conversa_combate_ativa = False 
        self.carroceiro_visivel = False
        self.carroceiro_andando = False 
        self.conversa_carroceiro_terminou = False
        self.combate_estrada_concluido = False
        self.inimigos_em_cena = [] 
        # --- CONTROLOS DO JOGO (REMAPEÁVEIS) ---
        self.preset_controles = "WASD"
        self.controles = {
            "Cima": pygame.K_w,
            "Baixo": pygame.K_s,
            "Esquerda": pygame.K_a,
            "Direita": pygame.K_d,
            "Correr": pygame.K_LSHIFT,
            "Interagir": pygame.K_e,
            "Pause": pygame.K_ESCAPE,
            "Inventário": pygame.K_TAB
        }

        # --- Máquina de Estados ---
        self.estados = {
            "MENU": MenuState(self),
            "INTRO": IntroState(self),
            "JOGANDO": PlayingState(self),
            "COMBATE": CombatState(self),
            "PAUSE": PauseState(self),
            "CREDITOS": CreditsState(self),
            "CONFIGURACOES": SettingsState(self),
            "CONTROLES": ControlesState(self),
            "INVENTARIO": InventoryState(self),
            "LOJA": ShopState(self),
            "SLOTS": SlotsState(self),
            "SELECAO_CONTROLES": SelecaoControlesState(self),
            "CONQUISTAS": ConquistasState(self)
        }
        self.nome_estado_atual = "MENU"
        self.origem_configuracoes = "MENU"
        self.origem_conquistas = "MENU"
        self.mudar_estado("MENU")

    def aplicar_preset_controles(self, tipo="WASD"):
        """Aplica uma predefinição de controles completa (WASD ou Setinhas)."""
        if tipo.upper() in ["SETINHAS", "SETAS"]:
            self.preset_controles = "SETINHAS"
            self.controles = {
                "Cima": pygame.K_UP,
                "Baixo": pygame.K_DOWN,
                "Esquerda": pygame.K_LEFT,
                "Direita": pygame.K_RIGHT,
                "Correr": pygame.K_RSHIFT,
                "Interagir": pygame.K_SPACE,
                "Pause": pygame.K_ESCAPE,
                "Inventário": pygame.K_TAB
            }
        else:
            self.preset_controles = "WASD"
            self.controles = {
                "Cima": pygame.K_w,
                "Baixo": pygame.K_s,
                "Esquerda": pygame.K_a,
                "Direita": pygame.K_d,
                "Correr": pygame.K_LSHIFT,
                "Interagir": pygame.K_e,
                "Pause": pygame.K_ESCAPE,
                "Inventário": pygame.K_TAB
            }
        self.origem_creditos = "MENU"
        # Rastreia em que ponto da conversa cada NPC está
        self.progresso_npcs = {
            "carroceiro": 0  # 0: Início, 1: Falou com ele, 2: Viagem liberada, etc.
        }

    def mudar_estado(self, novo_estado):
        """Altera dinamicamente o comportamento e as telas do jogo"""
        if novo_estado in self.estados:
            self.nome_estado_atual = novo_estado
            self.estado_atual = self.estados[novo_estado]
            if novo_estado == "MENU":
                self.menu.atualizar_opcoes()
                if hasattr(self, 'audio') and self.audio:
                    self.audio.tocar_musica("menu_tema")

    def iniciar_combate(self, inimigos, on_vitoria=None, on_derrota=None, on_fuga=None):
        """Inicia um combate de forma modular e desacoplada em qualquer momento do jogo."""
        if isinstance(inimigos, (list, tuple)):
            self.inimigos_em_cena = list(inimigos)
        else:
            self.inimigos_em_cena = [inimigos]
            
        self.mudar_estado("COMBATE")
        self.tela_combate.iniciar_combate(
            jogador=self.halia,
            inimigos=self.inimigos_em_cena,
            on_vitoria=on_vitoria,
            on_derrota=on_derrota,
            on_fuga=on_fuga
        )

    def iniciar_dialogo(self, id_ou_dados):
        """Inicia uma conversa ou fala através da caixa de diálogo central."""
        self.caixa_dialogo.iniciar_dialogo(id_ou_dados)

    def run(self):
        """Loop principal e delegação de controle para o estado ativo"""
        while self.running:
            eventos = pygame.event.get()
            teclas = pygame.key.get_pressed()
            
            for evento in eventos:
                if evento.type == pygame.QUIT:
                    self.running = False

            # Interceptação global de notificações e comandos do dev
            eventos = self.notificacoes.handle_events(eventos)

            dev_ativo = False
            if hasattr(self, 'dev_commands') and self.dev_commands:
                eventos_restantes = []
                for ev in eventos:
                    if not self.dev_commands.processar_evento(ev):
                        eventos_restantes.append(ev)
                eventos = eventos_restantes
                dev_ativo = getattr(self.dev_commands, 'ativo', False)

            # Silencia comandos de movimento contínuo da Halia se o console dev estiver na tela
            teclas_ativas = [False] * len(teclas) if dev_ativo else teclas

            self.estado_atual.handle_events(eventos, teclas_ativas)
            self.estado_atual.update()
            self.notificacoes.update()
            
            self.tela.fill((0, 0, 0))
            self.estado_atual.draw(self.tela)
            
            # Se os comandos do dev estiverem ativos, desenha o overlay por cima de tudo
            if hasattr(self, 'dev_commands') and self.dev_commands:
                self.dev_commands.desenhar(self.tela)

            # Notificações globais desenhadas no topo apenas em telas que NÃO possuem filtro de memória próprio
            # (Em PlayingState e CombatState, as notificações são desenhadas antes do filtro para serem afetadas por ele)
            if getattr(self, 'nome_estado_atual', '') not in ["JOGANDO", "COMBATE"]:
                self.notificacoes.draw(self.tela)

            pygame.display.flip()
            self.clock.tick(60)

    def salvar_estado(self, slot=None, tipo="manual", silenciar_notificacao=False):
        return self.save_manager.salvar_estado(slot, tipo=tipo, silenciar_notificacao=silenciar_notificacao)

    def carregar_estado(self, slot, tipo="manual"):
        return self.save_manager.carregar_estado(slot, tipo=tipo)

    def resetar_progresso(self, slot_novo):
        return self.save_manager.resetar_progresso(slot_novo)

    def executar_com_feedback(self, texto, funcao_acao):
        """Exibe a tela escura de feedback ('Salvando...', 'Carregando...') 
           diretamente na gameplay antes de executar a ação."""
        
        if hasattr(self, 'estado_atual') and self.estado_atual:
            self.estado_atual.draw(self.tela)
        
        # Cria a película escura de loading
        overlay = pygame.Surface((self.LARGURA, self.ALTURA))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(220)
        self.tela.blit(overlay, (0, 0))
        
        # Renderiza o texto centralizado na tela
        fonte = pygame.font.Font(None, 60)
        render_texto = fonte.render(texto, True, (255, 255, 255))
        pos_x = (self.LARGURA - render_texto.get_width()) // 2
        pos_y = (self.ALTURA - render_texto.get_height()) // 2
        self.tela.blit(render_texto, (pos_x, pos_y))
        
        # Atualiza a janela imediatamente para o texto aparecer para si
        pygame.display.flip()
        
        # Executa a função real (Salvar ou Carregar os dados)
        funcao_acao()
        

        tempo_inicio = pygame.time.get_ticks()
        while pygame.time.get_ticks() - tempo_inicio < 800:
            pygame.event.pump()

    def definir_clima(self, tipo):
        """Define o clima ativo: 'limpo', 'comum' (ou 'chuva'), 'pesada' (ou 'tempestade')."""
        if hasattr(self, 'efeito_chuva'):
            self.efeito_chuva.definir_clima(tipo)

    def alternar_clima(self):
        """Alterna ciclicamente entre: Limpo -> Chuva Comum -> Chuva Pesada -> Limpo."""
        if hasattr(self, 'efeito_chuva'):
            return self.efeito_chuva.alternar_clima()
        return "limpo"