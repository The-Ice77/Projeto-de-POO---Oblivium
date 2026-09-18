# src/utils/animations.py
import pygame
import random
import math
from src.utils.resource_manager import ResourceManager

class ParticulaFlutuante:
    """
    Classe base de física e renderização para partículas orgânicas flutuantes
    (pétalas, folhas, brasas, cinzas, poeira mágica, etc.).
    """
    def __init__(self, sprites_disponiveis, largura_tela=1280, altura_tela=720,
                 velocidade_y=(35.0, 85.0), vento_x=(-18.0, -4.0),
                 sway_amplitude=(18.0, 38.0), sway_speed=(1.4, 2.8),
                 velocidade_rotacao=(-40.0, 40.0), escala=(0.60, 0.95),
                 alpha=(160, 240), inicializar_na_tela=False):
        self.sprites = sprites_disponiveis
        self.largura_tela = largura_tela
        self.altura_tela = altura_tela
        
        # Parâmetros de configuração de comportamento
        self.cfg_vy = velocidade_y
        self.cfg_vx = vento_x
        self.cfg_sway_amp = sway_amplitude
        self.cfg_sway_spd = sway_speed
        self.cfg_rot = velocidade_rotacao
        self.cfg_escala = escala
        self.cfg_alpha = alpha
        
        self.reset(inicializar_na_tela)

    def reset(self, inicializar_na_tela=False):
        self.sprite_base = random.choice(self.sprites) if self.sprites else None

        self.x = random.uniform(-20, self.largura_tela + 40)
        self.y = random.uniform(-50, self.altura_tela) if inicializar_na_tela else random.uniform(-80, -10)
        
        self.vy = random.uniform(*self.cfg_vy)
        self.vx_base = random.uniform(*self.cfg_vx)
        
        self.sway_phase = random.uniform(0, math.pi * 2)
        self.sway_speed = random.uniform(*self.cfg_sway_spd)
        self.sway_amplitude = random.uniform(*self.cfg_sway_amp)
        
        self.angulo = random.uniform(0, 360)
        self.velocidade_rotacao = random.uniform(*self.cfg_rot)
        
        self.escala = random.uniform(*self.cfg_escala)
        self.alpha = random.randint(*self.cfg_alpha)

    def atualizar(self, dt):
        self.sway_phase += self.sway_speed * dt
        sway_x = math.sin(self.sway_phase) * self.sway_amplitude * dt
        
        self.x += (self.vx_base + sway_x) * dt
        self.y += self.vy * dt
        self.angulo = (self.angulo + self.velocidade_rotacao * dt) % 360
        
        if self.y > self.altura_tela + 40 or self.x < -60 or self.x > self.largura_tela + 60:
            self.reset(inicializar_na_tela=False)

    def desenhar(self, superficie):
        if not self.sprite_base:
            return

        rot_surf = pygame.transform.rotozoom(self.sprite_base, self.angulo, self.escala)
        if self.alpha < 255:
            rot_surf.set_alpha(self.alpha)
            
        pos_x = int(self.x - rot_surf.get_width() // 2)
        pos_y = int(self.y - rot_surf.get_height() // 2)
        superficie.blit(rot_surf, (pos_x, pos_y))


# Alias de conveniência
PetalaParticula = ParticulaFlutuante


class EfeitoChuvaParticulas:
    """
    Gerenciador genérico e desacoplado de partículas caindo/flutuando em cena.
    Pode ser instanciado diretamente com qualquer spritesheet ou lista de superfícies.
    """
    def __init__(self, sprites_ou_caminho, largura_tela=1280, altura_tela=720, quantidade=30, **kwargs_particula):
        self.largura = largura_tela
        self.altura = altura_tela
        
        if isinstance(sprites_ou_caminho, str):
            self.sprites = ResourceManager.extrair_sprites_individuais(sprites_ou_caminho)
        else:
            self.sprites = sprites_ou_caminho
            
        self.particulas = [
            ParticulaFlutuante(self.sprites, self.largura, self.altura, inicializar_na_tela=True, **kwargs_particula)
            for _ in range(quantidade)
        ]

    def atualizar(self, dt=0.016):
        for p in self.particulas:
            p.atualizar(dt)

    def desenhar(self, superficie):
        for p in self.particulas:
            p.desenhar(superficie)


class EfeitoPetalas(EfeitoChuvaParticulas):
    """
    Efeito de chuva de pétalas em segundo plano para o menu e cenas de Oblivium.
    Reutiliza a base de EfeitoChuvaParticulas e ResourceManager.
    """
    def __init__(self, largura_tela=1280, altura_tela=720, quantidade_petalas=30):
        super().__init__(
            sprites_ou_caminho="menu inicial/Spritesheet - Petálas Caindo.png",
            largura_tela=largura_tela,
            altura_tela=altura_tela,
            quantidade=quantidade_petalas
        )
