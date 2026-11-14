# src/mechanics/cutscene_manager.py
import pygame
import random
import math
from src.utils.resource_manager import ResourceManager
from src.mechanics.cena_base import CenaBase


class CutsceneManager(CenaBase):
    """
    Gerenciador das Cutscenes Cinemáticas e Efeitos Visuais de Magia no Overworld:
    - Bola de Fogo: projétil ardente com rastro dinâmico de brasas, detonação expansiva,
      screen shake, ejeção de fragmentos e acendimento de chamas no cenário.
    - Levitação Gravitacional: controle de elevação arcana, auras e poeira mágica.
    """

    VELOCIDADE_PROJETIL_FOGO = 960.0  # 16 px/quadro * 60 FPS
    VELOCIDADE_RECUO_HALIA = 240.0    # 4 px/quadro * 60 FPS
    DURACAO_EXPLOSAO = 85.0 / 60.0    # ~1.42 s (equivalente a 85 quadros a 60 FPS)
    DURACAO_LEVITACAO = 50.0 / 60.0   # ~0.83 s (equivalente a 50 quadros a 60 FPS)

    def __init__(self, game):
        # Estado da explosão (inicializado antes de CenaBase.__init__ para @ativo.setter)
        self.explosao_ativa = False
        self.timer_explosao = 0.0
        super().__init__(game=game, on_concluido=None)
        
        # Estado do projétil de fogo
        self.particulas_rastro = []
        
        # Partículas e efeitos da explosão
        self.particulas_explosao = []
        self.fragmentos_rocha = []
        self.shake_offset = (0, 0)

        # Sprites oficiais organizadas de explosão e fogo
        self.frames_explosao = ResourceManager.carregar_frames_pasta("efeitos/explosao/explosao_1")
        self.frames_fagulhas = ResourceManager.carregar_frames_pasta("efeitos/fogo/chama_fagulhas_brasas")
        self.frames_chama_pequena = ResourceManager.carregar_frames_pasta("efeitos/fogo/chama_fogo_pequeno")

    @property
    def ativo(self):
        magia = getattr(self.game, "magia_ativa", None) if self.game is not None else None
        return bool((magia not in (None, "CONCLUIDO")) or self.explosao_ativa)

    @ativo.setter
    def ativo(self, valor):
        if not valor:
            self.explosao_ativa = False
            if self.game is not None and getattr(self.game, "magia_ativa", None) not in (None, "CONCLUIDO"):
                self.game.magia_ativa = "CONCLUIDO"

    def iniciar(self, tipo_magia=None, on_concluido=None):
        """Inicia um ciclo de cutscene mágica ('FOGO' ou 'LEVITAR') e reinicia callbacks."""
        self._reiniciar_estado_execucao(on_concluido=on_concluido)
        self.explosao_ativa = False
        self.timer_explosao = 0.0
        self.particulas_rastro.clear()
        self.particulas_explosao.clear()
        self.fragmentos_rocha.clear()
        self.shake_offset = (0, 0)

        if tipo_magia in ("FOGO", "LEVITAR") and self.game is not None:
            self.game.magia_ativa = tipo_magia
            self.game.magia_usada_no_puzzle = tipo_magia
            self.game.timer_magia = 0.0
            self.game.bola_fogo_ativa = False
            self.game.distanciando_halia = (tipo_magia == "FOGO")

    def handle_event(self, evento):
        """Permite pular a cutscene mágica com ESC."""
        if not self.ativo:
            return False
        if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
            self.pular()
            return True
        return False

    def atualizar(self, dt=None):
        """Implementação do contrato CenaBase delegando para atualizar_magia."""
        return self.atualizar_magia(dt)

    def desenhar(self, tela):
        """Implementação do contrato CenaBase delegando para desenhar_efeitos."""
        return self.desenhar_efeitos(tela)

    def finalizar(self):
        """Finaliza a cutscene mágica ativa garantindo estado narrativo e callback único."""
        if self.game is not None:
            magia = getattr(self.game, "magia_ativa", None)
            if magia not in ("FOGO", "LEVITAR") and self.explosao_ativa:
                magia = "FOGO"

            if magia in ("FOGO", "LEVITAR") and self.concluido:
                self._reiniciar_estado_execucao()

            if magia == "FOGO":
                if hasattr(self.game, "halia") and self.game.halia:
                    if self.game.halia.x > 850:
                        self.game.halia.x = 850
                    self.game.halia.virado_direita = True
                    self.game.halia.direcao = "direita"
                    self.game.halia.mudar_estado("idle")
                if hasattr(self.game, "mapa_casa") and hasattr(self.game.mapa_casa, "desobstruir_estrada"):
                    self.game.mapa_casa.desobstruir_estrada("FOGO")
                self.game.magia_usada_no_puzzle = "FOGO"
                self.game.magia_ativa = "CONCLUIDO"
                self.game.distanciando_halia = False
                self.game.bola_fogo_ativa = False
                self.game.timer_magia = 0.0
                self.explosao_ativa = False
                self.timer_explosao = 0.0
                self.shake_offset = (0, 0)
                self.particulas_rastro.clear()
                self.particulas_explosao.clear()
                self.fragmentos_rocha.clear()
                if hasattr(self.game, "conquistas") and self.game.conquistas:
                    self.game.conquistas.desbloquear("fogo_destrutivo")
                if hasattr(self.game, "caixa_dialogo") and self.game.caixa_dialogo:
                    self.game.caixa_dialogo.iniciar_dialogo("pos_fogo")
                self.game.conversa_combate_ativa = True
            elif magia == "LEVITAR":
                if hasattr(self.game, "mapa_casa") and hasattr(self.game.mapa_casa, "desobstruir_estrada"):
                    self.game.mapa_casa.desobstruir_estrada("LEVITAR")
                self.game.magia_usada_no_puzzle = "LEVITAR"
                self.game.magia_ativa = "CONCLUIDO"
                self.game.distanciando_halia = False
                self.game.bola_fogo_ativa = False
                self.game.timer_magia = 0.0
                self.explosao_ativa = False
                self.timer_explosao = 0.0
                self.shake_offset = (0, 0)
                self.particulas_rastro.clear()
                self.particulas_explosao.clear()
                self.fragmentos_rocha.clear()
                if hasattr(self.game, "caixa_dialogo") and self.game.caixa_dialogo:
                    self.game.caixa_dialogo.iniciar_dialogo("pos_levitar")
                self.game.conversa_combate_ativa = True

        return super().finalizar()

    def pular(self):
        """Pula a cutscene mágica aplicando as mesmas consequências de assistir até o fim."""
        return self.finalizar()

    def _obter_dt(self, dt=None):
        """Retorna delta-time em segundos garantindo fallback seguro a 1/60s."""
        if isinstance(dt, (int, float)) and dt > 0:
            return float(dt)
        dt_jogo = getattr(self.game, "dt", 1.0 / 60.0)
        if isinstance(dt_jogo, (int, float)) and dt_jogo > 0:
            return float(dt_jogo)
        return 1.0 / 60.0

    def atualizar_magia(self, dt=None):
        """Atualiza a lógica cinemática das magias e suas fases de execução."""
        dt = self._obter_dt(dt)

        # Atualiza tremor de tela (shake)
        if self.timer_explosao > 0:
            # Guarda defensiva para valores legados atribuídos em número de quadros (> 2s)
            if self.timer_explosao > 2.0:
                self.timer_explosao /= 60.0
            intensidade = min(7, max(1, int((self.timer_explosao / self.DURACAO_EXPLOSAO) * 8)))
            self.shake_offset = (random.randint(-intensidade, intensidade), random.randint(-intensidade, intensidade))
            if not self.explosao_ativa:
                self.timer_explosao = max(0.0, self.timer_explosao - dt)
        else:
            self.shake_offset = (0, 0)

        # Atualiza partículas de explosão ativas
        if self.explosao_ativa:
            self._atualizar_particulas_explosao(dt)

        if self.game.magia_ativa is None or self.game.magia_ativa == "CONCLUIDO":
            return False

        if self.concluido and self.game.magia_ativa in ("FOGO", "LEVITAR"):
            self._reiniciar_estado_execucao()

        # 1. Recuo estratégico de Halia para conjuração
        if self.game.distanciando_halia:
            if self.game.halia.x > 850:
                self.game.halia.x -= self.VELOCIDADE_RECUO_HALIA * dt
                self.game.halia.virado_direita = False
                self.game.halia.direcao = "esquerda"
                self.game.halia.mudar_estado("andar")
                self.game.halia.atualizar_animacao()
            else:
                self.game.distanciando_halia = False
                self.game.halia.virado_direita = True
                self.game.halia.direcao = "direita"
                self.game.halia.mudar_estado("idle")

                if self.game.magia_ativa == "FOGO":
                    self.game.magia_usada_no_puzzle = "FOGO"
                    self.game.bola_fogo_ativa = True
                    self.game.bola_fogo_x = self.game.halia.x + self.game.halia.largura + 12
                    self.game.bola_fogo_y = self.game.halia.y + (self.game.halia.altura // 2) - 6
                    self.particulas_rastro.clear()
                    self.explosao_ativa = False
                elif self.game.magia_ativa == "LEVITAR":
                    self.game.magia_usada_no_puzzle = "LEVITAR"
                    self.game.timer_magia = 0.0
        else:
            self.game.timer_magia += dt
            if self.game.magia_ativa == "FOGO":
                self._processar_fogo(dt)
            elif self.game.magia_ativa == "LEVITAR":
                self._processar_levitacao(dt)

    def _processar_fogo(self, dt=None):
        """Gerencia o voo veloz da bola de fogo, o impacto e a subsequente explosão."""
        dt = self._obter_dt(dt)

        # Atualiza partículas do rastro deixado pela bola de fogo
        vivas_rastro = []
        for p in self.particulas_rastro:
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            p["vida"] -= dt
            if p["vida"] > 0:
                vivas_rastro.append(p)
        self.particulas_rastro = vivas_rastro

        if self.game.bola_fogo_ativa:
            self.game.bola_fogo_x += self.VELOCIDADE_PROJETIL_FOGO * dt

            # Emite fagulhas incandescentes e brasas no rastro do voo
            qtd_fagulhas = max(1, int(round(2 * dt * 60.0)))
            for _ in range(qtd_fagulhas):
                self.particulas_rastro.append({
                    "x": self.game.bola_fogo_x - random.uniform(8, 22),
                    "y": self.game.bola_fogo_y + random.uniform(-10, 10),
                    "vx": random.uniform(-55.0, -20.0),
                    "vy": random.uniform(-20.0, 20.0),
                    "vida": random.uniform(0.25, 0.55),
                    "vida_max": 0.55,
                    "raio": random.uniform(2.5, 5.0),
                    "cor": random.choice([(255, 230, 100), (255, 160, 30), (255, 80, 10), (240, 40, 10)])
                })

            # Ponto de colisão com as rochas do bloqueio
            if self.game.bola_fogo_x >= 1050:
                self.game.bola_fogo_ativa = False
                self._disparar_explosao(self.game.bola_fogo_x, self.game.bola_fogo_y)

        elif self.explosao_ativa:
            self.timer_explosao = max(0.0, self.timer_explosao - dt)
            if self.timer_explosao <= 0:
                self.finalizar()

    def _disparar_explosao(self, centro_x, centro_y):
        """Detona a explosão no obstáculo, gerando onda de choque, fragmentos e fogo no ambiente."""
        self.explosao_ativa = True
        self.timer_explosao = self.DURACAO_EXPLOSAO  # Tempo em segundos equivalente a 85 quadros a 60 FPS
        self.exp_centro_x = centro_x
        self.exp_centro_y = centro_y

        # Desobstrui e acende as chamas no ambiente de imediato
        self.game.mapa_casa.desobstruir_estrada("FOGO")

        # 1. Dezenas de partículas de fogo e fagulhas em expansão radial
        self.particulas_explosao.clear()
        for _ in range(55):
            angulo = random.uniform(0, math.pi * 2)
            velocidade = random.uniform(100.0, 320.0)
            self.particulas_explosao.append({
                "x": centro_x + random.uniform(-12, 12),
                "y": centro_y + random.uniform(-12, 12),
                "vx": math.cos(angulo) * velocidade,
                "vy": math.sin(angulo) * velocidade - random.uniform(20.0, 65.0),  # Leve empuxo térmico
                "vida": random.uniform(0.65, 1.25),
                "vida_max": 1.25,
                "raio": random.uniform(3.0, 7.5),
                "cor": random.choice([(255, 255, 210), (255, 210, 40), (255, 130, 20), (245, 50, 10), (180, 25, 10)])
            })

        # 2. Fragmentos de rocha estilhaçada arremessados pelos ares
        self.fragmentos_rocha.clear()
        for _ in range(16):
            ang = random.uniform(-math.pi * 0.88, -math.pi * 0.12)  # Ejetados para cima e para os lados
            vel = random.uniform(130.0, 270.0)
            self.fragmentos_rocha.append({
                "x": centro_x + random.uniform(-18, 18),
                "y": centro_y + random.uniform(-18, 18),
                "vx": math.cos(ang) * vel,
                "vy": math.sin(ang) * vel,
                "gravidade": 480.0,
                "largura": random.randint(6, 14),
                "altura": random.randint(5, 12),
                "angulo": random.uniform(0, 360),
                "vel_rot": random.uniform(-360.0, 360.0),
                "vida": random.uniform(0.70, 1.20),
                "vida_max": 1.20,
                "cor": random.choice([(70, 68, 65), (95, 90, 85), (55, 50, 48), (115, 110, 105)])
            })

    def _atualizar_particulas_explosao(self, dt=None):
        """Atualiza a física dos fragmentos e faíscas da explosão."""
        dt = self._obter_dt(dt)
        amortecimento = 0.93 ** (dt * 60.0)

        vivas_exp = []
        for p in self.particulas_explosao:
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            p["vx"] *= amortecimento  # Resistência do ar proporcional ao tempo
            p["vy"] *= amortecimento
            p["vida"] -= dt
            if p["vida"] > 0:
                vivas_exp.append(p)
        self.particulas_explosao = vivas_exp

        vivas_rocha = []
        for r in self.fragmentos_rocha:
            r["x"] += r["vx"] * dt
            r["y"] += r["vy"] * dt
            r["vy"] += r["gravidade"] * dt
            r["angulo"] += r["vel_rot"] * dt
            r["vida"] -= dt
            if r["vida"] > 0:
                vivas_rocha.append(r)
        self.fragmentos_rocha = vivas_rocha

    def _processar_levitacao(self, dt=None):
        """Conduz a transição cinematográfica da levitação arcana."""
        self._obter_dt(dt)
        progresso = min(1.0, self.game.timer_magia / self.DURACAO_LEVITACAO)
        
        # Atualiza a posição e aura das pedras através do delegador do mapa
        if hasattr(self.game.mapa_casa, 'atualizar_levitacao_minigame'):
            self.game.mapa_casa.atualizar_levitacao_minigame(progresso)

        if self.game.timer_magia >= self.DURACAO_LEVITACAO:
            self.finalizar()

    def desenhar_efeitos(self, tela):
        """Renderiza a bola de fogo animada, o rastro e o impacto pirotécnico no overworld."""
        # Aplica o tremor de tela (shake) em caso de explosão ativa
        ox, oy = self.shake_offset

        # 1. Rastro de partículas deixado no ar pela bola de fogo
        for p in self.particulas_rastro:
            pct = max(0.0, p["vida"] / p["vida_max"])
            raio = max(1, int(p["raio"] * pct))
            alpha = int(240 * pct)
            surf_p = pygame.Surface((raio * 2, raio * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf_p, (*p["cor"][:3], alpha), (raio, raio), raio)
            tela.blit(surf_p, (int(p["x"] - raio + ox), int(p["y"] - raio + oy)))

        # 2. A Bola de Fogo em voo (Projétil de Alta Fidelidade)
        if self.game.mapa_casa.cenario_atual == "ESTRADA_2" and getattr(self.game, 'bola_fogo_ativa', False):
            bx = int(self.game.bola_fogo_x + ox)
            by = int(self.game.bola_fogo_y + oy)
            tempo = pygame.time.get_ticks() / 1000.0

            # 2.1. Glow térmico translúcido no ambiente
            raio_glow = 38
            surf_glow = pygame.Surface((raio_glow * 2, raio_glow * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf_glow, (255, 110, 15, 60), (raio_glow, raio_glow), raio_glow)
            pygame.draw.circle(surf_glow, (255, 200, 50, 95), (raio_glow, raio_glow), raio_glow // 2)
            tela.blit(surf_glow, (bx - raio_glow, by - raio_glow))

            # 2.2. Cauda ondulante de labaredas (chama horizontal)
            comprimento_cauda = 26
            pontos_cauda = [
                (bx + 4, by - 12),
                (bx - comprimento_cauda + math.sin(tempo * 20.0) * 4, by),
                (bx + 4, by + 12)
            ]
            pygame.draw.polygon(tela, (230, 55, 10), pontos_cauda)

            pontos_cauda_interna = [
                (bx + 2, by - 7),
                (bx - (comprimento_cauda - 8) + math.sin(tempo * 24.0) * 3, by),
                (bx + 2, by + 7)
            ]
            pygame.draw.polygon(tela, (255, 160, 20), pontos_cauda_interna)

            # 2.3. Núcleo Incandescente Multicamadas com pulso
            pulso = math.sin(tempo * 18.0) * 1.5
            r_ext = max(10, int(18 + pulso))
            r_med = max(6, int(12 + pulso))
            r_int = max(3, int(6 + pulso))

            pygame.draw.circle(tela, (235, 45, 10), (bx, by), r_ext)
            pygame.draw.circle(tela, (255, 145, 20), (bx, by), r_med)
            pygame.draw.circle(tela, (255, 235, 110), (bx, by), r_int)
            pygame.draw.circle(tela, (255, 255, 240), (bx, by), max(2, r_int // 2))

        # 3. Explosão e Onda de Choque no Impacto
        if self.explosao_ativa:
            cx = int(self.exp_centro_x + ox)
            cy = int(self.exp_centro_y + oy)
            duracao_exp = self.DURACAO_EXPLOSAO
            pct_exp = min(1.0, max(0.0, 1.0 - (self.timer_explosao / duracao_exp)))

            # 3.1. Sprites da Nova Explosão Oficial
            if self.frames_explosao:
                idx_exp = min(len(self.frames_explosao) - 1, int(pct_exp * len(self.frames_explosao)))
                frame_exp = self.frames_explosao[idx_exp]
                tamanho_exp = 220  # Escala épica no obstáculo para permitir nitidez absoluta
                img_exp = pygame.transform.scale(frame_exp, (tamanho_exp, tamanho_exp))
                tela.blit(img_exp, (cx - tamanho_exp // 2, cy - tamanho_exp // 2))

            # 3.2. Clarão de Detonação e Onda de Choque Expansiva
            raio_onda = int(22 + pct_exp * 120)
            alpha_onda = max(0, int(230 * (1.0 - pct_exp)))
            if alpha_onda > 0 and raio_onda > 2:
                surf_onda = pygame.Surface((raio_onda * 2 + 4, raio_onda * 2 + 4), pygame.SRCALPHA)
                pygame.draw.circle(surf_onda, (255, 210, 80, alpha_onda // 2), (raio_onda + 2, raio_onda + 2), raio_onda, 4)
                pygame.draw.circle(surf_onda, (255, 255, 220, alpha_onda), (raio_onda + 2, raio_onda + 2), max(1, raio_onda - 4), 2)
                tela.blit(surf_onda, (cx - raio_onda - 2, cy - raio_onda - 2))

            # 3.2. Fragmentos de Rocha Ejetados pela Força da Explosão
            for r in self.fragmentos_rocha:
                rx, ry = int(r["x"] + ox), int(r["y"] + oy)
                surf_pedra = pygame.Surface((r["largura"], r["altura"]), pygame.SRCALPHA)
                surf_pedra.fill(r["cor"])
                surf_rot = pygame.transform.rotate(surf_pedra, r["angulo"])
                tela.blit(surf_rot, (rx - surf_rot.get_width() // 2, ry - surf_rot.get_height() // 2))

            # 3.3. Partículas e Fagulhas Incandescentes da Detonação
            for p in self.particulas_explosao:
                pct_p = max(0.0, p["vida"] / p["vida_max"])
                raio_p = max(1, int(p["raio"] * pct_p))
                alpha_p = int(255 * pct_p)
                surf_p = pygame.Surface((raio_p * 2, raio_p * 2), pygame.SRCALPHA)
                pygame.draw.circle(surf_p, (*p["cor"][:3], alpha_p), (raio_p, raio_p), raio_p)
                tela.blit(surf_p, (int(p["x"] - raio_p + ox), int(p["y"] - raio_p + oy)))