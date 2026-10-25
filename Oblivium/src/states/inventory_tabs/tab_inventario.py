# src/states/inventory_tabs/tab_inventario.py
import pygame
from src.utils.colors import (
    BORDA_DESTAQUE, CINZA_LINHO, CINZA_ARDOSIA, MARFIM_OFFWHITE, DOURADO_ENVELHECIDO
)
from src.ui.ui_utils import desenhar_card_pergaminho
from src.ui.icon_registry import (
    IconRegistry,
    desenhar_icone_slot_inventario,
    desenhar_estrela_quatro_pontas
)


class TabInventarioRenderer:
    """
    Renderizador dedicado para a aba [1] Inventário & Equipamentos de Oblivium.

    Responsabilidades:
    - Renderização dos 4 slots de Equipamentos arcanos (Roupa, Cajado, Acessórios I e II) mantendo seus ícones de slot.
    - Renderização dos 4 slots de Grimórios arcanos despertados.
    - Painel pergaminho com Guia Rápido de comandos.
    - Navegação e renderização das sub-abas de filtro da bolsa (Bolsa, Equipamentos, Materiais, Outros).
    - Renderização da grelha de itens da bolsa usando apenas as sprites de itens existentes no jogo
      e mantendo o modelo antigo (apenas texto) caso não exista sprite para o item.
    """

    def __init__(self, state):
        self.state = state

    def desenhar(self, tela, halia):
        s = self.state
        inv = getattr(halia, 'inventario', None) if halia else None

        # 1. EQUIPAMENTOS (Topo Esquerdo)
        txt_eq = s.fonte_sub.render("Equipamentos Arcanos", True, MARFIM_OFFWHITE)
        tela.blit(txt_eq, (s.x_menu + 45, s.y_menu + 78))

        slots_eq_dados = [
            (s.slot_roupa, "ROUPA", "Roupa"),
            (s.slot_cajado, "CAJADO", "Cajado"),
            (s.slot_acess1, "ACESSORIO_1", "Acessório I"),
            (s.slot_acess2, "ACESSORIO_2", "Acessório II")
        ]

        for rect_s, nome_s, rotulo in slots_eq_dados:
            hover = (s.slot_hover and s.slot_hover[0] == "equipamento" and s.slot_hover[1] == nome_s)
            item_eq = inv.equipados.get(nome_s) if inv else None

            fundo_s = (36, 36, 46) if hover else (22, 22, 26)
            borda_s = BORDA_DESTAQUE if hover else CINZA_LINHO
            pygame.draw.rect(tela, fundo_s, rect_s, border_radius=3)
            pygame.draw.rect(tela, borda_s, rect_s, 2 if hover else 1, border_radius=3)

            lbl_rot = s.fonte_mini.render(rotulo, True, (130, 130, 140))
            tela.blit(lbl_rot, (rect_s.x + 6, rect_s.y + 4))

            # Ícone do slot (mantém o ícone antigo do slot ou a sprite real caso o item equipado possua)
            rect_icone_eq = pygame.Rect(rect_s.x + 16, rect_s.y + 19, rect_s.width - 32, rect_s.height - 38)
            desenhar_icone_slot_inventario(
                tela, rect_icone_eq,
                item_eq if item_eq else nome_s,
                equipado=bool(item_eq)
            )

            if item_eq:
                txt_item = s.fonte_mini.render(item_eq.nome[:10], True, MARFIM_OFFWHITE)
                tela.blit(txt_item, (rect_s.centerx - txt_item.get_width() // 2, rect_s.bottom - txt_item.get_height() - 4))
                up = getattr(item_eq, 'nivel_upgrade', 0)
                if up > 0:
                    txt_up = s.fonte_mini.render(f"+{up}", True, (230, 210, 120))
                    tela.blit(txt_up, (rect_s.right - txt_up.get_width() - 5, rect_s.y + 4))
            else:
                lbl_vazio = s.fonte_mini.render("Vazio", True, (90, 90, 100))
                tela.blit(lbl_vazio, (rect_s.centerx - lbl_vazio.get_width() // 2, rect_s.bottom - lbl_vazio.get_height() - 4))

        # 2. SLOTS DE GRIMÓRIOS (4 Espaços Abaixo dos Equipamentos)
        txt_gr = s.fonte_sub.render("Grimórios Despertados (4 Espaços)", True, MARFIM_OFFWHITE)
        tela.blit(txt_gr, (s.x_menu + 45, s.y_menu + 225))

        for i, rect_g in enumerate(s.slots_grimorios):
            chave_g = f"GRIMORIO_{i+1}"
            hover_g = (s.slot_hover and s.slot_hover[0] == "equipamento" and s.slot_hover[1] == chave_g)
            item_g = inv.equipados.get(chave_g) if inv else None

            fundo_g = (36, 36, 46) if hover_g else (22, 22, 26)
            borda_g = BORDA_DESTAQUE if hover_g else CINZA_LINHO
            pygame.draw.rect(tela, fundo_g, rect_g, border_radius=3)
            pygame.draw.rect(tela, borda_g, rect_g, 2 if hover_g else 1, border_radius=3)

            lbl_g_rot = s.fonte_mini.render(f"Grimório {i+1}", True, (130, 130, 140))
            tela.blit(lbl_g_rot, (rect_g.x + 6, rect_g.y + 4))

            # Ícone do slot de grimório (ou sprite oficial do Grimório quando equipado)
            rect_icone_gr = pygame.Rect(rect_g.x + 16, rect_g.y + 19, rect_g.width - 32, rect_g.height - 38)
            desenhar_icone_slot_inventario(
                tela, rect_icone_gr,
                item_g if item_g else chave_g,
                equipado=bool(item_g)
            )

            if item_g:
                txt_item_g = s.fonte_mini.render(item_g.nome[:10], True, (240, 225, 160))
                tela.blit(txt_item_g, (rect_g.centerx - txt_item_g.get_width() // 2, rect_g.bottom - txt_item_g.get_height() - 4))
            else:
                lbl_vazio_g = s.fonte_mini.render("Vazio", True, (90, 90, 100))
                tela.blit(lbl_vazio_g, (rect_g.centerx - lbl_vazio_g.get_width() // 2, rect_g.bottom - lbl_vazio_g.get_height() - 4))

        # Painel Informativo Inferior Esquerdo (Guia Rápido)
        r_inst = pygame.Rect(s.x_menu + 45, s.y_menu + 375, 360, 180)
        desenhar_card_pergaminho(tela, r_inst, cor_fundo=(20, 20, 24), cor_borda=CINZA_ARDOSIA)
        desenhar_estrela_quatro_pontas(tela, r_inst.x + 22, r_inst.y + 22, 5, 2, (210, 195, 140))
        tela.blit(s.fonte_mini.render("GUIA RÁPIDO DE INVENTÁRIO", True, (210, 195, 140)), (r_inst.x + 32, r_inst.y + 14))
        linhas_guia = [
            "• Passe o cursor sobre itens para ler suas propriedades.",
            "• [Clique Esquerdo] Usa consumíveis ou veste equipamentos.",
            "• [Clique Direito] Remove o equipamento para a bolsa.",
            "• Os Grimórios equipados contêm feitiços ancestrais."
        ]
        y_g = r_inst.y + 42
        for lg in linhas_guia:
            tela.blit(s.fonte_mini.render(lg, True, CINZA_LINHO), (r_inst.x + 16, y_g))
            y_g += 26

        # Linha vertical separadora
        pygame.draw.line(tela, CINZA_ARDOSIA, (s.x_menu + 445, s.y_menu + 75), (s.x_menu + 445, s.y_menu + s.altura_menu - 50), 1)

        # 3. SUB-ABAS DA BOLSA (Direita)
        s.rects_sub_abas_bolsa.clear()
        sub_x = s.x_menu + 475
        sub_y = s.y_menu + 76
        altura_sub = 28

        for s_idx, nome_sub in enumerate(s.sub_abas_bolsa):
            ativa_s = (s_idx == s.sub_aba_bolsa_ativa)
            txt_s = s.fonte_abas.render(nome_sub, True, MARFIM_OFFWHITE if ativa_s else CINZA_LINHO)
            largura_s = txt_s.get_width() + (30 if ativa_s else 18)

            rect_sub = pygame.Rect(sub_x, sub_y, largura_s, altura_sub)
            s.rects_sub_abas_bolsa.append(rect_sub)

            pygame.draw.rect(tela, (36, 36, 46) if ativa_s else (20, 20, 24), rect_sub, border_radius=2)
            pygame.draw.rect(tela, MARFIM_OFFWHITE if ativa_s else CINZA_ARDOSIA, rect_sub, 1, border_radius=2)
            if ativa_s:
                desenhar_estrela_quatro_pontas(tela, rect_sub.x + 11, rect_sub.centery, 4, 1, DOURADO_ENVELHECIDO)
                tela.blit(txt_s, (rect_sub.x + 19, rect_sub.centery - txt_s.get_height() // 2))
            else:
                tela.blit(txt_s, (rect_sub.centerx - txt_s.get_width() // 2, rect_sub.centery - txt_s.get_height() // 2))
            sub_x += largura_s + 8

        # 4. GRELHA DE ITENS DA BOLSA
        cat_atual = s.mapa_sub_categorias[s.sub_aba_bolsa_ativa]
        itens_filtrados = inv.obter_itens_por_categoria(cat_atual) if inv else []

        for idx_slot, rect_g in enumerate(s.slots_gerais):
            hover_g = (s.slot_hover and s.slot_hover[0] == "bolsa" and rect_g.collidepoint(s.pos_mouse))
            fundo_g = (34, 34, 42) if hover_g else (18, 18, 22)
            borda_g = BORDA_DESTAQUE if hover_g else CINZA_ARDOSIA

            pygame.draw.rect(tela, fundo_g, rect_g, border_radius=3)
            pygame.draw.rect(tela, borda_g, rect_g, 2 if hover_g else 1, border_radius=3)

            if idx_slot < len(itens_filtrados):
                idx_real, item_slot = itens_filtrados[idx_slot]
                item = item_slot.item
                qtd = item_slot.quantidade

                nome_formatado = item.nome_formatado if hasattr(item, 'nome_formatado') else item.nome
                cat_txt = "Grimório" if item.categoria == "GRIMORIO" else item.categoria.capitalize()
                txt_cat = s.fonte_mini.render(cat_txt[:10], True, (130, 130, 145))

                # Usa apenas a sprite do item caso ela exista oficialmente no jogo
                sprite_item = IconRegistry.obter_sprite_item(item, (40, 40))
                if sprite_item:
                    tela.blit(sprite_item, (rect_g.centerx - sprite_item.get_width() // 2, rect_g.y + 24))

                    txt_item = s.fonte_mini.render(nome_formatado[:15] + (".." if len(nome_formatado) > 15 else ""), True, MARFIM_OFFWHITE)
                    tela.blit(txt_item, (rect_g.x + 8, rect_g.y + 6))
                    tela.blit(txt_cat, (rect_g.x + 8, rect_g.bottom - txt_cat.get_height() - 5))
                else:
                    # Modelo antigo (apenas texto) caso não exista sprite para o item
                    txt_item = s.fonte_mini.render(nome_formatado[:14] + ("..." if len(nome_formatado) > 14 else ""), True, MARFIM_OFFWHITE)
                    tela.blit(txt_item, (rect_g.x + 8, rect_g.y + 10))
                    tela.blit(txt_cat, (rect_g.x + 8, rect_g.y + 36))

                if qtd > 1 or item.acumulavel:
                    txt_qtd = s.fonte_mini.render(f"x{qtd}", True, (230, 215, 150))
                    tela.blit(txt_qtd, (rect_g.right - txt_qtd.get_width() - 8, rect_g.bottom - txt_qtd.get_height() - 6))
            else:
                desenhar_icone_slot_inventario(tela, rect_g, "VAZIO_BOLSA", equipado=False)
