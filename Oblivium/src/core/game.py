# src/core/game.py
import pygame
from src.ui.menu import Menu
from src.ui.dialogue_box import DialogueBox  
from src.ui.intro import Intro
from src.entities.player import Player
from src.maps.map_loader import Mapa
from src.ui.transition import Transition
from src.entities.NPC import NPC
from src.ui.flashback import Flashback  
from src.mechanics.minigames import MinigameTiming, MinigameMash 
from src.mechanics.combat import CombatScreen

# Importação dos Estados Estruturados
from src.states.menu_states import MenuState
from src.states.playing_states import PlayingState
from src.states.intro_states import IntroState
from src.states.combat_states import CombatState



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
        self.mapa_casa = Mapa(self.LARGURA, self.ALTURA)
        self.transicao = Transition(self.LARGURA, self.ALTURA)
        self.flashback_sistema = Flashback(self.LARGURA, self.ALTURA) 
        self.tela_combate = CombatScreen(self.LARGURA, self.ALTURA)
        self.mg_timing = MinigameTiming(self.LARGURA, self.ALTURA)
        self.mg_mash = MinigameMash(self.LARGURA, self.ALTURA)

        self.fonte_indicador = pygame.font.Font(None, 24)
        
        # --- Entidades Estáveis ---
        self.halia = Player("Halia", 100, 210, 280, 3, None, 50)
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
        
        # CORREÇÃO DA VARIÁVEL: Mantendo estritamente "cena" em português para evitar AttributeError
        self.inimigos_em_cena = [] 

        # --- Máquina de Estados ---
        self.estados = {
            "MENU": MenuState(self),
            "INTRO": IntroState(self),
            "JOGANDO": PlayingState(self),
            "COMBATE": CombatState(self)
        }
        self.estado_atual = self.estados["MENU"]

    def mudar_estado(self, novo_estado):
        """Altera dinamicamente o comportamento e as telas do jogo"""
        if novo_estado in self.estados:
            self.estado_atual = self.estados[novo_estado]

    def run(self):
        """Loop principal e delegação de controle para o estado ativo"""
        while self.running:
            eventos = pygame.event.get()
            teclas = pygame.key.get_pressed()
            
            for evento in eventos:
                if evento.type == pygame.QUIT:
                    self.running = False

            # Delegação limpa de Responsabilidade Única
            self.estado_atual.handle_events(eventos, teclas)
            self.estado_atual.update()
            
            # Renderização em Camada Isolada
            self.tela.fill((0, 0, 0))
            self.estado_atual.draw(self.tela)
            
            pygame.display.flip()
            self.clock.tick(60)