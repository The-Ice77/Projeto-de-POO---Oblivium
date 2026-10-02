# src/maps/mapa_casa.py
import pygame
from src.maps.cenario_base import CenarioBase
from src.entities.item import Item
from src.utils.resource_manager import ResourceManager
from src.utils.colors import (
    CENARIO_FUNDO_FORA, CENARIO_MADEIRA_VARANDA, CENARIO_PAREDE_CASA,
    CENARIO_CHAO_CASA, CENARIO_PORTA, CENARIO_MOVEIS,
    COLOR_BOLSA_MOEDAS, COLOR_LIVRO_ANTIGO, COLOR_CAJADO_MAGICO
)


class MapaCasa(CenarioBase):
    """
    Representa o interior e a varanda da residência inicial de Halia.
    Contém a cama, estante de livros arcanos, itens ancestrais a serem coletados
    e a porta de saída com trava mecânica ligada aos itens iniciais.
    """

    def __init__(self, game, largura_tela, altura_tela):
        self.porta_aberta = False

        # Geometria e áreas de colisão da casa
        self.area_chao_casa = pygame.Rect(50, 50, 500, 600)
        self.varanda_madeira = pygame.Rect(550, 50, 150, 600)

        self.paredes_casa = [
            pygame.Rect(50, 50, 500, 40),
            pygame.Rect(50, 50, 40, 600),
            pygame.Rect(50, 610, 500, 40),
            pygame.Rect(510, 50, 40, 250),
            pygame.Rect(510, 400, 40, 250),
        ]

        self.porta = pygame.Rect(510, 300, 40, 100)

        self.moveis = [
            pygame.Rect(90, 90, 100, 140),   # Cama
            pygame.Rect(400, 90, 110, 80),   # Estante / Armário
        ]

        self.limites_varanda = [
            pygame.Rect(550, 45, 150, 5),
            pygame.Rect(550, 650, 150, 5),
        ]

        super().__init__(game, largura_tela, altura_tela, nome="CASA")

    def carregar_recursos(self):
        """Carrega texturas específicas da casa via ResourceManager."""
        self.fundo_casa = ResourceManager.carregar_imagem("assets/maps/fundo_casa.png", (self.largura_tela, self.altura_tela))
        self.sprite_porta_fechada = ResourceManager.carregar_imagem("assets/props/porta_fechada.png", (40, 100))
        self.sprite_porta_aberta = ResourceManager.carregar_imagem("assets/props/porta_aberta.png", (40, 100))
        self.sprite_estante = ResourceManager.carregar_imagem("assets/props/estante.png", (110, 180))
        self.sprite_cama = ResourceManager.carregar_imagem("assets/props/cama.png", (100, 140))

    def inicializar_cenario(self):
        """Monta a lista de colisões ativas e instancia os itens no chão caso não coletados."""
        self.hitboxes = []
        self.hitboxes.extend(self.paredes_casa)
        self.hitboxes.extend(self.moveis)
        self.hitboxes.extend(self.limites_varanda)

        if not self.porta_aberta:
            self.hitboxes.append(self.porta)

        self.itens_no_chao = []
        itens_brutos = [
            Item("A Bolsa de Moedas", 420, 300, 40, 40, COLOR_BOLSA_MOEDAS, caminho_sprite="props/Bolsa de Moedas.png"),
            Item("O Livro Antigo", 300, 450, 40, 40, COLOR_LIVRO_ANTIGO, caminho_sprite="props/Grimório.png"),
            Item("O Cajado Mágico", 230, 200, 55, 55, COLOR_CAJADO_MAGICO, caminho_sprite="props/Cajado.png")
        ]

        itens_brutos[0].id_unico = "item_moedas"
        itens_brutos[1].id_unico = "item_livro"
        itens_brutos[2].id_unico = "item_cajado"

        coletados = getattr(self.game, 'itens_coletados', [])
        for item in itens_brutos:
            if item.id_unico not in coletados:
                self.itens_no_chao.append(item)

    def abrir_porta(self):
        """Abre a porta da casa e atualiza a colisão."""
        self.porta_aberta = True
        if self.porta in self.hitboxes:
            self.hitboxes.remove(self.porta)

    def desenhar_camada_inferior(self, tela):
        """Renderiza o fundo do interior e os pisos da casa."""
        if self.fundo_casa:
            tela.blit(self.fundo_casa, (0, 0))
        else:
            tela.fill(CENARIO_FUNDO_FORA)
            pygame.draw.rect(tela, CENARIO_MADEIRA_VARANDA, self.varanda_madeira)
            pygame.draw.rect(tela, CENARIO_PAREDE_CASA, self.varanda_madeira, 2)
            pygame.draw.rect(tela, CENARIO_CHAO_CASA, self.area_chao_casa)
            for parede in self.paredes_casa:
                pygame.draw.rect(tela, CENARIO_PAREDE_CASA, parede)
                pygame.draw.rect(tela, CENARIO_FUNDO_FORA, parede, 2)
            for limite in self.limites_varanda:
                pygame.draw.rect(tela, CENARIO_PAREDE_CASA, limite)

    def desenhar_props(self, tela):
        """Renderiza portas e móveis da casa."""
        # 1. Porta
        if not self.porta_aberta:
            if self.sprite_porta_fechada:
                tela.blit(self.sprite_porta_fechada, self.porta.topleft)
            else:
                pygame.draw.rect(tela, CENARIO_PORTA, self.porta)
                pygame.draw.rect(tela, CENARIO_PAREDE_CASA, self.porta, 2)
        else:
            if self.sprite_porta_aberta:
                tela.blit(self.sprite_porta_aberta, self.porta.topleft)
            else:
                pygame.draw.rect(tela, CENARIO_CHAO_CASA, self.porta, 2)

        # 2. Móveis
        sprites_moveis = [self.sprite_cama, self.sprite_estante]
        for i, movel in enumerate(self.moveis):
            sprite = sprites_moveis[i] if i < len(sprites_moveis) else None
            if sprite:
                tela.blit(sprite, movel.topleft)
            else:
                pygame.draw.rect(tela, CENARIO_MOVEIS, movel)
                pygame.draw.rect(tela, CENARIO_PAREDE_CASA, movel, 2)
