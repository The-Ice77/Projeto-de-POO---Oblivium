# src/entities/elemento_cenario.py
import pygame
import random
import math
from abc import ABC, abstractmethod
from src.utils.resource_manager import ResourceManager


class ElementoCenario(ABC):
    """
    Classe base abstrata para objetos decorativos, props e efeitos dinâmicos de cenário.
    Padroniza:
    - Posição (x, y) com ancoragem precisa na base do solo (y é o chão de contato)
    - Ciclos de animação dessincronizados para evitar repetição mecânica
    - Halo de iluminação (glow) pulsante com cores e intensidades configuráveis
    - Emissor autônomo de partículas temáticas (fagulhas, brasas, fumaça, orbes)
    """

    def __init__(self, x, y, escala=1.0, glow_base=35, vel_anim=0.24,
                 cor_glow_externo=(255, 110, 15), cor_glow_interno=(255, 205, 55)):
        self.x = float(x)
        self.y = float(y)
        self.escala_base = float(escala)
        self.glow_base = glow_base
        self.visivel = True

        # Cores da iluminação ambiente no solo
        self.cor_glow_ext = cor_glow_externo
        self.cor_glow_int = cor_glow_interno

        # Controle de animação
        self.frames = []
        self.frame_idx = 0.0
        self.vel_anim = vel_anim

        # Pulsação orgânica da luz
        self.fase_pulso_luz = random.uniform(0.0, 10.0)
        self.vel_pulso_luz = random.uniform(3.5, 5.5)

        # Sistema de partículas dinâmicas do prop
        self.particulas = []

    def atualizar_animacao(self, dt=0.016):
        """Avança o ciclo de frames da textura animada."""
        if self.frames:
            self.frame_idx += self.vel_anim
            if self.frame_idx >= len(self.frames):
                self.frame_idx = 0.0

    def atualizar_glow(self, dt=0.016):
        """Avança a oscilação senoidal do halo de luz emitido."""
        self.fase_pulso_luz += dt * self.vel_pulso_luz

    def atualizar_particulas(self, dt=0.016):
        """Atualiza física e tempo de vida de todas as partículas ativas."""
        vivas = []
        for p in self.particulas:
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            p["vida"] -= dt
            if p["vida"] > 0:
                vivas.append(p)
        self.particulas = vivas

    @abstractmethod
    def atualizar(self, dt=0.016, **kwargs):
        """Comportamento específico de atualização da entidade de cenário."""
        pass

    def desenhar_glow(self, tela, offset_y=-4):
        """Renderiza o halo de iluminação pulsante ancorado na base do chão."""
        if self.glow_base <= 0:
            return

        pulso_luz = (math.sin(self.fase_pulso_luz) + 1.0) * 0.5
        raio_glow = max(10, int(self.glow_base * (0.88 + pulso_luz * 0.24)))
        surf_luz = pygame.Surface((raio_glow * 2, raio_glow * 2), pygame.SRCALPHA)

        alpha_ext = int(42 + pulso_luz * 22)
        alpha_int = int(75 + pulso_luz * 30)

        pygame.draw.circle(surf_luz, (*self.cor_glow_ext[:3], alpha_ext), (raio_glow, raio_glow), raio_glow)
        pygame.draw.circle(surf_luz, (*self.cor_glow_int[:3], alpha_int), (raio_glow, raio_glow), raio_glow // 2)

        pos_gx = int(self.x - raio_glow)
        pos_gy = int(self.y + offset_y - raio_glow)
        tela.blit(surf_luz, (pos_gx, pos_gy))

    def desenhar_sprite(self, tela):
        """Renderiza o frame atual da sprite ancorado na base inferior (self.y)."""
        if not self.frames:
            return

        idx = int(self.frame_idx) % len(self.frames)
        frame_base = self.frames[idx]

        fw = max(1, int(frame_base.get_width() * self.escala_base))
        fh = max(1, int(frame_base.get_height() * self.escala_base))
        frame_render = pygame.transform.scale(frame_base, (fw, fh))

        pos_x = int(self.x - fw // 2)
        pos_y = int(self.y - fh)
        tela.blit(frame_render, (pos_x, pos_y))

    def desenhar_particulas(self, tela):
        """Renderiza as partículas emitidas com atenuação gradual de tamanho e transparência."""
        for p in self.particulas:
            pct = max(0.0, p["vida"] / p["vida_max"])
            raio = max(1, int(p["raio"] * pct))
            alpha = int(240 * pct)
            surf_p = pygame.Surface((raio * 2, raio * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf_p, (*p["cor"][:3], alpha), (raio, raio), raio)
            tela.blit(surf_p, (int(p["x"] - raio), int(p["y"] - raio)))

    def desenhar(self, tela):
        """Template Method padrão: renderiza halo de luz, sprite e partículas."""
        if not self.visivel:
            return

        self.desenhar_glow(tela)
        self.desenhar_sprite(tela)
        self.desenhar_particulas(tela)


class ChamaIndependente(ElementoCenario):
    """
    Entidade visual de fogo com comportamento dinâmico e independente.
    Herda de ElementoCenario e implementa:
    - Uso das novas sprites oficiais em todas as cores (laranja, azul, verde, roxa, amarela, branca)
    - Emissão autônoma de brasas e fagulhas incandescentes com influência de vento
    - Iluminação quente/mística e pulsante com ancoragem fiel no solo
    """

    CORES_CONFIG = {
        "laranja": {
            "glow_ext": (255, 110, 15), "glow_int": (255, 205, 55),
            "particulas": [(255, 215, 60), (255, 140, 25), (255, 80, 10), (245, 235, 130)]
        },
        "azul": {
            "glow_ext": (30, 110, 255), "glow_int": (110, 210, 255),
            "particulas": [(90, 215, 255), (40, 140, 255), (160, 240, 255), (230, 250, 255)]
        },
        "verde": {
            "glow_ext": (25, 190, 50), "glow_int": (120, 255, 140),
            "particulas": [(80, 255, 130), (35, 190, 65), (180, 255, 200), (230, 255, 220)]
        },
        "roxa": {
            "glow_ext": (160, 35, 220), "glow_int": (220, 115, 255),
            "particulas": [(210, 95, 255), (145, 30, 225), (245, 180, 255), (255, 220, 255)]
        },
        "amarela": {
            "glow_ext": (255, 170, 15), "glow_int": (255, 240, 90),
            "particulas": [(255, 245, 130), (255, 195, 30), (255, 150, 10), (255, 255, 200)]
        },
        "branca": {
            "glow_ext": (170, 190, 220), "glow_int": (240, 245, 255),
            "particulas": [(255, 255, 255), (210, 225, 245), (160, 185, 220), (240, 245, 255)]
        },
    }

    def __init__(self, x, y, tipo="media", cor="laranja", escala=1.2, glow_base=38, vel_anim=None):
        # Determina a cor base
        self.cor = cor.lower()
        if "_" in tipo:
            for c_nome in self.CORES_CONFIG.keys():
                if tipo.endswith(f"_{c_nome}"):
                    self.cor = c_nome
                    tipo = tipo[:-len(f"_{c_nome}")]
                    break

        cfg_cor = self.CORES_CONFIG.get(self.cor, self.CORES_CONFIG["laranja"])

        super().__init__(
            x=x,
            y=y,
            escala=escala,
            glow_base=glow_base,
            vel_anim=vel_anim or random.uniform(0.20, 0.28),
            cor_glow_externo=cfg_cor["glow_ext"],
            cor_glow_interno=cfg_cor["glow_int"]
        )
        self.tipo = tipo
        self.cores_particulas = cfg_cor["particulas"]

        # Localiza a pasta nos assets
        dir_nome = f"{tipo}_{self.cor}"
        pasta = f"efeitos/fogo/{dir_nome}"
        self.frames = ResourceManager.carregar_frames_pasta(pasta)
        if not self.frames:
            # Fallback para laranja se a variante não existir
            pasta = f"efeitos/fogo/{tipo}_laranja"
            self.frames = ResourceManager.carregar_frames_pasta(pasta)
            if not self.frames:
                self.frames = ResourceManager.carregar_frames_pasta("efeitos/fogo/media_laranja")

        # Dessincronização individual do ciclo de animação
        if self.frames:
            self.frame_idx = random.uniform(0.0, float(len(self.frames) - 1))

    def atualizar(self, dt=0.016, vento_x=0.0, **kwargs):
        """Atualiza a labareda, iluminação de solo e emissão de fagulhas."""
        self.atualizar_animacao(dt)
        self.atualizar_glow(dt)

        # Emissão contínua de fagulhas incandescentes que sobem ao ar
        if self.frames and random.random() < 0.25:
            fw = self.frames[0].get_width() * self.escala_base
            fh = self.frames[0].get_height() * self.escala_base
            self.particulas.append({
                "x": self.x + random.uniform(-fw * 0.35, fw * 0.35),
                "y": self.y - random.uniform(fh * 0.1, fh * 0.7),
                "vx": random.uniform(-10.0, 10.0) + vento_x * 12.0,
                "vy": random.uniform(-55.0, -25.0),
                "vida": random.uniform(0.45, 0.95),
                "vida_max": 0.95,
                "raio": random.uniform(1.5, 3.0),
                "cor": random.choice(self.cores_particulas)
            })

        self.atualizar_particulas(dt)


# Aliases
Chama = ChamaIndependente
PropCenario = ElementoCenario
