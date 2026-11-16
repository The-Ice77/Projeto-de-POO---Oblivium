# src/core/game.py
import pygame
from src.ui.menu import Menu
from src.ui.dialogue_box import DialogueBox  
from src.ui.scenes import Intro, Flashback, TelaDespertarMemoria
from src.entities.player import Player
from src.maps.map_loader import Mapa
from src.ui.transition import Transition
from src.entities.npc_factory import NPCFactory
from src.mechanics.minigames import MinigameTiming, MinigameMash 
from src.mechanics.combat import CombatScreen
from src.core.save_manager import SaveManager
from src.ui.hud import HUD
from src.utils.filtro_memoria import FiltroMemoria
from src.ui.notification_manager import NotificationManager
from src.utils.constants import desenvolvimento_habilitado
from src.utils.animations import EfeitoFolhas
from src.utils.clima import EfeitoChuva
from src.core.audio_manager import AudioManager
from src.mechanics.progression import AchievementManager, QuestManager
from src.mechanics.progression.segredo_oakhaven import SegredoOakhaven
from src.mechanics.progression.economia_demo import VERSAO_ECONOMIA
from src.ui.quest_tracker import QuestTracker

# Importação dos Estados Estruturados
from src.states.menus import (
    MenuState,
    PauseState,
    CreditsState,
    SettingsState,
    ControlesState,
    SlotsState,
    SelecaoControlesState,
    ConquistasState,
)
from src.states.playing import PlayingState
from src.states.intro_states import IntroState
from src.states.combat_states import CombatState
from src.states.inventory_states import InventoryState
from src.states.shop_states import ShopState



