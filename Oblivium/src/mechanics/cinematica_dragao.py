# src/mechanics/cinematica_dragao.py
import math
import random
import pygame
from src.utils.resource_manager import ResourceManager
from src.entities.elemento_cenario import ChamaIndependente


class CinematicaAtaqueDragao:
    """
    Controlador Cinemático do Repouso Noturno de Halia e Ataque Aéreo de Ignis'Vahr em Oakhaven.
    
    Aprimoramentos de Elite:
    - Estudo anatômico e alinhamento milimétrico de sprites (elimina 100% dos tremores e 'pulos' verticais).
    - Escala calibrada (1.08) para impor majestade e terror sem deformar a perspectiva da vila.
    - Física de voo fluida: mergulho predatório, voo rasante com curvatura aerodinâmica e subida aos céus.
    - Inclinação orgânica (banking) do corpo do dragão conforme sua aceleração e altitude.
    - Ataque em 3 pontos de impacto estratégicos (Distrito Oeste/Feira, Praça/Monumento e Distrito Leste/Armeria).
    - Explosões colossais em cadeia, ondas de choque, fumaça preta volumétrica e focos de incêndio
      reais que se acendem imediatamente nos locais atingidos antes da transição da vila.
    """

    OFFSETS_FLIGHT = [45, 78, 112, 51, 4, 0]
    OFFSETS_SPECIAL = [155, 112, 47, 16, 7, 0]

    def __init__(self, game, playing):
        self.game = game
        self.playing = playing
        self.ativo = False
        self.fase = "INATIVO"
        self.tempo_fase = 0.0

        # Subfases do Ataque Aéreo (Passe 1 no Norte/Centro -> Tensão no Sul -> Passe 2 nas Partes de Baixo)
        self.subfase_voo = "PASSE_1"
        self.tempo_subfase = 0.0

        # Efeitos de transição visual e tela
        self.alpha_fade = 0.0
        self.shake_offset = (0, 0)
        self.timer_shake = 0.0
        self.intensidade_shake = 0.0
        self.flash_clarão = 0.0

        # Coordenadas de Halia e da Casa de Hóspedes (Porta oficial de c1_f05 na base frontal sul)
        self.porta_casa_x = 1345
        self.porta_casa_y = 1122
        self.praca_x = 1102
        self.praca_y = 660
        self.waypoints_caminho = []
        self.waypoint_idx = 0

        # Dinâmica física do dragão
        self.dragao_x = -240.0
        self.dragao_y = 360.0
        self.dragao_vx = 420.0
        self.dragao_vy = 0.0
        self.dragao_angulo = -6.0
        self.virado_direita = True
        self.altitude_aparente = 130.0
        self.dragao_anim_tipo = "flight"
        self.dragao_frame_idx = 0.0
        self.dragao_escala = 1.08
        self.subfase_voo = "PASSE_NORTE"
        self.tempo_subfase = 0.0

        # Efeitos visuais do ataque
        self.explosoes = []
        self.impactos_programados = []
        self.particulas_sopro = []
        self.colunas_fumaca = []
        self.focos_fogo_ativos = []

        # Recursos gráficos pré-processados e padronizados
        self.frames_flight = self._carregar_frames_padronizados(
            "assets/inimigos/dragao_vermelho/flight",
            self.OFFSETS_FLIGHT,
            largura_canvas=260,
            altura_canvas=186
        )
        self.frames_special = self._carregar_frames_padronizados(
            "assets/inimigos/dragao_vermelho/special",
            self.OFFSETS_SPECIAL,
            largura_canvas=262,
            altura_canvas=250
        )
        self.frames_explosao_1 = self._carregar_frames_explosao("efeitos/explosao/explosao_1", (240, 240))
        self.frames_explosao_2 = self._carregar_frames_explosao("efeitos/explosao/explosao_2", (190, 190))
        self.frames_explosao_3 = self._carregar_frames_explosao("efeitos/explosao/explosao_3", (210, 210))

        # Cache de superfícies para alto desempenho (zero alocações no loop)
        dw = int(260 * self.dragao_escala)
        dh = int(186 * self.dragao_escala)
        sombra_w = int(dw * 0.72)
        sombra_h = int(dh * 0.22)
        self._sombra_dragao_surf = pygame.Surface((sombra_w, sombra_h), pygame.SRCALPHA)
        pygame.draw.ellipse(self._sombra_dragao_surf, (12, 6, 10, 120), (0, 0, sombra_w, sombra_h))

        # Sombra suave para altas altitudes
        self._sombra_alta_surf = pygame.Surface((int(sombra_w * 0.85), int(sombra_h * 0.85)), pygame.SRCALPHA)
        pygame.draw.ellipse(self._sombra_alta_surf, (12, 6, 10, 65), (0, 0, int(sombra_w * 0.85), int(sombra_h * 0.85)))

        self._glow_explosao_surf = pygame.Surface((360, 360), pygame.SRCALPHA)
        pygame.draw.circle(self._glow_explosao_surf, (255, 140, 30, 75), (180, 180), 175)
        pygame.draw.circle(self._glow_explosao_surf, (255, 230, 120, 140), (180, 180), 85)

        self._glow_boca_surf = pygame.Surface((120, 120), pygame.SRCALPHA)
        pygame.draw.circle(self._glow_boca_surf, (255, 140, 20, 100), (60, 60), 55)
        pygame.draw.circle(self._glow_boca_surf, (255, 230, 90, 170), (60, 60), 28)
        pygame.draw.circle(self._glow_boca_surf, (255, 255, 220, 230), (60, 60), 12)

    def _carregar_frames_padronizados(self, pasta, offsets_y, largura_canvas, altura_canvas):
        """
        Padroniza e ancora os frames do dragão em um canvas único compensando
        as variações de recorte da spritesheet original. Elimina qualquer oscilação ou tremor.
        """
        frames_brutos = ResourceManager.carregar_frames_pasta(pasta)
        if not frames_brutos:
            surf = pygame.Surface((int(largura_canvas * self.dragao_escala), int(altura_canvas * self.dragao_escala)), pygame.SRCALPHA)
            pygame.draw.ellipse(surf, (180, 40, 25), (0, 0, surf.get_width(), surf.get_height()))
            return [surf]

        cw = int(largura_canvas * self.dragao_escala)
        ch = int(altura_canvas * self.dragao_escala)
        frames_finais = []

        for i, f in enumerate(frames_brutos):
            off_y = offsets_y[i] if i < len(offsets_y) else 0
            canvas = pygame.Surface((cw, ch), pygame.SRCALPHA)
            nw = max(1, int(f.get_width() * self.dragao_escala))
            nh = max(1, int(f.get_height() * self.dragao_escala))
            f_redim = pygame.transform.smoothscale(f, (nw, nh))
            canvas.blit(f_redim, (0, int(off_y * self.dragao_escala)))
            frames_finais.append(canvas)

        return frames_finais

    def _carregar_frames_explosao(self, pasta, tamanho):
        frames = ResourceManager.carregar_frames_pasta(pasta)
        if not frames:
            surf = pygame.Surface(tamanho, pygame.SRCALPHA)
            pygame.draw.circle(surf, (255, 130, 20), (tamanho[0] // 2, tamanho[1] // 2), tamanho[0] // 2)
            return [surf]
        return [pygame.transform.smoothscale(f, tamanho) for f in frames]

    def iniciar_sono(self):
        """Inicia a cutscene de descanso: Halia caminha pelas ruas da vila até a Casa de Hóspedes e dorme."""
        self.ativo = True
        self.fase = "CAMINHANDO_CASA"
        self.tempo_fase = 0.0
        self.alpha_fade = 0.0
        self.shake_offset = (0, 0)
        self.timer_shake = 0.0
        self.flash_clarão = 0.0

        if hasattr(self.game, "halia") and self.game.halia:
            self.game.halia.mudar_estado("andar")
            hx, hy = self.game.halia.x, self.game.halia.y

            # Traçado urbano oficial pelas vias da vila (evita fonte, jardineiras, placas e construções)
            rota = []
            if hy < 658:
                rota.append((hx, 660))
            if hx > 950:
                rota.append((945, 660))
            rota.extend([
                (945, 860),   # Desce pela alameda oeste da Praça contornando a fonte
                (1150, 860),  # Entra na Estrada Principal Norte-Sul
                (1150, 1180), # Desce pela Estrada Principal até a Rua Residencial Sul
                (1345, 1180), # Caminha a leste pela Rua Residencial Sul até a entrada da Casa
                (1345, 1122)  # Sobe o ramal da calçada e chega exatamente à soleira da porta da Casa
            ])
            self.waypoints_caminho = rota
            self.waypoint_idx = 0

    def iniciar_ataque_aereo(self):
        """Dispara o ataque aéreo contínuo e devastador de Ignis'Vahr em Oakhaven."""
        self.ativo = True
        self.fase = "VOO_DRAGAO"
        self.subfase_voo = "PASSE_NORTE"
        self.tempo_fase = 0.0
        self.tempo_subfase = 0.0
        self.alpha_fade = 255.0  # Clareia suavemente após o silêncio da noite
        self.timer_shake = 0.0
        self.intensidade_shake = 0.0
        self.flash_clarão = 0.0

        # Vila à noite intacta antes das detonações
        self.game.oakhaven_noite = True
        self.game.oakhaven_destruida = False
        self.game.cena_inimigos_andando = False
        self.game.inimigos_em_cena.clear()

        # Halia abrigada na Casa de Hóspedes
        self.game.halia.x = self.porta_casa_x
        self.game.halia.y = self.porta_casa_y
        self.game.halia.direcao = "baixo"
        self.game.halia.mudar_estado("idle")

        # Inicia a trilha sonora épica
        if hasattr(self.game, "audio") and self.game.audio:
            self.game.audio.tocar_musica("combate_dragao", loop=-1, fade_ms=600)

        # Posição e dinâmica inicial do voo contínuo
        self.dragao_x = -240.0
        self.dragao_y = 360.0
        self.dragao_vx = 420.0
        self.dragao_vy = 0.0
        self.dragao_angulo = -6.0
        self.virado_direita = True
        self.altitude_aparente = 130.0
        self.dragao_anim_tipo = "flight"
        self.dragao_frame_idx = 0.0

        self.explosoes.clear()
        self.particulas_sopro.clear()
        self.colunas_fumaca.clear()
        self.focos_fogo_ativos.clear()

        # Cronograma de bombardeio nos distritos de Oakhaven (sincronizado com o voo contínuo)
        # Formato: (tempo_s, x_alvo, y_alvo, tipo_explosao, potencia_shake, desc)
        self.impactos_programados = [
            # 1. Distrito Oeste (Feira e Botânica) - durante PASSE_NORTE
            (1.60, 450, 520, "exp_2", 11.0, "barraca_oeste"),
            (1.85, 540, 480, "exp_1", 14.0, "feira_oeste"),

            # 2. Distrito Central (Praça Cívica e Monumento dos Heróis) - durante PASSE_NORTE
            (3.20, 1110, 540, "exp_1", 18.0, "monumento_centro"),
            (3.50, 1240, 560, "exp_3", 12.0, "praca_leste"),

            # 3. Distrito Leste (Armeria e Ferraria) - durante PASSE_NORTE
            (4.55, 1680, 480, "exp_1", 16.0, "armeria_leste"),
            (4.85, 1820, 510, "exp_2", 11.0, "telhado_ferraria"),

            # 4. Distrito Residencial Sul (As Partes de Baixo) - durante PASSE_SUL
            (7.10, 1620, 960, "exp_3", 13.0, "residencial_sul_leste"),
            (7.70, 1420, 980, "exp_2", 11.0, "jardim_sul_centro"),
            (8.15, 1345, 1120, "exp_1", 20.0, "porta_casa_hospedes"),  # DIRETO na porta da Casa de Halia!
            (9.10, 880, 960, "exp_2", 12.0, "alameda_sul_centro"),
            (9.75, 640, 980, "exp_1", 15.0, "casas_sul_oeste"),
        ]

    def obter_foco_camera(self):
        """Retorna o centro alvo (cx, cy) para a câmera acompanhando o dragão 100% do tempo."""
        if self.fase == "VOO_DRAGAO":
            # Segue diretamente o corpo do dragão para que ele nunca fique fora de foco
            return (self.dragao_x + 140.0, self.dragao_y + 100.0)
        return (self.game.halia.x, self.game.halia.y)

    def handle_event(self, evento):
        """Permite avançar cutscene com ENTER ou ESPAÇO."""
        if not self.ativo:
            return False
        if evento.type == pygame.KEYDOWN and evento.key in (pygame.K_RETURN, pygame.K_SPACE):
            if self.fase == "DORMINDO":
                self.iniciar_ataque_aereo()
                return True
            elif self.fase == "CAMINHANDO_CASA":
                self.game.halia.x = self.porta_casa_x
                self.game.halia.y = self.porta_casa_y
                self.game.halia.direcao = "cima"
                self.game.halia.mudar_estado("idle")
                self.fase = "ENTRANDO_CASA"
                self.tempo_fase = 0.0
                return True
            elif self.fase == "VOO_DRAGAO" and self.tempo_fase > 2.0:
                self._finalizar_ataque_e_despertar()
                return True
            elif self.fase == "HALIA_DESPERTANDO":
                self.game.halia.x = self.praca_x
                self.game.halia.y = self.praca_y
                self.game.halia.direcao = "cima"
                self.game.halia.mudar_estado("idle")
                self.ativo = False
                self.fase = "INATIVO"
                self.shake_offset = (0, 0)
                if getattr(self.game, "slot_atual", None):
                    self.game.salvar_estado(self.game.slot_atual, tipo="autosave")
                self.game.caixa_dialogo.iniciar_dialogo("despertar_ataque_dragao_vila")
                return True
        return False

    def atualizar(self, dt=0.016):
        if not self.ativo:
            return

        self.tempo_fase += dt

        # Decaimento do Screen Shake físico
        if self.timer_shake > 0:
            self.timer_shake -= dt
            potencia = int(self.intensidade_shake * max(0.0, self.timer_shake / 2.0))
            if potencia > 0:
                self.shake_offset = (random.randint(-potencia, potencia), random.randint(-potencia, potencia))
            else:
                self.shake_offset = (0, 0)
        else:
            self.shake_offset = (0, 0)

        # Decaimento do clarão de impacto
        if self.flash_clarão > 0:
            self.flash_clarão = max(0.0, self.flash_clarão - dt * 280.0)

        # 1. Halia caminhando pelas ruas da vila até a Casa de Hóspedes
        if self.fase == "CAMINHANDO_CASA":
            if self.waypoint_idx < len(self.waypoints_caminho):
                alvo_x, alvo_y = self.waypoints_caminho[self.waypoint_idx]
                hx, hy = self.game.halia.x, self.game.halia.y
                dx = alvo_x - hx
                dy = alvo_y - hy
                dist = math.hypot(dx, dy)

                if dist < 6:
                    self.waypoint_idx += 1
                    if self.waypoint_idx >= len(self.waypoints_caminho):
                        self.game.halia.x = self.porta_casa_x
                        self.game.halia.y = self.porta_casa_y
                        self.game.halia.direcao = "cima"
                        self.game.halia.mudar_estado("idle")
                        self.fase = "ENTRANDO_CASA"
                        self.tempo_fase = 0.0
                else:
                    vel = 140.0 * dt
                    if abs(dx) > abs(dy):
                        self.game.halia.direcao = "direita" if dx > 0 else "esquerda"
                        self.game.halia.virado_direita = (dx > 0)
                    else:
                        self.game.halia.direcao = "baixo" if dy > 0 else "cima"

                    passo = min(dist, vel)
                    self.game.halia.x += (dx / dist) * passo
                    self.game.halia.y += (dy / dist) * passo
                    self.game.halia.mudar_estado("andar")
                    self.game.halia.atualizar_animacao()
            else:
                self.game.halia.x = self.porta_casa_x
                self.game.halia.y = self.porta_casa_y
                self.game.halia.direcao = "cima"
                self.game.halia.mudar_estado("idle")
                self.fase = "ENTRANDO_CASA"
                self.tempo_fase = 0.0

        # 2. Entrando e fade para escuro
        elif self.fase == "ENTRANDO_CASA":
            # Halia avança suavemente em direção à soleira/interior ao fechar a porta
            self.game.halia.direcao = "cima"
            self.game.halia.mudar_estado("andar")
            self.game.halia.y = max(1116.0, self.game.halia.y - dt * 14.0)
            self.game.halia.atualizar_animacao()

            self.alpha_fade = min(255.0, self.alpha_fade + dt * 260.0)
            if self.alpha_fade >= 255.0:
                self.alpha_fade = 255.0
                self.fase = "DORMINDO"
                self.tempo_fase = 0.0

        # 3. Noite de sono
        elif self.fase == "DORMINDO":
            self.alpha_fade = 255.0
            if self.tempo_fase >= 3.2:
                self.iniciar_ataque_aereo()

        # 4. Voo e bombardeio aéreo de Ignis'Vahr em circuito contínuo
        elif self.fase == "VOO_DRAGAO":
            if self.alpha_fade > 0:
                self.alpha_fade = max(0.0, self.alpha_fade - dt * 220.0)

            self.tempo_subfase += dt
            em_ataque = False

            # -------------------------------------------------------------
            # TRECHO 1: PASSE_NORTE (Oeste -> Leste pelo Norte e Centro)
            # -------------------------------------------------------------
            if self.subfase_voo == "PASSE_NORTE":
                self.virado_direita = True
                self.dragao_x += self.dragao_vx * dt

                # Ondulação aerodinâmica suave batendo asas
                fase_onda = (self.dragao_x + 240.0) / 2100.0
                alvo_y = 390.0 + math.sin(fase_onda * math.pi * 2.0) * 35.0
                self.dragao_vy = (alvo_y - self.dragao_y) * 5.0
                self.dragao_y += self.dragao_vy * dt
                alvo_ang = max(-9.0, min(9.0, -self.dragao_vy * 0.22))
                self.dragao_angulo += (alvo_ang - self.dragao_angulo) * 0.15
                self.altitude_aparente = 140.0

                em_ataque = (280 <= self.dragao_x <= 1860)

                if self.dragao_x >= 1860.0:
                    self.subfase_voo = "CURVA_LESTE"
                    self.tempo_subfase = 0.0

            # -------------------------------------------------------------
            # TRECHO 2: CURVA_LESTE (Curva contínua no leste contornando para o Sul)
            # -------------------------------------------------------------
            elif self.subfase_voo == "CURVA_LESTE":
                em_ataque = False
                dur_curva = 1.6
                prog = min(1.0, self.tempo_subfase / dur_curva)

                # Curva senoidal em arco no leste de y=390 para y=925
                self.dragao_x = 1860.0 + math.sin(prog * math.pi) * 85.0
                self.dragao_y = 390.0 + (925.0 - 390.0) * (0.5 - 0.5 * math.cos(prog * math.pi))
                self.altitude_aparente = 130.0

                if prog < 0.5:
                    self.virado_direita = True
                    self.dragao_angulo = -18.0 * math.sin(prog * math.pi)
                else:
                    self.virado_direita = False
                    self.dragao_angulo = 18.0 * math.sin(prog * math.pi)

                if prog >= 1.0:
                    self.subfase_voo = "PASSE_SUL"
                    self.tempo_subfase = 0.0
                    self.virado_direita = False
                    self.dragao_vx = -390.0
                    self.dragao_angulo = 0.0

            # -------------------------------------------------------------
            # TRECHO 3: PASSE_SUL (Leste -> Oeste pelas PARTES DE BAIXO!)
            # -------------------------------------------------------------
            elif self.subfase_voo == "PASSE_SUL":
                self.virado_direita = False
                self.dragao_x += self.dragao_vx * dt

                # Voo rasante aterrorizante rente aos telhados do sul e sobre a Casa de Hóspedes
                fase_onda = (1860.0 - self.dragao_x) / 1440.0
                alvo_y = 925.0 + math.sin(fase_onda * math.pi * 2.0) * 28.0
                self.dragao_vy = (alvo_y - self.dragao_y) * 5.0
                self.dragao_y += self.dragao_vy * dt
                alvo_ang = max(-8.0, min(8.0, self.dragao_vy * 0.22))
                self.dragao_angulo += (alvo_ang - self.dragao_angulo) * 0.15
                self.altitude_aparente = 100.0  # Muito rente ao solo

                em_ataque = (420 <= self.dragao_x <= 1820)

                if self.dragao_x <= 420.0:
                    self.subfase_voo = "SUBIDA_FINAL"
                    self.tempo_subfase = 0.0
                    self.virado_direita = True
                    self.dragao_angulo = 16.0

            # -------------------------------------------------------------
            # TRECHO 4: SUBIDA_FINAL (Ascensão triunfal rumo às montanhas do norte)
            # -------------------------------------------------------------
            elif self.subfase_voo == "SUBIDA_FINAL":
                em_ataque = False
                self.virado_direita = True
                self.dragao_x += 460.0 * dt
                self.dragao_y -= 340.0 * dt
                self.dragao_angulo = 18.0
                self.altitude_aparente = 160.0 + self.tempo_subfase * 80.0

                if self.dragao_y < -220 or self.dragao_x > 2400 or self.tempo_subfase >= 3.6:
                    self._finalizar_ataque_e_despertar()

            # Animação contínua e 100% fluida de voo (sem jamais truncar ou trocar bruscamente de sprite)
            self.dragao_anim_tipo = "flight"
            self.dragao_frame_idx = (self.dragao_frame_idx + dt * 8.5) % len(self.frames_flight)

            # Posição da boca conforme a direção do dragão
            if self.virado_direita:
                boca_x = self.dragao_x + int(246 * self.dragao_escala)
            else:
                boca_x = self.dragao_x + int(14 * self.dragao_escala)
            boca_y = self.dragao_y + int(118 * self.dragao_escala)

            # Torrentes de fogo descendentes e contínuas durante o ataque
            if em_ataque:
                vel_x_min, vel_x_max = (35, 115) if self.virado_direita else (-115, -35)
                for _ in range(3):
                    self.particulas_sopro.append({
                        "x": boca_x + random.uniform(-4, 4),
                        "y": boca_y + random.uniform(-3, 3),
                        "vx": random.uniform(vel_x_min, vel_x_max),
                        "vy": random.uniform(220, 360),
                        "raio": random.uniform(7.0, 15.0),
                        "vida": random.uniform(0.42, 0.78),
                        "vida_max": 0.78,
                        "cor": random.choice([
                            (255, 255, 220), (255, 210, 60),
                            (255, 130, 20), (255, 60, 10), (180, 30, 10)
                        ])
                    })

            # Atualiza partículas de sopro
            vivas_sopro = []
            for p in self.particulas_sopro:
                p["x"] += p["vx"] * dt
                p["y"] += p["vy"] * dt
                p["vida"] -= dt
                if p["vida"] > 0:
                    vivas_sopro.append(p)
            self.particulas_sopro = vivas_sopro

            # Disparo e verificação dos impactos programados (sincronizados com o tempo global de cena)
            restantes_impactos = []
            for t_disp, ex, ey, tipo_exp, shake_forca, _ in self.impactos_programados:
                if self.tempo_fase >= t_disp:
                    frames_exp = self.frames_explosao_1
                    if tipo_exp == "exp_2":
                        frames_exp = self.frames_explosao_2
                    elif tipo_exp == "exp_3":
                        frames_exp = self.frames_explosao_3

                    self.explosoes.append({
                        "x": ex,
                        "y": ey,
                        "frames": frames_exp,
                        "frame_idx": 0.0,
                        "vel_anim": 42.0,
                        "raio_onda": 10.0,
                        "onda_ativa": True
                    })

                    # Clarão e abalo sísmico
                    self.flash_clarão = 220.0
                    self.timer_shake = 1.9
                    self.intensidade_shake = shake_forca

                    # Instancia fogo real e colunas de fumaça persistente no local detonado
                    self.focos_fogo_ativos.append(
                        ChamaIndependente(ex, ey + 24, tipo="chao_larga", escala=1.05, glow_base=42)
                    )
                    self.colunas_fumaca.append({
                        "x": ex + random.uniform(-15, 15),
                        "y": ey - 10,
                        "timer_particula": 0.0,
                        "particulas": []
                    })
                else:
                    restantes_impactos.append((t_disp, ex, ey, tipo_exp, shake_forca, _))
            self.impactos_programados = restantes_impactos

            # Atualiza explosões
            vivas_exp = []
            for exp in self.explosoes:
                exp["frame_idx"] += dt * exp["vel_anim"]
                if exp["onda_ativa"]:
                    exp["raio_onda"] += dt * 320.0
                    if exp["raio_onda"] > 160.0:
                        exp["onda_ativa"] = False
                if int(exp["frame_idx"]) < len(exp["frames"]):
                    vivas_exp.append(exp)
            self.explosoes = vivas_exp

            # Atualiza chamas ativas criadas durante a destruição
            for fogo in self.focos_fogo_ativos:
                fogo.atualizar(dt, vento_x=0.4)

            # Atualiza colunas de fumaça
            for col in self.colunas_fumaca:
                col["timer_particula"] += dt
                if col["timer_particula"] >= 0.08:
                    col["timer_particula"] = 0.0
                    col["particulas"].append({
                        "x": col["x"] + random.uniform(-10, 10),
                        "y": col["y"],
                        "vx": random.uniform(8.0, 22.0),
                        "vy": random.uniform(-55.0, -32.0),
                        "raio": random.uniform(6.0, 10.0),
                        "vida": random.uniform(2.0, 3.2),
                        "vida_max": 3.2,
                        "alpha": random.uniform(140, 210)
                    })
                vivas_p = []
                for p in col["particulas"]:
                    p["x"] += p["vx"] * dt
                    p["y"] += p["vy"] * dt
                    p["raio"] += 5.5 * dt
                    p["vida"] -= dt
                    if p["vida"] > 0:
                        vivas_p.append(p)
                col["particulas"] = vivas_p

        # 5. Halia saindo da casa e correndo pelas ruas da vila até a praça em ruínas
        elif self.fase == "HALIA_DESPERTANDO":
            if self.waypoint_idx < len(self.waypoints_caminho):
                alvo_x, alvo_y = self.waypoints_caminho[self.waypoint_idx]
                hx, hy = self.game.halia.x, self.game.halia.y
                dx = alvo_x - hx
                dy = alvo_y - hy
                dist = math.hypot(dx, dy)

                if dist < 8:
                    self.waypoint_idx += 1
                    if self.waypoint_idx >= len(self.waypoints_caminho):
                        self.game.halia.x = self.praca_x
                        self.game.halia.y = self.praca_y
                        self.game.halia.direcao = "cima"
                        self.game.halia.mudar_estado("idle")
                        self.ativo = False
                        self.fase = "INATIVO"
                        self.shake_offset = (0, 0)

                        if getattr(self.game, "slot_atual", None):
                            self.game.salvar_estado(self.game.slot_atual, tipo="autosave")

                        self.game.caixa_dialogo.iniciar_dialogo("despertar_ataque_dragao_vila")
                else:
                    vel = 180.0 * dt  # Corrida rápida e alarmada para socorrer a vila
                    if abs(dx) > abs(dy):
                        self.game.halia.direcao = "direita" if dx > 0 else "esquerda"
                        self.game.halia.virado_direita = (dx > 0)
                    else:
                        self.game.halia.direcao = "baixo" if dy > 0 else "cima"

                    passo = min(dist, vel)
                    self.game.halia.x += (dx / dist) * passo
                    self.game.halia.y += (dy / dist) * passo
                    self.game.halia.mudar_estado("andar")
                    self.game.halia.atualizar_animacao()
            else:
                self.game.halia.x = self.praca_x
                self.game.halia.y = self.praca_y
                self.game.halia.direcao = "cima"
                self.game.halia.mudar_estado("idle")
                self.ativo = False
                self.fase = "INATIVO"
                self.shake_offset = (0, 0)

                if getattr(self.game, "slot_atual", None):
                    self.game.salvar_estado(self.game.slot_atual, tipo="autosave")

                self.game.caixa_dialogo.iniciar_dialogo("despertar_ataque_dragao_vila")

    def _finalizar_ataque_e_despertar(self):
        """Transiciona a vila para o estado devastado permanente e posiciona Halia saindo da casa."""
        self.game.oakhaven_destruida = True
        self.game.mapa_casa.carregar_cenario("OAKHAVEN_DESTRUIDA")
        self.game.halia.x = self.porta_casa_x
        self.game.halia.y = self.porta_casa_y
        self.game.halia.direcao = "baixo"
        self.game.halia.mudar_estado("andar")
        self.playing.atualizar_camera(instantaneo=True)
        self.fase = "HALIA_DESPERTANDO"
        self.subfase_voo = "CONCLUIDO"
        self.tempo_fase = 0.0
        self.dragao_x = 3500
        self.explosoes.clear()
        self.particulas_sopro.clear()
        self.colunas_fumaca.clear()
        self.focos_fogo_ativos.clear()

        # Rota de retorno correndo pelas ruas da vila até a Praça Central em chamas
        self.waypoints_caminho = [
            (1345, 1180),  # Desce da soleira até a Rua Residencial Sul
            (1150, 1180),  # Corre a oeste pela Rua Residencial Sul
            (1150, 860),   # Sobe pela Estrada Principal Norte-Sul
            (945, 860),    # Vira a oeste na alameda da praça
            (945, 660),    # Sobe pelo corredor oeste da praça
            (1102, 660),   # Corre a leste até a estátua/praça diante de Aldous
        ]
        self.waypoint_idx = 0

    def pular_direto_para_despertar(self):
        """Atalho para testes e comandos dev."""
        self.game.oakhaven_noite = True
        self.game.oakhaven_destruida = True
        self.game.mapa_casa.carregar_cenario("OAKHAVEN_DESTRUIDA")
        self.game.cena_inimigos_andando = False
        self.game.inimigos_em_cena.clear()
        self.game.halia.x = self.praca_x
        self.game.halia.y = self.praca_y
        self.game.halia.direcao = "cima"
        self.game.halia.mudar_estado("idle")
        self.ativo = False
        self.fase = "INATIVO"
        self.subfase_voo = "CONCLUIDO"
        self.shake_offset = (0, 0)
        if getattr(self.game, "slot_atual", None):
            self.game.salvar_estado(self.game.slot_atual, tipo="autosave")
        self.game.caixa_dialogo.iniciar_dialogo("despertar_ataque_dragao_vila")

    def desenhar_mundo(self, superficie_mundo):
        """Renderiza dragão, sopro, chamas, explosões e fumaça no espaço do mundo."""
        if not self.ativo or self.fase not in ("VOO_DRAGAO", "HALIA_DESPERTANDO"):
            return

        # 1. Focos de fogo acesos durante o ataque
        for fogo in self.focos_fogo_ativos:
            fogo.desenhar(superficie_mundo)

        # 2. Colunas de fumaça preta volumétrica que sobem dos destroços
        for col in self.colunas_fumaca:
            for p in col["particulas"]:
                frac = max(0.0, p["vida"] / p["vida_max"])
                alpha = int(p["alpha"] * (frac ** 1.2))
                r = int(p["raio"])
                if r > 0 and alpha > 0:
                    s_fum = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                    pygame.draw.circle(s_fum, (35, 30, 32, alpha), (r, r), r)
                    superficie_mundo.blit(s_fum, (int(p["x"] - r), int(p["y"] - r)))

        # 3. Torrentes de labaredas do sopro do dragão
        for p in self.particulas_sopro:
            raio = max(1, int(p["raio"]))
            pygame.draw.circle(superficie_mundo, p["cor"], (int(p["x"]), int(p["y"])), raio)

        # 4. Detonações e ondas de choque em expansão
        for exp in self.explosoes:
            idx = min(len(exp["frames"]) - 1, int(exp["frame_idx"]))
            frame_exp = exp["frames"][idx]
            ew, eh = frame_exp.get_size()
            superficie_mundo.blit(frame_exp, (exp["x"] - ew // 2, exp["y"] - eh // 2))

            # Clarão pulsante de impacto
            superficie_mundo.blit(self._glow_explosao_surf, (exp["x"] - 180, exp["y"] - 180))

            # Onda de choque em anel
            if exp["onda_ativa"]:
                r_onda = int(exp["raio_onda"])
                if r_onda > 1:
                    pygame.draw.circle(superficie_mundo, (255, 235, 180), (exp["x"], exp["y"]), r_onda, width=3)
                    pygame.draw.circle(superficie_mundo, (255, 110, 20), (exp["x"], exp["y"]), max(1, r_onda - 4), width=2)

        # 5. Sombra no solo e corpo do Dragão Vermelho no ar
        if self.fase == "VOO_DRAGAO" and -350 <= self.dragao_x <= 2500:
            frames_atuais = self.frames_flight
            idx_d = min(len(frames_atuais) - 1, int(self.dragao_frame_idx))
            sprite_dragao = frames_atuais[idx_d]

            # Inversão horizontal se virado para a esquerda
            if not self.virado_direita:
                sprite_base = pygame.transform.flip(sprite_dragao, True, False)
            else:
                sprite_base = sprite_dragao

            # Rotação aerodinâmica suave (banking) ancorada no centro
            orig_rect = sprite_base.get_rect(topleft=(int(self.dragao_x), int(self.dragao_y)))
            if abs(self.dragao_angulo) > 0.5:
                sprite_render = pygame.transform.rotate(sprite_base, self.dragao_angulo)
                draw_rect = sprite_render.get_rect(center=orig_rect.center)
            else:
                sprite_render = sprite_base
                draw_rect = orig_rect

            # Projeção da sombra no solo conforme a altitude aparente
            sombra_surf = self._sombra_dragao_surf if self.altitude_aparente < 180 else self._sombra_alta_surf
            dist_chao = max(100, min(240, 120 + int(self.altitude_aparente * 0.35)))
            sombra_y = min(1440, int(self.dragao_y + dist_chao))
            superficie_mundo.blit(sombra_surf, (int(self.dragao_x + 35), sombra_y))

            # Renderização do corpo do Dragão Vermelho sobrevoando a vila
            superficie_mundo.blit(sprite_render, draw_rect.topleft)

            # Clarão ardente na boca enquanto sopra fogo
            if self.subfase_voo in ("PASSE_NORTE", "PASSE_SUL") and (
                (self.subfase_voo == "PASSE_NORTE" and 280 <= self.dragao_x <= 1860) or
                (self.subfase_voo == "PASSE_SUL" and 420 <= self.dragao_x <= 1820)
            ):
                bx = self.dragao_x + (int(246 * self.dragao_escala) if self.virado_direita else int(14 * self.dragao_escala))
                by = self.dragao_y + int(118 * self.dragao_escala)
                superficie_mundo.blit(self._glow_boca_surf, (bx - 60, by - 60))

    def desenhar_tela(self, tela):
        """Renderiza vinheta narrativa, fades e clarões de explosão em coordenadas de tela."""
        if not self.ativo:
            return

        larg_tela, alt_tela = tela.get_width(), tela.get_height()

        # Vinheta narrativa durante o sono de Halia
        if self.fase == "DORMINDO":
            overlay = pygame.Surface((larg_tela, alt_tela))
            overlay.fill((10, 10, 14))
            tela.blit(overlay, (0, 0))

            card_w, card_h = 760, 260
            cx = (larg_tela - card_w) // 2
            cy = (alt_tela - card_h) // 2
            pygame.draw.rect(tela, (16, 18, 24), (cx, cy, card_w, card_h), border_radius=8)
            pygame.draw.rect(tela, (196, 191, 182), (cx, cy, card_w, card_h), width=1, border_radius=8)
            pygame.draw.rect(tela, (215, 190, 135), (cx + 12, cy + 12, card_w - 24, card_h - 24), width=1, border_radius=6)

            fonte_tit = ResourceManager.carregar_fonte("sunday", 26)
            fonte_sub = ResourceManager.carregar_fonte("just_breathe", 23)
            fonte_pula = ResourceManager.carregar_fonte("contrail", 15)

            txt_l1 = fonte_tit.render("A Noite no Refúgio de Oakhaven", True, (215, 190, 135))
            txt_l2 = fonte_sub.render("O crepitar suave da lareira na Casa de Hóspedes envolvia a vila em silêncio...", True, (246, 243, 236))
            txt_l3 = fonte_sub.render("Halia adormeceu sob o teto acolhedor, ignorando a tempestade de fogo que se aproximava.", True, (196, 191, 182))
            txt_pula = fonte_pula.render("[ ENTER / ESPAÇO: Avançar ]", True, (125, 125, 132))

            tela.blit(txt_l1, (cx + (card_w - txt_l1.get_width()) // 2, cy + 42))
            tela.blit(txt_l2, (cx + (card_w - txt_l2.get_width()) // 2, cy + 102))
            tela.blit(txt_l3, (cx + (card_w - txt_l3.get_width()) // 2, cy + 144))
            tela.blit(txt_pula, (cx + (card_w - txt_pula.get_width()) // 2, cy + card_h - 38))

        # Clarão de impacto das explosões (Flash de Calor)
        elif self.flash_clarão > 0 and self.fase == "VOO_DRAGAO":
            surf_flash = pygame.Surface((larg_tela, alt_tela))
            surf_flash.fill((255, 180, 80))
            surf_flash.set_alpha(min(160, int(self.flash_clarão)))
            tela.blit(surf_flash, (0, 0))

        # Fades de transição suaves
        elif self.alpha_fade > 0 and self.fase in ("ENTRANDO_CASA", "VOO_DRAGAO"):
            fade_surf = pygame.Surface((larg_tela, alt_tela))
            fade_surf.fill((10, 10, 14))
            fade_surf.set_alpha(int(self.alpha_fade))
            tela.blit(fade_surf, (0, 0))
