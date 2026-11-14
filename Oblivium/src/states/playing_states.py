# src/states/playing_states.py
import pygame
from src.states.states import State
from src.entities.enemy_factory import EnemyFactory
from src.mechanics.item_factory import ItemFactory
from src.mechanics.cutscene_manager import CutsceneManager
from src.mechanics.cinematica_dragao import CinematicaAtaqueDragao
from src.mechanics.minigame_ferraria import MinigameFerraria
from src.mechanics.minigame_curandeira import MinigameCurandeira
from src.mechanics.cutscene_reconstrucao_visual import CutsceneReconstrucaoVisual
from src.ui.ui_utils import desenhar_indicador_tecla

class PlayingState(State):
    def __init__(self, game):
        super().__init__(game)
        self.game = game
        self.cutscene = CutsceneManager(game)
        self.cinematica_dragao = CinematicaAtaqueDragao(game, self)
        self.game.cinematica_dragao = self.cinematica_dragao
        self.minigame_ferraria = MinigameFerraria(game, self)
        self.minigame_curandeira = MinigameCurandeira(game, self)
        self.cutscene_reconstrucao = CutsceneReconstrucaoVisual(game, self)
        self.memoria_anterior_registrada = getattr(self.game.halia, 'fragmentos_memoria', 0)
        self.camera_x = 0.0
        self.camera_y = 0.0
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
        if incluir_cenas and any(getattr(cena, "ativo", False) for cena in self.cenas):
            return True
        if incluir_minigames and any(getattr(mg, "ativo", False) for mg in self.minigames):
            return True
        return False

    def atualizar_camera(self, instantaneo=False):
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

        # Se a cinemática do dragão estiver no voo aéreo, a câmera acompanha o dragão cruzando a vila com visão ampla da destruição no solo
        if hasattr(self, "cinematica_dragao") and self.cinematica_dragao.ativo and self.cinematica_dragao.fase == "VOO_DRAGAO":
            centro_x, centro_y = self.cinematica_dragao.obter_foco_camera()
            vel_lerp = 0.20
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
        # Delegação à cutscene de encerramento / timeskip
        if hasattr(self, "cutscene_reconstrucao") and self.cutscene_reconstrucao.ativo:
            for evento in eventos:
                self.cutscene_reconstrucao.handle_event(evento)
            return

        if hasattr(self, "cinematica_dragao") and self.cinematica_dragao.ativo:
            for evento in eventos:
                self.cinematica_dragao.handle_event(evento)
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
            elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                self._handle_clicks(evento)

    def update(self):
        # Atualização prioritária de timeskip e minigames ativos
        dt = getattr(self.game, "dt", 1.0 / 60.0)
        if hasattr(self, "cutscene_reconstrucao") and self.cutscene_reconstrucao.ativo:
            self.cutscene_reconstrucao.atualizar(dt)
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
        if mem_atual > self.memoria_anterior_registrada:
            # Só inicia o despertar se não houver diálogos ativos
            if hasattr(self.game, 'tela_despertar') and self.game.tela_despertar.estado == "INATIVO" and not self.game.caixa_dialogo.ativo:
                self.game.tela_despertar.iniciar(self.memoria_anterior_registrada, mem_atual)
        elif mem_atual < self.memoria_anterior_registrada:
            # Caso ocorra regressão de memórias, ajusta o filtro imediatamente de forma suave
            self.memoria_anterior_registrada = mem_atual
            if hasattr(self.game, 'filtro_memoria') and self.game.filtro_memoria:
                self.game.filtro_memoria.definir_estagio(mem_atual, com_transicao_suave=True)
        
        # Durante a apresentação dos textos, o mundo espera
        if hasattr(self.game, 'tela_despertar') and self.game.tela_despertar.estado != "INATIVO":
            concluiu = self.game.tela_despertar.atualizar()
            if concluiu:
                # O jogador concluiu a leitura dos textos! Agora sim disparamos o pulso de cor e atualizamos o estágio
                self.memoria_anterior_registrada = mem_atual
                if hasattr(self.game, 'filtro_memoria') and self.game.filtro_memoria:
                    self.game.filtro_memoria.definir_estagio(
                        mem_atual, 
                        com_transicao_suave=True, 
                        pos_origem=(self.game.halia.x + 20, self.game.halia.y + 30)
                    )
                if hasattr(self.game, 'notificacoes') and self.game.notificacoes:
                    self.game.notificacoes.notificar_memoria_desperta(mem_atual)
                if hasattr(self.game, 'conquistas') and self.game.conquistas and mem_atual >= 1:
                    self.game.conquistas.desbloquear("sincronia_2")
        else:
            # Sincronização de segurança: garante que o filtro e o registro correspondam exatamente à memória
            if mem_atual > self.memoria_anterior_registrada:
                if hasattr(self.game, 'notificacoes') and self.game.notificacoes:
                    self.game.notificacoes.notificar_memoria_desperta(mem_atual)
            if hasattr(self.game, 'filtro_memoria') and self.game.filtro_memoria:
                if self.game.filtro_memoria.estagio_atual != mem_atual:
                    self.game.filtro_memoria.definir_estagio(mem_atual, com_transicao_suave=False)
            self.self_mem_sync = mem_atual
            self.memoria_anterior_registrada = mem_atual

        # Atualiza a interpolação suave do filtro de memória continuamente
        if hasattr(self.game, 'filtro_memoria'):
            self.game.filtro_memoria.atualizar()

        # Atualiza as folhas de outono no cenário
        if hasattr(self.game, 'efeito_folhas') and self.game.efeito_folhas:
            self.game.efeito_folhas.atualizar()

        # Atualiza o efeito de clima e chuva no cenário
        if hasattr(self.game, 'efeito_chuva') and self.game.efeito_chuva:
            self.game.efeito_chuva.atualizar(0.016)

        # Atualiza o cenário ativo (animações de ambiente como poças de água)
        if hasattr(self.game, 'mapa_casa') and self.game.mapa_casa:
            self.game.mapa_casa.atualizar(0.016)

        # Atualiza a câmera 2D acompanhando Halia em cenários expandidos (ex: Oakhaven)
        self.atualizar_camera()

        self.game.caixa_dialogo.atualizar()
        self.cutscene.atualizar_magia(dt)
        self._update_minigames_e_flashbacks()
        self._update_inimigos_e_triggers()
        self._update_transitions()

        if self.game.caixa_dialogo.opcao_cancelada_id in ["voltar_magia", "desistir_puzzle"]:
            self.game.investigou_pedras = False
            self.game.caixa_dialogo.opcao_cancelada_id = None

    def draw(self, tela):
        self.atualizar_camera()
        larg_tela, alt_tela = tela.get_width(), tela.get_height()
        larg_mundo = getattr(self.game.mapa_casa, "largura_mundo", larg_tela)
        alt_mundo = getattr(self.game.mapa_casa, "altura_mundo", alt_tela)
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

        # Áreas excluídas para folhagens e clima (ex: dentro da casa de Halia não cai folhas)
        areas_excluidas = []
        if getattr(self.game.mapa_casa, 'cenario_atual', '') == "CASA":
            areas_excluidas.append(pygame.Rect(0, 0, 505, 545))

        # Se houver diálogo ativo, exclui a região da caixa de diálogo para garantir leitura 100% limpa
        if hasattr(self.game, 'caixa_dialogo') and self.game.caixa_dialogo.ativo:
            areas_excluidas.append(pygame.Rect(60, 480, 1160, 225))

        # Multiplicador de opacidade: durante diálogos ou cutscenes/flashbacks, folhas ficam sutis ao fundo (0.20)
        em_dialogo_ou_cutscene = (
            getattr(self.game.caixa_dialogo, 'ativo', False) or 
            getattr(self.game.flashback_sistema, 'estado', 'INATIVO') != 'INATIVO' or
            (hasattr(self, "cinematica_dragao") and self.cinematica_dragao.ativo and self.cinematica_dragao.fase == "DORMINDO") or
            (hasattr(self, "cutscene_reconstrucao") and self.cutscene_reconstrucao.ativo)
        )
        alpha_folhas = 0.20 if em_dialogo_ou_cutscene else 1.0

        # 1. Camada de fundo das folhas (passando suavemente atrás dos personagens e props)
        if hasattr(self.game, 'efeito_folhas') and self.game.efeito_folhas:
            if hasattr(self.game.efeito_folhas, 'desenhar_camada_fundo'):
                self.game.efeito_folhas.desenhar_camada_fundo(tela, areas_excluidas=areas_excluidas, alpha_multiplicador=alpha_folhas)

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
                self.game.efeito_folhas.desenhar_camada_frente(tela, areas_excluidas=areas_excluidas, alpha_multiplicador=alpha_folhas)
            else:
                self.game.efeito_folhas.desenhar(tela, areas_excluidas=areas_excluidas, alpha_multiplicador=alpha_folhas)

        # Efeito de clima (chuva comum ou chuva pesada com relâmpagos)
        if hasattr(self.game, 'efeito_chuva') and self.game.efeito_chuva and self.game.efeito_chuva.ativo:
            areas_excluidas_chuva = []
            if getattr(self.game.mapa_casa, 'cenario_atual', '') == "CASA":
                areas_excluidas_chuva.append(pygame.Rect(0, 0, 505, 545))
            self.game.efeito_chuva.desenhar(tela, areas_excluidas=areas_excluidas_chuva)

        if not usa_ysort:
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
            
            self.game.halia.mover(dx, dy, hitboxes_atuais)
            self.game.halia.velocidade = velocidade_original
        else:
            self.game.halia.mudar_estado("idle")

    def _handle_keydown(self, evento):
        # Avanço da Tela Solene de Despertar de Memória (Enter ou Clique)
        if hasattr(self.game, 'tela_despertar') and self.game.tela_despertar.estado != "INATIVO":
            if evento.key in [pygame.K_RETURN, pygame.K_KP_ENTER]:
                self.game.tela_despertar.processar_input()
                return

        # ABRIR O INVENTÁRIO
        if evento.key == self.game.controles.get("Inventário", pygame.K_TAB):
            if not self._bloqueio_ativo() and not self.game.aguardando_fim_viagem:
                self.game.mudar_estado("INVENTARIO")
                return

        # ABRIR O PAUSE
        if evento.key == self.game.controles["Pause"]:
            if not self._bloqueio_ativo(incluir_inimigos_andando=False):
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
        # Avanço da Tela Solene de Despertar de Memória
        if hasattr(self.game, 'tela_despertar') and self.game.tela_despertar.estado != "INATIVO":
            self.game.tela_despertar.processar_input()
            return

        pos = evento.pos
        
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
                self.game.caixa_dialogo.clicar_mouse(pos)
        elif self.game.flashback_sistema.estado == "ESCURIDAO":
            self.game.flashback_sistema.processar_input()

    def _checar_sucesso_timing(self):
        res = self.game.mg_timing.checar_sucesso()
        if res == "VENCEU" or res is True:
            self.game.magia_ativa = "FOGO"
            self.game.distanciando_halia = True
            self.game.timer_magia = 0
            if hasattr(self.game, 'conquistas') and self.game.conquistas:
                self.game.conquistas.desbloquear("chama_primordial")
        elif res == "AVANCOU_ETAPA":
            pass
        else:
            self.game.caixa_dialogo.iniciar_dialogo("falha_timing")

    def _finalizar_minigame_levitacao(self, res):
        """Finaliza a levitação, assenta as rochas e abre o diálogo pos_levitar."""
        if res == "VENCEU":
            if hasattr(self.game.mapa_casa, 'desobstruir_estrada'):
                self.game.mapa_casa.desobstruir_estrada("LEVITAR")
            self.game.magia_usada_no_puzzle = "LEVITAR"
            self.game.magia_ativa = "CONCLUIDO"
            self.game.distanciando_halia = False
            self.game.timer_magia = 0
            if hasattr(self.game, 'conquistas') and self.game.conquistas:
                self.game.conquistas.desbloquear("dominio_gravidade")
            self.game.caixa_dialogo.iniciar_dialogo("pos_levitar")
            self.game.conversa_combate_ativa = True
        elif res == "PERDEU":
            if hasattr(self.game.mapa_casa, 'atualizar_levitacao_minigame'):
                self.game.mapa_casa.atualizar_levitacao_minigame(0.0)
            self.game.caixa_dialogo.iniciar_dialogo("falha_mash")

    def _update_minigames_e_flashbacks(self):
        dt = getattr(self.game, "dt", 1.0 / 60.0)
        if self.game.flashback_sistema.atualizar(dt):
            if getattr(self.game.mapa_casa, "cenario_atual", None) == "NINHO_DRAGAO":
                self.atualizar_camera(instantaneo=True)

        if self.game.mg_timing.ativo:
            self.game.mg_timing.atualizar(dt)
        elif self.game.mg_mash.ativo:
            res = self.game.mg_mash.atualizar(dt)

            pct = self.game.mg_mash.get_progresso_pct()
            if hasattr(self.game.mapa_casa, 'atualizar_levitacao_minigame'):
                self.game.mapa_casa.atualizar_levitacao_minigame(pct)

            if res in ["VENCEU", "PERDEU"]:
                self._finalizar_minigame_levitacao(res)

        if self.game.mapa_casa.cenario_atual == "ESTRADA_2" and self.game.investigou_pedras and self.game.magia_ativa is None and not self._bloqueio_ativo(incluir_transicao=False, incluir_inimigos_andando=False):
            if self.game.magia_selecionada_temporaria == "FOGO":
                self.game.magia_selecionada_temporaria = None
                self.game.mg_timing.iniciar()
            elif self.game.magia_selecionada_temporaria == "LEVITAR":
                self.game.magia_selecionada_temporaria = None
                self.game.mg_mash.iniciar()

    def _update_inimigos_e_triggers(self):
        # 1. GATILHO DA CUTSCENE (Nascer dos inimigos)
        if self.game.conversa_combate_ativa and not self.game.caixa_dialogo.ativo:
            self.game.conversa_combate_ativa = False
            self.game.cena_inimigos_andando = True
            
            if self.game.halia.x > 1000:
                self.game.halia.x = 1000
            self.game.halia.virado_direita = True
            self.game.halia.direcao = "direita"
            self.game.halia.mudar_estado("idle")
                
            if self.game.magia_usada_no_puzzle == "FOGO":
                sombra1 = EnemyFactory.criar("demonio_inferior", x=1180, y=290, nome_custom="Demônio Inferior Voraz")
                sombra2 = EnemyFactory.criar("demonio_inferior", x=1180, y=420, nome_custom="Demônio Inferior Vigia")
                sombra1.velocidade = 3.5
                sombra2.velocidade = 3.5
                sombra1.recompensas = {"moedas": 20, "memorias": 0, "xp": 40}
                sombra2.recompensas = {"moedas": 20, "memorias": 0, "xp": 40}
                sombra1.virado_direita = False
                sombra2.virado_direita = False
                sombra1.direcao = "esquerda"
                sombra2.direcao = "esquerda"
                self.game.inimigos_em_cena.extend([sombra1, sombra2])
            elif self.game.magia_usada_no_puzzle == "LEVITAR":
                boss = EnemyFactory.criar_boss("demonio_superior", x=1180, y=310, nome_custom="Demônio Superior (Chefe)")
                boss.velocidade = 3.5
                boss.recompensas = {"moedas": 45, "memorias": 0, "xp": 80}
                boss.virado_direita = False
                boss.direcao = "esquerda"
                self.game.inimigos_em_cena.append(boss)

        # 2. MOVIMENTO DA CUTSCENE (Roteirizado)
        if self.game.cena_inimigos_andando:
            x_parada = max(self.game.halia.x + self.game.halia.largura + 100, 850)
            alguem_chegou = False
            
            for inimigo in self.game.inimigos_em_cena:
                if not self.game.iniciando_combate:
                    inimigo.virado_direita = False
                    inimigo.direcao = "esquerda"
                    if inimigo.x > x_parada:
                        inimigo.mover(-inimigo.velocidade, 0)
                    else:
                        inimigo.mover(0, 0)
                        alguem_chegou = True
                        
            if alguem_chegou and not self.game.iniciando_combate:
                self.game.iniciando_combate = True
                self.game.transicao.iniciar()

        self._check_map_zone_triggers()

    def _check_map_zone_triggers(self):
        if self.game.caixa_dialogo.ativo or self.game.transicao.estado != "INATIVO" or self.game.cena_inimigos_andando:
            return

        # Processa eventos de fim de diálogo (funcionando tanto via teclado quanto via clique do mouse)
        evt_pendente = getattr(self.game.caixa_dialogo.manager, "evento_pendente", None)
        if evt_pendente in (
            "cura_elara_missao",
            "cura_elara_destruida",
            "ir_patrulha_doran",
            "iniciar_cutscene_dormir_vila",
            "iniciar_amanhecer_ataque_dragao",
            "ir_para_ninho_dragao",
            "iniciar_climax_dragao_oakhaven",
            "iniciar_combate_dragao_oakhaven",
            "iniciar_flashback_sylvan_ninho",
            "retornar_oakhaven_vitoria",
            "iniciar_timeskip_final_oakhaven",
        ):
            self.game.caixa_dialogo.manager.consumir_evento()
            if evt_pendente in ("cura_elara_missao", "cura_elara_destruida"):
                if hasattr(self.game, "halia") and self.game.halia:
                    self.game.halia.restaurar_total()
                if evt_pendente == "cura_elara_missao" and hasattr(self.game, "missoes") and self.game.missoes:
                    if self.game.missoes.missoes.get("missao_ervas_medicinais", {}).get("status") != "CONCLUIDA":
                        self.game.missoes.concluir_missao("missao_ervas_medicinais")
                return
            elif evt_pendente == "ir_patrulha_doran":
                self._ir_para_patrulha_orla_norte()
                return
            elif evt_pendente == "iniciar_cutscene_dormir_vila":
                self.game.caixa_dialogo.ativo = False
                if hasattr(self, "cinematica_dragao"):
                    self.cinematica_dragao.iniciar_sono()
                return
            elif evt_pendente == "iniciar_amanhecer_ataque_dragao":
                if hasattr(self, "cinematica_dragao"):
                    self.cinematica_dragao.iniciar_ataque_aereo()
                else:
                    self._iniciar_amanhecer_ataque_dragao()
                return
            elif evt_pendente in ("ir_para_ninho_dragao", "iniciar_climax_dragao_oakhaven"):
                self._iniciar_climax_dragao_oakhaven()
                return
            elif evt_pendente == "iniciar_combate_dragao_oakhaven":
                self.game.combate_climax_dragao = True
                self.game.iniciando_combate = True
                self.game.transicao.iniciar()
                return
            elif evt_pendente == "iniciar_flashback_sylvan_ninho":
                seq_sylvan = self.game.caixa_dialogo.manager.obter_sequencia_linear("flashback_memoria_2_sylvan")
                self.game.flashback_sylvan_ativo = True
                self.game.flashback_sistema.iniciar(seq_sylvan, tipo="acampamento", game=self.game)
                return
            elif evt_pendente == "retornar_oakhaven_vitoria":
                self.game.transicao.iniciar("Retornando vitoriosa a Oakhaven...")
                cenario_retorno = "OAKHAVEN_DESTRUIDA" if getattr(self.game, "oakhaven_destruida", True) else "OAKHAVEN"
                self.game.mapa_casa.carregar_cenario(cenario_retorno)
                self.game.halia.x, self.game.halia.y = 1102, 660
                self.game.halia.direcao = "cima"
                self.game.halia.mudar_estado("idle")
                self.atualizar_camera(instantaneo=True)
                self.game.aguardando_dialogo_pos_dragao = True
                if self.game.slot_atual:
                    self.game.salvar_estado(self.game.slot_atual, tipo="autosave")
                return
            elif evt_pendente == "iniciar_timeskip_final_oakhaven":
                if hasattr(self, "cutscene_reconstrucao"):
                    self.cutscene_reconstrucao.iniciar()
                return

        if self.game.mapa_casa.cenario_atual == "CASA" and self.game.mapa_casa.porta_aberta and self.game.halia.y > 545:
            self.game.mapa_casa.fechar_porta()
            self.game.caixa_dialogo.iniciar_dialogo("fechar_porta")
            
        if self.game.mapa_casa.cenario_atual == "CASA" and not self.game.mapa_casa.porta_aberta and self.game.halia.x > 1220:
            self.game.transicao.iniciar("Seguindo viagem...")

        if self.game.mapa_casa.cenario_atual == "ESTRADA" and not self.game.carroceiro_visivel and self.game.halia.x > 640:
            self.game.carroceiro_visivel = True
            self.game.carroceiro_andando = True
            self.game.carroceiro.velocidade = 2
            self.game.carroceiro.mudar_estado("andar")
            self.game.caixa_dialogo.iniciar_dialogo("avistar_carroceiro")

        if self.game.mapa_casa.cenario_atual == "ESTRADA_2" and not self.game.investigou_pedras and self.game.halia.x > 1000:
            self.game.investigou_pedras = True; self.game.halia.x = 980
            self.game.caixa_dialogo.iniciar_dialogo("escolha_magias" if self.game.flashback_magia_concluido else "investigar_pedras")

        if self.game.carroceiro_andando:
            self._mover_carroceiro_autonomo()

        if self.game.mapa_casa.cenario_atual == "ESTRADA" and self.game.aguardando_fim_viagem and not self.game.caixa_dialogo.ativo:
            self.game.aguardando_fim_viagem = False; self.game.conversa_carroceiro_terminou = True
            self.game.transicao.iniciar("Algumas horas depois...")

        # Partida com o carroceiro em Estrada 2 -> Desperta a Memória e Cores (Padrão original do Prólogo)
        if self.game.mapa_casa.cenario_atual == "ESTRADA_2" and getattr(self.game, 'partindo_estrada2', False) and not self.game.caixa_dialogo.ativo:
            self.game.partindo_estrada2 = False
            self.game.conversa_carroceiro_terminou = True
            if hasattr(self.game, 'conquistas') and self.game.conquistas:
                self.game.conquistas.desbloquear("rumo_a_vila")
            if self.game.halia.fragmentos_memoria < 1:
                self.game.halia.recuperar_memoria(1)
            if self.game.slot_atual:
                self.game.salvar_estado(self.game.slot_atual, tipo="autosave")

        # No Ninho do Dragão após a vitória ao amanhecer: caminhar até a trilha sul (y > 645) retorna a Oakhaven
        if self.game.mapa_casa.cenario_atual == "NINHO_DRAGAO" and getattr(self.game.mapa_casa.cenario_objeto, "dragao_derrotado", False):
            if self.game.halia.y > 645 and self.game.transicao.estado == "INATIVO" and not self.game.caixa_dialogo.ativo:
                self.game.transicao.iniciar("Retornando vitoriosa a Oakhaven...")
                cenario_retorno = "OAKHAVEN_DESTRUIDA" if getattr(self.game, "oakhaven_destruida", True) else "OAKHAVEN"
                self.game.mapa_casa.carregar_cenario(cenario_retorno)
                self.game.halia.x, self.game.halia.y = 1102, 660
                self.game.halia.direcao = "cima"
                self.game.halia.mudar_estado("idle")
                self.atualizar_camera(instantaneo=True)
                self.game.aguardando_dialogo_pos_dragao = True
                if self.game.slot_atual:
                    self.game.salvar_estado(self.game.slot_atual, tipo="autosave")
                return

        # Após despertar da Memória 2 (Sylvan) no pós-clímax do Dragão em Oakhaven
        if getattr(self.game, "aguardando_dialogo_pos_dragao", False):
            despertar_inativo = (not hasattr(self.game, "tela_despertar") or self.game.tela_despertar.estado == "INATIVO")
            if despertar_inativo and self.memoria_anterior_registrada >= 2:
                self.game.aguardando_dialogo_pos_dragao = False
                self.game.caixa_dialogo.iniciar_dialogo("pos_vitoria_dragao_oakhaven")
                return

        # Em ORLA_NORTE: onde o Guarda Doran levou Halia para enfrentar os 2 Batedores Demoníacos
        if self.game.mapa_casa.cenario_atual == "ORLA_NORTE":
            # Se Halia caminhar de volta pelo portão sul da clareira, retorna a Oakhaven
            if self.game.halia.y > 660 and not getattr(self.game, "combate_climax_dragao", False):
                self.game.inimigos_em_cena.clear()
                self.game.mapa_casa.carregar_cenario("OAKHAVEN")
                self.game.halia.x, self.game.halia.y = 1102, 245
                self.game.halia.direcao = "baixo"
                self.game.halia.mudar_estado("idle")
                self.atualizar_camera(instantaneo=True)
                return

            # Se Halia se aproximar dos batedores na clareira da Orla Norte, inicia o combate de patrulha
            if self.game.inimigos_em_cena and not self.game.iniciando_combate:
                area_halia = pygame.Rect(int(self.game.halia.x - 28), int(self.game.halia.y - 28), self.game.halia.largura + 56, self.game.halia.altura + 56)
                for inim in self.game.inimigos_em_cena:
                    r_inim = pygame.Rect(int(inim.x), int(inim.y), inim.largura, inim.altura)
                    if area_halia.colliderect(r_inim):
                        # Revela a verdadeira forma feroz de mímico para o combate
                        for inim_alvo in self.game.inimigos_em_cena:
                            if getattr(inim_alvo, "eh_mimico", False):
                                inim_alvo.finalizar_revelacao()
                        self.game.iniciando_combate = True
                        self.game.transicao.iniciar()
                        break

    def _mover_carroceiro_autonomo(self):
        next_h = pygame.Rect(int(self.game.carroceiro.x - 2), int(self.game.carroceiro.y), self.game.carroceiro.largura, self.game.carroceiro.altura)
        h_halia = pygame.Rect(int(self.game.halia.x), int(self.game.halia.y), self.game.halia.largura, self.game.halia.altura)
        if not next_h.colliderect(h_halia): self.game.carroceiro.mover(-1, 0, [])
        if self.game.carroceiro.x <= 900 or next_h.colliderect(h_halia):
            if self.game.carroceiro.x <= 900: self.game.carroceiro.x = 900
            self.game.carroceiro_andando = False
            self.game.carroceiro.velocidade = 0
            self.game.carroceiro.mudar_estado("idle")
            self.game.carroceiro.virado_direita = (self.game.halia.x > self.game.carroceiro.x)
            h_npc = pygame.Rect(int(self.game.carroceiro.x), int(self.game.carroceiro.y), self.game.carroceiro.largura, self.game.carroceiro.altura)
            if h_npc not in self.game.mapa_casa.hitboxes: self.game.mapa_casa.hitboxes.append(h_npc)

    def _processar_avanco_dialogo(self):
        abrir_loja_apos = False
        loja_id_alvo = None
        ir_patrulha_apos = False
        if self.game.caixa_dialogo.em_escolha:
            if self.game.caixa_dialogo.opcoes_disponiveis and 0 <= self.game.caixa_dialogo.opcao_selecionada < len(self.game.caixa_dialogo.opcoes_disponiveis):
                opcao_atual = self.game.caixa_dialogo.opcoes_disponiveis[self.game.caixa_dialogo.opcao_selecionada]
                opt_id = opcao_atual.get("id")
                if opt_id == "analisar_pedras":
                    self.game.caixa_dialogo.ativo = False
                    self.game.caixa_dialogo.em_escolha = False
                    seq_flashback = self.game.caixa_dialogo.manager.obter_sequencia_linear("flashback_magia")
                    self.game.flashback_sistema.iniciar(seq_flashback, game=self.game)
                    return
                elif opt_id == "recordar_amigos_monumento":
                    self.game.caixa_dialogo.ativo = False
                    self.game.caixa_dialogo.em_escolha = False
                    seq_sylvan = self.game.caixa_dialogo.manager.obter_sequencia_linear("flashback_memoria_2_sylvan")
                    self.game.flashback_monumento_ativo = True
                    self.game.flashback_sistema.iniciar(seq_sylvan, tipo="acampamento", game=self.game)
                    return
                elif opt_id == "sair_monumento":
                    self.game.caixa_dialogo.ativo = False
                    self.game.caixa_dialogo.em_escolha = False
                    return
                elif opt_id == "escolha_fogo":
                    self.game.magia_selecionada_temporaria = "FOGO"
                elif opt_id == "escolha_levitar":
                    self.game.magia_selecionada_temporaria = "LEVITAR"
                elif opt_id in ["voltar_magia", "desistir_puzzle"]:
                    self.game.investigou_pedras = False
                elif opt_id == "prosseguir":
                    self.game.aguardando_fim_viagem = True
                elif opt_id == "seguir_capital":
                    self.game.partindo_estrada2 = True
                elif opcao_atual.get("acao") == "abrir_loja" or opcao_atual.get("evento") == "abrir_loja":
                    abrir_loja_apos = True
                    loja_id_alvo = opcao_atual.get("loja_id")
                elif opcao_atual.get("acao") == "ir_patrulha_doran" or opcao_atual.get("evento") == "ir_patrulha_doran":
                    ir_patrulha_apos = True
        self.game.caixa_dialogo.proximo_texto()
        evt_atual = getattr(self.game.caixa_dialogo.manager, "evento_pendente", None)
        if abrir_loja_apos or evt_atual == "abrir_loja":
            self.game.caixa_dialogo.manager.consumir_evento()
            if not loja_id_alvo and hasattr(self.game, "npc_interagindo_atual") and self.game.npc_interagindo_atual:
                loja_id_alvo = getattr(self.game.npc_interagindo_atual, "loja_id", None)

            # Validação estrita de pré-requisitos da loja do NPC
            npc_atual = getattr(self.game, "npc_interagindo_atual", None)
            pode_abrir = True
            qm = getattr(self.game, "missoes", None)
            if npc_atual and hasattr(npc_atual, "pode_abrir_loja"):
                pode_abrir = npc_atual.pode_abrir_loja(qm)
            elif loja_id_alvo and qm and hasattr(qm, "missoes"):
                norm_l = str(loja_id_alvo).lower()
                if "forja" in norm_l or "torvald" in norm_l:
                    pode_abrir = (qm.missoes.get("missao_pedra_forja", {}).get("status") == "CONCLUIDA")
                elif "botanica" in norm_l or "elara" in norm_l:
                    pode_abrir = (qm.missoes.get("missao_ervas_medicinais", {}).get("status") == "CONCLUIDA")

            self.game.caixa_dialogo.ativo = False
            if pode_abrir:
                if hasattr(self.game, "missoes") and self.game.missoes:
                    self.game.missoes.atualizar_progresso("conhecer_mercado", 1)
                    self.game.missoes.atualizar_progresso("visitar_mercado", 1)
                if hasattr(self.game, "abrir_loja"):
                    self.game.abrir_loja(loja_id_alvo)
                else:
                    self.game.mudar_estado("LOJA")
        elif ir_patrulha_apos or (not self.game.caixa_dialogo.ativo and evt_atual == "ir_patrulha_doran"):
            self.game.caixa_dialogo.manager.consumir_evento()
            self.game.caixa_dialogo.ativo = False
            self._ir_para_patrulha_orla_norte()
        elif evt_atual == "cura_elara_missao":
            self.game.caixa_dialogo.manager.consumir_evento()
            if hasattr(self.game, "halia") and self.game.halia:
                self.game.halia.restaurar_total()
            if hasattr(self.game, "missoes") and self.game.missoes:
                if self.game.missoes.missoes.get("missao_ervas_medicinais", {}).get("status") != "CONCLUIDA":
                    self.game.missoes.concluir_missao("missao_ervas_medicinais")
        elif not self.game.caixa_dialogo.ativo and evt_atual == "iniciar_cutscene_dormir_vila":
            self.game.caixa_dialogo.manager.consumir_evento()
            self.game.caixa_dialogo.ativo = False
            if hasattr(self, "cinematica_dragao"):
                self.cinematica_dragao.iniciar_sono()
        elif not self.game.caixa_dialogo.ativo and evt_atual == "iniciar_amanhecer_ataque_dragao":
            self.game.caixa_dialogo.manager.consumir_evento()
            self.game.caixa_dialogo.ativo = False
            if hasattr(self, "cinematica_dragao"):
                self.cinematica_dragao.iniciar_ataque_aereo()
            else:
                self._iniciar_amanhecer_ataque_dragao()
        elif not self.game.caixa_dialogo.ativo and evt_atual in ("ir_para_ninho_dragao", "iniciar_climax_dragao_oakhaven"):
            self.game.caixa_dialogo.manager.consumir_evento()
            self.game.caixa_dialogo.ativo = False
            self._iniciar_climax_dragao_oakhaven()
        elif not self.game.caixa_dialogo.ativo and evt_atual == "iniciar_combate_dragao_oakhaven":
            self.game.caixa_dialogo.manager.consumir_evento()
            self.game.caixa_dialogo.ativo = False
            self.game.combate_climax_dragao = True
            self.game.iniciando_combate = True
            self.game.transicao.iniciar()
        elif not self.game.caixa_dialogo.ativo and evt_atual == "iniciar_flashback_sylvan_ninho":
            self.game.caixa_dialogo.manager.consumir_evento()
            self.game.caixa_dialogo.ativo = False
            seq_sylvan = self.game.caixa_dialogo.manager.obter_sequencia_linear("flashback_memoria_2_sylvan")
            self.game.flashback_sylvan_ativo = True
            self.game.flashback_sistema.iniciar(seq_sylvan, tipo="acampamento", game=self.game)
        elif not self.game.caixa_dialogo.ativo and evt_atual == "retornar_oakhaven_vitoria":
            self.game.caixa_dialogo.manager.consumir_evento()
            self.game.caixa_dialogo.ativo = False
            self.game.transicao.iniciar("Retornando vitoriosa a Oakhaven...")
            cenario_retorno = "OAKHAVEN_DESTRUIDA" if getattr(self.game, "oakhaven_destruida", True) else "OAKHAVEN"
            self.game.mapa_casa.carregar_cenario(cenario_retorno)
            self.game.halia.x, self.game.halia.y = 1102, 660
            self.game.halia.direcao = "cima"
            self.game.halia.mudar_estado("idle")
            self.atualizar_camera(instantaneo=True)
            self.game.aguardando_dialogo_pos_dragao = True
            if self.game.slot_atual:
                self.game.salvar_estado(self.game.slot_atual, tipo="autosave")
        elif not self.game.caixa_dialogo.ativo and evt_atual == "iniciar_timeskip_final_oakhaven":
            self.game.caixa_dialogo.manager.consumir_evento()
            self.game.caixa_dialogo.ativo = False
            if hasattr(self, "cutscene_reconstrucao"):
                self.cutscene_reconstrucao.iniciar()

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
        area_interacao = pygame.Rect(self.game.halia.x - 24, self.game.halia.y - 24, self.game.halia.largura + 48, self.game.halia.altura + 48)
        
        for item in self.game.mapa_casa.itens_no_chao[:]: 
            if area_interacao.colliderect(item.rect):
                id_do_item = getattr(item, "id_unico", "desconhecido")
                if str(id_do_item).startswith("erva_lunar"):
                    self.minigame_curandeira.iniciar(item)
                    return

                self.game.mapa_casa.itens_no_chao.remove(item)
                if hasattr(self.game, 'audio') and self.game.audio:
                    self.game.audio.tocar_sfx("item_coletar")
                
                id_do_item = getattr(item, "id_unico", "desconhecido")
                if id_do_item not in self.game.itens_coletados:
                    self.game.itens_coletados.append(id_do_item)
                
                if id_do_item == "item_moedas":
                    self.game.halia.ganhar_dinheiro(50 * self.game.halia.COBRES_POR_OURO) # 50 Moedas de Ouro = 10.000 Cobres
                    self.game.caixa_dialogo.iniciar_dialogo([{"autor": "Sistema", "texto": "Você encontrou a Bolsa de Moedas com 50 moedas de ouro."}])
                elif id_do_item == "item_cajado":
                    cajado = ItemFactory.criar("cajado_espinheiro")
                    if cajado:
                        self.game.halia.inventario.equipados["CAJADO"] = cajado
                    self.game.halia.recalcular_status_derivados()
                    self.game.caixa_dialogo.iniciar_dialogo([{"autor": "Sistema", "texto": "Você empunhou o Cajado de Espinheiro."}])
                elif id_do_item == "item_livro":
                    tomo = ItemFactory.criar("tomo_chama_ancestral")
                    if tomo:
                        self.game.halia.inventario.equipados["GRIMORIO_1"] = tomo
                    self.game.caixa_dialogo.iniciar_dialogo([{"autor": "Sistema", "texto": "Você recolheu o Livro Antigo contendo encantamentos arcanos esquecidos."}])
                else:
                    self.game.caixa_dialogo.iniciar_dialogo([{"autor": "Sistema", "texto": f"Você guardou: {item.nome}."}])
                return
        
        if self.game.mapa_casa.cenario_atual == "CASA" and area_interacao.colliderect(self.game.mapa_casa.porta) and not self.game.mapa_casa.porta_aberta:
            if len(self.game.mapa_casa.itens_no_chao) == 0:
                self.game.mapa_casa.abrir_porta()
                self.game.caixa_dialogo.iniciar_dialogo("porta_abriu")
            else:
                self.game.caixa_dialogo.iniciar_dialogo("porta_trancada")
            return

        if self.game.mapa_casa.cenario_atual in ["ESTRADA", "ESTRADA_2"] and self.game.carroceiro_visivel:
            if area_interacao.colliderect(pygame.Rect(self.game.carroceiro.x, self.game.carroceiro.y, self.game.carroceiro.largura, self.game.carroceiro.altura)):
                self.game.carroceiro.virado_direita = (self.game.halia.x > self.game.carroceiro.x)
                self.game.halia.virado_direita = (self.game.carroceiro.x > self.game.halia.x)
                if self.game.mapa_casa.cenario_atual == "ESTRADA":
                    self.game.caixa_dialogo.iniciar_dialogo("hub_carroceiro")
                elif self.game.mapa_casa.cenario_atual == "ESTRADA_2":
                    if getattr(self.game, 'combate_estrada_concluido', False):
                        self.game.caixa_dialogo.iniciar_dialogo("carroceiro_pos_combate")
                    elif self.game.magia_ativa == "CONCLUIDO":
                        self.game.caixa_dialogo.iniciar_dialogo("carroceiro_pos_puzzle")
                    else:
                        self.game.caixa_dialogo.iniciar_dialogo("carroceiro_impedimento")
                return

        if self.game.mapa_casa.cenario_atual == "ESTRADA_2" and self.game.magia_ativa != "CONCLUIDO" and not getattr(self.game, 'combate_estrada_concluido', False):
            if self.game.halia.x >= 950:
                self.game.investigou_pedras = True
                if self.game.flashback_magia_concluido:
                    self.game.caixa_dialogo.iniciar_dialogo("escolha_magias")
                else:
                    self.game.caixa_dialogo.iniciar_dialogo("investigar_pedras")
                return

        # Interações com NPCs do cenário ativo (ex: Oakhaven)
        for npc in getattr(self.game.mapa_casa, "npcs", []):
            r_npc = pygame.Rect(int(npc.x - 10), int(npc.y - 10), npc.largura + 20, npc.altura + 20)
            if area_interacao.colliderect(r_npc):
                self.game.npc_interagindo_atual = npc
                npc.virado_direita = (self.game.halia.x > npc.x)
                self.game.halia.virado_direita = (npc.x > self.game.halia.x)
                if hasattr(self.game, "missoes") and self.game.missoes:
                    if npc.npc_id in ("curandeira_elara", "ferreiro_torvald"):
                        self.game.missoes.atualizar_progresso("conhecer_mercado", 1)
                        self.game.missoes.atualizar_progresso("visitar_mercado", 1)
                npc.interagir(self.game)
                return

        # Interação com Patusco (Easter Egg 1/7 no tufo de grama - desativado à noite pois ele já dorme)
        eh_noite = getattr(self.game, "oakhaven_noite", False)
        if not eh_noite:
            for animal in getattr(self.game.mapa_casa, "animais", []):
                if hasattr(animal, "interagir") and getattr(animal, "visivel", True):
                    r_anim = pygame.Rect(int(animal.x - 24), int(animal.y - 24), 48, 48)
                    if area_interacao.colliderect(r_anim):
                        animal.interagir(self.game)
                        return

        # Interação com pontos de lore e objetos de missão no cenário (Monumento, Quadro, Rocha de Minério)
        for pt in getattr(self.game.mapa_casa, "pontos_interacao", []):
            if area_interacao.colliderect(pt["rect"]):
                if pt.get("id") == "rocha_minerio_torvald":
                    estado_missao = (
                        (self.game.missoes.obter_missao("missao_pedra_forja") or {}).get("status", "NAO_INICIADA")
                        if hasattr(self.game, "missoes") and self.game.missoes
                        else "NAO_INICIADA"
                    )
                    if estado_missao == "ATIVA" and not getattr(self.game, "pedra_torvald_quebrada", False):
                        self.minigame_ferraria.iniciar()
                        return
                    else:
                        self.game.caixa_dialogo.iniciar_dialogo([
                            {
                                "autor": "Narrador",
                                "texto": "Um grande bloco de minério bruto com veios metálicos azulados repousa no pátio da forja. O Ferreiro Torvald parece precisar de auxílio para parti-lo."
                            }
                        ])
                        return
                    return
                if "evento" in pt:
                    ev = pt["evento"]
                    if ev == "retornar_oakhaven_vitoria":
                        self.game.transicao.iniciar("Retornando vitoriosa a Oakhaven...")
                        cenario_retorno = "OAKHAVEN_DESTRUIDA" if getattr(self.game, "oakhaven_destruida", True) else "OAKHAVEN"
                        self.game.mapa_casa.carregar_cenario(cenario_retorno)
                        self.game.halia.x, self.game.halia.y = 1102, 660
                        self.game.halia.direcao = "cima"
                        self.game.halia.mudar_estado("idle")
                        self.atualizar_camera(instantaneo=True)
                        self.game.aguardando_dialogo_pos_dragao = True
                        if self.game.slot_atual:
                            self.game.salvar_estado(self.game.slot_atual, tipo="autosave")
                        return
                    elif ev == "iniciar_climax_dragao_oakhaven":
                        self._iniciar_climax_dragao_oakhaven()
                        return
                if pt.get("id") == "estatua_herois":
                    self.game.caixa_dialogo.iniciar_dialogo("monumento_herois")
                    return
                if "dialogo" in pt:
                    self.game.caixa_dialogo.iniciar_dialogo(pt["dialogo"])
                    return

    def _update_transitions(self):
        if self.game.transicao.update() if hasattr(self.game.transicao, 'update') else self.game.transicao.atualizar():
            if self.game.iniciando_combate:
                self.game.iniciando_combate = False
                self.game.transicao.estado = "CLAREANDO"
                cenario_combate = self.game.mapa_casa.cenario_atual

                def on_vitoria():
                    if getattr(self.game, "combate_climax_dragao", False):
                        self.game.combate_climax_dragao = False
                        self.game.inimigos_em_cena.clear()
                        self.game.cena_inimigos_andando = False
                        self.game.oakhaven_noite = False  # A longa noite de batalha terminou: rompe a alvorada!
                        self.game.dragao_derrotado = True
                        self.game.desespero_superado = True
                        
                        # Halia permanece no NINHO_DRAGAO contemplando exausta o corpo do dragão ao amanhecer
                        self.game.mapa_casa.carregar_cenario("NINHO_DRAGAO")
                        ninho = self.game.mapa_casa.cenario_objeto
                        ninho.ninho_amanhecer = True
                        ninho.dragao_derrotado = True
                        ninho.inicializar_cenario()
                        
                        self.game.halia.x, self.game.halia.y = 610, 380
                        self.game.halia.direcao = "cima"
                        self.game.halia.mudar_estado("idle")
                        self.atualizar_camera(instantaneo=True)
                        
                        if hasattr(self.game, "audio") and self.game.audio:
                            self.game.audio.tocar_ambiente("vento_suave", loop=-1, fade_ms=1000)
                            
                        self.game.mudar_estado("JOGANDO")
                        self.game.caixa_dialogo.iniciar_dialogo("cena_pos_combate_ninho_dragao")
                        return

                    if cenario_combate in ("OAKHAVEN", "ORLA_NORTE"):
                        self.game.inimigos_em_cena.clear()
                        self.game.cena_inimigos_andando = False
                        self.game.oakhaven_noite = True
                        if hasattr(self.game, "missoes") and self.game.missoes:
                            self.game.missoes.atualizar_progresso("derrotar_demonios", 2)
                            self.game.missoes.atualizar_progresso("derrotar_sombras", 2)
                        self.game.mapa_casa.carregar_cenario("OAKHAVEN")
                        self.game.halia.x, self.game.halia.y = 1102, 265
                        self.game.halia.direcao = "cima"
                        self.game.halia.mudar_estado("idle")
                        self.atualizar_camera(instantaneo=True)
                        if self.game.slot_atual:
                            self.game.salvar_estado(self.game.slot_atual, tipo="autosave")
                        self.game.mudar_estado("JOGANDO")
                        self.game.caixa_dialogo.iniciar_dialogo([
                            {"autor": "Guarda Doran", "texto": "Excelente combate, Halia! Aqueles soldados caídos eram na verdade Mímicos ferozes disfarçados... Que emboscada hedionda! Já caiu a noite sobre Oakhaven quando retornamos — fale comigo aqui no Portão Norte para encerrarmos a ronda!"}
                        ])
                        return

                    self.game.combate_estrada_concluido = True
                    self.game.magia_ativa = "CONCLUIDO"
                    self.game.mapa_casa.desobstruir_estrada(self.game.magia_usada_no_puzzle or "FOGO")
                    teve_chefe = any(getattr(i, 'eh_chefe', False) or "superior" in getattr(i, 'nome', '').lower() for i in self.game.inimigos_em_cena)
                    self.game.inimigos_em_cena.clear()
                    self.game.cena_inimigos_andando = False
                    if hasattr(self.game, 'conquistas') and self.game.conquistas:
                        self.game.conquistas.desbloquear("primeiro_sangue")
                        if teve_chefe:
                            self.game.conquistas.desbloquear("cacadora_abissal")
                    self.game.mudar_estado("JOGANDO")
                    self.game.caixa_dialogo.iniciar_dialogo("pos_combate_vitoria")
                    
                def on_derrota():
                    self.on_derrota()
                    
                def on_fuga():
                    if cenario_combate in ("OAKHAVEN", "ORLA_NORTE"):
                        self.game.inimigos_em_cena.clear()
                        self.game.mapa_casa.carregar_cenario("OAKHAVEN")
                        self.game.halia.x, self.game.halia.y = 1102, 280
                        self.atualizar_camera(instantaneo=True)
                    else:
                        self.game.halia.x = max(60, self.game.halia.x - 120)
                        self.game.inimigos_em_cena.clear()
                    self.game.cena_inimigos_andando = False
                    self.game.mudar_estado("JOGANDO")

                # Garante que durante o combate o mímico permaneça na sua forma feroz revelada
                for inim_combate in self.game.inimigos_em_cena:
                    if getattr(inim_combate, "eh_mimico", False):
                        inim_combate.finalizar_revelacao()

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
            self.game.combate_estrada_concluido = False
            self.game.inimigos_em_cena.clear()
            self.game.cena_inimigos_andando = False
            self.game.iniciando_combate = False
            self.game.halia.restaurar_total()
            self.game.magia_ativa = None
            self.game.investigou_pedras = False
            self.game.bola_fogo_ativa = False
            self.game.mapa_casa.restaurar_bloqueio_estrada2()

        self.game.mudar_estado("JOGANDO")

    def _entrar_na_estrada_1(self):
        self.game.mapa_casa.carregar_cenario("ESTRADA")
        self.game.halia.x, self.game.halia.y = 40, 330
        self.atualizar_camera(instantaneo=True)
        if not getattr(self.game, 'conversa_carroceiro_terminou', False):
            self.game.carroceiro_visivel = False
            self.game.carroceiro_andando = False
            self.game.carroceiro.x, self.game.carroceiro.y = 1350, 330
            self.game.carroceiro.velocidade = 2
            self.game.carroceiro.mudar_estado("idle")
        if self.game.slot_atual:
            self.game.salvar_estado(self.game.slot_atual, tipo="autosave")
        pygame.event.clear()
        self.game.caixa_dialogo.iniciar_dialogo("entrada_estrada1")
        self.game.transicao.estado = "CLAREANDO"

    def _entrar_na_estrada_2(self):
        if not (self.game.magia_ativa == "CONCLUIDO" or self.game.combate_estrada_concluido):
            self.game.mapa_casa.restaurar_bloqueio_estrada2()
        self.game.mapa_casa.carregar_cenario("ESTRADA_2")
        self.game.conversa_carroceiro_terminou = False; self.game.aguardando_fim_viagem = False
        self.game.magia_ativa = None; self.game.bola_fogo_ativa = False; self.game.cena_inimigos_andando = False
        self.game.inimigos_em_cena.clear()
        
        self.game.halia.x, self.game.halia.y = 60, 330
        self.atualizar_camera(instantaneo=True)
        self.game.carroceiro_visivel, self.game.carroceiro_andando = True, False
        self.game.carroceiro.velocidade, self.game.carroceiro.x, self.game.carroceiro.y = 0, 200, 330
        self.game.carroceiro.mudar_estado("idle")
        self.game.carroceiro.virado_direita = (self.game.halia.x > self.game.carroceiro.x)
        
        h_npc = pygame.Rect(int(self.game.carroceiro.x), int(self.game.carroceiro.y), self.game.carroceiro.largura, self.game.carroceiro.altura)
        if h_npc not in self.game.mapa_casa.hitboxes: self.game.mapa_casa.hitboxes.append(h_npc)
        
        if self.game.slot_atual:
            self.game.salvar_estado(self.game.slot_atual, tipo="autosave")
            
        pygame.event.clear()
        self.game.caixa_dialogo.iniciar_dialogo("entrada_estrada2")
        self.game.transicao.estado = "CLAREANDO"

    def _entrar_em_oakhaven(self):
        """Transiciona Halia para a entrada sul da Vila de Oakhaven (Fase 1)."""
        self.game.mapa_casa.carregar_cenario("OAKHAVEN")
        self.game.carroceiro_visivel = False
        self.game.carroceiro_andando = False
        self.game.cena_inimigos_andando = False
        self.game.inimigos_em_cena.clear()
        self.game.halia.x, self.game.halia.y = 1102, 1320
        self.game.halia.direcao = "cima"
        self.game.halia.mudar_estado("idle")
        self.atualizar_camera(instantaneo=True)

        if self.game.slot_atual:
            self.game.salvar_estado(self.game.slot_atual, tipo="autosave")

        pygame.event.clear()
        self.game.caixa_dialogo.iniciar_dialogo([
            {
                "autor": "Narrador",
                "texto": "As cores suaves do entardecer tocam os telhados de Oakhaven. No centro da praça à frente, ergue-se um monumento de pedra onde o Ancião Aldous aguarda em silêncio."
            }
        ])
        self.game.transicao.estado = "CLAREANDO"

    def _ir_para_patrulha_orla_norte(self):
        """
        O Guarda Doran conduz Halia pelo Portão Norte até a clareira da Orla Norte ('ORLA_NORTE'),
        onde os 2 Batedores Demoníacos estão escondidos.
        """
        self.game.mapa_casa.carregar_cenario("ORLA_NORTE")
        self.game.cena_inimigos_andando = False
        self.game.inimigos_em_cena.clear()
        self.game.halia.x, self.game.halia.y = 610, 520
        self.game.halia.direcao = "cima"
        self.game.halia.mudar_estado("idle")
        self.atualizar_camera(instantaneo=True)

        if self.game.slot_atual:
            self.game.salvar_estado(self.game.slot_atual, tipo="autosave")

        batedor1 = EnemyFactory.criar("mimico", x=565, y=285, nome_custom="Mímico Batedor 1")
        batedor2 = EnemyFactory.criar("mimico", x=665, y=305, nome_custom="Mímico Batedor 2")
        for bat in (batedor1, batedor2):
            bat.velocidade = 0
            bat.virado_direita = False
            bat.direcao = "esquerda"
            bat.recompensas = {"moedas": 25, "memorias": 0, "xp": 45}
            bat.disfarcado = True
            bat.revelado = False
            bat.revelando = False
            bat.mudar_estado("corpo")
        self.game.inimigos_em_cena.extend([batedor1, batedor2])

        self.game.caixa_dialogo.iniciar_dialogo([
            {
                "autor": "Guarda Doran",
                "texto": "Chegamos à clareira, Halia! Aqueles dois parecem corpos de soldados da patrulha caídos na grama... Mas sinto um miasma maligno no ar. Aproxime-se com cautela para investigar!"
            }
        ])

    def _iniciar_amanhecer_ataque_dragao(self):
        """
        Após o repouso noturno em Oakhaven, Halia acorda na calada da noite com
        Ignis'Vahr, o Dragão Vermelho Ancestral, atacando e destruindo a vila ('OAKHAVEN_DESTRUIDA').
        """
        self.game.oakhaven_noite = True
        self.game.oakhaven_destruida = True
        self.game.mapa_casa.carregar_cenario("OAKHAVEN_DESTRUIDA")
        self.game.cena_inimigos_andando = False
        self.game.inimigos_em_cena.clear()
        self.game.halia.x, self.game.halia.y = 1102, 660
        self.game.halia.direcao = "cima"
        self.game.halia.mudar_estado("idle")
        self.atualizar_camera(instantaneo=True)

        if self.game.slot_atual:
            self.game.salvar_estado(self.game.slot_atual, tipo="autosave")

        if hasattr(self.game, "audio") and self.game.audio:
            self.game.audio.tocar_musica("combate_dragao", loop=-1, fade_ms=800)

        self.game.caixa_dialogo.iniciar_dialogo("despertar_ataque_dragao_vila")

    def _iniciar_climax_dragao_oakhaven(self):
        """
        Inicia o Clímax da Fase 1 no Ninho do Dragão ('NINHO_DRAGAO') durante a noite:
        Ignis'Vahr, o Dragão Vermelho Ancestral, aguarda nos penhascos vulcânicos, desencadeando
        a Crise de Ansiedade 1 (Trauma do Fogo) + Ancoragem Sensorial antes da Batalha de Chefe.
        """
        self.game.oakhaven_noite = True
        self.game.mapa_casa.carregar_cenario("NINHO_DRAGAO")
        self.game.cena_inimigos_andando = False
        self.game.inimigos_em_cena.clear()
        self.game.halia.x, self.game.halia.y = 610, 520
        self.game.halia.direcao = "cima"
        self.game.halia.mudar_estado("idle")
        self.atualizar_camera(instantaneo=True)

        if self.game.slot_atual:
            self.game.salvar_estado(self.game.slot_atual, tipo="autosave")

        ninho = self.game.mapa_casa.cenario_objeto
        ninho.ninho_amanhecer = False
        ninho.dragao_derrotado = False
        ninho.inicializar_cenario()

        dragao = EnemyFactory.criar_boss("dragao_vermelho", x=525, y=145, nome_custom="Ignis'Vahr, o Dragão Vermelho")
        dragao.velocidade = 0
        dragao.virado_direita = False
        dragao.direcao = "esquerda"
        self.game.inimigos_em_cena.append(dragao)

        if hasattr(self.game, "audio") and self.game.audio:
            self.game.audio.tocar_musica("combate_dragao", loop=-1, fade_ms=800)

        self.game.caixa_dialogo.iniciar_dialogo("crise_ansiedade_dragao_oakhaven")

    def _ir_para_ninho_dragao(self):
        """Alias semântico para transportar Halia de Oakhaven destruída até o Ninho do Dragão."""
        self._iniciar_climax_dragao_oakhaven()

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
            if self.game.mapa_casa.cenario_atual == "CASA" and area_interacao.colliderect(self.game.mapa_casa.porta) and not self.game.mapa_casa.porta_aberta:
                desenhar_indicador_tecla(tela, self.game.mapa_casa.porta.x + (self.game.mapa_casa.porta.width // 2), self.game.mapa_casa.porta.y - 34, tecla=tecla_interacao_str, acao="para Abrir")

        if self.game.mapa_casa.cenario_atual in ["ESTRADA", "ESTRADA_2"] and self.game.carroceiro_visivel:
            r_c = pygame.Rect(self.game.carroceiro.x, self.game.carroceiro.y, self.game.carroceiro.largura, self.game.carroceiro.altura)
            if area_interacao.colliderect(r_c) and not bloqueado_geral:
                desenhar_indicador_tecla(tela, self.game.carroceiro.x + (self.game.carroceiro.largura // 2), self.game.carroceiro.y - 38, tecla=tecla_interacao_str, acao="para Conversar")

        if self.game.mapa_casa.cenario_atual == "ESTRADA_2" and self.game.magia_ativa != "CONCLUIDO" and not getattr(self.game, 'combate_estrada_concluido', False):
            if self.game.halia.x >= 950 and not bloqueado_geral:
                txt_acao = "para Usar Magia" if self.game.flashback_magia_concluido else "para Investigar"
                desenhar_indicador_tecla(tela, 1070, 200, tecla=tecla_interacao_str, acao=txt_acao)

        if not self.game.caixa_dialogo.ativo and not self.game.flashback_sistema.ativo:
            for npc in getattr(self.game.mapa_casa, "npcs", []):
                r_npc = pygame.Rect(int(npc.x - 10), int(npc.y - 10), npc.largura + 20, npc.altura + 20)
                if area_interacao.colliderect(r_npc):
                    topo_y = npc.obter_topo_cabeca() if hasattr(npc, "obter_topo_cabeca") else int(npc.y - 42)
                    prompt_y = int(topo_y - 34)
                    desenhar_indicador_tecla(tela, int(npc.x + npc.largura // 2), prompt_y, tecla=tecla_interacao_str, acao=f"Falar com {npc.nome}")
                    return

            if not getattr(self.game, "oakhaven_noite", False):
                for animal in getattr(self.game.mapa_casa, "animais", []):
                    if hasattr(animal, "interagir") and getattr(animal, "visivel", True):
                        r_anim = pygame.Rect(int(animal.x - 24), int(animal.y - 24), 48, 48)
                        if area_interacao.colliderect(r_anim):
                            desenhar_indicador_tecla(tela, int(animal.x), int(animal.y - 62), tecla=tecla_interacao_str, acao="para Acariciar Patusco")
                            return

            for pt in getattr(self.game.mapa_casa, "pontos_interacao", []):
                if area_interacao.colliderect(pt["rect"]):
                    desenhar_indicador_tecla(tela, pt["prompt_x"], pt["prompt_y"], tecla=tecla_interacao_str, acao=pt["acao_texto"])
                    return

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
        
        # O HUD deve ser desenhado normalmente quando não houver minigames, diálogos ou telas de despertar ou timeskip
        timeskip_ativo = getattr(getattr(self, 'cutscene_reconstrucao', None), 'ativo', False)
        if hasattr(self.game, 'hud') and not minigame_ativo and not self.game.caixa_dialogo.ativo and getattr(self.game.tela_despertar, 'estado', 'INATIVO') == 'INATIVO' and not timeskip_ativo:
            self.game.hud.desenhar(tela, self.game)

        # Quest Tracker no Canto Superior Direito da Tela
        if hasattr(self.game, 'quest_tracker') and not minigame_ativo and not self.game.caixa_dialogo.ativo and getattr(self.game.tela_despertar, 'estado', 'INATIVO') == 'INATIVO' and not timeskip_ativo:
            self.game.quest_tracker.desenhar(tela, self.game)
