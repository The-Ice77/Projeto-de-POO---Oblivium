# src/mechanics/combat/combat_renderer.py
import pygame
import random
from src.entities.player import Player
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
from src.mechanics.combat.combat_narrator import CombatNarrator
from src.utils.resource_manager import ResourceManager

class TextoFlutuante:
    """Gerencia textos flutuantes de dano, cura ou status na tela de combate."""
    def __init__(self, texto, x, y, cor=TEXTO_ALERTA_COMBATE, duracao=60, velocidade_y=-1.3, y_min=114):
        self.texto = str(texto)
        self.x = float(x)
        self.y = float(y)
        self.cor = cor
        self.duracao = duracao
        self.vida = duracao
        self.velocidade_y = velocidade_y
        self.y_min = float(y_min)

    def atualizar(self):
        self.y = max(self.y_min, self.y + self.velocidade_y)
        self.vida -= 1
        return self.vida > 0

    @staticmethod
    def _cor_legivel(cor):
        r, g, b = cor[:3]
        luma = 0.299 * r + 0.587 * g + 0.114 * b
        if luma >= 185:
            return (r, g, b)
        fator = min(0.65, (185.0 - luma) / max(1.0, 255.0 - luma))
        return (
            int(r + (255 - r) * fator),
            int(g + (255 - g) * fator),
            int(b + (255 - b) * fator),
        )

    def desenhar(self, tela, fonte):
        if self.vida <= 0: return
        alpha = max(0, min(255, int((self.vida / self.duracao) * 255)))
        cor_final = self._cor_legivel(self.cor)
        superficie = fonte.render(self.texto, True, cor_final)
        superficie.set_alpha(alpha)
        sombra = fonte.render(self.texto, True, PRETO)
        sombra.set_alpha(int(alpha * 0.85))
        ix, iy = int(self.x), int(self.y)
        for ox, oy in ((-1, 0), (1, 0), (0, -1), (0, 1), (2, 2)):
            tela.blit(sombra, (ix + ox, iy + oy))
        tela.blit(superficie, (ix, iy))


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

    def criar_texto_flutuante(self, texto, x, y, cor=TEXTO_ALERTA_COMBATE, duracao=60):
        """Posiciona texto flutuante abaixo do HUD da coluna correspondente e sem empilhamento."""
        hud_rects = getattr(self.cs, "rects_hud_status", {})
        largura_txt = self.cs.fonte_dano.size(str(texto))[0] if hasattr(self.cs, "fonte_dano") else 120
        nx = max(28.0, min(float(self.largura - max(180, largura_txt + 30)), float(x)))
        faixa_x = pygame.Rect(int(nx) - 24, 0, max(120, largura_txt + 48), self.altura)
        hud_relevante = [
            r for r in hud_rects.values()
            if r.colliderect(faixa_x)
            or (len(hud_rects) <= 2 and ((nx > 500 and r.centerx > 500) or (nx <= 500 and r.centerx <= 500)))
        ]
        hud_bottom = max((r.bottom for r in hud_relevante), default=0)
        safe_top = float(max(118, hud_bottom + 8))
        ny = max(safe_top, min(410.0, float(y)))

        for _ in range(12):
            colide = any(
                abs(tf.x - nx) < 150 and abs(tf.y - ny) < 26
                for tf in self.cs.textos_flutuantes
            )
            if not colide:
                break
            ny += 26.0
            if ny > 410.0:
                ny = safe_top
                nx = max(28.0, min(float(self.largura - 220), nx - 120.0 if nx > 600 else nx + 120.0))

        return TextoFlutuante(texto, nx, ny, cor=cor, duracao=duracao, y_min=safe_top - 4.0)

    def _medir_pilula(self, texto, fonte):
        tw, th = fonte.size(texto)
        return tw + 14, max(20, th + 4)

    def _desenhar_pilula(self, tela, rect, texto, fonte, bg, borda, cor_texto):
        pygame.draw.rect(tela, bg, rect, border_radius=3)
        pygame.draw.rect(tela, borda, rect, 1, border_radius=3)
        txt = fonte.render(texto, True, cor_texto)
        tela.blit(txt, (rect.x + (rect.width - txt.get_width()) // 2, rect.y + (rect.height - txt.get_height()) // 2))

    def _montar_badges_entidade(self, entidade, eh_jogador=False):
        badges = []
        if not eh_jogador and getattr(entidade, "enfurecido", False):
            badges.append(("[FÚRIA]", (76, 22, 18), (255, 225, 165), (255, 242, 205)))
        if not eh_jogador and getattr(entidade, "preparando_sopro", False):
            badges.append(("[!] PREPARANDO SOPRO!", (92, 34, 12), (255, 238, 168), (255, 248, 210)))
        if eh_jogador and getattr(entidade, "defendendo", False):
            badges.append(("[EM GUARDA]", (24, 48, 72), (195, 230, 255), (240, 248, 255)))
        if getattr(entidade, "vulneravel", False):
            badges.append(("[VULNERÁVEL]", (72, 26, 26), (255, 210, 200), (255, 235, 228)))
        for cond in getattr(entidade, "condicoes", []):
            badges.append((f"{cond.icone}:{cond.duracao}", (26, 30, 40), (205, 205, 215), (246, 243, 236)))
        return badges

    def _desenhar_card_status(
        self,
        tela,
        titulo,
        badges,
        x,
        y,
        max_largura,
        cor_titulo,
        direita=False,
        compacto=False,
        centralizado=False,
        obstaculos=None,
        destaque=False,
    ):
        fonte_tit = self.cs.fonte_log if compacto else self.cs.fonte_nomes
        fonte_badge = self.cs.fonte_status
        pad_x = 12 if not compacto else 10
        pad_y = 7 if not compacto else 4
        if compacto:
            surf_t = fonte_tit.render(titulo, True, cor_titulo)
            pilulas = [(texto_b, bg_b, borda_b, cor_b, *self._medir_pilula(texto_b, fonte_badge)) for texto_b, bg_b, borda_b, cor_b in badges]
            larg_pilulas = (sum(p[4] for p in pilulas) + 6 * len(pilulas)) if pilulas else 0
            min_w = 116 if centralizado else 220
            larg_card = min(max_largura, max(min_w, surf_t.get_width() + larg_pilulas + pad_x * 2 + 6))
            alt_card = max(29, surf_t.get_height() + pad_y * 2)
            base_x = (x - larg_card // 2) if centralizado else ((x - larg_card) if direita else x)
            min_x = 420 if centralizado else 16
            max_x = max(min_x, self.largura - larg_card - 16)
            base_x = max(min_x, min(max_x, base_x))
            limite_inf_y = 352 if centralizado else 415
            base_y = max(12, min(limite_inf_y, y))
            card_rect = pygame.Rect(base_x, base_y, larg_card, alt_card)
            if obstaculos:
                deslocamentos = []
                for dy in (0, -8, -16, -24, -34, -44, 8):
                    for dx in (0, 24, -24, 48, -48, 72, -72, 92, -92):
                        deslocamentos.append((abs(dx) + abs(dy) * 1.4, dx, dy))
                deslocamentos.sort(key=lambda item: item[0])
                for _, dx, dy in deslocamentos:
                    cx_cand = max(min_x, min(max_x, base_x + dx))
                    cy_cand = max(12, min(limite_inf_y, base_y + dy))
                    cand = pygame.Rect(cx_cand, cy_cand, larg_card, alt_card)
                    if not any(cand.colliderect(obs) for obs in obstaculos):
                        card_rect = cand
                        break
            surf_bg = pygame.Surface((card_rect.width, card_rect.height), pygame.SRCALPHA)
            surf_bg.fill((14, 15, 20, 238))
            tela.blit(surf_bg, card_rect.topleft)
            tem_alerta = any(b[0].startswith("[!]") or b[0] == "[FÚRIA]" for b in badges)
            cor_borda = (255, 220, 110) if destaque else ((255, 230, 175) if tem_alerta else (215, 210, 202))
            pygame.draw.rect(tela, cor_borda, card_rect, 2 if destaque else 1, border_radius=3)
            if centralizado and not pilulas:
                tx = card_rect.x + max(pad_x, (card_rect.width - surf_t.get_width()) // 2)
                tela.blit(surf_t, (tx, card_rect.y + (card_rect.height - surf_t.get_height()) // 2))
            elif centralizado:
                tx = card_rect.x + pad_x
                tela.blit(surf_t, (tx, card_rect.y + (card_rect.height - surf_t.get_height()) // 2))
                bx = tx + surf_t.get_width() + 8
                for texto_b, bg_b, borda_b, cor_b, bw, bh in pilulas:
                    if bx + bw <= card_rect.right - pad_x + 2:
                        self._desenhar_pilula(tela, pygame.Rect(bx, card_rect.y + (card_rect.height - bh) // 2, bw, bh), texto_b, fonte_badge, bg_b, borda_b, cor_b)
                        bx += bw + 6
            else:
                tx = card_rect.right - pad_x - surf_t.get_width()
                tela.blit(surf_t, (tx, card_rect.y + (card_rect.height - surf_t.get_height()) // 2))
                bx = tx - 8
                for texto_b, bg_b, borda_b, cor_b, bw, bh in reversed(pilulas):
                    bx -= bw
                    if bx >= card_rect.x + pad_x:
                        self._desenhar_pilula(tela, pygame.Rect(bx, card_rect.y + (card_rect.height - bh) // 2, bw, bh), texto_b, fonte_badge, bg_b, borda_b, cor_b)
                        bx -= 6
            return card_rect

        inner_max = max(180, max_largura - pad_x * 2)

        linhas_tit = quebrar_texto_em_linhas(titulo, fonte_tit, inner_max) or [titulo]
        alt_linha_tit = fonte_tit.get_height() + 2
        larg_tit = max(fonte_tit.size(l)[0] for l in linhas_tit)

        linhas_badges = []
        linha_atual = []
        larg_atual = 0
        max_linha_badge = 0
        for texto_b, bg_b, borda_b, cor_b in badges:
            bw, bh = self._medir_pilula(texto_b, fonte_badge)
            gap = 6 if linha_atual else 0
            if linha_atual and larg_atual + gap + bw > inner_max:
                linhas_badges.append((linha_atual, larg_atual))
                max_linha_badge = max(max_linha_badge, larg_atual)
                linha_atual = [(texto_b, bg_b, borda_b, cor_b, bw, bh)]
                larg_atual = bw
            else:
                linha_atual.append((texto_b, bg_b, borda_b, cor_b, bw, bh))
                larg_atual += gap + bw
        if linha_atual:
            linhas_badges.append((linha_atual, larg_atual))
            max_linha_badge = max(max_linha_badge, larg_atual)

        larg_card = min(max_largura, max(200 if not compacto else 220, max(larg_tit, max_linha_badge) + pad_x * 2))
        alt_badges = (len(linhas_badges) * 24 + (len(linhas_badges) - 1) * 4) if linhas_badges else 0
        gap_secao = 5 if linhas_badges else 0
        alt_card = pad_y * 2 + len(linhas_tit) * alt_linha_tit + gap_secao + alt_badges

        card_x = (x - larg_card) if direita else x
        card_x = max(16, min(self.largura - larg_card - 16, card_x))
        card_rect = pygame.Rect(card_x, y, larg_card, alt_card)

        surf_bg = pygame.Surface((card_rect.width, card_rect.height), pygame.SRCALPHA)
        surf_bg.fill((14, 15, 20, 238))
        tela.blit(surf_bg, card_rect.topleft)
        tem_alerta = any(b[0].startswith("[!]") or b[0] == "[FÚRIA]" for b in badges)
        cor_borda = (255, 220, 110) if destaque else ((255, 230, 175) if tem_alerta else (215, 210, 202))
        pygame.draw.rect(tela, cor_borda, card_rect, 2 if destaque else 1, border_radius=3)

        cur_y = card_rect.y + pad_y
        for l_txt in linhas_tit:
            surf_t = fonte_tit.render(l_txt, True, cor_titulo)
            tx = (card_rect.right - pad_x - surf_t.get_width()) if direita else (card_rect.x + pad_x)
            tela.blit(surf_t, (tx, cur_y))
            cur_y += alt_linha_tit

        if linhas_badges:
            cur_y += gap_secao
            for row, row_w in linhas_badges:
                bx = (card_rect.right - pad_x - row_w) if direita else (card_rect.x + pad_x)
                for texto_b, bg_b, borda_b, cor_b, bw, bh in row:
                    self._desenhar_pilula(tela, pygame.Rect(bx, cur_y, bw, bh), texto_b, fonte_badge, bg_b, borda_b, cor_b)
                    bx += bw + 6
                cur_y += 28

        return card_rect

    def _desenhar_headers_status(self, tela):
        """Renderiza cartões de nome: topo-esquerdo para Halia, topo-direito para 1 inimigo e ancorados acima de cada sprite para múltiplos."""
        badges_h = self._montar_badges_entidade(self.cs.jogador, eh_jogador=True)
        card_h = self._desenhar_card_status(
            tela, self.cs.jogador.nome, badges_h,
            x=40, y=14, max_largura=400, cor_titulo=(212, 248, 224),
            direita=False, compacto=False,
        )
        self.cs.rects_hud_status["jogador"] = card_h

        vivos = [e for e in self.cs.inimigos if getattr(e, "vivo", True)]
        if not vivos:
            return
        if len(vivos) == 1:
            inimigo = vivos[0]
            badges_e = self._montar_badges_entidade(inimigo, eh_jogador=False)
            destaque = self.cs.estado_combate == "SELECIONANDO_ALVO"
            card_e = self._desenhar_card_status(
                tela, inimigo.nome, badges_e,
                x=self.largura - 40, y=14, max_largura=520,
                cor_titulo=(252, 232, 224), direita=True, compacto=False, destaque=destaque,
            )
            self.cs.rects_hud_status[inimigo] = card_e
            return

        obstaculos = [card_h.inflate(8, 6)]
        for r_spr in getattr(self.cs, "rects_sprites_combate", {}).values():
            obstaculos.append(r_spr.inflate(6, 4))
        for r_bar in getattr(self.cs, "_rects_barras_inimigos", []):
            obstaculos.append(r_bar.inflate(4, 4))

        for idx, inimigo in enumerate(vivos):
            titulo = f"#{idx + 1} {inimigo.nome}"
            badges_e = self._montar_badges_entidade(inimigo, eh_jogador=False)
            r_spr = self.cs.rects_sprites_combate.get(inimigo)
            if r_spr:
                ancora_x = r_spr.centerx
                ancora_y = max(14, r_spr.top - 46)
            else:
                pos_x, pos_y = self.cs._obter_posicao_combate(inimigo)
                ancora_x = pos_x + 40
                ancora_y = max(14, pos_y - 40)
            destaque = self.cs.estado_combate == "SELECIONANDO_ALVO" and idx == self.cs.indice_alvo
            card_e = self._desenhar_card_status(
                tela, titulo, badges_e,
                x=ancora_x, y=ancora_y, max_largura=270,
                cor_titulo=(255, 240, 200) if destaque else (252, 232, 224),
                direita=False, compacto=True, centralizado=True,
                obstaculos=obstaculos, destaque=destaque,
            )
            self.cs.rects_hud_status[inimigo] = card_e
            obstaculos.append(card_e.inflate(8, 6))

    def atualizar_animacoes(self, dt_efetivo):
        """Avança as animações e transições de estado de Halia e inimigos no ciclo update()."""
        if self.cs.jogador and hasattr(self.cs.jogador, "animacoes"):
            estado_h = self.cs.obter_estado_animacao_halia()
            anim_h = self.cs.jogador.animacoes.get(estado_h)
            if anim_h:
                anim_h.atualizar(dt_efetivo)
                if estado_h == "combate_special" and getattr(anim_h, "concluida", False):
                    self.cs.animando_magia_halia = False
                    anim_idle = self.cs.jogador.animacoes.get("combate_idle")
                    if anim_idle:
                        anim_idle.resetar()

        for inimigo in self.cs.inimigos:
            esta_vivo = getattr(inimigo, 'vivo', True) and getattr(inimigo, 'vida_atual', 1) > 0
            if hasattr(inimigo, 'atualizar_animacao'):
                if esta_vivo:
                    est = getattr(inimigo, 'estado_atual', 'idle')
                    if est == 'hurt' and getattr(inimigo.animacoes.get('hurt'), 'concluida', False):
                        inimigo.definir_estado('idle')
                    elif est in ('attack', 'ataque'):
                        anim_atk = inimigo.animacoes.get('attack') or inimigo.animacoes.get('ataque')
                        if getattr(anim_atk, 'concluida', False):
                            inimigo.definir_estado('idle')
                else:
                    if getattr(inimigo, 'estado_atual', '') not in ('dead', 'morte', 'morrer'):
                        for est_m in ('dead', 'morte', 'morrer'):
                            if est_m in inimigo.animacoes:
                                inimigo.definir_estado(est_m)
                                break
                inimigo.atualizar_animacao(dt_efetivo)

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

    def _resolver_sprite_combate_inimigo(self, inimigo):
        """Obtém o sprite de combate do inimigo em escala proporcional à sua altura opaca."""
        if hasattr(inimigo, '_sincronizar_imagem_atual'):
            inimigo._sincronizar_imagem_atual()

        imagem = getattr(inimigo, 'imagem_atual', None)
        if not imagem:
            return None

        pasta_sprites = getattr(inimigo, 'pasta_sprites', None)
        altura_alvo = getattr(inimigo, 'altura_combate_alvo', None)
        estado_atual = getattr(inimigo, 'estado_atual', 'idle')
        anims = getattr(inimigo, 'animacoes', None) or {}
        anim_atual = anims.get(estado_atual)

        img_base = None
        if (
            pasta_sprites
            and altura_alvo
            and anim_atual
            and getattr(anim_atual, 'frames', None)
            and imagem is anim_atual.get_imagem()
        ):
            img_base = ResourceManager.obter_frame_combate_inimigo(
                pasta_sprites, estado_atual, int(anim_atual.frame_atual), altura_alvo
            )

        if img_base is None:
            escala_c = getattr(inimigo, 'escala_combate', 0.85)
            if altura_alvo:
                anim_ref = anims.get('idle')
                ref_surf = anim_ref.frames[0] if (anim_ref and getattr(anim_ref, 'frames', None)) else imagem
                br_ref = ref_surf.get_bounding_rect()
                if br_ref.height > 0:
                    escala_c = float(altura_alvo) / float(br_ref.height)
            nw = max(1, int(round(imagem.get_width() * escala_c)))
            nh = max(1, int(round(imagem.get_height() * escala_c)))
            img_base = imagem if (nw, nh) == imagem.get_size() else pygame.transform.scale(imagem, (nw, nh))

        # Inimigos na direita da arena encaram Halia na esquerda
        if getattr(inimigo, 'virado_direita', True):
            return pygame.transform.flip(img_base, True, False)
        return img_base

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
        self.cs.rects_hud_status.clear()
        self.cs.rects_sprites_combate.clear()
        self.cs._rects_barras_inimigos = []
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
            cx = draw_x + 40
            cy = draw_y + 90

            img_combate = self._resolver_sprite_combate_inimigo(inimigo)
            rect_visivel = None
            bx = draw_x
            by = draw_y

            if img_combate:
                nw, nh = img_combate.get_size()
                offset_flutuante = -16 if (getattr(inimigo, 'flutuante', False) and esta_vivo) else 0
                bb_vis = img_combate.get_bounding_rect()
                if bb_vis.width > 0 and bb_vis.height > 0:
                    bx = cx - (bb_vis.x + bb_vis.width // 2)
                    by = (cy + offset_flutuante) - bb_vis.bottom
                    rect_visivel = pygame.Rect(bx + bb_vis.x, by + bb_vis.y, bb_vis.width, bb_vis.height)
                else:
                    bx = cx - (nw // 2)
                    by = cy - nh + offset_flutuante
                    rect_visivel = pygame.Rect(bx, by, nw, nh)
                self.cs.rects_sprites_combate[inimigo] = rect_visivel
            else:
                rect_visivel = pygame.Rect(draw_x, draw_y, getattr(inimigo, 'largura', 40) * 2, getattr(inimigo, 'altura', 40) * 2)
                self.cs.rects_sprites_combate[inimigo] = rect_visivel

            # Plataforma / Sombra sutil no chão proporcional à envergadura do monstro
            if esta_vivo or alpha_morte > 60:
                larg_sombra = max(100, min(280, rect_visivel.width + 22))
                sombra_x = cx - (larg_sombra // 2)
                sombra_y = cy - 10
                if esta_vivo or alpha_morte >= 250:
                    pygame.draw.ellipse(tela, (22, 22, 26), (sombra_x, sombra_y, larg_sombra, 20))
                else:
                    sombra_surf = pygame.Surface((larg_sombra, 20), pygame.SRCALPHA)
                    alpha_sombra = int(220 * (alpha_morte / 255.0))
                    pygame.draw.ellipse(sombra_surf, (22, 22, 26, alpha_sombra), (0, 0, larg_sombra, 20))
                    tela.blit(sombra_surf, (sombra_x, sombra_y))

            # Hitbox para clique de mouse e cursor de mira (apenas se vivo)
            if esta_vivo:
                rect_hitbox = pygame.Rect(
                    0,
                    0,
                    max(96, rect_visivel.width + 24),
                    max(96, rect_visivel.height + 12),
                )
                rect_hitbox.center = rect_visivel.center
                rect_hitbox = rect_hitbox.union(rect_visivel.inflate(16, 10))
                self.cs.rects_inimigos.append(rect_hitbox)

                if self.cs.estado_combate == "SELECIONANDO_ALVO" and self.cs.indice_alvo < len(inimigos_vivos) and inimigos_vivos[self.cs.indice_alvo] is inimigo:
                    cursor_txt = self.cs.fonte_titulo.render(">", True, TXT_SISTEMA_NARRADOR)
                    cursor_x = min(draw_x - 30, rect_hitbox.left - 22)
                    tela.blit(cursor_txt, (cursor_x, rect_hitbox.centery - 18))
                    pygame.draw.rect(tela, TXT_SISTEMA_NARRADOR, rect_hitbox, 1)

            # Renderiza Imagem ou Bloco Colorido
            if img_combate:
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
                cor_bloco = BRANCO if (esta_vivo and self.cs.shake_timers.get(inimigo, 0) > 6) else (getattr(inimigo, 'cor', (140, 40, 50)) if esta_vivo else (60, 60, 70))
                pygame.draw.rect(tela, cor_bloco, rect_visivel)
                pygame.draw.rect(tela, CINZA_CLARO, rect_visivel, 2)

            # Interface de Status (Barras abaixo da plataforma; nomes/condições nos cartões superiores)
            if esta_vivo:
                base_bar_y = draw_y + 105
                larg_bar_inimigo = 150
                alt_bar = 12
                if len(inimigos_vivos) > 1 and inimigo in inimigos_vivos:
                    idx_v = inimigos_vivos.index(inimigo)
                    txt_idx = self.cs.fonte_status.render(f"#{idx_v + 1}", True, (246, 243, 236))
                    tela.blit(txt_idx, (draw_x - 36, base_bar_y - 2))
                vida_v = self.cs.vidas_visuais.get(inimigo, float(inimigo.vida_atual))
                self.desenhar_barra(tela, draw_x - 15, base_bar_y, vida_v, inimigo.vida_maxima, BARRA_VIDA_INIMIGO, largura=larg_bar_inimigo, altura=alt_bar)
                txt_hp = self.cs.fonte_status.render(f"HP {int(round(vida_v))}/{inimigo.vida_maxima}", True, UI_TEXTO_DESTAQUE)
                tela.blit(txt_hp, (draw_x - 15 + larg_bar_inimigo + 10, base_bar_y - 2))

                # Barra de Mana Suave Interpolada do Monstro (Idêntico ao padrão visual de Halia)
                mana_max = getattr(inimigo, 'mana_maxima', 20)
                mana_v = self.cs.manas_visuais.get(inimigo, float(getattr(inimigo, 'mana_atual', mana_max)))
                mp_bar_y = base_bar_y + 20
                self.desenhar_barra(tela, draw_x - 15, mp_bar_y, mana_v, mana_max, BARRA_MANA, largura=larg_bar_inimigo, altura=alt_bar)
                txt_mp = self.cs.fonte_status.render(f"MP {int(round(mana_v))}/{mana_max}", True, UI_TEXTO_DESTAQUE)
                tela.blit(txt_mp, (draw_x - 15 + larg_bar_inimigo + 10, mp_bar_y - 2))
                self.cs._rects_barras_inimigos.append(pygame.Rect(draw_x - 42, base_bar_y - 4, 260, 42))

        # 3. RENDERIZAR HALIA COM AS NOVAS SPRITES DE ALTA FIDELIDADE (Lado Esquerdo)
        halia_x, halia_y = self.cs._obter_posicao_combate(self.cs.jogador)
        offset_h_x = random.randint(-3, 3) if self.cs.shake_timers.get(self.cs.jogador, 0) > 0 else 0
        offset_h_y = random.randint(-2, 2) if self.cs.shake_timers.get(self.cs.jogador, 0) > 0 else 0
        
        draw_hx = halia_x + offset_h_x
        draw_hy = halia_y + offset_h_y

        # Seleciona o estado da animação oficial da Halia no combate sem mutar cursores em render
        if hasattr(self.cs, "obter_estado_animacao_halia"):
            estado_halia = self.cs.obter_estado_animacao_halia()
        else:
            estado_halia = "combate_special" if getattr(self.cs, "animando_magia_halia", False) else "combate_idle"

        img_halia = None
        anims_h = getattr(self.cs.jogador, 'animacoes', {})
        for cand_h in (estado_halia, "combate_idle", "idle_direita", "idle"):
            anim_h = anims_h.get(cand_h)
            if anim_h and getattr(anim_h, "frames", None):
                img_halia = anim_h.get_imagem()
                break

        if not img_halia:
            img_halia = getattr(self.cs.jogador, 'imagem_atual', None)

        alt_h = 120
        larg_h = 50
        ponto_pes_x = draw_hx + 28
        ponto_pes_y = draw_hy + alt_h

        if img_halia:
            ow_h, oh_h = img_halia.get_size()
            altura_corpo = getattr(self.cs.jogador, "altura_corpo_combate", None)
            altura_canvas = getattr(self.cs.jogador, "altura_canvas_combate", oh_h)
            if estado_halia.startswith("combate_") and altura_corpo and oh_h == altura_canvas:
                escala_h = alt_h / float(altura_corpo)
                larg_c = max(1, int(round(ow_h * escala_h)))
                alt_c = max(1, int(round(oh_h * escala_h)))
                img_c = img_halia if (larg_c, alt_c) == (ow_h, oh_h) else pygame.transform.scale(img_halia, (larg_c, alt_c))
                bx_h = ponto_pes_x - (larg_c // 2)
                by_h = ponto_pes_y - alt_c
                larg_h = 56
            else:
                larg_h = max(1, int(alt_h * (ow_h / oh_h)))
                img_c = pygame.transform.scale(img_halia, (larg_h, alt_h))
                bx_h = draw_hx
                by_h = draw_hy

        # Plataforma / Sombra sutil no chão sob Halia ancorada aos pés
        pygame.draw.ellipse(tela, (22, 22, 26), (ponto_pes_x - 38, ponto_pes_y - 12, 76, 22))

        if img_halia:
            bb_h = img_c.get_bounding_rect()
            if bb_h.width > 0 and bb_h.height > 0:
                self.cs.rects_sprites_combate["jogador"] = pygame.Rect(bx_h + bb_h.x, by_h + bb_h.y, bb_h.width, bb_h.height)
            if self.cs.shake_timers.get(self.cs.jogador, 0) > 6:
                flash_surf = img_c.copy()
                flash_surf.fill((255, 255, 255, 180), special_flags=pygame.BLEND_RGBA_MULT)
                tela.blit(flash_surf, (bx_h, by_h))
            else:
                tela.blit(img_c, (bx_h, by_h))
        else:
            rect_h = pygame.Rect(draw_hx, draw_hy, larg_h, alt_h)
            self.cs.rects_sprites_combate["jogador"] = rect_h
            cor_h = BRANCO if self.cs.shake_timers.get(self.cs.jogador, 0) > 6 else (34, 139, 34)
            pygame.draw.rect(tela, cor_h, rect_h)
            pygame.draw.rect(tela, CINZA_CLARO, rect_h, 2)

        # Efeito Visual de Respingo de Sangue sobre Halia ao Sofrer Dano
        if self.cs.efeitos_sangue:
            hx_centro = ponto_pes_x
            hy_centro = ponto_pes_y - (alt_h // 2)
            for ef in self.cs.efeitos_sangue:
                idx_s = int(ef["frame_atual"])
                frames_s = ef["frames"]
                if 0 <= idx_s < len(frames_s):
                    frame_s = frames_s[idx_s]
                    pos_sx = hx_centro - (frame_s.get_width() // 2) + ef.get("offset_x", 0)
                    pos_sy = hy_centro - (frame_s.get_height() // 2) + ef.get("offset_y", 0)
                    tela.blit(frame_s, (pos_sx, pos_sy))

        # Barras Interpoladas de HP e MP da Halia (Abaixo da plataforma dos pés, sem sobrepor botas)
        vida_h_v = self.cs.vidas_visuais.get(self.cs.jogador, float(self.cs.jogador.vida_atual))
        mana_h_v = self.cs.manas_visuais.get(self.cs.jogador, float(self.cs.jogador.mana_atual))
        larg_h_bar = 180
        alt_h_bar = 12
        base_h_bar_y = draw_hy + 135

        self.desenhar_barra(tela, draw_hx, base_h_bar_y, vida_h_v, self.cs.jogador.vida_maxima, BARRA_VIDA_JOGADOR, largura=larg_h_bar, altura=alt_h_bar)
        hp_mostrado = 0 if (self.cs.jogador.vida_atual <= 0 or not getattr(self.cs.jogador, 'vivo', True)) else max(1, int(round(vida_h_v)))
        tela.blit(self.cs.fonte_status.render(f"HP {hp_mostrado}/{self.cs.jogador.vida_maxima}", True, UI_TEXTO_DESTAQUE), (draw_hx + larg_h_bar + 10, base_h_bar_y - 2))

        self.desenhar_barra(tela, draw_hx, base_h_bar_y + 20, mana_h_v, self.cs.jogador.mana_maxima, BARRA_MANA, largura=larg_h_bar, altura=alt_h_bar)
        tela.blit(self.cs.fonte_status.render(f"MP {int(round(mana_h_v))}/{self.cs.jogador.mana_maxima}", True, UI_TEXTO_DESTAQUE), (draw_hx + larg_h_bar + 10, base_h_bar_y + 18))

        # Efeitos Mágicos Visuais (Projéteis Direcionados, Rastros, Flashes e Explosões Elementais)
        if hasattr(self.cs, "efeitos_visuais") and self.cs.efeitos_visuais:
            self.cs.efeitos_visuais.desenhar(tela)

        # Cartões superiores reservados (nomes, fúria, alerta de sopro, condições)
        self._desenhar_headers_status(tela)

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
                    marcador = ">  "
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
                    marcador = "> "
                else:
                    pygame.draw.rect(tela, (18, 18, 22), item_rect, border_radius=2)
                    pygame.draw.rect(tela, CINZA_ARDOSIA, item_rect, 1, border_radius=2)
                    cor = CINZA_LINHO
                    marcador = "  "
                    
                custo_atq = ataque.obter_custo_mana(self.cs.jogador) if hasattr(ataque, 'obter_custo_mana') else getattr(ataque, 'custo_mana', 0)
                custo_str = f"({custo_atq} MP)" if custo_atq > 0 else ""
                eh_aoe = getattr(ataque, 'alvo_tipo', '') in ["TODOS_INIMIGOS", "TODOS"] or getattr(ataque, 'tipo_alvo', '') in ["todos_inimigos", "todos"]
                aoe_tag = " [ÁREA]" if eh_aoe else ""
                txt = self.cs.fonte_menu.render(f"{marcador}{ataque.nome} {custo_str}{aoe_tag}".strip(), True, cor)
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
                    marcador = "> "
                else:
                    pygame.draw.rect(tela, (18, 18, 22), item_rect, border_radius=2)
                    pygame.draw.rect(tela, CINZA_ARDOSIA, item_rect, 1, border_radius=2)
                    cor = CINZA_LINHO
                    marcador = "  "
                    
                custo_efetivo = magia.obter_custo_mana(self.cs.jogador) if hasattr(magia, 'obter_custo_mana') else magia.custo_mana
                custo_txt = f"({custo_efetivo} MP)" if custo_efetivo > 0 else "(Grátis)"
                eh_aoe = getattr(magia, 'alvo_tipo', '') in ["TODOS_INIMIGOS", "TODOS"] or getattr(magia, 'tipo_alvo', '') in ["todos_inimigos", "todos"]
                aoe_tag = " [ÁREA]" if eh_aoe else ""
                txt = self.cs.fonte_menu.render(f"{marcador}{magia.nome} {custo_txt}{aoe_tag}", True, cor)
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
                    marcador = "> "
                else:
                    pygame.draw.rect(tela, (18, 18, 22), item_rect, border_radius=2)
                    pygame.draw.rect(tela, CINZA_ARDOSIA, item_rect, 1, border_radius=2)
                    cor = CINZA_LINHO
                    marcador = "  "
                    
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
                    marcador = "> "
                else:
                    pygame.draw.rect(tela, (18, 18, 22), item_rect, border_radius=2)
                    pygame.draw.rect(tela, CINZA_ARDOSIA, item_rect, 1, border_radius=2)
                    cor = CINZA_LINHO
                    marcador = "  "
                    
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
                prefixo = f"#{i + 1} " if len(inimigos_vivos) > 1 else ""
                txt_i = self.cs.fonte_status.render(f"{marcador}{prefixo}{inimigo.nome} ({inimigo.vida_atual}/{inimigo.vida_maxima} HP)", True, cor)
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
        custo = acao.obter_custo_mana(self.cs.jogador) if hasattr(acao, 'obter_custo_mana') else getattr(acao, 'custo_mana', 0)
        custo_str = f" | Custo: {custo} MP" if custo > 0 else (" | Custo: Grátis" if tipo == "MAGICO" else "")

        alvo_t = str(getattr(acao, 'alvo_tipo', getattr(acao, 'tipo_alvo', ''))).upper()
        if alvo_t in ("TODOS_INIMIGOS", "TODOS"):
            alvo_tag = " [ÁREA]"
            alvo_info = " | Alvo: Todos os Inimigos"
        elif alvo_t in ("PROPRIO", "ALIADO"):
            alvo_tag = ""
            alvo_info = " | Alvo: Próprio"
        else:
            alvo_tag = ""
            alvo_info = " | Alvo: Inimigo Único"

        if categoria == "CONSUMIVEL":
            tipo_c = getattr(acao, 'tipo_consumivel', '')
            if tipo_c == "CURA_HP":
                detalhe = f"[ITEM CURA] {acao.nome} | Restaura {getattr(acao, 'valor_efeito', 0)} HP{alvo_info} - {desc}"
            elif tipo_c == "RESTAURA_MP":
                detalhe = f"[ITEM MANA] {acao.nome} | Restaura {getattr(acao, 'valor_efeito', 0)} MP{alvo_info} - {desc}"
            elif tipo_c == "DANO_OFENSIVO":
                detalhe = f"[ITEM OFENSIVO{alvo_tag}] {acao.nome} | Causa {getattr(acao, 'valor_efeito', 0)} Dano{alvo_info} - {desc}"
            else:
                detalhe = f"[ITEM] {acao.nome}{alvo_info} - {desc}"
        elif tipo == "MAGICO":
            bonus_m = self.cs.jogador.maestria_feiticos.get(getattr(acao, 'id_acao', ''), {}).get('bonus_poder', 0) if hasattr(self.cs.jogador, 'maestria_feiticos') else 0
            bonus_g = 0
            if hasattr(self.cs.jogador, 'inventario') and self.cs.jogador.inventario:
                for g_s in ['GRIMORIO_1', 'GRIMORIO_2', 'GRIMORIO_3', 'GRIMORIO_4']:
                    tomo = self.cs.jogador.inventario.equipados.get(g_s)
                    if tomo and getattr(tomo, 'magia_id', None) == getattr(acao, 'id_acao', ''):
                        bonus_g += getattr(tomo, 'bonus_poder', 0)
            p_base = getattr(acao, 'poder_base', 0)
            p_txt = f"{p_base} (+{bonus_m + bonus_g})" if (bonus_m + bonus_g) > 0 else f"{p_base}"
            detalhe = f"[{elemento}{alvo_tag}] {acao.nome}{custo_str} | Poder: {p_txt}{alvo_info} - {desc}"
        elif tipo == "FOCO":
            detalhe = f"[TÁTICO] {acao.nome} - {desc}"
        elif tipo == "DEFESA":
            detalhe = f"[TÁTICO] {acao.nome} - {desc}"
        elif tipo == "FISICO":
            detalhe = f"[FÍSICO{alvo_tag}] {acao.nome}{custo_str} | Poder: {getattr(acao, 'poder_base', 0)}{alvo_info} - {desc}"
        else:
            detalhe = f"[{elemento}{alvo_tag}] {acao.nome}{alvo_info} - {desc}"

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
            moedas = Player.formatar_valor_moedas(self.cs.recompensas_vitoria["moedas"], compacto=True)
            msg1 = f"Recompensas: +{moedas} | +{self.cs.recompensas_vitoria['memorias']} Memória(s)"
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
