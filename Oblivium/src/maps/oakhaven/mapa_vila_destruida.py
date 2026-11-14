# src/maps/oakhaven/mapa_vila_destruida.py
import pygame
from src.maps.oakhaven.mapa_vila import MapaOakhaven
from src.utils.resource_manager import ResourceManager
from src.entities.npc_factory import NPCFactory
from src.entities.elemento_cenario import ChamaIndependente


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

        # Remove hitboxes dos NPCs anteriores criados no super() (como o Ferreiro em seu local original)
        hitboxes_npcs = [pygame.Rect(int(npc.x), int(npc.y), npc.largura, npc.altura) for npc in self.npcs]
        self.hitboxes = [h for h in self.hitboxes if h not in hitboxes_npcs]

        # Na praça de Oakhaven Destruída, os sobreviventes estão reunidos acolhendo Halia:
        # Ancião Aldous, Curandeira Elara e Guarda Doran (o Ferreiro Torvald permanece fora de cena na forja/escombros)
        self.npcs = [
            NPCFactory.criar(
                "anciao_aldous",
                x=1060,
                y=615,
                dialogo_id="hub_aldous_destruida",
                tem_loja=False,
            ),
            NPCFactory.criar(
                "curandeira_elara",
                x=1110,
                y=615,
                dialogo_id="hub_elara_destruida",
                tem_loja=False,
            ),
            NPCFactory.criar(
                "guarda_doran",
                x=1160,
                y=615,
                dialogo_id="hub_doran_destruida",
                tem_loja=False,
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
