# src/maps/mapa_oakhaven.py
import math
import random
import pygame
from src.maps.cenario_base import CenarioBase
from src.utils.resource_manager import ResourceManager
from src.entities.NPC import NPC
from src.entities.animal import Passaro, Gato
from src.entities.elemento_cenario import ChamaIndependente
from src.entities.item import Item


def _carregar_tiles_terreno():
    """
    Carrega e escala (32x32) os tiles sólidos e bordas de Grama, Terra, Tijolo de Pedra
    e Calçamento a partir de Floors_Tiles.png e 02_Pisos_Externos.
    """
    tiles = {
        "grama_centro": [],
        "grama_borda": {},
        "terra_centro": [],
        "pedra_centro": [],
        "pedra_borda": {},
        "calca_centro": [],
        "calca_borda": {},
    }

    sheet_floors = ResourceManager.carregar_imagem("assets/cenario/pisos_externos/pedra/Floors_Tiles.png")
    if sheet_floors:
        def _sub32(col, lin):
            sub = sheet_floors.subsurface(pygame.Rect(col * 16, lin * 16, 16, 16)).copy()
            return pygame.transform.scale(sub, (32, 32))

        # 1. Grama Sólida (linha 11, colunas 1..3) + Bordas de Grama sobre Terra/Pedra (linhas 0..4, colunas 0..4)
        tiles["grama_centro"] = [_sub32(1, 11), _sub32(2, 11), _sub32(3, 11)]
        tiles["grama_borda"] = {
            "N": [_sub32(1, 0), _sub32(2, 0), _sub32(3, 0)],
            "S": [_sub32(1, 4), _sub32(2, 4), _sub32(3, 4)],
            "W": [_sub32(0, 1), _sub32(0, 2), _sub32(0, 3)],
            "E": [_sub32(4, 1), _sub32(4, 2), _sub32(4, 3)],
            "NW": _sub32(1, 1),
            "NE": _sub32(3, 1),
            "SW": _sub32(1, 3),
            "SE": _sub32(3, 3),
        }

        # 2. Terra Sólida (linha 11, colunas 11..13)
        tiles["terra_centro"] = [_sub32(11, 11), _sub32(12, 11), _sub32(13, 11)]

        # 3. Tijolos de Pedra Cinza Sólidos (linhas 1..3, colunas 16..18) + Bordas (colunas 15..19)
        tiles["pedra_centro"] = [
            _sub32(16, 1), _sub32(17, 1), _sub32(18, 1),
            _sub32(16, 2), _sub32(17, 2), _sub32(18, 2),
            _sub32(16, 3), _sub32(17, 3), _sub32(18, 3),
        ]
        tiles["pedra_borda"] = {
            "N": [_sub32(16, 0), _sub32(17, 0), _sub32(18, 0)],
            "S": [_sub32(16, 4), _sub32(17, 4), _sub32(18, 4)],
            "W": [_sub32(15, 1), _sub32(15, 2), _sub32(15, 3)],
            "E": [_sub32(19, 1), _sub32(19, 2), _sub32(19, 3)],
            "NW": _sub32(16, 1),
            "NE": _sub32(18, 1),
            "SW": _sub32(16, 3),
            "SE": _sub32(18, 3),
        }

        # 4. Calçamento de Pedra Sólido (linha 11, colunas 6..8) + Bordas (linhas 0..4, colunas 5..9)
        tiles["calca_centro"] = [_sub32(6, 11), _sub32(7, 11), _sub32(8, 11)]
        tiles["calca_borda"] = {
            "N": [_sub32(6, 0), _sub32(7, 0), _sub32(8, 0)],
            "S": [_sub32(6, 4), _sub32(7, 4), _sub32(8, 4)],
            "W": [_sub32(5, 1), _sub32(5, 2), _sub32(5, 3)],
            "E": [_sub32(9, 1), _sub32(9, 2), _sub32(9, 3)],
            "NW": _sub32(6, 1),
            "NE": _sub32(8, 1),
            "SW": _sub32(6, 3),
            "SE": _sub32(8, 3),
        }

    return tiles


def _renderizar_grade_autotile(largura_mundo, altura_mundo, grade, tiles, seed=4201):
    """
    Renderiza uma grade 2D de tiles 32x32 com autotiling orgânico:
    0 = Grama Verde Sólida
    1 = Caminho de Terra Marrom (com bordas orgânicas de grama sobrepostas)
    2 = Praça/Calçada de Tijolos de Pedra Cinza (com bordas de grama quando adjacente à grama)
    3 = Pátio Interno de Calçamento de Pedra (Floors_Tiles cols 5..9)
    """
    surf = pygame.Surface((largura_mundo, altura_mundo))
    surf.fill((75, 128, 52))
    cols = len(grade[0])
    rows = len(grade)

    grama_c = tiles["grama_centro"]
    terra_c = tiles["terra_centro"]
    pedra_c = tiles["pedra_centro"]
    calca_c = tiles["calca_centro"] or pedra_c
    gb = tiles["grama_borda"]

    def _tipo(gx, gy):
        if 0 <= gx < cols and 0 <= gy < rows:
            return grade[gy][gx]
        return grade[max(0, min(rows - 1, gy))][max(0, min(cols - 1, gx))]

    def _sobrepor_borda_grama(px, py, gx, gy):
        n_grama = (_tipo(gx, gy - 1) == 0)
        s_grama = (_tipo(gx, gy + 1) == 0)
        w_grama = (_tipo(gx - 1, gy) == 0)
        e_grama = (_tipo(gx + 1, gy) == 0)

        if n_grama and w_grama and gb.get("NW"):
            surf.blit(gb["NW"], (px, py))
        elif n_grama and e_grama and gb.get("NE"):
            surf.blit(gb["NE"], (px, py))
        elif s_grama and w_grama and gb.get("SW"):
            surf.blit(gb["SW"], (px, py))
        elif s_grama and e_grama and gb.get("SE"):
            surf.blit(gb["SE"], (px, py))
        else:
            if n_grama and gb.get("N"):
                surf.blit(gb["N"][gx % len(gb["N"])], (px, py))
            if s_grama and gb.get("S"):
                surf.blit(gb["S"][gx % len(gb["S"])], (px, py))
            if w_grama and gb.get("W"):
                surf.blit(gb["W"][gy % len(gb["W"])], (px, py))
            if e_grama and gb.get("E"):
                surf.blit(gb["E"][gy % len(gb["E"])], (px, py))

    for gy in range(rows):
        for gx in range(cols):
            px, py = gx * 32, gy * 32
            t = grade[gy][gx]

            # 1. Base de grama sólida sempre desenhada por baixo
            if grama_c:
                sp_g = grama_c[(gx * 3 + gy * 5) % len(grama_c)]
                surf.blit(sp_g, (px, py))

            if t == 0:
                continue

            # 2. Caminho de Terra + Bordas Orgânicas de Grama
            if t == 1:
                if terra_c:
                    sp_t = terra_c[(gx * 7 + gy * 13) % len(terra_c)]
                    surf.blit(sp_t, (px, py))
                else:
                    pygame.draw.rect(surf, (176, 124, 82), (px, py, 32, 32))
                _sobrepor_borda_grama(px, py, gx, gy)

            # 3. Calçada / Praça de Tijolos de Pedra Cinza
            elif t == 2:
                if pedra_c:
                    sp_p = pedra_c[(gx * 3 + gy * 7) % len(pedra_c)]
                    surf.blit(sp_p, (px, py))
                _sobrepor_borda_grama(px, py, gx, gy)

            # 4. Pátio Nobre de Calçamento (Coração da Praça Central)
            elif t == 3:
                if pedra_c:
                    surf.blit(pedra_c[(gx + gy) % len(pedra_c)], (px, py))
                if calca_c:
                    sp_c = calca_c[(gx * 5 + gy * 3) % len(calca_c)]
                    surf.blit(sp_c, (px, py))
                # Moldura sutil nos limites entre o calçamento interno (3) e os tijolos externos (2)
                n_out = (_tipo(gx, gy - 1) != 3)
                s_out = (_tipo(gx, gy + 1) != 3)
                w_out = (_tipo(gx - 1, gy) != 3)
                e_out = (_tipo(gx + 1, gy) != 3)
                cor_friso = (96, 92, 88)
                if n_out:
                    pygame.draw.line(surf, cor_friso, (px, py), (px + 31, py), 2)
                if s_out:
                    pygame.draw.line(surf, cor_friso, (px, py + 31), (px + 31, py + 31), 2)
                if w_out:
                    pygame.draw.line(surf, cor_friso, (px, py), (px, py + 31), 2)
                if e_out:
                    pygame.draw.line(surf, cor_friso, (px + 31, py), (px + 31, py + 31), 2)

    return surf


