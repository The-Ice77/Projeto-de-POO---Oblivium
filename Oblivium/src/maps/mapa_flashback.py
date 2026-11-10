# src/maps/mapa_flashback.py
import math
import random
import pygame
import os
from src.maps.cenario_base import CenarioBase
from src.utils.resource_manager import ResourceManager, Animacao, PASTA_ASSETS
from src.utils.colors import PRETO


class VagaLume:
    """Partícula viva de vaga-lume com trajetória senoidal tridimensional e pulso de luz suave."""
    def __init__(self, x_origem, y_origem, raio_orbita_x, raio_orbita_y, freq_x, freq_y, cor, fase=0.0):
        self.cx = x_origem
        self.cy = y_origem
        self.rx = raio_orbita_x
        self.ry = raio_orbita_y
        self.fx = freq_x
        self.fy = freq_y
        self.cor = cor
        self.fase = fase
        self.x = x_origem
        self.y = y_origem
        self.brilho = 1.0

    def atualizar(self, tempo):
        t = tempo + self.fase
        self.x = self.cx + math.sin(t * self.fx) * self.rx + math.cos(t * self.fy * 0.5) * (self.rx * 0.35)
        self.y = self.cy + math.cos(t * self.fy) * self.ry + math.sin(t * self.fx * 0.7) * (self.ry * 0.3)
        self.brilho = 0.35 + 0.65 * (0.5 + 0.5 * math.sin(t * (self.fx + self.fy) * 1.5))


class FolhaVento:
    """Folha de outono flutuando suavemente com a brisa noturna."""
    def __init__(self, largura_tela, altura_tela):
        self.largura = largura_tela
        self.altura = altura_tela
        self.resetar(random.randint(0, largura_tela))

    def resetar(self, x=None):
        self.x = x if x is not None else -30
        self.y = random.uniform(90, self.altura - 130)
        self.vx = random.uniform(35, 75)
        self.vy = random.uniform(-8, 16)
        self.angulo = random.uniform(0, 360)
        self.v_rot = random.uniform(-70, 70)
        self.fase_onda = random.uniform(0, math.pi * 2)

    def atualizar(self, dt, tempo):
        self.x += self.vx * dt
        self.y += (self.vy + math.sin(tempo * 2.2 + self.fase_onda) * 14.0) * dt
        self.angulo += self.v_rot * dt
        if self.x > self.largura + 40 or self.y > self.altura + 20:
            self.resetar(-20)


