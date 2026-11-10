# src/states/inventory_tabs/tab_magia.py
import pygame
from src.utils.colors import (
    CINZA_LINHO, CINZA_ARDOSIA, MARFIM_OFFWHITE, BORDA_DESTAQUE, DOURADO_ENVELHECIDO
)
from src.ui.ui_utils import (
    desenhar_painel_padrao,
    desenhar_flor_botanica,
    desenhar_card_pergaminho,
    desenhar_estrela_quatro_pontas,
    quebrar_texto_em_linhas
)
from src.mechanics.skills import ActionCatalog


class TabMagiaRenderer:
    """
    Renderizador dedicado para a aba [3] Grimório de Magia de Oblivium.

    Responsabilidades:
    - Verificação de bloqueio arcano (selo de memória caso o flashback inicial não esteja concluído).
    - Renderização da coluna esquerda com a lista navegável e com scroll de feitiços arcanos.
    - Renderização da coluna direita com detalhes completos: badges de elemento/custo/categoria,
      cálculo de escalamento de intelecto, descrição narrativa e reflexões de canalização.
    """

    def __init__(self, state):
        self.state = state

    def desenhar(self, tela, halia):
        s = self.state
        flashback_concluido = getattr(s.game, 'flashback_magia_concluido', False) or (halia and halia.fragmentos_memoria > 0)

        if not flashback_concluido:
            r_selo = pygame.Rect(s.x_menu + 180, s.y_menu + 110, s.largura_menu - 360, 420)
            desenhar_card_pergaminho(tela, r_selo, cor_fundo=(18, 18, 22), cor_borda=(70, 70, 85))

            desenhar_flor_botanica(tela, r_selo.centerx, r_selo.y + 80, cor=(90, 90, 110), escala=1.5)

            txt_selo_tit = s.fonte_destaque.render("Conhecimento Arcano Selado", True, (220, 205, 150))
            tx = r_selo.centerx - txt_selo_tit.get_width() // 2
            ty = r_selo.y + 160
            tela.blit(txt_selo_tit, (tx, ty))
            desenhar_estrela_quatro_pontas(tela, tx - 14, ty + 10, 6, 2, (220, 205, 150))
            desenhar_estrela_quatro_pontas(tela, tx + txt_selo_tit.get_width() + 14, ty + 10, 6, 2, (220, 205, 150))

            linhas_selo = [
                "Os feitiços arcanos e os mistérios ancestrais de Halia repousam em silêncio.",
                "As páginas do Grimório ainda aguardam o despertar da memória arcana.",
                "Investigue os obstáculos da estrada para reconectar-se com sua essência mágica."
            ]

            y_s = r_selo.y + 215
            for ls in linhas_selo:
                txt_ls = s.fonte_texto.render(ls, True, CINZA_LINHO)
                tela.blit(txt_ls, (r_selo.centerx - txt_ls.get_width() // 2, y_s))
                y_s += 30
            return

        # CATÁLOGO DE MAGIAS DESBLOQUEADAS EM 2 COLUNAS
        magias_ids = getattr(halia, 'magias_desbloqueadas', ["bola_de_fogo", "levitar", "brisa_curativa"])
        if not magias_ids:
            magias_ids = ["bola_de_fogo", "levitar", "brisa_curativa"]

        if s.magia_selecionada_idx >= len(magias_ids):
            s.magia_selecionada_idx = 0

        w_lista = 390
        h_coluna = 465
        x_lista = s.x_menu + 45
        y_coluna = s.y_menu + 85

        r_painel_lista = pygame.Rect(x_lista, y_coluna, w_lista, h_coluna)
        desenhar_painel_padrao(tela, r_painel_lista, cor_fundo=(20, 20, 25), cor_borda=CINZA_LINHO, border_radius=4)

        tela.blit(s.fonte_sub.render(f"Grimório ({len(magias_ids)} Despertadas)", True, MARFIM_OFFWHITE), (x_lista + 18, y_coluna + 14))
        pygame.draw.line(tela, CINZA_ARDOSIA, (x_lista + 18, y_coluna + 42), (x_lista + w_lista - 18, y_coluna + 42), 1)

        y_itens_inicio = y_coluna + 50
        h_viewport = h_coluna - 60
        r_viewport = pygame.Rect(x_lista + 10, y_itens_inicio, w_lista - 20, h_viewport)

        antigo_clip = tela.get_clip()
        tela.set_clip(r_viewport)

        s.rects_lista_magias.clear()
        h_card_m = 76
        espacamento_m = 8
        altura_total_lista = len(magias_ids) * (h_card_m + espacamento_m)
        max_scroll = max(0, altura_total_lista - h_viewport)
        s.scroll_magias = max(0, min(s.scroll_magias, max_scroll))

        for idx_m, id_magia in enumerate(magias_ids):
            acao = ActionCatalog.get(id_magia)
            nome = acao.nome if acao else id_magia.replace('_', ' ').title()
            custo = acao.obter_custo_mana(halia) if (acao and hasattr(acao, 'obter_custo_mana')) else (acao.custo_mana if acao else 0)
            elemento = acao.elemento if acao else 'ARCANO'
            maestria_card = halia.maestria_feiticos.get(id_magia) if (halia and hasattr(halia, 'maestria_feiticos')) else None

            # Verifica se há tomo equipado vinculado a este feitiço
            tomo_card = None
            if halia and hasattr(halia, 'inventario') and halia.inventario:
                for g_s in ['GRIMORIO_1', 'GRIMORIO_2', 'GRIMORIO_3', 'GRIMORIO_4']:
                    t = halia.inventario.equipados.get(g_s)
                    if t and getattr(t, 'magia_id', None) == id_magia:
                        tomo_card = t
                        break

            pos_y_card = y_itens_inicio + (idx_m * (h_card_m + espacamento_m)) - s.scroll_magias
            r_card_item = pygame.Rect(x_lista + 14, pos_y_card, w_lista - 38, h_card_m)
            s.rects_lista_magias.append(r_card_item)

            esta_selecionada = (idx_m == s.magia_selecionada_idx)
            pos_m = pygame.mouse.get_pos()
            hover_card = r_card_item.collidepoint(pos_m)

            if esta_selecionada:
                fundo_c = (38, 38, 50)
                borda_c = BORDA_DESTAQUE
            elif hover_card:
                fundo_c = (30, 30, 38)
                borda_c = CINZA_LINHO
            else:
                fundo_c = (22, 22, 28)
                borda_c = (215, 185, 95) if tomo_card else CINZA_ARDOSIA

            pygame.draw.rect(tela, fundo_c, r_card_item, border_radius=3)
            pygame.draw.rect(tela, borda_c, r_card_item, 2 if (esta_selecionada or tomo_card) else 1, border_radius=3)

            if esta_selecionada:
                pygame.draw.rect(tela, (230, 215, 140), (r_card_item.x + 3, r_card_item.y + 6, 4, r_card_item.height - 12), border_radius=2)

            cor_nome = (245, 230, 165) if esta_selecionada else MARFIM_OFFWHITE
            desenhar_estrela_quatro_pontas(tela, r_card_item.x + 20, r_card_item.y + 22, 5, 2, cor_nome)

            # Badge de Maestria / Tomo Ativo no topo direito do card
            txt_m_badge = None
            w_badge_m = 0
            lvl_m = maestria_card.get('nivel_maestria', 0) if maestria_card else 0
            if tomo_card and lvl_m > 0:
                txt_m_badge = s.fonte_mini.render(f"Nv.{lvl_m} [Tomo]", True, (255, 225, 130))
            elif tomo_card:
                txt_m_badge = s.fonte_mini.render("✦ Tomo Ativo", True, (245, 220, 130))
            elif lvl_m > 0:
                txt_m_badge = s.fonte_mini.render(f"Nv.{lvl_m}", True, (245, 215, 120))

            if txt_m_badge:
                w_badge_m = txt_m_badge.get_width() + 10

            # Nome da Magia com limite anti-colisão em relação ao badge
            w_disp_nome = r_card_item.width - 45 - w_badge_m
            nome_render = nome
            if s.fonte_destaque.size(nome_render)[0] > w_disp_nome:
                while len(nome_render) > 3 and s.fonte_destaque.size(f"{nome_render}...")[0] > w_disp_nome:
                    nome_render = nome_render[:-1]
                nome_render = f"{nome_render}..."

            txt_nm = s.fonte_destaque.render(nome_render, True, cor_nome)
            tela.blit(txt_nm, (r_card_item.x + 30, r_card_item.y + 12))

            if txt_m_badge:
                r_badge_m = pygame.Rect(r_card_item.right - w_badge_m - 10, r_card_item.y + 12, w_badge_m, 20)
                cor_bg_b = (44, 36, 18) if tomo_card else (36, 32, 22)
                cor_bd_b = (225, 195, 95) if tomo_card else (215, 185, 95)
                pygame.draw.rect(tela, cor_bg_b, r_badge_m, border_radius=2)
                pygame.draw.rect(tela, cor_bd_b, r_badge_m, 1, border_radius=2)
                tela.blit(txt_m_badge, (r_badge_m.centerx - txt_m_badge.get_width() // 2, r_badge_m.centery - txt_m_badge.get_height() // 2))

            txt_elem = s.fonte_mini.render(f"{elemento.capitalize()}", True, (140, 190, 240))
            tela.blit(txt_elem, (r_card_item.x + 16, r_card_item.y + 42))

            txt_custo = s.fonte_mini.render(f"{custo} MP", True, (160, 240, 180))
            tela.blit(txt_custo, (r_card_item.right - txt_custo.get_width() - 14, r_card_item.y + 42))

        tela.set_clip(antigo_clip)

        if max_scroll > 0:
            trilho_x = x_lista + w_lista - 14
            trilho_y = y_itens_inicio
            trilho_h = h_viewport
            pygame.draw.rect(tela, (18, 18, 22), (trilho_x, trilho_y, 5, trilho_h), border_radius=2)

            tamanho_thumb = max(24, int((h_viewport / altura_total_lista) * trilho_h))
            thumb_y = trilho_y + int((s.scroll_magias / max_scroll) * (trilho_h - tamanho_thumb))
            pygame.draw.rect(tela, (160, 160, 180), (trilho_x, thumb_y, 5, tamanho_thumb), border_radius=2)

        # COLUNA DIREITA: DETALHES COMPLETOS
        w_detalhes = 620
        x_detalhes = s.x_menu + 465
        r_painel_det = pygame.Rect(x_detalhes, y_coluna, w_detalhes, h_coluna)
        desenhar_painel_padrao(tela, r_painel_det, cor_fundo=(20, 20, 25), cor_borda=CINZA_LINHO, border_radius=4)

        id_selecionada = magias_ids[s.magia_selecionada_idx]
        acao_sel = ActionCatalog.get(id_selecionada)
        nome_sel = acao_sel.nome if acao_sel else id_selecionada.replace("_", " ").title()
        custo_sel = acao_sel.obter_custo_mana(halia) if (acao_sel and hasattr(acao_sel, 'obter_custo_mana')) else (acao_sel.custo_mana if acao_sel else 0)
        elem_sel = acao_sel.elemento if acao_sel else "ARCANO"
        desc_sel = acao_sel.descricao if acao_sel else "Feitiço ancestral canalizado através da vontade mágica de Halia."
        tipo_acao = acao_sel.tipo if acao_sel else "OFENSIVA"
        maestria_sel = halia.maestria_feiticos.get(id_selecionada) if (halia and hasattr(halia, 'maestria_feiticos')) else None

        txt_tit_det = s.fonte_sub.render(nome_sel, True, (245, 230, 165))
        tela.blit(txt_tit_det, (x_detalhes + 24, y_coluna + 16))
        desenhar_flor_botanica(tela, x_detalhes + txt_tit_det.get_width() + 45, y_coluna + 26, cor=(210, 195, 140), escala=0.55)

        pygame.draw.line(tela, CINZA_ARDOSIA, (x_detalhes + 24, y_coluna + 46), (x_detalhes + w_detalhes - 24, y_coluna + 46), 1)

        # Verifica se há tomo equipado para a magia selecionada
        tomo_sel = None
        if halia and hasattr(halia, 'inventario') and halia.inventario:
            for g_s in ['GRIMORIO_1', 'GRIMORIO_2', 'GRIMORIO_3', 'GRIMORIO_4']:
                t = halia.inventario.equipados.get(g_s)
                if t and getattr(t, 'magia_id', None) == id_selecionada:
                    tomo_sel = t
                    break

        badges = [
            ("Elemento", elem_sel.capitalize(), (140, 190, 240)),
            ("Custo", f"{custo_sel} MP", (160, 240, 180)),
            ("Categoria", tipo_acao.capitalize(), (230, 210, 140))
        ]
        if maestria_sel and maestria_sel.get("nivel_maestria", 0) > 0:
            badges.append(("Maestria", f"Nv. {maestria_sel['nivel_maestria']}", (245, 215, 120)))
        if tomo_sel:
            badges.append(("Grimório", f"Equipado (+{tomo_sel.bonus_poder} Poder)", (255, 220, 140)))

        # 2. Badges com quebra automática e rastreamento dinâmico de Y (zero sobreposição)
        cur_y = y_coluna + 52
        x_badge = x_detalhes + 24
        y_badge = cur_y
        for rotulo_b, valor_b, cor_v in badges:
            txt_b = s.fonte_mini.render(f"{rotulo_b}: {valor_b}", True, cor_v)
            w_b = txt_b.get_width() + 16
            if x_badge + w_b > x_detalhes + w_detalhes - 24:
                x_badge = x_detalhes + 24
                y_badge += 28
            r_b = pygame.Rect(x_badge, y_badge, w_b, 22)
            pygame.draw.rect(tela, (26, 26, 34), r_b, border_radius=3)
            pygame.draw.rect(tela, CINZA_ARDOSIA, r_b, 1, border_radius=3)
            tela.blit(txt_b, (r_b.centerx - txt_b.get_width() // 2, r_b.centery - txt_b.get_height() // 2))
            x_badge += r_b.width + 8

        # Linha divisória posicionada dinamicamente após todos os badges
        cur_y = y_badge + 22 + 10
        pygame.draw.line(tela, CINZA_ARDOSIA, (x_detalhes + 24, cur_y), (x_detalhes + w_detalhes - 24, cur_y), 1)
        cur_y += 10

        attrs_tot = halia.obter_atributos_totais() if halia else None
        mod_int = attrs_tot.mod_int if attrs_tot else 0
        dano_base = getattr(acao_sel, 'poder_base', 12) if acao_sel else 12
        bonus_m = maestria_sel.get("bonus_poder", 0) if maestria_sel else 0
        bonus_tomo = getattr(tomo_sel, 'bonus_poder', 0) if tomo_sel else 0

        # Estatísticas de equipamentos arcanos (cajados, vestimentas, acessórios)
        poder_equip = 0
        bonus_elem_pct = 0
        if halia and hasattr(halia, 'inventario') and halia.inventario:
            totais = halia.inventario.obter_bonus_totais_equipamentos()
            st = totais.get("stats", {})
            poder_equip = st.get("poder_magico", 0) + st.get("dano_magico", 0)
            if elem_sel.upper() == "FOGO":
                bonus_elem_pct = st.get("dano_fogo_bonus", 0)
            elif elem_sel.upper() in ["GELO", "FRIO"]:
                bonus_elem_pct = st.get("dano_gelo_bonus", 0)
            elif tipo_acao == "CURA":
                bonus_elem_pct = st.get("cura_bonus", 0)

        # Potência Total com fórmula consolidada
        dano_bruto_est = dano_base + bonus_m + bonus_tomo + poder_equip + (mod_int * 2)
        if bonus_elem_pct > 0:
            dano_bruto_est = int(dano_bruto_est * (1.0 + (bonus_elem_pct / 100.0)))
        dano_estimado = dano_bruto_est

        # 3. Card de Escalamento Arcano estruturado em linhas verticais dedicadas (sem colisão horizontal)
        h_card_poder = 66
        r_card_poder = pygame.Rect(x_detalhes + 24, cur_y, w_detalhes - 48, h_card_poder)
        pygame.draw.rect(tela, (24, 24, 30), r_card_poder, border_radius=3)
        pygame.draw.rect(tela, (215, 185, 95) if (bonus_tomo > 0 or poder_equip > 0) else CINZA_ARDOSIA, r_card_poder, 1, border_radius=3)

        tela.blit(s.fonte_mini.render("ESCALAMENTO ARCANO & POTÊNCIA ESTIMADA", True, (210, 195, 140)), (r_card_poder.x + 14, r_card_poder.y + 7))

        txt_pot_esq = s.fonte_destaque.render(f"Potência: ~{dano_estimado} pts", True, MARFIM_OFFWHITE)
        tela.blit(txt_pot_esq, (r_card_poder.x + 14, r_card_poder.y + 24))

        if bonus_elem_pct > 0:
            txt_elem_tag = s.fonte_mini.render(f"+{bonus_elem_pct}% {elem_sel.capitalize()}", True, (150, 230, 240))
            tela.blit(txt_elem_tag, (r_card_poder.right - 14 - txt_elem_tag.get_width(), r_card_poder.y + 26))

        # Fórmula completa em linha separada sem jamais colidir com a potência
        partes_formula = [f"Base {dano_base}"]
        if bonus_m > 0:
            partes_formula.append(f"Maestria +{bonus_m}")
        if bonus_tomo > 0:
            partes_formula.append(f"Tomo +{bonus_tomo}")
        if poder_equip > 0:
            partes_formula.append(f"Equip +{poder_equip}")
        partes_formula.append(f"INT +{mod_int*2}")
        str_formula = f"Fórmula: { ' + '.join(partes_formula) }"
        if s.fonte_mini.size(str_formula)[0] > (r_card_poder.width - 28):
            b_tot = bonus_m + bonus_tomo + poder_equip
            str_formula = f"Fórmula: Base {dano_base} + Bônus +{b_tot} + INT +{mod_int*2}"

        txt_formula = s.fonte_mini.render(str_formula, True, (165, 205, 235))
        tela.blit(txt_formula, (r_card_poder.x + 14, r_card_poder.y + 45))

        cur_y += h_card_poder + 12

        # 4. Descrição do Feitiço
        tela.blit(s.fonte_mini.render("DESCRIÇÃO DO FEITIÇO", True, (210, 195, 140)), (x_detalhes + 24, cur_y))
        cur_y += 18
        linhas_desc = quebrar_texto_em_linhas(desc_sel, s.fonte_texto, w_detalhes - 54)
        for ld in linhas_desc[:3]:
            tela.blit(s.fonte_texto.render(ld, True, MARFIM_OFFWHITE), (x_detalhes + 24, cur_y))
            cur_y += 20
        cur_y += 10

        # 5. Card de Nota de Canalização / Reflexão Arcano
        espaco_restante = (y_coluna + h_coluna - 14) - cur_y
        if espaco_restante >= 55:
            h_ref = min(115, espaco_restante)
            r_ref = pygame.Rect(x_detalhes + 24, cur_y, w_detalhes - 48, h_ref)
            desenhar_card_pergaminho(tela, r_ref, cor_fundo=(22, 22, 26), cor_borda=CINZA_ARDOSIA)
            desenhar_estrela_quatro_pontas(tela, r_ref.x + 22, r_ref.y + 18, 5, 2, (220, 205, 140))
            tela.blit(s.fonte_mini.render("NOTA DE CANALIZAÇÃO", True, (220, 205, 140)), (r_ref.x + 32, r_ref.y + 10))

            reflexoes = {
                "bola_de_fogo": "A chama incinera obstáculos e abre caminhos obstruídos por galhos secos e vinhas do esquecimento.",
                "levitar": "A gravidade dobra-se à mente, permitindo erguer rochas colossais e afastar perigos sem confronto direto.",
                "brisa_curativa": "Um sopro vital restaurador que dissipa a fadiga física e acalma as feridas sofridas em combate."
            }
            nota_texto = reflexoes.get(id_selecionada, "Feitiço gravado nas memórias ancestrais da ordem dos guardiões arcanos.")
            linhas_ref = quebrar_texto_em_linhas(nota_texto, s.fonte_texto, w_detalhes - 85)
            max_linhas_ref = max(1, (h_ref - 36) // 20)
            y_tr = r_ref.y + 32
            for lr in linhas_ref[:max_linhas_ref]:
                tela.blit(s.fonte_texto.render(lr, True, CINZA_LINHO), (r_ref.x + 16, y_tr))
                y_tr += 20
