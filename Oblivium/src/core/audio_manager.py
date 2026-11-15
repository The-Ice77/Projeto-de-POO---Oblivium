# src/core/audio_manager.py
import json
import os
import logging
import random
import re
import time
import pygame

logger = logging.getLogger(__name__)

# Diretórios base de assets de áudio e dados
_DIRETORIO_ATUAL = os.path.dirname(os.path.abspath(__file__))
_DIRETORIO_SRC = os.path.dirname(_DIRETORIO_ATUAL)
_DIRETORIO_RAIZ = os.path.dirname(_DIRETORIO_SRC)
PASTA_AUDIO = os.path.join(_DIRETORIO_RAIZ, "assets", "audio")
PASTA_MUSICA = os.path.join(PASTA_AUDIO, "music")
PASTA_AMBIENTE = os.path.join(PASTA_AUDIO, "ambience")
PASTA_SFX = os.path.join(PASTA_AUDIO, "sfx")
CAMINHO_MANIFESTO_AUDIO = os.path.join(_DIRETORIO_SRC, "data", "audio_manifest.json")


class AudioManager:
    """
    Gerenciador Central de Áudio e Música de Oblivium.
    
    Recursos principais:
    - Mixagem multicanal dedicada: BGM (pygame.mixer.music), BGS/Ambience (canal reservado) e SFX dinâmico.
    - Controle hierárquico de volume (Master, Música, Ambiente, SFX).
    - Resolução automática de arquivos de áudio (.ogg, .wav, .mp3) e subpastas de categorias.
    - Carregamento tolerante e limpo: silêncio automático caso o arquivo ainda não exista no disco,
      sem bipes sintéticos artificiais e pronto para receber os assets definitivos.
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
        self.mutado = False

        # Manifesto, estado atual de reprodução e fade sequencial não bloqueante
        self.manifesto = {}
        self.faixas_musica = {}
        self.aliases_musica = {}
        self.aliases_sfx = {}
        self.aliases_ambiente = {}
        self.grupos_sfx = {}
        self._carregar_manifesto()

        self.musica_atual = None
        self.musica_anterior = None
        self.ambiente_atual = None
        self._ambiente_chave_atual = None
        self.musica_pausada = False
        self.contexto_musica = "nenhum"
        self.geracao_contexto = 0
        self._token_combate = None
        self._musica_stream_carregada = None
        self._fator_fade_musica = 1.0
        self._transicao_musica = None
        self._fanfarra_tempo_s = 0.0

        # Cache de efeitos sonoros carregados fisicamente e estado de variações/passos
        self._cache_sfx = {}
        self._cache_sfx_variantes = {}
        self._ultimo_sfx_indice = {}
        self._ultimo_disparo_sfx = {}
        self._passo_timer_s = 0.0
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
    def _normalizar_volume(valor, escala="auto"):
        """Converte valor percentual (0..100 int) ou unitário (0.0..1.0 float) para [0.0, 1.0]."""
        if isinstance(valor, bool):
            return 1.0 if valor else 0.0
        try:
            val = float(valor)
        except (ValueError, TypeError):
            return 1.0

        modo = str(escala or "auto").lower().strip()
        if modo == "percentual":
            val = val / 100.0
        elif modo == "auto" and (isinstance(valor, int) or val > 1.0):
            val = val / 100.0
        return max(0.0, min(1.0, val))

    def definir_volume_master(self, valor, escala="auto"):
        """Define o volume geral (Master)."""
        self.volume_master = self._normalizar_volume(valor, escala=escala)
        self._aplicar_volumes()

    def definir_volume_musica(self, valor, escala="auto"):
        """Define o volume da música de fundo (BGM)."""
        self.volume_musica = self._normalizar_volume(valor, escala=escala)
        self._aplicar_volume_musica()

    def definir_volume_sfx(self, valor, escala="auto"):
        """Define o volume dos efeitos sonoros (SFX)."""
        self.volume_sfx = self._normalizar_volume(valor, escala=escala)

    def definir_volume_ambiente(self, valor, escala="auto"):
        """Define o volume do som de ambiente contínuo (BGS)."""
        self.volume_ambiente = self._normalizar_volume(valor, escala=escala)
        self._aplicar_volume_ambiente()

    def definir_mute(self, mutado):
        """Ativa ou desativa o silenciamento global sem perder os volumes configurados."""
        self.mutado = bool(mutado)
        self._aplicar_volumes()

    def alternar_mute(self):
        """Alterna o estado global de mute e retorna o novo estado."""
        self.definir_mute(not self.mutado)
        return self.mutado

    def obter_volume_musica_efetivo(self):
        """Retorna o volume linear efetivo aplicado ao stream musical atual."""
        if self.mutado:
            return 0.0
        return max(0.0, min(1.0, self.volume_musica * self.volume_master * self._fator_fade_musica))

    def _aplicar_volumes(self):
        self._aplicar_volume_musica()
        self._aplicar_volume_ambiente()

    def _aplicar_volume_musica(self):
        try:
            pygame.mixer.music.set_volume(self.obter_volume_musica_efetivo())
        except Exception:
            pass

    def _aplicar_volume_ambiente(self):
        if self.canal_ambiente:
            try:
                vol_final = 0.0 if self.mutado else (self.volume_ambiente * self.volume_master)
                self.canal_ambiente.set_volume(max(0.0, min(1.0, vol_final)))
            except Exception:
                pass

    def get_volume_sfx_efetivo(self, volume_relativo=1.0):
        """Calcula o volume final para um efeito sonoro."""
        if self.mutado:
            return 0.0
        return max(0.0, min(1.0, self.volume_sfx * self.volume_master * volume_relativo))

    # =========================================================================
    # MÚSICA DE FUNDO (BGM)
    # =========================================================================

    def _carregar_manifesto(self):
        """Carrega o catálogo e aliases oficiais de áudio de `src/data/audio_manifest.json`."""
        if not os.path.isfile(CAMINHO_MANIFESTO_AUDIO):
            return
        try:
            with open(CAMINHO_MANIFESTO_AUDIO, "r", encoding="utf-8") as f:
                dados = json.load(f)
            if isinstance(dados, dict):
                self.manifesto = dados
                self.faixas_musica = dict(dados.get("faixas_musica") or {})
                self.aliases_musica = {
                    str(k).lower().strip(): str(v)
                    for k, v in (dados.get("aliases_musica") or {}).items()
                }
                self.aliases_sfx = {
                    str(k).lower().strip(): str(v)
                    for k, v in (dados.get("aliases_sfx") or {}).items()
                }
                self.aliases_ambiente = {
                    str(k).lower().strip(): str(v)
                    for k, v in (dados.get("aliases_ambiente") or {}).items()
                }
                self.grupos_sfx = {
                    str(k).lower().strip(): list(v)
                    for k, v in (dados.get("grupos_sfx") or {}).items()
                    if isinstance(v, list)
                }
        except Exception as e:
            logger.warning("Falha ao carregar manifesto de áudio: %s", e)

    @staticmethod
    def _normalizar_caminho(caminho):
        if not caminho:
            return None
        return os.path.normcase(os.path.abspath(str(caminho)))

    @classmethod
    def _mesmo_caminho(cls, a, b):
        if not a or not b:
            return False
        return cls._normalizar_caminho(a) == cls._normalizar_caminho(b)

    @staticmethod
    def _inferir_contexto(nome_ou_caminho):
        chave = os.path.splitext(os.path.basename(str(nome_ou_caminho or "").lower()))[0]
        if "combate" in chave:
            return "combate"
        if chave in ("vitoria", "derrota"):
            return "resultado_combate"
        if chave == "menu_tema":
            return "menu"
        if chave in ("cutscene_intro", "tema_intro"):
            return "intro"
        if chave in ("cutscene_magia", "tema_memorias", "cutscene_final", "creditos_demo", "tema_encerramento"):
            return "cutscene"
        return "mundo"

    def validar_manifesto_musica(self):
        """Valida se todas as faixas e aliases do manifesto apontam para arquivos existentes."""
        erros = []
        if not self.faixas_musica:
            erros.append("Manifesto de áudio sem faixas_musica.")
        for chave, meta in self.faixas_musica.items():
            arq = meta.get("arquivo") if isinstance(meta, dict) else None
            caminho = self._localizar_arquivo_musica(arq or chave)
            if not caminho or not os.path.isfile(caminho):
                erros.append(f"Faixa '{chave}' ausente em disco ({arq}).")
        for alias in self.aliases_musica:
            caminho = self.resolver_caminho_musica(alias)
            if not caminho or not os.path.isfile(caminho):
                erros.append(f"Alias '{alias}' sem destino válido.")
        return (len(erros) == 0, erros)

    def resolver_caminho_musica(self, nome_ou_caminho):
        """Interface pública para resolver um alias ou caminho até o OGG físico."""
        return self._localizar_arquivo_musica(nome_ou_caminho)

    def limpar_contexto_combate(self):
        """Invalida restaurações pendentes de trilha pré-combate (ex: ida ao menu ou cutscene)."""
        self.musica_anterior = None
        self._token_combate = None
        self.geracao_contexto += 1

    @staticmethod
    def _eh_fanfarra_vitoria(caminho):
        return os.path.basename(str(caminho or "")).lower() == "vitoria.ogg"

    def _carregar_e_iniciar_stream(self, caminho_arquivo, loop=-1):
        pygame.mixer.music.load(caminho_arquivo)
        self._musica_stream_carregada = caminho_arquivo
        if self._eh_fanfarra_vitoria(caminho_arquivo):
            self._fanfarra_tempo_s = 0.0
        self._aplicar_volume_musica()
        pygame.mixer.music.play(loops=loop)

    def tocar_musica(self, nome_ou_caminho, loop=-1, fade_ms=800, salvar_anterior=True, contexto=None, forcar_reinicio=False):
        """
        Toca uma faixa musical usando o mixer streaming (`pygame.mixer.music`) sem bloquear o loop.
        Mantém continuidade entre aliases equivalentes que apontem para o mesmo OGG.
        """
        if not pygame.mixer.get_init():
            return

        caminho_arquivo = self._localizar_arquivo_musica(nome_ou_caminho)
        if not (caminho_arquivo and os.path.isfile(caminho_arquivo)):
            if nome_ou_caminho not in self._avisos_arquivo_ausente:
                self._avisos_arquivo_ausente.add(nome_ou_caminho)
                logger.info(
                    "Arquivo de música '%s' não encontrado. Aguardando inserção em assets/audio/music.",
                    nome_ou_caminho,
                )
            return

        ctx = contexto or self._inferir_contexto(nome_ou_caminho)
        em_transicao = self._transicao_musica is not None
        trans_destino = self._transicao_musica.get("destino") if em_transicao else None
        trans_proximo = (self._transicao_musica.get("proximo") or {}).get("destino") if em_transicao else None

        # Continuidade: mesma faixa física já em execução ou agendada nesta transição
        if (
            not forcar_reinicio
            and not self.musica_pausada
            and self._mesmo_caminho(self.musica_atual, caminho_arquivo)
            and (
                (
                    em_transicao
                    and (
                        self._mesmo_caminho(trans_destino, caminho_arquivo)
                        or self._mesmo_caminho(trans_proximo, caminho_arquivo)
                    )
                )
                or pygame.mixer.music.get_busy()
            )
        ):
            if ctx != self.contexto_musica:
                self.contexto_musica = ctx
                if ctx not in ("combate", "resultado_combate"):
                    self.musica_anterior = None
                    self._token_combate = None
                    self.geracao_contexto += 1
            return

        fade_total_ms = max(0, int(fade_ms or 0))
        fanfarra_pendente = (
            em_transicao
            and self._eh_fanfarra_vitoria(trans_destino)
        )
        fanfarra_recem_iniciada = (
            self._eh_fanfarra_vitoria(self._musica_stream_carregada)
            and pygame.mixer.music.get_busy()
            and self._fanfarra_tempo_s < 0.90
            and (
                self.contexto_musica == "resultado_combate"
                or (em_transicao and self._transicao_musica.get("estado") in ("ENTRANDO", "FANFARRA"))
            )
        )
        if not forcar_reinicio and ctx == "mundo" and not self.musica_pausada and (fanfarra_pendente or fanfarra_recem_iniciada):
            # Preserva a fanfarra de vitória em confirmações rápidas e agenda a trilha do mapa em sequência.
            self.musica_atual = caminho_arquivo
            self.contexto_musica = ctx
            self.musica_anterior = None
            self._token_combate = None
            self.geracao_contexto += 1
            proximo = {
                "destino": caminho_arquivo,
                "loop": loop,
                "fade_out_s": max(0.05, (fade_total_ms * 0.45) / 1000.0) if fade_total_ms > 0 else 0.12,
                "fade_in_s": max(0.05, (fade_total_ms * 0.55) / 1000.0) if fade_total_ms > 0 else 0.15,
            }
            if em_transicao:
                self._transicao_musica["proximo"] = proximo
            else:
                self._transicao_musica = {
                    "estado": "FANFARRA",
                    "destino": self._musica_stream_carregada,
                    "loop": 0,
                    "tempo": self._fanfarra_tempo_s,
                    "fanfarra_min_s": 0.90,
                    "proximo": proximo,
                }
            return

        if ctx in ("menu", "intro", "cutscene") or not salvar_anterior:
            if ctx not in ("combate", "resultado_combate"):
                self.musica_anterior = None
                self._token_combate = None
        elif salvar_anterior and self.musica_atual and not self._mesmo_caminho(self.musica_atual, caminho_arquivo):
            if self.contexto_musica not in ("combate", "resultado_combate"):
                self.musica_anterior = self.musica_atual

        self.geracao_contexto += 1
        if ctx == "combate":
            self._token_combate = self.geracao_contexto
        elif ctx != "resultado_combate":
            self._token_combate = None

        self.musica_atual = caminho_arquivo
        self.contexto_musica = ctx
        self.musica_pausada = False

        try:
            stream_ocupado = bool(pygame.mixer.music.get_busy() and self._musica_stream_carregada is not None)

            if not forcar_reinicio and stream_ocupado and self._mesmo_caminho(self._musica_stream_carregada, caminho_arquivo):
                if fade_total_ms > 0:
                    self._transicao_musica = {
                        "estado": "ENTRANDO",
                        "destino": caminho_arquivo,
                        "loop": loop,
                        "tempo": 0.0,
                        "fade_in_s": max(0.05, fade_total_ms / 1000.0),
                        "vol_inicio": self._fator_fade_musica,
                    }
                else:
                    self._fator_fade_musica = 1.0
                    self._transicao_musica = None
                    self._aplicar_volume_musica()
                return

            if fade_total_ms > 0 and stream_ocupado:
                # Sequencial não bloqueante: atenua atual -> troca o stream no update(dt) -> sobe nova faixa
                eh_fanf_res = ctx == "resultado_combate" and self._eh_fanfarra_vitoria(caminho_arquivo)
                fade_out_s = min(0.06, max(0.03, (fade_total_ms * 0.45) / 1000.0)) if eh_fanf_res else max(0.05, (fade_total_ms * 0.45) / 1000.0)
                fade_in_s = min(0.06, max(0.03, (fade_total_ms * 0.55) / 1000.0)) if eh_fanf_res else max(0.05, (fade_total_ms * 0.55) / 1000.0)
                self._transicao_musica = {
                    "estado": "SAINDO",
                    "destino": caminho_arquivo,
                    "loop": loop,
                    "tempo": 0.0,
                    "fade_out_s": fade_out_s,
                    "fade_in_s": fade_in_s,
                    "vol_inicio": max(0.0, min(1.0, self._fator_fade_musica)),
                }
            elif fade_total_ms > 0:
                self._fator_fade_musica = 0.0
                self._carregar_e_iniciar_stream(caminho_arquivo, loop=loop)
                self._transicao_musica = {
                    "estado": "ENTRANDO",
                    "destino": caminho_arquivo,
                    "loop": loop,
                    "tempo": 0.0,
                    "fade_in_s": max(0.05, fade_total_ms / 1000.0),
                    "vol_inicio": 0.0,
                }
            else:
                self._fator_fade_musica = 1.0
                self._transicao_musica = None
                self._carregar_e_iniciar_stream(caminho_arquivo, loop=loop)
        except Exception as e:
            logger.warning("Falha ao tocar música '%s': %s", caminho_arquivo, e)

    def parar_musica(self, fade_ms=600):
        """Interrompe a música de fundo com fadeout não bloqueante ou parada imediata."""
        if not pygame.mixer.get_init():
            return
        try:
            fade_total_ms = max(0, int(fade_ms or 0))
            self.musica_atual = None
            self.musica_pausada = False
            self.limpar_contexto_combate()
            if fade_total_ms > 0 and pygame.mixer.music.get_busy() and self._musica_stream_carregada is not None:
                self._transicao_musica = {
                    "estado": "SAINDO",
                    "destino": None,
                    "loop": 0,
                    "tempo": 0.0,
                    "fade_out_s": max(0.05, fade_total_ms / 1000.0),
                    "fade_in_s": 0.0,
                    "vol_inicio": max(0.0, min(1.0, self._fator_fade_musica)),
                }
            else:
                self._transicao_musica = None
                self._fator_fade_musica = 1.0
                self._musica_stream_carregada = None
                pygame.mixer.music.stop()
        except Exception:
            pass

    def update(self, dt=None):
        """Avança a máquina de fade musical (SAINDO -> troca -> ENTRANDO -> OCIOSO) sem bloquear."""
        if self.musica_pausada:
            return
        if dt is None:
            dt = getattr(self.game, "dt", 1.0 / 60.0) if self.game else (1.0 / 60.0)
        try:
            dt_seg = max(0.0, float(dt))
        except (TypeError, ValueError):
            dt_seg = 1.0 / 60.0

        if self._eh_fanfarra_vitoria(self._musica_stream_carregada) and pygame.mixer.music.get_busy():
            self._fanfarra_tempo_s += dt_seg

        if not self._transicao_musica:
            return

        trans = self._transicao_musica
        trans["tempo"] += dt_seg
        estado = trans["estado"]

        if estado == "SAINDO":
            dur = max(0.01, trans["fade_out_s"])
            prog = min(1.0, trans["tempo"] / dur)
            self._fator_fade_musica = max(0.0, trans["vol_inicio"] * (1.0 - prog))
            self._aplicar_volume_musica()
            if prog >= 1.0:
                destino = trans.get("destino")
                try:
                    pygame.mixer.music.stop()
                except Exception:
                    pass
                self._musica_stream_carregada = None
                if destino and os.path.isfile(destino):
                    try:
                        self._fator_fade_musica = 0.0
                        self._carregar_e_iniciar_stream(destino, loop=trans.get("loop", -1))
                        trans["estado"] = "ENTRANDO"
                        trans["tempo"] = 0.0
                        trans["vol_inicio"] = 0.0
                    except Exception as e:
                        logger.warning("Falha ao trocar música em fade '%s': %s", destino, e)
                        self._transicao_musica = None
                else:
                    self._fator_fade_musica = 1.0
                    self._transicao_musica = None
        elif estado == "ENTRANDO":
            dur = max(0.01, trans["fade_in_s"])
            prog = min(1.0, trans["tempo"] / dur)
            v0 = trans.get("vol_inicio", 0.0)
            self._fator_fade_musica = min(1.0, v0 + (1.0 - v0) * prog)
            self._aplicar_volume_musica()
            if prog >= 1.0:
                self._fator_fade_musica = 1.0
                self._aplicar_volume_musica()
                proximo = trans.get("proximo")
                if proximo:
                    self._transicao_musica = {
                        "estado": "FANFARRA",
                        "destino": self._musica_stream_carregada,
                        "loop": 0,
                        "tempo": self._fanfarra_tempo_s,
                        "fanfarra_min_s": 0.90,
                        "proximo": proximo,
                    }
                else:
                    self._transicao_musica = None
        elif estado == "FANFARRA":
            proximo = trans.get("proximo")
            if not proximo:
                self._transicao_musica = None
                return
            stream_parou = not pygame.mixer.music.get_busy()
            if stream_parou or self._fanfarra_tempo_s >= trans.get("fanfarra_min_s", 0.90):
                self._transicao_musica = {
                    "estado": "SAINDO",
                    "destino": proximo["destino"],
                    "loop": proximo.get("loop", -1),
                    "tempo": 0.0,
                    "fade_out_s": 0.01 if stream_parou else max(0.05, proximo.get("fade_out_s", 0.2)),
                    "fade_in_s": max(0.05, proximo.get("fade_in_s", 0.25)),
                    "vol_inicio": 0.0 if stream_parou else max(0.0, min(1.0, self._fator_fade_musica)),
                }

    def atualizar(self, dt=None):
        """Alias em português para `update(dt)`."""
        self.update(dt)

    def pausar_musica(self):
        """Pausa a música de fundo."""
        if pygame.mixer.get_init() and (pygame.mixer.music.get_busy() or self._transicao_musica is not None) and not self.musica_pausada:
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

    def restaurar_musica_anterior(self, fade_ms=800, token_esperado=None):
        """Restaura a trilha pré-combate somente se nenhum contexto posterior assumiu a música."""
        if token_esperado is not None and self._token_combate != token_esperado:
            return False
        if self.contexto_musica not in ("combate", "resultado_combate"):
            return False
        if self.musica_anterior:
            ant = self.musica_anterior
            self.musica_anterior = None
            self._token_combate = None
            self.tocar_musica(ant, loop=-1, fade_ms=fade_ms, salvar_anterior=False, contexto="mundo")
            return True
        return False

    # =========================================================================
    # SOM AMBIENTE (BGS)
    # =========================================================================

    def tocar_ambiente(self, nome_ou_caminho, loop=-1, fade_ms=600):
        """Toca um efeito de ambiente contínuo (ex: chuva, vento, fogueira, caverna_lava)."""
        if not pygame.mixer.get_init() or not self.canal_ambiente:
            return

        chave_logica = os.path.splitext(str(nome_ou_caminho or "").lower().strip())[0]
        chave_logica = self.aliases_ambiente.get(chave_logica, chave_logica)
        if self._ambiente_chave_atual == chave_logica and self.canal_ambiente.get_busy():
            self._aplicar_volume_ambiente()
            return

        caminho_arquivo = self._localizar_arquivo_ambiente(nome_ou_caminho)
        if not caminho_arquivo:
            return
        if self.ambiente_atual == caminho_arquivo and self.canal_ambiente.get_busy():
            self._ambiente_chave_atual = chave_logica
            self._aplicar_volume_ambiente()
            return

        som = self._carregar_som(caminho_arquivo)
        if som:
            try:
                if fade_ms > 0:
                    self.canal_ambiente.fadeout(fade_ms)
                self._aplicar_volume_ambiente()
                self.canal_ambiente.play(som, loops=loop, fade_ms=fade_ms)
                self._aplicar_volume_ambiente()
                self.ambiente_atual = caminho_arquivo
                self._ambiente_chave_atual = chave_logica
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
            self._ambiente_chave_atual = None

    # =========================================================================
    # EFEITOS SONOROS (SFX)
    # =========================================================================

    def tocar_sfx(self, alias_ou_caminho, volume_extra=1.0):
        """
        Dispara um efeito sonoro instantâneo com suporte automático a variações (_01, _02, _03).
        Caso o arquivo de som ainda não exista na pasta assets, retorna None silenciosamente.
        """
        if not pygame.mixer.get_init():
            return None

        som = self._carregar_sfx(alias_ou_caminho)
        if som:
            try:
                vol_final = self.get_volume_sfx_efetivo(volume_extra)
                som.set_volume(vol_final)
                canal = som.play()
                return canal
            except Exception as e:
                logger.debug("Falha ao reproduzir SFX '%s': %s", alias_ou_caminho, e)
        return None

    def tocar_sfx_com_cooldown(self, alias_ou_caminho, cooldown_s=0.12, volume_extra=1.0):
        """Reproduz SFX respeitando um intervalo mínimo entre disparos do mesmo alias."""
        chave = os.path.splitext(str(alias_ou_caminho or "").lower().strip())[0]
        agora = time.monotonic()
        ultimo = self._ultimo_disparo_sfx.get(chave, 0.0)
        if (agora - ultimo) < max(0.0, float(cooldown_s)):
            return None
        canal = self.tocar_sfx(alias_ou_caminho, volume_extra=volume_extra)
        if canal is not None or pygame.mixer.get_init():
            self._ultimo_disparo_sfx[chave] = agora
        return canal

    def tocar_sfx_elemento(self, elemento, eh_dragao=False, fallback="magia_cast", volume_extra=1.0):
        """Seleciona e toca o efeito sonoro elemental correspondente para magias ou habilidades."""
        el = str(elemento or "").upper().strip()
        mapa_elem = {
            "FOGO": "magia_fogo",
            "BRASA": "magia_fogo",
            "CHAMA": "magia_fogo",
            "SOPRO": "explosao" if eh_dragao else "magia_fogo",
            "GELO": "magia_gelo",
            "CRIO": "magia_gelo",
            "RAIO": "magia_raio",
            "ARCANO": "magia_raio",
            "TROVAO": "magia_raio",
            "RELAMPAGO": "magia_raio",
            "CURA": "magia_cura",
            "LUZ": "magia_cura",
            "VIDA": "magia_cura",
        }
        alias = mapa_elem.get(el, fallback)
        return self.tocar_sfx(alias, volume_extra=volume_extra)

    def atualizar_passos(self, movendo, correndo=False, superficie="grama", dt=None):
        """Sincroniza passos individuais com a cadência e superfície de caminhada/corrida."""
        if not movendo:
            self._passo_timer_s = 0.0
            return None
        if dt is None:
            dt = getattr(self.game, "dt", 1.0 / 60.0) if self.game else (1.0 / 60.0)
        try:
            dt_seg = max(0.0, float(dt))
        except (TypeError, ValueError):
            dt_seg = 1.0 / 60.0

        intervalo = 0.25 if correndo else 0.39
        self._passo_timer_s += dt_seg
        if self._passo_timer_s >= intervalo:
            self._passo_timer_s %= intervalo
            alias = "passo_pedra" if str(superficie).lower() == "pedra" else "passo_grama"
            vol = 0.62 if correndo else 0.48
            return self.tocar_sfx_com_cooldown(alias, cooldown_s=0.14, volume_extra=vol)
        return None

    def atualizar_passos_jogador(self, game, movendo, correndo=False):
        """Calcula a superfície sob Halia e dispara passos sincronizados com a locomoção."""
        if not movendo or not game or not getattr(game, "halia", None):
            return self.atualizar_passos(False)
        halia = game.halia
        mapa = getattr(game, "mapa_casa", None)
        sup = "grama"
        if mapa and hasattr(mapa, "obter_superficie_passo"):
            rect = getattr(halia, "rect", None)
            if rect is not None:
                px, py = rect.centerx, rect.bottom
            else:
                px = float(getattr(halia, "x", 0.0)) + float(getattr(halia, "largura", 36)) * 0.5
                py = float(getattr(halia, "y", 0.0)) + float(getattr(halia, "altura", 36))
            sup = mapa.obter_superficie_passo(px, py)
        return self.atualizar_passos(True, correndo=correndo, superficie=sup, dt=getattr(game, "dt", None))

    def _carregar_sfx(self, alias_ou_caminho):
        """
        Obtém um Sound do cache selecionando aleatoriamente uma das variações do alias
        (evitando repetição imediata da mesma variação consecutiva).
        """
        chave = str(alias_ou_caminho or "").lower().strip()
        variantes = self._cache_sfx_variantes.get(chave)
        if variantes is None:
            variantes = self._resolver_arquivos_sfx(alias_ou_caminho)
            self._cache_sfx_variantes[chave] = variantes
        if not variantes:
            return None

        idx = 0
        if len(variantes) > 1:
            ultimo = self._ultimo_sfx_indice.get(chave)
            candidatos = [i for i in range(len(variantes)) if i != ultimo]
            idx = random.choice(candidatos)
            self._ultimo_sfx_indice[chave] = idx
        caminho_arquivo = variantes[idx]

        chave_arq = self._normalizar_caminho(caminho_arquivo)
        if chave_arq in self._cache_sfx:
            return self._cache_sfx[chave_arq]

        if os.path.isfile(caminho_arquivo):
            try:
                som = pygame.mixer.Sound(caminho_arquivo)
                self._cache_sfx[chave_arq] = som
                return som
            except Exception as e:
                logger.warning("Erro ao carregar arquivo de som '%s': %s", caminho_arquivo, e)

        return None

    def _carregar_som(self, caminho_arquivo):
        """Carrega um arquivo de Sound genérico a partir do caminho físico."""
        if caminho_arquivo and os.path.isfile(caminho_arquivo):
            try:
                return pygame.mixer.Sound(caminho_arquivo)
            except Exception:
                pass
        return None

    # =========================================================================
    # RESOLUÇÃO DE CAMINHOS & ALIASES
    # =========================================================================

    def _localizar_arquivo_musica(self, nome_ou_caminho):
        """Resolve o caminho físico de uma música via manifesto, alias ou nome de arquivo."""
        if not nome_ou_caminho:
            return None
        if os.path.isfile(str(nome_ou_caminho)):
            return str(nome_ou_caminho)

        chave = str(nome_ou_caminho).strip()
        chave_norm = os.path.splitext(chave)[0].lower().strip()

        candidatos = []
        alias_arq = self.aliases_musica.get(chave.lower()) or self.aliases_musica.get(chave_norm)
        if alias_arq:
            candidatos.append(alias_arq)

        meta_faixa = self.faixas_musica.get(chave_norm)
        if isinstance(meta_faixa, dict) and meta_faixa.get("arquivo"):
            candidatos.append(meta_faixa["arquivo"])

        candidatos.extend([
            chave,
            f"{nome_ou_caminho}.ogg",
            f"{nome_ou_caminho}.mp3",
            f"{nome_ou_caminho}.wav",
        ])
        for c in candidatos:
            caminho_completo = os.path.join(PASTA_MUSICA, c)
            if os.path.isfile(caminho_completo):
                return caminho_completo
        return None

    def _localizar_arquivo_ambiente(self, nome_ou_caminho):
        """Resolve o caminho de arquivo para um som de ambiente (com aliases e variações _01.._0N)."""
        if not nome_ou_caminho:
            return None
        if os.path.isfile(str(nome_ou_caminho)):
            return str(nome_ou_caminho)

        chave_raw = str(nome_ou_caminho).strip()
        chave_norm = os.path.splitext(chave_raw.lower())[0]
        chave_alvo = self.aliases_ambiente.get(chave_norm, chave_norm)
        chaves = [chave_raw] if chave_raw.lower() == chave_alvo else [chave_alvo, chave_raw]

        candidatos = []
        for c_nome in chaves:
            candidatos.extend([c_nome, f"{c_nome}.ogg", f"{c_nome}.wav", f"{c_nome}.mp3"])
        for c in candidatos:
            caminho_completo = os.path.join(PASTA_AMBIENTE, c)
            if os.path.isfile(caminho_completo):
                return caminho_completo

        if os.path.isdir(PASTA_AMBIENTE):
            padrao = re.compile(rf"^{re.escape(chave_alvo)}_\d+$", re.IGNORECASE)
            variantes = [
                os.path.join(PASTA_AMBIENTE, arq)
                for arq in sorted(os.listdir(PASTA_AMBIENTE))
                if os.path.splitext(arq)[1].lower() in (".ogg", ".wav", ".mp3")
                and padrao.match(os.path.splitext(arq)[0])
            ]
            if variantes:
                return random.choice(variantes)
        return None

    def _resolver_arquivos_sfx(self, alias_ou_caminho):
        """Lista todos os caminhos de arquivo correspondentes a um alias SFX (incluindo variações)."""
        if not alias_ou_caminho:
            return []
        if os.path.isfile(str(alias_ou_caminho)):
            return [str(alias_ou_caminho)]

        pastas_busca = [
            PASTA_SFX,
            os.path.join(PASTA_SFX, "ui"),
            os.path.join(PASTA_SFX, "combate"),
            os.path.join(PASTA_SFX, "mundo"),
            os.path.join(PASTA_SFX, "itens"),
        ]

        chave_norm = os.path.splitext(str(alias_ou_caminho).lower().strip())[0]
        alvo_alias = self.aliases_sfx.get(chave_norm)
        chaves_busca = [chave_norm]
        if alvo_alias and alvo_alias not in chaves_busca:
            chaves_busca.insert(0, str(alvo_alias).lower().strip())

        grupo_explicitos = self.grupos_sfx.get(chave_norm) or (
            self.grupos_sfx.get(str(alvo_alias).lower().strip()) if alvo_alias else None
        )
        encontrados = []
        vistos = set()

        def _adicionar(caminho):
            if os.path.isfile(caminho):
                norm = self._normalizar_caminho(caminho)
                if norm not in vistos:
                    vistos.add(norm)
                    encontrados.append(caminho)

        if grupo_explicitos:
            for item in grupo_explicitos:
                for pasta in pastas_busca:
                    _adicionar(os.path.join(pasta, item))
                    for ext in (".ogg", ".wav", ".mp3"):
                        _adicionar(os.path.join(pasta, f"{item}{ext}"))

        for chave in chaves_busca:
            for pasta in pastas_busca:
                if not os.path.isdir(pasta):
                    continue
                for nome in (chave, f"{chave}.ogg", f"{chave}.wav", f"{chave}.mp3"):
                    _adicionar(os.path.join(pasta, nome))
                padrao = re.compile(rf"^{re.escape(chave)}_\d+$", re.IGNORECASE)
                for arq in sorted(os.listdir(pasta)):
                    stem, ext = os.path.splitext(arq)
                    if ext.lower() in (".ogg", ".wav", ".mp3") and padrao.match(stem):
                        _adicionar(os.path.join(pasta, arq))

        return encontrados

    def _localizar_arquivo_sfx(self, alias_ou_caminho):
        """
        Pesquisa o arquivo principal de SFX nas pastas organizadas:
        assets/audio/sfx/, ui/, combate/, mundo/, itens/
        """
        arquivos = self._resolver_arquivos_sfx(alias_ou_caminho)
        return arquivos[0] if arquivos else None

    def validar_manifesto_sfx_e_ambiente(self):
        """Valida a presença física dos efeitos canônicos e ambiências listados no manifesto."""
        ausentes = []
        reg = self.manifesto.get("recursos_integrados") or self.manifesto.get("recursos_pendentes") or {}
        sfx_canonicos = list((reg.get("sfx") or {}).get("canonicos") or [])
        amb_canonicos = list((reg.get("ambience") or {}).get("canonicos") or [])
        for alias in sfx_canonicos:
            if not self._resolver_arquivos_sfx(alias):
                ausentes.append(f"sfx:{alias}")
        for amb in amb_canonicos:
            if not self._localizar_arquivo_ambiente(amb):
                ausentes.append(f"ambience:{amb}")
        return {
            "sfx_canonicos": sfx_canonicos,
            "ambientes_canonicos": amb_canonicos,
            "ausentes": ausentes,
        }
