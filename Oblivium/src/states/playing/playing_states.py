# src/states/playing/playing_states.py
import pygame
from src.states.states import State
from src.states.playing.prologo_controller import PrologoController
from src.states.playing.oakhaven_controller import OakhavenController
from src.mechanics.cutscenes import (
    CutsceneManager,
    CinematicaAtaqueDragao,
    CutsceneReconstrucaoVisual,
)
from src.mechanics.minigames import MinigameFerraria, MinigameCurandeira
from src.ui.ui_utils import desenhar_indicador_tecla

class PlayingState(State):
    def __init__(self, game):
        super().__init__(game)
        self.game = game
        self.prologo_controller = PrologoController(game, self)
        self.prologo = self.prologo_controller
        self.oakhaven_controller = OakhavenController(game, self)
        self.oakhaven = self.oakhaven_controller
        self.cutscene = CutsceneManager(game)
        self.cinematica_dragao = CinematicaAtaqueDragao(game, self)
        self.game.cinematica_dragao = self.cinematica_dragao
        self.minigame_ferraria = MinigameFerraria(game, self)
        self.minigame_curandeira = MinigameCurandeira(game, self)
        self.cutscene_reconstrucao = CutsceneReconstrucaoVisual(game, self)
        self.memoria_anterior_registrada = getattr(self.game.halia, 'fragmentos_memoria', 0)
        self.camera_x = 0.0
        self.camera_y = 0.0
        self.camera_cinematica_alvo = None
        self.camera_cinematica_vel = 4.5
        self._superficie_mundo = None

    @property
    def cutscene_timeskip(self):
        """Alias legado preservado por compatibilidade com testes e referências antigas."""
        return self.cutscene_reconstrucao

    @cutscene_timeskip.setter
    def cutscene_timeskip(self, valor):
        self.cutscene_reconstrucao = valor

    @property
    def cenas(self):
        """Lista das cenas e cutscenes gerenciadas durante o estado JOGANDO."""
        return [
            cena for cena in (
                getattr(self, "cutscene_reconstrucao", None),
                getattr(self, "cinematica_dragao", None),
                getattr(self, "cutscene", None),
                getattr(self.game, "flashback_sistema", None),
                getattr(self.game, "tela_despertar", None),
            )
            if cena is not None
        ]

    @property
    def minigames(self):
        """Lista dos minigames gerenciados durante o estado JOGANDO."""
        return [
            mg for mg in (
                getattr(self, "minigame_ferraria", None),
                getattr(self, "minigame_curandeira", None),
                getattr(self.game, "mg_timing", None),
                getattr(self.game, "mg_mash", None),
            )
            if mg is not None
        ]

    def _em_leitura_ou_cutscene(self):
        return (
            getattr(getattr(self.game, "caixa_dialogo", None), "ativo", False)
            or getattr(getattr(self.game, "flashback_sistema", None), "estado", "INATIVO") != "INATIVO"
            or (hasattr(self, "cinematica_dragao") and self.cinematica_dragao.ativo and self.cinematica_dragao.fase == "DORMINDO")
            or (hasattr(self, "cutscene_reconstrucao") and self.cutscene_reconstrucao.ativo)
        )

    def _obter_areas_protegidas_folhas(self, largura_tela, altura_tela):
        areas_excluidas = []
        if getattr(getattr(self.game, "mapa_casa", None), "cenario_atual", "") == "CASA":
            areas_excluidas.append(pygame.Rect(0, 0, 505, 545))
        caixa = getattr(self.game, "caixa_dialogo", None)
        if caixa and getattr(caixa, "ativo", False) and hasattr(caixa, "obter_areas_protegidas"):
            areas_excluidas.extend(caixa.obter_areas_protegidas(largura_tela, altura_tela))
        return areas_excluidas

    def _bloqueio_ativo(
        self,
        incluir_dialogo=True,
        incluir_transicao=True,
        incluir_cenas=True,
        incluir_minigames=True,
        incluir_inimigos_andando=True,
    ):
        """Verifica de forma unificada se alguma cena, minigame ou painel bloqueia o mundo."""
        if incluir_dialogo and getattr(getattr(self.game, "caixa_dialogo", None), "ativo", False):
            return True
        if incluir_transicao:
            transicao = getattr(self.game, "transicao", None)
            if transicao is not None and getattr(transicao, "estado", "INATIVO") != "INATIVO":
                return True
        if incluir_inimigos_andando and getattr(self.game, "cena_inimigos_andando", False):
            return True
        if incluir_inimigos_andando and any(getattr(i, "revelando", False) for i in self.game.inimigos_em_cena):
            return True
        if any(getattr(self.game, flag, False) for flag in (
            "iniciando_combate", "conversa_combate_ativa", "aguardando_fim_viagem", "fechando_porta"
        )):
            return True
        if incluir_cenas and self.game.dragao_derrotado and getattr(self.game, "etapa_epilogo", "") in (
            "POS_DRAGAO", "FLASHBACK_SYLVAN_PENDENTE", "DESPERTAR_PENDENTE", "RECONSTRUCAO_PENDENTE", "DESPEDIDA_PENDENTE"
        ):
            return True
        if incluir_cenas:
            if any(getattr(cena, "ativo", False) for cena in self.cenas):
                return True
            if getattr(getattr(self.game, "tela_despertar", None), "estado", "INATIVO") != "INATIVO":
                return True
        if incluir_minigames and any(getattr(mg, "ativo", False) for mg in self.minigames):
            return True
        return False

    def atualizar_camera(self, instantaneo=False, dt=None):
        """
        Atualiza suavemente a câmera 2D (Viewport 1280x720) acompanhando Halia
        em mapas expandidos como Oakhaven (2240x1480), respeitando os limites do mundo.
        """
        larg_tela = getattr(self.game, "LARGURA", 1280)
        alt_tela = getattr(self.game, "ALTURA", 720)
        larg_mundo = getattr(self.game.mapa_casa, "largura_mundo", larg_tela)
        alt_mundo = getattr(self.game.mapa_casa, "altura_mundo", alt_tela)

        if larg_mundo <= larg_tela and alt_mundo <= alt_tela:
            self.camera_x = 0.0
            self.camera_y = 0.0
            return

        dt_seg = float(dt) if (isinstance(dt, (int, float)) and dt > 0) else (1.0 / 60.0)
        if hasattr(self, "cutscene_reconstrucao") and self.cutscene_reconstrucao.ativo:
            centro_x, centro_y = self.cutscene_reconstrucao.obter_foco_camera()
            vel_lerp = min(1.0, dt_seg * self.camera_cinematica_vel)
        elif hasattr(self, "cinematica_dragao") and self.cinematica_dragao.ativo and self.cinematica_dragao.fase == "VOO_DRAGAO":
            centro_x, centro_y = self.cinematica_dragao.obter_foco_camera()
            vel_lerp = 0.20
        elif self.camera_cinematica_alvo is not None:
            centro_x, centro_y = self.camera_cinematica_alvo
            vel_lerp = min(1.0, dt_seg * self.camera_cinematica_vel)
        else:
            centro_x = self.game.halia.x + self.game.halia.largura * 0.5
            centro_y = self.game.halia.y + self.game.halia.altura * 0.5
            vel_lerp = 0.16

        alvo_x = max(0.0, min(float(larg_mundo - larg_tela), centro_x - larg_tela * 0.5))
        alvo_y = max(0.0, min(float(alt_mundo - alt_tela), centro_y - alt_tela * 0.5))

        if instantaneo:
            self.camera_x = alvo_x
            self.camera_y = alvo_y
        else:
            self.camera_x += (alvo_x - self.camera_x) * vel_lerp
            self.camera_y += (alvo_y - self.camera_y) * vel_lerp
            if abs(alvo_x - self.camera_x) < 0.5:
                self.camera_x = alvo_x
            if abs(alvo_y - self.camera_y) < 0.5:
                self.camera_y = alvo_y

    def handle_events(self, eventos, teclas):
        if self.game.nome_estado_atual != "JOGANDO":
            return
        cenas_entrada = (self.cutscene_reconstrucao, self.cinematica_dragao, self.game.tela_despertar,
                        self.game.flashback_sistema if not self.game.caixa_dialogo.ativo else None, self.cutscene)
        cena = next((c for c in cenas_entrada if c is not None and c.ativo), None)
        if cena is not None:
            for evento in eventos:
                cena.handle_event(evento)
                if evento.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                    break
            return

        # Delegação aos minigames interativos da vila
        if hasattr(self, "minigame_ferraria") and self.minigame_ferraria.ativo:
            self.minigame_ferraria.handle_events(eventos, teclas)
            return

        if hasattr(self, "minigame_curandeira") and self.minigame_curandeira.ativo:
            self.minigame_curandeira.handle_events(eventos, teclas)
            return

        self._processar_movimento(teclas)
        
        for evento in eventos:
            if hasattr(self.game, 'quest_tracker') and not self.game.caixa_dialogo.ativo and not self.game.mg_timing.ativo and not self.game.mg_mash.ativo and self.game.quest_tracker.handle_event(evento, self.game):
                continue
            if evento.type == pygame.MOUSEMOTION:
                self.game.caixa_dialogo.atualizar_mouse(evento.pos)
                continue
            elif evento.type == pygame.MOUSEWHEEL:
                if self.game.caixa_dialogo.ativo and self.game.caixa_dialogo.em_escolha:
                    self.game.caixa_dialogo.rolar_pagina(evento.y)
                continue
            
            if evento.type == pygame.KEYDOWN:
                self._handle_keydown(evento)
                return
            elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                self._handle_clicks(evento)
                return

    def _atualizar_cinematica_reconstrucao(self, dt):
        return self.oakhaven_controller.atualizar_cinematica_reconstrucao(dt)

    def _concluir_despertar_memoria(self, mem_alvo):
        return self.oakhaven_controller.concluir_despertar_memoria(mem_alvo)

    def update(self, dt=None):
        # Atualização prioritária de timeskip e minigames ativos
        if dt is None or not isinstance(dt, (int, float)) or dt <= 0:
            dt = getattr(self.game, "dt", 1.0 / 60.0)
        if hasattr(self, "cutscene_reconstrucao") and self.cutscene_reconstrucao.ativo:
            self._atualizar_cinematica_reconstrucao(dt)
            return

        if hasattr(self, "minigame_ferraria") and self.minigame_ferraria.ativo:
            self.minigame_ferraria.atualizar(dt)
            return

        if hasattr(self, "minigame_curandeira") and self.minigame_curandeira.ativo:
            self.minigame_curandeira.atualizar(dt)
            return

        # Adiciona o tempo decorrido ao tempo jogado
        self.game.tempo_jogado += dt

        if hasattr(self, "cinematica_dragao") and self.cinematica_dragao.ativo:
            self.cinematica_dragao.atualizar(dt)

        # Verificação de Morte de Halia no Overworld
        if not getattr(self.game.halia, 'vivo', True) or self.game.halia.vida_atual <= 0:
            if hasattr(self.game, 'transicao'):
                if self.game.transicao.estado == "INATIVO":
                    self.game.transicao.iniciar("Halia sucumbiu... Retornando ao último marco.")
                elif self.game.transicao.estado == "ESCURO":
                    if self.game.slot_atual and self.game.save_manager.save_existe(self.game.slot_atual, tipo="autosave"):
                        self.game.carregar_estado(self.game.slot_atual, tipo="autosave")
                    elif self.game.slot_atual and self.game.save_manager.save_existe(self.game.slot_atual, tipo="manual"):
                        self.game.carregar_estado(self.game.slot_atual, tipo="manual")
                    else:
                        self.game.halia.restaurar_total()
                        self.game.mapa_casa.carregar_cenario("CASA")
                        self.game.halia.x, self.game.halia.y = 210, 280
                    self.game.transicao.estado = "CLAREANDO"
            return
        
        # Gerencia e dispara a tela solene de despertar de memória
        mem_atual = getattr(self.game.halia, 'fragmentos_memoria', 0)
        sem_bloqueio_despertar = (
            not self.game.caixa_dialogo.ativo
            and getattr(getattr(self.game, "flashback_sistema", None), "estado", "INATIVO") == "INATIVO"
            and getattr(getattr(self.game, "transicao", None), "estado", "INATIVO") == "INATIVO"
            and not getattr(self.game, "flashback_sylvan_ativo", False)
        )
        if mem_atual > self.memoria_anterior_registrada:
            if (
                hasattr(self.game, 'tela_despertar')
                and self.game.tela_despertar.estado == "INATIVO"
                and sem_bloqueio_despertar
            ):
                self.game.tela_despertar.iniciar(
                    self.memoria_anterior_registrada,
                    mem_atual,
                    on_concluido=lambda m=mem_atual: self._concluir_despertar_memoria(m),
                )
        elif mem_atual < self.memoria_anterior_registrada:
            # Caso ocorra regressão de memórias, ajusta o filtro imediatamente de forma suave
            self.memoria_anterior_registrada = mem_atual
            if hasattr(self.game, 'filtro_memoria') and self.game.filtro_memoria:
                self.game.filtro_memoria.definir_estagio(mem_atual, com_transicao_suave=True)
        
        # Durante a apresentação dos textos, o mundo espera
        if hasattr(self.game, 'tela_despertar') and self.game.tela_despertar.estado != "INATIVO":
            concluiu = self.game.tela_despertar.atualizar(dt)
            if concluiu:
                self._concluir_despertar_memoria(mem_atual)
        else:
            # Sincroniza o filtro apenas quando não há despertar pendente aguardando janela livre
            if mem_atual == self.memoria_anterior_registrada:
                if hasattr(self.game, 'filtro_memoria') and self.game.filtro_memoria:
                    if self.game.filtro_memoria.estagio_atual != mem_atual:
                        self.game.filtro_memoria.definir_estagio(mem_atual, com_transicao_suave=False)

        # Atualiza a interpolação suave do filtro de memória continuamente
        if hasattr(self.game, 'filtro_memoria'):
            self.game.filtro_memoria.atualizar()

        # Atualiza as folhas de outono no cenário com dt e fade suave de leitura
        if hasattr(self.game, 'efeito_folhas') and self.game.efeito_folhas:
            alvo_folhas = 0.20 if self._em_leitura_ou_cutscene() else 1.0
            self.game.efeito_folhas.atualizar(dt, alpha_alvo=alvo_folhas)

        # Atualiza o efeito de clima e chuva no cenário
        if hasattr(self.game, 'efeito_chuva') and self.game.efeito_chuva:
            self.game.efeito_chuva.atualizar(dt)

        # Atualiza o cenário ativo (animações de ambiente como poças de água)
        if hasattr(self.game, 'mapa_casa') and self.game.mapa_casa:
            self.game.mapa_casa.atualizar(dt)

        # Atualiza a câmera 2D acompanhando Halia em cenários expandidos (ex: Oakhaven)
        self.atualizar_camera()

        self.game.caixa_dialogo.atualizar()
        self.cutscene.atualizar_magia(dt)
        self._update_minigames_e_flashbacks()
        self._update_inimigos_e_triggers()
        self._update_transitions()

        # Avança animações das entidades em cena uma única vez por atualização (dependente de dt)
        if hasattr(self.game, "halia") and hasattr(self.game.halia, "atualizar_animacao"):
            self.game.halia.atualizar_animacao(dt)
        if getattr(self.game, "carroceiro_visivel", False) and hasattr(self.game, "carroceiro"):
            self.game.carroceiro.atualizar_animacao(dt)
        for inim_cena in getattr(self.game, "inimigos_em_cena", []):
            if hasattr(inim_cena, "atualizar_animacao"):
                inim_cena.atualizar_animacao(dt)
        for npc_mapa in getattr(self.game.mapa_casa, "npcs", []):
            if hasattr(npc_mapa, "atualizar_animacao"):
                npc_mapa.atualizar_animacao(dt)

        if self.game.caixa_dialogo.opcao_cancelada_id in ["voltar_magia", "desistir_puzzle"]:
            self.game.investigou_pedras = False
            self.game.caixa_dialogo.opcao_cancelada_id = None

    def draw(self, tela):
        cut_reconst = getattr(self, "cutscene_reconstrucao", None)
        em_cinematica_reconstrucao = bool(cut_reconst and getattr(cut_reconst, "ativo", False))
        larg_tela, alt_tela = tela.get_width(), tela.get_height()
        larg_mundo = getattr(self.game.mapa_casa, "largura_mundo", larg_tela)
        alt_mundo = getattr(self.game.mapa_casa, "altura_mundo", alt_tela)
        if em_cinematica_reconstrucao:
            self.camera_x = max(0.0, min(float(max(0, larg_mundo - larg_tela)), self.camera_x))
            self.camera_y = max(0.0, min(float(max(0, alt_mundo - alt_tela)), self.camera_y))
        else:
            self.atualizar_camera()
        usa_camera_mundo = (larg_mundo > larg_tela or alt_mundo > alt_tela)

        if usa_camera_mundo:
            if (
                self._superficie_mundo is None
                or self._superficie_mundo.get_width() != larg_mundo
                or self._superficie_mundo.get_height() != alt_mundo
            ):
                self._superficie_mundo = pygame.Surface((larg_mundo, alt_mundo))
            alvo_mundo = self._superficie_mundo
        else:
            alvo_mundo = tela

        cenario_obj = getattr(self.game.mapa_casa, "cenario_objeto", None)
        usa_ysort = bool(cenario_obj and hasattr(cenario_obj, "desenhar_mundo_ysort"))
        if usa_ysort:
            area_culling = pygame.Rect(int(self.camera_x - 140), int(self.camera_y - 140), larg_tela + 280, alt_tela + 280) if usa_camera_mundo else None
            try:
                cenario_obj.desenhar_camada_inferior(alvo_mundo, area_visivel=area_culling)
            except TypeError:
                cenario_obj.desenhar_camada_inferior(alvo_mundo)
            entidades_dinamicas = [self.game.halia] + list(self.game.inimigos_em_cena)
            if self.game.carroceiro_visivel:
                entidades_dinamicas.append(self.game.carroceiro)
            try:
                cenario_obj.desenhar_mundo_ysort(alvo_mundo, entidades_dinamicas=entidades_dinamicas, area_visivel=area_culling)
            except TypeError:
                cenario_obj.desenhar_mundo_ysort(alvo_mundo, entidades_dinamicas=entidades_dinamicas)
            self.cutscene.desenhar_efeitos(alvo_mundo)
            if hasattr(self, "cinematica_dragao"):
                self.cinematica_dragao.desenhar_mundo(alvo_mundo)
            if cut_reconst and hasattr(cut_reconst, "desenhar_mundo"):
                cut_reconst.desenhar_mundo(alvo_mundo)
            if not em_cinematica_reconstrucao:
                self._draw_interactable_prompts(alvo_mundo)
            if usa_camera_mundo:
                shake_x, shake_y = (0, 0)
                if hasattr(self, "cinematica_dragao") and self.cinematica_dragao.ativo:
                    shake_x, shake_y = self.cinematica_dragao.shake_offset
                cam_x_final = max(0.0, min(float(larg_mundo - larg_tela), self.camera_x + shake_x))
                cam_y_final = max(0.0, min(float(alt_mundo - alt_tela), self.camera_y + shake_y))
                rect_cam = pygame.Rect(int(cam_x_final), int(cam_y_final), larg_tela, alt_tela)
                tela.blit(alvo_mundo, (0, 0), rect_cam)
        else:
            self.game.mapa_casa.desenhar(alvo_mundo)

        # Áreas protegidas reais (casa de Halia e DialogueBox/escolhas/popup com margem de segurança)
        areas_excluidas = self._obter_areas_protegidas_folhas(tela.get_width(), tela.get_height())

        # 1. Camada de fundo das folhas (passando suavemente atrás dos personagens e props)
        if hasattr(self.game, 'efeito_folhas') and self.game.efeito_folhas:
            if hasattr(self.game.efeito_folhas, 'desenhar_camada_fundo'):
                self.game.efeito_folhas.desenhar_camada_fundo(tela, areas_excluidas=areas_excluidas)

        if not usa_ysort:
            if self.game.carroceiro_visivel:
                self.game.carroceiro.desenhar(tela)

            self.game.halia.desenhar(tela)

            for inimigo in self.game.inimigos_em_cena:
                inimigo.desenhar(tela)

            self.cutscene.desenhar_efeitos(tela)

        # 2. Camadas média e frontal das folhas (passando sobre os personagens e rente à tela do jogador)
        if hasattr(self.game, 'efeito_folhas') and self.game.efeito_folhas:
            if hasattr(self.game.efeito_folhas, 'desenhar_camada_frente'):
                self.game.efeito_folhas.desenhar_camada_frente(tela, areas_excluidas=areas_excluidas)
            else:
                self.game.efeito_folhas.desenhar(tela, areas_excluidas=areas_excluidas)

        # Efeito de clima (chuva comum ou chuva pesada com relâmpagos)
        if hasattr(self.game, 'efeito_chuva') and self.game.efeito_chuva and self.game.efeito_chuva.ativo:
            areas_excluidas_chuva = []
            if getattr(self.game.mapa_casa, 'cenario_atual', '') == "CASA":
                areas_excluidas_chuva.append(pygame.Rect(0, 0, 505, 545))
            self.game.efeito_chuva.desenhar(tela, areas_excluidas=areas_excluidas_chuva)

        if not usa_ysort and not em_cinematica_reconstrucao:
            self._draw_interactable_prompts(tela)
        self._draw_ui_overlays(tela)

        # 1. Notificações do gameplay desenhadas antes do filtro para seguirem o estágio de memória
        if hasattr(self.game, 'notificacoes'):
            self.game.notificacoes.draw(tela)

        # 2. Aplica o Filtro de Memória sobre o mundo do jogo, interface e notificações
        if hasattr(self.game, 'filtro_memoria') and self.game.filtro_memoria:
            pos_jog_tela = (
                int(self.game.halia.x - self.camera_x + 20),
                int(self.game.halia.y - self.camera_y + 30)
            )
            self.game.filtro_memoria.aplicar_filtro(tela, pos_jogador=pos_jog_tela)

        # 3. A Tela de Despertar é desenhada no topo absoluto após o filtro com 100% de cores vivas e vibrantes
        if hasattr(self.game, 'tela_despertar') and self.game.tela_despertar.estado != "INATIVO":
            self.game.tela_despertar.desenhar(tela)

        # 4. Cinemática de Repouso e Ataque Aéreo do Dragão (vinheta narrativa e fades)
        if hasattr(self, 'cinematica_dragao'):
            self.cinematica_dragao.desenhar_tela(tela)

        # 5. Cutscene Cinemática de Timeskip de Oakhaven (encerramento da Fase 1)
        if hasattr(self, 'cutscene_reconstrucao') and self.cutscene_reconstrucao.ativo:
            self.cutscene_reconstrucao.desenhar(tela)

    def _processar_movimento(self, teclas):
        if self._bloqueio_ativo():
            if not getattr(self.game, 'distanciando_halia', False):
                self.game.halia.mudar_estado("idle")
            return
            
        dx, dy = 0, 0
        if teclas[self.game.controles["Cima"]]: dy = -1
        if teclas[self.game.controles["Baixo"]]: dy = 1
        if teclas[self.game.controles["Esquerda"]]: dx = -1
        if teclas[self.game.controles["Direita"]]: dx = 1
        
        if dx != 0 or dy != 0:
            velocidade_original = self.game.halia.velocidade
            dt_fator = getattr(self.game, 'dt_fator', 1.0)
            vel_ajustada = velocidade_original * dt_fator
            tecla_correr = self.game.controles.get("Correr", pygame.K_LSHIFT)
            esta_correndo = teclas[tecla_correr] or (tecla_correr in [pygame.K_LSHIFT, pygame.K_RSHIFT] and (teclas[pygame.K_LSHIFT] or teclas[pygame.K_RSHIFT]))
            if esta_correndo:
                vel_ajustada *= 1.8
                
            self.game.halia.velocidade = vel_ajustada
            hitboxes_atuais = list(self.game.mapa_casa.hitboxes) 
            
            if self.game.carroceiro_visivel:
                rect_carroceiro = pygame.Rect(
                    int(self.game.carroceiro.x), 
                    int(self.game.carroceiro.y), 
                    self.game.carroceiro.largura, 
                    self.game.carroceiro.altura
                )
                hitboxes_atuais.append(rect_carroceiro)
            
            pos_ant = (self.game.halia.x, self.game.halia.y)
            self.game.halia.mover(dx, dy, hitboxes_atuais)
            self.game.halia.velocidade = velocidade_original
            if getattr(self.game, 'audio', None): self.game.audio.atualizar_passos_jogador(self.game, (self.game.halia.x, self.game.halia.y) != pos_ant, esta_correndo)
        else:
            self.game.halia.mudar_estado("idle")
            if getattr(self.game, 'audio', None): self.game.audio.atualizar_passos(False)

    def _handle_keydown(self, evento):
        if self.game.flashback_sistema.ativo and evento.key == pygame.K_ESCAPE:
            self.game.flashback_sistema.handle_event(evento)
            return
        if self.game.transicao.estado not in ("INATIVO", "EXIBINDO_TEXTO"):
            return
        # ABRIR O INVENTÁRIO
        if evento.key == self.game.controles.get("Inventário", pygame.K_TAB):
            if not self._bloqueio_ativo() and not self.game.aguardando_fim_viagem:
                self.game.mudar_estado("INVENTARIO")
                return

        # ABRIR O PAUSE
        if evento.key == self.game.controles["Pause"]:
            if not self._bloqueio_ativo():
                self.game.origem_pause = "JOGANDO"
                self.game.mudar_estado("PAUSE")
                return

        # MINIGAMES: Exclusivamente tecla ESPAÇO
        if hasattr(self.game, 'transicao') and self.game.transicao.estado == "EXIBINDO_TEXTO":
            if evento.key in [pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE]:
                self.game.transicao.avancar()
                return
        elif self.game.mg_timing.ativo:
            if evento.key in [pygame.K_SPACE, pygame.K_RETURN, pygame.K_e]:
                self._checar_sucesso_timing()
        elif self.game.mg_mash.ativo:
            res = self.game.mg_mash.processar_evento(evento)
            if res:
                pct = self.game.mg_mash.get_progresso_pct()
                if hasattr(self.game.mapa_casa, 'atualizar_levitacao_minigame'):
                    self.game.mapa_casa.atualizar_levitacao_minigame(pct)
                if res in ["VENCEU", "PERDEU"]:
                    self._finalizar_minigame_levitacao(res)
        elif self.game.caixa_dialogo.ativo:
            box = self.game.caixa_dialogo
            if box.em_escolha:
                if box.pop_up_aberto:
                    if evento.key == pygame.K_ESCAPE:
                        box.fechar_pop_up()
                        return
                    elif evento.key in [pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE]:
                        box.fechar_pop_up()
                        self._processar_avanco_dialogo()
                        return
                    return
                elif evento.key == pygame.K_ESCAPE and box.pode_fechar:
                    box.opcao_cancelada_id = box.id_cancelamento_no
                    box.manager.cancelar_escolha()
                    box._sincronizar_com_manager()
                    return
                elif evento.key in [pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT, 
                                  pygame.K_w, pygame.K_s, pygame.K_a, pygame.K_d,
                                  pygame.K_TAB,
                                  pygame.K_1, pygame.K_KP1,
                                  pygame.K_2, pygame.K_KP2,
                                  pygame.K_3, pygame.K_KP3,
                                  pygame.K_4, pygame.K_KP4]:
                    box.controlar_menu_escolhas(evento.key)
                elif evento.key in [pygame.K_RETURN, pygame.K_KP_ENTER]:
                    if box.opcoes_disponiveis and 0 <= box.opcao_selecionada < len(box.opcoes_disponiveis):
                        opt_atual = box.opcoes_disponiveis[box.opcao_selecionada]
                        if box.opcao_eh_longa(opt_atual, box.opcao_selecionada):
                            box.abrir_pop_up(opt_atual, box.opcao_selecionada)
                            return
                    self._processar_avanco_dialogo()
            elif evento.key in [pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE, pygame.K_e]:
                self._processar_avanco_dialogo()
        elif self.game.flashback_sistema.estado == "ESCURIDAO" and evento.key in [pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE]:
            self.game.flashback_sistema.processar_input()
        elif not self.game.cena_inimigos_andando:
            tecla_interacao = self.game.tecla_interacao
            teclas_validas_interagir = [tecla_interacao]
            if tecla_interacao == pygame.K_SPACE:
                teclas_validas_interagir.extend([pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_e])
            elif tecla_interacao == pygame.K_e:
                teclas_validas_interagir.append(pygame.K_SPACE)

            if evento.key in teclas_validas_interagir:
                self._processar_interacoes_mundo()

    def _handle_clicks(self, evento):
        pos = evento.pos
        if self.game.transicao.estado not in ("INATIVO", "EXIBINDO_TEXTO"):
            return
        
        # Se o minigame de levitação estiver ativo, cliques do mouse impulsionam a magia
        if self.game.mg_mash.ativo:
            res = self.game.mg_mash.processar_evento(evento)
            pct = self.game.mg_mash.get_progresso_pct()
            if hasattr(self.game.mapa_casa, 'atualizar_levitacao_minigame'):
                self.game.mapa_casa.atualizar_levitacao_minigame(pct)
            if res in ["VENCEU", "PERDEU"]:
                self._finalizar_minigame_levitacao(res)
            return
        elif self.game.mg_timing.ativo:
            self._checar_sucesso_timing()
            return

        # Clicar na bolsa do HUD abre o inventário
        if hasattr(self.game, 'hud') and not self._bloqueio_ativo() and not self.game.aguardando_fim_viagem:
            
            if self.game.hud.rect_bolsa.collidepoint(pos):
                self.game.mudar_estado("INVENTARIO")
                return
                
        if hasattr(self.game, 'transicao') and self.game.transicao.estado == "EXIBINDO_TEXTO":
            self.game.transicao.avancar()
            return
        elif self.game.caixa_dialogo.ativo:
            if self.game.caixa_dialogo.em_escolha:
                self._processar_clique_escolha(pos)
            else:
                self._processar_avanco_dialogo()
        elif self.game.flashback_sistema.estado == "ESCURIDAO":
            self.game.flashback_sistema.processar_input()

    def _checar_sucesso_timing(self):
        return self.prologo_controller.checar_sucesso_timing()

    def _finalizar_minigame_levitacao(self, res):
        """Finaliza a levitação, assenta as rochas e abre o diálogo pos_levitar."""
        return self.prologo_controller.finalizar_minigame_levitacao(res)

    def _update_minigames_e_flashbacks(self):
        dt = getattr(self.game, "dt", 1.0 / 60.0)
        if self.game.flashback_sistema.atualizar(dt):
            if getattr(self.game.mapa_casa, "cenario_atual", None) == "NINHO_DRAGAO":
                self.atualizar_camera(instantaneo=True)

        self.prologo_controller.atualizar_minigames(dt)

    def _update_inimigos_e_triggers(self):
        self.prologo_controller.atualizar_inimigos_e_combate()
        self._check_map_zone_triggers()

    def _check_map_zone_triggers(self):
        if (self.game.caixa_dialogo.ativo or self.game.transicao.estado != "INATIVO" or self.game.cena_inimigos_andando
                or any(c.ativo for c in self.cenas) or any(m.ativo for m in self.minigames)):
            return

        if self.oakhaven_controller.verificar_gatilhos_zona():
            return

        self.prologo_controller.verificar_gatilhos_zona()

    def _mover_carroceiro_autonomo(self):
        return self.prologo_controller.mover_carroceiro_autonomo()

    def _processar_avanco_dialogo(self):
        box = self.game.caixa_dialogo
        if not box.ativo or (box.tempo_ultimo_input > 0 and pygame.time.get_ticks() - box.tempo_ultimo_input < 250):
            return
        res_oakhaven = {"abrir_loja": False, "loja_id": None, "ir_patrulha": False}
        if self.game.caixa_dialogo.em_escolha:
            if self.game.caixa_dialogo.opcoes_disponiveis and 0 <= self.game.caixa_dialogo.opcao_selecionada < len(self.game.caixa_dialogo.opcoes_disponiveis):
                opcao_atual = self.game.caixa_dialogo.opcoes_disponiveis[self.game.caixa_dialogo.opcao_selecionada]
                if opcao_atual not in (box.manager.no_atual or {}).get("opcoes", (box.manager.no_atual or {}).get("escolhas", [])):
                    box._sincronizar_com_manager()
                    return
                if not box.manager._opcao_atende_condicoes(opcao_atual):
                    box._sincronizar_com_manager()
                    return
                opt_id = opcao_atual.get("id")
                if self.prologo_controller.processar_escolha_dialogo(opt_id):
                    return
                res_oakhaven = self.oakhaven_controller.processar_escolha_dialogo(opcao_atual)
                if res_oakhaven["interromper"]:
                    return
        self.game.caixa_dialogo.proximo_texto()
        self.oakhaven_controller.processar_eventos_pos_avanco_dialogo(
            abrir_loja_apos=res_oakhaven["abrir_loja"],
            loja_id_alvo=res_oakhaven["loja_id"],
            ir_patrulha_apos=res_oakhaven["ir_patrulha"],
        )

    def _processar_clique_escolha(self, pos):
        box = self.game.caixa_dialogo
        if box.pop_up_aberto:
            if box.rect_popup_confirmar and box.rect_popup_confirmar.collidepoint(pos):
                box.fechar_pop_up()
                self._processar_avanco_dialogo()
                return
            elif (box.rect_popup_cancelar and box.rect_popup_cancelar.collidepoint(pos)) or \
                 (box.rect_popup_fechar and box.rect_popup_fechar.collidepoint(pos)):
                box.fechar_pop_up()
                return
            elif box.rect_popup and not box.rect_popup.collidepoint(pos):
                box.fechar_pop_up()
                return
            return

        for i, r in enumerate(box.rects_opcoes):
            if r.collidepoint(pos):
                idx_global = (box.pagina_atual * box.opcoes_por_pagina) + i
                if idx_global < len(box.opcoes_disponiveis):
                    box.opcao_selecionada = idx_global
                    opt = box.opcoes_disponiveis[idx_global]
                    if box.opcao_eh_longa(opt, idx_global):
                        box.abrir_pop_up(opt, idx_global)
                        return
                    self._processar_avanco_dialogo()
                    return
                    
        box.clicar_mouse(pos)

    def _processar_interacoes_mundo(self):
        if self.game.nome_estado_atual != "JOGANDO" or self._bloqueio_ativo():
            return
        area_interacao = pygame.Rect(
            self.game.halia.x - 24,
            self.game.halia.y - 24,
            self.game.halia.largura + 48,
            self.game.halia.altura + 48,
        )

        for item in self.game.mapa_casa.itens_no_chao[:]:
            if area_interacao.colliderect(item.rect):
                id_do_item = getattr(item, "id_unico", "desconhecido")
                if str(id_do_item).startswith("erva_lunar"):
                    self.minigame_curandeira.iniciar(item)
                    return

                self.game.mapa_casa.itens_no_chao.remove(item)
                if hasattr(self.game, "audio") and self.game.audio:
                    self.game.audio.tocar_sfx("item_coletar")

                if id_do_item not in self.game.itens_coletados:
                    self.game.itens_coletados.append(id_do_item)

                self.prologo_controller.processar_interacao_item_inicial(item, id_do_item)
                return

        if self.prologo_controller.processar_interacao_cenario(area_interacao):
            return

        self.oakhaven_controller.processar_interacao_cenario(area_interacao)

    def _update_transitions(self):
        if self.game.transicao.update() if hasattr(self.game.transicao, 'update') else self.game.transicao.atualizar():
            if self.game.iniciando_combate:
                self.game.iniciando_combate = False
                self.game.transicao.estado = "CLAREANDO"
                cenario_combate = self.game.mapa_casa.cenario_atual

                def on_vitoria():
                    if getattr(self.game, "combate_climax_dragao", False):
                        self.oakhaven_controller.on_vitoria_combate_dragao()
                        return

                    if cenario_combate in ("OAKHAVEN", "ORLA_NORTE"):
                        self.oakhaven_controller.on_vitoria_combate_patrulha()
                        return

                    self.prologo_controller.on_vitoria_combate_estrada()

                def on_derrota():
                    self.on_derrota()

                def on_fuga():
                    if cenario_combate in ("OAKHAVEN", "ORLA_NORTE"):
                        self.oakhaven_controller.on_fuga_combate_patrulha()
                    else:
                        self.prologo_controller.on_fuga_combate_estrada()
                    self.game.cena_inimigos_andando = False
                    self.game.mudar_estado("JOGANDO")

                self.game.iniciar_combate(
                    inimigos=self.game.inimigos_em_cena,
                    on_vitoria=on_vitoria,
                    on_derrota=on_derrota,
                    on_fuga=on_fuga
                )
            elif self.game.mapa_casa.cenario_atual == "CASA":
                self._entrar_na_estrada_1()
            elif self.game.mapa_casa.cenario_atual == "ESTRADA":
                self._entrar_na_estrada_2()
            elif self.game.mapa_casa.cenario_atual == "ESTRADA_2":
                self._entrar_em_oakhaven()

    def on_derrota(self):
        """Recarrega o checkpoint após derrota e limpa uniformemente flags transitórias, cenas e inimigos."""
        self.game.inimigos_em_cena.clear()
        carregou_save = False
        if self.game.slot_atual and self.game.save_manager.save_existe(self.game.slot_atual, tipo="autosave"):
            carregou_save = bool(self.game.carregar_estado(self.game.slot_atual, tipo="autosave"))
        elif self.game.slot_atual and self.game.save_manager.save_existe(self.game.slot_atual, tipo="manual"):
            carregou_save = bool(self.game.carregar_estado(self.game.slot_atual, tipo="manual"))

        if not carregou_save:
            self.game.halia.restaurar_total()
            self.game.halia.x, self.game.halia.y = 60, 330

        for attr_game, padrao in self.game.save_manager.FLAGS_TRANSITORIAS:
            setattr(self.game, attr_game, padrao)
        self.game.iniciando_combate = False
        self.game.cena_inimigos_andando = False
        self.game.bola_fogo_ativa = False
        self.game.distanciando_halia = False
        self.game.timer_magia = 0
        self.game.inimigos_em_cena.clear()

        if hasattr(self.game, "caixa_dialogo") and self.game.caixa_dialogo:
            self.game.caixa_dialogo.ativo = False
            self.game.caixa_dialogo.em_escolha = False
            if hasattr(self.game.caixa_dialogo, "manager") and self.game.caixa_dialogo.manager:
                self.game.caixa_dialogo.manager.consumir_evento()
        if hasattr(self.game, "transicao") and self.game.transicao:
            self.game.transicao.estado = "INATIVO"
        if hasattr(self, "cinematica_dragao") and self.cinematica_dragao:
            self.cinematica_dragao.ativo = False
        if hasattr(self, "cutscene_reconstrucao") and self.cutscene_reconstrucao:
            self.cutscene_reconstrucao.ativo = False

        if self.game.mapa_casa.cenario_atual == "ESTRADA_2":
            self.prologo_controller.resetar_derrota_estrada_2()

        self.game.mudar_estado("JOGANDO")

    def _entrar_na_estrada_1(self):
        return self.prologo_controller.entrar_na_estrada_1()

    def _entrar_na_estrada_2(self):
        return self.prologo_controller.entrar_na_estrada_2()

    def _entrar_em_oakhaven(self):
        """Transiciona Halia para a entrada sul da Vila de Oakhaven (Fase 1)."""
        return self.oakhaven_controller.entrar_em_oakhaven()

    def _ir_para_patrulha_orla_norte(self):
        """
        O Guarda Doran conduz Halia pelo Portão Norte até a clareira da Orla Norte ('ORLA_NORTE'),
        onde os 2 Batedores Demoníacos estão escondidos.
        """
        return self.oakhaven_controller.ir_para_patrulha_orla_norte()

    def _iniciar_amanhecer_ataque_dragao(self):
        """
        Após o repouso noturno em Oakhaven, Halia acorda na calada da noite com
        Ignis'Vahr, o Dragão Vermelho Ancestral, atacando e destruindo a vila ('OAKHAVEN_DESTRUIDA').
        """
        return self.oakhaven_controller.iniciar_amanhecer_ataque_dragao()

    def _iniciar_climax_dragao_oakhaven(self):
        """
        Inicia o Clímax da Fase 1 no Ninho do Dragão ('NINHO_DRAGAO') durante a noite:
        Ignis'Vahr, o Dragão Vermelho Ancestral, aguarda nos penhascos vulcânicos, desencadeando
        a Crise de Ansiedade 1 (Trauma do Fogo) + Ancoragem Sensorial antes da Batalha de Chefe.
        """
        return self.oakhaven_controller.iniciar_climax_dragao_oakhaven()

    def _ir_para_ninho_dragao(self):
        """Alias semântico para transportar Halia de Oakhaven destruída até o Ninho do Dragão."""
        return self.oakhaven_controller.ir_para_ninho_dragao()

    def _draw_interactable_prompts(self, tela):
        if self._bloqueio_ativo(incluir_dialogo=False, incluir_transicao=False, incluir_cenas=False, incluir_minigames=True, incluir_inimigos_andando=False):
            return

        bloqueado_geral = self._bloqueio_ativo()
        area_interacao = pygame.Rect(self.game.halia.x - 24, self.game.halia.y - 24, self.game.halia.largura + 48, self.game.halia.altura + 48)
        tecla_interacao_str = self.game.nome_tecla_interacao

        if not self.game.caixa_dialogo.ativo:
            for item in self.game.mapa_casa.itens_no_chao:
                if area_interacao.colliderect(item.rect):
                    acao_item = "para Colher" if str(getattr(item, "id_unico", "")).startswith("erva_lunar") else "para Pegar"
                    desenhar_indicador_tecla(tela, item.x + (item.largura // 2), item.y - 34, tecla=tecla_interacao_str, acao=acao_item)
                    break

        self.prologo_controller.desenhar_prompts(
            tela, area_interacao, tecla_interacao_str, bloqueado_geral, desenhar_indicador_tecla
        )
        self.oakhaven_controller.desenhar_prompts(
            tela, area_interacao, tecla_interacao_str, desenhar_indicador_tecla
        )

    def _draw_ui_overlays(self, tela):
        self.game.mg_timing.desenhar(tela)
        self.game.mg_mash.desenhar(tela)
        self.game.transicao.desenhar(tela)
        self.game.flashback_sistema.desenhar(tela)
        self.game.caixa_dialogo.desenhar(tela)

        minigame_ativo = self._bloqueio_ativo(
            incluir_dialogo=False,
            incluir_transicao=False,
            incluir_cenas=False,
            incluir_minigames=True,
            incluir_inimigos_andando=False,
        )

        # Minigames Interativos da Vila (Ferraria e Curandeira)
        if hasattr(self, 'minigame_ferraria') and self.minigame_ferraria.ativo:
            self.minigame_ferraria.desenhar(tela)
        if hasattr(self, 'minigame_curandeira') and self.minigame_curandeira.ativo:
            self.minigame_curandeira.desenhar(tela)
        
        # O HUD e Quest Tracker são desenhados normalmente quando não houver minigames, diálogos, despertar ou timeskip
        timeskip_ativo = getattr(getattr(self, 'cutscene_reconstrucao', None), 'ativo', False)
        if not minigame_ativo and not self.game.caixa_dialogo.ativo and getattr(self.game.tela_despertar, 'estado', 'INATIVO') == 'INATIVO' and not timeskip_ativo:
            if hasattr(self.game, 'hud'):
                self.game.hud.desenhar(tela, self.game)
            if hasattr(self.game, 'quest_tracker'):
                self.game.quest_tracker.desenhar(tela, self.game)
