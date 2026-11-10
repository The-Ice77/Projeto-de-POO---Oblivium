# src/mechanics/minigame_ferraria.py
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

class ParticulaRocha:
    """Partícula leve para faíscas arcanas e estilhaços da rocha partida."""
    __slots__ = ("x", "y", "vx", "vy", "vida", "vida_max", "cor", "raio", "rotacao", "v_rot", "gravidade")

    def __init__(self, x, y, vx, vy, vida, cor, raio=3.0, gravidade=0.15):
        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)
        self.vy = float(vy)
        self.vida = float(vida)
        self.vida_max = float(vida)
        self.cor = cor
        self.raio = float(raio)
        self.rotacao = random.uniform(0, 360)
        self.v_rot = random.uniform(-6.0, 6.0)
        self.gravidade = float(gravidade)

    def atualizar(self, dt=1.0):
        self.vida -= dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += self.gravidade * dt
        self.rotacao += self.v_rot * dt
        return self.vida > 0

    def desenhar(self, tela):
        ratio = max(0.0, min(1.0, self.vida / self.vida_max))
        alpha = int(255 * ratio)
        raio_atual = max(1, int(self.raio * ratio))
        
        surf = pygame.Surface((raio_atual * 2, raio_atual * 2), pygame.SRCALPHA)
        cor_rgba = (*self.cor[:3], alpha)
        pygame.draw.circle(surf, cor_rgba, (raio_atual, raio_atual), raio_atual)
        tela.blit(surf, (int(self.x) - raio_atual, int(self.y) - raio_atual))


class FragmentoRocha:
    """Pedaço poligonal da rocha que se espalha em 360 graus na fratura final."""
    def __init__(self, x, y, vertices_relativos, cor_base, vx, vy):
        self.x = float(x)
        self.y = float(y)
        self.vertices_orig = vertices_relativos
        self.cor_base = cor_base
        self.vx = float(vx)
        self.vy = float(vy)
        self.angulo = 0.0
        self.v_rot = random.uniform(-4.0, 4.0)
        self.vida = 60.0
        self.vida_max = 60.0

    def atualizar(self, dt=1.0):
        self.vida -= dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += 0.22 * dt  # gravidade
        self.angulo += self.v_rot * dt
        return self.vida > 0

    def desenhar(self, tela):
        ratio = max(0.0, min(1.0, self.vida / self.vida_max))
        alpha = int(255 * ratio)
        rad = math.radians(self.angulo)
        cos_a = math.cos(rad)
        sin_a = math.sin(rad)

        pts_rot = []
        for vx, vy in self.vertices_orig:
            rx = vx * cos_a - vy * sin_a + self.x
            ry = vx * sin_a + vy * cos_a + self.y
            pts_rot.append((rx, ry))

        if len(pts_rot) >= 3:
            # Desenha com alpha
            min_x = min(p[0] for p in pts_rot)
            max_x = max(p[0] for p in pts_rot)
            min_y = min(p[1] for p in pts_rot)
            max_y = max(p[1] for p in pts_rot)
            w = max(4, int(max_x - min_x) + 4)
            h = max(4, int(max_y - min_y) + 4)

            surf = pygame.Surface((w, h), pygame.SRCALPHA)
            pts_locais = [(p[0] - min_x + 2, p[1] - min_y + 2) for p in pts_rot]
            pygame.draw.polygon(surf, (*self.cor_base[:3], alpha), pts_locais)
            pygame.draw.polygon(surf, (200, 220, 245, int(alpha * 0.7)), pts_locais, 1)
            tela.blit(surf, (int(min_x) - 2, int(min_y) - 2))


