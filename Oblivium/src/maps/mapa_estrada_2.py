# src/maps/mapa_estrada_2.py
import pygame
import random
import math
from src.maps.cenario_base import CenarioBase
from src.utils.resource_manager import ResourceManager
from src.utils.colors import CENARIO_GRAMA_CINZA, CENARIO_ESTRADA, COR_PEDRA_DESLIZAMENTO, COR_BORDA_PEDRA
from src.entities.elemento_cenario import ChamaIndependente


class MapaEstrada2(CenarioBase):
    """
    Representa o segundo trecho da Estrada Rural de Oblivium: O Desfiladeiro do Deslizamento.
    Cenário que retrata o colapso geológico: árvores tombadas, cascalho pela pista e
    a barricada de rochas que bloqueia a passagem para a Capital.
    
    Suporta:
    - Minigame e cutscene de Levitação Gravitacional com movimentação em tempo real,
      sombras tridimensionais, anéis rúnicos no solo e auras arcanas nas pedras.
    - Desobstrução por Bola de Fogo gerando chamas animadas permanentes no ambiente,
      marcas de fuligem e brasas crepitantes nas sprites oficiais do jogo.
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
        self.PEDRAS_ORIGINAIS = [
            pygame.Rect(1070, 245, 84, 75),
            pygame.Rect(1140, 280, 95, 85),
            pygame.Rect(1060, 325, 90, 80),
            pygame.Rect(1115, 385, 105, 95),
            pygame.Rect(1040, 395, 75, 65)
        ]
        # Posições-alvo desobstruídas nas margens norte e sul para o feitiço de levitação
        self.PEDRAS_ALVO_LEVITACAO = [
            pygame.Rect(1120, 175, 84, 75),  # Margem norte
            pygame.Rect(1205, 195, 95, 85),  # Margem norte recuada
            pygame.Rect(1210, 485, 90, 80),  # Margem sul recuada
            pygame.Rect(1125, 500, 105, 95), # Margem sul
            pygame.Rect(1045, 495, 75, 65)   # Margem sul
        ]

        self.pedras_deslizamento = [p.copy() for p in self.PEDRAS_ORIGINAIS]
        self.bloqueio_ativo = True
        self.tipo_desobstrucao = None

        # Estado da Magia de Levitação em Tempo Real
        self.levitacao_ativa = False
        self.levitacao_pct = 0.0
        self.timer_levitacao = 0.0
        self.particulas_levitacao = []
        self.particulas_impacto = []

        # Estado das Chamas de Fogo no Ambiente
        self.focos_fogo = []
        self.particulas_brasas = []
        self.manchas_fuligem = []

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

        # Poças d'Água Acumuladas
        self.pocas_agua = [
            (810, 330, "poca_grande_02"),
            (830, 270, "poca_pequena_01"),
            (850, 400, "poca_pequena_03"),
            (560, 360, "poca_media_01"),
            (420, 280, "poca_media_02"),
            (680, 290, "poca_ondulacao_01"),
            (690, 405, "poca_pequena_02"),
            (210, 335, "poca_grande_03"),
            (110, 400, "poca_media_03"),
            (150, 265, "poca_pequena_01"),
            (360, 385, "poca_mini_01"),
        ]

        self.timer_pocas = 0.0
        self.frame_poca_atual = 0

        super().__init__(game, largura_tela, altura_tela, nome="ESTRADA_2")

    def carregar_recursos(self):
        """Carrega e prepara chão, árvores, pedras e spritesheets de fogo para o ambiente."""
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

        # 6. Poças de Água Animadas
        p_pocas = "assets/cenario/pisos_externos/agua/pocas_agua"
        p_anim = f"{p_pocas}/animadas"
        self.sprites_pocas = {
            "poca_lagoa_01": ResourceManager.carregar_imagem(f"{p_pocas}/poca_agua_lagoa_01.png"),
            "poca_grande_02": ResourceManager.carregar_imagem(f"{p_pocas}/poca_agua_grande_02.png"),
            "poca_grande_03": ResourceManager.carregar_imagem(f"{p_pocas}/poca_agua_grande_03.png"),
            "poca_media_01": ResourceManager.carregar_imagem(f"{p_pocas}/poca_agua_media_01.png"),
            "poca_media_02": ResourceManager.carregar_imagem(f"{p_pocas}/poca_agua_media_02.png"),
            "poca_media_03": ResourceManager.carregar_imagem(f"{p_pocas}/poca_agua_media_03.png"),
            "poca_pequena_01": ResourceManager.carregar_imagem(f"{p_pocas}/poca_agua_pequena_01.png"),
            "poca_pequena_02": ResourceManager.carregar_imagem(f"{p_pocas}/poca_agua_pequena_02.png"),
            "poca_pequena_03": ResourceManager.carregar_imagem(f"{p_pocas}/poca_agua_pequena_03.png"),
            "poca_pequena_04": ResourceManager.carregar_imagem(f"{p_pocas}/poca_agua_pequena_04.png"),
            "poca_mini_01": ResourceManager.carregar_imagem(f"{p_pocas}/poca_agua_mini_01.png"),
            "poca_ondulacao_01": ResourceManager.carregar_imagem(f"{p_pocas}/poca_agua_ondulacao_01.png"),
        }

        self.anim_pocas = {}
        for chave in ["poca_grande_02", "poca_grande_03", "poca_media_01", "poca_media_02", "poca_pequena_02", "poca_ondulacao_01"]:
            frames = []
            nome_arq = f"poca_agua_{chave.replace('poca_', '')}"
            for fr in range(6):
                f_img = ResourceManager.carregar_imagem(f"{p_anim}/{nome_arq}_f{fr}.png")
                if f_img:
                    frames.append(f_img)
            if frames:
                self.anim_pocas[chave] = frames

        # 7. Sprites Oficiais de Fogo para a Bagunça no Ambiente
        self.sprites_chama_coluna = ResourceManager.carregar_frames_pasta("efeitos/fogo/chama_coluna_fogo")
        self.sprites_chama_fogueira = ResourceManager.carregar_frames_pasta("efeitos/fogo/chama_fogueira_larga")
        self.sprites_chama_braseiro = ResourceManager.carregar_frames_pasta("efeitos/fogo/chama_braseiro_medio")
        self.sprites_chama_pequeno = ResourceManager.carregar_frames_pasta("efeitos/fogo/chama_fogo_pequeno")
        self.sprites_chama_fagulhas = ResourceManager.carregar_frames_pasta("efeitos/fogo/chama_fagulhas_brasas")

    def inicializar_cenario(self):
        """Configura hitboxes e elementos do cenário."""
        self.hitboxes = []
        self.hitboxes.extend(self.barreiras_estrada)
        self.limite_oeste = pygame.Rect(0, 0, 20, self.altura_tela)
        self.hitboxes.append(self.limite_oeste)
        
        if self.bloqueio_ativo:
            self.hitboxes.extend(self.pedras_deslizamento)

        # Troncos em pé
        for x, y, w, h, _ in self.arvores_norte:
            self.hitboxes.append(pygame.Rect(x + (w // 2) - 16, y + h - 28, 32, 24))

        for x, y, w, h, _ in self.arvores_sul:
            self.hitboxes.append(pygame.Rect(x + (w // 2) - 16, y + h - 28, 32, 24))

        # Árvores tombadas
        self.hitboxes.append(pygame.Rect(930, 195, 110, 35))
        self.hitboxes.append(pygame.Rect(960, 445, 110, 35))

        self.itens_no_chao = []

    def restaurar_bloqueio(self):
        """Restaura as rochas de bloqueio originais e suas hitboxes."""
        self.bloqueio_ativo = True
        self.tipo_desobstrucao = None
        self.levitacao_ativa = False
        self.levitacao_pct = 0.0
        self.focos_fogo.clear()
        self.manchas_fuligem.clear()
        self.particulas_brasas.clear()
        self.particulas_impacto.clear()
        self.pedras_deslizamento = [p.copy() for p in self.PEDRAS_ORIGINAIS]
        self.inicializar_cenario()

    def atualizar_levitacao_minigame(self, progresso_pct, dt=0.016):
        """
        Atualiza em tempo real as pedras conforme o jogador clica no minigame.
        Se progresso cresce: pedras se erguem no ar e avançam para as margens.
        Se progresso diminui: pedras descem suavemente e voltam para o bloqueio.
        """
        self.levitacao_pct = max(0.0, min(1.0, progresso_pct))
        self.timer_levitacao += dt

        if self.levitacao_pct > 0.01:
            self.levitacao_ativa = True
            
            # Interpola a posição de cada rocha entre o bloqueio original e as margens desobstruídas
            for i in range(len(self.PEDRAS_ORIGINAIS)):
                orig = self.PEDRAS_ORIGINAIS[i]
                alvo = self.PEDRAS_ALVO_LEVITACAO[i]
                dest_rect = self.pedras_deslizamento[i]

                # Interpolação cúbica suave
                t = self.levitacao_pct
                dest_rect.x = int(orig.x + (alvo.x - orig.x) * t)
                dest_rect.y = int(orig.y + (alvo.y - orig.y) * t)

            # Emite partículas arcanas de antigravidade subindo do solo
            if random.random() < 0.60:
                p_alvo = random.choice(self.pedras_deslizamento)
                self.particulas_levitacao.append({
                    "x": p_alvo.centerx + random.uniform(-p_alvo.width // 2, p_alvo.width // 2),
                    "y": p_alvo.bottom + random.uniform(-4, 10),
                    "vy": random.uniform(-65.0, -35.0),
                    "vx": random.uniform(-10.0, 10.0),
                    "vida": random.uniform(0.6, 1.2),
                    "vida_max": 1.2,
                    "raio": random.uniform(2.0, 4.0),
                    "cor": random.choice([(90, 190, 255), (140, 220, 255), (180, 240, 255), (60, 140, 240)])
                })
        else:
            self.levitacao_ativa = False
            for i in range(len(self.PEDRAS_ORIGINAIS)):
                self.pedras_deslizamento[i] = self.PEDRAS_ORIGINAIS[i].copy()

    def desobstruir_estrada(self, tipo_magia="FOGO"):
        """
        Desobstrui a passagem pela magia escolhida:
        - FOGO: gera estilhaços, fuligem e múltiplos focos de fogo animados no ambiente.
        - LEVITAR: rochas assentam com firmeza e segurança nas margens.
        """
        self.bloqueio_ativo = False
        self.tipo_desobstrucao = tipo_magia
        self.levitacao_ativa = False

        for p in self.pedras_deslizamento:
            if p in self.hitboxes:
                self.hitboxes.remove(p)

        if tipo_magia == "FOGO":
            # Rochas fragmentadas e espalhadas pela explosão
            self.pedras_deslizamento = [
                pygame.Rect(1110, 430, 28, 20),
                pygame.Rect(1160, 440, 30, 22),
                pygame.Rect(1090, 450, 22, 16),
                pygame.Rect(1180, 220, 26, 18),
                pygame.Rect(1140, 200, 24, 16)
            ]

            # Manchas de fuligem e cinzas no solo da explosão
            self.manchas_fuligem = [
                (1060, 340, 75, 45),
                (980, 210, 50, 30),
                (1120, 430, 60, 36),
                (1100, 270, 40, 25),
                (1020, 390, 55, 32),
            ]

            # Focos de Fogo Reais e Independentes utilizando as novas sprites de chamas laranjas
            self.focos_fogo = [
                # Epicentro da explosão: fogueira larga e vigorosa
                ChamaIndependente(1055, 345, tipo="fogueira", escala=1.25, glow_base=48),
                # Na árvore tombada ao norte: coluna de fogo subindo
                ChamaIndependente(980, 215, tipo="coluna", escala=1.15, glow_base=42),
                # Nos escombros de pedras ao sul: braseiro crepitante
                ChamaIndependente(1120, 435, tipo="braseiro", escala=1.15, glow_base=38),
                # Labaredas na terra chamuscada
                ChamaIndependente(1095, 275, tipo="rasteira", escala=1.10, glow_base=34),
                ChamaIndependente(1025, 390, tipo="chao_larga", escala=1.10, glow_base=34),
                ChamaIndependente(1165, 375, tipo="chao_pequena", escala=1.15, glow_base=30),
            ]
        else:
            # LEVITAR: rochas assentam com firmeza e impacto sólido nas margens
            self.pedras_deslizamento = [p.copy() for p in self.PEDRAS_ALVO_LEVITACAO]
            self.focos_fogo.clear()

            # Efeito visual de impacto: puffs de poeira e terra no solo ao redor da base das pedras
            self.particulas_impacto.clear()
            for p in self.PEDRAS_ALVO_LEVITACAO:
                for _ in range(14):
                    ang = random.uniform(0, math.pi * 2)
                    vel = random.uniform(35.0, 105.0)
                    self.particulas_impacto.append({
                        "x": p.centerx + random.uniform(-p.width * 0.35, p.width * 0.35),
                        "y": p.bottom - random.uniform(0, 6),
                        "vx": math.cos(ang) * vel,
                        "vy": -abs(math.sin(ang) * vel * 0.55),
                        "vida": random.uniform(0.35, 0.70),
                        "vida_max": 0.70,
                        "raio": random.uniform(2.5, 5.5),
                        "cor": random.choice([(130, 120, 105), (160, 150, 135), (95, 90, 80), (180, 170, 150)])
                    })

            # Micro-tremor de impacto no solo para transmitir o peso das rochas pousando
            if hasattr(self.game, 'estados'):
                playing = self.game.estados.get("JOGANDO") or self.game.estados.get("playing")
                if playing and hasattr(playing, 'cutscene'):
                    playing.cutscene.timer_explosao = 8
            elif hasattr(self.game, 'cutscene_manager'):
                self.game.cutscene_manager.timer_explosao = 8

    def atualizar(self, dt=0.016):
        """Atualiza a água, poças, levitação contínua e chamas crepitantes."""
        # 1. Poças d'água
        self.timer_pocas += dt
        if self.timer_pocas >= 0.18:
            self.timer_pocas = 0.0
            self.frame_poca_atual = (self.frame_poca_atual + 1) % 6

        # 2. Partículas de Levitação Arcana
        vivas_lev = []
        for p in self.particulas_levitacao:
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            p["vida"] -= dt
            if p["vida"] > 0:
                vivas_lev.append(p)
        self.particulas_levitacao = vivas_lev

        # 3. Focos de Fogo Independentes e Autônomos
        for foco in self.focos_fogo:
            if hasattr(foco, 'atualizar'):
                foco.atualizar(dt)
            elif isinstance(foco, dict) and foco.get("frames"):
                foco["idx"] += foco.get("vel", 0.24)
                if foco["idx"] >= len(foco["frames"]):
                    foco["idx"] = 0.0

        # 4. Partículas de Impacto de Poeira e Terra no Solo
        vivas_imp = []
        for p in self.particulas_impacto:
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            p["vx"] *= 0.90
            p["vy"] *= 0.90
            p["vida"] -= dt
            if p["vida"] > 0:
                vivas_imp.append(p)
        self.particulas_impacto = vivas_imp

    def desenhar_camada_inferior(self, tela):
        """Renderiza chão, poças d'água, vegetação e marcas de fuligem."""
        if self.chao_completo:
            tela.blit(self.chao_completo, (0, 0))
        else:
            tela.fill(CENARIO_GRAMA_CINZA)
            pygame.draw.rect(tela, CENARIO_ESTRADA, self.area_estrada)

        # 1. Manchas de Fuligem e Queimado no chão da explosão
        for fx, fy, fw, fh in self.manchas_fuligem:
            surf_fuligem = pygame.Surface((fw, fh), pygame.SRCALPHA)
            pygame.draw.ellipse(surf_fuligem, (20, 18, 16, 175), (0, 0, fw, fh))
            pygame.draw.ellipse(surf_fuligem, (12, 10, 8, 215), (fw // 4, fh // 4, fw // 2, fh // 2))
            tela.blit(surf_fuligem, (fx - fw // 2, fy - fh // 2))

        # 2. Poças d'água com ondulações
        frame_poca = self.frame_poca_atual
        for px, py, chave in self.pocas_agua:
            frames = self.anim_pocas.get(chave)
            if frames:
                sprite = frames[frame_poca % len(frames)]
            else:
                sprite = self.sprites_pocas.get(chave)
            if sprite:
                tela.blit(sprite, (px, py))

        # 3. Vegetação e Cascalho
        for px, py, chave in self.vegetacao_margem:
            sprite = self.sprites_veg.get(chave)
            if sprite:
                tela.blit(sprite, (px, py))

        for px, py, chave in self.pedras_espalhadas:
            sprite = self.sprites_detritos.get(chave)
            if sprite:
                tela.blit(sprite, (px, py))

    def desenhar_props(self, tela):
        """Renderiza árvores, rochas (com levitação viva e auras) e chamas do ambiente."""
        # 1. Árvores em Pé
        for x, y, w, h, k in self.arvores_norte + self.arvores_sul:
            sprite = self.sprites_arvores.get(k)
            if sprite:
                tela.blit(sprite, (x, y))

        # 2. Árvores Caídas e Troncos Partidos
        for x, y, _, chave in self.arvores_caidas:
            sprite = self.sprites_caidas.get(chave)
            if sprite:
                tela.blit(sprite, (x, y))

        # 3. Rochas Ancestrais (com suporte a Levitação Arcana 2.5D)
        tempo = pygame.time.get_ticks() / 1000.0

        for i, pedra in enumerate(self.pedras_deslizamento):
            idx_sprite = i % len(self.sprites_rochas_grandes)
            sprite = self.sprites_rochas_grandes[idx_sprite]

            # Altitude gravitacional em tempo real
            if self.levitacao_ativa and self.levitacao_pct > 0.01:
                oscilacao = math.sin(tempo * 4.8 + i * 1.3) * 4.0
                altitude_z = int(self.levitacao_pct * 42.0 + oscilacao)
                alpha_aura = int(self.levitacao_pct * 195)
            else:
                altitude_z = 0
                alpha_aura = 0

            # 3.1. Sombra 2.5D no solo (encolhe e fica mais translúcida com a altitude)
            fator_sombra = max(0.25, 1.0 - (altitude_z / 65.0))
            sw = max(8, int(pedra.width * 0.9 * fator_sombra))
            sh = max(4, int(pedra.height * 0.35 * fator_sombra))
            surf_sombra = pygame.Surface((sw, sh), pygame.SRCALPHA)
            alpha_sombra = int(140 * fator_sombra)
            pygame.draw.ellipse(surf_sombra, (15, 18, 22, alpha_sombra), (0, 0, sw, sh))
            tela.blit(surf_sombra, (pedra.centerx - sw // 2, pedra.bottom - sh // 2))

            # 3.2. Círculo Rúnico e Anéis de Gravidade no Solo
            if self.levitacao_ativa and alpha_aura > 10:
                raio_runa = int((pedra.width // 2 + 8) * self.levitacao_pct)
                if raio_runa > 4:
                    surf_runa = pygame.Surface((raio_runa * 2 + 10, raio_runa + 10), pygame.SRCALPHA)
                    cx, cy = raio_runa + 5, (raio_runa + 10) // 2
                    
                    # Anel externo e interno com pulso luminoso azul-celeste
                    cor_runa = (80, 185, 255, int(alpha_aura * 0.75))
                    cor_brilho = (170, 230, 255, int(alpha_aura * 0.90))
                    pygame.draw.ellipse(surf_runa, cor_runa, (cx - raio_runa, cy - raio_runa // 2, raio_runa * 2, raio_runa), 2)
                    pygame.draw.ellipse(surf_runa, cor_brilho, (cx - raio_runa + 4, cy - (raio_runa // 2) + 2, (raio_runa - 4) * 2, raio_runa - 4), 1)
                    
                    tela.blit(surf_runa, (pedra.centerx - cx, pedra.bottom - cy))

            # 3.3. Aura e Glow Luminoso ao Redor da Rocha em Levitação
            if self.levitacao_ativa and alpha_aura > 15:
                margem_glow = 18
                gw = pedra.width + margem_glow * 2
                gh = pedra.height + margem_glow * 2
                surf_glow = pygame.Surface((gw, gh), pygame.SRCALPHA)
                
                # Halo pulsante arcano
                pulso = (math.sin(tempo * 6.0 + i) + 1.0) * 0.5
                alpha_glow = int((120 + pulso * 70) * self.levitacao_pct)
                pygame.draw.ellipse(surf_glow, (60, 150, 255, alpha_glow // 2), (0, 0, gw, gh))
                pygame.draw.ellipse(surf_glow, (140, 215, 255, alpha_glow), (margem_glow // 2, margem_glow // 2, gw - margem_glow, gh - margem_glow))
                
                tela.blit(surf_glow, (pedra.x - margem_glow, (pedra.y - altitude_z) - margem_glow))

            # 3.4. Desenho da Rocha
            pos_rocha = (pedra.x, pedra.y - altitude_z)
            if sprite:
                img_escalada = pygame.transform.scale(sprite, (pedra.width, pedra.height))
                tela.blit(img_escalada, pos_rocha)
            else:
                rect_flutuante = pygame.Rect(pos_rocha[0], pos_rocha[1], pedra.width, pedra.height)
                pygame.draw.rect(tela, COR_PEDRA_DESLIZAMENTO, rect_flutuante)
                pygame.draw.rect(tela, COR_BORDA_PEDRA, rect_flutuante, 2)

        # 4. Partículas Arcanas Ascendentes da Levitação
        for p in self.particulas_levitacao:
            prog_vida = max(0.0, p["vida"] / p["vida_max"])
            raio = max(1, int(p["raio"] * prog_vida))
            alpha_p = int(220 * prog_vida)
            cor = (*p["cor"][:3], alpha_p)
            surf_p = pygame.Surface((raio * 2, raio * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf_p, cor, (raio, raio), raio)
            tela.blit(surf_p, (int(p["x"] - raio), int(p["y"] - raio)))

        # 4.1. Partículas de Impacto de Poeira e Terra no Solo (Pouso da Levitação)
        for p in self.particulas_impacto:
            pct_p = max(0.0, p["vida"] / p["vida_max"])
            raio_p = max(1, int(p["raio"] * pct_p))
            alpha_p = int(180 * pct_p)
            surf_p = pygame.Surface((raio_p * 2, raio_p * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf_p, (*p["cor"][:3], alpha_p), (raio_p, raio_p), raio_p)
            tela.blit(surf_p, (int(p["x"] - raio_p), int(p["y"] - raio_p)))

        # 5. Focos de Fogo no Ambiente (Chamas Reais e Independentes)
        for foco in self.focos_fogo:
            if hasattr(foco, 'desenhar'):
                foco.desenhar(tela)
            elif isinstance(foco, dict) and foco.get("frames"):
                idx = int(foco.get("idx", 0)) % len(foco["frames"])
                frame_chama = foco["frames"][idx]
                tela.blit(frame_chama, (foco["x"], foco["y"]))
