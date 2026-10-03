# src/maps/mapa_casa.py
import pygame
from src.maps.cenario_base import CenarioBase
from src.entities.item import Item
from src.utils.resource_manager import ResourceManager
from src.utils.colors import (
    CENARIO_FUNDO_FORA, CENARIO_PAREDE_CASA,
    CENARIO_CHAO_CASA, CENARIO_PORTA, CENARIO_MOVEIS,
    COLOR_BOLSA_MOEDAS, COLOR_LIVRO_ANTIGO, COLOR_CAJADO_MAGICO
)


class MapaCasa(CenarioBase):
    """
    Representa a residência inicial de Halia e seu entorno florestal com lago natural e mata densa.
    O exterior conta com um gramado verdejante, um lago sereno à frente da casa com contorno
    perfeito de margens e quinas orgânicas, uma densa mata fechada após o lago que atua como cenário,
    e uma estrada de terra rústica com bordas de transição natural para a grama.
    O interior é acolhedor e unificado: paredes modulares de madeira limpas (sem saliências verticais),
    chão de tábuas de madeira contínuo, cômoda e cama ligeiramente aumentadas, itens proporcionais,
    e um amplo tapete ornamental retangular com borda dourada.
    """

    def __init__(self, game, largura_tela, altura_tela):
        self.porta_aberta = False

        # Dimensões da Casa
        # x=60..500 (largura 440), y=60..540 (altura 480)
        self.area_chao_casa = pygame.Rect(60, 60, 440, 480)

        # Porta Frontal com vão de 64px, nivelada exatamente com a altura da parede (34px)
        self.porta = pygame.Rect(248, 506, 64, 34)
        self.hitbox_porta = pygame.Rect(248, 506, 64, 34)

        # Paredes com Colisões Físicas 2.5D
        self.paredes_casa = [
            pygame.Rect(60, 60, 440, 36),             # Parede Norte
            pygame.Rect(60, 60, 16, 480),             # Parede Oeste (Lateral Fina)
            pygame.Rect(484, 60, 16, 480),            # Parede Leste (Lateral Fina)
            pygame.Rect(60, 506, 188, 34),            # Parede Sul Esquerda
            pygame.Rect(312, 506, 188, 34),           # Parede Sul Direita
        ]

        # Móveis do Quarto (tamanhos aumentados ligeiramente e hitboxes na base física)
        # 1. Cama Casal: 82x98
        self.rect_cama = pygame.Rect(80, 105, 82, 98)
        self.hitbox_cama = pygame.Rect(80, 155, 82, 45)

        # 2. Cômoda / Estante: 78x32
        self.rect_estante = pygame.Rect(365, 105, 78, 32)
        self.hitbox_estante = pygame.Rect(365, 118, 78, 18)

        # 3. Tapete Ornamental amplo com borda dourada centralizado
        self.rect_tapete = pygame.Rect(190, 210, 180, 160)

        self.moveis = [self.hitbox_cama, self.hitbox_estante]

        # Pequeno Lago Sereno no jardim à frente da residência
        self.rect_lago = pygame.Rect(580, 160, 224, 160)
        self.hitbox_lago = pygame.Rect(588, 168, 208, 144)

        # Limites colidíveis do exterior
        # Halia não pode vagar desnecessariamente pela região do lago/mata; fica como belo cenário comum
        self.limites_jardim = [
            pygame.Rect(0, 540, 248, 180),            # Bosque denso à esquerda da trilha da porta
            pygame.Rect(312, 608, 968, 20),           # Borda norte da estrada (resguarda o lago e mata como cenário)
            pygame.Rect(0, 704, 1280, 20),            # Borda sul da estrada
            self.hitbox_lago,                         # Margem d'água
        ]

        # Pequena Estrada de Terra Rústica (sai da porta e ruma ao leste)
        self.trilha_porta = pygame.Rect(248, 540, 64, 100)
        self.trilha_jardim = pygame.Rect(248, 640, 1032, 64)

        # Vegetação Rica e Detalhada: moitas, juncos aquáticos, pedras, flores e cogumelos
        self.props_exterior = [
            # Margem e orla do lago (plantas aquáticas e juncos)
            (575, 305, "m48"), (615, 142, "m50"), (775, 142, "m50"),
            (795, 230, "m66"), (740, 310, "m48"),
            # Pedras naturais na orla e jardim
            (565, 175, "r03"), (805, 280, "r04"), (620, 330, "r04"),
            (690, 148, "r03"), (520, 480, "r03"), (380, 615, "r04"),
            # Flores coloridas no gramado
            (520, 200, "v12"), (540, 260, "v18"), (520, 360, "v12"),
            (480, 580, "v18"), (380, 580, "v12"),
            # Cogumelos do bosque
            (510, 360, "v27"),
            # Moitas densas
            (510, 75, "m31"), (510, 240, "m22"), (510, 420, "m26"),
            (660, 340, "m01"),
            # Arbustos na orla da mata fechada
            (810, 560, "m31"), (920, 560, "m26"), (1030, 560, "m22"), (1140, 560, "m31"),
            (205, 550, "m31"), (320, 550, "m22"), (215, 605, "m01"),
            (180, 650, "m26"), (210, 680, "m66"),
        ]

        # Densa Mata Fechada (após o lago e acima do lago)
        self.arvores_exterior = [
            # Fileira superior contornando o lago
            (560, 10, 106, 160, "t1_sz5_a"),
            (680, 15, 106, 160, "t1_sz5_b"),
            (800, 10, 106, 160, "t1_sz5_a"),
            (920, 15, 106, 160, "t1_sz5_b"),
            (1030, 10, 106, 160, "t1_sz5_a"),
            (1140, 15, 106, 160, "t1_sz5_b"),
            # Floresta densa e fechada após o lago (x > 820)
            (830, 120, 106, 160, "t1_sz5_b"),
            (940, 130, 106, 160, "t1_sz5_a"),
            (1050, 125, 106, 160, "t1_sz5_b"),
            (1160, 120, 106, 160, "t1_sz5_a"),
            (840, 240, 106, 160, "t1_sz5_a"),
            (950, 235, 106, 160, "t1_sz5_b"),
            (1060, 240, 106, 160, "t1_sz5_a"),
            (1170, 235, 106, 160, "t1_sz5_b"),
            (830, 360, 106, 160, "t1_sz5_b"),
            (940, 355, 106, 160, "t1_sz5_a"),
            (1050, 360, 106, 160, "t1_sz5_b"),
            (1160, 355, 106, 160, "t1_sz5_a"),
            (840, 460, 106, 160, "t1_sz5_a"),
            (950, 465, 106, 160, "t1_sz5_b"),
            (1060, 460, 106, 160, "t1_sz5_a"),
            (1170, 465, 106, 160, "t1_sz5_b"),
        ]

        super().__init__(game, largura_tela, altura_tela, nome="CASA")

    def carregar_recursos(self):
        """Carrega e armazena em cache as texturas, paredes modulares, lago e decorações."""
        p_cen = "assets/cenario"
        p_props_int = f"{p_cen}/sprites_separadas_interior/Buildings_Interior_Interior_Props_01"
        p_props_ext = f"{p_cen}/sprites_separadas_interior/Buildings_Props"
        p_walls = f"{p_cen}/sprites_separadas_interior/Buildings_Walls"
        p_veg = f"{p_cen}/vegetacao_pedras_separadas/Vegetation"
        p_rocks = f"{p_cen}/vegetacao_pedras_separadas/Rocks"
        p_pisos_ext = f"{p_cen}/02_Pisos_Externos"
        p_grama = f"{p_pisos_ext}/01_Grama_Verde"
        p_terra = f"{p_pisos_ext}/03_Terra_Marrom"
        p_agua = f"{p_pisos_ext}/06_Agua_Azul"

        # 1. Gramado do Exterior
        tile_grama = ResourceManager.carregar_imagem(f"{p_grama}/piso_grama_r10_c01.png", (32, 32))
        self.surf_chao_externo = ResourceManager.criar_superficie_32bit(self.largura_tela, self.altura_tela)
        if tile_grama:
            for y in range(0, self.altura_tela, 32):
                for x in range(0, self.largura_tela, 32):
                    self.surf_chao_externo.blit(tile_grama, (x, y))

        # 2. Piso Interno de Madeira Unificado
        img_piso_raw = ResourceManager.carregar_imagem(
            f"{p_cen}/sprites_separadas_interior/Buildings_Interior_Interior_Walls_01/Buildings_Interior_Interior_Walls_01_005_piso_madeira.png"
        )
        if img_piso_raw:
            tile_piso_madeira = img_piso_raw.subsurface((20, 20, 32, 32))
        else:
            tile_piso_madeira = None

        self.piso_madeira = ResourceManager.criar_superficie_32bit(self.area_chao_casa.width, self.area_chao_casa.height)
        self.piso_madeira.fill((107, 65, 28))
        if tile_piso_madeira:
            for y in range(0, self.area_chao_casa.height, 32):
                for x in range(0, self.area_chao_casa.width, 32):
                    self.piso_madeira.blit(tile_piso_madeira, (x, y))

        # 3. Pequeno Lago Natural com Quinas Flawless de Autotile
        self.tile_agua = ResourceManager.carregar_imagem(f"{p_agua}/piso_agua_r10_c02.png", (32, 32))
        self.tile_sh_top = ResourceManager.carregar_imagem(f"{p_agua}/piso_agua_r04_c02.png", (32, 32))
        self.tile_sh_bot = ResourceManager.carregar_imagem(f"{p_agua}/piso_agua_r00_c02.png", (32, 32))
        self.tile_sh_l = ResourceManager.carregar_imagem(f"{p_agua}/piso_agua_r02_c04.png", (32, 32))
        self.tile_sh_r = ResourceManager.carregar_imagem(f"{p_agua}/piso_agua_r02_c00.png", (32, 32))
        # Cantos perfeitos de lago (curvas contínuas sem vazamento de água)
        self.tile_c_tl = ResourceManager.carregar_imagem(f"{p_agua}/piso_agua_r03_c03.png", (32, 32))
        self.tile_c_tr = ResourceManager.carregar_imagem(f"{p_agua}/piso_agua_r03_c01.png", (32, 32))
        self.tile_c_bl = ResourceManager.carregar_imagem(f"{p_agua}/piso_agua_r01_c03.png", (32, 32))
        self.tile_c_br = ResourceManager.carregar_imagem(f"{p_agua}/piso_agua_r01_c01.png", (32, 32))

        # 4. Pequena Estrada de Terra Rústica com Transições de Grama
        self.tile_terra = ResourceManager.carregar_imagem(f"{p_terra}/piso_terra_r10_c11.png", (32, 32))
        self.trans_norte = ResourceManager.carregar_imagem(f"{p_grama}/piso_grama_r00_c02.png", (32, 32))
        self.trans_sul = ResourceManager.carregar_imagem(f"{p_grama}/piso_grama_r04_c02.png", (32, 32))
        self.trans_oeste = ResourceManager.carregar_imagem(f"{p_grama}/piso_grama_r02_c00.png", (32, 32))
        self.trans_leste = ResourceManager.carregar_imagem(f"{p_grama}/piso_grama_r02_c04.png", (32, 32))

        # 5. Paredes Modulares Legítimas de Madeira com Recorte Limpo (sem saliências)
        img_wall_raw = ResourceManager.carregar_imagem(f"{p_walls}/Buildings_Walls_002(parede madeira, recortar).png")
        if img_wall_raw:
            self.tl = img_wall_raw.subsurface((0, 16, 16, 26))
            self.tr = img_wall_raw.subsurface((80, 16, 16, 26))
            self.top_mid = img_wall_raw.subsurface((16, 16, 64, 26))

            self.side_l = img_wall_raw.subsurface((0, 32, 16, 32))
            self.side_r = img_wall_raw.subsurface((80, 32, 16, 32))

            self.bl = img_wall_raw.subsurface((0, 112, 16, 34))
            self.br = img_wall_raw.subsurface((80, 112, 16, 34))
            self.bot_mid = img_wall_raw.subsurface((16, 112, 64, 34))
        else:
            self.tl = self.tr = self.bl = self.br = None
            self.top_mid = self.bot_mid = self.side_l = self.side_r = None

        # 6. Porta Frontal de Madeira e sua Variação Aberta niveladas com a parede
        self.sprite_porta_fechada = ResourceManager.carregar_imagem(f"{p_props_ext}/porta_madeira.png", (64, 34))
        self.sprite_porta_aberta = ResourceManager.carregar_imagem(f"{p_props_ext}/porta_madeira_aberta.png", (64, 34))

        # 7. Móveis Ligeiramente Maiores e Proporcionais
        self.sprite_cama = (
            ResourceManager.carregar_imagem(f"{p_props_int}/Buildings_Interior_Interior_Props_01_096(cama casal).png", (82, 98)) or
            ResourceManager.carregar_imagem(f"{p_props_int}/Buildings_Interior_Interior_Props_01_096.png", (82, 98))
        )
        self.sprite_estante = ResourceManager.carregar_imagem(
            f"{p_props_int}/Buildings_Interior_Interior_Props_01_001(comoda).png", (78, 32)
        )

        # 8. Tapete Amplo com Borda Dourada Elegante
        img_tapete_raw = ResourceManager.carregar_imagem(f"{p_props_int}/tapete_verde_claro.png")
        if img_tapete_raw:
            self.sprite_tapete = pygame.transform.scale(img_tapete_raw, (self.rect_tapete.width, self.rect_tapete.height))
        else:
            self.sprite_tapete = None

        # 9. Dicionário de Sprites de Vegetação e Detalhes
        self.sprites_decor = {
            "v12": ResourceManager.carregar_imagem(f"{p_veg}/Vegetation_012.png"),
            "v18": ResourceManager.carregar_imagem(f"{p_veg}/Vegetation_018.png"),
            "v27": ResourceManager.carregar_imagem(f"{p_veg}/Vegetation_027.png"),
            "m48": ResourceManager.carregar_imagem(f"{p_veg}/Vegetation_048.png", (32, 26)),
            "m50": ResourceManager.carregar_imagem(f"{p_veg}/Vegetation_050.png"),
            "m66": ResourceManager.carregar_imagem(f"{p_veg}/Vegetation_066.png", (31, 25)),
            "r03": ResourceManager.carregar_imagem(f"{p_rocks}/Rocks_003.png"),
            "r04": ResourceManager.carregar_imagem(f"{p_rocks}/Rocks_004.png"),
            "m31": ResourceManager.carregar_imagem(f"{p_veg}/Vegetation_031.png", (43, 43)),
            "m22": ResourceManager.carregar_imagem(f"{p_veg}/Vegetation_022.png", (36, 32)),
            "m26": ResourceManager.carregar_imagem(f"{p_veg}/Vegetation_026.png", (42, 32)),
            "m01": ResourceManager.carregar_imagem(f"{p_veg}/Vegetation_001.png", (29, 27)),
            "m02": ResourceManager.carregar_imagem(f"{p_veg}/Vegetation_002.png", (29, 27)),
        }

        # 10. Árvores Frondosas Model 01 (com copas cheias)
        p_t1 = f"{p_cen}/arvores_separadas_tipo1"
        self.sprites_arvores = {
            "t1_sz5_a": ResourceManager.carregar_imagem(f"{p_t1}/Model_01_Size_05/Model_01_Size_05_01.png", (106, 160)),
            "t1_sz5_b": ResourceManager.carregar_imagem(f"{p_t1}/Model_01_Size_05/Model_01_Size_05_02.png", (106, 160)),
        }

    def inicializar_cenario(self):
        """Monta colisões ativas e distribui os itens no chão com proporções reduzidas."""
        self.hitboxes = []
        self.hitboxes.extend(self.paredes_casa)
        self.hitboxes.extend(self.moveis)
        self.hitboxes.extend(self.limites_jardim)

        # Troncos colidíveis da mata densa
        for x, y, w, h, _ in self.arvores_exterior:
            self.hitboxes.append(pygame.Rect(x + (w // 2) - 16, y + h - 28, 32, 24))

        if not self.porta_aberta:
            self.hitboxes.append(self.hitbox_porta)

        # Itens com tamanhos menores e perfeitos
        self.itens_no_chao = []
        itens_brutos = [
            Item("A Bolsa de Moedas", 390, 260, 28, 28, COLOR_BOLSA_MOEDAS, caminho_sprite="props/Bolsa de Moedas.png"),
            Item("O Livro Antigo", 200, 390, 30, 30, COLOR_LIVRO_ANTIGO, caminho_sprite="props/Grimório.png"),
            Item("O Cajado Mágico", 155, 130, 40, 40, COLOR_CAJADO_MAGICO, caminho_sprite="props/Cajado.png")
        ]

        itens_brutos[0].id_unico = "item_moedas"
        itens_brutos[1].id_unico = "item_livro"
        itens_brutos[2].id_unico = "item_cajado"

        coletados = getattr(self.game, 'itens_coletados', [])
        for item in itens_brutos:
            if item.id_unico not in coletados:
                self.itens_no_chao.append(item)

    def abrir_porta(self):
        """Abre a porta frontal da casa e libera a passagem para o jardim."""
        self.porta_aberta = True
        if self.hitbox_porta in self.hitboxes:
            self.hitboxes.remove(self.hitbox_porta)

    def fechar_porta(self):
        """Fecha e tranca a porta atrás de Halia após sair para o jardim."""
        self.porta_aberta = False
        if self.hitbox_porta not in self.hitboxes:
            self.hitboxes.append(self.hitbox_porta)

    def desenhar_camada_inferior(self, tela):
        """Renderiza o gramado, lago, estrada com transições, piso interno, tapete e paredes modulares."""
        # 1. Chão Exterior Contínuo
        if getattr(self, 'surf_chao_externo', None):
            tela.blit(self.surf_chao_externo, (0, 0))
        else:
            tela.fill(CENARIO_FUNDO_FORA)

        # 2. Lago Natural com Margens e Quinas Flawless
        if self.tile_agua:
            lx, ly, lw, lh = self.rect_lago.x, self.rect_lago.y, self.rect_lago.width, self.rect_lago.height
            # Centro de água
            for y in range(ly + 32, ly + lh - 32, 32):
                for x in range(lx + 32, lx + lw - 32, 32):
                    tela.blit(self.tile_agua, (x, y))
            # Margens retas
            if self.tile_sh_top and self.tile_sh_bot:
                for x in range(lx + 32, lx + lw - 32, 32):
                    tela.blit(self.tile_sh_top, (x, ly))
                    tela.blit(self.tile_sh_bot, (x, ly + lh - 32))
            if self.tile_sh_l and self.tile_sh_r:
                for y in range(ly + 32, ly + lh - 32, 32):
                    tela.blit(self.tile_sh_l, (lx, y))
                    tela.blit(self.tile_sh_r, (lx + lw - 32, y))
            # 4 Quinas orgânicas perfeitas
            if self.tile_c_tl and self.tile_c_tr and self.tile_c_bl and self.tile_c_br:
                tela.blit(self.tile_c_tl, (lx, ly))
                tela.blit(self.tile_c_tr, (lx + lw - 32, ly))
                tela.blit(self.tile_c_bl, (lx, ly + lh - 32))
                tela.blit(self.tile_c_br, (lx + lw - 32, ly + lh - 32))

        # 3. Pequena Estrada de Terra Rústica com Transições Orgânicas de Grama
        if self.tile_terra:
            # Estrada horizontal rumo ao leste (y=640..704)
            for x in range(self.trilha_jardim.left, self.trilha_jardim.right, 32):
                tela.blit(self.tile_terra, (x, 640))
                tela.blit(self.tile_terra, (x, 672))
                if self.trans_norte:
                    tela.blit(self.trans_norte, (x, 640))
                if self.trans_sul:
                    tela.blit(self.trans_sul, (x, 672))

            # Segmento vertical saindo da porta até a estrada
            for y in range(self.trilha_porta.top, self.trilha_porta.bottom, 32):
                tela.blit(self.tile_terra, (self.trilha_porta.left, y))
                tela.blit(self.tile_terra, (self.trilha_porta.left + 32, y))
                if self.trans_oeste:
                    tela.blit(self.trans_oeste, (self.trilha_porta.left, y))
                if self.trans_leste:
                    tela.blit(self.trans_leste, (self.trilha_porta.left + 32, y))

        # 4. Piso Interno de Madeira Unificado
        if self.piso_madeira:
            tela.blit(self.piso_madeira, self.area_chao_casa.topleft)
        else:
            pygame.draw.rect(tela, CENARIO_CHAO_CASA, self.area_chao_casa)

        # 5. Tapete Amplo com Borda Dourada Centralizado
        if self.sprite_tapete:
            tela.blit(self.sprite_tapete, self.rect_tapete.topleft)

        # 6. Paredes Modulares Legítimas de Madeira (Recorte limpo sem saliências verticais)
        if self.top_mid:
            # Parede Norte:
            tela.blit(self.tl, (60, 60))
            for x in range(76, 484, 64):
                w_clip = min(64, 484 - x)
                tela.blit(self.top_mid.subsurface((0, 0, w_clip, 26)), (x, 60))
            tela.blit(self.tr, (484, 60))

            # Paredes Laterais Finas (Oeste e Leste):
            for y in range(86, 506, 32):
                h_clip = min(32, 506 - y)
                tela.blit(self.side_l.subsurface((0, 0, 16, h_clip)), (60, y))
                tela.blit(self.side_r.subsurface((0, 0, 16, h_clip)), (484, y))

            # Parede Sul com vão ampliado da porta (x=248..312):
            door_x = self.porta.x
            door_w = self.porta.width
            tela.blit(self.bl, (60, 506))
            for x in range(76, door_x, 64):
                w_clip = min(64, door_x - x)
                tela.blit(self.bot_mid.subsurface((0, 0, w_clip, 34)), (x, 506))
            for x in range(door_x + door_w, 484, 64):
                w_clip = min(64, 484 - x)
                tela.blit(self.bot_mid.subsurface((0, 0, w_clip, 34)), (x, 506))
            tela.blit(self.br, (484, 506))
        else:
            for p in self.paredes_casa:
                pygame.draw.rect(tela, CENARIO_PAREDE_CASA, p)

        # 7. Detalhes de Vegetação, Pedras, Flores e Cogumelos no Jardim
        for px, py, chave in self.props_exterior:
            sprite = self.sprites_decor.get(chave)
            if sprite:
                tela.blit(sprite, (px, py))

    def desenhar_props(self, tela):
        """Renderiza a cama, cômoda restaurada, porta frontal e a densa mata fechada."""
        # 1. Cama de Madeira com Lençol
        if self.sprite_cama:
            tela.blit(self.sprite_cama, self.rect_cama.topleft)
        else:
            pygame.draw.rect(tela, CENARIO_MOVEIS, self.rect_cama)

        # 2. Cômoda / Estante de Madeira Restaurada
        if self.sprite_estante:
            tela.blit(self.sprite_estante, self.rect_estante.topleft)
        else:
            pygame.draw.rect(tela, CENARIO_MOVEIS, self.rect_estante)

        # 3. Porta Frontal de Madeira (preenchendo perfeitamente o vão e alinhada à parede)
        pos_porta = self.porta.topleft
        if not self.porta_aberta:
            if self.sprite_porta_fechada:
                tela.blit(self.sprite_porta_fechada, pos_porta)
            else:
                pygame.draw.rect(tela, (65, 42, 28), self.porta)
        else:
            if self.sprite_porta_aberta:
                tela.blit(self.sprite_porta_aberta, pos_porta)
            else:
                pygame.draw.rect(tela, (25, 20, 18), self.porta)

        # 4. Árvores Frondosas da Densa Mata Fechada
        for x, y, w, h, k in self.arvores_exterior:
            sprite = self.sprites_arvores.get(k)
            if sprite:
                tela.blit(sprite, (x, y))

    def desenhar_camada_superior(self, tela):
        """Renderiza camadas que sobrepõem o jogador se necessário."""
        pass
