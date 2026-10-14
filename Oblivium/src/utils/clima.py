# src/utils/clima.py
import pygame
import random
import math
from src.utils.resource_manager import ResourceManager


class GotaChuva:
    """Representa um pingo individual de chuva com física e camada de profundidade."""
    def __init__(self, largura_tela, altura_tela, tipo="comum", inicializar_espalhado=False):
        self.largura_tela = largura_tela
        self.altura_tela = altura_tela
        self.reset(tipo=tipo, inicializar_espalhado=inicializar_espalhado)

    def reset(self, tipo="comum", inicializar_espalhado=False):
        self.x = random.uniform(-100, self.largura_tela + 200)
        self.y = random.uniform(-50, self.altura_tela) if inicializar_espalhado else random.uniform(-90, -10)
        self.y_chao = random.uniform(220, self.altura_tela + 30)
        self.camada_fundo = (random.random() < 0.40)

        if tipo == "pesada":
            self.vy = random.uniform(850.0, 1150.0) if not self.camada_fundo else random.uniform(750.0, 950.0)
            self.vx = random.uniform(-360.0, -260.0)
            self.escala = random.uniform(0.75, 1.15) if not self.camada_fundo else random.uniform(0.55, 0.85)
            self.alpha = random.randint(190, 255) if not self.camada_fundo else random.randint(140, 200)
        else:
            self.vy = random.uniform(620.0, 840.0) if not self.camada_fundo else random.uniform(540.0, 720.0)
            self.vx = random.uniform(-190.0, -110.0)
            self.escala = random.uniform(0.65, 0.95) if not self.camada_fundo else random.uniform(0.50, 0.75)
            self.alpha = random.randint(170, 240) if not self.camada_fundo else random.randint(120, 180)


