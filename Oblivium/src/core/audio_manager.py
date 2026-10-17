# src/core/audio_manager.py
import os
import math
import struct
import logging
import pygame

logger = logging.getLogger(__name__)

# Diretórios base de assets de áudio
_DIRETORIO_ATUAL = os.path.dirname(os.path.abspath(__file__))
_DIRETORIO_SRC = os.path.dirname(_DIRETORIO_ATUAL)
_DIRETORIO_RAIZ = os.path.dirname(_DIRETORIO_SRC)
PASTA_AUDIO = os.path.join(_DIRETORIO_RAIZ, "assets", "audio")
PASTA_MUSICA = os.path.join(PASTA_AUDIO, "music")
PASTA_AMBIENTE = os.path.join(PASTA_AUDIO, "ambience")
PASTA_SFX = os.path.join(PASTA_AUDIO, "sfx")


class AudioManager:
    """
    Gerenciador Central de Áudio e Música de Oblivium.
    
    Recursos principais:
    - Mixagem multicanal dedicada: BGM (pygame.mixer.music), BGS/Ambience (canal reservado) e SFX dinâmico.
    - Controle hierárquico de volume (Master, Música, Ambiente, SFX).
    - Resolução automática de nomes de arquivos (.ogg, .wav, .mp3) e aliases amigáveis.
    - Fallback procedural integrado: sintetiza ondas sonoras leves via PCM caso arquivos
      de som ainda não existam no disco, garantindo feedback imediato sem travar o motor.
    - Memória de trilha musical para alternância suave (ex: transição de/para combate).
    """

    _instancia = None

    def __init__(self, game=None):
        AudioManager._instancia = self
        self.game = game

        # Volumes base (0.0 a 1.0)
        self.volume_master = 1.0
        self.volume_musica = 0.75
        self.volume_sfx = 0.85
        self.volume_ambiente = 0.65

        # Estado atual de reprodução
        self.musica_atual = None
        self.musica_anterior = None
        self.ambiente_atual = None
        self.musica_pausada = False

        # Caches
        self._cache_sfx = {}
        self._cache_procedural = {}
        self._avisos_arquivo_ausente = set()

        # Inicialização do Mixer Pygame
        self._inicializar_mixer()

        # Canal reservado para Efeitos de Ambiente (BGS)
        self.CANAL_AMBIENTE_ID = 0
        try:
            pygame.mixer.set_reserved(1)
            self.canal_ambiente = pygame.mixer.Channel(self.CANAL_AMBIENTE_ID)
        except Exception as e:
            logger.warning("Falha ao reservar canal de ambiente: %s", e)
            self.canal_ambiente = None

    @classmethod
    def get_instance(cls):
        """Retorna a instância ativa do AudioManager."""
        return cls._instancia

    def _inicializar_mixer(self):
        """Inicializa o subsistema de áudio com buffer responsivo."""
        if not pygame.mixer.get_init():
            try:
                # 44.1kHz, 16-bit com sinal, 2 canais (estéreo), buffer de 512 amostras para baixa latência
                pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=512)
                pygame.mixer.init()
                pygame.mixer.set_num_channels(32)
            except Exception as e:
                logger.error("Erro ao inicializar pygame.mixer: %s", e)
        else:
            try:
                pygame.mixer.set_num_channels(32)
            except Exception:
                pass

    # =========================================================================
    # CONTROLE DE VOLUMES
    # =========================================================================

    @staticmethod
    def _normalizar_volume(valor):
        """Converte valor percentual (0 a 100) ou unitário (0.0 a 1.0) para float normalizado [0.0, 1.0]."""
        try:
            val = float(valor)
            if val > 1.0:
                val = val / 100.0
            return max(0.0, min(1.0, val))
        except (ValueError, TypeError):
            return 1.0

    def definir_volume_master(self, valor):
        """Define o volume geral (Master)."""
        self.volume_master = self._normalizar_volume(valor)
        self._aplicar_volumes()

    def definir_volume_musica(self, valor):
        """Define o volume da música de fundo (BGM)."""
        self.volume_musica = self._normalizar_volume(valor)
        self._aplicar_volume_musica()

    def definir_volume_sfx(self, valor):
        """Define o volume dos efeitos sonoros (SFX)."""
        self.volume_sfx = self._normalizar_volume(valor)

    def definir_volume_ambiente(self, valor):
        """Define o volume do som de ambiente contínuo (BGS)."""
        self.volume_ambiente = self._normalizar_volume(valor)
        self._aplicar_volume_ambiente()

    def _aplicar_volumes(self):
        self._aplicar_volume_musica()
        self._aplicar_volume_ambiente()

    def _aplicar_volume_musica(self):
        try:
            vol_final = self.volume_musica * self.volume_master
            pygame.mixer.music.set_volume(vol_final)
        except Exception:
            pass

    def _aplicar_volume_ambiente(self):
        if self.canal_ambiente:
            try:
                vol_final = self.volume_ambiente * self.volume_master
                self.canal_ambiente.set_volume(vol_final)
            except Exception:
                pass

    def get_volume_sfx_efetivo(self, volume_relativo=1.0):
        """Calcula o volume final para um efeito sonoro."""
        return max(0.0, min(1.0, self.volume_sfx * self.volume_master * volume_relativo))

    # =========================================================================
    # MÚSICA DE FUNDO (BGM)
    # =========================================================================

    def tocar_musica(self, nome_ou_caminho, loop=-1, fade_ms=800, salvar_anterior=True):
        """
        Inicia a reprodução de uma música de fundo com transição suave.
        Se a música já for a mesma atualmente em execução, não reinicia.
        """
        if not pygame.mixer.get_init():
            return

        caminho_arquivo = self._localizar_arquivo_musica(nome_ou_caminho)

        # Evita reiniciar caso já esteja tocando a mesma faixa
        if self.musica_atual == caminho_arquivo and pygame.mixer.music.get_busy() and not self.musica_pausada:
            return

        if salvar_anterior and self.musica_atual and self.musica_atual != caminho_arquivo:
            self.musica_anterior = self.musica_atual

        if caminho_arquivo and os.path.isfile(caminho_arquivo):
            try:
                if fade_ms > 0 and pygame.mixer.music.get_busy():
                    pygame.mixer.music.fadeout(fade_ms)
                
                pygame.mixer.music.load(caminho_arquivo)
                self._aplicar_volume_musica()
                pygame.mixer.music.play(loops=loop, fade_ms=fade_ms if fade_ms > 0 else 0)
                self.musica_atual = caminho_arquivo
                self.musica_pausada = False
            except Exception as e:
                logger.warning("Falha ao tocar música '%s': %s", caminho_arquivo, e)
        else:
            if nome_ou_caminho not in self._avisos_arquivo_ausente:
                self._avisos_arquivo_ausente.add(nome_ou_caminho)
                logger.info("Arquivo de música '%s' não encontrado. Aguardando inserção em assets/audio/music.", nome_ou_caminho)

    def parar_musica(self, fade_ms=600):
        """Interrompe a música de fundo com fadeout."""
        if not pygame.mixer.get_init():
            return
        try:
            if fade_ms > 0:
                pygame.mixer.music.fadeout(fade_ms)
            else:
                pygame.mixer.music.stop()
            self.musica_atual = None
            self.musica_pausada = False
        except Exception:
            pass

    def pausar_musica(self):
        """Pausa a música de fundo."""
        if pygame.mixer.get_init() and pygame.mixer.music.get_busy() and not self.musica_pausada:
            try:
                pygame.mixer.music.pause()
                self.musica_pausada = True
            except Exception:
                pass

    def despausar_musica(self):
        """Retoma a música de fundo pausada."""
        if pygame.mixer.get_init() and self.musica_pausada:
            try:
                pygame.mixer.music.unpause()
                self.musica_pausada = False
            except Exception:
                pass

    def restaurar_musica_anterior(self, fade_ms=800):
        """Restaura a música que tocava antes da faixa atual (útil ao sair de combate)."""
        if self.musica_anterior:
            ant = self.musica_anterior
            self.musica_anterior = None
            self.tocar_musica(ant, loop=-1, fade_ms=fade_ms, salvar_anterior=False)

    # =========================================================================
    # SOM AMBIENTE (BGS)
    # =========================================================================

    def tocar_ambiente(self, nome_ou_caminho, loop=-1, fade_ms=600):
        """Toca um efeito de ambiente contínuo (ex: chuva, vento, lareira) no canal reservado."""
        if not pygame.mixer.get_init() or not self.canal_ambiente:
            return

        caminho_arquivo = self._localizar_arquivo_ambiente(nome_ou_caminho)
        if self.ambiente_atual == caminho_arquivo and self.canal_ambiente.get_busy():
            return

        som = self._carregar_som(caminho_arquivo, fallback_procedural="ambiente_suave")
        if som:
            try:
                if fade_ms > 0:
                    self.canal_ambiente.fadeout(fade_ms)
                self.canal_ambiente.set_volume(self.volume_ambiente * self.volume_master)
                self.canal_ambiente.play(som, loops=loop, fade_ms=fade_ms)
                self.ambiente_atual = caminho_arquivo
            except Exception as e:
                logger.warning("Falha ao tocar som ambiente '%s': %s", nome_ou_caminho, e)

    def parar_ambiente(self, fade_ms=600):
        """Cessa o som de ambiente."""
        if self.canal_ambiente and self.canal_ambiente.get_busy():
            try:
                if fade_ms > 0:
                    self.canal_ambiente.fadeout(fade_ms)
                else:
                    self.canal_ambiente.stop()
            except Exception:
                pass
            self.ambiente_atual = None

    # =========================================================================
    # EFEITOS SONOROS (SFX)
    # =========================================================================

    def tocar_sfx(self, alias_ou_caminho, volume_extra=1.0):
        """
        Dispara um efeito sonoro instantâneo.
        Se o arquivo físico não for encontrado, sintetiza um tom procedural suave
        para resposta tátil imediata do jogo.
        """
        if not pygame.mixer.get_init():
            return None

        som = self._carregar_sfx_com_fallback(alias_ou_caminho)
        if som:
            try:
                vol_final = self.get_volume_sfx_efetivo(volume_extra)
                som.set_volume(vol_final)
                canal = som.play()
                return canal
            except Exception as e:
                logger.debug("Falha ao reproduzir SFX '%s': %s", alias_ou_caminho, e)
        return None

    def _carregar_sfx_com_fallback(self, alias_ou_caminho):
        """Obtém o Sound do cache, carrega do disco ou gera proceduralmente."""
        chave = str(alias_ou_caminho).lower().strip()
        if chave in self._cache_sfx:
            return self._cache_sfx[chave]

        caminho_arquivo = self._localizar_arquivo_sfx(alias_ou_caminho)
        if caminho_arquivo and os.path.isfile(caminho_arquivo):
            try:
                som = pygame.mixer.Sound(caminho_arquivo)
                self._cache_sfx[chave] = som
                return som
            except Exception as e:
                logger.warning("Erro ao carregar arquivo de som '%s': %s", caminho_arquivo, e)

        # Fallback Procedural: sintetiza som matemático equivalente
        som_proc = self._gerar_sfx_procedural(chave)
        self._cache_sfx[chave] = som_proc
        return som_proc

    def _carregar_som(self, caminho_arquivo, fallback_procedural=None):
        """Carrega um arquivo de Sound genérico."""
        if caminho_arquivo and os.path.isfile(caminho_arquivo):
            try:
                return pygame.mixer.Sound(caminho_arquivo)
            except Exception:
                pass
        if fallback_procedural:
            return self._gerar_sfx_procedural(fallback_procedural)
        return None

    # =========================================================================
    # RESOLUÇÃO DE CAMINHOS & ALIASES
    # =========================================================================

    def _localizar_arquivo_musica(self, nome_ou_caminho):
        """Resolve o caminho de arquivo para uma música."""
        if not nome_ou_caminho:
            return None
        if os.path.isfile(str(nome_ou_caminho)):
            return str(nome_ou_caminho)

        candidatos = [
            str(nome_ou_caminho),
            f"{nome_ou_caminho}.ogg",
            f"{nome_ou_caminho}.mp3",
            f"{nome_ou_caminho}.wav",
        ]
        for c in candidatos:
            caminho_completo = os.path.join(PASTA_MUSICA, c)
            if os.path.isfile(caminho_completo):
                return caminho_completo
        return None

    def _localizar_arquivo_ambiente(self, nome_ou_caminho):
        """Resolve o caminho de arquivo para um som de ambiente."""
        if not nome_ou_caminho:
            return None
        if os.path.isfile(str(nome_ou_caminho)):
            return str(nome_ou_caminho)

        candidatos = [
            str(nome_ou_caminho),
            f"{nome_ou_caminho}.ogg",
            f"{nome_ou_caminho}.mp3",
            f"{nome_ou_caminho}.wav",
        ]
        for c in candidatos:
            caminho_completo = os.path.join(PASTA_AMBIENTE, c)
            if os.path.isfile(caminho_completo):
                return caminho_completo
        return None

    def _localizar_arquivo_sfx(self, alias_ou_caminho):
        """
        Pesquisa o arquivo de SFX em pastas comuns:
        assets/audio/sfx/, assets/audio/sfx/ui/, assets/audio/sfx/combate/, assets/audio/sfx/mundo/
        """
        if not alias_ou_caminho:
            return None
        if os.path.isfile(str(alias_ou_caminho)):
            return str(alias_ou_caminho)

        pastas_busca = [
            PASTA_SFX,
            os.path.join(PASTA_SFX, "ui"),
            os.path.join(PASTA_SFX, "combate"),
            os.path.join(PASTA_SFX, "mundo"),
        ]

        nomes = [
            str(alias_ou_caminho),
            f"{alias_ou_caminho}.wav",
            f"{alias_ou_caminho}.ogg",
            f"{alias_ou_caminho}.mp3",
        ]

        for pasta in pastas_busca:
            for nome in nomes:
                caminho = os.path.join(pasta, nome)
                if os.path.isfile(caminho):
                    return caminho

        return None

    # =========================================================================
    # SINTETIZADOR PROCEDURAL (FALLBACK ACÚSTICO IMEDIATO)
    # =========================================================================

    def _gerar_sfx_procedural(self, tipo):
        """
        Gera amostras de áudio PCM sintéticas 16-bit estéreo puras,
        permitindo feedback acústico imediato sem dependências externas.
        """
        if tipo in self._cache_procedural:
            return self._cache_procedural[tipo]

        sample_rate = 44100
        buffer_bytes = bytearray()

        def add_tone(freq, duracao, volume=0.3, envelope="decay"):
            num_samples = int(sample_rate * duracao)
            for i in range(num_samples):
                t = i / sample_rate
                # Envelope de amplitude
                if envelope == "decay":
                    env = max(0.0, 1.0 - (i / num_samples))
                elif envelope == "pluck":
                    env = max(0.0, (1.0 - (i / num_samples)) ** 2)
                elif envelope == "bell":
                    env = math.sin(math.pi * (i / num_samples))
                else:
                    env = 1.0

                onda = math.sin(2.0 * math.pi * freq * t)
                val = int(onda * 32767 * volume * env)
                val = max(-32767, min(32767, val))
                buffer_bytes.extend(struct.pack('<hh', val, val))

        def add_noise(duracao, volume=0.25):
            import random
            num_samples = int(sample_rate * duracao)
            for i in range(num_samples):
                env = (1.0 - (i / num_samples)) ** 1.5
                val = int((random.random() * 2.0 - 1.0) * 32767 * volume * env)
                val = max(-32767, min(32767, val))
                buffer_bytes.extend(struct.pack('<hh', val, val))

        tipo_lower = str(tipo).lower()

        # UI: Hover / Cursor
        if "cursor" in tipo_lower or "hover" in tipo_lower:
            add_tone(580, 0.035, volume=0.15, envelope="pluck")

        # UI: Confirmar / Selecionar
        elif "confirmar" in tipo_lower or "select" in tipo_lower or "confirm" in tipo_lower:
            add_tone(440, 0.04, volume=0.25, envelope="pluck")
            add_tone(880, 0.06, volume=0.25, envelope="decay")

        # UI: Voltar / Cancelar
        elif "voltar" in tipo_lower or "cancel" in tipo_lower or "back" in tipo_lower:
            add_tone(520, 0.04, volume=0.25, envelope="pluck")
            add_tone(320, 0.07, volume=0.25, envelope="decay")

        # UI: Erro / Bloqueio
        elif "erro" in tipo_lower or "error" in tipo_lower or "invalid" in tipo_lower:
            add_tone(180, 0.08, volume=0.35, envelope="decay")
            add_tone(140, 0.08, volume=0.35, envelope="decay")

        # UI: Diálogo / Texto
        elif "dialogo" in tipo_lower or "fala" in tipo_lower or "type" in tipo_lower:
            add_tone(720, 0.018, volume=0.08, envelope="pluck")

        # Combate: Acerto de Ataque
        elif "acerto" in tipo_lower or "hit" in tipo_lower:
            add_noise(0.04, volume=0.3)
            add_tone(220, 0.08, volume=0.35, envelope="pluck")

        # Combate: Crítico
        elif "critico" in tipo_lower or "crit" in tipo_lower:
            add_noise(0.05, volume=0.4)
            add_tone(330, 0.06, volume=0.4, envelope="pluck")
            add_tone(660, 0.12, volume=0.45, envelope="decay")

        # Combate: Erro (Woosh)
        elif "erro_ataque" in tipo_lower or "ataque_erro" in tipo_lower or "miss" in tipo_lower:
            add_tone(280, 0.04, volume=0.18, envelope="pluck")
            add_tone(180, 0.06, volume=0.12, envelope="decay")

        # Combate: Esquiva
        elif "esquiva" in tipo_lower or "dodge" in tipo_lower:
            add_tone(400, 0.03, volume=0.2, envelope="pluck")
            add_tone(700, 0.05, volume=0.25, envelope="decay")

        # Combate: Dano em Halia
        elif "dano_halia" in tipo_lower or "player_hit" in tipo_lower:
            add_noise(0.06, volume=0.4)
            add_tone(160, 0.12, volume=0.4, envelope="decay")

        # Combate: Dano no Inimigo
        elif "dano_inimigo" in tipo_lower or "enemy_hit" in tipo_lower:
            add_noise(0.05, volume=0.35)
            add_tone(240, 0.09, volume=0.3, envelope="pluck")

        # Combate: Magia / Feitiço
        elif "magia" in tipo_lower or "spell" in tipo_lower or "cast" in tipo_lower:
            add_tone(392, 0.05, volume=0.25, envelope="bell")
            add_tone(587, 0.06, volume=0.3, envelope="bell")
            add_tone(784, 0.10, volume=0.35, envelope="decay")

        # Combate: Concentrar / Guarda
        elif "concentrar" in tipo_lower or "foco" in tipo_lower or "defesa" in tipo_lower:
            add_tone(330, 0.08, volume=0.2, envelope="bell")
            add_tone(495, 0.14, volume=0.25, envelope="decay")

        # Combate: Poção / Consumível
        elif "pocao" in tipo_lower or "item" in tipo_lower or "potion" in tipo_lower:
            add_tone(523, 0.04, volume=0.25, envelope="pluck")
            add_tone(659, 0.04, volume=0.25, envelope="pluck")
            add_tone(784, 0.08, volume=0.3, envelope="decay")

        # Combate: Fuga
        elif "fuga" in tipo_lower or "run" in tipo_lower:
            add_tone(350, 0.03, volume=0.2, envelope="pluck")
            add_tone(290, 0.04, volume=0.2, envelope="pluck")
            add_tone(240, 0.06, volume=0.2, envelope="decay")

        # Mundo: Porta
        elif "porta" in tipo_lower or "door" in tipo_lower:
            add_noise(0.03, volume=0.2)
            add_tone(140, 0.08, volume=0.3, envelope="decay")

        # Padrão Genérico
        else:
            add_tone(440, 0.05, volume=0.2, envelope="decay")

        try:
            snd = pygame.mixer.Sound(buffer=bytes(buffer_bytes))
            self._cache_procedural[tipo] = snd
            return snd
        except Exception as e:
            logger.debug("Falha ao criar Sound procedural: %s", e)
            return None
