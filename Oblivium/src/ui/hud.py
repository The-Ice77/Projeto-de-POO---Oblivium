# src/ui/hud.py
import pygame
import math
import os
from src.utils.colors import UI_FUNDO_PADRAO, CINZA_CLARO, UI_TEXTO_DESTAQUE, UI_TEXTO_APAGADO

class HUD:
    def __init__(self, largura_tela, altura_tela):
        self.largura = largura_tela
        self.altura = altura_tela
        
        # Fontes seguindo o padrão exato da DialogueBox
        self.fonte_nome = pygame.font.Font(None, 36) 
        self.fonte_pequena = pygame.font.Font(None, 22)
        
        # Hitbox da bolsa (cantos estritamente quadrados, alinhados à UI)
        self.rect_bolsa = pygame.Rect(self.largura - 90, self.altura - 90, 60, 60)
        
        # --- PROGRESSÃO DE FASES (1 a 7) ---
        # Altere esta variável (ou atualize via save/map_loader) conforme a fase atual do jogo
        self.fase_atual_amuleto = 1 
        self.memorias_coletadas = 0  # Quantas partes da memória foram ativadas (0 a 7)
        
        # --- SUPORTE A SPRITES ---
        self.sprite_bolsa = None
        self.sprite_memorias = None

    def carregar_sprite_fase(self, caminho_imagem):
        """Atualiza a sprite do círculo de memórias conforme avança de fase."""
        if os.path.exists(caminho_imagem):
            self.sprite_memorias = pygame.image.load(caminho_imagem).convert_alpha()
            self.sprite_memorias = pygame.transform.scale(self.sprite_memorias, (80, 80))
        else:
            self.sprite_memorias = None

    def desenhar(self, tela, halia):
        # 1. CAIXA DE STATUS (Bordas Retas / Quadradas) - fazer seguir a vida da personagem
        largura_caixa = 280
        altura_caixa = 95
        x_caixa = 30
        y_caixa = 30
        
        # Retângulos estritamente geométricos 
        pygame.draw.rect(tela, UI_FUNDO_PADRAO, (x_caixa, y_caixa, largura_caixa, altura_caixa))
        pygame.draw.rect(tela, CINZA_CLARO, (x_caixa, y_caixa, largura_caixa, altura_caixa), 2)
        
        # Nome da Personagem
        txt_nome = self.fonte_nome.render(halia.nome, True, UI_TEXTO_DESTAQUE)
        tela.blit(txt_nome, (x_caixa + 20, y_caixa + 12))
        
        # Textos Indicativos (Vida / Mana)
        txt_vida = self.fonte_pequena.render("Vida", True, UI_TEXTO_APAGADO)
        txt_mana = self.fonte_pequena.render("Mana", True, UI_TEXTO_APAGADO)
        tela.blit(txt_vida, (x_caixa + 20, y_caixa + 45))
        tela.blit(txt_mana, (x_caixa + 20, y_caixa + 67))
        
        razao_vida = getattr(halia, 'vida_atual', 100) / getattr(halia, 'vida_maxima', 100)
        razao_mana = getattr(halia, 'mana_atual', 50) / getattr(halia, 'mana_maxima', 50)
        
        # Barra de Vida (Quadrada)
        pygame.draw.rect(tela, (60, 10, 10), (x_caixa + 70, y_caixa + 48, 180, 10))
        pygame.draw.rect(tela, (200, 40, 50), (x_caixa + 70, y_caixa + 48, int(180 * razao_vida), 10))
        
        # Barra de Mana (Quadrada)
        pygame.draw.rect(tela, (10, 20, 60), (x_caixa + 70, y_caixa + 70, 180, 10))
        pygame.draw.rect(tela, (50, 130, 210), (x_caixa + 70, y_caixa + 70, int(180 * razao_mana), 10))

        # 2. AMULETO DE MEMÓRIAS (Exatamente 7 Fases / Etapas)

        cx_memorias = x_caixa + largura_caixa + 50
        cy_memorias = y_caixa + (altura_caixa // 2)
        
        if self.sprite_memorias:
            ret_img = self.sprite_memorias.get_rect(center=(cx_memorias, cy_memorias))
            tela.blit(self.sprite_memorias, ret_img.topleft)
        else:
            self._desenhar_amuleto_7_fases(tela, cx_memorias, cy_memorias, self.memorias_coletadas, self.fase_atual_amuleto)

       
        # 3. ÍCONE DA BOLSA (Estilo Geométrico / Quadrado)
       
        if self.sprite_bolsa:
            tela.blit(self.sprite_bolsa, self.rect_bolsa.topleft)
        else:
            pygame.draw.rect(tela, UI_FUNDO_PADRAO, self.rect_bolsa)
            pygame.draw.rect(tela, CINZA_CLARO, self.rect_bolsa, 2)
            
            inner_rect = pygame.Rect(self.rect_bolsa.x + 12, self.rect_bolsa.y + 12, 36, 36)
            pygame.draw.rect(tela, (30, 30, 35), inner_rect)
            pygame.draw.rect(tela, CINZA_CLARO, inner_rect, 1)

            pygame.draw.rect(tela, UI_TEXTO_DESTAQUE, (self.rect_bolsa.centerx - 6, self.rect_bolsa.y + 12, 12, 8), 1)
            pygame.draw.rect(tela, UI_TEXTO_DESTAQUE, (self.rect_bolsa.centerx - 4, self.rect_bolsa.centery - 2, 8, 10), 1)

    def _desenhar_amuleto_7_fases(self, tela, cx, cy, atuais, fase):
        """Desenha o anel dividido rigorosamente em 7 etapas/fases, sem preenchimento automático completo."""
        raio_externo = 40
        raio_interno = 16
        max_mem = 7  # Exatamente 7 fases / 7 divisões
        
        # Fundo e moldura circular geométrica
        pygame.draw.circle(tela, UI_FUNDO_PADRAO, (cx, cy), raio_externo)
        pygame.draw.circle(tela, CINZA_CLARO, (cx, cy), raio_externo, 2)
        pygame.draw.circle(tela, CINZA_CLARO, (cx, cy), raio_interno, 2)
        
        angulo_fatia = 360 / max_mem
        
        # Paletas de cores exclusivas para cada uma das 7 fases do jogo (fácil alteração) - a ser implementado e registrado no arquivo de cores
        cores_fases = {
            1: (90, 160, 210),   # Fase 1: Azul frio inicial
            2: (120, 190, 140),  # Fase 2: Verde musgo / aurora
            3: (210, 180, 90),   # Fase 3: Dourado pálido
            4: (220, 130, 80),   # Fase 4: Âmbar / Laranja
            5: (180, 90, 180),   # Fase 5: Roxo místico
            6: (220, 90, 110),   # Fase 6: Carmesim / Vermelho vivo
            7: (240, 240, 240)   # Fase 7: Branco puro / Despertar completo
        }
        
        cor_ativa = cores_fases.get(fase, (200, 200, 200))
        
        for i in range(max_mem):
            ang_inicial = math.radians(i * angulo_fatia - 90)
            ang_final = math.radians((i + 1) * angulo_fatia - 90)
            
            pontos = []
            for p in range(5):
                a = ang_inicial + (ang_final - ang_inicial) * (p / 4.0)
                pontos.append((cx + (raio_externo - 4) * math.cos(a), cy + (raio_externo - 4) * math.sin(a)))
            for p in range(4, -1, -1):
                a = ang_inicial + (ang_final - ang_inicial) * (p / 4.0)
                pontos.append((cx + (raio_interno + 4) * math.cos(a), cy + (raio_interno + 4) * math.sin(a)))
            
        
            if i < atuais:
                pygame.draw.polygon(tela, cor_ativa, pontos)
            else:

                pygame.draw.polygon(tela, (30, 30, 35), pontos)
            
            pygame.draw.polygon(tela, (10, 10, 12), pontos, 1)