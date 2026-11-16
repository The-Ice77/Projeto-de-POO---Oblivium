# src/maps/oakhaven/mapa_vila.py
import math
import random
import pygame
from src.maps.cenario_base import CenarioBase
from src.maps.oakhaven.terreno_utils import (
    _carregar_tiles_terreno,
    _renderizar_grade_autotile,
    criar_sombra_contato_estrutura,
)
from src.utils.resource_manager import ResourceManager
from src.entities.npc_factory import NPCFactory
from src.entities.animal import Passaro, Gato
from src.entities.elemento_cenario import ChamaIndependente
from src.entities.item import Item
from src.maps.oakhaven.detalhes_assinatura import preparar_detalhes, sprite_bancada, desenhar_revelacao


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
            "cerca_v": _carregar_escala(f"{p_cercas}/03_Laterais_Verticais/cerca_lateral_esq_modulo_18x16.png", 2.0),
            "cerca_craft_v": _carregar_escala(
                "assets/novos assets/craftpix-net-665131-free-fields-tileset-pixel-art-for-tower-defense/2 Objects/2 Fence/7.png",
                2.0,
            ),
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
        self.grade = grade

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
        # Inspeção visual R05: peças de 08_Cercas (~36px alt.) e Craftpix 2 Fence (~30-62px)
        # são cercas baixas de jardim/pasto; esticá-las para ~90px distorceria a silhueta.
        # Mantemos a paliçada robusta de carvalho (~84-99px) com abertura exata em x=1030..1200.
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

        # Canteiros naturais de grama alta nos recantos onde Patusco pode se esconder
        # (Todos os 5 esconderijos calibrados exclusivamente em terreno gramado puro e com interação desobstruída)
        if self.sprites_grama_tufos:
            for cx, cy in [
                (176, 240),    # Bosque Noroeste atrás da taverna
                (1360, 192),   # Bosque Nordeste perto da colina norte
                (160, 480),    # Canteiro botânico oeste
                (816, 944),    # Prado gramado do riacho sul
                (1648, 944),   # Pomar sudeste perto da forja
            ]:
                for ox, oy, idx in [
                    (-28, -10, 0), (14, -12, 1), (-32, 12, 2),
                    (18, 10, 5), (-8, 18, 6), (4, -18, 7)
                ]:
                    sp_tufo = self.sprites_grama_tufos[idx % len(self.sprites_grama_tufos)]
                    surf.blit(sp_tufo, (cx + ox, cy + oy))

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

        def _add_estrutura(
            sprite,
            x,
            y,
            hitbox_rel=None,
            sombra=True,
            y_sort_custom=None,
            id_estrutura=None,
            categoria=None,
        ):
            if not sprite:
                return None
            sw, sh = sprite.get_size()
            if hitbox_rel is None:
                # Hitbox 2.5D padrão: ocupa os 38% inferiores da construção (permitindo passar atrás do telhado!)
                hb = pygame.Rect(int(x + sw * 0.08), int(y + sh * 0.58), int(sw * 0.84), int(sh * 0.36))
            else:
                rx, ry, rw, rh = hitbox_rel
                hb = pygame.Rect(int(x + rx), int(y + ry), int(rw), int(rh))
            if hb.width > 0 and hb.height > 0:
                self.hitboxes.append(hb)

            # Pré-renderização da sombra de contato ancorada à base opaca real (zero alocações por frame)
            sombra_surf = None
            sombra_offset = (0, 0)
            if sombra:
                sombra_surf, sombra_offset = criar_sombra_contato_estrutura(sprite, cor=(14, 18, 16, 75))

            calc_ysort = y_sort_custom if y_sort_custom is not None else max(int(hb.bottom), int(y + sh - 4))
            est_dict = {
                "id": id_estrutura,
                "categoria": categoria,
                "sprite": sprite,
                "x": int(x),
                "y": int(y),
                "y_sort": calc_ysort,
                "sombra": sombra,
                "sombra_surf": sombra_surf,
                "sombra_offset": sombra_offset,
                "sw": sw,
                "sh": sh,
                "rect": pygame.Rect(int(x), int(y), sw, sh),
                "hitbox_ref": hb,
            }
            self.estruturas_ysort.append(est_dict)
            return est_dict

        self._add_estrutura_fn = _add_estrutura

        # =====================================================================
        # 1. PRAÇA CENTRAL DOS HERÓIS (Coração de Oakhaven)
        # =====================================================================
        # Monumento dos 6 Heróis (no topo norte da Praça Central)
        _add_estrutura(
            self.spr_monumento,
            935,
            455,
            hitbox_rel=(18, 82, 334, 52),
            id_estrutura="monumento_praca",
            categoria="monumento",
        )
        # Fonte de Pedra Intacta (no centro-sul da Praça Central)
        _add_estrutura(
            self.spr_fonte,
            1042,
            705,
            hitbox_rel=(20, 62, 116, 66),
            id_estrutura="fonte_praca",
            categoria="fonte",
        )

        # Bancos de pedra, postes de iluminação, quadro de avisos e vasos ao redor da Praça
        _add_estrutura(self.sprites_props["banco_pedra"], 835, 585, hitbox_rel=(6, 22, 60, 20))
        _add_estrutura(self.sprites_props["banco_pedra"], 1330, 585, hitbox_rel=(6, 22, 60, 20))
        _add_estrutura(self.sprites_props["banco_pedra"], 835, 755, hitbox_rel=(6, 22, 60, 20))
        _add_estrutura(self.sprites_props["banco_pedra"], 1330, 755, hitbox_rel=(6, 22, 60, 20))
        _add_estrutura(self.sprites_props["quadro_avisos"], 1245, 815, hitbox_rel=(10, 48, 65, 24), id_estrutura="quadro_vila")
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
        _add_estrutura(self.sprites_lojas["taverna_frente"], 310, 140, id_estrutura="loja_taverna", categoria="loja")
        _add_estrutura(self.sprites_lojas["livraria_frente"], 610, 155, id_estrutura="loja_livraria", categoria="loja")
        # Barris e banco posicionados ao lado da Taverna sem sobrepor a fachada
        _add_estrutura(self.sprites_props["barris"], 245, 285, hitbox_rel=(6, 26, 44, 24))
        _add_estrutura(
            self.sprites_props["banco_madeira"],
            535,
            295,
            hitbox_rel=(6, 20, 62, 18),
            id_estrutura="banco_taverna",
            categoria="prop",
        )

        # Botânica de Elara + Loja de Poções + Floricultura na Avenida Oeste (acima da calçada y=608)
        _add_estrutura(self.sprites_lojas["magia_frente"], 175, 430, id_estrutura="loja_magia", categoria="loja")
        _add_estrutura(self.sprites_lojas["botanica_frente"], 385, 425, id_estrutura="loja_botanica", categoria="loja")
        _add_estrutura(self.sprites_lojas["floricultura_frente"], 600, 435, id_estrutura="loja_floricultura", categoria="loja")

        # Canteiros de Ervas flanqueando a loja de Elara (deixando a porta central em x=440..530 livre!)
        _add_estrutura(self.sprites_props["canteiro_ervas"], 330, 580, hitbox_rel=(6, 18, 56, 22), id_estrutura="canteiro_elara")
        _add_estrutura(self.sprites_props["canteiro_flores"], 555, 580, hitbox_rel=(6, 18, 56, 22))

        # Barracas da Feira Botânica e Canteiros na Clareira Sudoeste
        _add_estrutura(self.sprites_barracas["b_hortifruti"], 155, 745, id_estrutura="barraca_hortifruti", categoria="barraca")
        _add_estrutura(self.sprites_barracas["b_flores"], 355, 745, id_estrutura="barraca_flores", categoria="barraca")
        _add_estrutura(self.sprites_barracas["b_alquimia"], 555, 745, id_estrutura="barraca_alquimia", categoria="barraca")
        _add_estrutura(self.sprites_props["canteiro_ervas"], 185, 915, hitbox_rel=(6, 18, 56, 22))
        _add_estrutura(self.sprites_props["canteiro_flores"], 435, 915, hitbox_rel=(6, 18, 56, 22))

        # =====================================================================
        # 3. DISTRITO NORDESTE & LESTE — PADARIA, EMPÓRIO, ARMERIA & FORJA DE TORVALD
        # =====================================================================
        # Alameda Nordeste: Padaria, Empório e Carpintaria
        _add_estrutura(self.sprites_lojas["padaria_frente"], 1435, 145, id_estrutura="loja_padaria", categoria="loja")
        _add_estrutura(self.sprites_lojas["emporio_frente"], 1690, 145, id_estrutura="loja_emporio", categoria="loja")
        _add_estrutura(self.sprites_lojas["carpintaria_frente"], 1945, 155, id_estrutura="loja_carpintaria", categoria="loja")

        # Avenida Leste: Armeria Principal + Casa da Forja de Torvald (hitbox refinada apenas na parede base)
        _add_estrutura(
            self.sprites_lojas["armeria_frente"],
            1545,
            425,
            hitbox_rel=(10, 110, 142, 48),
            id_estrutura="loja_armeria",
            categoria="loja",
        )
        _add_estrutura(
            self.sprites_casas["c2_f02_forja"],
            1800,
            420,
            hitbox_rel=(12, 104, 170, 54),
            id_estrutura="casa_forja",
            categoria="casa",
        )

        # Pátio da Forja e Barracas de Equipamentos (espaçamento amplo para fluxo suave de Halia)
        _add_estrutura(self.sprites_barracas["b_ferraria"], 1485, 750, id_estrutura="barraca_ferraria", categoria="barraca")
        _add_estrutura(self.sprites_barracas["b_aventureiro"], 1925, 750, id_estrutura="barraca_aventureiro", categoria="barraca")
        _add_estrutura(self.sprites_props["bebedouro"], 1645, 785, hitbox_rel=(6, 16, 52, 22))
        _add_estrutura(self.sprites_props["carroca"], 1755, 775, hitbox_rel=(10, 22, 76, 28), id_estrutura="carroca_forja", categoria="prop")
        _add_estrutura(self.sprites_props["barris"], 1500, 585, hitbox_rel=(4, 18, 38, 18))
        _add_estrutura(self.sprites_props["caixas_pilha"], 1745, 600, hitbox_rel=(4, 18, 44, 18))
        _add_estrutura(sprite_bancada(), 1740, 565, hitbox_rel=(6, 20, 56, 18), id_estrutura="bancada_torvald")
        _add_estrutura(self.sprites_props["lenha_org"], 2005, 575, hitbox_rel=(4, 18, 32, 18))

        # Rocha de Minério Bruto no Pátio da Forja (Missão Secundária de Torvald: missao_pedra_forja)
        pedra_quebrada = getattr(self.game, "pedra_torvald_quebrada", False)
        if not pedra_quebrada and self.spr_rocha_minerio_intacta:
            # Compõe a rocha com cristais de minério incrustados
            sp_rocha = self.spr_rocha_minerio_intacta.copy()
            if self.spr_cristal_minerio:
                sp_rocha.blit(self.spr_cristal_minerio, (18, 16))
            _add_estrutura(sp_rocha, 1835, 650, hitbox_rel=(8, 28, 56, 30), id_estrutura="rocha_minerio_torvald")
        elif pedra_quebrada:
            if self.spr_rocha_minerio_quebrada_1:
                _add_estrutura(self.spr_rocha_minerio_quebrada_1, 1830, 675, hitbox_rel=(0, 0, 0, 0), sombra=False)
            if self.spr_rocha_minerio_quebrada_2:
                _add_estrutura(self.spr_rocha_minerio_quebrada_2, 1870, 682, hitbox_rel=(0, 0, 0, 0), sombra=False)

        # =====================================================================
        # 4. CASAS RESIDENCIAIS E CASAS NAS BORDAS DO MAPA (Zero sobreposições!)
        # =====================================================================
        # Borda Oeste (parcialmente ocultas na margem esquerda, reveladas ao explorar):
        _add_estrutura(self.sprites_casas["c1_f04"], -45, 155, id_estrutura="casa_c1_f04", categoria="casa")
        _add_estrutura(self.sprites_casas["c2_f05_sobrado"], -55, 415, id_estrutura="casa_c2_f05_sobrado", categoria="casa")
        _add_estrutura(self.sprites_casas["c1_b05"], -55, 770)
        _add_estrutura(self.sprites_casas["c2_b06"], -45, 1135)

        # Borda Leste (parcialmente ocultas na margem direita):
        _add_estrutura(self.sprites_casas["c1_f06"], 2055, 415)
        _add_estrutura(self.sprites_casas["c1_b04"], 2110, 775)
        _add_estrutura(self.sprites_casas["c1_b01"], 2090, 1135)

        # Quarteirão Residencial Sul (voltadas para a Rua Residencial Sul em y=1152..1248):
        _add_estrutura(self.sprites_casas["c1_f03"], 575, 965, id_estrutura="casa_c1_f03", categoria="casa")
        _add_estrutura(self.sprites_casas["c2_f03_hera"], 825, 980, id_estrutura="casa_c2_f03_hera", categoria="casa")
        _add_estrutura(self.sprites_casas["c1_f05"], 1245, 975)
        _add_estrutura(self.sprites_casas["c2_f06_dois_andares"], 1495, 965, id_estrutura="casa_c2_f06_dois_andares", categoria="casa")
        _add_estrutura(self.sprites_casas["c1_f07"], 1755, 985, id_estrutura="casa_c1_f07", categoria="casa")

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
        _add_estrutura(
            self.sprites_props["estandarte"],
            950,
            65,
            hitbox_rel=(6, 65, 32, 18),
            id_estrutura="estandarte_norte_esq",
            categoria="prop",
        )
        _add_estrutura(
            self.sprites_props["estandarte"],
            1245,
            65,
            hitbox_rel=(6, 65, 32, 18),
            id_estrutura="estandarte_norte_dir",
            categoria="prop",
        )

        # =====================================================================
        # 5. CERCAS MODULARES DE MADEIRA DA VILA (08_Cercas & 2 Fence)
        # =====================================================================
        sp_ch = self.sprites_props.get("cerca_h")
        sp_cv_esq = self.sprites_props.get("cerca_v")
        idx_cerca = 1

        if sp_ch:
            posicoes_cercas_h = [
                # Cercado do jardim botânico sudoeste (corredor central aberto em x=302..390)
                (170, 865), (236, 865), (390, 865), (456, 865),
                # Cercas dos jardins residenciais sul (preservando acesso aos portões)
                (782, 1110), (1020, 1110),
                (1442, 1110), (1700, 1110),
                # Cercado rústico próximo ao canto de Patusco
                (1785, 920), (1851, 920),
                # Cercas decorativas ao longo da entrada sul (corredor sul 1024..1216 livre)
                (880, 1255), (946, 1255), (1225, 1255), (1291, 1255),
            ]
            for cx, cy in posicoes_cercas_h:
                _add_estrutura(
                    sp_ch,
                    cx,
                    cy,
                    hitbox_rel=(4, 20, 58, 14),
                    sombra=False,
                    id_estrutura=f"cerca_vila_{idx_cerca:02d}",
                    categoria="cerca",
                )
                idx_cerca += 1

        # Cercas laterais verticais fechando as extremidades dos canteiros e pátio rústico
        sp_craft_v = self.sprites_props.get("cerca_craft_v") or sp_cv_esq
        laterais_v = [
            (sp_craft_v, 166, 896, (2, 18, 10, 36)),
            (sp_craft_v, 504, 896, (2, 18, 10, 36)),
            (sp_craft_v, 1775, 926, (2, 18, 10, 36)),
            (sp_craft_v, 1912, 926, (2, 18, 10, 36)),
        ]
        for sp_v, cx, cy, hb_v in laterais_v:
            if sp_v:
                _add_estrutura(
                    sp_v,
                    cx,
                    cy,
                    hitbox_rel=hb_v,
                    sombra=False,
                    id_estrutura=f"cerca_vila_{idx_cerca:02d}",
                    categoria="cerca",
                )
                idx_cerca += 1

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
            NPCFactory.criar("anciao_aldous", x=1102, y=615),
            NPCFactory.criar("curandeira_elara", x=465, y=625),
            NPCFactory.criar("ferreiro_torvald", x=1665, y=625),
            NPCFactory.criar("guarda_doran", x=1102, y=215),
        ]
        for npc in self.npcs:
            self.hitboxes.append(pygame.Rect(int(npc.x), int(npc.y), npc.largura, npc.altura))

        # =====================================================================
        # 9. ERVAS DE ORVALHO LUNAR (Para a missão de Elara: missao_ervas_medicinais)
        # =====================================================================
        self.ervas_coletaveis = []
        coletados = getattr(self.game, "itens_coletados", [])
        # Todas as 7 ervas posicionadas exclusivamente em solo de grama verde natural e em locais 100% acessíveis
        posicoes_ervas = [
            ("erva_lunar_oakhaven_1", 176, 464),   # Clareira botânica oeste
            ("erva_lunar_oakhaven_2", 304, 1264),  # Jardim campestre sudoeste
            ("erva_lunar_oakhaven_3", 848, 976),   # Prado do riacho centro-sul
            ("erva_lunar_oakhaven_4", 1648, 1344), # Campina residencial sul-leste
            ("erva_lunar_oakhaven_5", 1616, 464),  # Bosque leste da forja
            ("erva_lunar_oakhaven_6", 1424, 272),  # Bosque nordeste da paliçada
            ("erva_lunar_oakhaven_7", 240, 240),   # Bosque noroeste da taverna
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
                item_erva.origem_botanica = id_erva
                item_erva.imagem = spr_erva
                self.itens_no_chao.append(item_erva)
                self.ervas_coletaveis.append(item_erva)

        # =====================================================================
        # 10. FAUNA VIVA: PÁSSAROS E PATUSCO (ENCONTRO AMBIENTAL)
        # =====================================================================
        # Todos os esconderijos calibrados estritamente sobre tufos de grama verde (sem terra, pedra ou colisores)
        esconderijos_patusco = [
            (176, 240),    # Bosque Noroeste atrás da taverna
            (1360, 192),   # Bosque Nordeste perto da colina norte
            (160, 480),    # Canteiro botânico oeste
            (816, 944),    # Prado gramado do riacho sul
            (1648, 944),   # Pomar sudeste perto da forja
        ]
        pos_salva = getattr(self.game, "patusco_pos_oakhaven", None)
        if pos_salva in esconderijos_patusco:
            pos_gato = pos_salva
        else:
            pos_gato = random.choice(esconderijos_patusco)
            if self.game is not None:
                self.game.patusco_pos_oakhaven = pos_gato

        self.patusco = Gato(
            x=pos_gato[0],
            y=pos_gato[1],
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
                "estrutura_id": "monumento_praca",
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
                "estrutura_id": "quadro_vila",
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
                "estrutura_id": "canteiro_elara",
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
                "estrutura_id": "bancada_torvald",
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
                "estrutura_id": "rocha_minerio_torvald",
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

        preparar_detalhes(self)

    def respawn_erva_alternativa(self, item_antigo=None):
        """
        Quando uma colheita falha e a flor murcha, remove o nó danificado e
        faz brotar uma nova Erva de Orvalho Lunar em um local alternativo da vila.
        """
        origem = getattr(item_antigo, "origem_botanica", getattr(item_antigo, "id_unico", None))
        if not origem or origem in getattr(self.game, "itens_coletados", []):
            return None
        if item_antigo and item_antigo in self.itens_no_chao:
            self.itens_no_chao.remove(item_antigo)
        if item_antigo and hasattr(self, "ervas_coletaveis") and item_antigo in self.ervas_coletaveis:
            self.ervas_coletaveis.remove(item_antigo)

        pontos_alternativos = [
            (784, 944),   # Prado do riacho centro-sul (100% grama)
            (1584, 944),  # Pomar sudeste (100% grama)
            (1330, 192),  # Bosque nordeste (100% grama)
            (848, 976),   # Prado gramado do riacho (100% grama)
            (176, 464),   # Clareira botânica oeste (100% grama)
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
        nova_erva.id_unico = origem
        nova_erva.origem_botanica = origem
        nova_erva.imagem = self._gerar_sprite_erva_lunar()
        self.itens_no_chao.append(nova_erva)
        if hasattr(self, "ervas_coletaveis"):
            self.ervas_coletaveis.append(nova_erva)
            
        return nova_erva

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
        estado_jogando = getattr(self.game, "estados", {}).get("JOGANDO") if hasattr(self.game, "estados") else None
        cut_reconst = getattr(estado_jogando, "cutscene_reconstrucao", None) if estado_jogando else None
        if getattr(self.game, "ocultar_marcadores_npc", False) or (cut_reconst and getattr(cut_reconst, "ativo", False)):
            qm = None

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
        # Durante o ataque aéreo do dragão na cutscene, os moradores se abrigam das chamas e não ficam na rua
        cinematica = getattr(self.game, "cinematica_dragao", None)
        em_ataque_cutscene = bool(cinematica and getattr(cinematica, "ativo", False) and getattr(cinematica, "fase", "") in ("VOO_DRAGAO", "DORMINDO"))
        if not em_ataque_cutscene:
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
                    dx_s, dy_s = obj.get("sombra_offset", (int(obj["sw"] * 0.07), obj["sh"] - 12))
                    tela.blit(s_surf, (ox + dx_s, oy + dy_s))
                tela.blit(sp, (ox, oy))
                if obj.get("id") == "tabua_assinatura":
                    desenhar_revelacao(self, tela)
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
