# src/mechanics/minigame_curandeira.py
import pygame
import math
import random
import os
import sys

# Garante path raiz de Oblivium
_raiz = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _raiz not in sys.path:
    sys.path.insert(0, _raiz)

from src.utils.resource_manager import ResourceManager
from src.utils.colors import (
    CARVAO_PROFUNDO, CINZA_ARDOSIA, CINZA_ESCURO, CINZA_LINHO,
    MARFIM_OFFWHITE, DOURADO_ENVELHECIDO, AZUL_HOVER_MENU
)


class ParticulaPetala:
    """Partícula leve que simula pétalas luminescentes e gotas de orvalho místico."""
    __slots__ = ("x", "y", "vx", "vy", "vida", "vida_max", "cor", "raio", "angulo", "v_rot", "gravidade", "fase_seno")

    def __init__(self, x, y, vx, vy, vida, cor, raio=3.0, gravidade=-0.08):
        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)
        self.vy = float(vy)
        self.vida = float(vida)
        self.vida_max = float(vida)
        self.cor = cor
        self.raio = float(raio)
        self.angulo = random.uniform(0, 360)
        self.v_rot = random.uniform(-4.0, 4.0)
        self.gravidade = float(gravidade)
        self.fase_seno = random.uniform(0, math.pi * 2)

    def atualizar(self, dt=1.0):
        self.vida -= dt
        self.fase_seno += 0.08 * dt
        self.x += (self.vx + math.sin(self.fase_seno) * 0.7) * dt
        self.y += self.vy * dt
        self.vy += self.gravidade * dt
        self.angulo += self.v_rot * dt
        return self.vida > 0

    def desenhar(self, tela):
        ratio = max(0.0, min(1.0, self.vida / self.vida_max))
        alpha = int(255 * ratio)
        raio_atual = max(1, int(self.raio * ratio))

        surf = pygame.Surface((raio_atual * 3, raio_atual * 3), pygame.SRCALPHA)
        cor_rgba = (*self.cor[:3], alpha)
        cx, cy = raio_atual * 1.5, raio_atual * 1.5

        # Pétala ovalada ou gota
        pygame.draw.ellipse(surf, cor_rgba, (cx - raio_atual, cy - raio_atual * 1.4, raio_atual * 2, raio_atual * 2.8))
        tela.blit(surf, (int(self.x) - cx, int(self.y) - cy))


