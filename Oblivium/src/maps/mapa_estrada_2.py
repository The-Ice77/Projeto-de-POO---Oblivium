# src/maps/mapa_estrada_2.py
import pygame
from src.maps.cenario_base import CenarioBase
from src.utils.resource_manager import ResourceManager
from src.utils.colors import (
    CENARIO_FUNDO_FORA, CENARIO_GRAMA_CINZA, CENARIO_ESTRADA, CENARIO_BARREIRAS,
    COR_PEDRA_DESLIZAMENTO, COR_BORDA_PEDRA
)


class MapaEstrada2(CenarioBase):
    """
    Representa o segundo trecho da Estrada Rural de Oblivium.
    Cenário que contém o quebra-cabeça de campo com o Deslizamento de Pedras Ancestrais,
    exigindo o despertar e uso das magias arcanas de Halia (Bola de Fogo / Levitar).
    """

    def __init__(self, game, largura_tela, altura_tela):
        self.area_estrada = pygame.Rect(0, 250, largura_tela, 220)
        self.barreiras_estrada = [
            pygame.Rect(0, 0, largura_tela, 250),
            pygame.Rect(0, 470, largura_tela, 250)
        ]
        self.limite_oeste = pygame.Rect(0, 0, 20, altura_tela)

        # Pedras que bloqueiam o caminho
        self.pedras_deslizamento = [
            pygame.Rect(1100, 250, 80, 70),
            pygame.Rect(1150, 310, 90, 80),
            pygame.Rect(1080, 320, 80, 80),
            pygame.Rect(1120, 390, 100, 90)
        ]

        super().__init__(game, largura_tela, altura_tela, nome="ESTRADA_2")

    def carregar_recursos(self):
        """Carrega sprites das pedras e texturas de fundo da estrada."""
        self.sprite_pedra = ResourceManager.carregar_imagem("assets/props/pedra.png")

    def inicializar_cenario(self):
        """Configura hitboxes das barreiras e pedras do deslizamento."""
        self.hitboxes = []
        self.hitboxes.extend(self.barreiras_estrada)
        self.hitboxes.append(self.limite_oeste)
        self.hitboxes.extend(self.pedras_deslizamento)
        self.itens_no_chao = []

    def desobstruir_estrada(self, tipo_magia="FOGO"):
        """
        Remove as pedras de bloqueio das hitboxes e as reposiciona como escombros/laterais
        conforme o feitiço executado no puzzle narrativo.
        """
        for p in self.pedras_deslizamento:
            if p in self.hitboxes:
                self.hitboxes.remove(p)

        if tipo_magia == "FOGO":
            self.pedras_deslizamento = [
                pygame.Rect(1110, 430, 20, 15),
                pygame.Rect(1160, 440, 25, 20),
                pygame.Rect(1090, 450, 15, 12)
            ]
        else:
            self.pedras_deslizamento = [
                pygame.Rect(1100, 190, 60, 50),
                pygame.Rect(1150, 500, 65, 55)
            ]

    def desenhar_camada_inferior(self, tela):
        """Renderiza o chão da estrada 2."""
        tela.fill(CENARIO_GRAMA_CINZA)
        pygame.draw.rect(tela, CENARIO_ESTRADA, self.area_estrada)
        for barreira in self.barreiras_estrada:
            pygame.draw.rect(tela, CENARIO_BARREIRAS, barreira)
            pygame.draw.rect(tela, CENARIO_FUNDO_FORA, barreira, 1)

    def desenhar_props(self, tela):
        """Renderiza as pedras do deslizamento ou seus escombros."""
        for pedra in self.pedras_deslizamento:
            if self.sprite_pedra:
                img_escalada = pygame.transform.scale(self.sprite_pedra, (pedra.width, pedra.height))
                tela.blit(img_escalada, pedra.topleft)
            else:
                pygame.draw.rect(tela, COR_PEDRA_DESLIZAMENTO, pedra)
                pygame.draw.rect(tela, COR_BORDA_PEDRA, pedra, 2)
