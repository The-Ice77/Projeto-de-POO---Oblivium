# src/core/game.py
import pygame
from src.ui.menu import Menu
from src.ui.dialogue_box import DialogueBox  
from src.ui.intro import Intro
from src.entities.player import Player
from src.mechanics.attributes import Atributos
from src.maps.map_loader import Mapa
from src.ui.transition import Transition
from src.entities.NPC import NPC
from src.ui.flashback import Flashback  
from src.mechanics.minigames import MinigameTiming, MinigameMash 
from src.mechanics.combat import CombatScreen
from src.utils import save_manager
from src.utils.resource_manager import ResourceManager, Animacao
from src.ui.hud import HUD
from src.utils.filtro_memoria import FiltroMemoria
from src.ui.tela_despertar import TelaDespertarMemoria

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
        self.mg_timing = MinigameTiming(self.LARGURA, self.ALTURA)
        self.mg_mash = MinigameMash(self.LARGURA, self.ALTURA)
        # --- CONFIGURAÇÕES DO JOGO ---
        self.config_velocidade_indice = 1  # 0: Lento, 1: Normal, 2: Rápido
        self.opcoes_velocidade = ["Lento", "Normal", "Rápido"]
        self.valores_velocidade = [0.5, 1.0, 2.5]
        
        self.config_velocidade_combate_indice = 0  # 0: 1.0x (Normal), 1: 1.5x (Rápido), 2: 2.0x (Ultra)
        self.opcoes_velocidade_combate = ["1.0x (Normal)", "1.5x (Rápido)", "2.0x (Ultra)"]
        self.valores_velocidade_combate = [1.0, 1.5, 2.0]
        
        self.config_audio = 100            # De 0 a 100%
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
            "INVENTARIO": InventoryState(self),
            "SLOTS": SlotsState(self) 
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

    def iniciar_combate(self, inimigos, on_vitoria=None, on_derrota=None, on_fuga=None):
        """Inicia um combate de forma modular e desacoplada em qualquer momento do jogo."""
        self.inimigos_em_cena = inimigos
        self.mudar_estado("COMBATE")
        self.tela_combate.iniciar_combate(
            jogador=self.halia,
            inimigos=self.inimigos_em_cena,
            on_vitoria=on_vitoria,
            on_derrota=on_derrota,
            on_fuga=on_fuga
        )

    def run(self):
        """Loop principal e delegação de controle para o estado ativo"""
        while self.running:
            eventos = pygame.event.get()
            teclas = pygame.key.get_pressed()
            
            for evento in eventos:
                if evento.type == pygame.QUIT:
                    self.running = False

            
            self.estado_atual.handle_events(eventos, teclas)
            self.estado_atual.update()
            
            self.tela.fill((0, 0, 0))
            self.estado_atual.draw(self.tela)
            
            pygame.display.flip()
            self.clock.tick(60)
    def salvar_estado(self, slot=None, tipo="manual"):
        slot_alvo = slot or self.slot_atual
        if not slot_alvo: 
            return 
            
        dados_save = {
            "cenario_atual": self.mapa_casa.cenario_atual,
            "tempo_jogado": self.tempo_jogado,
            "slot": slot_alvo,
            "tipo_save": tipo,
            "halia": {
                "nome": self.halia.nome,
                "x": self.halia.x,
                "y": self.halia.y,
                "vivo": getattr(self.halia, 'vivo', True),
                "estado_animacao": getattr(self.halia, 'estado_atual', "idle"),
                "vida_atual": getattr(self.halia, 'vida_atual', 100),
                "vida_maxima": getattr(self.halia, 'vida_maxima', 100),
                "mana_atual": getattr(self.halia, 'mana_atual', 50),
                "mana_maxima": getattr(self.halia, 'mana_maxima', 50),
                "fragmentos_memoria": getattr(self.halia, 'fragmentos_memoria', 0),
                "nivel_sincronia": getattr(self.halia, 'nivel_sincronia', 1),
                "dinheiro": getattr(self.halia, 'dinheiro', 0),
                "atributos": self.halia.atributos.to_dict(),
                "magias_desbloqueadas": getattr(self.halia, 'magias_desbloqueadas', []),
                "ataques_fisicos": getattr(self.halia, 'ataques_fisicos', ["ataque_basico", "golpe_concentrado"])
            },
            "carroceiro": {
                "x": self.carroceiro.x,
                "y": self.carroceiro.y,
                "visivel": self.carroceiro_visivel,
                "andando": self.carroceiro_andando,
                "conversa_terminou": getattr(self, 'conversa_carroceiro_terminou', False)
            },
            "flags": {
                "porta_aberta": getattr(self.mapa_casa, 'porta_aberta', False),
                "investigou_pedras": self.investigou_pedras,
                "flashback_magia_concluido": self.flashback_magia_concluido,
                "magia_ativa": self.magia_ativa,
                "magia_usada_no_puzzle": self.magia_usada_no_puzzle,
                "puzzle_concluido": (self.magia_ativa == "CONCLUIDO"),
                "combate_concluido": getattr(self, 'combate_estrada_concluido', False),
                "itens_coletados": self.itens_coletados,
                "historico_dialogos": list(self.caixa_dialogo.historico_escolhas)
            }
        }
        
        save_manager.salvar_dados(slot_alvo, dados_save, tipo=tipo)

    def carregar_estado(self, slot, tipo="manual"):
        dados = save_manager.carregar_dados(slot, tipo=tipo)
        if not dados:
            outro_tipo = "autosave" if tipo == "manual" else "manual"
            dados = save_manager.carregar_dados(slot, tipo=outro_tipo)
            
        if not dados:
            return False
            
        self.slot_atual = slot 
        self.tempo_jogado = dados.get("tempo_jogado", 0.0) 
        self.origem_pause = "JOGANDO"
        self.caixa_dialogo.historico_escolhas = set(dados.get("flags", {}).get("historico_dialogos", []))
        
        # 1. Recupera as flags e o progresso
        flags = dados.get("flags", {})
        self.mapa_casa.porta_aberta = flags.get("porta_aberta", False)
        self.investigou_pedras = flags.get("investigou_pedras", False)
        self.flashback_magia_concluido = flags.get("flashback_magia_concluido", False)
        self.magia_ativa = flags.get("magia_ativa", None)
        self.magia_usada_no_puzzle = flags.get("magia_usada_no_puzzle", None)
        self.combate_estrada_concluido = flags.get("combate_concluido", False)
        self.itens_coletados = flags.get("itens_coletados", [])
        self.conversa_carroceiro_terminou = dados.get("carroceiro", {}).get("conversa_terminou", False)
        
        # Reseta flags temporárias de transição e batalha em andamento
        self.inimigos_em_cena = []
        self.cena_inimigos_andando = False
        self.iniciando_combate = False
        self.conversa_combate_ativa = False
        self.transicao.estado = "INATIVO"
        
        # 2. Carrega o cenário e desobstrui caminhos se já resolvidos
        cenario_salvo = dados.get("cenario_atual", "CASA")
        self.mapa_casa.carregar_cenario(cenario_salvo)
        
        if cenario_salvo == "ESTRADA_2":
            if self.magia_ativa == "CONCLUIDO" or self.combate_estrada_concluido or flags.get("puzzle_concluido", False):
                self.magia_ativa = "CONCLUIDO"
                self.mapa_casa.desobstruir_estrada(self.magia_usada_no_puzzle or "FOGO")
        
        # 3. Restaura posições da Halia, atributos, Grimório e NPCs
        halia_dados = dados.get("halia", {})
        self.halia.x = halia_dados.get("x", 210)
        self.halia.y = halia_dados.get("y", 280)
        self.halia.fragmentos_memoria = halia_dados.get("fragmentos_memoria", 0)
        self.halia.nivel_sincronia = halia_dados.get("nivel_sincronia", 1 + self.halia.fragmentos_memoria)
        self.halia.dinheiro = halia_dados.get("dinheiro", 0)
        
        if "atributos" in halia_dados:
            self.halia.atributos = Atributos.from_dict(halia_dados["atributos"])
            self.halia.recalcular_status_derivados(manter_porcentagem=False)
            
        self.halia.vida_atual = halia_dados.get("vida_atual", self.halia.vida_maxima)
        self.halia.mana_atual = halia_dados.get("mana_atual", self.halia.mana_maxima)
        
        # Herda a condição de vivo ou reanima Halia para poder movimentar
        esta_vivo = halia_dados.get("vivo", True)
        if self.halia.vida_atual > 0:
            self.halia.vivo = esta_vivo
        else:
            self.halia.restaurar_total()
            
        # Limpa resíduos de combate
        self.halia.condicoes.clear()
        self.halia.defendendo = False
        self.halia.vulneravel = False
        self.halia.focado = False
        
        if self.halia.vivo:
            estado_salvo = halia_dados.get("estado_animacao", "idle")
            if estado_salvo == "morrer":
                estado_salvo = "idle"
            self.halia.mudar_estado(estado_salvo)
        else:
            self.halia.mudar_estado("morrer")
        
        if "magias_desbloqueadas" in halia_dados and halia_dados["magias_desbloqueadas"]:
            self.halia.magias_desbloqueadas = list(halia_dados["magias_desbloqueadas"])
        else:
            self.halia.atualizar_grimorio()
            
        if "ataques_fisicos" in halia_dados:
            self.halia.ataques_fisicos = list(halia_dados["ataques_fisicos"])
        
        carroceiro_dados = dados.get("carroceiro", {})
        self.carroceiro.x = carroceiro_dados.get("x", 200)
        self.carroceiro.y = carroceiro_dados.get("y", 330)
        self.carroceiro_visivel = carroceiro_dados.get("visivel", True)
        self.carroceiro_andando = carroceiro_dados.get("andando", False)
        
        # 4. Sincroniza imediatamente o Filtro de Memória, HUD e telas visuais com o save carregado
        if hasattr(self, 'filtro_memoria') and self.filtro_memoria:
            self.filtro_memoria.definir_estagio(self.halia.fragmentos_memoria, com_transicao_suave=False)
        if hasattr(self, 'tela_despertar') and self.tela_despertar:
            self.tela_despertar.reiniciar()
        if hasattr(self, 'estados') and "JOGANDO" in self.estados:
            self.estados["JOGANDO"].memoria_anterior_registrada = self.halia.fragmentos_memoria
        if hasattr(self, 'hud') and self.hud:
            self.hud.memorias_coletadas = self.halia.fragmentos_memoria
        
        return True 

    def resetar_progresso(self, slot_novo):
        """Limpa as variáveis globais para iniciar um Novo Jogo limpo no slot."""
        self.slot_atual = slot_novo
        self.tempo_jogado = 0.0
        self.itens_coletados = []
        self.caixa_dialogo.historico_escolhas.clear()
        save_manager.apagar_dados(slot_novo, tipo="autosave")
        
        # Reset da Halia
        self.halia.x, self.halia.y = 210, 280
        self.halia.fragmentos_memoria = 0
        self.halia.dinheiro = 0
        self.halia.atributos = Atributos(forca=7, destreza=10, constituicao=10, intelecto=13, sabedoria=11, presenca=12)
        self.halia.recalcular_status_derivados(manter_porcentagem=False)
        self.halia.atualizar_grimorio()
        # Inicia o jogo com vida e mana cheias
        self.halia.vida_atual = self.halia.vida_maxima
        self.halia.mana_atual = self.halia.mana_maxima
        self.halia.vivo = True
        self.halia.mudar_estado("idle")
        
        # Reset do Carroceiro
        self.carroceiro.x, self.carroceiro.y = 1350, 330
        self.carroceiro_visivel = False
        self.carroceiro_andando = False
        self.conversa_carroceiro_terminou = False
        self.progresso_npcs["carroceiro"] = 0
        
        # Reset de Flags do Mapa e Progresso
        self.fechando_porta = False
        self.aguardando_fim_viagem = False
        self.investigou_pedras = False
        self.flashback_magia_concluido = False
        self.mapa_casa.porta_aberta = False
        self.magia_ativa = None
        self.magia_usada_no_puzzle = None
        self.magia_selecionada_temporaria = None
        self.combate_estrada_concluido = False
        self.iniciando_combate = False
        self.cena_inimigos_andando = False
        self.conversa_combate_ativa = False
        self.inimigos_em_cena = []
        self.transicao.estado = "INATIVO"

        # Sincroniza e reseta o Filtro de Memória (100% P&B / Estágio 0), HUD e Cutscenes
        if hasattr(self, 'filtro_memoria') and self.filtro_memoria:
            self.filtro_memoria.reiniciar(0)
        if hasattr(self, 'tela_despertar') and self.tela_despertar:
            self.tela_despertar.reiniciar()
        if hasattr(self, 'estados') and "JOGANDO" in self.estados:
            self.estados["JOGANDO"].memoria_anterior_registrada = 0
        if hasattr(self, 'hud') and self.hud:
            self.hud.memorias_coletadas = 0
        
        # Recarrega o cenário inicial limpo
        self.mapa_casa.carregar_cenario("CASA")

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