class SplashChuva:
    """Representa o respingo animado de água quando uma gota atinge o chão."""
    def __init__(self, x, y, frames_splash, escala=1.0):
        self.x = x
        self.y = y
        self.frames = frames_splash
        self.escala = escala
        self.frame_idx = 0.0
        self.velocidade = random.uniform(14.0, 22.0)
        self.concluido = False

    def atualizar(self, dt):
        self.frame_idx += self.velocidade * dt
        if self.frame_idx >= len(self.frames):
            self.concluido = True

    def desenhar(self, superficie, areas_excluidas=None):
        if self.concluido or not self.frames:
            return
        if areas_excluidas:
            for area in areas_excluidas:
                if area.collidepoint(self.x, self.y):
                    return

        idx = min(len(self.frames) - 1, int(self.frame_idx))
        frame = self.frames[idx]
        if self.escala != 1.0:
            nw = max(1, int(frame.get_width() * self.escala))
            nh = max(1, int(frame.get_height() * self.escala))
            frame = pygame.transform.scale(frame, (nw, nh))

        superficie.blit(frame, (int(self.x - frame.get_width() // 2), int(self.y - frame.get_height() // 2)))


class FlocoNeve:
    """Representa um floco de neve flutuante com oscilação orgânica, giro e profundidade."""
    def __init__(self, largura_tela, altura_tela, tipo="neve", inicializar_espalhado=False):
        self.largura_tela = largura_tela
        self.altura_tela = altura_tela
        self.reset(tipo=tipo, inicializar_espalhado=inicializar_espalhado)

    def reset(self, tipo="neve", inicializar_espalhado=False):
        self.x = random.uniform(-60, self.largura_tela + 100)
        self.y = random.uniform(-40, self.altura_tela) if inicializar_espalhado else random.uniform(-70, -10)
        
        self.sway_phase = random.uniform(0, math.pi * 2)
        self.angulo = random.uniform(0, 360)

        if tipo == "nevasca":
            self.vy = random.uniform(90.0, 160.0)
            self.vx_vento = random.uniform(-260.0, -160.0)
            self.sway_amp = random.uniform(10.0, 25.0)
            self.sway_spd = random.uniform(3.0, 5.5)
            self.vel_rot = random.uniform(-80.0, 80.0)
            self.escala = random.uniform(0.50, 1.10)
            self.alpha = random.randint(180, 255)
        else:
            self.vy = random.uniform(40.0, 85.0)
            self.vx_vento = random.uniform(-35.0, 15.0)
            self.sway_amp = random.uniform(20.0, 42.0)
            self.sway_spd = random.uniform(1.2, 2.6)
            self.vel_rot = random.uniform(-35.0, 35.0)
            self.escala = random.uniform(0.40, 0.90)
            self.alpha = random.randint(150, 230)

    def atualizar(self, dt):
        self.sway_phase += self.sway_spd * dt
        sway_x = math.sin(self.sway_phase) * self.sway_amp * dt
        self.x += (self.vx_vento + sway_x) * dt
        self.y += self.vy * dt
        self.angulo = (self.angulo + self.vel_rot * dt) % 360

        if self.y > self.altura_tela + 30 or self.x < -80 or self.x > self.largura_tela + 80:
            self.reset(inicializar_espalhado=False)


# Constantes de Clima
MODO_LIMPO = "limpo"
MODO_COMUM = "comum"
MODO_PESADA = "pesada"
MODO_NEVE = "neve"
MODO_NEVASCA = "nevasca"


class EfeitoChuva:
    """
    Gerenciador Central de Clima de Oblivium:
    - Chuva Comum: densidade equilibrada, vento suave e splashes ocasionais.
    - Chuva Pesada (Tempestade): densidade densa, vento cortante, splashes frequentes,
      filtro tempestuoso e relâmpagos ocasionais ao longe.
    - Neve Suave: flocos brancos serenos oscilando e caindo lentamente com leve brisa.
    - Nevasca: ventania fria cortante com alta densidade de flocos e véu gélido.
    - Tempo Limpo: céu claro.
    """

    MODO_LIMPO = MODO_LIMPO
    MODO_COMUM = MODO_COMUM
    MODO_PESADA = MODO_PESADA
    MODO_NEVE = MODO_NEVE
    MODO_NEVASCA = MODO_NEVASCA

    def __init__(self, largura_tela=1280, altura_tela=720):
        self.largura = largura_tela
        self.altura = altura_tela
        self.modo_atual = self.MODO_LIMPO
        self.ativo = False

        # 1. Carregamento das texturas de chuva
        self.sprite_chuva_clara = ResourceManager.carregar_imagem("efeitos/chuva clara/rain light.png")
        self.sprite_chuva_escura = ResourceManager.carregar_imagem("efeitos/chuva escura/rain dark.png")

        # Fallback de segurança para chuva
        if not self.sprite_chuva_clara:
            self.sprite_chuva_clara = pygame.Surface((3, 22), pygame.SRCALPHA)
            self.sprite_chuva_clara.fill((160, 210, 255, 200))
        if not self.sprite_chuva_escura:
            self.sprite_chuva_escura = pygame.Surface((2, 18), pygame.SRCALPHA)
            self.sprite_chuva_escura.fill((100, 140, 210, 170))

        # 2. Carregamento dos frames de splash
        self.frames_splash = []
        splash_sheet = ResourceManager.carregar_imagem("efeitos/chuva splash/rain splash.png")
        if splash_sheet:
            largura_frame = 16
            altura_frame = 16
            total_frames = max(1, splash_sheet.get_width() // largura_frame)
            for i in range(total_frames):
                sub = splash_sheet.subsurface((i * largura_frame, 0, largura_frame, altura_frame))
                self.frames_splash.append(sub)
        else:
            for r in [2, 4, 6, 4, 2]:
                s = pygame.Surface((16, 16), pygame.SRCALPHA)
                pygame.draw.circle(s, (160, 215, 255, 180), (8, 8), r, 1)
                self.frames_splash.append(s)

        # 3. Carregamento da textura de floco de neve
        self.sprite_neve = ResourceManager.carregar_imagem("efeitos/snowflake/snowflake(1).png")
        if not self.sprite_neve:
            self.sprite_neve = pygame.Surface((12, 12), pygame.SRCALPHA)
            pygame.draw.circle(self.sprite_neve, (240, 245, 255, 220), (6, 6), 5)
            pygame.draw.circle(self.sprite_neve, (255, 255, 255, 255), (6, 6), 3)

        # 4. Conjuntos de partículas
        self.gotas = []
        self.splashes = []
        self.flocos_neve = []

        # 5. Atmosfera e relâmpagos
        self.timer_relampago = random.uniform(10.0, 22.0)
        self.brilho_relampago = 0.0

        # Superfícies de sobreposição ambiental
        self.overlay_clima = pygame.Surface((largura_tela, altura_tela), pygame.SRCALPHA)
        self.overlay_relampago = pygame.Surface((largura_tela, altura_tela))
        self.overlay_relampago.fill((235, 245, 255))

    def definir_clima(self, tipo):
        """Define o modo climático: 'limpo', 'comum' (ou 'chuva'), 'pesada', 'neve', 'nevasca'."""
        if not tipo or str(tipo).lower() in [self.MODO_LIMPO, "off", "desativado", "sol"]:
            self.modo_atual = self.MODO_LIMPO
            self.ativo = False
            self.gotas.clear()
            self.splashes.clear()
            self.flocos_neve.clear()
            self.brilho_relampago = 0.0
            return

        tipo_str = str(tipo).lower()
        if "nevasca" in tipo_str or "neve_pesada" in tipo_str or "blizzard" in tipo_str:
            self.modo_atual = self.MODO_NEVASCA
            self.ativo = True
            self.gotas.clear()
            self.splashes.clear()
            self.flocos_neve = [
                FlocoNeve(self.largura, self.altura, tipo="nevasca", inicializar_espalhado=True)
                for _ in range(195)
            ]
        elif "neve" in tipo_str or "snow" in tipo_str or "gelo" in tipo_str:
            self.modo_atual = self.MODO_NEVE
            self.ativo = True
            self.gotas.clear()
            self.splashes.clear()
            self.flocos_neve = [
                FlocoNeve(self.largura, self.altura, tipo="neve", inicializar_espalhado=True)
                for _ in range(85)
            ]
        elif "pesad" in tipo_str or "tempestade" in tipo_str or "forte" in tipo_str:
            self.modo_atual = self.MODO_PESADA
            self.ativo = True
            self.flocos_neve.clear()
            self.gotas = [
                GotaChuva(self.largura, self.altura, tipo=self.modo_atual, inicializar_espalhado=True)
                for _ in range(220)
            ]
            self.splashes.clear()
            self.timer_relampago = random.uniform(10.0, 20.0)
            self.brilho_relampago = 0.0
        else:
            self.modo_atual = self.MODO_COMUM
            self.ativo = True
            self.flocos_neve.clear()
            self.gotas = [
                GotaChuva(self.largura, self.altura, tipo=self.modo_atual, inicializar_espalhado=True)
                for _ in range(85)
            ]
            self.splashes.clear()
            self.brilho_relampago = 0.0

    def alternar_clima(self):
        """Ciclo completo: Limpo -> Chuva Comum -> Chuva Pesada -> Neve Suave -> Nevasca -> Limpo."""
        if self.modo_atual == self.MODO_LIMPO:
            self.definir_clima(self.MODO_COMUM)
        elif self.modo_atual == self.MODO_COMUM:
            self.definir_clima(self.MODO_PESADA)
        elif self.modo_atual == self.MODO_PESADA:
            self.definir_clima(self.MODO_NEVE)
        elif self.modo_atual == self.MODO_NEVE:
            self.definir_clima(self.MODO_NEVASCA)
        else:
            self.definir_clima(self.MODO_LIMPO)
        return self.modo_atual

    def definir_modo(self, tipo):
        """Alias para definir_clima."""
        return self.definir_clima(tipo)

    def atualizar(self, dt=0.016):
        """Atualiza a física de chuva, splashes, neve e relâmpagos."""
        if not self.ativo or self.modo_atual == self.MODO_LIMPO:
            return

        # 1. Neve e Nevasca
        if self.modo_atual in [self.MODO_NEVE, self.MODO_NEVASCA]:
            for fn in self.flocos_neve:
                fn.atualizar(dt)
            return

        # 2. Gotas de Chuva
        for g in self.gotas:
            g.x += g.vx * dt
            g.y += g.vy * dt

            if g.y >= g.y_chao or g.y > self.altura + 30:
                chance_splash = 0.70 if self.modo_atual == self.MODO_PESADA else 0.45
                if random.random() < chance_splash and g.y_chao < self.altura:
                    escala_sp = g.escala * 0.9
                    self.splashes.append(SplashChuva(g.x, min(self.altura - 10, g.y_chao), self.frames_splash, escala=escala_sp))

                g.reset(tipo=self.modo_atual, inicializar_espalhado=False)

            elif g.x < -120 or g.x > self.largura + 220:
                g.reset(tipo=self.modo_atual, inicializar_espalhado=False)

        # 3. Atualização dos Splashes
        vivos = []
        for sp in self.splashes:
            sp.atualizar(dt)
            if not sp.concluido:
                vivos.append(sp)
        self.splashes = vivos

        # 4. Relâmpago na Chuva Pesada
        if self.modo_atual == self.MODO_PESADA:
            self.timer_relampago -= dt
            if self.timer_relampago <= 0.0:
                self.brilho_relampago = random.uniform(0.40, 0.75)
                self.timer_relampago = random.uniform(12.0, 25.0)

            if self.brilho_relampago > 0.0:
                self.brilho_relampago = max(0.0, self.brilho_relampago - (dt * 3.8))
        else:
            self.brilho_relampago = 0.0

    def desenhar(self, superficie, areas_excluidas=None):
        """Renderiza as camadas visuais do clima sobre o mundo."""
        if not self.ativo or self.modo_atual == self.MODO_LIMPO:
            return

        # 1. RENDERIZAÇÃO DE NEVE / NEVASCA
        if self.modo_atual in [self.MODO_NEVE, self.MODO_NEVASCA]:
            for fn in self.flocos_neve:
                if areas_excluidas:
                    ignorar = False
                    for area in areas_excluidas:
                        if area.collidepoint(fn.x, fn.y):
                            ignorar = True
                            break
                    if ignorar:
                        continue

                # Rotozoom no floco de neve
                rot_neve = pygame.transform.rotozoom(self.sprite_neve, fn.angulo, fn.escala)
                if fn.alpha < 255:
                    rot_neve.set_alpha(fn.alpha)
                superficie.blit(rot_neve, (int(fn.x - rot_neve.get_width() // 2), int(fn.y - rot_neve.get_height() // 2)))

            # Véu frio ambiental
            alpha_neve = 35 if self.modo_atual == self.MODO_NEVASCA else 14
            self.overlay_clima.fill((215, 235, 255, alpha_neve))
            superficie.blit(self.overlay_clima, (0, 0))
            return

        # 2. RENDERIZAÇÃO DE CHUVA
        for sp in self.splashes:
            sp.desenhar(superficie, areas_excluidas=areas_excluidas)

        for g in self.gotas:
            if areas_excluidas:
                ponto_colisao = False
                for area in areas_excluidas:
                    if area.collidepoint(g.x, g.y):
                        ponto_colisao = True
                        break
                if ponto_colisao:
                    continue

            sprite_base = self.sprite_chuva_escura if g.camada_fundo else self.sprite_chuva_clara
            w_dest = max(1, int(sprite_base.get_width() * g.escala))
            h_dest = max(2, int(sprite_base.get_height() * g.escala))

            img_gota = pygame.transform.scale(sprite_base, (w_dest, h_dest))
            if g.alpha < 255:
                img_gota.set_alpha(g.alpha)

            superficie.blit(img_gota, (int(g.x), int(g.y)))

        # Overlay Atmosférico Dark Fantasy
        alpha_ambiente = 55 if self.modo_atual == self.MODO_PESADA else 22
        cor_filtro = (12, 18, 28, alpha_ambiente)
        self.overlay_clima.fill(cor_filtro)
        superficie.blit(self.overlay_clima, (0, 0))

        # Clarão de Relâmpago na Tempestade
        if self.brilho_relampago > 0.01:
            alpha_flash = int(self.brilho_relampago * 180)
            self.overlay_relampago.set_alpha(max(0, min(255, alpha_flash)))
            superficie.blit(self.overlay_relampago, (0, 0))
