# src/ui/hud.py
import pygame
import math
import os
from src.utils.colors import (
    UI_FUNDO_PADRAO, CINZA_CLARO, CINZA_LINHO, CINZA_ARDOSIA, CARVAO_PROFUNDO,
    MARFIM_OFFWHITE, BRANCO, BARRA_VIDA_JOGADOR, BARRA_MANA, BARRA_EXP,
    BARRA_FUNDO_ESCURO, BORDA_PADRAO, BORDA_DESTAQUE, AZUL_HOVER_MENU, AZUL_HOVER_BG,
    AMULETO_COR_FASE_1, AMULETO_COR_FASE_2, AMULETO_COR_FASE_3, AMULETO_COR_FASE_4,
    AMULETO_COR_FASE_5, AMULETO_COR_FASE_6, AMULETO_COR_FASE_7
)
from src.utils.resource_manager import ResourceManager
from src.ui.ui_utils import desenhar_barra_status_interpolada, desenhar_painel_padrao

class HUD:
    """
    HUD Simplificado e Focado de Oblivium:
    - Retrato de Halia com moldura sutil em carvão escuro
    - Nome de Halia em tipografia Sunday
    - Barras de HP (Carmim) e MP (Cerúleo) limpas com interpolação suave
    - Amuleto das 7 Fases de Memória na lateral do container
    - Botão da Bolsa no canto inferior direito com atalho [B] e hover azul etéreo
    - Fade dinâmico de proximidade quando Halia se aproxima
    """
    def __init__(self, largura_tela, altura_tela):
        self.largura = largura_tela
        self.altura = altura_tela
        
        # Fontes temáticas
        self.fonte_nome = ResourceManager.carregar_fonte("sunday", 24)
        self.fonte_status = ResourceManager.carregar_fonte("contrail", 14)
        self.fonte_slots = ResourceManager.carregar_fonte("contrail", 14)
        self.fonte_pequena = ResourceManager.carregar_fonte("contrail", 16)
        
        # Hitbox da bolsa no canto inferior direito
        self.rect_bolsa = pygame.Rect(self.largura - 110, self.altura - 110, 85, 85)
        self.hover_bolsa = False
        
        # --- PROGRESSÃO DE FASES (0 a 7) ---
        self.fase_atual_amuleto = 1 
        self.memorias_coletadas = 0
        
        # --- SUPORTE A SPRITES ---
        self.sprite_bolsa = ResourceManager.carregar_imagem("hud/Bolsa.png", (75, 75))
        self.sprite_halia = ResourceManager.carregar_imagem("Halia/halia_portrait.png", (52, 60))
        
        # Pré-carrega as 8 fases do amuleto
        self.sprites_memorias = {
            i: ResourceManager.carregar_imagem(f"hud/Sistema de Memórias - {i}.png", (72, 72))
            for i in range(8)
        }

        # --- CONTROLE DE TRANSPARÊNCIA (FADE POR PROXIMIDADE) ---
        self.alpha_atual = 255

    def atualizar_mouse(self, pos_mouse):
        """Atualiza estado de hover do mouse sobre elementos interativos do HUD."""
        self.hover_bolsa = self.rect_bolsa.collidepoint(pos_mouse)

    def desenhar(self, tela, game):
        """Desenha o HUD completo verificando transições, flashbacks e proximidade da Halia."""
        
        halia = getattr(game, 'halia', None)
        if halia:
            self.memorias_coletadas = getattr(halia, 'fragmentos_memoria', 0)
            
        # 1. Oculta automaticamente se houver transição, flashback ou tela de despertar ativa
        if hasattr(game, 'transicao') and game.transicao.estado != "INATIVO":
            return
        if hasattr(game, 'flashback_sistema') and game.flashback_sistema.estado != "INATIVO":
            return
        if hasattr(game, 'tela_despertar') and game.tela_despertar.estado != "INATIVO":
            return

        if not halia:
            return

        # 2. Zonas de Proximidade para Transparência Dinâmica
        zona_topo_esq = pygame.Rect(20, 20, 420, 130)
        zona_bolsa = self.rect_bolsa.inflate(40, 40)
        
        rect_halia = pygame.Rect(
            int(getattr(halia, 'x', 0)), 
            int(getattr(halia, 'y', 0)), 
            getattr(halia, 'largura', 40), 
            getattr(halia, 'altura', 40)
        )

        perto_hud = rect_halia.colliderect(zona_topo_esq) or rect_halia.colliderect(zona_bolsa)
        alvo_alpha = 45 if perto_hud else 255

        if self.alpha_atual < alvo_alpha:
            self.alpha_atual = min(alvo_alpha, self.alpha_atual + 20)
        elif self.alpha_atual > alvo_alpha:
            self.alpha_atual = max(alvo_alpha, self.alpha_atual - 20)

        surface_hud = pygame.Surface((self.largura, self.altura), pygame.SRCALPHA)

        # --- DADOS DA PERSONAGEM ---
        nome_personagem = getattr(halia, 'nome', 'Halia')
        vida_atual = getattr(halia, 'vida_atual', 100)
        vida_maxima = max(1, getattr(halia, 'vida_maxima', 100))
        mana_atual = getattr(halia, 'mana_atual', 50)
        mana_maxima = max(1, getattr(halia, 'mana_maxima', 50))

        # 3. CONTAINER PRINCIPAL SUPERIOR ESQUERDO
        x_hud = 24
        y_hud = 20
        largura_painel = 310
        altura_painel = 78

        rect_painel = pygame.Rect(x_hud, y_hud, largura_painel, altura_painel)
        desenhar_painel_padrao(surface_hud, rect_painel, cor_fundo=CARVAO_PROFUNDO, cor_borda=CINZA_LINHO, alpha=240)

        # 3.1 Moldura e Retrato de Halia
        x_ret = x_hud + 9
        y_ret = y_hud + 9
        w_ret = 52
        h_ret = 60
        rect_retrato = pygame.Rect(x_ret, y_ret, w_ret, h_ret)
        pygame.draw.rect(surface_hud, (14, 14, 18), rect_retrato, border_radius=2)
        pygame.draw.rect(surface_hud, CINZA_ARDOSIA, rect_retrato, 1, border_radius=2)

        if self.sprite_halia:
            surface_hud.blit(self.sprite_halia, (x_ret + 1, y_ret + 1))
        else:
            f_ini = ResourceManager.carregar_fonte("sunday", 28)
            txt_ini = f_ini.render("H", True, MARFIM_OFFWHITE)
            surface_hud.blit(txt_ini, txt_ini.get_rect(center=rect_retrato.center))

        # 3.2 Nome e Barras de Status (HP e MP)
        x_conteudo = x_ret + w_ret + 14
        txt_nome = self.fonte_nome.render(nome_personagem, True, MARFIM_OFFWHITE)
        surface_hud.blit(txt_nome, (x_conteudo, y_hud + 8))

        # Barra de Vida (HP)
        y_hp = y_hud + 36
        w_barra = 150
        h_barra = 12
        desenhar_barra_status_interpolada(
            surface_hud, x_conteudo, y_hp, w_barra, h_barra,
            vida_atual, vida_maxima,
            BARRA_VIDA_JOGADOR, (50, 16, 18), BORDA_PADRAO
        )
        txt_hp_num = self.fonte_status.render(f"HP {int(vida_atual)}/{int(vida_maxima)}", True, MARFIM_OFFWHITE)
        surface_hud.blit(txt_hp_num, (x_conteudo + w_barra + 8, y_hp - 1))

        # Barra de Mana (MP)
        y_mp = y_hp + 19
        desenhar_barra_status_interpolada(
            surface_hud, x_conteudo, y_mp, w_barra, h_barra,
            mana_atual, mana_maxima,
            BARRA_MANA, (16, 26, 52), BORDA_PADRAO
        )
        txt_mp_num = self.fonte_status.render(f"MP {int(mana_atual)}/{int(mana_maxima)}", True, MARFIM_OFFWHITE)
        surface_hud.blit(txt_mp_num, (x_conteudo + w_barra + 8, y_mp - 1))

        # 4. AMULETO DE MEMÓRIAS (Ao lado do painel)
        cx_memorias = x_hud + largura_painel + 48
        cy_memorias = y_hud + (altura_painel // 2)
        
        sprite_memoria_atual = self.sprites_memorias.get(self.memorias_coletadas)
        if sprite_memoria_atual:
            ret_img = sprite_memoria_atual.get_rect(center=(cx_memorias, cy_memorias))
            surface_hud.blit(sprite_memoria_atual, ret_img.topleft)
        else:
            self._desenhar_amuleto_7_fases(surface_hud, cx_memorias, cy_memorias, self.memorias_coletadas, self.fase_atual_amuleto)

        # 5. ÍCONE DA BOLSA / INVENTÁRIO (Canto inferior direito com hover azul clarinho)
        borda_bolsa = AZUL_HOVER_MENU if self.hover_bolsa else CINZA_LINHO
        fundo_bolsa = AZUL_HOVER_BG if self.hover_bolsa else CARVAO_PROFUNDO
        
        desenhar_painel_padrao(surface_hud, self.rect_bolsa, cor_fundo=fundo_bolsa, cor_borda=borda_bolsa, alpha=240)

        if self.sprite_bolsa:
            ret_b = self.sprite_bolsa.get_rect(center=self.rect_bolsa.center)
            surface_hud.blit(self.sprite_bolsa, ret_b.topleft)
        else:
            txt_b = self.fonte_nome.render("Bolsa", True, MARFIM_OFFWHITE)
            surface_hud.blit(txt_b, txt_b.get_rect(center=self.rect_bolsa.center))

        # Atalho de Tecla [B] no canto superior do botão
        cor_atalho = AZUL_HOVER_MENU if self.hover_bolsa else MARFIM_OFFWHITE
        txt_atalho = self.fonte_slots.render("[B]", True, cor_atalho)
        surface_hud.blit(txt_atalho, (self.rect_bolsa.x + 6, self.rect_bolsa.y + 4))

        # Aplica a transparência final em toda a superfície do HUD e pinta na tela principal
        surface_hud.set_alpha(int(self.alpha_atual))
        tela.blit(surface_hud, (0, 0))

    def _desenhar_amuleto_7_fases(self, tela, cx, cy, atuais, fase):
        """Desenha o anel dividido em 7 partes com bordas delicadas e cores etéreas."""
        raio_externo = 34
        raio_interno = 13
        max_mem = 7
        
        pygame.draw.circle(tela, CARVAO_PROFUNDO, (cx, cy), raio_externo)
        pygame.draw.circle(tela, CINZA_LINHO, (cx, cy), raio_externo, 1)
        pygame.draw.circle(tela, CINZA_LINHO, (cx, cy), raio_interno, 1)
        
        angulo_fatia = 360 / max_mem
        
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
                pontos.append((cx + (raio_externo - 3) * math.cos(a), cy + (raio_externo - 3) * math.sin(a)))
            for p in range(4, -1, -1):
                a = ang_inicial + (ang_final - ang_inicial) * (p / 4.0)
                pontos.append((cx + (raio_interno + 3) * math.cos(a), cy + (raio_interno + 3) * math.sin(a)))
            
            if i < atuais:
                cor_fatia = cores_fases.get(i + 1, MARFIM_OFFWHITE)
                pygame.draw.polygon(tela, cor_fatia, pontos)
            else:
                pygame.draw.polygon(tela, (24, 24, 30), pontos)
            
            pygame.draw.polygon(tela, (8, 8, 12), pontos, 1)