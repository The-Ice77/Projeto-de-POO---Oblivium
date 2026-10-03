# src/maps/mapa_estrada.py
import pygame
from src.maps.cenario_base import CenarioBase
from src.utils.resource_manager import ResourceManager
from src.utils.colors import CENARIO_GRAMA_CINZA, CENARIO_ESTRADA


class MapaEstrada(CenarioBase):
    """
    Representa o primeiro trecho da Estrada Rural de Oblivium.
    Ambiente florestal denso e verdejante. A estrada de terra batida é contornada
    por transições suaves de grama sem emendas, margens com vegetação e fileiras
    densas de árvores ancestrais cheias de folhas (Model 01).
    """

    def __init__(self, game, largura_tela, altura_tela):
        self.area_estrada = pygame.Rect(0, 240, largura_tela, 240)

        # Barreiras ajustadas rigorosamente para manter o jogador na pista sem invadir o bosque
        self.barreiras_estrada = [
            pygame.Rect(0, 0, largura_tela, 235),       # Floresta densa ao Norte
            pygame.Rect(0, 480, largura_tela, altura_tela - 480) # Floresta densa ao Sul
        ]
        self.limite_oeste = pygame.Rect(0, 0, 20, altura_tela)
        self.limite_leste = pygame.Rect(1240, 0, 40, altura_tela)

        # Floresta Densa ao Norte (Model 01 copas cheias de folhas)
        self.arvores_norte = [
            (0, 5, 106, 160, "t1_sz5_a"),
            (80, 25, 106, 160, "t1_sz5_b"),
            (160, 5, 106, 160, "t1_sz5_a"),
            (240, 35, 73, 126, "t1_sz4_a"),
            (320, 10, 106, 160, "t1_sz5_b"),
            (410, 30, 106, 160, "t1_sz5_a"),
            (500, 15, 73, 126, "t1_sz4_b"),
            (570, 0, 106, 160, "t1_sz5_b"),
            (660, 25, 106, 160, "t1_sz5_a"),
            (750, 10, 73, 126, "t1_sz4_a"),
            (830, 20, 106, 160, "t1_sz5_b"),
            (920, 5, 106, 160, "t1_sz5_a"),
            (1010, 30, 73, 126, "t1_sz4_b"),
            (1090, 15, 106, 160, "t1_sz5_a"),
            (1170, 5, 106, 160, "t1_sz5_b"),
        ]

        # Floresta Densa ao Sul (copas cheias)
        self.arvores_sul = [
            (-10, 475, 106, 160, "t1_sz5_b"),
            (70, 490, 73, 126, "t1_sz4_a"),
            (150, 470, 106, 160, "t1_sz5_a"),
            (240, 485, 106, 160, "t1_sz5_b"),
            (330, 500, 73, 126, "t1_sz4_b"),
            (410, 470, 106, 160, "t1_sz5_a"),
            (500, 490, 106, 160, "t1_sz5_b"),
            (590, 475, 73, 126, "t1_sz4_a"),
            (670, 485, 106, 160, "t1_sz5_a"),
            (760, 470, 106, 160, "t1_sz5_b"),
            (850, 495, 73, 126, "t1_sz4_b"),
            (930, 475, 106, 160, "t1_sz5_a"),
            (1020, 485, 106, 160, "t1_sz5_b"),
            (1110, 470, 73, 126, "t1_sz4_a"),
            (1180, 480, 106, 160, "t1_sz5_b"),
        ]

        # Vegetação Farta na borda da grama (sem invadir a pista)
        self.detalhes_vegetacao = [
            (60, 205, "arbusto_1"), (140, 210, "flor_1"), (230, 208, "cogumelo"),
            (320, 212, "arbusto_2"), (410, 206, "flor_2"), (500, 210, "tufo_grama"),
            (600, 205, "arbusto_1"), (690, 212, "flor_1"), (780, 208, "cogumelo"),
            (870, 210, "arbusto_2"), (960, 205, "flor_2"), (1050, 212, "tufo_grama"),
            (1140, 208, "arbusto_1"),

            (40, 485, "flor_2"), (130, 490, "tufo_grama"), (220, 488, "arbusto_1"),
            (310, 492, "cogumelo"), (400, 486, "flor_1"), (490, 490, "arbusto_2"),
            (590, 488, "tufo_grama"), (680, 490, "flor_2"), (770, 486, "arbusto_1"),
            (860, 492, "cogumelo"), (950, 488, "flor_1"), (1040, 486, "tufo_grama"),
            (1130, 490, "arbusto_2"),

            (180, 215, "pedra_1"), (550, 212, "pedra_2"), (830, 495, "pedra_1"), (1090, 492, "pedra_2")
        ]

        super().__init__(game, largura_tela, altura_tela, nome="ESTRADA")

    def carregar_recursos(self):
        """Carrega e prepara chão com estrada e transições orgânicas sem costuras, árvores e vegetação."""
        # 1. Chão com Estrada de Terra e Transições Suaves
        self.chao_completo = ResourceManager.gerar_chao_com_estrada_e_transicao(
            self.largura_tela, self.altura_tela,
            y_estrada=self.area_estrada.y,
            h_estrada=self.area_estrada.height
        )

        # 2. Árvores Model 01
        p_t1 = "assets/cenario/arvores_separadas_tipo1"
        self.sprites_arvores = {
            "t1_sz5_a": ResourceManager.carregar_imagem(f"{p_t1}/Model_01_Size_05/Model_01_Size_05_01.png", (106, 160)),
            "t1_sz5_b": ResourceManager.carregar_imagem(f"{p_t1}/Model_01_Size_05/Model_01_Size_05_02.png", (106, 160)),
            "t1_sz5_c": ResourceManager.carregar_imagem(f"{p_t1}/Model_01_Size_05/Model_01_Size_05_03.png", (106, 160)),
            "t1_sz4_a": ResourceManager.carregar_imagem(f"{p_t1}/Model_01_Size_04/Model_01_Size_04_01.png", (73, 126)),
            "t1_sz4_b": ResourceManager.carregar_imagem(f"{p_t1}/Model_01_Size_04/Model_01_Size_04_02.png", (73, 126)),
        }

        # 3. Vegetação e Flores
        p_veg = "assets/cenario/vegetacao_pedras_separadas/Vegetation"
        p_rock = "assets/cenario/vegetacao_pedras_separadas/Rocks"

        self.sprites_decor = {
            "arbusto_1": ResourceManager.carregar_imagem(f"{p_veg}/Vegetation_001.png", (28, 28)),
            "arbusto_2": ResourceManager.carregar_imagem(f"{p_veg}/Vegetation_005.png", (26, 26)),
            "flor_1": ResourceManager.carregar_imagem(f"{p_veg}/Vegetation_012.png", (22, 22)),
            "flor_2": ResourceManager.carregar_imagem(f"{p_veg}/Vegetation_018.png", (20, 20)),
            "cogumelo": ResourceManager.carregar_imagem(f"{p_veg}/Vegetation_027.png", (18, 18)),
            "tufo_grama": ResourceManager.carregar_imagem(f"{p_veg}/Vegetation_034.png", (24, 24)),
            "pedra_1": ResourceManager.carregar_imagem(f"{p_rock}/Rocks_003.png", (20, 16)),
            "pedra_2": ResourceManager.carregar_imagem(f"{p_rock}/Rocks_004.png", (22, 18)),
        }

    def inicializar_cenario(self):
        """Configura as hitboxes das barreiras e troncos 2.5D."""
        self.hitboxes = []
        self.hitboxes.extend(self.barreiras_estrada)
        self.hitboxes.append(self.limite_oeste)
        self.hitboxes.append(self.limite_leste)

        # Colisões na base dos troncos
        for x, y, w, h, _ in self.arvores_norte:
            self.hitboxes.append(pygame.Rect(x + (w // 2) - 16, y + h - 28, 32, 24))

        for x, y, w, h, _ in self.arvores_sul:
            self.hitboxes.append(pygame.Rect(x + (w // 2) - 16, y + h - 28, 32, 24))

        self.itens_no_chao = []

    def desenhar_camada_inferior(self, tela):
        """Renderiza o chão e toda a vegetação das margens."""
        if self.chao_completo:
            tela.blit(self.chao_completo, (0, 0))
        else:
            tela.fill(CENARIO_GRAMA_CINZA)
            pygame.draw.rect(tela, CENARIO_ESTRADA, self.area_estrada)

        for px, py, chave in self.detalhes_vegetacao:
            sprite = self.sprites_decor.get(chave)
            if sprite:
                tela.blit(sprite, (px, py))

    def desenhar_props(self, tela):
        """Renderiza as árvores."""
        for x, y, w, h, k in self.arvores_norte + self.arvores_sul:
            sprite = self.sprites_arvores.get(k)
            if sprite:
                tela.blit(sprite, (x, y))