class MapaFlashbackAcampamento(CenarioBase):
    """
    Cenário Real de Acampamento dos Heróis do Passado (Oblivium).

    Recriação completa do acampamento em uma clareira viva, aconchegante e cativante:
    - Terreno de floresta com autotiling de grama exuberante e clareira orgânica de terra pisoteada.
    - Floresta densa envolvente em multicamadas (100% carvalhos e coníferas ancestrais verdes e viçosos).
    - Sub-bosque detalhado com samambaias, arbustos floridos e cogumelos bioluminescentes.
    - Tendas autênticas de expedição de aventureiro em lona com estacas e cordas.
    - Postes rústicos com lanternas de latão acesas iluminando as tendas.
    - Assentos de troncos caídos de floresta com mantas de pele e esteiras.
    - Fogueira viva central com tripé de ferro forjado e caldeirão de chá de ervas borbulhante (de Caelen).
    - Fauna e flora noturna: coruja de olhos dourados que pisca no galho alto, enxame de vaga-lumes
      verde-esmeralda e dourados, flores silvestres noturnas e cogumelos luminescentes.
    - Companheiros com novas sprites oficiais, respiração natural e equipamentos pessoais detalhados:
      * Roland: armadura completa, espada em mãos e escudo de torre fincado no solo com brasão dourado.
      * Caelen: túnica celeste serena, caldeirão de ervas medicinais e frascos alquímicos.
      * Sylvan: anão robusto sobre manta de pele, caneca de cerveja escura espumante e martelo de guerra.
      * Halia (Jovem): manto anil, grimório aberto com runas brilhantes e cristal azul de mana.
    - Iluminação radial dinâmica suave sem faixas (gradiente pré-renderizado) e brasas subindo ao céu estrelado.
    """

    def __init__(self, game=None, largura_tela=1280, altura_tela=720):
        self.tempo_cena = 0.0
        self.frame_fogo_idx = 0.0
        self.frame_fumaca_idx = 0.0

        # Estrelas fixas na abóbada celeste
        random.seed(1337)
        self.estrelas = [
            (
                random.randint(15, largura_tela - 15),
                random.randint(8, int(altura_tela * 0.40)),
                random.choice([
                    (230, 240, 255), (200, 220, 255),
                    (255, 248, 220), (240, 245, 255), (255, 235, 190)
                ]),
                random.choice([1, 1, 1, 2, 2]),
                random.uniform(0.8, 3.5),
                random.uniform(0.0, math.pi * 2)
            )
            for _ in range(80)
        ]

        # Partículas de brasas e fagulhas da fogueira
        self.particulas_brasas = [
            {
                "x": 640 + random.randint(-22, 22),
                "y": 440 - random.randint(0, 15),
                "vx": random.uniform(-18, 22),
                "vy": random.uniform(-35, -75),
                "raio": random.uniform(1.2, 2.6),
                "vida": random.uniform(0.6, 2.4),
                "vida_max": 2.4,
                "cor": random.choice([(255, 180, 45), (255, 125, 30), (255, 238, 120), (255, 80, 20)])
            }
            for _ in range(35)
        ]

        # Vaga-lumes vivos flutuando pela clareira
        random.seed(42)
        self.vaga_lumes = []
        for _ in range(26):
            cx = random.randint(140, largura_tela - 140)
            cy = random.randint(220, altura_tela - 120)
            rx = random.uniform(30, 75)
            ry = random.uniform(18, 50)
            fx = random.uniform(0.6, 1.6)
            fy = random.uniform(0.7, 1.9)
            cor = random.choice([
                (165, 248, 95),   # Verde-esmeralda
                (250, 228, 75),   # Dourado solar
                (135, 255, 175),  # Verde água místico
                (255, 205, 90)    # Âmbar quente
            ])
            self.vaga_lumes.append(VagaLume(cx, cy, rx, ry, fx, fy, cor, random.uniform(0, 6.28)))

        # Folhas de outono voando com o vento
        self.folhas_vento = [FolhaVento(largura_tela, altura_tela) for _ in range(12)]

        # Bolhas e vapor do chá de ervas de Caelen no caldeirão
        self.vapor_caldeirao = [
            {
                "x": 640 + random.uniform(-8, 8),
                "y": 400 - random.uniform(0, 5),
                "vy": random.uniform(-18, -32),
                "vx": random.uniform(-4, 8),
                "raio": random.uniform(3.0, 6.0),
                "vida": random.uniform(0.4, 1.5),
                "vida_max": 1.5
            }
            for _ in range(14)
        ]

        super().__init__(
            game=game,
            largura_tela=largura_tela,
            altura_tela=altura_tela,
            nome="FLASHBACK_ACAMPAMENTO",
            largura_mundo=largura_tela,
            altura_mundo=altura_tela
        )
        self.inicializar_cenario()

    def carregar_recursos(self):
        """Carrega texturas de solo, árvores 100% verdes, tendas autênticas e sprites dos heróis."""
        larg, alt = self.largura_tela, self.altura_tela

        # 1. Base contínua de grama de floresta para toda a clareira com terra orgânica central
        self.chao_superficie = pygame.Surface((larg, alt))
        self.chao_superficie.fill((28, 56, 18))
        tile_grama = ResourceManager.carregar_imagem("cenario/02_Pisos_Externos/01_Grama_Verde/piso_grama_r10_c01.png", (32, 32))
        if tile_grama:
            for y in range(int(alt * 0.26), alt, 32):
                for x in range(0, larg, 32):
                    self.chao_superficie.blit(tile_grama, (x, y))

        # Clareira orgânica de terra pisoteada com transição ultra-suave ao redor do fogo
        surf_terra = pygame.Surface((larg, alt), pygame.SRCALPHA)
        cx_fogo, cy_fogo = 640, 440
        for rx, ry, alpha, cor_t in [
            (390, 165, 45, (60, 42, 24)),
            (320, 135, 80, (70, 48, 28)),
            (250, 105, 120, (82, 58, 34)),
            (170, 75, 150, (94, 66, 38)),
            (100, 45, 180, (108, 76, 44))
        ]:
            pygame.draw.ellipse(surf_terra, (*cor_t, alpha), (cx_fogo - rx, cy_fogo - ry, rx * 2, ry * 2))
        self.chao_superficie.blit(surf_terra, (0, 0))

        # 2. Carvalhos e coníferas ancestrais frondosos (100% verdes, sem árvores secas nem tocos)
        p_t1 = "assets/cenario/arvores_separadas_tipo1"
        p_t2 = "assets/cenario/arvores_separadas_tipo2"

        # Árvores de fundo que criam a copa ao norte
        self.arvores_fundo = [
            (-30, -20, 195, 275, f"{p_t1}/Model_01_Size_05/Model_01_Size_05_01.png", False),
            (75, 0, 165, 240, f"{p_t1}/Model_01_Size_04/Model_01_Size_04_01.png", False),
            (185, -15, 190, 270, f"{p_t1}/Model_01_Size_05/Model_01_Size_05_02.png", True),
            (300, 5, 160, 235, f"{p_t1}/Model_01_Size_04/Model_01_Size_04_02.png", False),
            (415, -20, 190, 270, f"{p_t1}/Model_01_Size_05/Model_01_Size_05_01.png", True),
            (535, -5, 175, 250, f"{p_t2}/Model_02_Size_05/Model_02_Size_05_01.png", False),
            (660, -20, 190, 270, f"{p_t1}/Model_01_Size_05/Model_01_Size_05_01.png", False),
            (780, 5, 165, 240, f"{p_t1}/Model_01_Size_04/Model_01_Size_04_01.png", True),
            (890, -15, 190, 270, f"{p_t1}/Model_01_Size_05/Model_01_Size_05_02.png", False),
            (1005, 0, 165, 240, f"{p_t1}/Model_01_Size_04/Model_01_Size_04_02.png", True),
            (1115, -20, 195, 275, f"{p_t1}/Model_01_Size_05/Model_01_Size_05_01.png", True),
        ]

        # Árvores intermediárias para preencher o horizonte e cobrir troncos
        self.arvores_meio = [
            (25, 90, 140, 195, f"{p_t1}/Model_01_Size_03/Model_01_Size_03_01.png", False),
            (135, 100, 135, 190, f"{p_t1}/Model_01_Size_03/Model_01_Size_03_02.png", True),
            (965, 95, 140, 195, f"{p_t1}/Model_01_Size_03/Model_01_Size_03_01.png", True),
            (1075, 100, 135, 190, f"{p_t1}/Model_01_Size_03/Model_01_Size_03_02.png", False),
        ]

        # Árvores de primeiro plano nas bordas esquerda e direita para criar moldura natural
        self.arvores_moldura = [
            (-40, 140, 195, 280, f"{p_t1}/Model_01_Size_05/Model_01_Size_05_01.png", False),
            (-35, 360, 190, 275, f"{p_t1}/Model_01_Size_05/Model_01_Size_05_02.png", False),
            (1125, 130, 195, 280, f"{p_t1}/Model_01_Size_05/Model_01_Size_05_01.png", True),
            (1135, 350, 190, 275, f"{p_t1}/Model_01_Size_05/Model_01_Size_05_02.png", True),
        ]

        self.sprites_arvores = {}
        for _, _, w, h, path, fl in self.arvores_fundo + self.arvores_meio + self.arvores_moldura:
            chave = (path, w, h, fl)
            if chave not in self.sprites_arvores:
                im = ResourceManager.carregar_imagem(path, (w, h))
                if im and fl:
                    im = pygame.transform.flip(im, True, False)
                self.sprites_arvores[chave] = im

        # 3. Tendas e Props Autênticos de Acampamento (Craftpix Camp & Decor)
        p_camp = "assets/novos assets/craftpix-net-665131-free-fields-tileset-pixel-art-for-tower-defense/2 Objects/8 Camp"
        p_decor = "assets/novos assets/craftpix-net-665131-free-fields-tileset-pixel-art-for-tower-defense/2 Objects/7 Decor"
        p_bush = "assets/novos assets/craftpix-net-141354-free-top-down-bushes-pixel-art/PNG/Assets"
        p_cryst = "assets/novos assets/craftpix-net-106469-top-down-crystals-pixel-art/PNG/Assets"

        # Tendas autênticas de expedição
        self.spr_tenda_aframe = ResourceManager.carregar_imagem(f"{p_camp}/1.png", (155, 98))
        self.spr_tenda_lateral = ResourceManager.carregar_imagem(f"{p_camp}/4.png", (140, 95))
        self.spr_mochila = ResourceManager.carregar_imagem(f"{p_camp}/5.png", (38, 24))

        # Troncos caídos de floresta para assento rústico e tocos de mesa
        self.spr_tronco_longo = ResourceManager.carregar_imagem(f"{p_decor}/Log3.png", (114, 36))
        self.spr_banco = self.spr_tronco_longo
        self.spr_toco_mesa = ResourceManager.carregar_imagem(f"{p_decor}/Tree2.png", (50, 40))

        # Postes rústicos com lanternas de latão
        self.spr_poste_lanterna = ResourceManager.carregar_imagem(f"{p_decor}/Lamp1.png", (36, 75))

        # Caixas de provisões, barris de carvalho e lenha empilhada
        self.spr_lenha = ResourceManager.carregar_imagem("assets/cenario/vila/Props/Cargas_e_Transporte/pilha_lenha_organizada.png", (80, 68))
        self.spr_caixas = ResourceManager.carregar_imagem("assets/cenario/vila/Props/Cargas_e_Transporte/caixas_madeira_pilha.png", (78, 64))
        self.spr_barris = ResourceManager.carregar_imagem("assets/cenario/vila/Props/Cargas_e_Transporte/barris_pilha.png", (74, 72))

        # Pedras naturais da fogueira
        self.spr_pedra = ResourceManager.carregar_imagem("assets/cenario/vegetacao_pedras_separadas/Rocks/Rocks_005.png", (24, 20))

        # Vegetação e flores noturnas
        self.spr_samambaia = ResourceManager.carregar_imagem(f"{p_bush}/Fern1_1.png", (58, 58))
        self.spr_arbusto_azul = ResourceManager.carregar_imagem(f"{p_bush}/Bush_blue_flowers1.png", (62, 62))
        self.spr_arbusto_rosa = ResourceManager.carregar_imagem(f"{p_bush}/Bush_pink_flowers1.png", (60, 60))

        # Grimório aberto, cristal arcano e bolsa de componentes de Halia
        self.spr_grimorio = ResourceManager.carregar_imagem("assets/props/Grimorio.png", (46, 46))
        self.spr_cristal_mana = ResourceManager.carregar_imagem(f"{p_cryst}/Blue_crystal1.png", (28, 28))
        self.spr_bolsa_componentes = ResourceManager.carregar_imagem("assets/props/Bolsa de Moedas.png", (30, 30))

        # Folha de outono para o vento
        self.spr_folha = ResourceManager.carregar_imagem("assets/efeitos/folhas/autumn leaf.png", (18, 18))

        # 4. Animações de Fogo Autêntico e Fumaça
        self.frames_fogo = (
            ResourceManager.carregar_frames_pasta("efeitos/fogo/chama_fogueira_larga")
            or ResourceManager.carregar_frames_pasta("efeitos/fogo/fogueira_laranja")
            or []
        )
        self.frames_fumaca = (
            ResourceManager.carregar_frames_pasta("efeitos/fogo/fumaca_fogueira")
            or []
        )

        # 5. Heróis com Animações das Novas Sprites Oficiais e Fallbacks Canônicos
        self.spr_sylvan = self._criar_sprite_sylvan()
        self.spr_roland = self._criar_sprite_roland()
        self.spr_caelen = self._criar_sprite_caelen()
        self.spr_halia = self._criar_sprite_halia()

        self.anim_sylvan = self._carregar_animacao_heroi("npc/sylvan_anao/idle", 88, flip=False) or Animacao([self.spr_sylvan], 0.1)
        self.anim_roland = self._carregar_animacao_heroi("npc/roland_paladino/idle", 84, flip=True) or Animacao([self.spr_roland], 0.1)
        self.anim_caelen = self._carregar_animacao_heroi("npc/caelen_clerigo/idle", 80, flip=False) or Animacao([self.spr_caelen], 0.1)
        self.anim_halia = self._carregar_animacao_heroi("halia/novas_sprites/idle", 92, flip=True) or Animacao([self.spr_halia], 0.1)

        # 6. Iluminação Radial Suave Pré-Renderizada (Gaussian / Cosine Falloff)
        self._luz_fogo_suave = self._gerar_mapa_luz_suave(raio=430)
        self._luz_lanterna_suave = self._gerar_mapa_luz_suave(raio=110, max_alpha=120)

        # 7. Vinheta de Memória
        self._vinheta_cache = pygame.Surface((larg, alt), pygame.SRCALPHA)
        self._construir_vinheta(larg, alt)

    def _gerar_mapa_luz_suave(self, raio=400, max_alpha=145):
        """Gera uma superfície radial pré-renderizada com decaimento suave contínuo (sem faixas concêntricas)."""
        diam = raio * 2
        surf = pygame.Surface((diam, diam), pygame.SRCALPHA)
        passos = 160
        dr = raio / passos
        for i in range(passos, 0, -1):
            r = int(i * dr)
            frac = 1.0 - (r / raio)
            alpha = int(max_alpha * (frac ** 1.9))
            red = 255
            green = int(140 + 105 * (frac ** 1.2))
            blue = int(25 + 130 * (frac ** 2.0))
            pygame.draw.circle(surf, (red, green, blue, alpha), (raio, raio), r)
        return surf

    def _construir_vinheta(self, larg, alt):
        """Constrói vinheta cinematográfica de recordação suave nas bordas."""
        self._vinheta_cache.fill((0, 0, 0, 0))
        for raio_v in range(45, 0, -5):
            alpha_b = int((50 - raio_v) * 2.5)
            pygame.draw.rect(self._vinheta_cache, (10, 8, 14, alpha_b), (0, 0, larg, alt), width=raio_v)

    def inicializar_cenario(self):
        """Configura estado e elementos posicionais do acampamento."""
        self.hitboxes.clear()
        self.itens_no_chao.clear()

    def _carregar_animacao_heroi(self, pasta_rel, alt_alvo, flip=False):
        """Carrega animação fluida em alta fidelidade a partir das novas sprites recortadas."""
        pasta_abs = os.path.join(PASTA_ASSETS, pasta_rel)
        if not os.path.exists(pasta_abs):
            return None
        arqs = sorted([f for f in os.listdir(pasta_abs) if f.lower().endswith('.png')])
        frames = []
        for a in arqs:
            img_rel = os.path.join(pasta_rel, a).replace("\\", "/")
            surf = ResourceManager.carregar_imagem(img_rel)
            if surf:
                orig_w, orig_h = surf.get_size()
                larg_alvo = max(1, int(orig_w * (alt_alvo / orig_h)))
                surf_sc = pygame.transform.scale(surf, (larg_alvo, alt_alvo))
                if flip:
                    surf_sc = pygame.transform.flip(surf_sc, True, False)
                frames.append(surf_sc)
        if frames:
            return Animacao(frames, velocidade=0.08, loop=True)
        return None

    # =========================================================================
    # Geradores Canônicos de Pixel-Art dos Heróis (Fallbacks)
    # =========================================================================
    def _criar_sprite_sylvan(self):
        """Gera Sylvan: anão robusto com barba ruiva trançada, armadura de ferro e caneca."""
        gw, gh = 28, 34
        surf = pygame.Surface((gw, gh), pygame.SRCALPHA)
        contorno = (20, 16, 22)
        pele = (225, 185, 155)
        ruivo = (195, 75, 30)
        ferro = (130, 140, 150)
        ouro = (225, 185, 55)
        couro = (85, 55, 38)
        pygame.draw.rect(surf, contorno, (7, 28, 6, 6))
        pygame.draw.rect(surf, contorno, (15, 28, 6, 6))
        pygame.draw.rect(surf, couro, (8, 29, 4, 4))
        pygame.draw.rect(surf, couro, (16, 29, 4, 4))
        pygame.draw.rect(surf, contorno, (6, 22, 16, 8))
        pygame.draw.rect(surf, (65, 75, 90), (7, 23, 14, 6))
        pygame.draw.rect(surf, contorno, (4, 11, 20, 13))
        pygame.draw.rect(surf, couro, (5, 12, 18, 11))
        pygame.draw.rect(surf, ferro, (7, 13, 14, 7))
        pygame.draw.rect(surf, ouro, (5, 20, 18, 3))
        pygame.draw.rect(surf, contorno, (7, 3, 14, 11))
        pygame.draw.rect(surf, pele, (8, 4, 12, 9))
        pygame.draw.rect(surf, contorno, (5, 8, 18, 12))
        pygame.draw.rect(surf, ruivo, (6, 9, 16, 10))
        return surf

    def _criar_sprite_roland(self):
        """Gera Roland: paladino vigilante com armadura de placas prateadas e capa azul."""
        gw, gh = 26, 36
        surf = pygame.Surface((gw, gh), pygame.SRCALPHA)
        contorno = (18, 20, 24)
        placa = (185, 195, 210)
        azul_capa = (35, 65, 130)
        ouro = (225, 185, 55)
        pygame.draw.rect(surf, azul_capa, (4, 10, 18, 22))
        pygame.draw.rect(surf, contorno, (6, 28, 6, 8))
        pygame.draw.rect(surf, contorno, (14, 28, 6, 8))
        pygame.draw.rect(surf, placa, (7, 29, 4, 6))
        pygame.draw.rect(surf, placa, (15, 29, 4, 6))
        pygame.draw.rect(surf, contorno, (5, 9, 16, 16))
        pygame.draw.rect(surf, placa, (6, 10, 14, 14))
        pygame.draw.line(surf, ouro, (13, 11), (13, 21), 2)
        pygame.draw.line(surf, ouro, (9, 15), (17, 15), 2)
        pygame.draw.rect(surf, contorno, (7, 2, 12, 10))
        pygame.draw.rect(surf, (220, 225, 235), (8, 3, 10, 8))
        return surf

    def _criar_sprite_caelen(self):
        """Gera Caelen: clérigo sereno em túnica celeste e manto sacerdotal com capuz."""
        gw, gh = 24, 34
        surf = pygame.Surface((gw, gh), pygame.SRCALPHA)
        contorno = (20, 22, 28)
        pele = (225, 190, 160)
        celeste = (95, 145, 210)
        branco = (235, 240, 248)
        ouro = (225, 185, 55)
        pygame.draw.rect(surf, contorno, (5, 11, 14, 21))
        pygame.draw.rect(surf, branco, (6, 12, 12, 19))
        pygame.draw.rect(surf, celeste, (5, 11, 4, 19))
        pygame.draw.rect(surf, celeste, (15, 11, 4, 19))
        pygame.draw.rect(surf, ouro, (6, 29, 12, 2))
        pygame.draw.rect(surf, contorno, (6, 2, 12, 11))
        pygame.draw.rect(surf, celeste, (6, 2, 12, 10))
        pygame.draw.rect(surf, pele, (9, 5, 6, 6))
        return surf

    def _criar_sprite_halia(self):
        """Gera Halia Jovem: maga com manto azul anil e cabelos prateados luminescentes."""
        gw, gh = 24, 34
        surf = pygame.Surface((gw, gh), pygame.SRCALPHA)
        contorno = (20, 18, 26)
        pele = (235, 195, 170)
        manto = (45, 75, 145)
        cabelo = (225, 230, 245)
        pygame.draw.rect(surf, contorno, (5, 12, 14, 20))
        pygame.draw.rect(surf, manto, (6, 13, 12, 18))
        pygame.draw.rect(surf, (30, 50, 105), (8, 13, 8, 18))
        pygame.draw.rect(surf, contorno, (5, 2, 14, 13))
        pygame.draw.rect(surf, cabelo, (6, 3, 12, 11))
        pygame.draw.rect(surf, pele, (8, 5, 8, 7))
        pygame.draw.rect(surf, (60, 130, 230), (9, 7, 2, 2))
        pygame.draw.rect(surf, (60, 130, 230), (13, 7, 2, 2))
        return surf

    def atualizar(self, dt=0.016):
        """Atualiza tempo, física de partículas, animações e fauna noturna."""
        self.tempo_cena += dt
        tempo = self.tempo_cena

        # Atualiza frames do fogo e fumaça
        if self.frames_fogo:
            self.frame_fogo_idx = (self.frame_fogo_idx + 12.0 * dt) % len(self.frames_fogo)
        if self.frames_fumaca:
            self.frame_fumaca_idx = (self.frame_fumaca_idx + 8.0 * dt) % len(self.frames_fumaca)

        # Atualiza animações dos heróis
        if self.anim_sylvan: self.anim_sylvan.atualizar()
        if self.anim_roland: self.anim_roland.atualizar()
        if self.anim_caelen: self.anim_caelen.atualizar()
        if self.anim_halia: self.anim_halia.atualizar()

        # Atualiza vaga-lumes
        for vl in self.vaga_lumes:
            vl.atualizar(tempo)

        # Atualiza folhas ao vento
        for folha in self.folhas_vento:
            folha.atualizar(dt, tempo)

        # Atualiza partículas de brasas da fogueira
        cx_fogo, cy_fogo = 640, 440
        for p in self.particulas_brasas:
            p["x"] += p["vx"] * dt + math.sin(tempo * 3.5 + p["y"]) * 0.4
            p["y"] += p["vy"] * dt
            p["vida"] -= dt
            if p["vida"] <= 0:
                p["x"] = cx_fogo + random.randint(-22, 22)
                p["y"] = cy_fogo - random.randint(5, 18)
                p["vx"] = random.uniform(-18, 22)
                p["vy"] = random.uniform(-35, -75)
                p["vida"] = random.uniform(0.6, 2.4)
                p["vida_max"] = p["vida"]
                p["raio"] = random.uniform(1.2, 2.6)

        # Atualiza bolhas e vapor do caldeirão de Caelen
        for vp in self.vapor_caldeirao:
            vp["x"] += vp["vx"] * dt
            vp["y"] += vp["vy"] * dt
            vp["raio"] += dt * 3.5
            vp["vida"] -= dt
            if vp["vida"] <= 0:
                vp["x"] = cx_fogo + random.uniform(-8, 8)
                vp["y"] = cy_fogo - 40 - random.uniform(0, 5)
                vp["vx"] = random.uniform(-5, 9)
                vp["vy"] = random.uniform(-18, -32)
                vp["raio"] = random.uniform(2.5, 4.5)
                vp["vida"] = random.uniform(0.5, 1.5)
                vp["vida_max"] = vp["vida"]

    def desenhar_camada_inferior(self, tela, area_visivel=None):
        """Renderiza o céu estrelado através da copa, grama contínua de floresta e árvores de fundo."""
        larg, alt = self.largura_tela, self.altura_tela

        # 1. Gradiente suave da abóbada celeste ao norte (visível entre as copas das árvores)
        ceu_altura = int(alt * 0.45)
        for y_c in range(0, ceu_altura, 2):
            frac = y_c / ceu_altura
            r_c = int(8 + (18 - 8) * frac)
            g_c = int(12 + (26 - 12) * frac)
            b_c = int(28 + (46 - 28) * frac)
            pygame.draw.rect(tela, (r_c, g_c, b_c), (0, y_c, larg, 2))

        # 2. Constelações e estrelas cintilantes na abóbada celeste
        tempo_ms = self.tempo_cena
        for sx, sy, cor, raio, freq, fase in self.estrelas:
            pisca = int(math.sin(tempo_ms * freq + fase) * 26)
            cor_cint = (
                max(0, min(255, cor[0] + pisca)),
                max(0, min(255, cor[1] + pisca)),
                max(0, min(255, cor[2] + pisca))
            )
            pygame.draw.circle(tela, cor_cint, (sx, sy), raio)
            if raio >= 2 and pisca > 12:
                pygame.draw.line(tela, (*cor_cint, 90), (sx - 3, sy), (sx + 3, sy), 1)
                pygame.draw.line(tela, (*cor_cint, 90), (sx, sy - 3), (sx, sy + 3), 1)

        # 3. Lua prateada com halos difusos no céu à direita
        mx, my = 1040, 75
        for r_halo, alpha_h in [(60, 18), (48, 40), (36, 75)]:
            surf_halo = pygame.Surface((r_halo * 2, r_halo * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf_halo, (220, 235, 255, alpha_h), (r_halo, r_halo), r_halo)
            tela.blit(surf_halo, (mx - r_halo, my - r_halo))
        pygame.draw.circle(tela, (242, 245, 252), (mx, my), 28)
        pygame.draw.circle(tela, (210, 218, 235), (mx - 7, my - 5), 5)
        pygame.draw.circle(tela, (210, 218, 235), (mx + 8, my + 7), 7)

        # 4. Base contínua de grama de floresta e solo orgânico pisoteado
        if self.chao_superficie:
            tela.blit(self.chao_superficie, (0, 0))

        # 5. Árvores ancestrais fechando a clareira ao norte (copa superior, 100% verdes)
        for x, y, w, h, path, fl in self.arvores_fundo:
            spr = self.sprites_arvores.get((path, w, h, fl))
            if spr:
                tela.blit(spr, (x, y))

        # 6. Árvores intermediárias que criam a transição suave para o solo da clareira
        for x, y, w, h, path, fl in self.arvores_meio:
            spr = self.sprites_arvores.get((path, w, h, fl))
            if spr:
                tela.blit(spr, (x, y))

        # 7. Sub-bosque e vegetação rasteira ao longo da borda da floresta (samambaias e flores)
        if self.spr_samambaia:
            pos_samambaias = [(5, 230), (65, 240), (170, 245), (285, 245), (420, 245), (630, 245), (850, 245), (1020, 235), (1080, 240), (1200, 235)]
            for sx, sy in pos_samambaias:
                tela.blit(self.spr_samambaia, (sx, sy))
        if self.spr_arbusto_azul:
            pos_azuis = [(115, 235), (350, 240), (700, 240), (960, 245)]
            for bx, by in pos_azuis:
                tela.blit(self.spr_arbusto_azul, (bx, by))
        if self.spr_arbusto_rosa:
            pos_rosas = [(230, 240), (560, 240), (900, 240), (1140, 230)]
            for rx, ry in pos_rosas:
                tela.blit(self.spr_arbusto_rosa, (rx, ry))

        # 8. Cogumelos bioluminescentes azuis e violetas nas raízes das árvores
        self._desenhar_cogumelos_luminescentes(tela)

    def _desenhar_cogumelos_luminescentes(self, tela):
        """Desenha pequenos agrupamentos de cogumelos que pulsam com bioluminescência noturna."""
        pontos = [
            (125, 285, (90, 220, 235)),
            (138, 292, (80, 200, 225)),
            (118, 296, (110, 235, 245)),
            (240, 290, (180, 130, 245)),
            (252, 296, (195, 145, 255)),
            (1010, 290, (90, 220, 235)),
            (1024, 296, (80, 200, 225)),
            (1115, 285, (180, 130, 245)),
            (1128, 292, (195, 145, 255)),
        ]
        tempo = self.tempo_cena
        for x, y, cor in pontos:
            pulso = 0.5 + 0.5 * math.sin(tempo * 2.8 + x * 0.1)
            raio_halo = int(7 + pulso * 4)
            surf_h = pygame.Surface((raio_halo * 2, raio_halo * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf_h, (*cor, int(45 * pulso)), (raio_halo, raio_halo), raio_halo)
            tela.blit(surf_h, (x - raio_halo, y - raio_halo))
            pygame.draw.line(tela, (210, 215, 225), (x, y + 2), (x, y + 7), 2)
            pygame.draw.ellipse(tela, cor, (x - 5, y - 3, 10, 6))

    def desenhar_props(self, tela):
        """Renderiza tendas autênticas, postes com lanternas, caldeirão, fogueira viva e os quatro heróis com sombras."""
        cx_fogo, cy_fogo = 640, 440
        tempo_ms = self.tempo_cena

        # Sombras suaves de contato 2.5D (alfa realista de 90-120)
        surf_sombras = pygame.Surface((self.largura_tela, self.altura_tela), pygame.SRCALPHA)
        pygame.draw.ellipse(surf_sombras, (12, 18, 14, 90), (150, 355, 165, 30))  # Tenda esquerda
        pygame.draw.ellipse(surf_sombras, (12, 18, 14, 90), (885, 345, 150, 28))  # Tenda direita
        pygame.draw.ellipse(surf_sombras, (12, 18, 14, 100), (365, 452, 85, 22))  # Lenha
        pygame.draw.ellipse(surf_sombras, (12, 18, 14, 100), (845, 442, 80, 20))  # Caixas
        pygame.draw.ellipse(surf_sombras, (12, 18, 14, 100), (910, 448, 76, 20))  # Barris
        pygame.draw.ellipse(surf_sombras, (12, 18, 14, 120), (cx_fogo - 55, cy_fogo + 20, 110, 28)) # Fogueira
        # Sombras dos assentos
        pygame.draw.ellipse(surf_sombras, (12, 18, 14, 95), (410, 412, 120, 22))
        pygame.draw.ellipse(surf_sombras, (12, 18, 14, 95), (765, 412, 120, 22))
        # Sombras dos 4 heróis no chão (sob os pés)
        pygame.draw.ellipse(surf_sombras, (12, 18, 14, 120), (455, 465, 50, 16))  # Sylvan
        pygame.draw.ellipse(surf_sombras, (12, 18, 14, 120), (755, 468, 48, 16))  # Halia
        pygame.draw.ellipse(surf_sombras, (12, 18, 14, 110), (695, 385, 52, 15))  # Roland
        pygame.draw.ellipse(surf_sombras, (12, 18, 14, 110), (540, 385, 48, 15))  # Caelen
        tela.blit(surf_sombras, (0, 0))

        # 1. Tendas Autênticas de Campanha de Explorador (Lona e Estacas)
        if self.spr_tenda_aframe:
            tela.blit(self.spr_tenda_aframe, (155, 275))
        if self.spr_tenda_lateral:
            tela.blit(self.spr_tenda_lateral, (890, 265))

        # Mochilas de couro e sacos de viagem
        if self.spr_mochila:
            tela.blit(self.spr_mochila, (295, 345))
            tela.blit(self.spr_mochila, (870, 335))

        # 2. Postes Rústicos com Lanternas de Latão Iluminadas
        if self.spr_poste_lanterna:
            tela.blit(self.spr_poste_lanterna, (320, 265))
            tela.blit(self.spr_poste_lanterna, (860, 260))

        # 3. Caixas de Provisões, Barris de Carvalho e Lenha
        if self.spr_lenha:
            tela.blit(self.spr_lenha, (365, 395))
        if self.spr_caixas:
            tela.blit(self.spr_caixas, (845, 388))
        if self.spr_barris:
            tela.blit(self.spr_barris, (910, 385))

        # 4. Assentos de Troncos Caídos Naturais (Logs) com mantas confortáveis
        if self.spr_tronco_longo:
            # Tronco de Sylvan com manta de pele
            tela.blit(self.spr_tronco_longo, (415, 385))
            pygame.draw.ellipse(tela, (110, 75, 45), (430, 388, 65, 16))
            pygame.draw.ellipse(tela, (145, 105, 65), (435, 390, 55, 12))

            # Tronco de Halia com manta azul índigo
            tela.blit(self.spr_tronco_longo, (770, 385))
            pygame.draw.ellipse(tela, (42, 60, 105), (780, 388, 65, 16))
            pygame.draw.ellipse(tela, (60, 85, 145), (785, 390, 55, 12))

        # Mesas rústicas de toco
        if self.spr_toco_mesa:
            tela.blit(self.spr_toco_mesa, (390, 415))  # Mesa de Sylvan
            tela.blit(self.spr_toco_mesa, (510, 335))  # Mesa de Caelen

        # 5. Anel de Pedras Naturais na Fogueira
        if self.spr_pedra:
            for angulo in range(0, 360, 30):
                rad = math.radians(angulo)
                px = cx_fogo + int(math.cos(rad) * 42) - 12
                py = cy_fogo + 20 + int(math.sin(rad) * 20) - 10
                tela.blit(self.spr_pedra, (px, py))

        # Leito de carvão em brasa incandescente no fundo
        pulso_brasa = 0.75 + 0.25 * math.sin(tempo_ms * 5.0)
        cor_brasa = (int(255 * pulso_brasa), int(80 * pulso_brasa), 15)
        pygame.draw.ellipse(tela, cor_brasa, (cx_fogo - 30, cy_fogo + 6, 60, 20))
        pygame.draw.ellipse(tela, (255, 185, 45), (cx_fogo - 18, cy_fogo + 10, 36, 12))

        # 6. Fogueira Animada Central
        if self.frames_fogo:
            idx_f = int(self.frame_fogo_idx) % len(self.frames_fogo)
            spr_fogo = pygame.transform.scale(self.frames_fogo[idx_f], (92, 102))
            tela.blit(spr_fogo, (cx_fogo - 46, cy_fogo - 62))
        else:
            pygame.draw.circle(tela, (255, 140, 20), (cx_fogo, cy_fogo), 32)

        # 7. Tripé de Ferro Forjado e Caldeirão de Chá de Ervas (de Caelen)
        self._desenhar_tripe_e_caldeirao(tela, cx_fogo, cy_fogo)

        # Fumaça da fogueira subindo em volutas translúcidas
        if self.frames_fumaca:
            idx_fum = int(self.frame_fumaca_idx) % len(self.frames_fumaca)
            spr_fum = pygame.transform.scale(self.frames_fumaca[idx_fum], (58, 140))
            surf_fum_alpha = spr_fum.copy()
            surf_fum_alpha.set_alpha(125)
            tela.blit(surf_fum_alpha, (cx_fogo - 29, cy_fogo - 170))

        # Animações de respiração suave (bob) dos quatro companheiros
        bob_sylvan = int(math.sin(tempo_ms * 2.6) * 1.5)
        bob_halia = int(math.sin(tempo_ms * 2.2 + 0.8) * 1.5)
        bob_roland = int(math.sin(tempo_ms * 2.0 + 1.6) * 1.2)
        bob_caelen = int(math.sin(tempo_ms * 2.3 + 2.4) * 1.2)

        # 8. Personagens Oficiais em Harmonia com o Acampamento
        # Roland (ao fundo à direita, vigilante com armadura de placas completa e espada)
        spr_rol = self.anim_roland.get_imagem() if self.anim_roland else self.spr_roland
        if spr_rol:
            tela.blit(spr_rol, (695, 305 + bob_roland))
            # Escudo de torre de Roland fincado no solo ao lado dele
            self._desenhar_escudo_roland(tela, 752, 335)

        # Caelen (ao fundo à esquerda, sereno zelando pelo chá e ervas medicinais)
        spr_cae = self.anim_caelen.get_imagem() if self.anim_caelen else self.spr_caelen
        if spr_cae:
            tela.blit(spr_cae, (540, 310 + bob_caelen))
            # Frascos de poção e ervas secando sobre a mesa de toco
            self._desenhar_ervas_e_pocoes_caelen(tela, 518, 338)

        # Sylvan (em primeiro plano à esquerda, descansando confortavelmente em frente ao seu banco de tronco)
        spr_syl = self.anim_sylvan.get_imagem() if self.anim_sylvan else self.spr_sylvan
        if spr_syl:
            tela.blit(spr_syl, (455, 385 + bob_sylvan))
            # Caneca de ferro com cerveja artesanal e vapor sobre a mesa
            self._desenhar_caneca_sylvan(tela, 400, 416)

        # Halia (em primeiro plano à direita, jovem maga acolhida no calor da chama)
        spr_hal = self.anim_halia.get_imagem() if self.anim_halia else self.spr_halia
        if spr_hal:
            tela.blit(spr_hal, (755, 382 + bob_halia))
            # Grimório aberto com runas luminescentes, cristal azul e bolsa de componentes
            self._desenhar_artefatos_halia(tela, 825, 410)

        # 9. Árvores de primeiro plano nas bordas (moldura viva da floresta, 100% verdes)
        for x, y, w, h, path, fl in self.arvores_moldura:
            spr = self.sprites_arvores.get((path, w, h, fl))
            if spr:
                tela.blit(spr, (x, y))

        # 10. Fauna noturna: Coruja vigilante empoleirada no galho alto do carvalho à esquerda
        self._desenhar_coruja(tela, 145, 150)

    def _desenhar_tripe_e_caldeirao(self, tela, cx, cy):
        """Renderiza tripé de ferro forjado e caldeirão com chá de ervas borbulhante."""
        ferro = (42, 45, 50)
        ferro_claro = (85, 90, 100)
        apex_x, apex_y = cx, cy - 72

        # Pernas do tripé
        pygame.draw.line(tela, ferro, (apex_x, apex_y), (cx - 38, cy + 20), 3)
        pygame.draw.line(tela, ferro, (apex_x, apex_y), (cx + 38, cy + 20), 3)
        pygame.draw.line(tela, (30, 32, 36), (apex_x, apex_y), (cx + 6, cy - 20), 2)
        # Anel de ferro superior
        pygame.draw.circle(tela, ferro_claro, (apex_x, apex_y), 4, width=2)

        # Corrente pendurada
        for y_link in range(apex_y + 4, cy - 42, 6):
            pygame.draw.ellipse(tela, ferro_claro, (cx - 2, y_link, 4, 6), width=1)

        # Alça e corpo do caldeirão de ferro
        pote_y = cy - 44
        pygame.draw.arc(tela, ferro_claro, (cx - 16, pote_y - 12, 32, 22), 0, math.pi, 2)
        # Panela esférica
        pygame.draw.ellipse(tela, (28, 30, 35), (cx - 20, pote_y, 40, 30))
        pygame.draw.ellipse(tela, (48, 52, 60), (cx - 20, pote_y, 40, 10))
        # Chá de ervas fervente verde-oliva com brilho
        pulso_cha = 0.5 + 0.5 * math.sin(self.tempo_cena * 4.0)
        cor_cha = (int(110 + 20 * pulso_cha), int(160 + 25 * pulso_cha), int(80 + 15 * pulso_cha))
        pygame.draw.ellipse(tela, cor_cha, (cx - 17, pote_y + 2, 34, 7))

        # Bolhinhas e vapor subindo do caldeirão
        for vp in self.vapor_caldeirao:
            ratio = max(0.0, min(1.0, vp["vida"] / max(0.1, vp.get("vida_max", 1.5))))
            alpha_v = int(120 * ratio)
            r_v = max(2, int(vp["raio"]))
            surf_vp = pygame.Surface((r_v * 2, r_v * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf_vp, (235, 245, 230, alpha_v), (r_v, r_v), r_v)
            tela.blit(surf_vp, (int(vp["x"]), int(vp["y"])))

    def _desenhar_escudo_roland(self, tela, x, y):
        """Renderiza escudo de torre de Roland fincado no solo com reflexos dourados."""
        pygame.draw.polygon(tela, (170, 185, 205), [
            (x, y), (x + 22, y), (x + 20, y + 36), (x + 11, y + 46), (x, y + 36)
        ])
        pygame.draw.polygon(tela, (225, 185, 55), [
            (x, y), (x + 22, y), (x + 20, y + 36), (x + 11, y + 46), (x, y + 36)
        ], width=2)
        pygame.draw.line(tela, (225, 185, 55), (x + 11, y + 6), (x + 11, y + 38), 3)
        pygame.draw.line(tela, (225, 185, 55), (x + 4, y + 15), (x + 18, y + 15), 3)
        pulso_reflexo = 0.5 + 0.5 * math.sin(self.tempo_cena * 4.5)
        pygame.draw.line(tela, (255, 230, 140, int(150 * pulso_reflexo)), (x + 2, y + 2), (x + 2, y + 34), 1)

    def _desenhar_ervas_e_pocoes_caelen(self, tela, x, y):
        """Renderiza frascos de poção e sementes de cura de Caelen sobre o toco."""
        pygame.draw.rect(tela, (80, 220, 120), (x + 4, y, 6, 8), border_radius=2)
        pygame.draw.line(tela, (180, 140, 90), (x + 5, y - 2), (x + 9, y - 2), 2)
        pygame.draw.rect(tela, (100, 180, 255), (x + 14, y + 2, 6, 7), border_radius=2)
        pygame.draw.line(tela, (180, 140, 90), (x + 15, y), (x + 19, y), 2)

    def _desenhar_caneca_sylvan(self, tela, x, y):
        """Renderiza caneca de ferro com cerveja artesanal e vapor waftando."""
        pygame.draw.rect(tela, (85, 92, 102), (x + 4, y, 12, 12), border_radius=2)
        pygame.draw.rect(tela, (215, 180, 50), (x + 4, y + 3, 12, 2))
        pygame.draw.arc(tela, (85, 92, 102), (x + 13, y + 2, 6, 8), -math.pi / 2, math.pi / 2, 2)
        pygame.draw.ellipse(tela, (250, 246, 230), (x + 3, y - 3, 14, 6))
        vy = y - 5 - int((self.tempo_cena * 15.0) % 12)
        pygame.draw.circle(tela, (240, 240, 245, 80), (x + 9, vy), 2)

    def _desenhar_artefatos_halia(self, tela, x, y):
        """Renderiza grimório aberto com runas luminescentes, cristal de mana e bolsa de componentes."""
        if self.spr_grimorio:
            tela.blit(self.spr_grimorio, (x - 10, y - 15))
        else:
            pygame.draw.rect(tela, (140, 50, 60), (x - 8, y - 6, 32, 20), border_radius=2)
            pygame.draw.rect(tela, (240, 235, 215), (x - 6, y - 4, 13, 16))
            pygame.draw.rect(tela, (240, 235, 215), (x + 9, y - 4, 13, 16))

        pulso_runa = 0.5 + 0.5 * math.sin(self.tempo_cena * 3.2)
        cor_runa = (int(90 + 80 * pulso_runa), int(210 + 45 * pulso_runa), 255)
        pygame.draw.line(tela, cor_runa, (x + 2, y - 4), (x + 12, y - 4), 2)
        pygame.draw.line(tela, cor_runa, (x + 2, y), (x + 10, y), 1)
        pygame.draw.line(tela, cor_runa, (x + 18, y - 4), (x + 26, y - 4), 2)
        pygame.draw.line(tela, cor_runa, (x + 18, y), (x + 24, y), 1)

        if self.spr_cristal_mana:
            tela.blit(self.spr_cristal_mana, (x + 26, y - 4))
        if self.spr_bolsa_componentes:
            tela.blit(self.spr_bolsa_componentes, (x - 28, y - 2))

    def _desenhar_coruja(self, tela, x, y):
        """Renderiza corujinha vigilante empoleirada no galho alto com olhos dourados brilhantes que piscam."""
        tempo = self.tempo_cena % 4.5
        piscando = (tempo > 3.8 and tempo < 4.05)
        bob = int(math.sin(self.tempo_cena * 2.0) * 1.0)

        pygame.draw.line(tela, (55, 42, 32), (x - 20, y + 26), (x + 28, y + 22), 5)
        pygame.draw.line(tela, (75, 115, 60), (x - 14, y + 24), (x - 2, y + 23), 2)

        pygame.draw.circle(tela, (220, 180, 50), (x - 3, y + 23), 2)
        pygame.draw.circle(tela, (220, 180, 50), (x + 7, y + 22), 2)

        cor_plumagem = (50, 42, 36)
        cor_peito = (175, 155, 130)
        pygame.draw.ellipse(tela, cor_plumagem, (x - 10, y + 6 + bob, 24, 20))
        pygame.draw.ellipse(tela, cor_peito, (x - 5, y + 10 + bob, 14, 14))

        pygame.draw.circle(tela, cor_plumagem, (x + 2, y + 6 + bob), 10)
        pygame.draw.polygon(tela, cor_plumagem, [(x - 6, y + bob), (x - 3, y - 6 + bob), (x, y - 1 + bob)])
        pygame.draw.polygon(tela, cor_plumagem, [(x + 4, y - 1 + bob), (x + 7, y - 6 + bob), (x + 10, y + bob)])

        if piscando:
            pygame.draw.arc(tela, (220, 180, 60), (x - 4, y + 4 + bob, 5, 4), math.pi, 2 * math.pi, 2)
            pygame.draw.arc(tela, (220, 180, 60), (x + 3, y + 4 + bob, 5, 4), math.pi, 2 * math.pi, 2)
        else:
            pygame.draw.circle(tela, (245, 195, 45), (x - 2, y + 6 + bob), 4)
            pygame.draw.circle(tela, (245, 195, 45), (x + 6, y + 6 + bob), 4)
            pygame.draw.circle(tela, (20, 16, 14), (x - 2, y + 6 + bob), 2)
            pygame.draw.circle(tela, (20, 16, 14), (x + 6, y + 6 + bob), 2)
            tela.set_at((x - 1, y + 5 + bob), (255, 255, 255))
            tela.set_at((x + 7, y + 5 + bob), (255, 255, 255))

        pygame.draw.polygon(tela, (230, 160, 40), [(x + 1, y + 8 + bob), (x + 3, y + 8 + bob), (x + 2, y + 11 + bob)])

    def desenhar_camada_superior(self, tela):
        """Renderiza iluminação radial do fogo, vaga-lumes vivos, folhas ao vento e vinheta."""
        cx_fogo, cy_fogo = 640, 440
        pulso_flicker = 0.94 + 0.06 * (math.sin(self.tempo_cena * 4.6) + math.cos(self.tempo_cena * 2.8) * 0.5)

        # 1. Iluminação Dinâmica Quente Pré-Renderizada com Decaimento Suave Contínuo
        r_fogo = int(430 * pulso_flicker)
        surf_fogo_scaled = pygame.transform.scale(self._luz_fogo_suave, (r_fogo * 2, r_fogo * 2))
        tela.blit(surf_fogo_scaled, (cx_fogo - r_fogo, cy_fogo - r_fogo))

        # 2. Luzes das Lanternas dos Postes
        R_lamp = 110
        surf_lamp = pygame.transform.scale(self._luz_lanterna_suave, (R_lamp * 2, R_lamp * 2))
        tela.blit(surf_lamp, (320 + 18 - R_lamp, 265 + 35 - R_lamp))
        tela.blit(surf_lamp, (860 + 18 - R_lamp, 260 + 35 - R_lamp))

        # 3. Brasas e Fagulhas Subindo para a Noite
        for p in self.particulas_brasas:
            ratio = max(0.0, min(1.0, p["vida"] / max(0.1, p.get("vida_max", 2.4))))
            alpha_b = int(255 * ratio)
            raio = max(1, int(p["raio"]))
            surf_p = pygame.Surface((raio * 2, raio * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf_p, (*p["cor"], alpha_b), (raio, raio), raio)
            tela.blit(surf_p, (int(p["x"]), int(p["y"])))

        # 4. Enxame de Vaga-Lumes Vivos Flutuando pela Clareira
        for vl in self.vaga_lumes:
            alpha_vl = int(240 * vl.brilho)
            if alpha_vl > 15:
                raio_halo = int(9 * vl.brilho + 2)
                surf_h = pygame.Surface((raio_halo * 2, raio_halo * 2), pygame.SRCALPHA)
                pygame.draw.circle(surf_h, (*vl.cor, int(70 * vl.brilho)), (raio_halo, raio_halo), raio_halo)
                tela.blit(surf_h, (int(vl.x - raio_halo), int(vl.y - raio_halo)))
                pygame.draw.circle(tela, (255, 255, 255), (int(vl.x), int(vl.y)), 1)

        # 5. Folhas de outono voando com o vento
        if self.spr_folha:
            for f in self.folhas_vento:
                surf_f = pygame.transform.rotate(self.spr_folha, f.angulo)
                tela.blit(surf_f, (int(f.x), int(f.y)))

        # 6. Vinheta Nostálgica de Recordação nas Bordas
        tela.blit(self._vinheta_cache, (0, 0))

    def desenhar(self, tela):
        """Renderização do mapa completo em camadas polimórficas."""
        self.desenhar_camada_inferior(tela)
        self.desenhar_props(tela)
        self.desenhar_camada_superior(tela)