class MapaOakhaven(CenarioBase):
    """
    Fase 1 — Vilarejo de Oakhaven (A Vila da Fronteira).
    Cenário expandido (2240 x 1480) com rolagem suave de câmera 2D (Viewport 1280 x 720).

    Diretrizes Arquiteturais Implementadas:
    - Autotiling pixel-art real em grade 70x47 (32x32) usando os tiles de Grama Verde,
      Terra Marrom com bordas de grama, Tijolos de Pedra Cinza e Calçamento da Praça.
    - Caminhos de terra conectando todas as ruas, pátios e portas de casas e lojas.
    - Tufos de grama verde, samambaias, flores silvestres, arbustos, cercas de madeira
      e árvores frondosas da vila em escala pixel-art proporcional.
    - Posicionamento revisado sem nenhuma sobreposição entre casas, barris, carroças,
      bebedouros, canteiros ou chamas da forja.
    """

    LARGURA_MUNDO = 2240
    ALTURA_MUNDO = 1480

    def __init__(self, game, largura_tela, altura_tela):
        self.estruturas_ysort = []
        self.props_chao = []
        self.focos_fogo = []
        self.ervas_coletaveis = []
        self.patusco = None
        self.timer_fonte = 0.0
        self.particulas_fonte = []
        self.timer_chamine = 0.0
        self.particulas_chamine = []
        self.chamine_fumaca = []
        self._noite_surf_cache = None

        super().__init__(
            game,
            largura_tela,
            altura_tela,
            nome="OAKHAVEN",
            largura_mundo=self.LARGURA_MUNDO,
            altura_mundo=self.ALTURA_MUNDO
        )
        self.inicializar_cenario()

    def carregar_recursos(self):
        """Carrega e pré-renderiza o terreno expandido de Oakhaven e todas as sprites da vila."""
        p_vila = "assets/cenario/vila"
        p_t1 = "assets/cenario/arvores_separadas_tipo1"
        p_veg = "assets/cenario/vegetacao_pedras_separadas/Vegetation"
        p_arv_vila = f"{p_veg}/arvores_estilo_separado"
        p_rocks = "assets/cenario/vegetacao_pedras_separadas/Rocks"
        p_cercas = "assets/cenario/08_Cercas"

        def _carregar_escala(caminho, escala):
            img = ResourceManager.carregar_imagem(caminho)
            if not img:
                return None
            nw = max(1, int(img.get_width() * escala))
            nh = max(1, int(img.get_height() * escala))
            return ResourceManager.carregar_imagem(caminho, (nw, nh))

        # 1. Monumento e Fonte Central
        self.spr_monumento = _carregar_escala(f"{p_vila}/Props/Monumentos/monumento_herois_intacto.png", 0.28)
        self.spr_fonte = _carregar_escala(f"{p_vila}/Props/Fontes/fonte_pedra_intacta.png", 0.32)

        # 2. Lojas Principais e Oficinas
        self.sprites_lojas = {
            "botanica_frente": _carregar_escala(f"{p_vila}/Lojas/Frente/loja_02_botanica_ervas_alquimia.png", 0.42),
            "magia_frente": _carregar_escala(f"{p_vila}/Lojas/Frente/loja_01_artigos_magicos_pocoes.png", 0.40),
            "floricultura_frente": _carregar_escala(f"{p_vila}/Lojas/Frente/loja_09_floricultura.png", 0.40),
            "taverna_frente": _carregar_escala(f"{p_vila}/Lojas/Frente/loja_13_taverna_estalagem_grande.png", 0.42),
            "livraria_frente": _carregar_escala(f"{p_vila}/Lojas/Frente/loja_11_livraria_biblioteca.png", 0.40),
            "armeria_frente": _carregar_escala(f"{p_vila}/Lojas/Frente/loja_12_armeria_ferraria.png", 0.42),
            "padaria_frente": _carregar_escala(f"{p_vila}/Lojas/Frente/loja_06_padaria_forno_pedra.png", 0.40),
            "emporio_frente": _carregar_escala(f"{p_vila}/Lojas/Frente/loja_05_emporio_frutas_mercearia.png", 0.40),
            "carpintaria_frente": _carregar_escala(f"{p_vila}/Lojas/Frente/loja_04_madeira_carpintaria.png", 0.40),
            "quitanda_costas": _carregar_escala(f"{p_vila}/Lojas/Costas/loja_08_quitanda_hortifruti.png", 0.40),
            "alfaiataria_costas": _carregar_escala(f"{p_vila}/Lojas/Costas/loja_10_alfaiataria_tecidos.png", 0.40),
            "olaria_costas": _carregar_escala(f"{p_vila}/Lojas/Costas/loja_03_ceramica_vasos_olaria.png", 0.40),
        }

        # 3. Casas Residenciais (Frente e Costas — para ruas e bordas parcialmente ocultas)
        self.sprites_casas = {
            "c1_f01": _carregar_escala(f"{p_vila}/Casas/Conjunto_1/Frente/casa_01_empena_simples.png", 0.42),
            "c1_f02": _carregar_escala(f"{p_vila}/Casas/Conjunto_1/Frente/casa_02_retangular_duas_janelas.png", 0.42),
            "c1_f03": _carregar_escala(f"{p_vila}/Casas/Conjunto_1/Frente/casa_03_empena_chamine_puxadinho.png", 0.42),
            "c1_f04": _carregar_escala(f"{p_vila}/Casas/Conjunto_1/Frente/casa_04_retangular_varanda_coberta.png", 0.42),
            "c1_f05": _carregar_escala(f"{p_vila}/Casas/Conjunto_1/Frente/casa_05_bancada_alpendre.png", 0.42),
            "c1_f06": _carregar_escala(f"{p_vila}/Casas/Conjunto_1/Frente/casa_06_casa_grande_chamine_central.png", 0.42),
            "c1_f07": _carregar_escala(f"{p_vila}/Casas/Conjunto_1/Frente/casa_07_forno_pedra_lareira.png", 0.42),
            "c2_f02_forja": _carregar_escala(f"{p_vila}/Casas/Conjunto_2/Frente/casa_02_com_forja_chamine.png", 0.42),
            "c2_f03_hera": _carregar_escala(f"{p_vila}/Casas/Conjunto_2/Frente/casa_03_com_hera_jardim.png", 0.42),
            "c2_f05_sobrado": _carregar_escala(f"{p_vila}/Casas/Conjunto_2/Frente/casa_05_sobrado_com_varanda.png", 0.42),
            "c2_f06_dois_andares": _carregar_escala(f"{p_vila}/Casas/Conjunto_2/Frente/casa_06_dois_andares_janelas.png", 0.42),
            # Costas (para borda sul e lados sul das ruas)
            "c1_b01": _carregar_escala(f"{p_vila}/Casas/Conjunto_1/Costas/casa_01_empena_simples.png", 0.42),
            "c1_b02": _carregar_escala(f"{p_vila}/Casas/Conjunto_1/Costas/casa_02_retangular_duas_janelas.png", 0.42),
            "c1_b03": _carregar_escala(f"{p_vila}/Casas/Conjunto_1/Costas/casa_03_empena_chamine_puxadinho.png", 0.42),
            "c1_b04": _carregar_escala(f"{p_vila}/Casas/Conjunto_1/Costas/casa_04_retangular_varanda_coberta.png", 0.42),
            "c1_b05": _carregar_escala(f"{p_vila}/Casas/Conjunto_1/Costas/casa_05_bancada_alpendre.png", 0.42),
            "c1_b06": _carregar_escala(f"{p_vila}/Casas/Conjunto_1/Costas/casa_06_casa_grande_chamine_central.png", 0.42),
            "c2_b03": _carregar_escala(f"{p_vila}/Casas/Conjunto_2/Costas/casa_03_com_hera_jardim.png", 0.42),
            "c2_b05": _carregar_escala(f"{p_vila}/Casas/Conjunto_2/Costas/casa_05_sobrado_com_varanda.png", 0.42),
            "c2_b06": _carregar_escala(f"{p_vila}/Casas/Conjunto_2/Costas/casa_06_dois_andares_janelas.png", 0.42),
        }

        # 4. Barracas de Feira (Frente e Costas)
        self.sprites_barracas = {
            "b_hortifruti": _carregar_escala(f"{p_vila}/Barracas/Frente/barraca_01_hortifruti_legumes.png", 0.34),
            "b_padaria": _carregar_escala(f"{p_vila}/Barracas/Frente/barraca_02_padaria_paes_queijos.png", 0.34),
            "b_flores": _carregar_escala(f"{p_vila}/Barracas/Frente/barraca_04_floricultura_vasos.png", 0.34),
            "b_alquimia": _carregar_escala(f"{p_vila}/Barracas/Frente/barraca_05_alquimia_pocoes.png", 0.34),
            "b_cristais": _carregar_escala(f"{p_vila}/Barracas/Frente/barraca_06_magia_cristais.png", 0.34),
            "b_ferraria": _carregar_escala(f"{p_vila}/Barracas/Frente/barraca_09_ferraria_ferramentas.png", 0.34),
            "b_livros": _carregar_escala(f"{p_vila}/Barracas/Frente/barraca_10_livros_mapas_pergaminhos.png", 0.34),
            "b_aventureiro": _carregar_escala(f"{p_vila}/Barracas/Frente/barraca_11_aventureiro_equipamentos.png", 0.34),
            "b_tecidos_costas": _carregar_escala(f"{p_vila}/Barracas/Costas/barraca_08_alfaiataria_tecidos.png", 0.34),
            "b_ceramica_costas": _carregar_escala(f"{p_vila}/Barracas/Costas/barraca_07_ceramica_esculturas.png", 0.34),
        }

        # 5. Props Urbanos, Cercas, Iluminação, Cargas e Jardins
        self.sprites_props = {
            "banco_pedra": _carregar_escala(f"{p_vila}/Props/Bancos/banco_pedra.png", 0.25),
            "banco_madeira": _carregar_escala(f"{p_vila}/Props/Bancos/banco_madeira.png", 0.25),
            "barris": _carregar_escala(f"{p_vila}/Props/Cargas_e_Transporte/barris_pilha.png", 0.26),
            "caixas_pilha": _carregar_escala(f"{p_vila}/Props/Cargas_e_Transporte/caixas_madeira_pilha.png", 0.26),
            "caixa_ind": _carregar_escala(f"{p_vila}/Props/Cargas_e_Transporte/caixa_madeira_individual.png", 0.24),
            "carrinho": _carregar_escala(f"{p_vila}/Props/Cargas_e_Transporte/carrinho_de_mao.png", 0.26),
            "carroca": _carregar_escala(f"{p_vila}/Props/Cargas_e_Transporte/carroca_quatro_rodas.png", 0.30),
            "lenha_org": _carregar_escala(f"{p_vila}/Props/Cargas_e_Transporte/pilha_lenha_organizada.png", 0.28),
            "lenha_bruta": _carregar_escala(f"{p_vila}/Props/Cargas_e_Transporte/pilha_lenha_bruta.png", 0.28),
            "poste_madeira": _carregar_escala(f"{p_vila}/Props/Iluminacao_e_Postes/poste_lanterna_madeira.png", 0.28),
            "poste_ferro": _carregar_escala(f"{p_vila}/Props/Iluminacao_e_Postes/poste_ferro.png", 0.28),
            "lanterna_cristal": _carregar_escala(f"{p_vila}/Props/Iluminacao_e_Postes/lanterna_cristal_magica.png", 0.26),
            "pilar_pedra": _carregar_escala(f"{p_vila}/Props/Iluminacao_e_Postes/pilar_pedra.png", 0.30),
            "estandarte": _carregar_escala(f"{p_vila}/Props/Placas_e_Estandartes/estandarte_vermelho.png", 0.28),
            "placa_dir": _carregar_escala(f"{p_vila}/Props/Placas_e_Estandartes/placa_direcional.png", 0.28),
            "quadro_avisos": _carregar_escala(f"{p_vila}/Props/Placas_e_Estandartes/quadro_avisos.png", 0.30),
            "bebedouro": _carregar_escala(f"{p_vila}/Props/Vegetacao_e_Jardim/bebedouro_tanque_pedra.png", 0.28),
            "canteiro_ervas": _carregar_escala(f"{p_vila}/Props/Vegetacao_e_Jardim/canteiro_ervas_verdes.png", 0.32),
            "canteiro_flores": _carregar_escala(f"{p_vila}/Props/Vegetacao_e_Jardim/canteiro_flores_roxas.png", 0.32),
            "jardineira_flores": _carregar_escala(f"{p_vila}/Props/Vegetacao_e_Jardim/jardineira_madeira_flores.png", 0.28),
            "jardineira_arbusto": _carregar_escala(f"{p_vila}/Props/Vegetacao_e_Jardim/jardineira_madeira_arbusto.png", 0.28),
            "vaso_azul": _carregar_escala(f"{p_vila}/Props/Vegetacao_e_Jardim/vaso_flores_azul.png", 0.26),
            "vaso_vermelho": _carregar_escala(f"{p_vila}/Props/Vegetacao_e_Jardim/vaso_flores_vermelho.png", 0.26),
            "vaso_arbusto": _carregar_escala(f"{p_vila}/Props/Vegetacao_e_Jardim/vaso_arbusto_grande.png", 0.26),
            "cerca_h": _carregar_escala(f"{p_cercas}/01_Frente_Horizontal/cerca_frente_horizontal_33x18.png", 2.0),
            "cerca_v": _carregar_escala(f"{p_cercas}/02_Lateral_Vertical/cerca_lateral_vertical_7x48.png", 2.0),
        }

        # 6. Árvores Frondosas da Vila (sem troncos mortos!)
        self.sprites_arvores = {
            "arv_vila_verde": _carregar_escala(f"{p_arv_vila}/arvore_verde_vila.png", 2.0),
            "arv_maca": _carregar_escala(f"{p_arv_vila}/arvore_maca.png", 2.0),
            "arv_betula": _carregar_escala(f"{p_arv_vila}/arvore_betula.png", 2.0),
            "arv_bolotas": _carregar_escala(f"{p_arv_vila}/arvore_folhas_bolotas.png", 2.0),
            "arv_g1": ResourceManager.carregar_imagem(f"{p_t1}/Model_01_Size_05/Model_01_Size_05_01.png", (112, 168)),
            "arv_g2": ResourceManager.carregar_imagem(f"{p_t1}/Model_01_Size_05/Model_01_Size_05_02.png", (112, 168)),
            "arv_m1": ResourceManager.carregar_imagem(f"{p_t1}/Model_01_Size_04/Model_01_Size_04_01.png", (82, 138)),
            "arv_m2": ResourceManager.carregar_imagem(f"{p_t1}/Model_01_Size_04/Model_01_Size_04_02.png", (82, 138)),
        }

        # 7. Tufos de Grama Verde, Samambaias, Flores Silvestres, Arbustos e Rochas (escala 2x proporcional)
        self.sprites_grama_tufos = [
            sp for sp in [
                _carregar_escala(f"{p_veg}/Vegetation_037.png", 2.0),
                _carregar_escala(f"{p_veg}/Vegetation_038.png", 2.0),
                _carregar_escala(f"{p_veg}/Vegetation_039.png", 2.0),
                _carregar_escala(f"{p_veg}/Vegetation_043.png", 1.8),
                _carregar_escala(f"{p_veg}/Vegetation_047.png", 1.8),
                _carregar_escala(f"{p_veg}/Vegetation_053.png", 2.0),
                _carregar_escala(f"{p_veg}/Vegetation_059.png", 2.0),
                _carregar_escala(f"{p_veg}/Vegetation_066.png", 2.0),
                _carregar_escala(f"{p_veg}/Vegetation_071.png", 2.0),
            ] if sp is not None
        ]
        self.sprites_flores = [
            sp for sp in [
                _carregar_escala(f"{p_veg}/Vegetation_050.png", 2.0),
                _carregar_escala(f"{p_veg}/Vegetation_055.png", 2.0),
                _carregar_escala(f"{p_veg}/Vegetation_122.png", 2.0),
                _carregar_escala(f"{p_veg}/Vegetation_133.png", 2.0),
                _carregar_escala(f"{p_veg}/Vegetation_150.png", 1.8),
                _carregar_escala(f"{p_veg}/Vegetation_164.png", 1.8),
            ] if sp is not None
        ]
        self.sprites_arbustos = [
            sp for sp in [
                _carregar_escala(f"{p_veg}/Vegetation_001.png", 1.8),
                _carregar_escala(f"{p_veg}/Vegetation_022.png", 1.8),
                _carregar_escala(f"{p_veg}/Vegetation_026.png", 1.8),
                _carregar_escala(f"{p_veg}/Vegetation_031.png", 1.8),
            ] if sp is not None
        ]
        self.sprites_rochas = [
            sp for sp in [
                _carregar_escala(f"{p_rocks}/Rocks_001.png", 1.4),
                _carregar_escala(f"{p_rocks}/Rocks_003.png", 1.5),
            ] if sp is not None
        ]
        # Rocha de Minério Bruto (para a missão secundária do Ferreiro Torvald)
        self.spr_rocha_minerio_intacta = _carregar_escala(f"{p_rocks}/Rocks_005.png", 2.1)
        self.spr_cristal_minerio = _carregar_escala(f"{p_rocks}/Rocks_106.png", 1.8)
        self.spr_rocha_minerio_quebrada_1 = _carregar_escala(f"{p_rocks}/Rocks_018.png", 2.2)
        self.spr_rocha_minerio_quebrada_2 = _carregar_escala(f"{p_rocks}/Rocks_024.png", 2.2)

        # 8. Superfície pré-renderizada do solo completo de Oakhaven (2240 x 1480)
        self.chao_completo = self._construir_superficie_terreno()

    def _construir_superficie_terreno(self):
        """
        Gera o terreno rico de Oakhaven via Autotiler 70x47 (tiles 32x32):
        - Grama verde pixel-art em todo o solo natural
        - Estradas de terra batida, alamedas, pátios e trilhas até a porta de cada casa/loja
          com bordas orgânicas de grama sobrepostas
        - Praça Central de tijolos de pedra cinza + pátio interno de calçamento arredondado
        - Tufos de grama verde, flores silvestres, arbustos e pedregulhos nas áreas gramadas
        """
        w, h = self.largura_mundo, self.altura_mundo
        cols = w // 32       # 70 colunas
        rows = (h // 32) + 1  # 47 linhas (1504px, recortado em 1480px)
        grade = [[0 for _ in range(cols)] for _ in range(rows)]

        def _marcar_rect(gx1, gy1, gx2, gy2, tipo):
            for gy in range(max(0, gy1), min(rows, gy2 + 1)):
                for gx in range(max(0, gx1), min(cols, gx2 + 1)):
                    grade[gy][gx] = tipo

        # ---------------------------------------------------------------------
        # 1. ESTRADAS PRINCIPAIS, ALAMEDAS E TRILHAS DE TERRA (tipo = 1)
        # ---------------------------------------------------------------------
        # Estrada Principal Norte-Sul (Portão Norte -> Praça -> Portão Sul)
        _marcar_rect(32, 0, 37, 46, 1)
        # Avenida Principal Oeste-Leste (Distrito Botânico <-> Praça <-> Distrito da Forja)
        _marcar_rect(0, 19, 69, 22, 1)
        # Alameda Noroeste (Taverna e Livraria) + Ramais + Portas das Lojas
        _marcar_rect(2, 10, 32, 12, 1)
        _marcar_rect(14, 12, 16, 19, 1)
        _marcar_rect(23, 12, 25, 19, 1)
        _marcar_rect(1, 9, 2, 10, 1)      # Porta c1_f04
        _marcar_rect(12, 9, 14, 10, 1)    # Porta Taverna
        _marcar_rect(21, 9, 22, 10, 1)    # Porta Livraria
        # Alameda Nordeste (Padaria, Empório e Carpintaria) + Ramais + Portas
        _marcar_rect(37, 10, 66, 12, 1)
        _marcar_rect(44, 12, 46, 19, 1)
        _marcar_rect(54, 12, 56, 19, 1)
        _marcar_rect(47, 9, 49, 10, 1)    # Porta Padaria
        _marcar_rect(55, 9, 57, 10, 1)    # Porta Empório
        _marcar_rect(62, 9, 64, 10, 1)    # Porta Carpintaria
        # Portas das Lojas na Avenida Oeste e Leste
        _marcar_rect(1, 18, 2, 19, 1)     # Porta c2_f05_sobrado
        _marcar_rect(7, 18, 9, 19, 1)     # Porta Loja de Magia
        _marcar_rect(20, 18, 22, 19, 1)   # Porta Floricultura
        _marcar_rect(66, 18, 68, 19, 1)   # Porta c1_f06
        # Trilha da Clareira Botânica de Elara (Sudoeste)
        _marcar_rect(6, 22, 19, 25, 1)
        _marcar_rect(6, 25, 9, 34, 1)
        _marcar_rect(9, 31, 16, 34, 1)
        # Pátio de Trabalho da Forja e Feira Leste (Sudeste)
        _marcar_rect(46, 22, 62, 26, 1)
        _marcar_rect(52, 26, 57, 29, 1)
        # Rua Residencial Sul (Oeste e Leste da Estrada Sul) + Ramais para as casas
        _marcar_rect(4, 36, 32, 38, 1)
        _marcar_rect(37, 36, 65, 38, 1)
        _marcar_rect(20, 34, 22, 36, 1)   # Porta casa c1_f03
        _marcar_rect(28, 34, 30, 36, 1)   # Porta casa c2_f03_hera
        _marcar_rect(41, 34, 43, 36, 1)   # Porta casa c1_f05
        _marcar_rect(49, 34, 51, 36, 1)   # Porta casa c2_f06_dois_andares
        _marcar_rect(57, 34, 59, 36, 1)   # Porta casa c1_f07

        # ---------------------------------------------------------------------
        # 2. PRAÇA CENTRAL DOS HERÓIS & CALÇADAS DE PEDRA (tipos = 2 e 3)
        # ---------------------------------------------------------------------
        # Calçada da Botânica de Elara e Calçada da Armeria/Forja de Torvald
        _marcar_rect(13, 18, 17, 20, 2)
        _marcar_rect(49, 18, 61, 20, 2)
        # Grande Praça Central de Tijolos de Pedra Cinza
        _marcar_rect(24, 14, 45, 28, 2)
        # Pátio Interno Nobre (Calçamento de Pedra ao redor do Monumento e da Fonte)
        _marcar_rect(27, 15, 42, 26, 3)

        tiles = _carregar_tiles_terreno()
        surf_grade = _renderizar_grade_autotile(w, rows * 32, grade, tiles, seed=4201)
        surf = pygame.Surface((w, h))
        surf.blit(surf_grade, (0, 0), pygame.Rect(0, 0, w, h))

        # ---------------------------------------------------------------------
        # 3. PALIÇADA DEFENSIVA NORTE (Muralha de Toras de Carvalho no limite norte)
        # ---------------------------------------------------------------------
        for tx in range(0, w, 28):
            if 1030 <= tx <= 1200:
                continue  # Abertura do Portão Norte vigiado por Guarda Doran
            altura_tora = 84 + (tx % 3) * 5
            pygame.draw.rect(surf, (62, 42, 28), (tx, 0, 26, altura_tora))
            pygame.draw.rect(surf, (92, 66, 44), (tx + 3, 4, 20, altura_tora - 8))
            pygame.draw.polygon(
                surf,
                (48, 32, 20),
                [(tx, altura_tora), (tx + 13, altura_tora + 12), (tx + 26, altura_tora)]
            )

        # ---------------------------------------------------------------------
        # 4. VEGETAÇÃO RASTEIRA: TUFOS DE GRAMA VERDE, FLORES E ARBUSTOS
        # ---------------------------------------------------------------------
        rng = random.Random(4207)
        for gy in range(3, rows - 2):
            for gx in range(1, cols - 1):
                if grade[gy][gx] != 0:
                    continue
                # Evita desenhar em cima de calçadas/estradas vizinhas imediatas
                if any(
                    grade[ max(0, min(rows - 1, gy + dy)) ][ max(0, min(cols - 1, gx + dx)) ] != 0
                    for dy in (-1, 0, 1) for dx in (-1, 0, 1)
                ):
                    if rng.random() > 0.22:
                        continue
                else:
                    if rng.random() > 0.34:
                        continue

                px = gx * 32 + rng.randint(-6, 8)
                py = gy * 32 + rng.randint(-6, 8)
                if py < 96 or py > h - 48:
                    continue

                sorteio = rng.random()
                if sorteio < 0.65 and self.sprites_grama_tufos:
                    sp = rng.choice(self.sprites_grama_tufos)
                    surf.blit(sp, (px, py))
                elif sorteio < 0.88 and self.sprites_flores:
                    sp = rng.choice(self.sprites_flores)
                    surf.blit(sp, (px, py))
                elif sorteio < 0.96 and self.sprites_arbustos:
                    sp = rng.choice(self.sprites_arbustos)
                    surf.blit(sp, (px, py))
                elif self.sprites_rochas:
                    sp = rng.choice(self.sprites_rochas)
                    surf.blit(sp, (px, py))

        # Canteiro natural de grama alta onde Patusco (Easter Egg 1/7) se esconde (1855, 885)
        if self.sprites_grama_tufos:
            for ox, oy, idx in [
                (-28, -10, 0), (14, -12, 1), (-32, 12, 2),
                (18, 10, 5), (-8, 18, 6), (4, -18, 7)
            ]:
                sp_tufo = self.sprites_grama_tufos[idx % len(self.sprites_grama_tufos)]
                surf.blit(sp_tufo, (1855 + ox, 885 + oy))

        return surf

    def inicializar_cenario(self):
        """Popula todas as construções, cercas, árvores, props, NPCs, pássaros, ervas e Patusco."""
        self.hitboxes = []
        self.itens_no_chao = []
        self.estruturas_ysort = []
        self.props_chao = []

        w, h = self.largura_mundo, self.altura_mundo

        # Limites externos do mapa
        self.hitboxes.extend([
            pygame.Rect(0, 0, 1030, 92),              # Paliçada Norte Esquerda
            pygame.Rect(1200, 0, w - 1200, 92),       # Paliçada Norte Direita
            pygame.Rect(1030, 0, 170, 36),            # Portão Norte (Saída controlada por Guarda Doran)
            pygame.Rect(0, 0, 18, h),                 # Borda Oeste
            pygame.Rect(w - 18, 0, 18, h),            # Borda Leste
            pygame.Rect(0, h - 18, 1024, 18),         # Borda Sul Esquerda
            pygame.Rect(1216, h - 18, w - 1216, 18),  # Borda Sul Direita
        ])

        def _add_estrutura(sprite, x, y, hitbox_rel=None, sombra=True, y_sort_custom=None):
            if not sprite:
                return
            sw, sh = sprite.get_size()
            if hitbox_rel is None:
                # Hitbox 2.5D padrão: ocupa os 38% inferiores da construção (permitindo passar atrás do telhado!)
                hb = pygame.Rect(int(x + sw * 0.08), int(y + sh * 0.58), int(sw * 0.84), int(sh * 0.36))
            else:
                rx, ry, rw, rh = hitbox_rel
                hb = pygame.Rect(int(x + rx), int(y + ry), int(rw), int(rh))
            if hb.width > 0 and hb.height > 0:
                self.hitboxes.append(hb)

            # Pré-renderização da sombra para zero alocações por frame
            sombra_surf = None
            if sombra:
                sombra_larg = int(sw * 0.86)
                sombra_surf = pygame.Surface((sombra_larg, 18), pygame.SRCALPHA)
                pygame.draw.ellipse(sombra_surf, (14, 18, 16, 75), (0, 0, sombra_larg, 18))

            calc_ysort = y_sort_custom if y_sort_custom is not None else max(int(hb.bottom), int(y + sh - 4))
            self.estruturas_ysort.append({
                "sprite": sprite,
                "x": int(x),
                "y": int(y),
                "y_sort": calc_ysort,
                "sombra": sombra,
                "sombra_surf": sombra_surf,
                "sw": sw,
                "sh": sh,
                "rect": pygame.Rect(int(x), int(y), sw, sh)
            })

        # =====================================================================
        # 1. PRAÇA CENTRAL DOS HERÓIS (Coração de Oakhaven)
        # =====================================================================
        # Monumento dos 6 Heróis (no topo norte da Praça Central)
        _add_estrutura(self.spr_monumento, 935, 455, hitbox_rel=(18, 82, 334, 52))
        # Fonte de Pedra Intacta (no centro-sul da Praça Central)
        _add_estrutura(self.spr_fonte, 1042, 705, hitbox_rel=(20, 62, 116, 66))

        # Bancos de pedra, postes de iluminação, quadro de avisos e vasos ao redor da Praça
        _add_estrutura(self.sprites_props["banco_pedra"], 835, 585, hitbox_rel=(6, 22, 60, 20))
        _add_estrutura(self.sprites_props["banco_pedra"], 1330, 585, hitbox_rel=(6, 22, 60, 20))
        _add_estrutura(self.sprites_props["banco_pedra"], 835, 755, hitbox_rel=(6, 22, 60, 20))
        _add_estrutura(self.sprites_props["banco_pedra"], 1330, 755, hitbox_rel=(6, 22, 60, 20))
        _add_estrutura(self.sprites_props["quadro_avisos"], 1245, 815, hitbox_rel=(10, 48, 65, 24))
        _add_estrutura(self.sprites_props["placa_dir"], 975, 885, hitbox_rel=(12, 50, 24, 20))

        for px, py in [(790, 445), (1410, 445), (790, 810), (1410, 810), (1000, 250), (1200, 250)]:
            _add_estrutura(self.sprites_props["poste_madeira"], px, py, hitbox_rel=(14, 72, 16, 18))

        for vx, vy, k_vaso in [
            (900, 495, "vaso_azul"), (1315, 495, "vaso_azul"),
            (995, 735, "jardineira_flores"), (1215, 735, "jardineira_flores"),
            (780, 550, "vaso_vermelho"), (1430, 550, "vaso_vermelho"),
        ]:
            _add_estrutura(self.sprites_props[k_vaso], vx, vy, hitbox_rel=(4, 26, 22, 14))

        # =====================================================================
        # 2. DISTRITO NOROESTE & OESTE — TAVERNA, LIVRARIA, BOTÂNICA DE ELARA & FEIRA
        # =====================================================================
        # Grande Taverna e Estalagem + Livraria na Alameda Noroeste (y=140..330, acima da alameda y=320..416)
        _add_estrutura(self.sprites_lojas["taverna_frente"], 310, 140)
        _add_estrutura(self.sprites_lojas["livraria_frente"], 610, 155)
        # Barris e banco posicionados ao lado da Taverna sem sobrepor a fachada
        _add_estrutura(self.sprites_props["barris"], 245, 285, hitbox_rel=(6, 26, 44, 24))
        _add_estrutura(self.sprites_props["banco_madeira"], 535, 295, hitbox_rel=(6, 20, 62, 18))

        # Botânica de Elara + Loja de Poções + Floricultura na Avenida Oeste (acima da calçada y=608)
        _add_estrutura(self.sprites_lojas["magia_frente"], 175, 430)
        _add_estrutura(self.sprites_lojas["botanica_frente"], 385, 425)
        _add_estrutura(self.sprites_lojas["floricultura_frente"], 600, 435)

        # Canteiros de Ervas flanqueando a loja de Elara (deixando a porta central em x=440..530 livre!)
        _add_estrutura(self.sprites_props["canteiro_ervas"], 330, 580, hitbox_rel=(6, 18, 56, 22))
        _add_estrutura(self.sprites_props["canteiro_flores"], 555, 580, hitbox_rel=(6, 18, 56, 22))

        # Barracas da Feira Botânica e Canteiros na Clareira Sudoeste
        _add_estrutura(self.sprites_barracas["b_hortifruti"], 155, 745)
        _add_estrutura(self.sprites_barracas["b_flores"], 355, 745)
        _add_estrutura(self.sprites_barracas["b_alquimia"], 555, 745)
        _add_estrutura(self.sprites_props["canteiro_ervas"], 185, 915, hitbox_rel=(6, 18, 56, 22))
        _add_estrutura(self.sprites_props["canteiro_flores"], 435, 915, hitbox_rel=(6, 18, 56, 22))

        # =====================================================================
        # 3. DISTRITO NORDESTE & LESTE — PADARIA, EMPÓRIO, ARMERIA & FORJA DE TORVALD
        # =====================================================================
        # Alameda Nordeste: Padaria, Empório e Carpintaria
        _add_estrutura(self.sprites_lojas["padaria_frente"], 1435, 145)
        _add_estrutura(self.sprites_lojas["emporio_frente"], 1690, 145)
        _add_estrutura(self.sprites_lojas["carpintaria_frente"], 1945, 155)

        # Avenida Leste: Armeria Principal + Casa da Forja de Torvald (hitbox refinada apenas na parede base)
        _add_estrutura(self.sprites_lojas["armeria_frente"], 1545, 425, hitbox_rel=(10, 110, 142, 48))
        _add_estrutura(self.sprites_casas["c2_f02_forja"], 1800, 420, hitbox_rel=(12, 104, 170, 54))

        # Pátio da Forja e Barracas de Equipamentos (espaçamento amplo para fluxo suave de Halia)
        _add_estrutura(self.sprites_barracas["b_ferraria"], 1485, 750)
        _add_estrutura(self.sprites_barracas["b_aventureiro"], 1925, 750)
        _add_estrutura(self.sprites_props["bebedouro"], 1645, 785, hitbox_rel=(6, 16, 52, 22))
        _add_estrutura(self.sprites_props["carroca"], 1755, 775, hitbox_rel=(10, 22, 76, 28))
        _add_estrutura(self.sprites_props["barris"], 1500, 585, hitbox_rel=(4, 18, 38, 18))
        _add_estrutura(self.sprites_props["caixas_pilha"], 1745, 600, hitbox_rel=(4, 18, 44, 18))
        _add_estrutura(self.sprites_props["lenha_org"], 2005, 575, hitbox_rel=(4, 18, 32, 18))

        # Rocha de Minério Bruto no Pátio da Forja (Missão Secundária de Torvald: missao_pedra_forja)
        pedra_quebrada = getattr(self.game, "pedra_torvald_quebrada", False)
        if not pedra_quebrada and self.spr_rocha_minerio_intacta:
            # Compõe a rocha com cristais de minério incrustados
            sp_rocha = self.spr_rocha_minerio_intacta.copy()
            if self.spr_cristal_minerio:
                sp_rocha.blit(self.spr_cristal_minerio, (18, 16))
            _add_estrutura(sp_rocha, 1835, 650, hitbox_rel=(8, 28, 56, 30))
        elif pedra_quebrada:
            if self.spr_rocha_minerio_quebrada_1:
                _add_estrutura(self.spr_rocha_minerio_quebrada_1, 1830, 675, hitbox_rel=(0, 0, 0, 0), sombra=False)
            if self.spr_rocha_minerio_quebrada_2:
                _add_estrutura(self.spr_rocha_minerio_quebrada_2, 1870, 682, hitbox_rel=(0, 0, 0, 0), sombra=False)

        # =====================================================================
        # 4. CASAS RESIDENCIAIS E CASAS NAS BORDAS DO MAPA (Zero sobreposições!)
        # =====================================================================
        # Borda Oeste (parcialmente ocultas na margem esquerda, reveladas ao explorar):
        _add_estrutura(self.sprites_casas["c1_f04"], -45, 155)
        _add_estrutura(self.sprites_casas["c2_f05_sobrado"], -55, 415)
        _add_estrutura(self.sprites_casas["c1_b05"], -55, 770)
        _add_estrutura(self.sprites_casas["c2_b06"], -45, 1135)

        # Borda Leste (parcialmente ocultas na margem direita):
        _add_estrutura(self.sprites_casas["c1_f06"], 2055, 415)
        _add_estrutura(self.sprites_casas["c1_b04"], 2110, 775)
        _add_estrutura(self.sprites_casas["c1_b01"], 2090, 1135)

        # Quarteirão Residencial Sul (voltadas para a Rua Residencial Sul em y=1152..1248):
        _add_estrutura(self.sprites_casas["c1_f03"], 575, 965)
        _add_estrutura(self.sprites_casas["c2_f03_hera"], 825, 980)
        _add_estrutura(self.sprites_casas["c1_f05"], 1245, 975)
        _add_estrutura(self.sprites_casas["c2_f06_dois_andares"], 1495, 965)
        _add_estrutura(self.sprites_casas["c1_f07"], 1755, 985)

        # Fileira Extrema Sul (telhados de costas parcialmente na borda inferior da câmera):
        _add_estrutura(self.sprites_casas["c1_b02"], 115, 1315)
        _add_estrutura(self.sprites_casas["c1_b04"], 415, 1305)
        _add_estrutura(self.sprites_casas["c1_b06"], 710, 1295)
        _add_estrutura(self.sprites_casas["c2_b03"], 1255, 1310)
        _add_estrutura(self.sprites_casas["c1_b03"], 1555, 1315)
        _add_estrutura(self.sprites_casas["c2_b05"], 1845, 1295)

        # Portão Norte — Pilares e Estandartes da Guarda de Oakhaven
        _add_estrutura(self.sprites_props["pilar_pedra"], 1000, 55, hitbox_rel=(4, 65, 16, 24))
        _add_estrutura(self.sprites_props["pilar_pedra"], 1210, 55, hitbox_rel=(4, 65, 16, 24))
        _add_estrutura(self.sprites_props["estandarte"], 950, 65, hitbox_rel=(6, 65, 32, 18))
        _add_estrutura(self.sprites_props["estandarte"], 1245, 65, hitbox_rel=(6, 65, 32, 18))

        # =====================================================================
        # 5. CERCAS DE MADEIRA DA VILA (08_Cercas)
        # =====================================================================
        sp_ch = self.sprites_props.get("cerca_h")
        if sp_ch:
            posicoes_cercas_h = [
                # Cercado do jardim botânico sudoeste
                (170, 865), (236, 865), (390, 865), (456, 865),
                # Cercas dos jardins residenciais sul
                (782, 1110), (1020, 1110),
                (1442, 1110), (1700, 1110),
                # Cercado rústico próximo ao canto de Patusco
                (1785, 920), (1851, 920),
                # Cercas decorativas ao longo da entrada sul
                (880, 1255), (946, 1255), (1225, 1255), (1291, 1255),
            ]
            for cx, cy in posicoes_cercas_h:
                _add_estrutura(sp_ch, cx, cy, hitbox_rel=(4, 20, 58, 14), sombra=False)

        # =====================================================================
        # 6. ÁRVORES FRONDOSAS DA VILA E BOSQUES INTERNOS (Zero árvores mortas!)
        # =====================================================================
        posicoes_arvores = [
            (115, 155, "arv_vila_verde"),
            (835, 145, "arv_maca"),
            (1305, 145, "arv_betula"),
            (2125, 155, "arv_vila_verde"),
            (65, 935, "arv_vila_verde"),
            (135, 1085, "arv_maca"),
            (465, 985, "arv_betula"),
            (910, 1190, "arv_m1"),
            (1225, 1190, "arv_m2"),
            (1985, 925, "arv_bolotas"),
        ]
        for ax, ay, k_arv in posicoes_arvores:
            sp_a = self.sprites_arvores.get(k_arv)
            if sp_a:
                aw, ah = sp_a.get_size()
                _add_estrutura(sp_a, ax, ay, hitbox_rel=(aw // 2 - 16, ah - 30, 32, 24))

        # =====================================================================
        # 7. FOCOS DE FOGO NA FORJA DE TORVALD (Dentro da fornalha de pedra!)
        # =====================================================================
        # A abertura arqueada da fornalha de c2_f02_forja (em x=1800, y=420) fica exatamente em (1919, 557)
        self.focos_fogo = [
            ChamaIndependente(1919, 557, tipo="chao_larga", escala=0.88, glow_base=24),
        ]

        # =====================================================================
        # 8. OS 4 NPCS INTERATIVOS DE OAKHAVEN
        # =====================================================================
        self.npcs = [
            NPC(
                nome="Ancião Aldous",
                x=1102,
                y=615,
                npc_id="anciao_aldous",
                dialogo_id="hub_aldous",
                tem_loja=False,
                arquetipo="anciao"
            ),
            NPC(
                nome="Curandeira Elara",
                x=465,
                y=625,
                npc_id="curandeira_elara",
                dialogo_id="hub_elara",
                tem_loja=True,
                loja_id="botanica_elara",
                arquetipo="curandeira"
            ),
            NPC(
                nome="Ferreiro Torvald",
                x=1665,
                y=625,
                npc_id="ferreiro_torvald",
                dialogo_id="hub_torvald",
                tem_loja=True,
                loja_id="loja_torvald",
                arquetipo="ferreiro"
            ),
            NPC(
                nome="Guarda Doran",
                x=1102,
                y=215,
                npc_id="guarda_doran",
                dialogo_id="hub_doran",
                tem_loja=False,
                arquetipo="guarda"
            ),
        ]
        for npc in self.npcs:
            self.hitboxes.append(pygame.Rect(int(npc.x), int(npc.y), npc.largura, npc.altura))

        # =====================================================================
        # 9. ERVAS DE ORVALHO LUNAR (Para a missão de Elara: missao_ervas_medicinais)
        # =====================================================================
        self.ervas_coletaveis = []
        coletados = getattr(self.game, "itens_coletados", [])
        posicoes_ervas = [
            ("erva_lunar_oakhaven_1", 255, 1015),
            ("erva_lunar_oakhaven_2", 365, 1095),
            ("erva_lunar_oakhaven_3", 445, 1020),
        ]
        spr_erva = self._gerar_sprite_erva_lunar()
        for id_erva, ex, ey in posicoes_ervas:
            if id_erva not in coletados:
                item_erva = Item(
                    nome="Erva de Orvalho Lunar",
                    x=ex,
                    y=ey,
                    largura=28,
                    altura=28,
                    cor=(110, 235, 195)
                )
                item_erva.id_unico = id_erva
                item_erva.imagem = spr_erva
                self.itens_no_chao.append(item_erva)
                self.ervas_coletaveis.append(item_erva)

    def respawn_erva_alternativa(self, item_antigo=None):
        """
        Quando uma colheita falha e a flor murcha, remove o nó danificado e
        faz brotar uma nova Erva de Orvalho Lunar em um local alternativo da vila.
        """
        if item_antigo and item_antigo in self.itens_no_chao:
            self.itens_no_chao.remove(item_antigo)
        if item_antigo and hasattr(self, "ervas_coletaveis") and item_antigo in self.ervas_coletaveis:
            self.ervas_coletaveis.remove(item_antigo)

        pontos_alternativos = [
            (680, 1120),  # Próximo ao canteiro do riacho
            (1420, 1080), # Perto da ponte leste
            (1890, 680),  # Bosque ao fundo da taverna
            (820, 520),   # Jardim ao lado da praça norte
            (160, 640),   # Encosta oeste da botânica
        ]
        
        # Filtra pontos livres onde não há itens muito próximos
        pontos_livres = []
        for px, py in pontos_alternativos:
            muito_perto = any(abs(it.x - px) < 40 and abs(it.y - py) < 40 for it in self.itens_no_chao)
            if not muito_perto:
                pontos_livres.append((px, py))
        
        novo_x, novo_y = pontos_livres[0] if pontos_livres else (700, 1100)
        
        nova_erva = Item(
            nome="Erva de Orvalho Lunar",
            x=novo_x,
            y=novo_y,
            largura=28,
            altura=28,
            cor=(110, 235, 195)
        )
        nova_erva.id_unico = f"erva_lunar_respawn_{len(self.itens_no_chao)}"
        nova_erva.imagem = self._gerar_sprite_erva_lunar()
        self.itens_no_chao.append(nova_erva)
        if hasattr(self, "ervas_coletaveis"):
            self.ervas_coletaveis.append(nova_erva)
            
        return nova_erva

        # =====================================================================
        # 10. FAUNA VIVA: PÁSSAROS E PATUSCO (EASTER EGG 1/7 NO TUFO DE GRAMA)
        # =====================================================================
        self.patusco = Gato(
            x=1855,
            y=885,
            direcao_inicial="esquerda",
            fase_id="OAKHAVEN",
            nome="Patusco",
            escala=1.75
        )
        self.animais = [
            self.patusco,
            Passaro(980, 760, direcao_inicial="direita"),
            Passaro(1240, 680, direcao_inicial="esquerda"),
            Passaro(510, 710, direcao_inicial="direita"),
            Passaro(1610, 690, direcao_inicial="esquerda"),
            Passaro(1080, 990, direcao_inicial="direita"),
        ]

        # Durante a noite em Oakhaven, a fauna (gato Patusco e pássaros) vai dormir e não fica visível
        eh_noite = getattr(self.game, "oakhaven_noite", False)
        if eh_noite:
            for animal in self.animais:
                animal.visivel = False

        # =====================================================================
        # 11. PONTOS DE INTERAÇÃO E GATILHOS DE HUMANIDADE (Lore & Ecos)
        # =====================================================================
        self.pontos_interacao = [
            {
                "id": "estatua_herois",
                "rect": pygame.Rect(940, 480, 360, 140),
                "prompt_x": 1120,
                "prompt_y": 465,
                "acao_texto": "para Examinar Monumento",
                "dialogo": [
                    {
                        "autor": "Narrador",
                        "texto": "O monumento de pedra retrata a antiga companhia de seis heróis lendários. No centro-direita, uma maga élfica ergue um cajado com um cristal azul esculpido com fidelidade impressionante."
                    },
                    {
                        "autor": "Narrador",
                        "texto": "Ao lado do guerreiro de manto pesado, há uma inscrição desgastada pelo musgo: 'Àqueles que seguraram o céu quando a primeira fenda se abriu'."
                    }
                ]
            },
            {
                "id": "quadro_avisos_vila",
                "rect": pygame.Rect(1235, 805, 95, 90),
                "prompt_x": 1280,
                "prompt_y": 800,
                "acao_texto": "para Ler Avisos",
                "dialogo": [
                    {
                        "autor": "Quadro de Avisos de Oakhaven",
                        "texto": "AVISO DO CONSELHO: Caravanas para o Desfiladeiro Norte estão suspensas devido a tremores vulcânicos e batedores abissais na Orla Norte. — Guardião Doran & Ancião Aldous."
                    }
                ]
            },
            {
                "id": "canteiro_gengibre_elara",
                "rect": pygame.Rect(320, 565, 80, 55),
                "prompt_x": 360,
                "prompt_y": 555,
                "acao_texto": "para Sentir o Aroma das Ervas",
                "dialogo": [
                    {
                        "autor": "Narrador",
                        "texto": "O perfume suave de folhas de chá e gengibre fresco sobe do canteiro de Elara, trazendo uma sensação acolhedora de calma ao ambiente."
                    }
                ]
            },
            {
                "id": "bancada_ferramentas_torvald",
                "rect": pygame.Rect(1740, 565, 80, 55),
                "prompt_x": 1780,
                "prompt_y": 555,
                "acao_texto": "para Examinar Bancada da Forja",
                "dialogo": [
                    {
                        "autor": "Narrador",
                        "texto": "Pedras de amolar, óleo de têmpera e tiras de couro repousam organizadas sobre a bancada pesada do Ferreiro Torvald."
                    }
                ]
            }
        ]
        if not getattr(self.game, "pedra_torvald_quebrada", False):
            self.pontos_interacao.insert(0, {
                "id": "rocha_minerio_torvald",
                "rect": pygame.Rect(1815, 635, 105, 90),
                "prompt_x": 1868,
                "prompt_y": 630,
                "acao_texto": "para Quebrar Rocha de Minério",
                "dialogo": [
                    {
                        "autor": "Narrador",
                        "texto": "Uma grande Rocha de Minério Bruto trazida das encostas pelo Ferreiro Torvald. A casca rochosa brilha com veios metálicos no interior."
                    }
                ]
            })

    @staticmethod
    def _gerar_sprite_erva_lunar():
        """Cria uma sprite pixel-art luminosa para a Erva de Orvalho Lunar."""
        surf = pygame.Surface((28, 28), pygame.SRCALPHA)
        pygame.draw.circle(surf, (80, 210, 190, 75), (14, 14), 13)
        pygame.draw.polygon(surf, (45, 165, 130), [(14, 4), (9, 20), (14, 24), (19, 20)])
        pygame.draw.polygon(surf, (130, 245, 215), [(14, 6), (11, 18), (14, 21), (17, 18)])
        pygame.draw.polygon(surf, (70, 195, 160), [(6, 12), (12, 22), (14, 17)])
        pygame.draw.polygon(surf, (70, 195, 160), [(22, 12), (16, 22), (14, 17)])
        pygame.draw.circle(surf, (220, 255, 250), (14, 8), 2)
        return surf

    def atualizar(self, dt=0.016):
        """Atualiza chamas da forja, cintilação da fonte, NPCs e fauna (Patusco + Pássaros)."""
        eh_noite = getattr(self.game, "oakhaven_noite", False)

        pos_halia = None
        if hasattr(self.game, "halia") and self.game.halia:
            pos_halia = (
                self.game.halia.x + self.game.halia.largura * 0.5,
                self.game.halia.y + self.game.halia.altura * 0.5
            )

        for foco in self.focos_fogo:
            foco.atualizar(dt)

        for animal in self.animais:
            if eh_noite:
                animal.visivel = False
            else:
                # Durante o dia, restaura a visibilidade (caso não seja pássaro em trânsito fora da tela)
                if not animal.visivel and getattr(animal, "estado_atual", "") != "fora_da_tela":
                    animal.visivel = True
                animal.atualizar(dt, pos_jogador=pos_halia)

        for npc in self.npcs:
            if pos_halia:
                npc.virado_direita = (pos_halia[0] >= npc.x)

        # Partículas de água na Fonte Central
        self.timer_fonte += dt
        if self.timer_fonte >= 0.08:
            self.timer_fonte = 0.0
            self.particulas_fonte.append({
                "x": 1117 + random.uniform(-34, 34),
                "y": 775 + random.uniform(-12, 14),
                "vy": random.uniform(-18.0, -6.0),
                "vida": random.uniform(0.35, 0.75),
                "vida_max": 0.75,
                "raio": random.uniform(1.5, 3.0)
            })
        vivas = []
        for p in self.particulas_fonte:
            p["y"] += p["vy"] * dt
            p["vida"] -= dt
            if p["vida"] > 0:
                vivas.append(p)
        self.particulas_fonte = vivas

        # Fumaça da Chaminé da Forja de Torvald (origem exata no topo da chaminé: x=1919, y=419)
        self.timer_chamine += dt
        if self.timer_chamine >= 0.10:
            self.timer_chamine = 0.0
            self.particulas_chamine.append({
                "x": 1919.0 + random.uniform(-3.5, 3.5),
                "y": 419.0 + random.uniform(-1.0, 1.0),
                "vx": random.uniform(3.5, 8.0),
                "vy": random.uniform(-25.0, -16.0),
                "vida": random.uniform(1.8, 2.5),
                "vida_max": 2.5,
                "raio": random.uniform(2.6, 3.8),
                "alpha": random.uniform(110, 160)
            })
        vivas_chamine = []
        for p in self.particulas_chamine:
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            p["raio"] += 3.2 * dt
            p["vida"] -= dt
            if p["vida"] > 0:
                vivas_chamine.append(p)
        self.particulas_chamine = vivas_chamine

    def desenhar_camada_inferior(self, tela, area_visivel=None):
        """Renderiza o terreno pré-renderizado de Oakhaven e itens brilhantes no solo, otimizado para área visível."""
        if self.chao_completo:
            if area_visivel:
                tela.blit(self.chao_completo, area_visivel.topleft, area_visivel)
            else:
                tela.blit(self.chao_completo, (0, 0))

        # Cintilação ao redor das Ervas de Orvalho Lunar ainda não coletadas
        pulso = (math.sin(pygame.time.get_ticks() * 0.006) + 1.0) * 0.5
        for item in self.itens_no_chao:
            if area_visivel and not area_visivel.colliderect(item.rect):
                continue
            r_aura = int(16 + pulso * 5)
            aura = pygame.Surface((r_aura * 2, r_aura * 2), pygame.SRCALPHA)
            pygame.draw.circle(aura, (110, 235, 210, int(55 + pulso * 50)), (r_aura, r_aura), r_aura)
            tela.blit(aura, (item.x + item.largura // 2 - r_aura, item.y + item.altura // 2 - r_aura))
            item.desenhar(tela)

    def _obter_superficie_noite(self):
        """Cache da superfície de iluminação noturna (2240x1480) gerada uma única vez."""
        if self._noite_surf_cache is None:
            surf = pygame.Surface((self.largura_mundo, self.altura_mundo), pygame.SRCALPHA)
            surf.fill((10, 16, 38, 140))
            pontos_luz = [
                (802, 465, 95), (1422, 465, 95), (802, 830, 95),
                (1422, 830, 95), (1012, 270, 95), (1212, 270, 95),
                (1919, 552, 100), (415, 260, 110), (480, 535, 105),
                (1650, 535, 105), (1117, 765, 95)
            ]
            for lx, ly, raio in pontos_luz:
                for frac, cor_rgba in [
                    (1.00, (16, 20, 40, 122)),
                    (0.82, (22, 24, 42, 104)),
                    (0.64, (30, 28, 42, 86)),
                    (0.46, (38, 32, 40, 68)),
                    (0.28, (46, 36, 38, 52)),
                    (0.12, (56, 44, 36, 36)),
                ]:
                    pygame.draw.circle(surf, cor_rgba, (lx, ly), int(raio * frac))
            self._noite_surf_cache = surf
        return self._noite_surf_cache

    def desenhar_mundo_ysort(self, tela, entidades_dinamicas=None, area_visivel=None):
        """
        Renderiza todas as construções, props, focos de fogo, NPCs, Halia, inimigos e animais com Y-Sort 2.5D,
        aplicando frustum culling da câmera para garantir 60+ FPS cravados e camadas perfeitas sem sobreposição indevida.
        """
        qm = getattr(self.game, "missoes", None) or getattr(self.game, "quest_manager", None)

        # 0. Iluminação de solo (glow) das chamas antes de desenhar corpos sólidos
        for foco in self.focos_fogo:
            if area_visivel is None or area_visivel.collidepoint(foco.x, foco.y):
                foco.desenhar_glow(tela)

        fila_render = []

        # 1. Estruturas e Props do Cenário com Frustum Culling
        for est in self.estruturas_ysort:
            if area_visivel is None or area_visivel.colliderect(est.get("rect", pygame.Rect(est["x"], est["y"], 64, 64))):
                fila_render.append((est["y_sort"], "estrutura", est))

        # 2. Focos de Fogo integrados ao Y-Sort (ordenados fielmente pela base de contato no solo)
        for foco in self.focos_fogo:
            if area_visivel is None or area_visivel.collidepoint(foco.x, foco.y):
                fila_render.append((int(foco.y), "fogo", foco))

        # 3. NPCs da Vila com Frustum Culling
        for npc in self.npcs:
            r_npc = pygame.Rect(int(npc.x), int(npc.y), npc.largura, npc.altura)
            if area_visivel is None or area_visivel.colliderect(r_npc):
                fila_render.append((int(npc.y + npc.altura), "npc", npc))

        # 4. Animais (Patusco no tufo de grama e Pássaros no solo)
        # Durante a noite, a fauna está dormindo e não participa do Y-sort nem voa
        eh_noite = getattr(self.game, "oakhaven_noite", False)
        animais_voando = []
        if not eh_noite:
            for animal in self.animais:
                if not getattr(animal, "visivel", True):
                    continue
                if getattr(animal, "altitude", 0.0) > 18.0:
                    animais_voando.append(animal)
                else:
                    r_anim = pygame.Rect(int(animal.x - 20), int(animal.y - 20), 40, 40)
                    if area_visivel is None or area_visivel.colliderect(r_anim):
                        fila_render.append((int(animal.y + animal.altura * 0.5), "animal", animal))

        # 5. Entidades Dinâmicas (Halia, Inimigos em Cena)
        if entidades_dinamicas:
            for ent in entidades_dinamicas:
                if ent is not None:
                    fila_render.append((int(ent.y + getattr(ent, "altura", 36)), "entidade", ent))

        # 6. Partículas de água na Fonte Central (ancoradas no espelho da bacia em y=780)
        if area_visivel is None or area_visivel.colliderect(pygame.Rect(1020, 680, 160, 160)):
            fila_render.append((780, "fonte_agua", self.particulas_fonte))

        fila_render.sort(key=lambda item: item[0])

        for _, tipo, obj in fila_render:
            if tipo == "estrutura":
                sp = obj["sprite"]
                ox, oy = obj["x"], obj["y"]
                s_surf = obj.get("sombra_surf")
                if s_surf:
                    tela.blit(s_surf, (ox + int(obj["sw"] * 0.07), oy + obj["sh"] - 12))
                tela.blit(sp, (ox, oy))
            elif tipo == "fogo":
                obj.desenhar_sprite(tela)
                obj.desenhar_particulas(tela)
            elif tipo == "npc":
                obj.desenhar(tela, quest_manager=qm)
            elif tipo == "animal":
                obj.desenhar(tela)
            elif tipo == "entidade":
                obj.desenhar(tela)
            elif tipo == "fonte_agua":
                for p in obj:
                    r = max(1, int(p["raio"]))
                    pygame.draw.circle(tela, (165, 225, 255), (int(p["x"]), int(p["y"])), r)

        # Fumaça da Chaminé da Forja de Torvald (topo em x=1919, y=419 subindo até y~310)
        if area_visivel is None or area_visivel.colliderect(pygame.Rect(1895, 310, 100, 130)):
            for p in self.particulas_chamine:
                frac = max(0.0, p["vida"] / p["vida_max"])
                alpha = int(p["alpha"] * (frac ** 1.2))
                r = int(p["raio"])
                if r > 0 and alpha > 0:
                    surf_fum = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                    cor_fum = (155, 162, 172, alpha)
                    pygame.draw.circle(surf_fum, cor_fum, (r, r), r)
                    tela.blit(surf_fum, (int(p["x"] - r), int(p["y"] - r)))

        # Pássaros em voo alto passam por cima dos telhados (apenas de dia)
        if not eh_noite:
            for ave in animais_voando:
                if getattr(ave, "visivel", True):
                    ave.desenhar(tela)

        # Iluminação Noturna de Oakhaven (reutilização de superfície cacheadas sem re-alocação)
        if getattr(self.game, "oakhaven_noite", False):
            if area_visivel:
                tela.blit(self._obter_superficie_noite(), area_visivel.topleft, area_visivel)
            else:
                tela.blit(self._obter_superficie_noite(), (0, 0))

    def desenhar_props(self, tela):
        """Compatibilidade caso desenhar() padrão seja chamado sem entidades externas."""
        self.desenhar_mundo_ysort(tela, entidades_dinamicas=[])


class MapaOakhavenDestruida(MapaOakhaven):
    """
    Cenário de Oakhaven Destruída / Em Chamas na manhã seguinte, quando Halia acorda
    com o ataque de Ignis'Vahr, o Dragão Vermelho Ancestral, antes de persegui-lo até o Ninho do Dragão.
    Utiliza os assets reais de ruínas, telhados incendiados e monumentos destruídos de assets/cenario/vila.
    """

    def __init__(self, game, largura_tela, altura_tela):
        super().__init__(game, largura_tela, altura_tela)
        self.nome = "OAKHAVEN_DESTRUIDA"
        self._brasa_surf_cache = None

    def _obter_superficie_brasa(self):
        """Cache da camada atmosférica de fumaça e brasas sobre a vila atacada."""
        if self._brasa_surf_cache is None:
            surf = pygame.Surface((self.largura_mundo, self.altura_mundo), pygame.SRCALPHA)
            surf.fill((65, 22, 12, 48))
            self._brasa_surf_cache = surf
        return self._brasa_surf_cache

    def carregar_recursos(self):
        super().carregar_recursos()
        p_vila = "assets/cenario/vila"

        def _carregar_escala(caminho, escala):
            img = ResourceManager.carregar_imagem(caminho)
            if not img:
                return None
            nw = max(1, int(img.get_width() * escala))
            nh = max(1, int(img.get_height() * escala))
            return ResourceManager.carregar_imagem(caminho, (nw, nh))

        # Substitui o Monumento, a Fonte, Casas, Lojas, Barracas e Props pelas versões danificadas/em ruínas
        self.spr_monumento = _carregar_escala(f"{p_vila}/Props/Monumentos/monumento_herois_danificado.png", 0.28) or self.spr_monumento
        self.spr_fonte = _carregar_escala(f"{p_vila}/Props/Fontes/fonte_pedra_danificada.png", 0.32) or self.spr_fonte

        ruina_loja_14 = _carregar_escala(f"{p_vila}/Lojas/Frente/loja_14_ruina_telhado_danificado.png", 0.42)
        ruina_loja_15 = _carregar_escala(f"{p_vila}/Lojas/Frente/loja_15_ruina_incendio_telhado.png", 0.42)
        ruina_loja_16 = _carregar_escala(f"{p_vila}/Lojas/Frente/loja_16_ruina_grande_desabada.png", 0.42)
        ruina_loja_17 = _carregar_escala(f"{p_vila}/Lojas/Frente/loja_17_ruina_chamine_escombros.png", 0.42)

        if ruina_loja_16:
            self.sprites_lojas["taverna_frente"] = ruina_loja_16
        if ruina_loja_14:
            self.sprites_lojas["livraria_frente"] = ruina_loja_14
            self.sprites_lojas["padaria_frente"] = ruina_loja_14
        if ruina_loja_15:
            self.sprites_lojas["magia_frente"] = ruina_loja_15
            self.sprites_lojas["emporio_frente"] = ruina_loja_15
        if ruina_loja_17:
            self.sprites_lojas["floricultura_frente"] = ruina_loja_17
            self.sprites_lojas["carpintaria_frente"] = ruina_loja_17

        ruina_c1_12 = _carregar_escala(f"{p_vila}/Casas/Conjunto_1/Frente/casa_12_ruina_vigas_desabadas.png", 0.42)
        ruina_c1_13 = _carregar_escala(f"{p_vila}/Casas/Conjunto_1/Frente/casa_13_ruina_estrutura_queimada.png", 0.42)
        ruina_c1_14 = _carregar_escala(f"{p_vila}/Casas/Conjunto_1/Frente/casa_14_ruina_chamine_escombros.png", 0.42)
        ruina_c2_12 = _carregar_escala(f"{p_vila}/Casas/Conjunto_2/Frente/casa_12_lateral_destruida.png", 0.42)

        if ruina_c1_12:
            self.sprites_casas["c1_f01"] = ruina_c1_12
            self.sprites_casas["c1_f03"] = ruina_c1_12
        if ruina_c1_13:
            self.sprites_casas["c1_f02"] = ruina_c1_13
            # A Casa de Hóspedes (c1_f05) onde Halia dorme permanece com estrutura em pé para permitir sua saída
            self.sprites_casas["c2_f01_jardim"] = ruina_c1_13
        if ruina_c1_14:
            self.sprites_casas["c1_f07"] = ruina_c1_14
            self.sprites_casas["c2_f04_relogio"] = ruina_c1_14
        if ruina_c2_12:
            self.sprites_casas["c2_f03_hera"] = ruina_c2_12
            self.sprites_casas["c2_f06_dois_andares"] = ruina_c2_12

        ruina_b14 = _carregar_escala(f"{p_vila}/Barracas/Frente/barraca_14_ruina_saqueada.png", 0.34)
        ruina_b15 = _carregar_escala(f"{p_vila}/Barracas/Frente/barraca_15_ruina_queimada.png", 0.34)
        ruina_b16 = _carregar_escala(f"{p_vila}/Barracas/Frente/barraca_16_ruina_pedra_destruida.png", 0.34)
        if ruina_b14:
            self.sprites_barracas["b_hortifruti"] = ruina_b14
        if ruina_b15:
            self.sprites_barracas["b_flores"] = ruina_b15
            self.sprites_barracas["b_ferraria"] = ruina_b15
        if ruina_b16:
            self.sprites_barracas["b_alquimia"] = ruina_b16
            self.sprites_barracas["b_aventureiro"] = ruina_b16

        carroca_dest = _carregar_escala(f"{p_vila}/Props/Cargas_e_Transporte/carroca_destruida.png", 0.30)
        banco_queb = _carregar_escala(f"{p_vila}/Props/Bancos/banco_madeira_quebrado.png", 0.25)
        estandarte_rasg = _carregar_escala(f"{p_vila}/Props/Placas_e_Estandartes/estandarte_rasgado.png", 0.28)
        if carroca_dest:
            self.sprites_props["carroca"] = carroca_dest
        if banco_queb:
            self.sprites_props["banco_madeira"] = banco_queb
        if estandarte_rasg:
            self.sprites_props["estandarte"] = estandarte_rasg

    def inicializar_cenario(self):
        super().inicializar_cenario()
        # Na vila destruída pelas chamas do dragão, a fauna não está presente
        for animal in self.animais:
            animal.visivel = False

        # 6.2 Posicionamento dos NPCs Durante e Após o Ataque Noturno à Vila:
        # Durante o ataque noturno / desespero: Ferreiro, Ancião e Curandeira (Elara) não aparecem na vila.
        # Após Halia sair do desespero (desespero_superado = True ou dragao_derrotado = True):
        # Apenas Curandeira (Elara) reunida junto ao Ancião (Aldous), mantendo o Ferreiro fora de cena.
        desespero_superado = getattr(self.game, "desespero_superado", False) or getattr(self.game, "dragao_derrotado", False)
        
        # Remove hitboxes dos NPCs anteriores criados no super()
        hitboxes_npcs = [pygame.Rect(int(npc.x), int(npc.y), npc.largura, npc.altura) for npc in self.npcs]
        self.hitboxes = [h for h in self.hitboxes if h not in hitboxes_npcs]

        if not desespero_superado:
            # Durante o ataque: todos os NPCs estão escondidos/abrigados fora do alcance das chamas
            self.npcs = []
        else:
            # Após o combate contra o dragão: Ancião Aldous, Curandeira Elara e Guarda Doran reunidos na praça acolhendo Halia
            self.npcs = [
                NPC(
                    nome="Ancião Aldous",
                    x=1075,
                    y=635,
                    npc_id="anciao_aldous",
                    dialogo_id="hub_aldous_destruida",
                    tem_loja=False,
                    arquetipo="anciao"
                ),
                NPC(
                    nome="Curandeira Elara",
                    x=1125,
                    y=635,
                    npc_id="curandeira_elara",
                    dialogo_id="hub_elara_destruida",
                    tem_loja=False,
                    arquetipo="curandeira"
                ),
                NPC(
                    nome="Guarda Doran",
                    x=1170,
                    y=635,
                    npc_id="guarda_doran",
                    dialogo_id="hub_doran_destruida",
                    tem_loja=False,
                    arquetipo="guarda"
                ),
            ]
            for npc in self.npcs:
                self.hitboxes.append(pygame.Rect(int(npc.x), int(npc.y), npc.largura, npc.altura))

        # Múltiplos focos de incêndio espalhados pelas ruínas de Oakhaven após o ataque do Dragão
        self.focos_fogo = [
            ChamaIndependente(390, 290, tipo="grande", escala=1.1, glow_base=45),
            ChamaIndependente(660, 285, tipo="media", escala=1.0, glow_base=38),
            ChamaIndependente(240, 560, tipo="chao_larga", escala=1.0, glow_base=40),
            ChamaIndependente(650, 565, tipo="media", escala=0.95, glow_base=36),
            ChamaIndependente(1010, 560, tipo="chao_pequena", escala=0.9, glow_base=30),
            ChamaIndependente(1220, 555, tipo="chao_pequena", escala=0.9, glow_base=30),
            ChamaIndependente(1520, 280, tipo="grande", escala=1.05, glow_base=42),
            ChamaIndependente(1760, 285, tipo="chao_larga", escala=1.0, glow_base=38),
            ChamaIndependente(1919, 557, tipo="chao_larga", escala=1.0, glow_base=38),
            ChamaIndependente(1540, 815, tipo="media", escala=0.95, glow_base=35),
            ChamaIndependente(410, 815, tipo="media", escala=0.95, glow_base=35),
            ChamaIndependente(640, 1085, tipo="grande", escala=1.05, glow_base=42),
            ChamaIndependente(1310, 1085, tipo="chao_larga", escala=1.0, glow_base=38),
        ]

    def desenhar_mundo_ysort(self, tela, entidades_dinamicas=None, area_visivel=None):
        super().desenhar_mundo_ysort(tela, entidades_dinamicas=entidades_dinamicas, area_visivel=area_visivel)
        # Atmosfera de fumaça e brasa sobre a vila atacada pelo Dragão (superfície cacheada)
        if area_visivel:
            tela.blit(self._obter_superficie_brasa(), area_visivel.topleft, area_visivel)
        else:
            tela.blit(self._obter_superficie_brasa(), (0, 0))


class MapaNinhoDragao(CenarioBase):
    """
    Cenário do Ninho do Dragão ('NINHO_DRAGAO', 1280 x 720).
    Covil vulcânico e rochoso nas montanhas ao norte de Oakhaven, para onde Halia segue
    após o ataque à vila para enfrentar Ignis'Vahr, o Dragão Vermelho Ancestral.
    Suporta atmosfera noturna de combate e alvorada triunfal matinal após a vitória.
    """

    LARGURA_MUNDO = 1280
    ALTURA_MUNDO = 720

    def __init__(self, game, largura_tela, altura_tela):
        self.estruturas_ysort = []
        self.focos_fogo = []
        self.particulas_cinzas = []
        self._noite_surf_cache = None
        self._amanhecer_surf_cache = None
        self.ninho_amanhecer = False
        self.dragao_derrotado = False
        self.fumaca_corpo_dragao = []
        self.spr_dragao_derrotado = None
        super().__init__(
            game,
            largura_tela,
            altura_tela,
            nome="NINHO_DRAGAO",
            largura_mundo=self.LARGURA_MUNDO,
            altura_mundo=self.ALTURA_MUNDO
        )
        self.inicializar_cenario()

    def carregar_recursos(self):
        p_rocks = "assets/cenario/vegetacao_pedras_separadas/Rocks"
        p_ilum = "assets/cenario/vila/Props/Iluminacao_e_Postes"
        p_cristais = "assets/novos assets/craftpix-net-106469-top-down-crystals-pixel-art/PNG/Assets"
        p_ruinas = "assets/novos assets/craftpix-net-934618-free-top-down-ruins-pixel-art/PNG/Assets"

        def _carregar_escala(caminho, escala):
            img = ResourceManager.carregar_imagem(caminho)
            if not img:
                return None
            nw = max(1, int(img.get_width() * escala))
            nh = max(1, int(img.get_height() * escala))
            return ResourceManager.carregar_imagem(caminho, (nw, nh))

        self.sprites_rochas = {
            "penhasco_1": _carregar_escala(f"{p_rocks}/Rocks_001.png", 2.6),
            "penhasco_2": _carregar_escala(f"{p_rocks}/Rocks_002.png", 2.6),
            "penhasco_3": _carregar_escala(f"{p_rocks}/Rocks_003.png", 2.6),
            "penhasco_4": _carregar_escala(f"{p_rocks}/Rocks_004.png", 2.6),
            "penhasco_5": _carregar_escala(f"{p_rocks}/Rocks_005.png", 2.9),
            "penhasco_6": _carregar_escala(f"{p_rocks}/Rocks_006.png", 2.6),
            "penhasco_53": _carregar_escala(f"{p_rocks}/Rocks_053.png", 3.0),
            "penhasco_54": _carregar_escala(f"{p_rocks}/Rocks_054.png", 2.8),
            "escombro_1": _carregar_escala(f"{p_rocks}/Rocks_018.png", 2.0),
            "escombro_2": _carregar_escala(f"{p_rocks}/Rocks_024.png", 2.0),
            "pilar_pedra": _carregar_escala(f"{p_ilum}/pilar_pedra.png", 0.65),
            "cristal_magma_grande": _carregar_escala(f"{p_cristais}/Dark_red_ crystal1.png", 1.8) or _carregar_escala(f"{p_rocks}/Rocks_103.png", 1.8),
            "cristal_magma_medio": _carregar_escala(f"{p_cristais}/Red_crystal1.png", 1.6) or _carregar_escala(f"{p_rocks}/Rocks_103.png", 1.6),
            "cristal_obsidiana": _carregar_escala(f"{p_cristais}/Black_crystal1.png", 1.8) or _carregar_escala(f"{p_rocks}/Rocks_053.png", 1.8),
            "altar_ruina_grande": _carregar_escala(f"{p_ruinas}/Brown-gray_ruins1.png", 1.25) or _carregar_escala(f"{p_rocks}/Rocks_053.png", 1.25),
        }

        # Carrega a sprite colossal da carcaça do dragão derrotado (ampliada para 2.2x para imponência colossal)
        self.spr_dragao_derrotado = ResourceManager.carregar_imagem(
            "inimigos/dragao_vermelho/dead/dragao_vermelho_dead_03.png",
            (int(202 * 2.2), int(37 * 2.2))
        )
        self.chao_completo = self._construir_superficie_terreno()

    def _construir_superficie_terreno(self):
        w, h = self.largura_mundo, self.altura_mundo
        cols = w // 32
        rows = (h // 32) + 1
        grade = [[2 for _ in range(cols)] for _ in range(rows)]

        def _marcar_rect(gx1, gy1, gx2, gy2, tipo):
            for gy in range(max(0, gy1), min(rows, gy2 + 1)):
                for gx in range(max(0, gx1), min(cols, gx2 + 1)):
                    grade[gy][gx] = tipo

        _marcar_rect(6, 2, 33, 20, 3)
        _marcar_rect(13, 14, 26, 22, 1)

        tiles = _carregar_tiles_terreno()
        surf_grade = _renderizar_grade_autotile(w, rows * 32, grade, tiles, seed=7701)
        surf = pygame.Surface((w, h))
        surf.blit(surf_grade, (0, 0), pygame.Rect(0, 0, w, h))

        # Platô central vulcânico do ninho (terreno de rocha escura, basalto e fuligem)
        plato_surf = pygame.Surface((640, 290), pygame.SRCALPHA)
        pygame.draw.ellipse(plato_surf, (18, 10, 12, 195), (0, 0, 640, 290))
        pygame.draw.ellipse(plato_surf, (28, 14, 16, 165), (35, 20, 570, 250))
        pygame.draw.ellipse(plato_surf, (42, 18, 20, 130), (75, 45, 490, 200))
        surf.blit(plato_surf, (320, 95))

        # Fendas vulcânicas e veios de magma incandescente na cratera central
        veios_magma = [
            [(440, 240), (490, 265), (550, 255), (620, 295), (690, 280), (750, 315), (810, 305)],
            [(540, 230), (610, 205), (670, 230), (740, 215), (820, 240)],
            [(390, 310), (450, 345), (510, 335), (580, 375), (650, 360)],
            [(660, 325), (720, 365), (790, 345), (860, 375), (930, 355)],
            [(480, 175), (540, 195), (610, 175), (680, 190), (750, 175)],
            [(360, 260), (410, 285), (460, 275)],
            [(830, 260), (880, 285), (940, 275)],
            [(320, 200), (370, 220), (410, 210)],
            [(870, 205), (920, 225), (960, 210)],
        ]
        for veio in veios_magma:
            pygame.draw.lines(surf, (160, 25, 12), False, veio, width=14)
            pygame.draw.lines(surf, (220, 55, 18), False, veio, width=8)
            pygame.draw.lines(surf, (255, 140, 30), False, veio, width=4)
            pygame.draw.lines(surf, (255, 245, 160), False, veio, width=2)

        tint = pygame.Surface((w, h), pygame.SRCALPHA)
        tint.fill((42, 15, 20, 105))
        surf.blit(tint, (0, 0))
        return surf

    def inicializar_cenario(self):
        self.hitboxes = []
        self.itens_no_chao = []
        self.estruturas_ysort = []
        self.npcs = []
        self.animais = []
        self.pontos_interacao = []
        w, h = self.largura_mundo, self.altura_mundo

        self.hitboxes.extend([
            pygame.Rect(0, 0, w, 95),
            pygame.Rect(0, 0, 105, h),
            pygame.Rect(w - 105, 0, 105, h),
            pygame.Rect(0, h - 35, w, 35),
        ])

        if getattr(self, "dragao_derrotado", False):
            # Hitbox física sólida da carcaça colossal de Ignis'Vahr (impede Halia de atravessar a massa do dragão)
            self.hitboxes.append(pygame.Rect(430, 230, 420, 60))

        def _add_estrutura(sprite, x, y, hitbox_rel=None, sombra=True, y_sort_custom=None):
            if not sprite:
                return
            sw, sh = sprite.get_size()
            if hitbox_rel is None:
                hb = pygame.Rect(int(x + sw * 0.15), int(y + sh * 0.6), int(sw * 0.7), int(sh * 0.35))
            else:
                rx, ry, rw, rh = hitbox_rel
                hb = pygame.Rect(int(x + rx), int(y + ry), int(rw), int(rh))
            if hb.width > 0 and hb.height > 0:
                self.hitboxes.append(hb)

            sombra_surf = None
            if sombra:
                sombra_larg = int(sw * 0.86)
                sombra_surf = pygame.Surface((sombra_larg, 18), pygame.SRCALPHA)
                pygame.draw.ellipse(sombra_surf, (10, 8, 8, 90), (0, 0, sombra_larg, 18))

            calc_ysort = y_sort_custom if y_sort_custom is not None else max(int(hb.bottom), int(y + sh - 4))
            self.estruturas_ysort.append({
                "sprite": sprite,
                "x": int(x),
                "y": int(y),
                "y_sort": calc_ysort,
                "sombra": sombra,
                "sombra_surf": sombra_surf,
                "sw": sw,
                "sh": sh,
                "rect": pygame.Rect(int(x), int(y), sw, sh)
            })

        penhascos = [
            (25, 10, "penhasco_5"), (150, 5, "penhasco_1"), (300, 0, "penhasco_53"),
            (460, 0, "penhasco_3"), (680, 0, "penhasco_4"),
            (840, 0, "penhasco_54"), (990, 5, "penhasco_2"), (1120, 10, "penhasco_6"),
            (20, 160, "penhasco_53"), (30, 320, "penhasco_1"), (20, 480, "penhasco_5"),
            (1125, 160, "penhasco_54"), (1115, 320, "penhasco_2"), (1125, 480, "penhasco_6"),
            (570, 40, "altar_ruina_grande"),
            (370, 65, "cristal_obsidiana"), (870, 65, "cristal_obsidiana"),
            (240, 140, "pilar_pedra"), (1000, 140, "pilar_pedra"),
            (180, 340, "pilar_pedra"), (1060, 340, "pilar_pedra"),
            (320, 180, "cristal_magma_grande"), (920, 180, "cristal_magma_grande"),
            (170, 470, "cristal_magma_medio"), (1060, 470, "cristal_magma_medio"),
            (280, 360, "cristal_obsidiana"), (950, 360, "cristal_obsidiana"),
            (230, 490, "escombro_1"), (970, 490, "escombro_2"),
            (490, 525, "escombro_1"), (770, 525, "escombro_2"),
        ]
        for rx, ry, k_r in penhascos:
            _add_estrutura(self.sprites_rochas.get(k_r), rx, ry)

        self.focos_fogo = [
            ChamaIndependente(255, 165, tipo="braseiro", cor="laranja", escala=1.15, glow_base=50),
            ChamaIndependente(1015, 165, tipo="braseiro", cor="laranja", escala=1.15, glow_base=50),
            ChamaIndependente(195, 365, tipo="braseiro", cor="laranja", escala=1.05, glow_base=46),
            ChamaIndependente(1075, 365, tipo="braseiro", cor="laranja", escala=1.05, glow_base=46),
            ChamaIndependente(330, 230, tipo="grande", cor="laranja", escala=1.15, glow_base=48),
            ChamaIndependente(930, 230, tipo="grande", cor="laranja", escala=1.15, glow_base=48),
            ChamaIndependente(450, 130, tipo="media", cor="laranja", escala=1.05, glow_base=42),
            ChamaIndependente(810, 130, tipo="media", cor="laranja", escala=1.05, glow_base=42),
            ChamaIndependente(260, 480, tipo="chao_larga", cor="laranja", escala=1.05, glow_base=40),
            ChamaIndependente(990, 480, tipo="chao_larga", cor="laranja", escala=1.05, glow_base=40),
            ChamaIndependente(460, 510, tipo="chao_pequena", cor="laranja", escala=0.95, glow_base=34),
            ChamaIndependente(800, 510, tipo="chao_pequena", cor="laranja", escala=0.95, glow_base=34),
            ChamaIndependente(550, 195, tipo="chao_larga", cor="laranja", escala=1.1, glow_base=44),
            ChamaIndependente(710, 195, tipo="chao_larga", cor="laranja", escala=1.1, glow_base=44),
        ]

        self.particulas_cinzas = [
            {
                "x": random.randint(120, w - 120),
                "y": random.randint(80, h - 60),
                "vx": random.uniform(-18, 22),
                "vy": random.uniform(-25, -45),
                "raio": random.uniform(1.2, 2.6),
                "cor": random.choice([(255, 160, 50), (255, 90, 20), (230, 70, 20), (240, 210, 110)])
            }
            for _ in range(35)
        ]

        self.fumaca_corpo_dragao = []
        if self.dragao_derrotado:
            for _ in range(20):
                self.fumaca_corpo_dragao.append({
                    "x": 430 + random.uniform(0, 400),
                    "y": 220 + random.uniform(0, 50),
                    "vx": random.uniform(-4.0, 4.0),
                    "vy": random.uniform(-14.0, -6.0),
                    "vida": random.uniform(0.1, 2.2),
                    "vida_max": 2.2,
                    "alpha": random.randint(25, 60),
                    "raio": random.uniform(3.5, 7.5)
                })

            self.pontos_interacao = [
                {
                    "id": "corpo_dragao_derrotado",
                    "rect": pygame.Rect(390, 240, 500, 130),
                    "prompt_x": 640,
                    "prompt_y": 195,
                    "acao_texto": "para Examinar Ignis'Vahr",
                    "dialogo": "examinar_corpo_dragao"
                },
                {
                    "id": "trilha_descida_oakhaven",
                    "rect": pygame.Rect(540, 640, 200, 70),
                    "prompt_x": 640,
                    "prompt_y": 620,
                    "acao_texto": "para Descer a Oakhaven",
                    "evento": "retornar_oakhaven_vitoria"
                }
            ]

    def atualizar(self, dt=0.016):
        for foco in self.focos_fogo:
            foco.atualizar(dt)

        w, h = self.largura_mundo, self.altura_mundo
        for p in self.particulas_cinzas:
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            if p["y"] < 50:
                p["y"] = h - random.randint(40, 90)
                p["x"] = random.randint(120, w - 120)

        if getattr(self, "dragao_derrotado", False):
            for f in self.fumaca_corpo_dragao:
                f["x"] += f["vx"] * dt
                f["y"] += f["vy"] * dt
                f["vida"] -= dt
                if f["vida"] <= 0.0:
                    f["x"] = 430 + random.uniform(0, 400)
                    f["y"] = 220 + random.uniform(0, 50)
                    f["vy"] = random.uniform(-14.0, -6.0)
                    f["vx"] = random.uniform(-4.0, 4.0)
                    f["vida"] = random.uniform(1.2, 2.4)
                    f["vida_max"] = f["vida"]
                    f["alpha"] = random.randint(25, 60)
                    f["raio"] = random.uniform(3.5, 7.5)

    def desenhar_camada_inferior(self, tela, area_visivel=None):
        if self.chao_completo:
            tela.blit(self.chao_completo, (0, 0))

    def _obter_superficie_noite(self):
        if self._noite_surf_cache is None:
            surf = pygame.Surface((self.largura_mundo, self.altura_mundo), pygame.SRCALPHA)
            surf.fill((10, 14, 32, 135))
            pontos_luz_ninho = [
                (255, 165, 115), (1015, 165, 115), (195, 365, 105), (1075, 365, 105),
                (330, 230, 125), (930, 230, 125), (450, 130, 100), (810, 130, 100),
                (640, 230, 160)
            ]
            for lx, ly, raio in pontos_luz_ninho:
                for frac, cor_rgba in [
                    (1.00, (24, 18, 38, 120)),
                    (0.80, (32, 22, 40, 100)),
                    (0.60, (48, 28, 38, 80)),
                    (0.40, (70, 36, 32, 60)),
                    (0.20, (110, 50, 28, 40)),
                ]:
                    pygame.draw.circle(surf, cor_rgba, (lx, ly), int(raio * frac))
            self._noite_surf_cache = surf
        return self._noite_surf_cache

    def _obter_superficie_amanhecer(self):
        if self._amanhecer_surf_cache is None:
            w, h = self.largura_mundo, self.altura_mundo
            surf = pygame.Surface((w, h), pygame.SRCALPHA)
            for y in range(0, h, 4):
                prog = y / h
                r = int(248 * (1.0 - 0.22 * prog) + 215 * 0.22 * prog)
                g = int(200 * (1.0 - 0.32 * prog) + 165 * 0.32 * prog)
                b = int(140 * (1.0 - 0.45 * prog) + 185 * 0.45 * prog)
                alpha = int(38 + 24 * (1.0 - prog))
                pygame.draw.rect(surf, (r, g, b, alpha), (0, y, w, 4))

            feixes = [
                [(160, 0), (270, 0), (460, 720), (280, 720)],
                [(480, 0), (640, 0), (850, 720), (610, 720)],
                [(820, 0), (980, 0), (1200, 720), (970, 720)],
                [(340, 0), (440, 0), (620, 720), (490, 720)],
            ]
            for feixe in feixes:
                pygame.draw.polygon(surf, (255, 238, 185, 20), feixe)

            self._amanhecer_surf_cache = surf
        return self._amanhecer_surf_cache

    def desenhar_mundo_ysort(self, tela, entidades_dinamicas=None, area_visivel=None):
        # 1. Halo de iluminação no solo dos focos de fogo (antes dos elementos sólidos)
        for foco in self.focos_fogo:
            if area_visivel is None or area_visivel.collidepoint(foco.x, foco.y):
                foco.desenhar_glow(tela)

        fila_render = []

        # 2. Estruturas e Formações Rochosas com Frustum Culling
        for est in self.estruturas_ysort:
            if area_visivel is None or area_visivel.colliderect(est.get("rect", pygame.Rect(est["x"], est["y"], 64, 64))):
                fila_render.append((est["y_sort"], "estrutura", est))

        # 3. Focos de Fogo integrados ao Y-Sort (ordenados fielmente pela base de contato no solo)
        for foco in self.focos_fogo:
            if area_visivel is None or area_visivel.collidepoint(foco.x, foco.y):
                fila_render.append((int(foco.y), "fogo", foco))

        # 4. Entidades Dinâmicas (Halia, Dragão vivo durante o clímax, etc.)
        if entidades_dinamicas:
            for ent in entidades_dinamicas:
                if ent is not None:
                    fila_render.append((int(ent.y + getattr(ent, "altura", 36)), "entidade", ent))

        # 5. Carcaça Colossal de Ignis'Vahr estendida sobre a rocha vulcânica (Y-sort ancorado na linha de contato)
        if getattr(self, "dragao_derrotado", False) and self.spr_dragao_derrotado:
            # cx=418, cy=210, w=444, h=81 -> contato com o solo em cy + 81 = 291
            fila_render.append((291, "dragao_derrotado", {
                "x": 418,
                "y": 210,
                "sprite": self.spr_dragao_derrotado
            }))

        fila_render.sort(key=lambda item: item[0])

        for _, tipo, obj in fila_render:
            if tipo == "estrutura":
                sp = obj["sprite"]
                ox, oy = obj["x"], obj["y"]
                s_surf = obj.get("sombra_surf")
                if s_surf:
                    tela.blit(s_surf, (ox + int(obj["sw"] * 0.07), oy + obj["sh"] - 12))
                tela.blit(sp, (ox, oy))
            elif tipo == "entidade":
                obj.desenhar(tela)
            elif tipo == "fogo":
                obj.desenhar_sprite(tela)
                obj.desenhar_particulas(tela)
            elif tipo == "dragao_derrotado":
                cx, cy = obj["x"], obj["y"]
                # Sombra massiva do dragão derrotado espalhada sobre a rocha vulcânica
                sombra_corpo = pygame.Surface((450, 44), pygame.SRCALPHA)
                pygame.draw.ellipse(sombra_corpo, (14, 10, 14, 125), (0, 0, 450, 44))
                tela.blit(sombra_corpo, (cx - 3, cy + 48))
                tela.blit(obj["sprite"], (cx, cy))

                # Fumaça e fuligem subindo dos ferimentos e escamas da carcaça colossal
                for f in self.fumaca_corpo_dragao:
                    frac = max(0.0, f["vida"] / f["vida_max"])
                    alpha = int(f["alpha"] * frac)
                    r = int(f["raio"] * (1.0 + 0.4 * (1.0 - frac)))
                    if r > 0 and alpha > 0:
                        s_fum = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                        pygame.draw.circle(s_fum, (190, 195, 205, alpha), (r, r), r)
                        tela.blit(s_fum, (int(f["x"] - r), int(f["y"] - r)))

        # 6. Iluminação do Ninho: noturna escura durante o embate vs alvorada dourada ao amanhecer
        if getattr(self, "ninho_amanhecer", False):
            tela.blit(self._obter_superficie_amanhecer(), (0, 0))
        else:
            tela.blit(self._obter_superficie_noite(), (0, 0))

        # 7. Partículas de cinzas em suspensão atmosférica
        for p in self.particulas_cinzas:
            pygame.draw.circle(tela, p["cor"], (int(p["x"]), int(p["y"])), int(p["raio"]))

    def desenhar_props(self, tela):
        self.desenhar_mundo_ysort(tela, entidades_dinamicas=[])


class MapaOrlaNorte(CenarioBase):
    """
    Cenário da Orla Norte de Oakhaven (Clareira de Patrulha da Fronteira).
    Para onde o Guarda Doran conduz Halia durante a missão 'Ronda nas Fronteiras'
    para enfrentar os 2 Batedores Demoníacos longe das ruas civis da vila.
    """

    LARGURA_MUNDO = 1280
    ALTURA_MUNDO = 720

    def __init__(self, game, largura_tela, altura_tela):
        self.estruturas_ysort = []
        self.focos_fogo = []
        super().__init__(
            game,
            largura_tela,
            altura_tela,
            nome="ORLA_NORTE",
            largura_mundo=self.LARGURA_MUNDO,
            altura_mundo=self.ALTURA_MUNDO
        )
        self.inicializar_cenario()

    def carregar_recursos(self):
        p_vila = "assets/cenario/vila"
        p_t1 = "assets/cenario/arvores_separadas_tipo1"
        p_veg = "assets/cenario/vegetacao_pedras_separadas/Vegetation"
        p_arv_vila = f"{p_veg}/arvores_estilo_separado"
        p_rocks = "assets/cenario/vegetacao_pedras_separadas/Rocks"

        def _carregar_escala(caminho, escala):
            img = ResourceManager.carregar_imagem(caminho)
            if not img:
                return None
            nw = max(1, int(img.get_width() * escala))
            nh = max(1, int(img.get_height() * escala))
            return ResourceManager.carregar_imagem(caminho, (nw, nh))

        self.sprites_arvores = {
            "arv_vila_verde": _carregar_escala(f"{p_arv_vila}/arvore_verde_vila.png", 2.1),
            "arv_bolotas": _carregar_escala(f"{p_arv_vila}/arvore_folhas_bolotas.png", 2.1),
            "arv_betula": _carregar_escala(f"{p_arv_vila}/arvore_betula.png", 2.0),
            "arv_g1": ResourceManager.carregar_imagem(f"{p_t1}/Model_01_Size_05/Model_01_Size_05_01.png", (112, 168)),
            "arv_g2": ResourceManager.carregar_imagem(f"{p_t1}/Model_01_Size_05/Model_01_Size_05_02.png", (112, 168)),
        }
        self.sprites_props = {
            "pilar_pedra": _carregar_escala(f"{p_vila}/Props/Iluminacao_e_Postes/pilar_pedra.png", 0.30),
            "estandarte": _carregar_escala(f"{p_vila}/Props/Placas_e_Estandartes/estandarte_vermelho.png", 0.28),
            "rocha_g": _carregar_escala(f"{p_rocks}/Rocks_001.png", 1.8),
            "rocha_m": _carregar_escala(f"{p_rocks}/Rocks_003.png", 1.6),
        }
        self.sprites_grama_tufos = [
            sp for sp in [
                _carregar_escala(f"{p_veg}/Vegetation_037.png", 2.0),
                _carregar_escala(f"{p_veg}/Vegetation_038.png", 2.0),
                _carregar_escala(f"{p_veg}/Vegetation_039.png", 2.0),
                _carregar_escala(f"{p_veg}/Vegetation_053.png", 2.0),
                _carregar_escala(f"{p_veg}/Vegetation_066.png", 2.0),
            ] if sp is not None
        ]
        self.sprites_flores = [
            sp for sp in [
                _carregar_escala(f"{p_veg}/Vegetation_050.png", 2.0),
                _carregar_escala(f"{p_veg}/Vegetation_122.png", 2.0),
                _carregar_escala(f"{p_veg}/Vegetation_133.png", 2.0),
            ] if sp is not None
        ]

        self.chao_completo = self._construir_superficie_terreno()

    def _construir_superficie_terreno(self):
        w, h = self.largura_mundo, self.altura_mundo
        cols = w // 32       # 40
        rows = (h // 32) + 1  # 23
        grade = [[0 for _ in range(cols)] for _ in range(rows)]

        def _marcar_rect(gx1, gy1, gx2, gy2, tipo):
            for gy in range(max(0, gy1), min(rows, gy2 + 1)):
                for gx in range(max(0, gx1), min(cols, gx2 + 1)):
                    grade[gy][gx] = tipo

        # Trilha sul vinda do Portão Norte de Oakhaven + Clareira Central da Orla
        _marcar_rect(17, 13, 22, 22, 1)
        _marcar_rect(12, 6, 27, 15, 1)
        _marcar_rect(14, 5, 25, 16, 1)

        tiles = _carregar_tiles_terreno()
        surf_grade = _renderizar_grade_autotile(w, rows * 32, grade, tiles, seed=9103)
        surf = pygame.Surface((w, h))
        surf.blit(surf_grade, (0, 0), pygame.Rect(0, 0, w, h))

        # Paliçada ao sul (vista pelo lado externo do Portão Norte de Oakhaven)
        for tx in range(0, w, 28):
            if 530 <= tx <= 740:
                continue
            pygame.draw.rect(surf, (62, 42, 28), (tx, h - 54, 26, 54))
            pygame.draw.rect(surf, (92, 66, 44), (tx + 3, h - 48, 20, 44))

        rng = random.Random(9107)
        for gy in range(1, rows - 2):
            for gx in range(1, cols - 1):
                if grade[gy][gx] != 0 or rng.random() > 0.36:
                    continue
                px = gx * 32 + rng.randint(-6, 8)
                py = gy * 32 + rng.randint(-6, 8)
                if py > h - 75:
                    continue
                if rng.random() < 0.75 and self.sprites_grama_tufos:
                    surf.blit(rng.choice(self.sprites_grama_tufos), (px, py))
                elif self.sprites_flores:
                    surf.blit(rng.choice(self.sprites_flores), (px, py))

        return surf

    def inicializar_cenario(self):
        self.hitboxes = []
        self.itens_no_chao = []
        self.estruturas_ysort = []
        w, h = self.largura_mundo, self.altura_mundo

        self.hitboxes.extend([
            pygame.Rect(0, 0, w, 90),                 # Floresta densa norte
            pygame.Rect(0, 0, 95, h),                 # Floresta densa oeste
            pygame.Rect(w - 95, 0, 95, h),            # Floresta densa leste
            pygame.Rect(0, h - 56, 530, 56),          # Paliçada sul esquerda
            pygame.Rect(740, h - 56, w - 740, 56),    # Paliçada sul direita
        ])

        def _add_estrutura(sprite, x, y, hitbox_rel=None, sombra=True):
            if not sprite:
                return
            sw, sh = sprite.get_size()
            if hitbox_rel is None:
                hb = pygame.Rect(int(x + sw * 0.2), int(y + sh * 0.65), int(sw * 0.6), int(sh * 0.28))
            else:
                rx, ry, rw, rh = hitbox_rel
                hb = pygame.Rect(int(x + rx), int(y + ry), int(rw), int(rh))
            if hb.width > 0 and hb.height > 0:
                self.hitboxes.append(hb)
            self.estruturas_ysort.append({
                "sprite": sprite,
                "x": int(x),
                "y": int(y),
                "y_sort": int(hb.bottom if hb.height > 0 else y + sh),
                "sombra": sombra
            })

        # Cinturão de árvores cercando a clareira da Orla Norte
        arvores_orla = [
            (30, -20, "arv_vila_verde"), (190, -30, "arv_g1"), (350, -25, "arv_bolotas"),
            (520, -35, "arv_g2"), (710, -30, "arv_vila_verde"), (890, -25, "arv_bolotas"),
            (1060, -20, "arv_g1"),
            (20, 160, "arv_g2"), (40, 360, "arv_vila_verde"), (30, 480, "arv_betula"),
            (1110, 150, "arv_bolotas"), (1100, 340, "arv_g1"), (1120, 480, "arv_vila_verde"),
        ]
        for ax, ay, k_arv in arvores_orla:
            sp_a = self.sprites_arvores.get(k_arv)
            if sp_a:
                aw, ah = sp_a.get_size()
                _add_estrutura(sp_a, ax, ay, hitbox_rel=(aw // 2 - 18, ah - 32, 36, 26))

        _add_estrutura(self.sprites_props["pilar_pedra"], 505, h - 105, hitbox_rel=(4, 65, 16, 24))
        _add_estrutura(self.sprites_props["pilar_pedra"], 745, h - 105, hitbox_rel=(4, 65, 16, 24))
        _add_estrutura(self.sprites_props["rocha_g"], 290, 240, hitbox_rel=(8, 28, 48, 24))
        _add_estrutura(self.sprites_props["rocha_m"], 920, 290, hitbox_rel=(6, 20, 36, 20))

        # Guarda Doran acompanhando Halia na entrada da clareira
        self.npcs = [
            NPC(
                nome="Guarda Doran",
                x=485,
                y=465,
                npc_id="guarda_doran",
                dialogo_id="hub_doran",
                tem_loja=False,
                arquetipo="guarda"
            )
        ]
        for npc in self.npcs:
            self.hitboxes.append(pygame.Rect(int(npc.x), int(npc.y), npc.largura, npc.altura))

        self.animais = [
            Passaro(390, 420, direcao_inicial="direita"),
            Passaro(880, 390, direcao_inicial="esquerda"),
        ]
        if getattr(self.game, "oakhaven_noite", False):
            for animal in self.animais:
                animal.visivel = False
        self.pontos_interacao = []

    def atualizar(self, dt=0.016):
        eh_noite = getattr(self.game, "oakhaven_noite", False)
        pos_halia = None
        if hasattr(self.game, "halia") and self.game.halia:
            pos_halia = (
                self.game.halia.x + self.game.halia.largura * 0.5,
                self.game.halia.y + self.game.halia.altura * 0.5
            )
        for animal in self.animais:
            if eh_noite:
                animal.visivel = False
            else:
                if not animal.visivel and getattr(animal, "estado_atual", "") != "fora_da_tela":
                    animal.visivel = True
                animal.atualizar(dt, pos_jogador=pos_halia)
        for npc in self.npcs:
            if pos_halia:
                npc.virado_direita = (pos_halia[0] >= npc.x)

    def desenhar_camada_inferior(self, tela, area_visivel=None):
        if self.chao_completo:
            tela.blit(self.chao_completo, (0, 0))

    def desenhar_mundo_ysort(self, tela, entidades_dinamicas=None, area_visivel=None):
        qm = getattr(self.game, "missoes", None) or getattr(self.game, "quest_manager", None)
        fila_render = []
        for est in self.estruturas_ysort:
            fila_render.append((est["y_sort"], "estrutura", est))
        for npc in self.npcs:
            fila_render.append((int(npc.y + npc.altura), "npc", npc))
        eh_noite = getattr(self.game, "oakhaven_noite", False)
        animais_voando = []
        if not eh_noite:
            for animal in self.animais:
                if not getattr(animal, "visivel", True):
                    continue
                if getattr(animal, "altitude", 0.0) > 18.0:
                    animais_voando.append(animal)
                else:
                    fila_render.append((int(animal.y + animal.altura * 0.5), "animal", animal))
        if entidades_dinamicas:
            for ent in entidades_dinamicas:
                if ent is not None:
                    fila_render.append((int(ent.y + getattr(ent, "altura", 36)), "entidade", ent))

        fila_render.sort(key=lambda item: item[0])
        for _, tipo, obj in fila_render:
            if tipo == "estrutura":
                sp = obj["sprite"]
                ox, oy = obj["x"], obj["y"]
                if obj.get("sombra"):
                    sw, sh = sp.get_size()
                    sombra = pygame.Surface((int(sw * 0.86), 18), pygame.SRCALPHA)
                    pygame.draw.ellipse(sombra, (14, 18, 16, 75), (0, 0, int(sw * 0.86), 18))
                    tela.blit(sombra, (ox + int(sw * 0.07), oy + sh - 12))
                tela.blit(sp, (ox, oy))
            elif tipo == "npc":
                obj.desenhar(tela, quest_manager=qm)
            elif tipo == "animal":
                obj.desenhar(tela)
            elif tipo == "entidade":
                obj.desenhar(tela)

        if not eh_noite:
            for ave in animais_voando:
                if getattr(ave, "visivel", True):
                    ave.desenhar(tela)

    def desenhar_props(self, tela):
        self.desenhar_mundo_ysort(tela, entidades_dinamicas=[])
