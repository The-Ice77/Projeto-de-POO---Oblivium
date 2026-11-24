# src/maps/oakhaven/mapa_ninho_dragao.py
import random
import pygame
from src.maps.cenario_base import CenarioBase
from src.maps.oakhaven.terreno_utils import (
    _carregar_tiles_terreno,
    _renderizar_grade_autotile,
    criar_sombra_contato_estrutura,
    criar_sombra_silhueta_achatada,
)
from src.utils.resource_manager import ResourceManager
from src.entities.elemento_cenario import ChamaIndependente


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
            sombra_offset = (0, 0)
            if sombra:
                sombra_surf, sombra_offset = criar_sombra_contato_estrutura(sprite, cor=(10, 8, 8, 90))

            calc_ysort = y_sort_custom if y_sort_custom is not None else max(int(hb.bottom), int(y + sh - 4))
            self.estruturas_ysort.append({
                "sprite": sprite,
                "x": int(x),
                "y": int(y),
                "y_sort": calc_ysort,
                "sombra": sombra,
                "sombra_surf": sombra_surf,
                "sombra_offset": sombra_offset,
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
        else:
            self.pontos_interacao = [
                {
                    "id": "altar_desafiar_dragao",
                    "rect": pygame.Rect(420, 140, 440, 180),
                    "prompt_x": 640,
                    "prompt_y": 195,
                    "acao_texto": "para Enfrentar Ignis'Vahr",
                    "evento": "iniciar_climax_dragao_oakhaven"
                },
                {
                    "id": "trilha_recuar_oakhaven",
                    "rect": pygame.Rect(540, 640, 200, 70),
                    "prompt_x": 640,
                    "prompt_y": 620,
                    "acao_texto": "para Recuar a Oakhaven",
                    "evento": "recuar_oakhaven_destruida"
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
                    dx_s, dy_s = obj.get("sombra_offset", (int(obj["sw"] * 0.07), obj["sh"] - 12))
                    tela.blit(s_surf, (ox + dx_s, oy + dy_s))
                tela.blit(sp, (ox, oy))
            elif tipo == "entidade":
                obj.desenhar(tela)
            elif tipo == "fogo":
                obj.desenhar_sprite(tela)
                obj.desenhar_particulas(tela)
            elif tipo == "dragao_derrotado":
                cx, cy = obj["x"], obj["y"]
                # Sombra contornada pela silhueta real do dragão abatido sobre a rocha vulcânica
                sombra_corpo = getattr(self, "_sombra_dragao_derrotado", None)
                if sombra_corpo is None:
                    sombra_corpo = criar_sombra_silhueta_achatada(
                        obj["sprite"], cor=(14, 10, 14, 105), escala_y=0.26, desloc_x=4, desloc_y=3
                    )
                    self._sombra_dragao_derrotado = sombra_corpo
                s_surf_d, (dx_d, dy_d) = sombra_corpo
                if s_surf_d:
                    tela.blit(s_surf_d, (cx + dx_d, cy + dy_d))
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
