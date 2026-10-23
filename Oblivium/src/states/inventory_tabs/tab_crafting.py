# src/states/inventory_tabs/tab_crafting.py
import pygame
from src.utils.colors import CINZA_LINHO
from src.ui.ui_utils import desenhar_card_pergaminho, desenhar_flor_botanica


class TabCraftingRenderer:
    """
    Renderizador dedicado para a aba [4] Bancada de Criação, Alquimia e Forja de Oblivium.

    Responsabilidades:
    - Renderização visual da bancada arcana de criação e refinamento de itens.
    - Exibição de avisos atmosféricos quando fora do alcance de bancadas de alquimia/forjas do mapa.
    """

    def __init__(self, state):
        self.state = state

    def desenhar(self, tela, halia):
        s = self.state
        r_selo = pygame.Rect(s.x_menu + 180, s.y_menu + 110, s.largura_menu - 360, 420)
        desenhar_card_pergaminho(tela, r_selo, cor_fundo=(18, 18, 22), cor_borda=(70, 70, 85))

        desenhar_flor_botanica(tela, r_selo.centerx, r_selo.y + 80, cor=(100, 100, 125), escala=1.5)

        txt_selo_tit = s.fonte_destaque.render("✦ Bancada de Criação & Alquimia Selada ✦", True, (220, 205, 150))
        tela.blit(txt_selo_tit, (r_selo.centerx - txt_selo_tit.get_width() // 2, r_selo.y + 160))

        linhas_selo = [
            "A confecção de itens, transmutação e refinamento de equipamentos exigem uma bancada apropriada.",
            "Explore o mundo de Oblivium e descubra receitas ancestrais para desbloquear suas criações.",
            "Encontre bancadas de alquimia ou forjas arcanas pelo mapa para manipular reagentes."
        ]

        y_s = r_selo.y + 215
        for ls in linhas_selo:
            txt_ls = s.fonte_texto.render(ls, True, CINZA_LINHO)
            tela.blit(txt_ls, (r_selo.centerx - txt_ls.get_width() // 2, y_s))
            y_s += 30
