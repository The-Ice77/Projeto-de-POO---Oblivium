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


class ParticulaFolhaProfunda(ParticulaFlutuante):
    """
    Partícula de folha especializada com física, escala e opacidade proporcionais
    à sua profundidade ótica (2.5D com efeito de paralaxe).
    
    Camadas:
    - CAMADA_FUNDO: folhas pequenas, lentas e atmosféricas ao fundo do cenário.
    - CAMADA_MEDIA: folhas no plano principal de interação dos personagens.
    - CAMADA_FRENTE: folhas grandes, velozes e nítidas passando bem perto da tela/câmera.
    """
    CAMADA_FUNDO = 0
    CAMADA_MEDIA = 1
    CAMADA_FRENTE = 2

    def __init__(self, sprites_disponiveis, largura_tela=1280, altura_tela=720,
                 camada=CAMADA_MEDIA, inicializar_na_tela=False):
        self.camada = camada

        # Configurações de física e ótica ajustadas de acordo com a camada de profundidade
        if camada == self.CAMADA_FUNDO:
            # Ao fundo: pequenas, caem devagar e têm transparência suave pela atmosfera
            cfg_vy = (14.0, 30.0)
            cfg_vx = (-16.0, -6.0)
            cfg_sway_amp = (12.0, 24.0)
            cfg_sway_spd = (1.0, 1.8)
            cfg_rot = (-22.0, 22.0)
            cfg_escala = (0.55, 0.82)
            cfg_alpha = (130, 175)
        elif camada == self.CAMADA_FRENTE:
            # Em primeiro plano: grandes, passam rente à tela com velocidade e balanço acentuados
            cfg_vy = (70.0, 125.0)
            cfg_vx = (-58.0, -24.0)
            cfg_sway_amp = (46.0, 76.0)
            cfg_sway_spd = (2.2, 3.4)
            cfg_rot = (-60.0, 60.0)
            cfg_escala = (2.10, 2.90)
            cfg_alpha = (225, 255)
        else:
            # Camada média: escala natural no plano dos personagens
            cfg_vy = (24.0, 52.0)
            cfg_vx = (-28.0, -10.0)
            cfg_sway_amp = (24.0, 48.0)
            cfg_sway_spd = (1.5, 2.6)
            cfg_rot = (-40.0, 40.0)
            cfg_escala = (1.00, 1.40)
            cfg_alpha = (185, 235)

        super().__init__(
            sprites_disponiveis=sprites_disponiveis,
            largura_tela=largura_tela,
            altura_tela=altura_tela,
            velocidade_y=cfg_vy,
            vento_x=cfg_vx,
            sway_amplitude=cfg_sway_amp,
            sway_speed=cfg_sway_spd,
            velocidade_rotacao=cfg_rot,
            escala=cfg_escala,
            alpha=cfg_alpha,
            inicializar_na_tela=inicializar_na_tela
        )

    def reset(self, inicializar_na_tela=False):
        super().reset(inicializar_na_tela=inicializar_na_tela)
        # Folhas maiores de primeiro plano entram com margem mais ampla para evitar pop-in nas bordas
        if self.camada == self.CAMADA_FRENTE and not inicializar_na_tela:
            self.x = random.uniform(-40, self.largura_tela + 80)
            self.y = random.uniform(-110, -25)

    def atualizar(self, dt):
        self.sway_phase += self.sway_speed * dt
        sway_x = math.sin(self.sway_phase) * self.sway_amplitude * dt

        self.x += (self.vx_base + sway_x) * dt
        self.y += self.vy * dt
        self.angulo = (self.angulo + self.velocidade_rotacao * dt) % 360

        # Limites dinâmicos de tela de acordo com o tamanho da partícula
        limite_lateral = 110 if self.camada == self.CAMADA_FRENTE else 65
        limite_inferior = 70 if self.camada == self.CAMADA_FRENTE else 45

        if self.y > self.altura_tela + limite_inferior or self.x < -limite_lateral or self.x > self.largura_tela + limite_lateral:
            self.reset(inicializar_na_tela=False)


