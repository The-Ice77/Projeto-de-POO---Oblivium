# src/maps/oakhaven/mapa_orla_norte.py
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
from src.entities.animal import Passaro


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
        self.grade = grade

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

        # Paliçada defensiva ao sul (vista pelo lado externo do Portão Norte de Oakhaven)
        # Auditoria R05: peças de 08_Cercas (~36px) cobrem cercados internos; mantemos a paliçada de carvalho robusta na muralha externa.
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
            sombra_surf = None
            sombra_offset = (0, 0)
            if sombra:
                sombra_surf, sombra_offset = criar_sombra_contato_estrutura(sprite, cor=(14, 18, 16, 75))
            self.estruturas_ysort.append({
                "sprite": sprite,
                "x": int(x),
                "y": int(y),
                "y_sort": int(hb.bottom if hb.height > 0 else y + sh),
                "sombra": sombra,
                "sombra_surf": sombra_surf,
                "sombra_offset": sombra_offset,
                "sw": sw,
                "sh": sh,
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
            NPCFactory.criar("guarda_doran", x=485, y=465, dialogo_id="hub_doran_orla_norte")
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
                s_surf = obj.get("sombra_surf")
                if s_surf:
                    dx_s, dy_s = obj.get("sombra_offset", (0, 0))
                    tela.blit(s_surf, (ox + dx_s, oy + dy_s))
                elif obj.get("sombra"):
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
