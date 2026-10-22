# src/mechanics/combat_renderer.py
import pygame
import random
from src.ui.ui_utils import (
    desenhar_barra_status_interpolada,
    quebrar_texto_em_linhas
)
from src.utils.colors import (
    UI_FUNDO_PADRAO, CINZA_CLARO, CINZA_ESCURO, CINZA_LINHO, CINZA_ARDOSIA,
    UI_TEXTO_DESTAQUE, UI_TEXTO_APAGADO, TXT_SISTEMA_NARRADOR, TXT_PENSAMENTO_INTERNO,
    NOME_HALIA, TEXTO_ALERTA_COMBATE,
    BARRA_VIDA_JOGADOR, BARRA_VIDA_INIMIGO, BARRA_MANA, FUNDO_BARRA,
    BRANCO, PRETO,
    AZUL_HOVER_MENU, AZUL_HOVER_BG
)
from src.utils.resource_manager import ResourceManager
from src.mechanics.combat_narrator import CombatNarrator

class TextoFlutuante:
    """Gerencia textos flutuantes de dano, cura ou status na tela de combate."""
    def __init__(self, texto, x, y, cor=TEXTO_ALERTA_COMBATE, duracao=60, velocidade_y=-1.3):
        self.texto = str(texto)
        self.x = float(x)
        self.y = float(y)
        self.cor = cor
        self.duracao = duracao
        self.vida = duracao
        self.velocidade_y = velocidade_y

    def atualizar(self):
        self.y += self.velocidade_y
        self.vida -= 1
        return self.vida > 0

    def desenhar(self, tela, fonte):
        if self.vida <= 0: return
        alpha = max(0, min(255, int((self.vida / self.duracao) * 255)))
        superficie = fonte.render(self.texto, True, self.cor)
        superficie.set_alpha(alpha)
        # Sombra suave para contraste
        sombra = fonte.render(self.texto, True, PRETO)
        sombra.set_alpha(int(alpha * 0.7))
        tela.blit(sombra, (int(self.x) + 2, int(self.y) + 2))
        tela.blit(superficie, (int(self.x), int(self.y)))


