# src/maps/mapa_estrada_2.py
import pygame
from src.maps.cenario_base import CenarioBase
from src.utils.resource_manager import ResourceManager
from src.utils.colors import CENARIO_GRAMA_CINZA, CENARIO_ESTRADA, COR_PEDRA_DESLIZAMENTO, COR_BORDA_PEDRA


class MapaEstrada2(CenarioBase):
    """
    Representa o segundo trecho da Estrada Rural de Oblivium: O Desfiladeiro do Deslizamento.
    Cenário que retrata o recente colapso geológico: árvores ancestrais cheias de folhas tombadas,
    cascalho e rochas espalhados pela pista e uma barricada densa de rochas que bloqueia a passagem,
    com limites firmes que impedem o jogador de se perder no bosque.
    """

    def __init__(self, game, largura_tela, altura_tela):
        self.area_estrada = pygame.Rect(0, 240, largura_tela, 240)

        # Barreiras delimitadas rigorosamente
        self.barreiras_estrada = [
            pygame.Rect(0, 0, largura_tela, 235),
            pygame.Rect(0, 480, largura_tela, altura_tela - 480)
        ]
        self.limite_oeste = pygame.Rect(0, 0, 20, altura_tela)

        # Pedras Principais de Bloqueio (Colisões rígidas do deslizamento no leste)
        self.pedras_deslizamento = [
            pygame.Rect(1070, 245, 84, 75),
            pygame.Rect(1140, 280, 95, 85),
            pygame.Rect(1060, 325, 90, 80),
            pygame.Rect(1115, 385, 105, 95),
            pygame.Rect(1040, 395, 75, 65)
        ]

        # Árvores de Pé ao Norte (Model 01 copas cheias de folhas)
        self.arvores_norte = [
            (0, 10, 106, 160, "t1_sz5_a"),
            (90, 30, 106, 160, "t1_sz5_b"),
            (180, 5, 106, 160, "t1_sz5_c"),
            (270, 35, 73, 126, "t1_sz4_a"),
            (360, 15, 106, 160, "t1_sz5_a"),
            (460, 30, 106, 160, "t1_sz5_b"),
            (550, 10, 73, 126, "t1_sz4_b"),
            (640, 25, 106, 160, "t1_sz5_c"),
            (730, 10, 106, 160, "t1_sz5_a"),
            (820, 35, 73, 126, "t1_sz4_a"),
            (900, 15, 106, 160, "t1_sz5_b"),
        ]

        # Árvores de Pé ao Sul
        self.arvores_sul = [
            (0, 480, 106, 160, "t1_sz5_c"),
            (100, 495, 73, 126, "t1_sz4_a"),
            (190, 475, 106, 160, "t1_sz5_a"),
            (290, 490, 106, 160, "t1_sz5_b"),
            (380, 470, 73, 126, "t1_sz4_b"),
            (470, 485, 106, 160, "t1_sz5_c"),
            (570, 475, 106, 160, "t1_sz5_a"),
            (660, 495, 73, 126, "t1_sz4_a"),
            (750, 475, 106, 160, "t1_sz5_b"),
            (850, 490, 106, 160, "t1_sz5_c"),
        ]

        # Árvores Tombadas e Quebradas pelo Deslizamento
        self.arvores_caidas = [
            (930, 175, 72, "arvore_tombada_1"),
            (960, 425, -68, "arvore_tombada_2"),
            (1010, 205, 0, "tronco_partido_1"),
            (990, 475, 0, "tronco_partido_2"),
        ]

        # Detritos, Cascalho e Pedras Menores Espalhadas
        self.pedras_espalhadas = [
            (880, 260, "rocha_media_1"),
            (920, 240, "rocha_media_2"),
            (960, 275, "pedregulho_1"),
            (1000, 305, "pedregulho_2"),
            (930, 350, "pedregulho_1"),
            (970, 395, "rocha_media_1"),
            (1020, 425, "pedregulho_2"),
            (860, 335, "cascalho"),
            (900, 405, "cascalho"),
            (940, 440, "pedregulho_1"),
            (1010, 365, "rocha_media_2"),
            (1170, 225, "rocha_media_1"),
            (1185, 455, "rocha_media_2"),
        ]

        # Vegetação
        self.vegetacao_margem = [
            (80, 205, "arbusto"), (260, 210, "tufo_grama"), (440, 208, "flor_silvestre"),
            (620, 212, "arbusto"), (790, 210, "tufo_grama"),
            (70, 485, "tufo_grama"), (250, 490, "arbusto"), (430, 488, "flor_silvestre"),
            (610, 485, "tufo_grama"), (780, 490, "arbusto"),
        ]

        super().__init__(game, largura_tela, altura_tela, nome="ESTRADA_2")

    def carregar_recursos(self):
        """Carrega e prepara chão, árvores cheias de folhas, árvores tombadas e coleção de rochas."""
        # 1. Chão com Estrada de Terra e Transições Suaves
        self.chao_completo = ResourceManager.gerar_chao_com_estrada_e_transicao(
            self.largura_tela, self.altura_tela,
            y_estrada=self.area_estrada.y,
            h_estrada=self.area_estrada.height
        )

        # 2. Árvores em Pé
        p_t1 = "assets/cenario/arvores_separadas_tipo1"
        self.sprites_arvores = {
            "t1_sz5_a": ResourceManager.carregar_imagem(f"{p_t1}/Model_01_Size_05/Model_01_Size_05_01.png", (106, 160)),
            "t1_sz5_b": ResourceManager.carregar_imagem(f"{p_t1}/Model_01_Size_05/Model_01_Size_05_02.png", (106, 160)),
            "t1_sz5_c": ResourceManager.carregar_imagem(f"{p_t1}/Model_01_Size_05/Model_01_Size_05_03.png", (106, 160)),
            "t1_sz4_a": ResourceManager.carregar_imagem(f"{p_t1}/Model_01_Size_04/Model_01_Size_04_01.png", (73, 126)),
            "t1_sz4_b": ResourceManager.carregar_imagem(f"{p_t1}/Model_01_Size_04/Model_01_Size_04_02.png", (73, 126)),
        }

        # 3. Árvores Tombadas e Troncos Partidos
        arv_base_1 = ResourceManager.carregar_imagem(f"{p_t1}/Model_01_Size_04/Model_01_Size_04_01.png", (73, 126))
        arv_base_2 = ResourceManager.carregar_imagem(f"{p_t1}/Model_01_Size_04/Model_01_Size_04_02.png", (73, 126))

        self.sprites_caidas = {
            "arvore_tombada_1": pygame.transform.rotate(arv_base_1, 74) if arv_base_1 else None,
            "arvore_tombada_2": pygame.transform.rotate(arv_base_2, -70) if arv_base_2 else None,
            "tronco_partido_1": ResourceManager.carregar_imagem(f"{p_t1}/Model_01_Size_05/Model_01_Size_05_09.png", (61, 42)),
            "tronco_partido_2": ResourceManager.carregar_imagem(f"{p_t1}/Model_01_Size_04/Model_01_Size_04_09.png", (48, 36)),
        }

        # 4. Coleção de Rochas Ancestrais
        p_rocks = "assets/cenario/vegetacao_pedras_separadas/Rocks"
        self.sprites_rochas_grandes = [
            ResourceManager.carregar_imagem(f"{p_rocks}/Rocks_001.png"),
            ResourceManager.carregar_imagem(f"{p_rocks}/Rocks_002.png"),
            ResourceManager.carregar_imagem(f"{p_rocks}/Rocks_005.png"),
            ResourceManager.carregar_imagem(f"{p_rocks}/Rocks_006.png"),
        ]

        self.sprites_detritos = {
            "rocha_media_1": ResourceManager.carregar_imagem(f"{p_rocks}/Rocks_001.png", (44, 40)),
            "rocha_media_2": ResourceManager.carregar_imagem(f"{p_rocks}/Rocks_002.png", (40, 36)),
            "pedregulho_1": ResourceManager.carregar_imagem(f"{p_rocks}/Rocks_003.png", (24, 20)),
            "pedregulho_2": ResourceManager.carregar_imagem(f"{p_rocks}/Rocks_004.png", (22, 18)),
            "cascalho": ResourceManager.carregar_imagem(f"{p_rocks}/Rocks_007.png", (16, 12)),
        }

        # 5. Vegetação
        p_veg = "assets/cenario/vegetacao_pedras_separadas/Vegetation"
        self.sprites_veg = {
            "arbusto": ResourceManager.carregar_imagem(f"{p_veg}/Vegetation_001.png", (28, 28)),
            "tufo_grama": ResourceManager.carregar_imagem(f"{p_veg}/Vegetation_034.png", (24, 24)),
            "flor_silvestre": ResourceManager.carregar_imagem(f"{p_veg}/Vegetation_012.png", (20, 20)),
        }

    def inicializar_cenario(self):
        """Configura hitboxes das barreiras, árvores em pé e pedras do deslizamento."""
        self.hitboxes = []
        self.hitboxes.extend(self.barreiras_estrada)
        self.limite_oeste = pygame.Rect(0, 0, 20, self.altura_tela)
        self.hitboxes.append(self.limite_oeste)
        self.hitboxes.extend(self.pedras_deslizamento)

        # Colisões na base dos troncos em pé
        for x, y, w, h, _ in self.arvores_norte:
            self.hitboxes.append(pygame.Rect(x + (w // 2) - 16, y + h - 28, 32, 24))

        for x, y, w, h, _ in self.arvores_sul:
            self.hitboxes.append(pygame.Rect(x + (w // 2) - 16, y + h - 28, 32, 24))

        # Colisões das árvores caídas no solo
        self.hitboxes.append(pygame.Rect(930, 195, 110, 35))
        self.hitboxes.append(pygame.Rect(960, 445, 110, 35))

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
                pygame.Rect(1110, 430, 28, 20),
                pygame.Rect(1160, 440, 30, 22),
                pygame.Rect(1090, 450, 22, 16)
            ]
        else:
            self.pedras_deslizamento = [
                pygame.Rect(1100, 190, 65, 55),
                pygame.Rect(1150, 500, 70, 60)
            ]

    def desenhar_camada_inferior(self, tela):
        """Renderiza chão com estrada, vegetação e cascalho do deslizamento."""
        if self.chao_completo:
            tela.blit(self.chao_completo, (0, 0))
        else:
            tela.fill(CENARIO_GRAMA_CINZA)
            pygame.draw.rect(tela, CENARIO_ESTRADA, self.area_estrada)

        # 1. Vegetação sobrevivente nas margens
        for px, py, chave in self.vegetacao_margem:
            sprite = self.sprites_veg.get(chave)
            if sprite:
                tela.blit(sprite, (px, py))

        # 2. Cascalho e detritos menores da avalanche
        for px, py, chave in self.pedras_espalhadas:
            sprite = self.sprites_detritos.get(chave)
            if sprite:
                tela.blit(sprite, (px, py))

    def desenhar_props(self, tela):
        """Renderiza árvores em pé, árvores tombadas e o bloqueio de rochas maciças."""
        # 1. Árvores em Pé
        for x, y, w, h, k in self.arvores_norte + self.arvores_sul:
            sprite = self.sprites_arvores.get(k)
            if sprite:
                tela.blit(sprite, (x, y))

        # 2. Árvores Caídas e Troncos Partidos pelo Impacto
        for x, y, _, chave in self.arvores_caidas:
            sprite = self.sprites_caidas.get(chave)
            if sprite:
                tela.blit(sprite, (x, y))

        # 3. Barricada de Rochas Ancestrais
        for i, pedra in enumerate(self.pedras_deslizamento):
            idx = i % len(self.sprites_rochas_grandes)
            sprite = self.sprites_rochas_grandes[idx]
            if sprite:
                img_escalada = pygame.transform.scale(sprite, (pedra.width, pedra.height))
                tela.blit(img_escalada, pedra.topleft)
            else:
                pygame.draw.rect(tela, COR_PEDRA_DESLIZAMENTO, pedra)
                pygame.draw.rect(tela, COR_BORDA_PEDRA, pedra, 2)