class Game:
    def __init__(self):
        # --- Configurações de Janela e Clock ---
        self.LARGURA = 1280
        self.ALTURA = 720
        self.tela = pygame.display.set_mode((self.LARGURA, self.ALTURA))
        pygame.display.set_caption("Oblivium")
        self.clock = pygame.time.Clock()
        self.running = True
        self.foco_janela = True
        self.segredo_oakhaven = SegredoOakhaven()

        # --- Componentes Globais Compartilhados ---
        self.menu = Menu()
        self.caixa_dialogo = DialogueBox(self.LARGURA, game=self) 
        self.intro = Intro(self.LARGURA, self.ALTURA, game=self)
        self.mapa_casa = Mapa(self, self.LARGURA, self.ALTURA)
        self.transicao = Transition(self.LARGURA, self.ALTURA)
        self.flashback_sistema = Flashback(self.LARGURA, self.ALTURA, game=self) 
        self.tela_despertar = TelaDespertarMemoria(self.LARGURA, self.ALTURA, game=self)
        self.tela_combate = CombatScreen(self.LARGURA, self.ALTURA)
        self.tela_combate.game = self
        self.filtro_memoria = FiltroMemoria(self.LARGURA, self.ALTURA)
        self.efeito_folhas = EfeitoFolhas(self.LARGURA, self.ALTURA, quantidade_folhas=28)
        self.efeito_chuva = EfeitoChuva(self.LARGURA, self.ALTURA, game=self)
        self.mg_timing = MinigameTiming(self.LARGURA, self.ALTURA)
        self.mg_mash = MinigameMash(self.LARGURA, self.ALTURA)
        self.notificacoes = NotificationManager(self.LARGURA, self.ALTURA)
        self.conquistas = AchievementManager(self)
        self.missoes = QuestManager(self)
        self.quest_manager = self.missoes
        self.caixa_dialogo.manager.quest_manager = self.missoes
        self.quest_tracker = QuestTracker(self.LARGURA, self.ALTURA)
        self.dt_fator = 1.0
        self.dt = 1.0 / 60.0
        self.dev_commands = None
        if desenvolvimento_habilitado():
            from src.utils.dev_commands import ComandosDev
            self.dev_commands = ComandosDev(self)
        # --- CONFIGURAÇÕES DO JOGO ---
        self.config_velocidade_indice = 1  # 0: Lento, 1: Normal, 2: Rápido
        self.opcoes_velocidade = ["Lento", "Normal", "Rápido"]
        self.valores_velocidade = [0.5, 1.0, 2.5]
        
        self.config_velocidade_combate_indice = 0  # 0: 1.0x (Normal), 1: 1.5x (Rápido), 2: 2.0x (Ultra)
        self.opcoes_velocidade_combate = ["1.0x (Normal)", "1.5x (Rápido)", "2.0x (Ultra)"]
        self.valores_velocidade_combate = [1.0, 1.5, 2.0]
        
        # --- Configurações de Áudio por Área (0 a 100%) ---
        self.PADROES_AUDIO = {
            "master": 100,
            "musica": 55,
            "sfx": 95,
            "ambiente": 70,
            "mutado": False,
        }
        self.config_audio = self.PADROES_AUDIO["master"]            # Volume Geral (Master)
        self.config_audio_musica = self.PADROES_AUDIO["musica"]     # Volume da Música de Fundo (BGM)
        self.config_audio_sfx = self.PADROES_AUDIO["sfx"]           # Volume dos Efeitos Sonoros (SFX)
        self.config_audio_ambiente = self.PADROES_AUDIO["ambiente"] # Volume dos Sons de Ambiente (BGS / Clima)
        self.config_audio_mutado = self.PADROES_AUDIO["mutado"]     # Silenciar Tudo (Mute)

        self.audio = AudioManager(self)
        self.carregar_preferencias_usuario()
        self.save_manager = SaveManager(self)
        self.redefinindo_tecla = False     # Mantido por compatibilidade (REGRAS §3); tecla_interacao usa self.controles["Interagir"]
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
        self.halia.game = self
        self.carroceiro = NPCFactory.criar("carroceiro", x=1350, y=330, velocidade=2)

        # --- Flags Globais de Progresso Permanente (Salvas, restauradas e resetadas via SaveManager) ---
        self.investigou_pedras = False
        self.flashback_magia_concluido = False
        self.magia_ativa = None
        self.magia_usada_no_puzzle = None
        self.combate_estrada_concluido = False
        self.pedra_torvald_quebrada = False
        self.oakhaven_noite = False
        self.oakhaven_destruida = False
        self.dragao_derrotado = False
        self.desespero_superado = False
        self.patusco_pos_oakhaven = None
        self.estagio_memoria_apresentado = 0
        self.etapa_epilogo = "NAO_INICIADO"
        self.versao_progressao = 2
        self.versao_economia = VERSAO_ECONOMIA
        # Rastreia em que ponto da conversa cada NPC está
        self.progresso_npcs = {
            "carroceiro": 0  # 0: Início, 1: Falou com ele, 2: Viagem liberada, etc.
        }

        # --- Flags Transitórias de Cena, Cutscene, Minigame e Combate (Resetadas no load e Novo Jogo) ---
        self.fechando_porta = False
        self.aguardando_fim_viagem = False
        self.timer_magia = 0
        self.distanciando_halia = False
        self.bola_fogo_x = 0
        self.bola_fogo_y = 0
        self.bola_fogo_ativa = False
        self.magia_selecionada_temporaria = None
        self.iniciando_combate = False
        self.cena_inimigos_andando = False
        self.conversa_combate_ativa = False
        self.carroceiro_visivel = False
        self.carroceiro_andando = False
        self.conversa_carroceiro_terminou = False
        self.combate_climax_dragao = False
        self.aguardando_dialogo_pos_dragao = False
        self.flashback_monumento_ativo = False
        self.flashback_sylvan_ativo = False
        self.despedida_demo_exibida = False
        self.partindo_estrada2 = False
        self.pronto_viajar_oakhaven = False
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
            "Inventário": pygame.K_TAB,
            "Missões": pygame.K_o
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
        self.origem_creditos = "MENU"
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
                "Inventário": pygame.K_TAB,
                "Missões": pygame.K_o
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
                "Inventário": pygame.K_TAB,
                "Missões": pygame.K_o
            }

    @property
    def tecla_interacao(self):
        """Retorna a tecla de interação atual a partir de self.controles['Interagir']."""
        if hasattr(self, "controles") and isinstance(self.controles, dict):
            return self.controles.get("Interagir", pygame.K_e)
        return pygame.K_e

    @tecla_interacao.setter
    def tecla_interacao(self, nova_tecla):
        """Atualiza a tecla de interação diretamente em self.controles['Interagir']."""
        if not hasattr(self, "controles") or not isinstance(self.controles, dict):
            self.controles = {"Interagir": nova_tecla}
        else:
            self.controles["Interagir"] = nova_tecla

    @property
    def teclas_interacao(self):
        """Atalhos aceitos igualmente no toque e no gesto de interação contínua."""
        tecla = self.tecla_interacao
        if tecla == pygame.K_SPACE:
            return (tecla, pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_e)
        if tecla == pygame.K_e:
            return (tecla, pygame.K_SPACE)
        return (tecla,)

    def obter_nome_tecla(self, codigo_tecla):
        """Retorna o nome legível em português de uma tecla do Pygame (ex.: SPACE -> ESPAÇO)."""
        mapa_nomes = {
            pygame.K_SPACE: "ESPAÇO",
            pygame.K_RETURN: "ENTER",
            pygame.K_KP_ENTER: "ENTER",
            pygame.K_ESCAPE: "ESC",
            pygame.K_TAB: "TAB",
            pygame.K_UP: "SETA CIMA",
            pygame.K_DOWN: "SETA BAIXO",
            pygame.K_LEFT: "SETA ESQUERDA",
            pygame.K_RIGHT: "SETA DIREITA",
        }
        if codigo_tecla in mapa_nomes:
            return mapa_nomes[codigo_tecla]
        return pygame.key.name(codigo_tecla).upper()

    @property
    def nome_tecla_interacao(self):
        """Retorna o rótulo em maiúsculas da tecla de interação ativa (ex.: 'E', 'ESPAÇO')."""
        return self.obter_nome_tecla(self.tecla_interacao)

    def aplicar_config_audio(self):
        """Sincroniza todas as faixas de volume e estado de mute com o AudioManager."""
        self.config_audio = max(0, min(100, int(getattr(self, "config_audio", 100))))
        self.config_audio_musica = max(0, min(100, int(getattr(self, "config_audio_musica", 55))))
        self.config_audio_sfx = max(0, min(100, int(getattr(self, "config_audio_sfx", 95))))
        self.config_audio_ambiente = max(0, min(100, int(getattr(self, "config_audio_ambiente", 70))))
        self.config_audio_mutado = bool(getattr(self, "config_audio_mutado", False))

        if getattr(self, "audio", None):
            self.audio.definir_volume_master(self.config_audio)
            self.audio.definir_volume_musica(self.config_audio_musica)
            self.audio.definir_volume_sfx(self.config_audio_sfx)
            self.audio.definir_volume_ambiente(self.config_audio_ambiente)
            self.audio.definir_mute(self.config_audio_mutado)

    def aplicar_config_velocidades(self):
        """Aplica as velocidades salvas de diálogo e combate aos respectivos controladores."""
        if getattr(self, "valores_velocidade", None):
            self.config_velocidade_indice = max(
                0, min(len(self.valores_velocidade) - 1, int(getattr(self, "config_velocidade_indice", 1)))
            )
            if getattr(self, "caixa_dialogo", None):
                self.caixa_dialogo.velocidade_texto = self.valores_velocidade[self.config_velocidade_indice]

        if getattr(self, "valores_velocidade_combate", None):
            self.config_velocidade_combate_indice = max(
                0, min(len(self.valores_velocidade_combate) - 1, int(getattr(self, "config_velocidade_combate_indice", 0)))
            )
            if getattr(self, "tela_combate", None) and hasattr(self.tela_combate, "definir_velocidade"):
                self.tela_combate.definir_velocidade(
                    self.valores_velocidade_combate[self.config_velocidade_combate_indice]
                )

    def carregar_preferencias_usuario(self):
        """Carrega preferências persistidas sem gravar em disco caso o arquivo não exista."""
        from src.utils import save_storage as save_io

        dados = save_io.carregar_preferencias_usuario()
        if isinstance(dados, dict):
            audio = dados.get("audio")
            if isinstance(audio, dict):
                mapa_audio = (
                    ("master", "config_audio"),
                    ("musica", "config_audio_musica"),
                    ("sfx", "config_audio_sfx"),
                    ("ambiente", "config_audio_ambiente"),
                )
                for chave, attr in mapa_audio:
                    val = audio.get(chave)
                    if isinstance(val, (int, float)) and not isinstance(val, bool):
                        setattr(self, attr, max(0, min(100, int(round(val)))))
                if "mutado" in audio:
                    self.config_audio_mutado = bool(audio.get("mutado"))

            vel_txt = dados.get("velocidade_texto_indice")
            if isinstance(vel_txt, int) and not isinstance(vel_txt, bool):
                self.config_velocidade_indice = vel_txt

            vel_cbt = dados.get("velocidade_combate_indice")
            if isinstance(vel_cbt, int) and not isinstance(vel_cbt, bool):
                self.config_velocidade_combate_indice = vel_cbt

        self.aplicar_config_audio()
        self.aplicar_config_velocidades()

    def salvar_preferencias_usuario(self):
        """Persiste as preferências atuais de áudio e interface em config_usuario.json."""
        from src.utils import save_storage as save_io

        dados = {
            "audio": {
                "master": int(getattr(self, "config_audio", self.PADROES_AUDIO["master"])),
                "musica": int(getattr(self, "config_audio_musica", self.PADROES_AUDIO["musica"])),
                "sfx": int(getattr(self, "config_audio_sfx", self.PADROES_AUDIO["sfx"])),
                "ambiente": int(getattr(self, "config_audio_ambiente", self.PADROES_AUDIO["ambiente"])),
                "mutado": bool(getattr(self, "config_audio_mutado", False)),
            },
            "velocidade_texto_indice": int(getattr(self, "config_velocidade_indice", 1)),
            "velocidade_combate_indice": int(getattr(self, "config_velocidade_combate_indice", 0)),
        }
        return save_io.salvar_preferencias_usuario(dados)

    def restaurar_padroes_audio(self, salvar=True):
        """Restaura a mixagem equilibrada padrão de áudio e opcionalmente salva no disco."""
        self.config_audio = self.PADROES_AUDIO["master"]
        self.config_audio_musica = self.PADROES_AUDIO["musica"]
        self.config_audio_sfx = self.PADROES_AUDIO["sfx"]
        self.config_audio_ambiente = self.PADROES_AUDIO["ambiente"]
        self.config_audio_mutado = self.PADROES_AUDIO["mutado"]
        self.aplicar_config_audio()
        if salvar:
            self.salvar_preferencias_usuario()

    def mudar_estado(self, novo_estado):
        """Altera dinamicamente o comportamento e as telas do jogo"""
        if novo_estado in self.estados:
            nome_anterior = getattr(self, "nome_estado_atual", None)
            anterior = getattr(self, "estado_atual", None)
            destino = self.estados[novo_estado]
            mudou = anterior is not destino or nome_anterior != novo_estado
            sair = getattr(anterior, "ao_sair", None)
            if mudou and callable(sair):
                sair(proximo_estado=novo_estado)
            if mudou and getattr(self, "segredo_oakhaven", None):
                self.segredo_oakhaven.interromper()
            self.nome_estado_atual = novo_estado
            self.estado_atual = destino
            if novo_estado in ("MENU", "INTRO"):
                flashback = getattr(self, "flashback_sistema", None)
                cancelar = getattr(flashback, "cancelar", None)
                if callable(cancelar):
                    cancelar(sincronizar_ambiente=False)
                despertar = getattr(self, "tela_despertar", None)
                if despertar and despertar.ativo:
                    despertar.reiniciar(sincronizar_ambiente=False)
                audio = getattr(self, "audio", None)
                if audio:
                    for contexto in ("flashback", "despertar", "memoria_onda"):
                        audio.parar_sfx_contexto(contexto)
            if novo_estado == "MENU":
                self.menu.atualizar_opcoes()
                if hasattr(self, 'audio') and self.audio:
                    self.audio.parar_ambiente(fade_ms=400)
                    if hasattr(self.audio, 'limpar_contexto_combate'):
                        self.audio.limpar_contexto_combate()
                    self.audio.tocar_musica(
                        "menu_tema", loop=-1, fade_ms=800, salvar_anterior=False, contexto="menu"
                    )
            elif novo_estado == "INTRO":
                if hasattr(self, 'audio') and self.audio:
                    self.audio.parar_ambiente(fade_ms=400)
                    if hasattr(self.audio, 'limpar_contexto_combate'):
                        self.audio.limpar_contexto_combate()
                    self.audio.tocar_musica(
                        "cutscene_intro", loop=-1, fade_ms=900, salvar_anterior=False, contexto="intro"
                    )
            elif novo_estado == "JOGANDO":
                self.sincronizar_trilha_cenario(fade_ms=1000)
            entrar = getattr(destino, "ao_entrar", None)
            if mudou and callable(entrar):
                entrar(estado_anterior=nome_anterior)

    def sincronizar_trilha_cenario(self, fade_ms=1000):
        """Reaplica a música apropriada ao cenário e estado narrativo atual em exploração."""
        if not (hasattr(self, 'audio') and self.audio and getattr(self, 'nome_estado_atual', '') == 'JOGANDO'):
            return
        if not (hasattr(self, 'mapa_casa') and self.mapa_casa):
            return
        if hasattr(self.mapa_casa, '_deve_sincronizar_trilha_cenario') and not self.mapa_casa._deve_sincronizar_trilha_cenario():
            return
        trilha = self.mapa_casa.obter_trilha_cenario() if hasattr(self.mapa_casa, 'obter_trilha_cenario') else None
        if trilha:
            self.audio.tocar_musica(trilha, loop=-1, fade_ms=fade_ms, contexto="mundo")
        self.sincronizar_ambiente_cenario(fade_ms=fade_ms)

    def sincronizar_ambiente_cenario(self, fade_ms=900):
        """Resolve ambiente por cena narrativa, clima e mapa, nessa ordem."""
        if not (hasattr(self, 'audio') and self.audio and getattr(self, 'nome_estado_atual', '') == 'JOGANDO'):
            return
        flashback = getattr(self, "flashback_sistema", None)
        estado_flashback = getattr(flashback, "estado", "INATIVO")
        if estado_flashback != "INATIVO":
            if estado_flashback == "ESCURIDAO" and getattr(flashback, "tipo", None) == "acampamento":
                self.audio.tocar_ambiente("fogueira", loop=-1, fade_ms=fade_ms, volume_extra=0.70)
            else:
                self.audio.parar_ambiente(fade_ms=min(300, max(0, int(fade_ms))))
            return
        if (
            getattr(getattr(self, "intro", None), "ativo", False)
            or getattr(getattr(self, "tela_despertar", None), "estado", "INATIVO") != "INATIVO"
            or getattr(self, "etapa_epilogo", None) == "DESPERTAR_PENDENTE"
        ):
            self.audio.parar_ambiente(fade_ms=min(300, max(0, int(fade_ms))))
            return
        clima = getattr(self, 'efeito_chuva', None)
        modo_clima = str(getattr(clima, 'modo_atual', 'limpo') or 'limpo').lower()
        if modo_clima in ('comum', 'pesada', 'chuva', 'tempestade'):
            self.audio.tocar_ambiente("chuva", loop=-1, fade_ms=fade_ms)
            return
        if modo_clima in ('neve', 'nevasca'):
            self.audio.tocar_ambiente("vento_noite", loop=-1, fade_ms=fade_ms)
            return
        amb = self.mapa_casa.obter_ambiente_cenario() if (hasattr(self, 'mapa_casa') and hasattr(self.mapa_casa, 'obter_ambiente_cenario')) else None
        if amb:
            self.audio.tocar_ambiente(amb, loop=-1, fade_ms=fade_ms)
        else:
            self.audio.parar_ambiente(fade_ms=max(300, int(fade_ms)))

    def abrir_loja(self, loja_id=None):
        """Abre a interface da loja configurando o catálogo específico do mercador."""
        if "LOJA" in self.estados:
            self.estados["LOJA"].configurar_loja(loja_id)
        self.mudar_estado("LOJA")

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

    def observar_foco_janela(self, eventos):
        """Mantém o foco correto mesmo quando menus recebem os eventos da janela."""
        for evento in eventos:
            if evento.type == pygame.WINDOWFOCUSLOST:
                self.foco_janela = False
                self.segredo_oakhaven.interromper()
            elif evento.type == pygame.WINDOWFOCUSGAINED:
                self.foco_janela = True
            elif evento.type == pygame.ACTIVEEVENT and evento.state & 2:
                self.foco_janela = bool(evento.gain)
                if not self.foco_janela:
                    self.segredo_oakhaven.interromper()

    def run(self):
        """O Loop Principal enxuto, focado em delegar tarefas ao Estado Atual"""
        while self.running:
            eventos = pygame.event.get()
            teclas = pygame.key.get_pressed()
            self.observar_foco_janela(eventos)

            for evento in eventos:
                if evento.type == pygame.QUIT:
                    self.running = False

            if not self.running:
                break

            # Interceptação Global: Histórico de Notificações [H] e Comandos de Dev [']
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
            if hasattr(self, 'audio') and self.audio:
                self.audio.update(self.dt)
            
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
            dt_ms = self.clock.tick(60)
            self.atualizar_tempo_quadro(dt_ms)

    def atualizar_tempo_quadro(self, dt_ms):
        """Atualiza dt_fator (legado) e dt em segundos (limitado a 50 ms) após clock.tick."""
        self.dt_fator = max(0.5, min(2.0, dt_ms / 16.666)) if dt_ms > 0 else 1.0
        self.dt = min(0.05, dt_ms / 1000.0) if dt_ms > 0 else (1.0 / 60.0)

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
            if str(getattr(self.efeito_chuva, 'modo_atual', 'limpo')).lower() == 'limpo':
                self.sincronizar_ambiente_cenario(fade_ms=800)

    def alternar_clima(self):
        """Alterna ciclicamente entre: Limpo -> Chuva Comum -> Chuva Pesada -> Limpo."""
        if hasattr(self, 'efeito_chuva'):
            res = self.efeito_chuva.alternar_clima()
            if str(getattr(self.efeito_chuva, 'modo_atual', 'limpo')).lower() == 'limpo':
                self.sincronizar_ambiente_cenario(fade_ms=800)
            return res
        return "limpo"