class MinigameFerraria:
    """
    Minigame Interativo da Ferraria de Torvald: Concentração Arcana para Quebrar a Pedra.
    - Mecânica de barra oscilante com zona de ressonância estelar.
    - 3 acertos rompem a resistência do minério bruto.
    - Efeito visual da pedra rachando e se partindo em estilhaços luminosos ao concluir.
    """
    def __init__(self, game, playing_state=None):
        self.game = game
        self.playing_state = playing_state
        self.largura = 1280
        self.altura = 720

        # Estados: 'INATIVO', 'JOGANDO', 'FRATURA_FINAL', 'CONCLUIDO'
        self.estado = "INATIVO"
        self.ativo = False

        # Fontes do Minigame
        self.fonte_titulo = ResourceManager.carregar_fonte("sunday", 30)
        self.fonte_sub = ResourceManager.carregar_fonte("contrail", 18)
        self.fonte_destaque = ResourceManager.carregar_fonte("sunday", 22)
        self.fonte_aviso = ResourceManager.carregar_fonte("contrail", 16)

        # Regras e Progresso
        self.acertos_necessarios = 3
        self.acertos_atuais = 0
        self.tempo_oscilacao = 0.0
        self.velocidade_cursor = 2.85

        # Parâmetros da Barra
        self.largura_barra = 440
        self.altura_barra = 26
        self.barra_x = (self.largura - self.largura_barra) // 2
        self.barra_y = 520

        # Zona de Ressonância (Centro da barra)
        self.largura_zona = 84
        self.zona_x = self.barra_x + (self.largura_barra - self.largura_zona) // 2
        self.pos_cursor = 0.0  # 0.0 a 1.0

        # Feedback e Animação
        self.shake_barra = 0
        self.shake_rocha = 0
        self.flash_rocha = 0
        self.texto_feedback = ""
        self.cor_feedback = (255, 255, 255)
        self.timer_feedback = 0

        # Partículas e Efeitos
        self.particulas = []
        self.fragmentos = []
        self.timer_conclusao = 0

    def iniciar(self):
        """Abre o minigame de concentração da forja."""
        self.estado = "JOGANDO"
        self.ativo = True
        self.acertos_atuais = 0
        self.tempo_oscilacao = 0.0
        self.shake_barra = 0
        self.shake_rocha = 0
        self.flash_rocha = 0
        self.texto_feedback = "Sincronize o pulso arcano na zona iluminada!"
        self.cor_feedback = AZUL_HOVER_MENU
        self.timer_feedback = 60
        self.particulas.clear()
        self.fragmentos.clear()
        self.timer_conclusao = 0

        if hasattr(self.game, "audio") and self.game.audio:
            self.game.audio.tocar_sfx("concentrar")

    def handle_events(self, eventos, teclas=None):
        """Processa comandos de interação ou cancelamento."""
        if not self.ativo or self.estado != "JOGANDO":
            return

        for evento in eventos:
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    self._fechar_sem_sucesso()
                    return
                elif evento.key in [pygame.K_e, pygame.K_SPACE, pygame.K_RETURN]:
                    self._tentar_golpe()
                    return
            elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                self._tentar_golpe()
                return

    def _tentar_golpe(self):
        """Avalia se o cursor está dentro da zona de ressonância no momento do pulso."""
        cursor_x_real = self.barra_x + int(self.pos_cursor * (self.largura_barra - 8))
        zona_inicio = self.zona_x
        zona_fim = self.zona_x + self.largura_zona

        if zona_inicio <= cursor_x_real <= zona_fim:
            # ACERTO
            self.acertos_atuais += 1
            self.shake_rocha = 12
            self.flash_rocha = 14
            self.timer_feedback = 70

            # Dispara partículas arcanas no centro da rocha
            rx, ry = 640, 310
            for _ in range(18):
                ang = random.uniform(0, math.pi * 2)
                spd = random.uniform(2.5, 7.0)
                cor_p = random.choice([(120, 210, 255), (255, 230, 130), (160, 240, 255)])
                self.particulas.append(
                    ParticulaRocha(
                        x=rx,
                        y=ry,
                        vx=math.cos(ang) * spd,
                        vy=math.sin(ang) * spd - 1.5,
                        vida=random.uniform(16.0, 28.0),
                        cor=cor_p,
                        raio=random.uniform(2.5, 5.0)
                    )
                )

            if hasattr(self.game, "audio") and self.game.audio:
                self.game.audio.tocar_sfx("item_pocao")

            if self.acertos_atuais >= self.acertos_necessarios:
                self._desencadear_fratura_final()
            else:
                self.texto_feedback = f"Ressonância Firme! Fissura {self.acertos_atuais}/{self.acertos_necessarios}"
                self.cor_feedback = (100, 230, 160)
        else:
            # ERRO
            self.shake_barra = 12
            self.texto_feedback = "Pulso desalinhado! Mantenha a concentração."
            self.cor_feedback = (245, 150, 110)
            self.timer_feedback = 50

            # Fumaça cinzenta de dissipação
            rx, ry = 640, 310
            for _ in range(8):
                ang = random.uniform(-math.pi, 0)
                spd = random.uniform(1.0, 3.0)
                self.particulas.append(
                    ParticulaRocha(
                        x=rx + random.randint(-20, 20),
                        y=ry + random.randint(-10, 10),
                        vx=math.cos(ang) * spd,
                        vy=math.sin(ang) * spd,
                        vida=random.uniform(12.0, 20.0),
                        cor=(180, 180, 190),
                        raio=3.0,
                        gravidade=-0.03
                    )
                )

            if hasattr(self.game, "audio") and self.game.audio:
                self.game.audio.tocar_sfx("ui_erro")

    def _desencadear_fratura_final(self):
        """Dispara a explosão da rocha e transição comemorativa de sucesso."""
        self.estado = "FRATURA_FINAL"
        self.timer_conclusao = 75
        self.texto_feedback = "A rocha cedeu ao feitiço! O minério estelar foi libertado!"
        self.cor_feedback = (255, 230, 110)
        self.shake_rocha = 24
        self.flash_rocha = 28

        # Cria múltiplos fragmentos poligonais voando
        rx, ry = 640, 310
        fragmentos_dados = [
            [(-24, -18), (0, -32), (18, -10), (-8, 8)],
            [(0, -30), (32, -15), (28, 12), (0, 0)],
            [(-30, -5), (-5, 10), (-25, 30), (-35, 15)],
            [(5, 5), (32, 10), (20, 35), (-5, 25)],
            [(-15, -28), (15, -28), (0, -10)],
            [(-10, 12), (15, 8), (5, 36), (-20, 30)]
        ]

        for i, pts in enumerate(fragmentos_dados):
            ang = (i / len(fragmentos_dados)) * math.pi * 2 + random.uniform(-0.3, 0.3)
            spd = random.uniform(3.5, 7.5)
            self.fragmentos.append(
                FragmentoRocha(
                    x=rx,
                    y=ry,
                    vertices_relativos=pts,
                    cor_base=(55, 60, 72),
                    vx=math.cos(ang) * spd,
                    vy=math.sin(ang) * spd - 2.5
                )
            )

        # Centelhas e brilhos intensos de ferro estelar
        for _ in range(40):
            ang = random.uniform(0, math.pi * 2)
            spd = random.uniform(3.0, 9.5)
            cor_c = random.choice([(140, 220, 255), (255, 240, 160), (255, 255, 255)])
            self.particulas.append(
                ParticulaRocha(
                    x=rx,
                    y=ry,
                    vx=math.cos(ang) * spd,
                    vy=math.sin(ang) * spd - 2.0,
                    vida=random.uniform(22.0, 45.0),
                    cor=cor_c,
                    raio=random.uniform(3.0, 6.0)
                )
            )

        if hasattr(self.game, "audio") and self.game.audio:
            self.game.audio.tocar_sfx("item_coletar")

    def _concluir_com_sucesso(self):
        """Aplica recompensas, atualiza a missão e encerra o minigame."""
        self.ativo = False
        self.estado = "CONCLUIDO"

        # 1. Marca flag da rocha quebrada
        self.game.pedra_torvald_quebrada = True

        # 2. Re-inicializa cenário para atualizar o sprite da rocha partida
        if hasattr(self.game.mapa_casa, "cenario_objeto") and self.game.mapa_casa.cenario_objeto:
            self.game.mapa_casa.cenario_objeto.inicializar_cenario()

        # 3. Atualiza progresso da missão
        if hasattr(self.game, "missoes") and self.game.missoes:
            self.game.missoes.atualizar_progresso("quebrar_pedra_forja", 1)

        # 4. Autosave silencioso
        if getattr(self.game, "slot_atual", None):
            self.game.salvar_estado(self.game.slot_atual, tipo="autosave", silenciar_notificacao=True)

        # 5. Diálogo narrativo da Halia
        self.game.caixa_dialogo.iniciar_dialogo([
            {
                "autor": "Halia",
                "texto": "Canalizei um pulso arcano pelo Cajado de Espinheiro direto na fenda da rocha! O bloco de minério bruto se partiu, expondo os veios puros de ferro estelar para o Ferreiro Torvald."
            }
        ])

    def _fechar_sem_sucesso(self):
        """Cancela o minigame a pedido do jogador."""
        self.ativo = False
        self.estado = "INATIVO"

    def atualizar(self):
        """Atualiza a física e os temporizadores do minigame."""
        if not self.ativo:
            return

        dt = 1.0

        # Atualiza oscilação senoidal do cursor
        if self.estado == "JOGANDO":
            self.tempo_oscilacao += 0.035 * self.velocidade_cursor
            self.pos_cursor = 0.5 + 0.5 * math.sin(self.tempo_oscilacao)

        # Reduz shakers
        if self.shake_barra > 0:
            self.shake_barra -= 1
        if self.shake_rocha > 0:
            self.shake_rocha -= 1
        if self.flash_rocha > 0:
            self.flash_rocha -= 1
        if self.timer_feedback > 0:
            self.timer_feedback -= 1

        # Atualiza partículas e fragmentos
        self.particulas = [p for p in self.particulas if p.atualizar(dt)]
        self.fragmentos = [f for f in self.fragmentos if f.atualizar(dt)]

        # Estado de conclusão
        if self.estado == "FRATURA_FINAL":
            self.timer_conclusao -= 1
            if self.timer_conclusao <= 0:
                self._concluir_com_sucesso()

    def update(self):
        """Compatibilidade State Pattern."""
        self.atualizar()

    def draw(self, tela):
        """Compatibilidade State Pattern."""
        self.desenhar(tela)

    def desenhar(self, tela):
        """Renderiza a vinheta escura, o pedestal, a rocha, as fissuras e a barra de concentração."""
        if not self.ativo:
            return

        # 1. Overlay translúcido de vinheta
        overlay = pygame.Surface((self.largura, self.altura), pygame.SRCALPHA)
        overlay.fill((8, 10, 14, 215))
        tela.blit(overlay, (0, 0))

        # 2. Moldura e Títulos Superiores
        texto_tit = self.fonte_titulo.render("FORJA ARCANA — RESSONÂNCIA NO MINÉRIO", True, MARFIM_OFFWHITE)
        rect_tit = texto_tit.get_rect(center=(self.largura // 2, 70))
        tela.blit(texto_tit, rect_tit)

        texto_sub = self.fonte_sub.render("Harmonize a energia mágica para romper o bloco de minério bruto de Torvald", True, CINZA_LINHO)
        rect_sub = texto_sub.get_rect(center=(self.largura // 2, 105))
        tela.blit(texto_sub, rect_sub)

        # Linha decorativa fina
        pygame.draw.line(tela, DOURADO_ENVELHECIDO, (self.largura // 2 - 200, 125), (self.largura // 2 + 200, 125), 1)

        # 3. Pedestal Místico e Rocha
        cx = 640
        cy = 310

        # Aplica shake na rocha
        offset_rx = random.randint(-self.shake_rocha, self.shake_rocha) if self.shake_rocha > 0 else 0
        offset_ry = random.randint(-self.shake_rocha, self.shake_rocha) if self.shake_rocha > 0 else 0

        # Pedestal / Bigorna no solo
        pygame.draw.ellipse(tela, (25, 27, 34), (cx - 110, cy + 60, 220, 48))
        pygame.draw.ellipse(tela, CINZA_LINHO, (cx - 110, cy + 60, 220, 48), 1)

        # Se a rocha ainda não se partiu completamente
        if self.estado != "FRATURA_FINAL" or self.timer_conclusao > 50:
            self._desenhar_rocha_com_fissuras(tela, cx + offset_rx, cy + offset_ry)

        # Desenha fragmentos em vôo
        for frag in self.fragmentos:
            frag.desenhar(tela)

        # Desenha partículas
        for p in self.particulas:
            p.desenhar(tela)

        # 4. Indicador de Progresso (3 Gemas Rúnicas)
        self._desenhar_indicador_gemas(tela, cx, 465)

        # 5. Barra de Concentração e Zona de Ressonância
        offset_bx = random.randint(-self.shake_barra, self.shake_barra) if self.shake_barra > 0 else 0
        self._desenhar_barra_concentracao(tela, self.barra_x + offset_bx, self.barra_y)

        # 6. Texto de Feedback e Controles
        if self.texto_feedback:
            txt_fb = self.fonte_destaque.render(self.texto_feedback, True, self.cor_feedback)
            rect_fb = txt_fb.get_rect(center=(self.largura // 2, 575))
            tela.blit(txt_fb, rect_fb)

        txt_dica = self.fonte_aviso.render("Pressione [E], [ESPAÇO] ou [CLIQUE] na Zona Verde   |   [ESC] Sair", True, CINZA_LINHO)
        rect_dica = txt_dica.get_rect(center=(self.largura // 2, 640))
        tela.blit(txt_dica, rect_dica)

    def _desenhar_rocha_com_fissuras(self, tela, cx, cy):
        """Renderiza a rocha de minério volumétrica e suas fissuras iluminadas."""
        pts_rocha = [
            (cx - 75, cy - 10),
            (cx - 45, cy - 70),
            (cx + 25, cy - 80),
            (cx + 80, cy - 25),
            (cx + 65, cy + 45),
            (cx - 20, cy + 65),
            (cx - 70, cy + 30)
        ]

        # Corpo da Rocha
        cor_rocha = (52, 58, 68) if self.flash_rocha == 0 else (120, 160, 210)
        pygame.draw.polygon(tela, cor_rocha, pts_rocha)
        pygame.draw.polygon(tela, (85, 95, 115), pts_rocha, 2)

        # Sombreamento facetado
        facet_1 = [(cx - 75, cy - 10), (cx - 45, cy - 70), (cx, cy - 10)]
        facet_2 = [(cx + 25, cy - 80), (cx + 80, cy - 25), (cx + 10, cy)]
        facet_3 = [(cx - 20, cy + 65), (cx + 65, cy + 45), (cx, cy + 10)]
        pygame.draw.polygon(tela, (42, 46, 55), facet_1)
        pygame.draw.polygon(tela, (65, 74, 88), facet_2)
        pygame.draw.polygon(tela, (36, 40, 48), facet_3)

        # Veios de Minério Estelar reluzentes
        veio_pts = [
            (cx - 30, cy - 40), (cx - 10, cy - 20), (cx + 15, cy - 35),
            (cx + 35, cy - 10), (cx + 20, cy + 25)
        ]
        pygame.draw.lines(tela, (110, 215, 255), False, veio_pts, 3)

        # Fissura 1 (1 acerto)
        if self.acertos_atuais >= 1:
            fissura_1 = [
                (cx - 45, cy - 70), (cx - 25, cy - 30),
                (cx - 15, cy + 10), (cx - 35, cy + 45)
            ]
            pygame.draw.lines(tela, (255, 235, 130), False, fissura_1, 3)
            pygame.draw.lines(tela, (255, 255, 255), False, fissura_1, 1)

        # Fissura 2 (2 acertos)
        if self.acertos_atuais >= 2:
            fissura_2 = [
                (cx + 25, cy - 80), (cx + 10, cy - 25),
                (cx + 30, cy + 15), (cx + 55, cy + 40)
            ]
            fissura_ramo = [(cx + 10, cy - 25), (cx - 15, cy + 10)]
            pygame.draw.lines(tela, (255, 240, 140), False, fissura_2, 3)
            pygame.draw.lines(tela, (255, 255, 255), False, fissura_2, 1)
            pygame.draw.lines(tela, (130, 230, 255), False, fissura_ramo, 2)

    def _desenhar_indicador_gemas(self, tela, cx, cy):
        """Desenha os 3 marcadores rúnicos de impacto."""
        espacamento = 48
        inicio_x = cx - espacamento
        for i in range(self.acertos_necessarios):
            gx = inicio_x + i * espacamento
            acertou = (i < self.acertos_atuais)

            # Losango / Gema rúnica
            pts_gema = [(gx, cy - 10), (gx + 10, cy), (gx, cy + 10), (gx - 10, cy)]
            if acertou:
                pygame.draw.polygon(tela, (255, 225, 90), pts_gema)
                pygame.draw.polygon(tela, (255, 255, 255), pts_gema, 1)
                # Halo suave
                surf_h = pygame.Surface((32, 32), pygame.SRCALPHA)
                pygame.draw.circle(surf_h, (255, 220, 80, 80), (16, 16), 14)
                tela.blit(surf_h, (gx - 16, cy - 16))
            else:
                pygame.draw.polygon(tela, (28, 30, 36), pts_gema)
                pygame.draw.polygon(tela, CINZA_LINHO, pts_gema, 1)

    def _desenhar_barra_concentracao(self, tela, bx, by):
        """Renderiza a barra com a zona de ressonância e o cursor móvel."""
        # Fundo da Barra
        rect_barra = pygame.Rect(bx, by, self.largura_barra, self.altura_barra)
        pygame.draw.rect(tela, (18, 20, 26), rect_barra, border_radius=6)

        # Zona de Ressonância (Verde Esmeralda)
        rect_zona = pygame.Rect(self.zona_x, by + 2, self.largura_zona, self.altura_barra - 4)
        surf_zona = pygame.Surface((self.largura_zona, self.altura_barra - 4), pygame.SRCALPHA)
        surf_zona.fill((45, 195, 120, 180))
        tela.blit(surf_zona, (self.zona_x, by + 2))
        pygame.draw.rect(tela, (100, 240, 165), rect_zona, 1, border_radius=4)

        # Linha central guia na zona
        centro_zona_x = self.zona_x + self.largura_zona // 2
        pygame.draw.line(tela, (220, 255, 235), (centro_zona_x, by + 2), (centro_zona_x, by + self.altura_barra - 3), 2)

        # Contorno da Barra
        pygame.draw.rect(tela, CINZA_LINHO, rect_barra, 2, border_radius=6)

        # Cursor Móvel (Losango Dourado com Linha Vertical)
        cursor_x_real = bx + int(self.pos_cursor * (self.largura_barra - 8)) + 4
        cursor_y_centro = by + self.altura_barra // 2

        pts_cursor = [
            (cursor_x_real, by - 8),
            (cursor_x_real + 6, by),
            (cursor_x_real, by + 8),
            (cursor_x_real - 6, by)
        ]
        pygame.draw.line(tela, (255, 235, 140), (cursor_x_real, by - 4), (cursor_x_real, by + self.altura_barra + 4), 2)
        pygame.draw.polygon(tela, (255, 225, 90), pts_cursor)
        pygame.draw.polygon(tela, (255, 255, 255), pts_cursor, 1)
