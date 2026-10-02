# src/maps/mapa_estrada.py
import pygame
from src.maps.cenario_base import CenarioBase
from src.utils.resource_manager import ResourceManager
from src.utils.colors import (
    CENARIO_FUNDO_FORA, CENARIO_GRAMA_CINZA, CENARIO_ESTRADA, CENARIO_BARREIRAS
)


class MapaEstrada(CenarioBase):
    """
    Representa o primeiro trecho da Estrada Rural de Oblivium.
    Local de transição onde Halia encontra o Carroceiro e inicia sua jornada rumo a Vilarejo/Torre.
    """

    def __init__(self, game, largura_tela, altura_tela):
        self.area_estrada = pygame.Rect(0, 250, largura_tela, 220)
        self.barreiras_estrada = [
            pygame.Rect(0, 0, largura_tela, 250),
            pygame.Rect(0, 470, largura_tela, 250)
        ]
        self.limite_oeste = pygame.Rect(0, 0, 20, altura_tela)
        self.limite_leste = pygame.Rect(1220, 0, 30, altura_tela)

        super().__init__(game, largura_tela, altura_tela, nome="ESTRADA")

    def carregar_recursos(self):
        """Carrega a imagem de fundo ou texturas da estrada."""
        self.fundo_estrada = ResourceManager.carregar_imagem(
            "mapas/Estradas/Estrada 1/Estrada_1 - Sprite.webp",
            (self.largura_tela, self.altura_tela)
        )

    def inicializar_cenario(self):
        """Configura as hitboxes das barreiras da estrada e limites de tela."""
        self.hitboxes = []
        self.hitboxes.extend(self.barreiras_estrada)
        self.hitboxes.append(self.limite_oeste)
        self.hitboxes.append(self.limite_leste)
        self.itens_no_chao = []

    def desenhar_camada_inferior(self, tela):
        """Renderiza o chão da estrada e margens com grama."""
        if self.fundo_estrada:
            tela.blit(self.fundo_estrada, (0, 0))
        else:
            tela.fill(CENARIO_GRAMA_CINZA)
            pygame.draw.rect(tela, CENARIO_ESTRADA, self.area_estrada)
            for barreira in self.barreiras_estrada:
                pygame.draw.rect(tela, CENARIO_BARREIRAS, barreira)
                pygame.draw.rect(tela, CENARIO_FUNDO_FORA, barreira, 1)

    def desenhar_props(self, tela):
        """Props adicionais ou decorações da estrada."""
        pass