class EfeitoFolhas(EfeitoChuvaParticulas):
    """
    Efeito de chuva de folhas com profundidade 2.5D e paralaxe em 3 camadas ópticas:
    - Camada Fundo: folhas menores e lentas que passam ao fundo (inclusive atrás dos personagens).
    - Camada Média: folhas no plano de movimentação padrão da cena.
    - Camada Frente (Primeiro Plano): folhas grandes e rápidas passando rente à tela do jogador.
    """
    CAMADA_FUNDO = ParticulaFolhaProfunda.CAMADA_FUNDO
    CAMADA_MEDIA = ParticulaFolhaProfunda.CAMADA_MEDIA
    CAMADA_FRENTE = ParticulaFolhaProfunda.CAMADA_FRENTE

    def __init__(self, largura_tela=1280, altura_tela=720, quantidade_folhas=32, apenas_verdes=True):
        todas_sprites = ResourceManager.carregar_spritesheet_grid(
            "efeitos/folhas/autumn leaf.png",
            colunas=4,
            linhas=1
        )
        self.todas_sprites = todas_sprites
        self.apenas_verdes = apenas_verdes
        sprites_finais = self._obter_sprites_filtradas(apenas_verdes)

        self.largura = largura_tela
        self.altura = altura_tela
        self.sprites = sprites_finais

        # Distribuição harmônica das camadas de profundidade:
        # ~30% fundo, ~45% média, ~25% frente (primeiro plano rente à tela)
        qtd_frente = max(2, int(quantidade_folhas * 0.25))
        qtd_fundo = max(3, int(quantidade_folhas * 0.30))
        qtd_media = max(3, quantidade_folhas - qtd_frente - qtd_fundo)

        self.particulas = []
        for _ in range(qtd_fundo):
            self.particulas.append(
                ParticulaFolhaProfunda(self.sprites, self.largura, self.altura,
                                      camada=ParticulaFolhaProfunda.CAMADA_FUNDO,
                                      inicializar_na_tela=True)
            )
        for _ in range(qtd_media):
            self.particulas.append(
                ParticulaFolhaProfunda(self.sprites, self.largura, self.altura,
                                      camada=ParticulaFolhaProfunda.CAMADA_MEDIA,
                                      inicializar_na_tela=True)
            )
        for _ in range(qtd_frente):
            self.particulas.append(
                ParticulaFolhaProfunda(self.sprites, self.largura, self.altura,
                                      camada=ParticulaFolhaProfunda.CAMADA_FRENTE,
                                      inicializar_na_tela=True)
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

    def desenhar_camada_fundo(self, superficie, areas_excluidas=None, alpha_multiplicador=1.0):
        """Desenha apenas as folhas da camada de fundo (ideal para passar atrás dos personagens)."""
        if alpha_multiplicador <= 0.01:
            return
        for p in self.particulas:
            if getattr(p, 'camada', None) == ParticulaFolhaProfunda.CAMADA_FUNDO:
                p.desenhar(superficie, areas_excluidas=areas_excluidas, alpha_multiplicador=alpha_multiplicador)

    def desenhar_camada_frente(self, superficie, areas_excluidas=None, alpha_multiplicador=1.0):
        """Desenha as folhas das camadas média e frontal (passando na frente dos personagens e rente à tela)."""
        if alpha_multiplicador <= 0.01:
            return
        # Desenha na ordem: médias primeiro, depois frontais por cima de tudo
        for p in self.particulas:
            if getattr(p, 'camada', None) == ParticulaFolhaProfunda.CAMADA_MEDIA:
                p.desenhar(superficie, areas_excluidas=areas_excluidas, alpha_multiplicador=alpha_multiplicador)
        for p in self.particulas:
            if getattr(p, 'camada', None) == ParticulaFolhaProfunda.CAMADA_FRENTE:
                p.desenhar(superficie, areas_excluidas=areas_excluidas, alpha_multiplicador=alpha_multiplicador)

    def desenhar(self, superficie, areas_excluidas=None, alpha_multiplicador=1.0):
        """Desenha todas as folhas ordenadas por profundidade (fundo -> média -> frente)."""
        if alpha_multiplicador <= 0.01:
            return
        # Ordenação estável por camada garante que folhas de primeiro plano fiquem sempre na frente
        particulas_ordenadas = sorted(self.particulas, key=lambda p: getattr(p, 'camada', 1))
        for p in particulas_ordenadas:
            p.desenhar(superficie, areas_excluidas=areas_excluidas, alpha_multiplicador=alpha_multiplicador)