class MinigameCurandeira:
    """
    Minigame Interativo da Curandeira Elara: Colheita Sensível da Erva Lunar.
    - Mecânica de anel de precisão dinâmico concêntrico.
    - O anel externo de orvalho lunar contrai-se em direção à circunferência alvo de ressonância.
    - Acerto no ponto ideal (com margem de tolerância) preserva as raízes e nós luminescentes,
      desencadeando dispersão de orvalho, adição do item ao inventário e avanço da missão.
    """
    def __init__(self, game, playing_state=None):
        self.game = game
        self.playing_state = playing_state
        self.largura = 1280
        self.altura = 720

        # Estados: 'INATIVO', 'JOGANDO', 'SUCESSO_ANIMACAO', 'CONCLUIDO'
        self.estado = "INATIVO"
        self.ativo = False
        self.item_alvo = None

        # Fontes
        self.fonte_titulo = ResourceManager.carregar_fonte("sunday", 30)
        self.fonte_sub = ResourceManager.carregar_fonte("contrail", 18)
        self.fonte_destaque = ResourceManager.carregar_fonte("sunday", 22)
        self.fonte_aviso = ResourceManager.carregar_fonte("contrail", 16)

        # Geometria dos Anéis (Centro da Flor: 640, 315)
        self.centro_x = 640
        self.centro_y = 315
        self.raio_alvo = 70.0
        self.tolerancia = 12.0
        self.raio_max = 165.0
        self.raio_min = 20.0
        self.raio_atual = self.raio_max
        self.velocidade_anel = 2.05

        # Feedbacks e Shakers
        self.shake_flor = 0
        self.flash_flor = 0
        self.flash_anel = 0
        self.cor_flash_anel = (255, 255, 255)
        self.texto_feedback = ""
        self.cor_feedback = (255, 255, 255)
        self.timer_feedback = 0
        self.timer_conclusao = 0
        self.erros = 0
        self.max_erros = 2

        # Partículas
        self.particulas = []

    def iniciar(self, item=None):
        """Abre o minigame de colheita mística ao interagir com a erva no mapa."""
        self.estado = "JOGANDO"
        self.ativo = True
        self.item_alvo = item
        self.raio_atual = self.raio_max
        self.erros = 0
        self.shake_flor = 0
        self.flash_flor = 0
        self.flash_anel = 0
        self.texto_feedback = "Sincronize o pulso no momento exato em que o anel tocar a ressonância lunar!"
        self.cor_feedback = AZUL_HOVER_MENU
        self.timer_feedback = 70
        self.timer_conclusao = 0
        self.particulas.clear()

        if hasattr(self.game, "audio") and self.game.audio:
            self.game.audio.tocar_sfx("concentrar")

    def handle_events(self, eventos, teclas=None):
        """Processa entrada do jogador (teclado ou mouse)."""
        if not self.ativo or self.estado != "JOGANDO":
            return

        for evento in eventos:
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    self._fechar_sem_sucesso()
                    return
                elif evento.key in [pygame.K_e, pygame.K_SPACE, pygame.K_RETURN]:
                    self._tentar_colheita()
                    return
            elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                self._tentar_colheita()
                return

    def _tentar_colheita(self):
        """Avalia se a contração está dentro da margem de tolerância da flor."""
        diferenca = abs(self.raio_atual - self.raio_alvo)

        if diferenca <= self.tolerancia:
            # ACERTO
            self.estado = "SUCESSO_ANIMACAO"
            self.timer_conclusao = 65
            self.flash_flor = 22
            self.flash_anel = 26
            self.cor_flash_anel = (130, 255, 205)
            self.texto_feedback = "Colheita Perfeita! Os nós luminescentes foram preservados intactos."
            self.cor_feedback = (120, 245, 175)
            self.timer_feedback = 90

            # Dispersão de pétalas luminescentes e gotas de orvalho místico
            cx, cy = self.centro_x, self.centro_y
            for _ in range(36):
                ang = random.uniform(0, math.pi * 2)
                spd = random.uniform(2.0, 6.5)
                cor_p = random.choice([
                    (110, 240, 210),  # Ciano esmeralda
                    (185, 220, 255),  # Azul estelar
                    (255, 245, 170),  # Dourado orvalho
                    (190, 160, 255)   # Violeta lunar
                ])
                self.particulas.append(
                    ParticulaPetala(
                        x=cx + math.cos(ang) * 15,
                        y=cy + math.sin(ang) * 15,
                        vx=math.cos(ang) * spd,
                        vy=math.sin(ang) * spd - 1.2,
                        vida=random.uniform(25.0, 50.0),
                        cor=cor_p,
                        raio=random.uniform(3.0, 5.5),
                        gravidade=-0.05
                    )
                )

            if hasattr(self.game, "audio") and self.game.audio:
                self.game.audio.tocar_sfx("item_coletar")
        else:
            # ERRO
            self.erros += 1
            if self.erros < self.max_erros:
                self.shake_flor = 14
                self.flash_anel = 18
                self.cor_flash_anel = (255, 140, 70)
                if self.raio_atual > self.raio_alvo + self.tolerancia:
                    self.texto_feedback = "Você agiu cedo demais! Cuidado: mais um erro e a flor murchará!"
                else:
                    self.texto_feedback = "Você esperou demais! Cuidado: mais um erro e a flor murchará!"
                self.cor_feedback = (245, 150, 90)
                self.timer_feedback = 60
                self.raio_atual = self.raio_max
                if hasattr(self.game, "audio") and self.game.audio:
                    self.game.audio.tocar_sfx("ui_erro")
            else:
                # FALHA DEFINITIVA
                self.estado = "FALHA_ANIMACAO"
                self.timer_conclusao = 60
                self.shake_flor = 25
                self.flash_flor = 30
                self.flash_anel = 30
                self.cor_flash_anel = (220, 60, 50)
                self.texto_feedback = "A flor murchou completamente! A seiva secou e o broto se desfez."
                self.cor_feedback = (235, 75, 65)
                self.timer_feedback = 90

                # Partículas de cinzas/névoa escura se dispersando
                cx, cy = self.centro_x, self.centro_y
                for _ in range(25):
                    ang = random.uniform(0, math.pi * 2)
                    spd = random.uniform(1.5, 4.0)
                    self.particulas.append(
                        ParticulaPetala(
                            x=cx + math.cos(ang) * 10,
                            y=cy + math.sin(ang) * 10,
                            vx=math.cos(ang) * spd,
                            vy=math.sin(ang) * spd,
                            vida=random.uniform(30.0, 55.0),
                            cor=random.choice([(110, 110, 120), (80, 80, 95), (140, 90, 80)]),
                            raio=random.uniform(2.5, 4.5),
                            gravidade=0.08
                        )
                    )
                if hasattr(self.game, "audio") and self.game.audio:
                    self.game.audio.tocar_sfx("ui_erro")

    def _concluir_com_sucesso(self):
        """Aplica os efeitos da colheita bem-sucedida e encerra o minigame."""
        self.ativo = False
        self.estado = "CONCLUIDO"

        # 1. Adiciona a erva lunar ao inventário da Halia
        if hasattr(self.game, "halia") and hasattr(self.game.halia, "inventario") and self.game.halia.inventario:
            self.game.halia.inventario.adicionar_item("erva_lunar", 1)

        # 2. Remove o item físico do chão e registra coleta
        if self.item_alvo and hasattr(self.game, "mapa_casa") and hasattr(self.game.mapa_casa, "itens_no_chao"):
            if self.item_alvo in self.game.mapa_casa.itens_no_chao:
                self.game.mapa_casa.itens_no_chao.remove(self.item_alvo)
            id_item = getattr(self.item_alvo, "id_unico", None)
            if id_item and hasattr(self.game, "itens_coletados") and id_item not in self.game.itens_coletados:
                self.game.itens_coletados.append(id_item)

        # 3. Atualiza progresso da missão da Curandeira Elara
        if hasattr(self.game, "missoes") and self.game.missoes:
            self.game.missoes.atualizar_progresso("coletar_ervas", 1)

        # 4. Autosave silencioso
        if getattr(self.game, "slot_atual", None):
            self.game.salvar_estado(self.game.slot_atual, tipo="autosave", silenciar_notificacao=True)

        # 5. Diálogo contemplativo da Halia
        self.game.caixa_dialogo.iniciar_dialogo([
            {
                "autor": "Halia",
                "texto": "Colhi a Erva de Orvalho Lunar preservando intactos os nós luminescentes de sua raiz. As gotas de orvalho místico na corola repousam frescas e prontas para as infusões da Curandeira Elara."
            }
        ])

    def _concluir_com_falha(self):
        """Aplica os efeitos da colheita fracassada: flor murcha, é removida e nova erva brota em outro local."""
        self.ativo = False
        self.estado = "FALHOU"

        # 1. Remove a erva danificada do cenário
        if self.item_alvo and hasattr(self.game, "mapa_casa") and hasattr(self.game.mapa_casa, "itens_no_chao"):
            if self.item_alvo in self.game.mapa_casa.itens_no_chao:
                self.game.mapa_casa.itens_no_chao.remove(self.item_alvo)
            if hasattr(self.game.mapa_casa, "ervas_coletaveis") and self.item_alvo in self.game.mapa_casa.ervas_coletaveis:
                self.game.mapa_casa.ervas_coletaveis.remove(self.item_alvo)

            # 2. Gera novo broto em canteiro alternativo de Oakhaven
            if hasattr(self.game.mapa_casa, "respawn_erva_alternativa"):
                self.game.mapa_casa.respawn_erva_alternativa(self.item_alvo)
            elif hasattr(getattr(self.game.mapa_casa, "cenario_objeto", None), "respawn_erva_alternativa"):
                self.game.mapa_casa.cenario_objeto.respawn_erva_alternativa(self.item_alvo)

        # 3. Notificação explicativa
        if hasattr(self.game, "caixa_dialogo") and self.game.caixa_dialogo:
            self.game.caixa_dialogo.iniciar_dialogo([
                {
                    "autor": "Narrador",
                    "texto": "O toque impreciso rompeu a ressonância mágica da planta. A flor murchou e suas pétalas se desfizeram em cinzas... Um novo broto de Orvalho Lunar germinou em outro canteiro da vila."
                }
            ])

    def _fechar_sem_sucesso(self):
        """Cancela o minigame sem consumir o item no cenário."""
        self.ativo = False
        self.estado = "INATIVO"

    def atualizar(self, dt=1.0):
        """Atualiza animações, contração de anéis e partículas."""
        if not self.ativo:
            return

        if self.estado == "JOGANDO":
            self.raio_atual -= self.velocidade_anel
            if self.raio_atual < self.raio_min:
                # Reinicia a contração em ciclo contínuo e suave
                self.raio_atual = self.raio_max

        # Decaimento de shakers e flashes
        if self.shake_flor > 0:
            self.shake_flor -= 1
        if self.flash_flor > 0:
            self.flash_flor -= 1
        if self.flash_anel > 0:
            self.flash_anel -= 1
        if self.timer_feedback > 0:
            self.timer_feedback -= 1

        # Atualiza partículas
        self.particulas = [p for p in self.particulas if p.atualizar(dt)]

        # Estado de animação de sucesso
        if self.estado == "SUCESSO_ANIMACAO":
            self.timer_conclusao -= 1
            if self.timer_conclusao <= 0:
                self._concluir_com_sucesso()
        elif self.estado == "FALHA_ANIMACAO":
            self.timer_conclusao -= 1
            if self.timer_conclusao <= 0:
                self._concluir_com_falha()

    def update(self):
        """Compatibilidade State Pattern."""
        self.atualizar()

    def draw(self, tela):
        """Compatibilidade State Pattern."""
        self.desenhar(tela)

    def desenhar(self, tela):
        """Renderiza a vinheta mística, a planta lunar bioluminescente, os anéis concêntricos e feedback."""
        if not self.ativo:
            return

        # 1. Overlay translúcido de vinheta escura
        overlay = pygame.Surface((self.largura, self.altura), pygame.SRCALPHA)
        overlay.fill((6, 12, 16, 218))
        tela.blit(overlay, (0, 0))

        # 2. Títulos e Subtítulos Superiores
        texto_tit = self.fonte_titulo.render("HERBALISMO MÍSTICO — COLHEITA DA ERVA LUNAR", True, MARFIM_OFFWHITE)
        rect_tit = texto_tit.get_rect(center=(self.largura // 2, 70))
        tela.blit(texto_tit, rect_tit)

        texto_sub = self.fonte_sub.render("Harmonize sua sensibilidade com a ressonância da planta para preservar as raízes luminescentes", True, CINZA_LINHO)
        rect_sub = texto_sub.get_rect(center=(self.largura // 2, 105))
        tela.blit(texto_sub, rect_sub)

        pygame.draw.line(tela, DOURADO_ENVELHECIDO, (self.largura // 2 - 220, 125), (self.largura // 2 + 220, 125), 1)

        # 3. Desenho Central da Flor Lunar e Solo
        cx = self.centro_x
        cy = self.centro_y
        offset_fx = random.randint(-self.shake_flor, self.shake_flor) if self.shake_flor > 0 else 0
        offset_fy = random.randint(-self.shake_flor, self.shake_flor) if self.shake_flor > 0 else 0

        # Base de musgo / terra mística
        pygame.draw.ellipse(tela, (18, 28, 26), (cx - 85, cy + 50, 170, 38))
        pygame.draw.ellipse(tela, (45, 95, 75), (cx - 85, cy + 50, 170, 38), 1)

        # Desenho da Planta e Corola
        self._desenhar_erva_lunar(tela, cx + offset_fx, cy + offset_fy)

        # 4. Anel Alvo de Ressonância (Círculo Verde-Ciano Luminoso)
        self._desenhar_anel_alvo(tela, cx, cy)

        # 5. Anel Dinâmico de Concentração e Orvalho
        if self.estado in ["JOGANDO", "SUCESSO_ANIMACAO"]:
            self._desenhar_anel_concentracao(tela, cx, cy)

        # 6. Partículas ativas
        for p in self.particulas:
            p.desenhar(tela)

        # 7. Textos de Feedback e Controles
        if self.texto_feedback:
            txt_fb = self.fonte_destaque.render(self.texto_feedback, True, self.cor_feedback)
            rect_fb = txt_fb.get_rect(center=(self.largura // 2, 540))
            tela.blit(txt_fb, rect_fb)

        txt_dica = self.fonte_aviso.render("Pressione [E], [ESPAÇO] ou [CLIQUE] ao Alinhar os Círculos   |   [ESC] Sair", True, CINZA_LINHO)
        rect_dica = txt_dica.get_rect(center=(self.largura // 2, 615))
        tela.blit(txt_dica, rect_dica)

    def _desenhar_erva_lunar(self, tela, cx, cy):
        """Renderiza a Erva Lunar bioluminescente com caule esmeralda, pétalas cianas e núcleo de orvalho."""
        # Caule curvilíneo
        pts_caule = [
            (cx, cy + 50),
            (cx - 6, cy + 25),
            (cx + 4, cy),
            (cx, cy - 20)
        ]
        pygame.draw.lines(tela, (42, 140, 95), False, pts_caule, 4)

        # Folhas laterais
        folha_esq = [(cx - 5, cy + 25), (cx - 28, cy + 18), (cx - 18, cy + 10)]
        folha_dir = [(cx + 3, cy + 15), (cx + 26, cy + 8), (cx + 16, cy)]
        pygame.draw.polygon(tela, (55, 175, 120), folha_esq)
        pygame.draw.polygon(tela, (35, 120, 80), folha_esq, 1)
        pygame.draw.polygon(tela, (65, 195, 135), folha_dir)
        pygame.draw.polygon(tela, (35, 120, 80), folha_dir, 1)

        # Halo de bioluminescência suave atrás da corola
        raio_halo = 46 if self.flash_flor == 0 else 60
        surf_halo = pygame.Surface((raio_halo * 2, raio_halo * 2), pygame.SRCALPHA)
        cor_halo = (90, 235, 200, 50 if self.flash_flor == 0 else 120)
        pygame.draw.circle(surf_halo, cor_halo, (raio_halo, raio_halo), raio_halo)
        tela.blit(surf_halo, (cx - raio_halo, cy - 20 - raio_halo))

        # Pétalas da Flor Lunar (5 pétalas em disposição estelar)
        num_petalas = 5
        cor_petala = (140, 230, 255) if self.flash_flor == 0 else (240, 255, 255)
        cor_borda = (80, 180, 210)

        for i in range(num_petalas):
            ang = (i / num_petalas) * math.pi * 2 - math.pi / 2
            px = cx + math.cos(ang) * 22
            py = (cy - 20) + math.sin(ang) * 22

            # Desenha pétala oval
            surf_p = pygame.Surface((28, 28), pygame.SRCALPHA)
            pygame.draw.circle(surf_p, (*cor_petala, 220), (14, 14), 11)
            pygame.draw.circle(surf_p, (*cor_borda, 240), (14, 14), 11, 1)
            tela.blit(surf_p, (int(px) - 14, int(py) - 14))

        # Núcleo da Flor (Orvalho Lunar Brilhante)
        cor_nucleo = (255, 255, 210) if self.flash_flor == 0 else (255, 255, 255)
        pygame.draw.circle(tela, cor_nucleo, (cx, cy - 20), 8)
        pygame.draw.circle(tela, (255, 230, 120), (cx, cy - 20), 8, 1)

    def _desenhar_anel_alvo(self, tela, cx, cy):
        """Renderiza a circunferência alvo de ressonância com marcadores cardeais e zona de tolerância."""
        raio_alvo_int = int(self.raio_alvo)
        tol_int = int(self.tolerancia)

        # Faixa translúcida da zona de tolerância
        largura_faixa = tol_int * 2 + 10
        surf_faixa = pygame.Surface((largura_faixa * 2 + raio_alvo_int * 2, largura_faixa * 2 + raio_alvo_int * 2), pygame.SRCALPHA)
        cf_x, cf_y = surf_faixa.get_width() // 2, surf_faixa.get_height() // 2

        # Círculo preenchido da tolerância externa e recortado na interna
        pygame.draw.circle(surf_faixa, (45, 195, 140, 42), (cf_x, cf_y), raio_alvo_int + tol_int)
        pygame.draw.circle(surf_faixa, (0, 0, 0, 0), (cf_x, cf_y), max(1, raio_alvo_int - tol_int))
        tela.blit(surf_faixa, (cx - cf_x, (cy - 20) - cf_y))

        # Linhas pontilhadas/suaves dos limites de tolerância
        pygame.draw.circle(tela, (40, 150, 110), (cx, cy - 20), raio_alvo_int + tol_int, 1)
        pygame.draw.circle(tela, (40, 150, 110), (cx, cy - 20), max(1, raio_alvo_int - tol_int), 1)

        # Circunferência Alvo Central (Ciano Esmeralda Brilhante)
        pygame.draw.circle(tela, (90, 245, 195), (cx, cy - 20), raio_alvo_int, 2)

        # 4 Marcadores Cardeais de Ressonância (Losangos Rúnicos)
        for ang_deg in [0, 90, 180, 270]:
            rad = math.radians(ang_deg)
            mx = cx + math.cos(rad) * raio_alvo_int
            my = (cy - 20) + math.sin(rad) * raio_alvo_int
            pts_m = [(mx, my - 4), (mx + 4, my), (mx, my + 4), (mx - 4, my)]
            pygame.draw.polygon(tela, (140, 255, 220), pts_m)
            pygame.draw.polygon(tela, (255, 255, 255), pts_m, 1)

    def _desenhar_anel_concentracao(self, tela, cx, cy):
        """Renderiza o anel externo dinâmico que se contrai em direção ao alvo."""
        raio_c_int = max(2, int(self.raio_atual))

        # Determina a cor com base no flash
        if self.flash_anel > 0:
            cor_anel = self.cor_flash_anel
            espessura = 3
        else:
            cor_anel = (210, 245, 255)
            espessura = 2

        # Círculo dinâmico
        pygame.draw.circle(tela, cor_anel, (cx, cy - 20), raio_c_int, espessura)

        # Halo suave do anel móvel
        surf_h = pygame.Surface((raio_c_int * 2 + 16, raio_c_int * 2 + 16), pygame.SRCALPHA)
        ch_x = surf_h.get_width() // 2
        pygame.draw.circle(surf_h, (*cor_anel[:3], 45), (ch_x, ch_x), raio_c_int + 2, 2)
        tela.blit(surf_h, (cx - ch_x, (cy - 20) - ch_x))

        # 4 pequenas gotas de orvalho acompanhando a circunferência em contração
        for ang_deg in [45, 135, 225, 315]:
            rad = math.radians(ang_deg)
            gx = cx + math.cos(rad) * raio_c_int
            gy = (cy - 20) + math.sin(rad) * raio_c_int
            pygame.draw.circle(tela, (255, 255, 255), (int(gx), int(gy)), 3)
            pygame.draw.circle(tela, (120, 220, 255), (int(gx), int(gy)), 4, 1)
