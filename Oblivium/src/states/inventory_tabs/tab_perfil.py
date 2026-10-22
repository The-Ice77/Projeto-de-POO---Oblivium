# src/states/inventory_tabs/tab_perfil.py
import pygame
from src.utils.colors import (
    CINZA_LINHO, CINZA_ARDOSIA, MARFIM_OFFWHITE,
    BARRA_VIDA_JOGADOR, BARRA_MANA
)
from src.ui.ui_utils import (
    desenhar_painel_padrao,
    desenhar_barra_status_interpolada
)


class TabPerfilRenderer:
    """
    Renderizador dedicado para a aba [2] Perfil e Ficha D20 de Halia em Oblivium.

    Responsabilidades:
    - Exibição de Recursos Vitais com barras interpoladas (HP e MP).
    - Exibição de Carteira decomposta (Moedas de Ouro, Prata e Cobre).
    - Cálculo visual de Parâmetros de Combate (Esquiva, Bloqueio/Defesa Física, Defesa Mágica, Poder Mágico e Crítico).
    - Ficha de Atributos D20 Primários (INT, SAB, PRE, CON, DES, FOR) discriminando valores base, bônus de equipamentos e modificadores.
    """

    def __init__(self, state):
        self.state = state

    def desenhar(self, tela, halia):
        if not halia:
            return

        s = self.state
        memorias = getattr(halia, 'fragmentos_memoria', 0)
        attrs_totais = halia.obter_atributos_totais()
        attrs_base = halia.atributos

        # Cabeçalho Superior: Estágio da Memória
        txt_cab = s.fonte_destaque.render(f"Halia — Estágio da Memória: {memorias}", True, MARFIM_OFFWHITE)
        tela.blit(txt_cab, (s.x_menu + 45, s.y_menu + 75))

        # BLOCO 1 (Esquerda): RECURSOS E ESTATÍSTICAS
        r_bloco1 = pygame.Rect(s.x_menu + 45, s.y_menu + 110, 505, 450)
        desenhar_painel_padrao(tela, r_bloco1, cor_fundo=(20, 20, 25), cor_borda=CINZA_LINHO, border_radius=4)
        tela.blit(s.fonte_sub.render("Recursos & Capacidade de Combate", True, MARFIM_OFFWHITE), (r_bloco1.x + 20, r_bloco1.y + 16))
        pygame.draw.line(tela, CINZA_ARDOSIA, (r_bloco1.x + 20, r_bloco1.y + 46), (r_bloco1.right - 20, r_bloco1.y + 46), 1)

        # 1. Barras de Vida e Mana
        tela.blit(s.fonte_texto.render(f"Pontos de Vida (HP): {halia.vida_atual} / {halia.vida_maxima}", True, MARFIM_OFFWHITE), (r_bloco1.x + 20, r_bloco1.y + 58))
        desenhar_barra_status_interpolada(tela, r_bloco1.x + 20, r_bloco1.y + 84, halia.vida_atual, halia.vida_maxima, BARRA_VIDA_JOGADOR, largura=465, altura=14)

        tela.blit(s.fonte_texto.render(f"Reserva de Mana (MP): {halia.mana_atual} / {halia.mana_maxima}", True, MARFIM_OFFWHITE), (r_bloco1.x + 20, r_bloco1.y + 112))
        desenhar_barra_status_interpolada(tela, r_bloco1.x + 20, r_bloco1.y + 138, halia.mana_atual, halia.mana_maxima, BARRA_MANA, largura=465, altura=14)

        # 2. Carteira Decomposta
        pygame.draw.line(tela, CINZA_ARDOSIA, (r_bloco1.x + 20, r_bloco1.y + 170), (r_bloco1.right - 20, r_bloco1.y + 170), 1)
        tela.blit(s.fonte_mini.render("CARTEIRA (20 Cobre = 1 Prata | 10 Prata = 1 Ouro)", True, (210, 195, 140)), (r_bloco1.x + 20, r_bloco1.y + 180))

        str_moedas = f"🪙 {halia.moedas_ouro} Ouro   |   🥈 {halia.moedas_prata} Prata   |   🥉 {halia.moedas_cobre} Cobre"
        tela.blit(s.fonte_destaque.render(str_moedas, True, MARFIM_OFFWHITE), (r_bloco1.x + 20, r_bloco1.y + 206))

        # 3. Parâmetros de Combate
        pygame.draw.line(tela, CINZA_ARDOSIA, (r_bloco1.x + 20, r_bloco1.y + 242), (r_bloco1.right - 20, r_bloco1.y + 242), 1)
        tela.blit(s.fonte_mini.render("PARÂMETROS DE COMBATE", True, (210, 195, 140)), (r_bloco1.x + 20, r_bloco1.y + 252))

        inv = getattr(halia, 'inventario', None)
        bonus_stats = inv.obter_bonus_totais_equipamentos()["stats"] if inv else {}

        def_fisica = attrs_totais.calcular_defesa_fisica() + bonus_stats.get("defesa_fisica", 0)
        def_magica = attrs_totais.calcular_defesa_magica() + bonus_stats.get("defesa_magica", 0)
        esquiva = int(min(45.0, max(5.0, 10.0 + (attrs_totais.mod_des * 2.5) + bonus_stats.get("esquiva", 0))))
        critico = int(attrs_totais.calcular_chance_critico() + bonus_stats.get("critico", 0))
        poder_magico = max(0, attrs_totais.mod_int * 2) + bonus_stats.get("dano_magico", 0)

        stats_combate = [
            ("✦ Chance de Esquiva:", f"{esquiva}%"),
            ("✦ Bloqueio & Defesa Física:", f"{def_fisica} pts"),
            ("✦ Defesa Mágica:", f"{def_magica} pts"),
            ("✦ Poder Mágico Arcano:", f"+{poder_magico} pts"),
            ("✦ Acerto Crítico:", f"{critico}%")
        ]

        y_sc = r_bloco1.y + 280
        for rotulo_sc, valor_sc in stats_combate:
            tela.blit(s.fonte_texto.render(rotulo_sc, True, CINZA_LINHO), (r_bloco1.x + 24, y_sc))
            tela.blit(s.fonte_destaque.render(valor_sc, True, MARFIM_OFFWHITE), (r_bloco1.right - 100, y_sc - 2))
            y_sc += 30

        # BLOCO 2 (Direita): OS 6 ATRIBUTOS
        r_bloco2 = pygame.Rect(s.x_menu + 570, s.y_menu + 110, 505, 450)
        desenhar_painel_padrao(tela, r_bloco2, cor_fundo=(20, 20, 25), cor_borda=CINZA_LINHO, border_radius=4)
        tela.blit(s.fonte_sub.render("Atributos Primários (D20 Core)", True, MARFIM_OFFWHITE), (r_bloco2.x + 20, r_bloco2.y + 16))
        pygame.draw.line(tela, CINZA_ARDOSIA, (r_bloco2.x + 20, r_bloco2.y + 46), (r_bloco2.right - 20, r_bloco2.y + 46), 1)

        lista_attrs = [
            ("INT", "Intelecto", attrs_base.intelecto, attrs_totais.intelecto),
            ("SAB", "Sabedoria", attrs_base.sabedoria, attrs_totais.sabedoria),
            ("PRE", "Presença", attrs_base.presenca, attrs_totais.presenca),
            ("CON", "Constituição", attrs_base.constituicao, attrs_totais.constituicao),
            ("DES", "Destreza", attrs_base.destreza, attrs_totais.destreza),
            ("FOR", "Força", attrs_base.forca, attrs_totais.forca)
        ]

        y_attr_card = r_bloco2.y + 60
        for sigla, nome_a, v_base, v_total in lista_attrs:
            r_card_a = pygame.Rect(r_bloco2.x + 20, y_attr_card, 465, 54)
            pygame.draw.rect(tela, (26, 26, 32), r_card_a, border_radius=3)
            pygame.draw.rect(tela, CINZA_ARDOSIA, r_card_a, 1, border_radius=3)

            txt_sig = s.fonte_destaque.render(sigla, True, (230, 215, 140))
            tela.blit(txt_sig, (r_card_a.x + 14, r_card_a.y + 16))

            txt_nm = s.fonte_texto.render(nome_a, True, MARFIM_OFFWHITE)
            tela.blit(txt_nm, (r_card_a.x + 65, r_card_a.y + 18))

            bonus = v_total - v_base
            str_b = f"(Base {v_base} + Eq {bonus})" if bonus > 0 else f"(Base {v_base})"
            tela.blit(s.fonte_mini.render(str_b, True, (140, 140, 155)), (r_card_a.x + 190, r_card_a.y + 20))

            mod = (v_total - 10) // 2
            mod_str = f"+{mod}" if mod >= 0 else f"{mod}"
            cor_mod = (140, 230, 170) if mod >= 0 else (240, 130, 130)

            txt_tot = s.fonte_destaque.render(f"{v_total}", True, MARFIM_OFFWHITE)
            tela.blit(txt_tot, (r_card_a.right - 120, r_card_a.y + 16))

            txt_mod = s.fonte_destaque.render(f"[{mod_str}]", True, cor_mod)
            tela.blit(txt_mod, (r_card_a.right - 65, r_card_a.y + 16))

            y_attr_card += 62
