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
from src.utils import save_manager

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
        self.tela_combate = CombatScreen(self.LARGURA, self.ALTURA)
        self.mg_timing = MinigameTiming(self.LARGURA, self.ALTURA)
        self.mg_mash = MinigameMash(self.LARGURA, self.ALTURA)
        # --- CONFIGURAÇÕES DO JOGO ---
        self.config_velocidade_indice = 1  # 0: Lento, 1: Normal, 2: Rápido
        self.opcoes_velocidade = ["Lento", "Normal", "Rápido"]
        self.valores_velocidade = [0.5, 1.0, 2.5]
        
        self.config_audio = 100            # De 0 a 100%
        self.tecla_interacao = pygame.K_e  # Tecla padrão para interagir
        self.redefinindo_tecla = False     # Flag para escutar a nova tecla
       # --- CONTROLE DE SAVES / SLOTS ---
        self.acao_slots = "SALVAR" 
        self.origem_slots = "PAUSE"
        self.slot_atual = None      # Memoriza o slot da sessão (1, 2 ou 3)
        self.tempo_jogado = 0.0     # Conta os segundos jogados
        self.fonte_indicador = pygame.font.Font(None, 24)
        self.itens_coletados = []   # tentando fazer isso funcionar
        
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
        # --- CONTROLOS DO JOGO (REMAPEÁVEIS) ---
        self.controles = {
            "Cima": pygame.K_w,
            "Baixo": pygame.K_s,
            "Esquerda": pygame.K_a,
            "Direita": pygame.K_d,
            "Correr": pygame.K_LSHIFT,
            "Interagir": pygame.K_e,
            "Pause": pygame.K_ESCAPE,
            "Inventário": pygame.K_i
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
            "CONTROLES": ControlesState(self),
            "SLOTS": SlotsState(self) # <-- NOVO ESTADO ADICIONADO
        }
        self.estado_atual = self.estados["MENU"]
        self.origem_configuracoes = "MENU"
        # Rastreia em que ponto da conversa cada NPC está
        self.progresso_npcs = {
            "carroceiro": 0  # 0: Início, 1: Falou com ele, 2: Viagem liberada, etc.
        }

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
    def salvar_estado(self, slot=None):
        slot_alvo = slot or self.slot_atual
        if not slot_alvo: 
            return 
            
        dados_save = {
            "cenario_atual": self.mapa_casa.cenario_atual,
            "tempo_jogado": self.tempo_jogado,
            "halia": {
                "x": self.halia.x,
                "y": self.halia.y,
                "vida_atual": getattr(self.halia, 'vida_atual', 100),
                "mana_atual": getattr(self.halia, 'mana_atual', 50),
            },
            "carroceiro": {
                "x": self.carroceiro.x,
                "y": self.carroceiro.y,
                "visivel": self.carroceiro_visivel,
                "andando": self.carroceiro_andando
            },
            "flags": {
                "porta_aberta": getattr(self.mapa_casa, 'porta_aberta', False),
                "investigou_pedras": self.investigou_pedras,
                "flashback_magia_concluido": self.flashback_magia_concluido,
                "itens_coletados": self.itens_coletados,
                "historico_dialogos": list(self.caixa_dialogo.historico_escolhas)
            }
        }
        
        save_manager.salvar_dados(slot_alvo, dados_save)

    def carregar_estado(self, slot):
        dados = save_manager.carregar_dados(slot)
        if not dados:
            return False
            
        self.slot_atual = slot 
        self.tempo_jogado = dados.get("tempo_jogado", 0.0) 
        self.caixa_dialogo.historico_escolhas = set(dados["flags"].get("historico_dialogos", []))
        
        
        # 1. Recupera as flags e a lista de itens coletados PRIMEIRO
        self.mapa_casa.porta_aberta = dados["flags"].get("porta_aberta", False)
        self.investigou_pedras = dados["flags"]["investigou_pedras"]
        self.flashback_magia_concluido = dados["flags"]["flashback_magia_concluido"]
        self.itens_coletados = dados["flags"].get("itens_coletados", [])
        
        # 2. Carrega o cenário (que já deve nascer filtrado se o mapa consultar a lista)
        cenario_salvo = dados["cenario_atual"]
        self.mapa_casa.carregar_cenario(cenario_salvo)
        self.filtrar_itens_coletados() # Aplica o corte de itens imediatamente
        
        # 3. Restaura posições da Halia e NPCs exatamente como estavam
        self.halia.x = dados["halia"]["x"]
        self.halia.y = dados["halia"]["y"]
        self.halia.vida_atual = dados["halia"]["vida_atual"]
        self.halia.mana_atual = dados["halia"]["mana_atual"]
        
        self.carroceiro.x = dados["carroceiro"]["x"]
        self.carroceiro.y = dados["carroceiro"]["y"]
        self.carroceiro_visivel = dados["carroceiro"]["visivel"]
        self.carroceiro_andando = dados["carroceiro"]["andando"]
        
        
        return True 
    
    def filtrar_itens_coletados(self):
        """Filtra os itens do mapa atual com base na sua posição na lista original da sala."""
        if not hasattr(self, 'mapa_casa') or not self.mapa_casa:
            return
            
        itens_filtrados = []
        for indice, item in enumerate(self.mapa_casa.itens_no_chao):
            # ID único baseado estritamente na sala e na ordem do item na sala
            id_unico = f"{self.mapa_casa.cenario_atual}_item_{indice}"
            if id_unico not in self.itens_coletados:
                itens_filtrados.append(item)
        self.mapa_casa.itens_no_chao = itens_filtrados

    def executar_com_feedback(self, texto, funcao_acao):
        """Exibe a tela escura de feedback ('Salvando...', 'Carregando...') 
           diretamente na gameplay antes de executar a ação."""
        
        # Desenha o estado atual do jogo (o que está a acontecer na tela por trás do pause)
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
        
        # Mantém o feedback visível por 800 milissegundos de forma fluida
        tempo_inicio = pygame.time.get_ticks()
        while pygame.time.get_ticks() - tempo_inicio < 800:
            pygame.event.pump()