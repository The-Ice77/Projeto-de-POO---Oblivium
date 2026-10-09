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

    def desenhar(self, superficie, areas_excluidas=None, alpha_multiplicador=1.0):
        if not self.sprite_base or alpha_multiplicador <= 0.01:
            return

        # Verificação rápida por ponto central antes de aplicar transformações pesadas
        if areas_excluidas:
            for area in areas_excluidas:
                if area.collidepoint(self.x, self.y):
                    return

        rot_surf = pygame.transform.rotozoom(self.sprite_base, self.angulo, self.escala)
        alpha_final = int(self.alpha * alpha_multiplicador)
        if alpha_final < 255:
            rot_surf.set_alpha(max(0, min(255, alpha_final)))
            
        pos_x = int(self.x - rot_surf.get_width() // 2)
        pos_y = int(self.y - rot_surf.get_height() // 2)

        # Verificação precisa de colisão com a área da superfície para evitar qualquer sobreposição indesejada
        if areas_excluidas:
            rect_particula = pygame.Rect(pos_x, pos_y, rot_surf.get_width(), rot_surf.get_height())
            for area in areas_excluidas:
                if area.colliderect(rect_particula):
                    return

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

    def reiniciar(self, inicializar_na_tela=True):
        """Reinicia e redistribui todas as partículas na tela."""
        for p in self.particulas:
            p.reset(inicializar_na_tela=inicializar_na_tela)

    def atualizar(self, dt=0.016):
        for p in self.particulas:
            p.atualizar(dt)

    def desenhar(self, superficie, areas_excluidas=None, alpha_multiplicador=1.0):
        if alpha_multiplicador <= 0.01:
            return
        for p in self.particulas:
            p.desenhar(superficie, areas_excluidas=areas_excluidas, alpha_multiplicador=alpha_multiplicador)


class EfeitoPetalas(EfeitoChuvaParticulas):
    """
    Efeito de chuva de pétalas em segundo plano para o menu e cenas de Oblivium.
    Reutiliza a base de EfeitoChuvaParticulas e ResourceManager.
    """
    def __init__(self, largura_tela=1280, altura_tela=720, quantidade_petalas=30, **kwargs):
        super().__init__(
            sprites_ou_caminho="menu inicial/Spritesheet - Petálas Caindo.png",
            largura_tela=largura_tela,
            altura_tela=altura_tela,
            quantidade=quantidade_petalas,
            **kwargs
        )


class EfeitoFolhas(EfeitoChuvaParticulas):
    """
    Efeito de chuva de folhas caindo e flutuando suavemente pelos cenários de Oblivium.
    Neste início da jornada, utiliza exclusivamente as folhas verdes (frame 1 da spritesheet 'autumn leaf.png')
    com variações espelhadas naturais para ambientação florestal viva.
    """
    def __init__(self, largura_tela=1280, altura_tela=720, quantidade_folhas=28, apenas_verdes=True):
        todas_sprites = ResourceManager.carregar_spritesheet_grid(
            "efeitos/folhas/autumn leaf.png",
            colunas=4,
            linhas=1
        )
        self.todas_sprites = todas_sprites
        self.apenas_verdes = apenas_verdes

        sprites_finais = self._obter_sprites_filtradas(apenas_verdes)

        super().__init__(
            sprites_ou_caminho=sprites_finais,
            largura_tela=largura_tela,
            altura_tela=altura_tela,
            quantidade=quantidade_folhas,
            velocidade_y=(20.0, 56.0),         # Queda suave e orgânica
            vento_x=(-26.0, -8.0),             # Brisa constante soprando para a esquerda
            sway_amplitude=(24.0, 50.0),       # Oscilação horizontal orgânica
            sway_speed=(1.4, 2.6),             # Velocidade do balanço no vento
            velocidade_rotacao=(-42.0, 42.0),  # Giro suave da folha
            escala=(0.95, 1.45),               # Escala adequada para 16x16 pixels
            alpha=(175, 245)                   # Transparência suave para profundidade 2.5D
        )

    def _obter_sprites_filtradas(self, apenas_verdes):
        if apenas_verdes and len(self.todas_sprites) > 1:
            # Frame 1 é a folha verde viva. Adiciona também versão espelhada horizontalmente
            folha_verde = self.todas_sprites[1]
            folha_verde_flip = pygame.transform.flip(folha_verde, True, False)
            return [folha_verde, folha_verde_flip]
        return self.todas_sprites

    def definir_apenas_verdes(self, apenas_verdes=True):
        """Alterna dinamicamente entre folhas estritamente verdes e o conjunto completo outonal."""
        self.apenas_verdes = apenas_verdes
        sprites_finais = self._obter_sprites_filtradas(apenas_verdes)
        self.sprites = sprites_finais
        for p in self.particulas:
            p.sprites = sprites_finais
            p.sprite_base = random.choice(sprites_finais)
