# src/ui/hud.py
import pygame
import math
import os
from src.utils.colors import UI_FUNDO_PADRAO, CINZA_CLARO, UI_TEXTO_DESTAQUE, UI_TEXTO_APAGADO, AMULETO_COR_FASE_1, AMULETO_COR_FASE_2, AMULETO_COR_FASE_3, AMULETO_COR_FASE_4, AMULETO_COR_FASE_5, AMULETO_COR_FASE_6, AMULETO_COR_FASE_7
from src.utils.resource_manager import ResourceManager

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
        self.fase_atual_amuleto = 1 
        self.memorias_coletadas = 0 # Quantas partes da memória foram ativadas (0 a 7)
        
        # --- SUPORTE A SPRITES ---
        self.sprite_bolsa = None
        self.sprite_memorias = None

        # --- CONTROLE DE TRANSPARÊNCIA (FADE POR PROXIMIDADE) ---
        self.alpha_atual = 255

    def carregar_sprite_fase(self, caminho_imagem):
        """Atualiza a sprite do círculo de memórias conforme avança de fase."""
        if os.path.exists(caminho_imagem):
            self.sprite_memorias = pygame.image.load(caminho_imagem).convert_alpha()
            self.sprite_memorias = pygame.transform.scale(self.sprite_memorias, (80, 80))
        else:
            self.sprite_memorias = None

    def desenhar(self, tela, game):
        """Desenha o HUD completo verificando transições, flashbacks e proximidade da Halia."""
        
        # 1. Oculta automaticamente se houver transição ou flashback ativo
        if hasattr(game, 'transicao') and game.transicao.estado != "INATIVO":
            return
        if hasattr(game, 'flashback_sistema') and game.flashback_sistema.estado != "INATIVO":
            return

        halia = getattr(game, 'halia', None)
        if not halia:
            return

        # 2. Zonas de Proximidade para Transparência Dinâmica
        # Zona superior esquerda (Caixa de Status + Amuleto) e Zona inferior direita (Bolsa)
        zona_topo_esq = pygame.Rect(20, 20, 450, 130)
        zona_bolsa = pygame.Rect(self.largura - 110, self.altura - 110, 100, 100)
        
        rect_halia = pygame.Rect(
            int(getattr(halia, 'x', 0)), 
            int(getattr(halia, 'y', 0)), 
            getattr(halia, 'largura', 40), 
            getattr(halia, 'altura', 40)
        )

        perto_hud = rect_halia.colliderect(zona_topo_esq.inflate(60, 60)) or rect_halia.colliderect(zona_bolsa.inflate(60, 60))
        alvo_alpha = 40 if perto_hud else 255

        if self.alpha_atual < alvo_alpha:
            self.alpha_atual = min(alvo_alpha, self.alpha_atual + 20)
        elif self.alpha_atual > alvo_alpha:
            self.alpha_atual = max(alvo_alpha, self.alpha_atual - 20)

        surface_hud = pygame.Surface((self.largura, self.altura), pygame.SRCALPHA)

        # --- DADOS REAIS DA PERSONAGEM ---
        nome_personagem = getattr(halia, 'nome', 'Halia')
        vida_atual = getattr(halia, 'vida_atual', 100)
        vida_maxima = getattr(halia, 'vida_maxima', 100)
        mana_atual = getattr(halia, 'mana_atual', 50)
        mana_maxima = getattr(halia, 'mana_maxima', 50)


        largura_caixa = 280
        altura_caixa = 95
        x_caixa = 30
        y_caixa = 30
        
        pygame.draw.rect(surface_hud, UI_FUNDO_PADRAO, (x_caixa, y_caixa, largura_caixa, altura_caixa))
        pygame.draw.rect(surface_hud, CINZA_CLARO, (x_caixa, y_caixa, largura_caixa, altura_caixa), 2)
        
        # Nome da Personagem
        txt_nome = self.fonte_nome.render(nome_personagem, True, UI_TEXTO_DESTAQUE)
        surface_hud.blit(txt_nome, (x_caixa + 20, y_caixa + 12))
        
        # Textos Indicativos (Vida / Mana)
        txt_vida = self.fonte_pequena.render("Vida", True, UI_TEXTO_APAGADO)
        txt_mana = self.fonte_pequena.render("Mana", True, UI_TEXTO_APAGADO)
        surface_hud.blit(txt_vida, (x_caixa + 20, y_caixa + 45))
        surface_hud.blit(txt_mana, (x_caixa + 20, y_caixa + 67))
        
        razao_vida = max(0, min(1, vida_atual / vida_maxima)) if vida_maxima > 0 else 0
        razao_mana = max(0, min(1, mana_atual / mana_maxima)) if mana_maxima > 0 else 0
        
        # Barra de Vida (Automatizada)
        pygame.draw.rect(surface_hud, (60, 10, 10), (x_caixa + 70, y_caixa + 48, 180, 10))
        pygame.draw.rect(surface_hud, (200, 40, 50), (x_caixa + 70, y_caixa + 48, int(180 * razao_vida), 10))
        
        # Barra de Mana (Automatizada)
        pygame.draw.rect(surface_hud, (10, 20, 60), (x_caixa + 70, y_caixa + 70, 180, 10))
        pygame.draw.rect(surface_hud, (50, 130, 210), (x_caixa + 70, y_caixa + 70, int(180 * razao_mana), 10))

        # 4. AMULETO DE MEMÓRIAS
        cx_memorias = x_caixa + largura_caixa + 50
        cy_memorias = y_caixa + (altura_caixa // 2)
        
        if self.sprite_memorias:
            ret_img = self.sprite_memorias.get_rect(center=(cx_memorias, cy_memorias))
            surface_hud.blit(self.sprite_memorias, ret_img.topleft)
        else:
            self._desenhar_amuleto_7_fases(surface_hud, cx_memorias, cy_memorias, self.memorias_coletadas, self.fase_atual_amuleto)

        # 5. ÍCONE DA BOLSA
        if self.sprite_bolsa:
            surface_hud.blit(self.sprite_bolsa, self.rect_bolsa.topleft)
        else:
            pygame.draw.rect(surface_hud, UI_FUNDO_PADRAO, self.rect_bolsa)
            pygame.draw.rect(surface_hud, CINZA_CLARO, self.rect_bolsa, 2)
            
            inner_rect = pygame.Rect(self.rect_bolsa.x + 12, self.rect_bolsa.y + 12, 36, 36)
            pygame.draw.rect(surface_hud, (30, 30, 35), inner_rect)
            pygame.draw.rect(surface_hud, CINZA_CLARO, inner_rect, 1)

            pygame.draw.rect(surface_hud, UI_TEXTO_DESTAQUE, (self.rect_bolsa.centerx - 6, self.rect_bolsa.y + 12, 12, 8), 1)
            pygame.draw.rect(surface_hud, UI_TEXTO_DESTAQUE, (self.rect_bolsa.centerx - 4, self.rect_bolsa.centery - 2, 8, 10), 1)

        # Aplica a transparência final em toda a superfície do HUD e pinta na tela principal
        surface_hud.set_alpha(int(self.alpha_atual))
        tela.blit(surface_hud, (0, 0))

    def _desenhar_amuleto_7_fases(self, tela, cx, cy, atuais, fase):
        """Desenha o anel dividido em 7 partes, onde cada parte ativa possui a sua própria cor."""
        raio_externo = 40
        raio_interno = 16
        max_mem = 7  # Exatamente 7 divisões
        
        # Fundo e moldura circular geométrica
        pygame.draw.circle(tela, UI_FUNDO_PADRAO, (cx, cy), raio_externo)
        pygame.draw.circle(tela, CINZA_CLARO, (cx, cy), raio_externo, 2)
        pygame.draw.circle(tela, CINZA_CLARO, (cx, cy), raio_interno, 2)
        
        angulo_fatia = 360 / max_mem
        
        # Mapeia cada índice da fatia (1 a 7) à sua respetiva constante de cor
        cores_fases = {
            1: AMULETO_COR_FASE_1,
            2: AMULETO_COR_FASE_2,
            3: AMULETO_COR_FASE_3,
            4: AMULETO_COR_FASE_4,
            5: AMULETO_COR_FASE_5,
            6: AMULETO_COR_FASE_6,
            7: AMULETO_COR_FASE_7
        }
        
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
            
            # Se a fatia estiver ativa, pinta com a cor específica daquela parte (i + 1)
            if i < atuais:
                cor_fatia = cores_fases.get(i + 1, (200, 200, 200))
                pygame.draw.polygon(tela, cor_fatia, pontos)
            else:
                # Fatia inativa (escura)
                pygame.draw.polygon(tela, (30, 30, 35), pontos)
            
            pygame.draw.polygon(tela, (10, 10, 12), pontos, 1)