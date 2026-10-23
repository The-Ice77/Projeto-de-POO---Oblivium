# src/mechanics/minigames.py
import pygame
import random
import math
from src.utils.colors import (
    CARVAO_PROFUNDO, CINZA_ARDOSIA, CINZA_LINHO, MARFIM_OFFWHITE,
    AZUL_HOVER_MENU, UI_TEXTO_APAGADO
)
from src.utils.resource_manager import ResourceManager
from src.ui.ui_utils import desenhar_painel_padrao
from src.core.audio_manager import AudioManager


def _tocar_sfx_seguro(alias):
    """Reproduz efeito sonoro com tolerância total a instâncias não inicializadas."""
    try:
        audio = AudioManager.get_instance()
        if audio and hasattr(audio, "tocar_sfx"):
            audio.tocar_sfx(alias)
    except Exception:
        pass


class MinigameTiming:
    """
    Minigame da Bola de Fogo - Ritual da Tríplice Fagulha (3 Tempos):
    - Etapa 1: Fagulha Inicial (Cursor em velocidade moderada, zona de queima generosa)
    - Etapa 2: Combustão Térmica (Cursor acelerado, zona intermediária com maior rastro)
    - Etapa 3: Ignição Plena Devastadora (Cursor veloz, zona de precisão no núcleo de calor)
    - Painel centralizado Dark Fantasy em Carvão Profundo
    - Suporte híbrido fluido a Teclado (Espaço/Enter/E) e Cliques do Mouse
    """
    ETAPAS_CONFIG = [
        {
            "etapa": 1,
            "nome": "Fagulha Inicial",
            "subtitulo": "✦ Etapa I: Desperte a Fagulha Elemental [1/3] ✦",
            "instrucao": "Sincronize o disparo no núcleo para acender as primeiras brasas",
            "velocidade": 7.5,
            "zona_min": 125,
            "zona_largura": 90,
            "cor_zona": (180, 85, 20),
            "cor_borda": (255, 195, 70),
            "cor_nucleo": (255, 215, 90),
        },
        {
            "etapa": 2,
            "nome": "Combustão Térmica",
            "subtitulo": "✦ Etapa II: Canalize a Combustão Térmica [2/3] ✦",
            "instrucao": "Alimente a chama aumentando a intensidade do calor",
            "velocidade": 11.0,
            "zona_min": 142,
            "zona_largura": 56,
            "cor_zona": (205, 70, 20),
            "cor_borda": (255, 170, 50),
            "cor_nucleo": (255, 220, 80),
        },
        {
            "etapa": 3,
            "nome": "Ignição Plena",
            "subtitulo": "✦ Etapa III: Ignição Plena Devastadora [3/3] ✦",
            "instrucao": "Momento Crítico! Detone a esfera ígnea no ápice da fusão",
            "velocidade": 14.5,
            "zona_min": 154,
            "zona_largura": 32,
            "cor_zona": (225, 55, 20),
            "cor_borda": (255, 235, 120),
            "cor_nucleo": (255, 245, 185),
        }
    ]

    def __init__(self, largura_tela, altura_tela):
        self.largura_tela = largura_tela
        self.altura_tela = altura_tela
        self.largura_painel = 480
        self.altura_painel = 190
        self.px = (largura_tela - self.largura_painel) // 2
        self.py = altura_tela - 220

        self.largura_barra = 350
        self.altura_barra = 26
        self.bx = self.px + (self.largura_painel - self.largura_barra) // 2
        self.by = self.py + 95

        self.cursor_x = 0.0
        self.cursor_dir = 1
        self.etapa_idx = 0
        self.flash_acerto = 0
        
        self.fonte_titulo = ResourceManager.carregar_fonte("sunday", 24)
        self.fonte_sub = ResourceManager.carregar_fonte("contrail", 15)
        self.fonte_instrucao = ResourceManager.carregar_fonte("contrail", 13)
        self.fonte_rodape = ResourceManager.carregar_fonte("contrail", 14)
        self.fonte_etapa = ResourceManager.carregar_fonte("contrail", 12)
        
        self.ativo = False
        self.fagulhas = []

    def iniciar(self):
        self.etapa_idx = 0
        self.cursor_x = 0.0
        self.cursor_dir = 1
        self.ativo = True
        self.fagulhas.clear()
        self.flash_acerto = 0

    @property
    def config_atual(self):
        return self.ETAPAS_CONFIG[self.etapa_idx]

    def atualizar(self):
        if not self.ativo: return
        
        cfg = self.config_atual
        vel = cfg["velocidade"]
        
        self.cursor_x += vel * self.cursor_dir
        if self.cursor_x >= self.largura_barra:
            self.cursor_x = float(self.largura_barra)
            self.cursor_dir = -1
        elif self.cursor_x <= 0:
            self.cursor_x = 0.0
            self.cursor_dir = 1

        if self.flash_acerto > 0:
            self.flash_acerto -= 1

        # Gera fagulhas de fogo e calor escaladas por etapa
        prob_fagulha = 0.35 + (self.etapa_idx * 0.20)
        if random.random() < prob_fagulha:
            self.fagulhas.append({
                "x": self.bx + self.cursor_x + random.uniform(-5, 5),
                "y": self.by + self.altura_barra // 2 + random.uniform(-6, 6),
                "vy": random.uniform(-2.2, -0.7),
                "vx": random.uniform(-1.0, 1.0),
                "vida": random.randint(15, 32),
                "cor": random.choice([(255, 215, 70), (255, 130, 30), (240, 60, 20)])
            })

        vivas = []
        for f in self.fagulhas:
            f["x"] += f["vx"]
            f["y"] += f["vy"]
            f["vida"] -= 1
            if f["vida"] > 0:
                vivas.append(f)
        self.fagulhas = vivas

    def checar_sucesso(self):
        """
        Executa tentativa de disparo na etapa atual do ritual.
        Retorna:
        - 'AVANCOU_ETAPA': se acertou a etapa 1 ou 2 (avança para a próxima).
        - 'VENCEU': se acertou a etapa 3 final (conclui o minigame).
        - 'PERDEU': se errou a zona de tempo.
        """
        if not self.ativo:
            return "PERDEU"

        cfg = self.config_atual
        z_min = cfg["zona_min"]
        z_max = z_min + cfg["zona_largura"]
        
        if z_min <= self.cursor_x <= z_max:
            # Acerto!
            self.flash_acerto = 18
            self._gerar_explosao_acerto()
            _tocar_sfx_seguro("magia_cast")

            if self.etapa_idx < len(self.ETAPAS_CONFIG) - 1:
                self.etapa_idx += 1
                self.cursor_dir *= -1  # Inverte a direção para imprimir dinamismo
                return "AVANCOU_ETAPA"
            else:
                self.ativo = False
                return "VENCEU"
        else:
            # Erro
            self.ativo = False
            _tocar_sfx_seguro("ataque_erro")
            return "PERDEU"

    def _gerar_explosao_acerto(self):
        """Cria estouro de fagulhas douradas ao sincronizar o disparo."""
        cx = self.bx + int(self.cursor_x)
        cy = self.by + self.altura_barra // 2
        for _ in range(16):
            ang = random.uniform(0, 2 * math.pi)
            spd = random.uniform(2.0, 6.0)
            self.fagulhas.append({
                "x": cx,
                "y": cy,
                "vx": math.cos(ang) * spd,
                "vy": math.sin(ang) * spd,
                "vida": random.randint(18, 35),
                "cor": random.choice([(255, 245, 160), (255, 195, 60), (255, 90, 20)])
            })

    def desenhar(self, tela):
        if not self.ativo: return
        
        cfg = self.config_atual
        rect_painel = pygame.Rect(self.px, self.py, self.largura_painel, self.altura_painel)
        desenhar_painel_padrao(tela, rect_painel, cor_fundo=CARVAO_PROFUNDO, cor_borda=CINZA_LINHO, alpha=248)

        # 1. Título Ígneo
        r_tit = self.fonte_titulo.render("✦ Conjuração: Bola de Fogo ✦", True, (255, 185, 80))
        tela.blit(r_tit, (rect_painel.centerx - r_tit.get_width() // 2, self.py + 14))

        # 2. Subtítulo e Instrução da Etapa
        r_sub = self.fonte_sub.render(cfg["subtitulo"], True, (255, 210, 120))
        tela.blit(r_sub, (rect_painel.centerx - r_sub.get_width() // 2, self.py + 40))

        r_inst = self.fonte_instrucao.render(cfg["instrucao"], True, CINZA_LINHO)
        tela.blit(r_inst, (rect_painel.centerx - r_inst.get_width() // 2, self.py + 58))

        # 3. Indicadores das 3 Etapas do Ritual
        x_etapas = rect_painel.centerx - 70
        y_etapas = self.py + 77
        for i in range(3):
            cx = x_etapas + (i * 70)
            if i < self.etapa_idx:
                # Concluída
                pygame.draw.circle(tela, (255, 195, 60), (cx, y_etapas), 6)
                pygame.draw.circle(tela, (255, 240, 160), (cx, y_etapas), 3)
            elif i == self.etapa_idx:
                # Atual (Pulsante)
                raio_p = 6 + int(math.sin(pygame.time.get_ticks() * 0.008) * 2)
                pygame.draw.circle(tela, (255, 110, 30), (cx, y_etapas), raio_p)
                pygame.draw.circle(tela, (255, 230, 120), (cx, y_etapas), 3)
            else:
                # Futura
                pygame.draw.circle(tela, (45, 45, 55), (cx, y_etapas), 5)
                pygame.draw.circle(tela, CINZA_ARDOSIA, (cx, y_etapas), 5, 1)

        # 4. Trilho da Barra
        rect_barra = pygame.Rect(self.bx, self.by, self.largura_barra, self.altura_barra)
        pygame.draw.rect(tela, (16, 16, 20), rect_barra, border_radius=3)
        pygame.draw.rect(tela, CINZA_ARDOSIA, rect_barra, 1, border_radius=3)

        # 5. Zona Alvo de Calor da Etapa
        z_min = cfg["zona_min"]
        z_w = cfg["zona_largura"]
        rect_alvo = pygame.Rect(self.bx + z_min, self.by + 2, z_w, self.altura_barra - 4)
        pygame.draw.rect(tela, cfg["cor_zona"], rect_alvo, border_radius=2)
        pygame.draw.rect(tela, cfg["cor_borda"], rect_alvo, 1, border_radius=2)
        
        # Núcleo concentrado no meio da zona
        n_w = max(10, z_w // 2)
        rect_nucleo = pygame.Rect(self.bx + z_min + (z_w - n_w) // 2, self.by + 5, n_w, self.altura_barra - 10)
        pygame.draw.rect(tela, cfg["cor_nucleo"], rect_nucleo, border_radius=1)

        # 6. Fagulhas procedurais
        for f in self.fagulhas:
            pygame.draw.circle(tela, f["cor"], (int(f["x"]), int(f["y"])), 2)

        # 7. Cursor Ígneo
        cx_c = self.bx + int(self.cursor_x)
        rect_cursor = pygame.Rect(cx_c - 3, self.by - 4, 6, self.altura_barra + 8)
        c_cor = (255, 255, 255) if self.flash_acerto > 0 else (255, 235, 180)
        pygame.draw.rect(tela, c_cor, rect_cursor, border_radius=2)
        pygame.draw.rect(tela, (255, 100, 30), rect_cursor, 1, border_radius=2)

        # 8. Rodapé Informativo
        r_rod = self.fonte_rodape.render("[ Pressione ESPAÇO ou CLIQUE para disparar no núcleo ]", True, UI_TEXTO_APAGADO)
        tela.blit(r_rod, (rect_painel.centerx - r_rod.get_width() // 2, self.py + self.altura_painel - 24))


class MinigameMash:
    """
    Minigame da Levitação Gravitacional com Quick Time Events (QTE Rítmico):
    - Canalização rítmica de Runas Arcanas gravitacionais (W, A, S, D, ESPAÇO)
    - Anel temporal de reação que decresce conforme o tempo esgota
    - Cada acerto eleva e desloca as pedras em tempo real no cenário físico de Estrada 2
    - Erro ou tempo esgotado faz as pedras oscilarem e perderem sustentação (-16% progresso)
    - Suporte híbrido a Teclado e Clique do Mouse
    """
    TECLAS_QTE = [
        {"id": "W", "keys": [pygame.K_w, pygame.K_UP], "rotulo": "W"},
        {"id": "A", "keys": [pygame.K_a, pygame.K_LEFT], "rotulo": "A"},
        {"id": "S", "keys": [pygame.K_s, pygame.K_DOWN], "rotulo": "S"},
        {"id": "D", "keys": [pygame.K_d, pygame.K_RIGHT], "rotulo": "D"},
        {"id": "ESPAÇO", "keys": [pygame.K_SPACE], "rotulo": "ESPAÇO"}
    ]

    def __init__(self, largura_tela, altura_tela):
        self.largura_tela = largura_tela
        self.altura_tela = altura_tela
        self.largura_painel = 480
        self.altura_painel = 215
        self.px = (largura_tela - self.largura_painel) // 2
        self.py = altura_tela - 235

        self.largura_barra = 350
        self.altura_barra = 22
        self.bx = self.px + (self.largura_painel - self.largura_barra) // 2
        self.by = self.py + 152

        self.progresso = 15.0
        self.tempo_limite = 85  # ~1.4s por comando
        self.tempo_restante = self.tempo_limite
        self.tecla_atual = self.TECLAS_QTE[0]
        self.seq_acertos = 0
        
        self.feedback_acerto = 0
        self.feedback_erro = 0
        self.shake_x = 0
        self.shake_y = 0
        
        self.fonte_titulo = ResourceManager.carregar_fonte("sunday", 24)
        self.fonte_sub = ResourceManager.carregar_fonte("contrail", 15)
        self.fonte_tecla = ResourceManager.carregar_fonte("sunday", 26)
        self.fonte_tecla_espaco = ResourceManager.carregar_fonte("contrail", 18)
        self.fonte_rodape = ResourceManager.carregar_fonte("contrail", 14)
        self.fonte_status = ResourceManager.carregar_fonte("contrail", 13)
        
        self.ativo = False
        self.orbes = []
        self.rect_glifo = pygame.Rect(0, 0, 0, 0)

    def iniciar(self):
        self.progresso = 15.0
        self.ativo = True
        self.orbes.clear()
        self.seq_acertos = 0
        self.feedback_acerto = 0
        self.feedback_erro = 0
        self.shake_x = 0
        self.shake_y = 0
        self._sortear_nova_tecla()
        self.tempo_restante = self.tempo_limite

    def _sortear_nova_tecla(self):
        candidatas = [t for t in self.TECLAS_QTE if t["id"] != self.tecla_atual["id"]]
        self.tecla_atual = random.choice(candidatas)

    def atualizar(self):
        if not self.ativo: return None
        
        if self.feedback_acerto > 0:
            self.feedback_acerto -= 1
        if self.feedback_erro > 0:
            self.feedback_erro -= 1
            self.shake_x = random.randint(-3, 3)
            self.shake_y = random.randint(-2, 2)
        else:
            self.shake_x = 0
            self.shake_y = 0

        # Inércia gravitacional sutil das rochas
        self.progresso = max(0.0, self.progresso - 0.07)
        
        # Temporizador de reação do QTE
        self.tempo_restante -= 1
        if self.tempo_restante <= 0:
            # Tempo expirou! As pedras perdem sustentação
            self.progresso = max(0.0, self.progresso - 16.0)
            self.feedback_erro = 14
            self.seq_acertos = 0
            self._sortear_nova_tecla()
            self.tempo_restante = self.tempo_limite
            _tocar_sfx_seguro("ataque_erro")
            
            if self.progresso <= 0.0:
                self.ativo = False
                return "PERDEU"

        # Orbes ascendentes de levitação
        if random.random() < 0.45:
            self.orbes.append({
                "x": self.bx + random.uniform(10, self.largura_barra - 10),
                "y": self.by + self.altura_barra + random.uniform(0, 8),
                "vy": random.uniform(-2.2, -0.9),
                "vx": random.uniform(-0.5, 0.5),
                "vida": random.randint(20, 40),
                "cor": random.choice([(140, 195, 255), (90, 150, 245), (180, 220, 255)])
            })

        vivas = []
        for o in self.orbes:
            o["x"] += o["vx"]
            o["y"] += o["vy"]
            o["vida"] -= 1
            if o["vida"] > 0:
                vivas.append(o)
        self.orbes = vivas

        if self.progresso >= 99.5:
            self.ativo = False
            return "VENCEU"
            
        if self.progresso <= 0.0:
            self.ativo = False
            return "PERDEU"
            
        return None

    def get_progresso_pct(self):
        """Retorna o percentual normalizado (0.0 a 1.0) para transladar as pedras no mapa."""
        if self.progresso >= 99.5:
            return 1.0
        return max(0.0, min(1.0, self.progresso / 100.0))

    def processar_evento(self, evento):
        """Processa comandos de teclado e cliques nos QTEs rítmicos."""
        if not self.ativo:
            return False

        if evento.type == pygame.KEYDOWN:
            if evento.key in self.tecla_atual["keys"]:
                return self._acertar_qte()
            elif evento.key in [pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d, pygame.K_SPACE,
                                pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT]:
                return self._errar_qte()
        elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            # Clique do mouse valida o impulso arcano no glifo
            return self._acertar_qte()

        return False

    def esmagar(self):
        """Mantido para compatibilidade retroativa com chamadas diretas."""
        if self.ativo:
            return self._acertar_qte()
        return None

    def _acertar_qte(self):
        """Executa acerto no comando do QTE."""
        self.progresso = min(100.0, self.progresso + 24.0)
        self.feedback_acerto = 15
        self.seq_acertos += 1
        _tocar_sfx_seguro("magia_cast")
        
        if self.progresso >= 99.5:
            self.ativo = False
            return "VENCEU"
            
        self._sortear_nova_tecla()
        # Tempo diminui sutilmente conforme o jogador emenda uma sequência perfeita
        self.tempo_restante = max(58, self.tempo_limite - (self.seq_acertos * 3))
        return "ACERTOU"

    def _errar_qte(self):
        """Executa erro no comando do QTE."""
        self.progresso = max(0.0, self.progresso - 16.0)
        self.feedback_erro = 14
        self.seq_acertos = 0
        _tocar_sfx_seguro("ataque_erro")
        
        if self.progresso <= 0.0:
            self.ativo = False
            return "PERDEU"
            
        self._sortear_nova_tecla()
        self.tempo_restante = self.tempo_limite
        return "ERROU"

    def desenhar(self, tela):
        if not self.ativo: return
        
        # Painel com efeito de tremor em caso de erro
        px = self.px + self.shake_x
        py = self.py + self.shake_y
        rect_painel = pygame.Rect(px, py, self.largura_painel, self.altura_painel)
        desenhar_painel_padrao(tela, rect_painel, cor_fundo=CARVAO_PROFUNDO, cor_borda=CINZA_LINHO, alpha=248)

        # 1. Título e Subtítulo Arcano
        r_tit = self.fonte_titulo.render("✦ Conjuração: Levitação Gravitacional ✦", True, AZUL_HOVER_MENU)
        tela.blit(r_tit, (rect_painel.centerx - r_tit.get_width() // 2, py + 14))

        r_sub = self.fonte_sub.render("✦ Sincronize as Runas de Condução Arcana ✦", True, CINZA_LINHO)
        tela.blit(r_sub, (rect_painel.centerx - r_sub.get_width() // 2, py + 40))

        # 2. GLIFO RÚNICO CENTRAL (QTE)
        cx_glifo = rect_painel.centerx
        cy_glifo = py + 95
        raio_anel = 33
        
        # Fundo do glifo
        cor_glifo_bg = (20, 24, 34)
        if self.feedback_acerto > 0:
            cor_glifo_bg = (35, 75, 120)
        elif self.feedback_erro > 0:
            cor_glifo_bg = (70, 25, 30)
        pygame.draw.circle(tela, cor_glifo_bg, (cx_glifo, cy_glifo), raio_anel)
        
        # Anel de contorno base
        pygame.draw.circle(tela, (45, 55, 75), (cx_glifo, cy_glifo), raio_anel, 2)

        # Anel Temporal Dinâmico (Arco que esvazia com o tempo)
        razao_tempo = max(0.0, min(1.0, self.tempo_restante / self.tempo_limite))
        if razao_tempo > 0.05:
            # Cor do anel: Azul celeste se tempo bom, Âmbar se tempo acabando
            cor_anel = (140, 215, 255) if razao_tempo > 0.40 else (255, 180, 70)
            if self.feedback_acerto > 0:
                cor_anel = (220, 245, 255)
            
            rect_arco = pygame.Rect(cx_glifo - raio_anel, cy_glifo - raio_anel, raio_anel * 2, raio_anel * 2)
            ang_fim = (math.pi / 2)
            ang_ini = ang_fim - (2 * math.pi * razao_tempo)
            try:
                pygame.draw.arc(tela, cor_anel, rect_arco, ang_ini, ang_fim, 3)
            except Exception:
                pass

        # Caixa de Tecla Estilizada
        rotulo = self.tecla_atual["rotulo"]
        w_btn = 68 if rotulo == "ESPAÇO" else 42
        h_btn = 38
        self.rect_glifo = pygame.Rect(cx_glifo - w_btn // 2, cy_glifo - h_btn // 2, w_btn, h_btn)
        
        cor_btn_bg = (26, 32, 46) if self.feedback_erro == 0 else (90, 25, 30)
        cor_btn_borda = (160, 205, 240) if self.feedback_acerto == 0 else (255, 255, 255)
        pygame.draw.rect(tela, cor_btn_bg, self.rect_glifo, border_radius=4)
        pygame.draw.rect(tela, cor_btn_borda, self.rect_glifo, 1, border_radius=4)

        # Texto da Tecla
        fonte_usar = self.fonte_tecla_espaco if rotulo == "ESPAÇO" else self.fonte_tecla
        cor_texto = MARFIM_OFFWHITE if self.feedback_acerto == 0 else (220, 245, 255)
        r_tecla = fonte_usar.render(rotulo, True, cor_texto)
        tela.blit(r_tecla, (self.rect_glifo.centerx - r_tecla.get_width() // 2, self.rect_glifo.centery - r_tecla.get_height() // 2))

        # 3. Orbes ascendentes de levitação
        for o in self.orbes:
            pygame.draw.circle(tela, o["cor"], (int(o["x"]), int(o["y"])), 2)

        # 4. Trilho da Barra de Sustentação
        bx = self.bx + self.shake_x
        by = self.by + self.shake_y
        rect_barra = pygame.Rect(bx, by, self.largura_barra, self.altura_barra)
        pygame.draw.rect(tela, (16, 16, 20), rect_barra, border_radius=3)
        pygame.draw.rect(tela, CINZA_ARDOSIA, rect_barra, 1, border_radius=3)

        # 5. Preenchimento de Energia Arcana
        pct = max(0.0, min(1.0, self.progresso / 100.0))
        w_fill = int(self.largura_barra * pct)
        if w_fill > 0:
            rect_fill = pygame.Rect(bx + 2, by + 2, max(4, w_fill - 4), self.altura_barra - 4)
            pygame.draw.rect(tela, (45, 110, 195), rect_fill, border_radius=2)
            
            # Crista luminosa da barra
            rect_crista = pygame.Rect(rect_fill.right - 3, by + 2, 3, self.altura_barra - 4)
            pygame.draw.rect(tela, (180, 225, 255), rect_crista, border_radius=1)

        # 6. Indicador de Percentual
        r_pct = self.fonte_status.render(f"{int(self.progresso)}%", True, MARFIM_OFFWHITE)
        tela.blit(r_pct, (bx + self.largura_barra + 10, by + 3))

        # 7. Rodapé Informativo
        r_rod = self.fonte_rodape.render("[ Pressione a tecla da Runa antes que o tempo esgote ]", True, UI_TEXTO_APAGADO)
        tela.blit(r_rod, (rect_painel.centerx - r_rod.get_width() // 2, py + self.altura_painel - 22))