class CombatRenderer:
    """
    Renderizador Gráfico Desacoplado da Tela de Combate (View).
    
    Responsabilidades:
    - Desenhar a arena de combate, plano de fundo e linha de horizonte.
    - Renderizar Halia e os monstros com sombras 2.5D, animações, shake de impacto e efeitos de sangue.
    - Renderizar barras interpoladas de vida (HP) e mana (MP).
    - Renderizar menus e submenus táticos com scrollbars e marcações visuais de hover/seleção.
    - Renderizar histórico de combate (log com word wrap) e tooltips de magias/itens.
    - Renderizar banners de vitória, derrota e fuga.
    """
    def __init__(self, combat_screen):
        self.cs = combat_screen

    @property
    def largura(self):
        return self.cs.largura

    @property
    def altura(self):
        return self.cs.altura

    def desenhar_barra(self, tela, x, y, valor_atual, valor_maximo, cor_barra, cor_fundo=FUNDO_BARRA, largura=180, altura=12):
        """Encaminha para o utilitário centralizado de UI."""
        desenhar_barra_status_interpolada(tela, x, y, valor_atual, valor_maximo, cor_barra, cor_fundo=cor_fundo, largura=largura, altura=altura)

    def desenhar_cabecalho_e_scrollbar_submenu(self, tela, painel_rect, largura_secao_menu, total_itens, scroll_atual, titulo=""):
        """Desenha o botão de voltar, paginação e barra de rolagem (scrollbar) se houver muitos itens."""
        # Botão Voltar
        self.cs.rect_botao_voltar = pygame.Rect(painel_rect.x + 20, painel_rect.y + 12, 90, 26)
        pygame.draw.rect(tela, (25, 25, 30), self.cs.rect_botao_voltar)
        pygame.draw.rect(tela, CINZA_CLARO, self.cs.rect_botao_voltar, 1)
        txt_voltar = self.cs.fonte_status.render("< Voltar", True, UI_TEXTO_DESTAQUE)
        tela.blit(txt_voltar, (self.cs.rect_botao_voltar.x + 12, self.cs.rect_botao_voltar.y + 5))

        max_visivel = self.cs.ITENS_POR_PAGINA_SUBMENU
        if total_itens > max_visivel:
            max_scroll = total_itens - max_visivel
            
            # Texto indicador de itens (ex: 1-4/7)
            inicio_idx = scroll_atual + 1
            fim_idx = min(total_itens, scroll_atual + max_visivel)
            txt_pag = self.cs.fonte_status.render(f"{inicio_idx}-{fim_idx}/{total_itens}", True, UI_TEXTO_APAGADO)
            tela.blit(txt_pag, (self.cs.rect_botao_voltar.right + 12, painel_rect.y + 17))

            # Botões de seta para cima e para baixo
            self.cs.rect_scroll_cima = pygame.Rect(painel_rect.x + largura_secao_menu - 52, painel_rect.y + 12, 22, 24)
            self.cs.rect_scroll_baixo = pygame.Rect(painel_rect.x + largura_secao_menu - 26, painel_rect.y + 12, 22, 24)

            # Seta Cima
            cor_cima = BRANCO if scroll_atual > 0 else (60, 60, 70)
            pygame.draw.rect(tela, (25, 25, 30), self.cs.rect_scroll_cima)
            pygame.draw.rect(tela, CINZA_ESCURO, self.cs.rect_scroll_cima, 1)
            txt_c = self.cs.fonte_status.render("^", True, cor_cima)
            tela.blit(txt_c, (self.cs.rect_scroll_cima.x + 7, self.cs.rect_scroll_cima.y + 3))

            # Seta Baixo
            cor_baixo = BRANCO if scroll_atual < max_scroll else (60, 60, 70)
            pygame.draw.rect(tela, (25, 25, 30), self.cs.rect_scroll_baixo)
            pygame.draw.rect(tela, CINZA_ESCURO, self.cs.rect_scroll_baixo, 1)
            txt_b = self.cs.fonte_status.render("v", True, cor_baixo)
            tela.blit(txt_b, (self.cs.rect_scroll_baixo.x + 7, self.cs.rect_scroll_baixo.y + 4))

            # Barra de rolagem lateral (Trilha e Cursor)
            track_x = painel_rect.x + largura_secao_menu - 14
            track_y = painel_rect.y + 46
            track_h = 170
            track_rect = pygame.Rect(track_x, track_y, 4, track_h)
            pygame.draw.rect(tela, (20, 20, 26), track_rect, border_radius=2)

            thumb_h = max(24, int(track_h * (max_visivel / total_itens)))
            thumb_y = track_y + int((track_h - thumb_h) * (scroll_atual / max_scroll)) if max_scroll > 0 else track_y
            thumb_rect = pygame.Rect(track_x, thumb_y, 4, thumb_h)
            pygame.draw.rect(tela, (140, 140, 160), thumb_rect, border_radius=2)
        else:
            self.cs.rect_scroll_cima = pygame.Rect(0, 0, 0, 0)
            self.cs.rect_scroll_baixo = pygame.Rect(0, 0, 0, 0)

    def desenhar(self, tela):
        """Renderiza a arena, personagens, HUDs, menus, submenus, tooltips e banners."""
        if not self.cs.jogador:
            return

        # 1. FUNDO PADRÃO ESCURO DE OBLIVIUM
        tela.fill(UI_FUNDO_PADRAO)
        
        # Linha horizontal sutil de horizonte
        pygame.draw.line(tela, CINZA_ESCURO, (0, 390), (self.largura, 390), 1)

        # 2. RENDERIZAR INIMIGOS (Lado Direito)
        self.cs.rects_inimigos.clear()
        inimigos_vivos = self.cs._obter_inimigos_vivos()

        for inimigo in self.cs.inimigos:
            esta_vivo = getattr(inimigo, 'vivo', True)
            alpha_morte = self.cs.alphas_morte.get(inimigo, 255) if not esta_vivo else 255
            
            # Se já desvaneceu totalmente, não precisa renderizar
            if not esta_vivo and alpha_morte <= 0:
                continue

            pos_x, pos_y = self.cs._obter_posicao_combate(inimigo)
            
            offset_shake_x = random.randint(-3, 3) if (esta_vivo and self.cs.shake_timers.get(inimigo, 0) > 0) else 0
            offset_shake_y = random.randint(-2, 2) if (esta_vivo and self.cs.shake_timers.get(inimigo, 0) > 0) else 0
            
            draw_x = pos_x + offset_shake_x
            draw_y = pos_y + offset_shake_y

            # Plataforma / Sombra sutil no chão sob o monstro
            if esta_vivo or alpha_morte > 60:
                if esta_vivo or alpha_morte >= 250:
                    pygame.draw.ellipse(tela, (22, 22, 26), (draw_x - 10, draw_y + 80, 100, 20))
                else:
                    sombra_surf = pygame.Surface((100, 20), pygame.SRCALPHA)
                    alpha_sombra = int(220 * (alpha_morte / 255.0))
                    pygame.draw.ellipse(sombra_surf, (22, 22, 26, alpha_sombra), (0, 0, 100, 20))
                    tela.blit(sombra_surf, (draw_x - 10, draw_y + 80))

            # Hitbox para clique de mouse e cursor de mira (apenas se vivo)
            if esta_vivo:
                rect_hitbox = pygame.Rect(draw_x - 10, draw_y - 25, 240, 125)
                self.cs.rects_inimigos.append(rect_hitbox)

                if self.cs.estado_combate == "SELECIONANDO_ALVO" and self.cs.indice_alvo < len(inimigos_vivos) and inimigos_vivos[self.cs.indice_alvo] is inimigo:
                    cursor_txt = self.cs.fonte_titulo.render(">", True, TXT_SISTEMA_NARRADOR)
                    tela.blit(cursor_txt, (draw_x - 30, draw_y + 15))
                    pygame.draw.rect(tela, TXT_SISTEMA_NARRADOR, rect_hitbox, 1)

            # Atualiza Animações do Inimigo
            if hasattr(inimigo, 'atualizar_animacao'):
                if esta_vivo:
                    # Transição automática de estados hurt/attack para idle quando finalizados
                    if getattr(inimigo, 'estado_atual', 'idle') == 'hurt' and getattr(inimigo.animacoes.get('hurt', None), 'concluida', False):
                        inimigo.definir_estado('idle')
                    elif getattr(inimigo, 'estado_atual', 'idle') in ['attack', 'ataque'] and getattr(inimigo.animacoes.get('attack', inimigo.animacoes.get('ataque', None)), 'concluida', False):
                        inimigo.definir_estado('idle')
                else:
                    # Se está morto, garante que o estado é dead/morte/morrer
                    if getattr(inimigo, 'estado_atual', '') not in ['dead', 'morte', 'morrer']:
                        est_m = "dead" if "dead" in inimigo.animacoes else ("morte" if "morte" in inimigo.animacoes else "morrer")
                        if est_m in inimigo.animacoes:
                            inimigo.definir_estado(est_m)
                inimigo.atualizar_animacao()

            # Renderiza Imagem ou Bloco Colorido
            imagem = getattr(inimigo, 'imagem_atual', None)
            if imagem:
                # Inimigos na direita da arena encaram Halia na esquerda
                if getattr(inimigo, 'virado_direita', True):
                    img_virada = pygame.transform.flip(imagem, True, False)
                else:
                    img_virada = imagem
                escala_c = getattr(inimigo, 'escala_combate', 0.85)
                nw = max(1, int(img_virada.get_width() * escala_c))
                nh = max(1, int(img_virada.get_height() * escala_c))
                img_combate = pygame.transform.scale(img_virada, (nw, nh))

                # Ancoragem bottom-center acima da elipse da plataforma
                cx = draw_x + 40
                cy = draw_y + 90
                offset_flutuante = -16 if (getattr(inimigo, 'flutuante', False) and esta_vivo) else 0
                bx = cx - (nw // 2)
                by = cy - nh + offset_flutuante

                if esta_vivo:
                    if self.cs.shake_timers.get(inimigo, 0) > 6:
                        flash_surf = img_combate.copy()
                        flash_surf.fill((255, 255, 255, 180), special_flags=pygame.BLEND_RGBA_MULT)
                        tela.blit(flash_surf, (bx, by))
                    else:
                        tela.blit(img_combate, (bx, by))
                else:
                    # Inimigo em animação de morte ou desvanecimento suave
                    if alpha_morte < 255:
                        surf_morte = img_combate.copy()
                        surf_morte.set_alpha(alpha_morte)
                        tela.blit(surf_morte, (bx, by))
                    else:
                        tela.blit(img_combate, (bx, by))
            else:
                rect_inimigo = pygame.Rect(draw_x, draw_y, getattr(inimigo, 'largura', 40) * 2, getattr(inimigo, 'altura', 40) * 2)
                cor_bloco = BRANCO if (esta_vivo and self.cs.shake_timers.get(inimigo, 0) > 6) else (getattr(inimigo, 'cor', (140, 40, 50)) if esta_vivo else (60, 60, 70))
                pygame.draw.rect(tela, cor_bloco, rect_inimigo)
                pygame.draw.rect(tela, CINZA_CLARO, rect_inimigo, 2)

            # Interface de Status (Apenas se o inimigo estiver vivo)
            if esta_vivo:
                # Nome do Inimigo
                texto_nome = self.cs.fonte_nomes.render(inimigo.nome, True, TEXTO_ALERTA_COMBATE)
                tela.blit(texto_nome, (draw_x, draw_y - 28))
                
                # Badges de Condições Ativas
                offset_icone_x = draw_x + texto_nome.get_width() + 8
                for cond in getattr(inimigo, 'condicoes', []):
                    txt_badge = self.cs.fonte_status.render(f"{cond.icone}:{cond.duracao}", True, TXT_SISTEMA_NARRADOR)
                    tela.blit(txt_badge, (offset_icone_x, draw_y - 25))
                    offset_icone_x += txt_badge.get_width() + 6

                # Barra de Vida Suave Interpolada
                base_bar_y = draw_y + 105
                larg_bar_inimigo = 150
                alt_bar = 12
                vida_v = self.cs.vidas_visuais.get(inimigo, float(inimigo.vida_atual))
                self.desenhar_barra(tela, draw_x - 15, base_bar_y, vida_v, inimigo.vida_maxima, BARRA_VIDA_INIMIGO, largura=larg_bar_inimigo, altura=alt_bar)
                txt_hp = self.cs.fonte_status.render(f"HP {int(vida_v)}/{inimigo.vida_maxima}", True, UI_TEXTO_DESTAQUE)
                tela.blit(txt_hp, (draw_x - 15 + larg_bar_inimigo + 10, base_bar_y - 2))

                # Barra de Mana Suave Interpolada do Monstro (Idêntico ao padrão visual de Halia)
                mana_max = getattr(inimigo, 'mana_maxima', 20)
                mana_v = self.cs.manas_visuais.get(inimigo, float(getattr(inimigo, 'mana_atual', mana_max)))
                mp_bar_y = base_bar_y + 20
                self.desenhar_barra(tela, draw_x - 15, mp_bar_y, mana_v, mana_max, BARRA_MANA, largura=larg_bar_inimigo, altura=alt_bar)
                txt_mp = self.cs.fonte_status.render(f"MP {int(mana_v)}/{mana_max}", True, UI_TEXTO_DESTAQUE)
                tela.blit(txt_mp, (draw_x - 15 + larg_bar_inimigo + 10, mp_bar_y - 2))

        # 3. RENDERIZAR HALIA (Lado Esquerdo)
        halia_x, halia_y = 160, 160
        offset_h_x = random.randint(-3, 3) if self.cs.shake_timers.get(self.cs.jogador, 0) > 0 else 0
        offset_h_y = random.randint(-2, 2) if self.cs.shake_timers.get(self.cs.jogador, 0) > 0 else 0
        
        draw_hx = halia_x + offset_h_x
        draw_hy = halia_y + offset_h_y

        # Plataforma / Sombra sutil no chão sob Halia
        pygame.draw.ellipse(tela, (22, 22, 26), (draw_hx - 10, draw_hy + 90, 105, 22))

        # Imagem ou Bloco da Halia (Sempre voltada para a direita durante o combate)
        img_halia = None
        if hasattr(self.cs.jogador, 'animacoes') and "idle_direita" in self.cs.jogador.animacoes:
            anim_h = self.cs.jogador.animacoes["idle_direita"]
            anim_h.atualizar()
            img_halia = anim_h.get_imagem()
        elif hasattr(self.cs.jogador, 'animacoes') and "andar_direita" in self.cs.jogador.animacoes:
            anim_h = self.cs.jogador.animacoes["andar_direita"]
            img_halia = anim_h.get_imagem()
        
        if not img_halia:
            img_halia = ResourceManager.carregar_imagem("halia/andando_direita/Halia_parado_direita.png")
        if not img_halia:
            img_halia = getattr(self.cs.jogador, 'imagem_atual', None)

        larg_h = 64
        alt_h = 96

        if img_halia:
            img_c = pygame.transform.scale(img_halia, (larg_h, alt_h))
            if self.cs.shake_timers.get(self.cs.jogador, 0) > 6:
                flash_surf = img_c.copy()
                flash_surf.fill((255, 255, 255, 180), special_flags=pygame.BLEND_RGBA_MULT)
                tela.blit(flash_surf, (draw_hx, draw_hy))
            else:
                tela.blit(img_c, (draw_hx, draw_hy))
        else:
            rect_h = pygame.Rect(draw_hx, draw_hy, larg_h, alt_h)
            cor_h = BRANCO if self.cs.shake_timers.get(self.cs.jogador, 0) > 6 else (34, 139, 34)
            pygame.draw.rect(tela, cor_h, rect_h)
            pygame.draw.rect(tela, CINZA_CLARO, rect_h, 2)

        # Efeito Visual de Respingo de Sangue sobre Halia ao Sofrer Dano
        if self.cs.efeitos_sangue:
            hx_centro = draw_hx + (larg_h // 2)
            hy_centro = draw_hy + (alt_h // 2)
            for ef in self.cs.efeitos_sangue:
                idx_s = int(ef["frame_atual"])
                frames_s = ef["frames"]
                if 0 <= idx_s < len(frames_s):
                    frame_s = frames_s[idx_s]
                    pos_sx = hx_centro - (frame_s.get_width() // 2) + ef.get("offset_x", 0)
                    pos_sy = hy_centro - (frame_s.get_height() // 2) + ef.get("offset_y", 0)
                    tela.blit(frame_s, (pos_sx, pos_sy))

        # Nome da Halia
        txt_halia = self.cs.fonte_nomes.render(self.cs.jogador.nome, True, NOME_HALIA)
        tela.blit(txt_halia, (draw_hx, draw_hy - 32))
        
        # Badges de Condições da Halia
        offset_h_badge = draw_hx + txt_halia.get_width() + 8
        for cond in getattr(self.cs.jogador, 'condicoes', []):
            txt_badge_h = self.cs.fonte_status.render(f"{cond.icone}:{cond.duracao}", True, TXT_SISTEMA_NARRADOR)
            tela.blit(txt_badge_h, (offset_h_badge, draw_hy - 30))
            offset_h_badge += txt_badge_h.get_width() + 6

        # Barras Interpoladas de HP e MP da Halia (Mesmo padrão visual, espessura e espaçamento)
        vida_h_v = self.cs.vidas_visuais.get(self.cs.jogador, float(self.cs.jogador.vida_atual))
        mana_h_v = self.cs.manas_visuais.get(self.cs.jogador, float(self.cs.jogador.mana_atual))
        larg_h_bar = 180
        alt_h_bar = 12
        base_h_bar_y = draw_hy + 105

        self.desenhar_barra(tela, draw_hx, base_h_bar_y, vida_h_v, self.cs.jogador.vida_maxima, BARRA_VIDA_JOGADOR, largura=larg_h_bar, altura=alt_h_bar)
        hp_mostrado = 0 if (self.cs.jogador.vida_atual <= 0 or not getattr(self.cs.jogador, 'vivo', True)) else max(1, int(round(vida_h_v)))
        tela.blit(self.cs.fonte_status.render(f"HP {hp_mostrado}/{self.cs.jogador.vida_maxima}", True, UI_TEXTO_DESTAQUE), (draw_hx + larg_h_bar + 10, base_h_bar_y - 2))

        self.desenhar_barra(tela, draw_hx, base_h_bar_y + 20, mana_h_v, self.cs.jogador.mana_maxima, BARRA_MANA, largura=larg_h_bar, altura=alt_h_bar)
        tela.blit(self.cs.fonte_status.render(f"MP {int(mana_h_v)}/{self.cs.jogador.mana_maxima}", True, UI_TEXTO_DESTAQUE), (draw_hx + larg_h_bar + 10, base_h_bar_y + 18))

        # 4. PAINEL INFERIOR DE MENUS E COMBAT LOG
        altura_painel = 245
        painel_rect = pygame.Rect(40, self.altura - altura_painel - 20, self.largura - 80, altura_painel)
        pygame.draw.rect(tela, UI_FUNDO_PADRAO, painel_rect)
        pygame.draw.rect(tela, CINZA_CLARO, painel_rect, 2)

        # Divisão Interna: Seção de Ações (Esquerda 380px) | Seção de Log (Direita)
        largura_secao_menu = 380
        pygame.draw.line(tela, CINZA_ESCURO, (painel_rect.x + largura_secao_menu, painel_rect.y), (painel_rect.x + largura_secao_menu, painel_rect.bottom), 1)

        # RENDERIZAR MENU PRINCIPAL
        self.cs.rects_menu_principal.clear()
        if self.cs.estado_combate == "MENU_PRINCIPAL":
            for i, opcao in enumerate(self.cs.opcoes_menu_principal):
                item_y = painel_rect.y + 14 + (i * 44)
                item_rect = pygame.Rect(painel_rect.x + 20, item_y, largura_secao_menu - 40, 38)
                self.cs.rects_menu_principal.append(item_rect)
                
                if i == self.cs.indice_menu:
                    pygame.draw.rect(tela, AZUL_HOVER_BG, item_rect, border_radius=2)
                    pygame.draw.rect(tela, AZUL_HOVER_MENU, item_rect, 1, border_radius=2)
                    cor = AZUL_HOVER_MENU
                    marcador = "►  "
                else:
                    pygame.draw.rect(tela, (18, 18, 22), item_rect, border_radius=2)
                    pygame.draw.rect(tela, CINZA_ARDOSIA, item_rect, 1, border_radius=2)
                    cor = CINZA_LINHO
                    marcador = "    "
                    
                txt = self.cs.fonte_menu.render(f"{marcador}{opcao}", True, cor)
                tela.blit(txt, (item_rect.x + 10, item_rect.centery - txt.get_height() // 2))

        # RENDERIZAR SUBMENU DE ATAQUES FÍSICOS
        self.cs.rects_ataques_fisicos.clear()
        if self.cs.estado_combate == "SUBMENU_ATAQUE":
            total = len(self.cs.ataques_fisicos_disponiveis)
            self.desenhar_cabecalho_e_scrollbar_submenu(tela, painel_rect, largura_secao_menu, total, self.cs.scroll_ataque, "Ataques")
            largura_item = largura_secao_menu - 48 if total > self.cs.ITENS_POR_PAGINA_SUBMENU else largura_secao_menu - 40

            for slot_i, real_i in enumerate(range(self.cs.scroll_ataque, min(total, self.cs.scroll_ataque + self.cs.ITENS_POR_PAGINA_SUBMENU))):
                ataque = self.cs.ataques_fisicos_disponiveis[real_i]
                item_y = painel_rect.y + 46 + (slot_i * 44)
                item_rect = pygame.Rect(painel_rect.x + 20, item_y, largura_item, 38)
                self.cs.rects_ataques_fisicos.append((item_rect, real_i))
                
                if real_i == self.cs.indice_ataque_fisico:
                    pygame.draw.rect(tela, AZUL_HOVER_BG, item_rect, border_radius=2)
                    pygame.draw.rect(tela, AZUL_HOVER_MENU, item_rect, 1, border_radius=2)
                    cor = AZUL_HOVER_MENU
                    marcador = "►  "
                else:
                    pygame.draw.rect(tela, (18, 18, 22), item_rect, border_radius=2)
                    pygame.draw.rect(tela, CINZA_ARDOSIA, item_rect, 1, border_radius=2)
                    cor = CINZA_LINHO
                    marcador = "    "
                    
                custo_str = f"({ataque.custo_mana} MP)" if ataque.custo_mana > 0 else ""
                txt = self.cs.fonte_menu.render(f"{marcador}{ataque.nome} {custo_str}".strip(), True, cor)
                tela.blit(txt, (item_rect.x + 10, item_rect.centery - txt.get_height() // 2))

        # RENDERIZAR SUBMENU DE MAGIAS
        self.cs.rects_magias.clear()
        if self.cs.estado_combate == "SUBMENU_MAGIA":
            total = len(self.cs.magias_disponiveis)
            self.desenhar_cabecalho_e_scrollbar_submenu(tela, painel_rect, largura_secao_menu, total, self.cs.scroll_magia, "Grimório")
            largura_item = largura_secao_menu - 48 if total > self.cs.ITENS_POR_PAGINA_SUBMENU else largura_secao_menu - 40

            for slot_i, real_i in enumerate(range(self.cs.scroll_magia, min(total, self.cs.scroll_magia + self.cs.ITENS_POR_PAGINA_SUBMENU))):
                magia = self.cs.magias_disponiveis[real_i]
                item_y = painel_rect.y + 46 + (slot_i * 44)
                item_rect = pygame.Rect(painel_rect.x + 20, item_y, largura_item, 38)
                self.cs.rects_magias.append((item_rect, real_i))
                
                if real_i == self.cs.indice_magia:
                    pygame.draw.rect(tela, AZUL_HOVER_BG, item_rect, border_radius=2)
                    pygame.draw.rect(tela, AZUL_HOVER_MENU, item_rect, 1, border_radius=2)
                    cor = AZUL_HOVER_MENU
                    marcador = "►  "
                else:
                    pygame.draw.rect(tela, (18, 18, 22), item_rect, border_radius=2)
                    pygame.draw.rect(tela, CINZA_ARDOSIA, item_rect, 1, border_radius=2)
                    cor = CINZA_LINHO
                    marcador = "    "
                    
                custo_txt = f"({magia.custo_mana} MP)" if magia.custo_mana > 0 else "(Gratis)"
                txt = self.cs.fonte_menu.render(f"{marcador}{magia.nome} {custo_txt}", True, cor)
                tela.blit(txt, (item_rect.x + 10, item_rect.centery - txt.get_height() // 2))

        # RENDERIZAR SUBMENU DE CONCENTRAR
        self.cs.rects_concentrar.clear()
        if self.cs.estado_combate == "SUBMENU_CONCENTRAR":
            total = len(self.cs.opcoes_concentrar)
            self.desenhar_cabecalho_e_scrollbar_submenu(tela, painel_rect, largura_secao_menu, total, self.cs.scroll_concentrar, "Tático")
            largura_item = largura_secao_menu - 48 if total > self.cs.ITENS_POR_PAGINA_SUBMENU else largura_secao_menu - 40

            for slot_i, real_i in enumerate(range(self.cs.scroll_concentrar, min(total, self.cs.scroll_concentrar + self.cs.ITENS_POR_PAGINA_SUBMENU))):
                acao = self.cs.opcoes_concentrar[real_i]
                item_y = painel_rect.y + 46 + (slot_i * 44)
                item_rect = pygame.Rect(painel_rect.x + 20, item_y, largura_item, 38)
                self.cs.rects_concentrar.append((item_rect, real_i))
                
                if real_i == self.cs.indice_concentrar:
                    pygame.draw.rect(tela, AZUL_HOVER_BG, item_rect, border_radius=2)
                    pygame.draw.rect(tela, AZUL_HOVER_MENU, item_rect, 1, border_radius=2)
                    cor = AZUL_HOVER_MENU
                    marcador = "►  "
                else:
                    pygame.draw.rect(tela, (18, 18, 22), item_rect, border_radius=2)
                    pygame.draw.rect(tela, CINZA_ARDOSIA, item_rect, 1, border_radius=2)
                    cor = CINZA_LINHO
                    marcador = "    "
                    
                sufixo = "(+MP)" if acao.id_acao == "foco_espiritual" else "(Guarda)"
                txt = self.cs.fonte_menu.render(f"{marcador}{acao.nome} {sufixo}", True, cor)
                tela.blit(txt, (item_rect.x + 10, item_rect.centery - txt.get_height() // 2))

        # RENDERIZAR SUBMENU DE ITENS CONSUMÍVEIS
        self.cs.rects_itens_combate.clear()
        if self.cs.estado_combate == "SUBMENU_ITENS":
            total = len(self.cs.itens_combate_disponiveis)
            self.desenhar_cabecalho_e_scrollbar_submenu(tela, painel_rect, largura_secao_menu, total, self.cs.scroll_item_combate, "Bolsa")
            largura_item = largura_secao_menu - 48 if total > self.cs.ITENS_POR_PAGINA_SUBMENU else largura_secao_menu - 40

            for slot_i, real_i in enumerate(range(self.cs.scroll_item_combate, min(total, self.cs.scroll_item_combate + self.cs.ITENS_POR_PAGINA_SUBMENU))):
                idx_real, item_slot = self.cs.itens_combate_disponiveis[real_i]
                item = item_slot.item
                qtd = item_slot.quantidade
                item_y = painel_rect.y + 46 + (slot_i * 44)
                item_rect = pygame.Rect(painel_rect.x + 20, item_y, largura_item, 38)
                self.cs.rects_itens_combate.append((item_rect, real_i))
                
                if real_i == self.cs.indice_item_combate:
                    pygame.draw.rect(tela, AZUL_HOVER_BG, item_rect, border_radius=2)
                    pygame.draw.rect(tela, AZUL_HOVER_MENU, item_rect, 1, border_radius=2)
                    cor = AZUL_HOVER_MENU
                    marcador = "►  "
                else:
                    pygame.draw.rect(tela, (18, 18, 22), item_rect, border_radius=2)
                    pygame.draw.rect(tela, CINZA_ARDOSIA, item_rect, 1, border_radius=2)
                    cor = CINZA_LINHO
                    marcador = "    "
                    
                txt_it = self.cs.fonte_menu.render(f"{marcador}{item.nome} (x{qtd})", True, cor)
                tela.blit(txt_it, (item_rect.x + 10, item_rect.centery - txt_it.get_height() // 2))

        # RENDERIZAR SELEÇÃO DE ALVOS
        elif self.cs.estado_combate == "SELECIONANDO_ALVO":
            titulo_alvo = "Arremessar Item no Inimigo:" if self.cs.item_combate_selecionado else "Selecione o Inimigo Alvo:"
            txt_alvo = self.cs.fonte_menu.render(titulo_alvo, True, TXT_SISTEMA_NARRADOR)
            tela.blit(txt_alvo, (painel_rect.x + 20, painel_rect.y + 15))
            
            inimigos_vivos = self.cs._obter_inimigos_vivos()
            for i, inimigo in enumerate(inimigos_vivos):
                cor = TXT_SISTEMA_NARRADOR if i == self.cs.indice_alvo else CINZA_CLARO
                marcador = "> " if i == self.cs.indice_alvo else "  "
                txt_i = self.cs.fonte_status.render(f"{marcador}{inimigo.nome} ({inimigo.vida_atual}/{inimigo.vida_maxima} HP)", True, cor)
                tela.blit(txt_i, (painel_rect.x + 20, painel_rect.y + 55 + (i * 32)))

        # RENDERIZAR COMBAT LOG (Seção Direita com Word Wrap e Cores Preservadas)
        pos_log_x = painel_rect.x + largura_secao_menu + 30
        pos_log_y = painel_rect.y + 16
        
        txt_cabecalho_log = self.cs.fonte_status.render(f"HISTORICO DE COMBATE (Vel: {self.cs.velocidade_combate}x)", True, UI_TEXTO_APAGADO)
        tela.blit(txt_cabecalho_log, (pos_log_x, pos_log_y))
        
        # Histórico exibe 6 linhas completas
        max_linhas = 6
        linhas_exibidas = self.cs.historico_log[-max_linhas:]
        
        for idx, item in enumerate(linhas_exibidas):
            is_latest = (idx == len(linhas_exibidas) - 1)
            texto_linha = item.get("texto", "") if isinstance(item, dict) else str(item)
            cor_custom = item.get("cor", None) if isinstance(item, dict) else None
            
            if cor_custom:
                cor_linha = cor_custom
            elif is_latest:
                cor_linha = BRANCO
            else:
                cor_linha = CINZA_CLARO
                
            txt_linha = self.cs.fonte_log.render(texto_linha, True, cor_linha)
            tela.blit(txt_linha, (pos_log_x, pos_log_y + 26 + (idx * 27)))

        # RENDERIZAR TOOLTIP FIXO NA PARTE INFERIOR
        if self.cs.estado_combate in ["SUBMENU_ATAQUE", "SUBMENU_MAGIA", "SUBMENU_CONCENTRAR", "SUBMENU_ITENS"]:
            acao_sel = None
            if self.cs.estado_combate == "SUBMENU_ATAQUE" and self.cs.indice_ataque_fisico < len(self.cs.ataques_fisicos_disponiveis):
                acao_sel = self.cs.ataques_fisicos_disponiveis[self.cs.indice_ataque_fisico]
            elif self.cs.estado_combate == "SUBMENU_MAGIA" and self.cs.indice_magia < len(self.cs.magias_disponiveis):
                acao_sel = self.cs.magias_disponiveis[self.cs.indice_magia]
            elif self.cs.estado_combate == "SUBMENU_CONCENTRAR" and self.cs.indice_concentrar < len(self.cs.opcoes_concentrar):
                acao_sel = self.cs.opcoes_concentrar[self.cs.indice_concentrar]
            elif self.cs.estado_combate == "SUBMENU_ITENS" and self.cs.indice_item_combate < len(self.cs.itens_combate_disponiveis):
                _, item_slot = self.cs.itens_combate_disponiveis[self.cs.indice_item_combate]
                acao_sel = item_slot.item

            if acao_sel:
                largura_tooltip = (painel_rect.right - 15) - (painel_rect.x + largura_secao_menu + 20)
                self.desenhar_tooltip_acao(
                    tela,
                    acao_sel,
                    painel_rect.x + largura_secao_menu + 20,
                    painel_rect.bottom - 12,
                    largura_max=largura_tooltip
                )

        # 5. RENDERIZAR NÚMEROS FLUTUANTES
        for tf in self.cs.textos_flutuantes:
            tf.desenhar(tela, self.cs.fonte_dano)

        # 6. TELAS ESPECIAIS (Banners de Vitória, Derrota e Fuga)
        if self.cs.estado_combate in ["VITORIA", "DERROTA", "FUGIU"]:
            self.desenhar_banner_fim_combate(tela)

    def desenhar_tooltip_acao(self, tela, acao, x, y_bottom, largura_max=None):
        """Desenha uma caixa descritiva elegante fixada na parte inferior do painel, sobrepondo o histórico."""
        if not acao:
            return

        tipo = getattr(acao, 'tipo', '').upper()
        categoria = getattr(acao, 'categoria', '').upper()
        elemento = getattr(acao, 'elemento', 'NEUTRO').upper()
        desc = getattr(acao, 'descricao', '')
        custo = getattr(acao, 'custo_mana', 0)
        custo_str = f" | Custo: {custo} MP" if custo > 0 else (" | Custo: Grátis" if tipo == "MAGICO" else "")

        if categoria == "CONSUMIVEL":
            tipo_c = getattr(acao, 'tipo_consumivel', '')
            if tipo_c == "CURA_HP":
                detalhe = f"[ITEM CURA] {acao.nome} | Restaura {getattr(acao, 'valor_efeito', 0)} HP - {desc}"
            elif tipo_c == "RESTAURA_MP":
                detalhe = f"[ITEM MANA] {acao.nome} | Restaura {getattr(acao, 'valor_efeito', 0)} MP - {desc}"
            elif tipo_c == "DANO_OFENSIVO":
                detalhe = f"[ITEM OFENSIVO] {acao.nome} | Causa {getattr(acao, 'valor_efeito', 0)} Dano - {desc}"
            else:
                detalhe = f"[ITEM] {acao.nome} - {desc}"
        elif tipo == "MAGICO":
            detalhe = f"[{elemento}] {acao.nome}{custo_str} | Poder: {getattr(acao, 'poder_base', 0)} - {desc}"
        elif tipo == "FOCO":
            detalhe = f"[TÁTICO] {acao.nome} - {desc}"
        elif tipo == "DEFESA":
            detalhe = f"[TÁTICO] {acao.nome} - {desc}"
        elif tipo == "FISICO":
            detalhe = f"[FÍSICO] {acao.nome}{custo_str} | Poder: {getattr(acao, 'poder_base', 0)} - {desc}"
        else:
            detalhe = f"[{elemento}] {acao.nome} - {desc}"

        if largura_max is None:
            largura_max = self.largura - x - 40

        linhas_tt = quebrar_texto_em_linhas(detalhe, self.cs.fonte_tooltip, largura_max - 24)
        if not linhas_tt:
            linhas_tt = [detalhe]

        altura_linha = 20
        altura_tt = max(42, 14 + (len(linhas_tt) * altura_linha))
        pos_y_tt = y_bottom - altura_tt

        rect_tt = pygame.Rect(x, pos_y_tt, largura_max, altura_tt)
        pygame.draw.rect(tela, (22, 22, 28), rect_tt)
        pygame.draw.rect(tela, CINZA_CLARO, rect_tt, 1)

        for i, l in enumerate(linhas_tt):
            cor_txt = UI_TEXTO_DESTAQUE if i == 0 else CINZA_CLARO
            txt_d = self.cs.fonte_tooltip.render(l, True, cor_txt)
            tela.blit(txt_d, (rect_tt.x + 12, rect_tt.y + 7 + (i * altura_linha)))

    def desenhar_banner_fim_combate(self, tela):
        """Renderiza o banner escurecido centralizado de encerramento da batalha."""
        overlay = pygame.Surface((self.largura, self.altura), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 195))
        tela.blit(overlay, (0, 0))

        largura_b, altura_b = 640, 260
        rx = (self.largura - largura_b) // 2
        ry = (self.altura - altura_b) // 2
        self.cs.rect_banner = pygame.Rect(rx, ry, largura_b, altura_b)
        
        pygame.draw.rect(tela, UI_FUNDO_PADRAO, self.cs.rect_banner)
        
        if self.cs.estado_combate == "VITORIA":
            cor_borda = TXT_SISTEMA_NARRADOR
            titulo = CombatNarrator.obter_banner("vitoria_titulo") or "VITÓRIA ALCANÇADA!"
            msg1 = f"Recompensas: +{self.cs.recompensas_vitoria['moedas']} Moedas | +{self.cs.recompensas_vitoria['memorias']} Memória(s)"
            msg2 = CombatNarrator.obter_banner("continuar_prompt") or "Pressione [ENTER], [ESPAÇO] ou clique para prosseguir"
        elif self.cs.estado_combate == "DERROTA":
            cor_borda = TEXTO_ALERTA_COMBATE
            titulo = CombatNarrator.obter_banner("derrota_titulo") or "HALIA SUCUMBIU..."
            msg1 = CombatNarrator.obter_banner("derrota_sub") or "Suas memórias se desvanecem no vácuo de Oblivium..."
            msg2 = CombatNarrator.obter_banner("continuar_prompt") or "Pressione [ENTER] ou clique para reiniciar..."
        else: # FUGIU
            cor_borda = TXT_PENSAMENTO_INTERNO
            titulo = CombatNarrator.obter_banner("fuga_titulo") or "FUGA BEM-SUCEDIDA!"
            msg1 = CombatNarrator.obter_banner("fuga_sub") or "Halia recuou para uma posição segura fora de alcance."
            msg2 = CombatNarrator.obter_banner("continuar_prompt") or "Pressione [ENTER] ou clique para retornar..."

        pygame.draw.rect(tela, cor_borda, self.cs.rect_banner, 2)

        txt_t = self.cs.fonte_titulo.render(titulo, True, cor_borda)
        tela.blit(txt_t, (rx + (largura_b - txt_t.get_width()) // 2, ry + 35))

        txt_m1 = self.cs.fonte_menu.render(msg1, True, UI_TEXTO_DESTAQUE)
        tela.blit(txt_m1, (rx + (largura_b - txt_m1.get_width()) // 2, ry + 105))

        txt_m2 = self.cs.fonte_status.render(msg2, True, UI_TEXTO_APAGADO)
        tela.blit(txt_m2, (rx + (largura_b - txt_m2.get_width()) // 2, ry + 195))
