# src/maps/tilemap_builder.py
import pygame
from src.utils.resource_manager import ResourceManager


class TilemapBuilder:
    """
    Construtor e Compositor de Superfícies de Terreno e Tilesets de Oblivium.

    Responsabilidades:
    - Extração e escalonamento de tiles individuais a partir de folhas de tileset.
    - Geração de superfícies contínuas preenchidas por repetição de tiles (pisos internos/externos).
    - Composição de terrenos com base de grama, estradas de terra e bordas de transição (autotiling).
    """

    _cache_terrenos = {}

    @classmethod
    def limpar_cache(cls):
        """Limpa o cache de superfícies de terreno e tiles."""
        cls._cache_terrenos.clear()

    @classmethod
    def obter_tile(cls, caminho_tileset, col, lin, tamanho_tile=16, escala=None):
        """
        Extrai um tile individual (16x16 por padrão) de uma folha de tileset com cache.
        """
        chave = f"tile_{caminho_tileset}_{col}x{lin}_{tamanho_tile}_{escala}"
        if chave in cls._cache_terrenos:
            return cls._cache_terrenos[chave]

        img_sheet = ResourceManager.carregar_imagem(caminho_tileset)
        if not img_sheet:
            return None

        rect = pygame.Rect(col * tamanho_tile, lin * tamanho_tile, tamanho_tile, tamanho_tile)
        if rect.right > img_sheet.get_width() or rect.bottom > img_sheet.get_height():
            return None

        tile = img_sheet.subsurface(rect).copy()
        if escala and escala != 1.0:
            nw = int(tamanho_tile * escala)
            nh = int(tamanho_tile * escala)
            tile = pygame.transform.scale(tile, (nw, nh))

        cls._cache_terrenos[chave] = tile
        return tile

    @classmethod
    def criar_superficie_tiled(cls, caminho_tileset, largura_total, altura_total, col=0, lin=0, tamanho_tile=16, escala_tile=2):
        """
        Cria uma superfície contínua preenchida pela repetição de um tile específico de um tileset.
        """
        chave = f"tiled_{caminho_tileset}_{col}x{lin}_{largura_total}x{altura_total}_{escala_tile}"
        if chave in cls._cache_terrenos:
            return cls._cache_terrenos[chave]

        tile = cls.obter_tile(caminho_tileset, col, lin, tamanho_tile=tamanho_tile, escala=escala_tile)
        if not tile:
            surf = ResourceManager.criar_superficie_32bit(largura_total, altura_total)
            surf.fill((35, 55, 30))
            return surf

        tw, th = tile.get_size()
        superficie_final = ResourceManager.criar_superficie_32bit(largura_total, altura_total)

        for y in range(0, altura_total, th):
            for x in range(0, largura_total, tw):
                superficie_final.blit(tile, (x, y))

        cls._cache_terrenos[chave] = superficie_final
        return superficie_final

    @classmethod
    def gerar_chao_com_estrada_e_transicao(cls, largura_total, altura_total, y_estrada=240, h_estrada=240):
        """
        Gera uma superfície de chão com base de grama verde, caminho central de terra
        e faixas de transição orgânica (bordas recortadas de grama sobre a terra).
        """
        chave = f"chao_estrada_transicao_{largura_total}x{altura_total}_{y_estrada}_{h_estrada}"
        if chave in cls._cache_terrenos:
            return cls._cache_terrenos[chave]

        p_ext = "assets/cenario/02_Pisos_Externos"
        p_grama = f"{p_ext}/01_Grama_Verde"
        p_terra = f"{p_ext}/03_Terra_Marrom"

        tile_grama = (
            ResourceManager.carregar_imagem(f"{p_grama}/piso_grama_r10_c01.png", (32, 32))
            or cls.obter_tile("assets/cenario/pisos_externos/grama/Floors_Tiles.png", 1, 10, tamanho_tile=16, escala=2)
        )
        tile_terra = (
            ResourceManager.carregar_imagem(f"{p_terra}/piso_terra_r10_c11.png", (32, 32))
            or cls.obter_tile("assets/cenario/pisos_externos/terra/Floors_Tiles.png", 11, 10, tamanho_tile=16, escala=2)
        )

        tile_trans_norte = ResourceManager.carregar_imagem(f"{p_grama}/piso_grama_r00_c02.png", (32, 32))
        tile_trans_sul = ResourceManager.carregar_imagem(f"{p_grama}/piso_grama_r04_c02.png", (32, 32))

        surf_final = ResourceManager.criar_superficie_32bit(largura_total, altura_total)
        tw, th = 32, 32

        if tile_grama:
            for y in range(0, altura_total, th):
                for x in range(0, largura_total, tw):
                    surf_final.blit(tile_grama, (x, y))

        surf_estrada = ResourceManager.criar_superficie_32bit(largura_total, h_estrada)
        if tile_terra:
            for y in range(0, h_estrada, th):
                for x in range(0, largura_total, tw):
                    surf_estrada.blit(tile_terra, (x, y))

        if tile_trans_norte:
            for x in range(0, largura_total, tw):
                surf_estrada.blit(tile_trans_norte, (x, 0))

        if tile_trans_sul:
            for x in range(0, largura_total, tw):
                surf_estrada.blit(tile_trans_sul, (x, h_estrada - th))

        surf_final.blit(surf_estrada, (0, y_estrada))

        cls._cache_terrenos[chave] = surf_final
        return surf_final
