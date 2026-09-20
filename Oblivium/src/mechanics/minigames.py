# src/mechanics/minigames.py
import pygame
import math
import random
from src.utils.colors import (
    CARVAO_PROFUNDO, CINZA_ARDOSIA, CINZA_LINHO, MARFIM_OFFWHITE,
    AZUL_HOVER_MENU, AZUL_HOVER_BG, DOURADO_ENVELHECIDO, UI_TEXTO_APAGADO
)
from src.utils.resource_manager import ResourceManager
from src.ui.ui_utils import desenhar_painel_padrao

class MinigameTiming:
    """
    Minigame da Bola de Fogo:
    - Painel centralizado em Carvão Profundo com contornos elegantes
    - Zona alvo ígnea em âmbar/dourado com efeito de núcleo de calor
    - Cursor de fogo com rastro e fagulhas procedurais
    - Suporte a Teclado (Espaço/Enter/E) e Clique do Mouse
    """
    def __init__(self, largura_tela, altura_tela):
        self.largura_tela = largura_tela
        self.altura_tela = altura_tela
        self.largura_painel = 460
        self.altura_painel = 160
        self.px = (largura_tela - self.largura_painel) // 2
        self.py = altura_tela - 190

        self.largura_barra = 340
        self.altura_barra = 26
        self.bx = self.px + (self.largura_painel - self.largura_barra) // 2
        self.by = self.py + 75

        self.cursor_x = 0.0
        self.cursor_dir = 1
        self.velocidade_cursor = 8.5
        
        self.fonte_titulo = ResourceManager.carregar_fonte("sunday", 24)
        self.fonte_sub = ResourceManager.carregar_fonte("contrail", 15)
        self.fonte_rodape = ResourceManager.carregar_fonte("contrail", 14)
        
        self.ativo = False
        self.fagulhas = []

    def iniciar(self):
        self.cursor_x = 0.0
        self.cursor_dir = 1
        self.ativo = True
        self.fagulhas.clear()

    def atualizar(self):
        if not self.ativo: return
        
        self.cursor_x += self.velocidade_cursor * self.cursor_dir
        if self.cursor_x >= self.largura_barra:
            self.cursor_x = float(self.largura_barra)
            self.cursor_dir = -1
        elif self.cursor_x <= 0:
            self.cursor_x = 0.0
            self.cursor_dir = 1

        # Gera fagulhas de fogo ao redor do cursor
        if random.random() < 0.4:
            self.fagulhas.append({
                "x": self.bx + self.cursor_x + random.uniform(-4, 4),
                "y": self.by + self.altura_barra // 2 + random.uniform(-6, 6),
                "vy": random.uniform(-1.8, -0.6),
                "vx": random.uniform(-0.8, 0.8),
                "vida": random.randint(15, 30),
                "cor": random.choice([(255, 200, 60), (255, 120, 30), (240, 70, 20)])
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
        """Retorna True se o cursor acertou o núcleo ígneo (área dourada)."""
        zona_min = 135
        zona_max = 205
        sucesso = zona_min <= self.cursor_x <= zona_max
        self.ativo = False
        return sucesso

    def desenhar(self, tela):
        if not self.ativo: return
        
        rect_painel = pygame.Rect(self.px, self.py, self.largura_painel, self.altura_painel)
        desenhar_painel_padrao(tela, rect_painel, cor_fundo=CARVAO_PROFUNDO, cor_borda=CINZA_LINHO, alpha=245)

        # 1. Título e Instrução Ígnea
        r_tit = self.fonte_titulo.render("✦ Conjuração: Bola de Fogo ✦", True, (255, 180, 70))
        tela.blit(r_tit, (rect_painel.centerx - r_tit.get_width() // 2, self.py + 16))

        r_sub = self.fonte_sub.render("Dispare no núcleo ígneo para inflamar o obstáculo", True, CINZA_LINHO)
        tela.blit(r_sub, (rect_painel.centerx - r_sub.get_width() // 2, self.py + 46))

        # 2. Trilho da Barra
        rect_barra = pygame.Rect(self.bx, self.by, self.largura_barra, self.altura_barra)
        pygame.draw.rect(tela, (16, 16, 20), rect_barra, border_radius=3)
        pygame.draw.rect(tela, CINZA_ARDOSIA, rect_barra, 1, border_radius=3)

        # 3. Zona Alvo Dourada/Ígnea (Núcleo)
        rect_alvo = pygame.Rect(self.bx + 135, self.by + 2, 70, self.altura_barra - 4)
        pygame.draw.rect(tela, (180, 85, 20), rect_alvo, border_radius=2)
        pygame.draw.rect(tela, (255, 215, 90), rect_alvo, 1, border_radius=2)
        
        # Núcleo brilhante central
        rect_nucleo = pygame.Rect(self.bx + 155, self.by + 5, 30, self.altura_barra - 10)
        pygame.draw.rect(tela, (255, 210, 70), rect_nucleo, border_radius=1)

        # Fagulhas procedurais
        for f in self.fagulhas:
            pygame.draw.circle(tela, f["cor"], (int(f["x"]), int(f["y"])), 2)

        # 4. Cursor Ígneo
        cx = self.bx + int(self.cursor_x)
        rect_cursor = pygame.Rect(cx - 3, self.by - 4, 6, self.altura_barra + 8)
        pygame.draw.rect(tela, (255, 235, 180), rect_cursor, border_radius=2)
        pygame.draw.rect(tela, (255, 100, 30), rect_cursor, 1, border_radius=2)

        # 5. Rodapé Informativo
        r_rod = self.fonte_rodape.render("[ Pressione ESPAÇO para disparar ]", True, UI_TEXTO_APAGADO)
        tela.blit(r_rod, (rect_painel.centerx - r_rod.get_width() // 2, self.py + self.altura_painel - 24))


class MinigameMash:
    """
    Minigame da Levitação Gravitacional:
    - Painel em Carvão Profundo com energia etérea arcana
    - Barra de sustentação mágica azul etérea com pulso
    - Orbes arcanos procedurais flutuando para cima (antigravidade)
    - Operação exclusiva pela tecla ESPAÇO
    """
    def __init__(self, largura_tela, altura_tela):
        self.largura_tela = largura_tela
        self.altura_tela = altura_tela
        self.largura_painel = 460
        self.altura_painel = 165
        self.px = (largura_tela - self.largura_painel) // 2
        self.py = altura_tela - 190

        self.largura_barra = 340
        self.altura_barra = 26
        self.bx = self.px + (self.largura_painel - self.largura_barra) // 2
        self.by = self.py + 75

        self.progresso = 35.0
        self.decaimento = 0.35
        self.ganho_por_clique = 10.0
        
        self.fonte_titulo = ResourceManager.carregar_fonte("sunday", 24)
        self.fonte_sub = ResourceManager.carregar_fonte("contrail", 15)
        self.fonte_rodape = ResourceManager.carregar_fonte("contrail", 14)
        self.fonte_status = ResourceManager.carregar_fonte("contrail", 13)
        
        self.ativo = False
        self.orbes = []

    def iniciar(self):
        self.progresso = 35.0
        self.ativo = True
        self.orbes.clear()

    def atualizar(self):
        if not self.ativo: return None
        
        if self.progresso >= 100.0:
            self.ativo = False
            return "VENCEU"
            
        self.progresso -= self.decaimento
        
        # Orbes de levitação ascendentes (antigravidade)
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

        if self.progresso <= 0:
            self.ativo = False
            return "PERDEU"
        
        if self.progresso >= 99.5:
            self.ativo = False
            return "VENCEU"
            
        return None

    def esmagar(self):
        if self.ativo:
            self.progresso = min(100.0, self.progresso + self.ganho_por_clique)

    def desenhar(self, tela):
        if not self.ativo: return
        
        rect_painel = pygame.Rect(self.px, self.py, self.largura_painel, self.altura_painel)
        desenhar_painel_padrao(tela, rect_painel, cor_fundo=CARVAO_PROFUNDO, cor_borda=CINZA_LINHO, alpha=245)

        # 1. Título e Instrução Arcana
        r_tit = self.fonte_titulo.render("✦ Conjuração: Levitação Gravitacional ✦", True, AZUL_HOVER_MENU)
        tela.blit(r_tit, (rect_painel.centerx - r_tit.get_width() // 2, self.py + 16))

        r_sub = self.fonte_sub.render("Sustente o fluxo arcano para erguer os escombros", True, CINZA_LINHO)
        tela.blit(r_sub, (rect_painel.centerx - r_sub.get_width() // 2, self.py + 46))

        # Orbes de levitação
        for o in self.orbes:
            pygame.draw.circle(tela, o["cor"], (int(o["x"]), int(o["y"])), 2)

        # 2. Trilho da Barra
        rect_barra = pygame.Rect(self.bx, self.by, self.largura_barra, self.altura_barra)
        pygame.draw.rect(tela, (16, 16, 20), rect_barra, border_radius=3)
        pygame.draw.rect(tela, CINZA_ARDOSIA, rect_barra, 1, border_radius=3)

        # 3. Preenchimento de Energia Arcana
        pct = max(0.0, min(1.0, self.progresso / 100.0))
        w_fill = int(self.largura_barra * pct)
        if w_fill > 0:
            rect_fill = pygame.Rect(self.bx + 2, self.by + 2, max(4, w_fill - 4), self.altura_barra - 4)
            pygame.draw.rect(tela, (55, 110, 195), rect_fill, border_radius=2)
            
            # Linha de crista luminosa
            rect_crista = pygame.Rect(rect_fill.right - 3, self.by + 2, 3, self.altura_barra - 4)
            pygame.draw.rect(tela, (180, 225, 255), rect_crista, border_radius=1)

        # 4. Indicador de Percentual
        r_pct = self.fonte_status.render(f"{int(self.progresso)}%", True, MARFIM_OFFWHITE)
        tela.blit(r_pct, (self.bx + self.largura_barra + 10, self.by + 4))

        # 5. Rodapé Informativo
        r_rod = self.fonte_rodape.render("[ Pressione ESPAÇO repetidamente ]", True, UI_TEXTO_APAGADO)
        tela.blit(r_rod, (rect_painel.centerx - r_rod.get_width() // 2, self.py + self.altura_painel - 24))