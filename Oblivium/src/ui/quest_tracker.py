# src/ui/quest_tracker.py
import pygame
from src.utils.colors import (
    CARVAO_PROFUNDO, CINZA_LINHO, CINZA_ARDOSIA,
    MARFIM_OFFWHITE, AZUL_HOVER_MENU, AZUL_HOVER_BG
)
from src.utils.resource_manager import ResourceManager
from src.ui.ui_utils import quebrar_texto_em_linhas
from src.ui.icon_registry import (
    desenhar_icone_minimizar_expandir,
    desenhar_icone_objetivo,
    desenhar_icone_missao_badge,
    desenhar_icone_notificacao
)


class QuestTracker:
    """
    Rastreador de Missões (Quest Tracker) no canto superior direito da tela.

    Características:
    - Dimensões ampliadas (350px de largura) e tipografia maior para leitura clara e confortável.
    - Exibe simultaneamente até 1 Missão Principal e 1 Missão Secundária ativas juntas na tela.
    - Minimiza e expande exclusivamente pela tecla configurada em 'Missões' (padrão [O])
      ou clicando no botão [-]/[+] no cabeçalho do painel.
    - Ícones procedurais gerados em código (pergaminho, insígnias de categoria, checkmarks e botão -/+).
    - Transparência dinâmica (fade por proximidade) quando Halia caminha sob o painel.
    """

    def __init__(self, largura_tela=1280, altura_tela=720):
        self.largura_tela = largura_tela
        self.altura_tela = altura_tela

        # Estado de expansão (True: mostra Principal + Secundária e objetivos; False: recolhido no cabeçalho)
        self.expandido = True
        self.alpha_atual = 255.0

        # Tipografia Ampliada para Alta Legibilidade
        self.fonte_cabecalho = ResourceManager.carregar_fonte("sunday", 18)
        self.fonte_categoria = ResourceManager.carregar_fonte("contrail", 13)
        self.fonte_titulo = ResourceManager.carregar_fonte("sunday", 20)
        self.fonte_obj = ResourceManager.carregar_fonte("contrail", 16)
        self.fonte_contador = ResourceManager.carregar_fonte("contrail", 14)
        self.fonte_atalho = ResourceManager.carregar_fonte("contrail", 13)

        # Dimensões e posicionamento no Canto Superior Direito
        self.largura_box = 350
        self.margem_direita = 22
        self.margem_topo = 20
        self.x_box = self.largura_tela - self.largura_box - self.margem_direita
        self.y_box = self.margem_topo

        # Hitboxes interativas
        self.rect_painel = pygame.Rect(self.x_box, self.y_box, self.largura_box, 44)
        self.rect_botao_toggle = pygame.Rect(0, 0, 0, 0)
        self.hover_toggle = False

    def toggle_expandir(self):
        """Alterna entre o modo expandido e o modo minimizado."""
        self.expandido = not self.expandido

    def handle_event(self, evento, game=None):
        """
        Processa clique no botão [-]/[+] ou tecla configurada em 'Missões' (padrão [O])
        estritamente para minimizar e expandir o rastreador quando houver missão ativa.
        """
        missoes_ativas = []
        if game and hasattr(game, 'missoes') and game.missoes:
            missoes_ativas = game.missoes.obter_missoes_rastreadas()

        if evento.type == pygame.MOUSEMOTION:
            if missoes_ativas:
                self.hover_toggle = self.rect_botao_toggle.collidepoint(evento.pos)
            else:
                self.hover_toggle = False

        elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            if missoes_ativas and self.rect_botao_toggle.collidepoint(evento.pos):
                self.toggle_expandir()
                if game and hasattr(game, 'audio') and game.audio:
                    game.audio.tocar_sfx("ui_cursor")
                return True

        elif evento.type == pygame.KEYDOWN:
            tecla_missoes = pygame.K_o
            if game and hasattr(game, 'controles'):
                tecla_missoes = game.controles.get("Missões", pygame.K_o)

            if evento.key == tecla_missoes and missoes_ativas:
                self.toggle_expandir()
                if game and hasattr(game, 'audio') and game.audio:
                    game.audio.tocar_sfx("ui_cursor")
                return True

        return False

    def _calcular_layout_missao(self, missao, largura_texto_obj):
        """Pré-calcula as linhas quebradas de cada objetivo e a altura vertical do bloco da missão."""
        objetivos = missao.get("objetivos", [])
        linhas_por_obj = []
        altura_objs = 0
        for obj in objetivos:
            desc = obj.get("descricao", "")
            linhas = quebrar_texto_em_linhas(desc, self.fonte_obj, largura_texto_obj)
            if not linhas:
                linhas = [desc]
            linhas_por_obj.append((obj, linhas))
            altura_objs += (len(linhas) * 20) + 8

        # 22px (categoria) + 28px (título) + altura_objs + 10px (padding inferior)
        altura_bloco = 54 + altura_objs + 8
        return linhas_por_obj, altura_bloco

    def desenhar(self, tela, game):
        """Renderiza o painel de missões ativas (Principal e Secundária juntas) no canto superior direito."""
        if not hasattr(game, 'missoes') or not game.missoes:
            return

        # 1. Oculta durante transições de tela, flashbacks ou tela de despertar
        if hasattr(game, 'transicao') and game.transicao.estado != "INATIVO":
            return
        if hasattr(game, 'flashback_sistema') and game.flashback_sistema.estado != "INATIVO":
            return
        if hasattr(game, 'tela_despertar') and game.tela_despertar.estado != "INATIVO":
            return

        missoes_ativas = game.missoes.obter_missoes_rastreadas()
        if not missoes_ativas:
            return

        # 2. Layout Dinâmico
        altura_cabecalho = 44
        largura_texto_obj = self.largura_box - 102

        layouts_missoes = []
        altura_conteudo = 0

        if self.expandido:
            for idx, m in enumerate(missoes_ativas):
                linhas_obj, h_bloco = self._calcular_layout_missao(m, largura_texto_obj)
                layouts_missoes.append((m, linhas_obj, h_bloco))
                altura_conteudo += h_bloco
                if idx < len(missoes_ativas) - 1:
                    altura_conteudo += 14  # Espaço para a divisória entre Principal e Secundária
            altura_total = altura_cabecalho + altura_conteudo + 12
        else:
            altura_total = altura_cabecalho

        self.x_box = self.largura_tela - self.largura_box - self.margem_direita
        self.y_box = self.margem_topo
        self.rect_painel = pygame.Rect(self.x_box, self.y_box, self.largura_box, altura_total)

        # Botão [-]/[+] no canto superior direito do painel
        tam_btn = 26
        btn_x = self.x_box + self.largura_box - tam_btn - 10
        btn_y = self.y_box + (altura_cabecalho - tam_btn) // 2
        self.rect_botao_toggle = pygame.Rect(btn_x, btn_y, tam_btn, tam_btn)

        pos_mouse = pygame.mouse.get_pos()
        self.hover_toggle = self.rect_botao_toggle.collidepoint(pos_mouse)

        # 3. Fade por proximidade quando Halia passa por baixo do painel
        halia = getattr(game, 'halia', None)
        perto_painel = False
        if halia:
            rect_halia = pygame.Rect(
                int(getattr(halia, 'x', 0)),
                int(getattr(halia, 'y', 0)),
                getattr(halia, 'largura', 40),
                getattr(halia, 'altura', 40)
            )
            zona_fade = self.rect_painel.inflate(36, 36)
            perto_painel = rect_halia.colliderect(zona_fade)

        alvo_alpha = 65.0 if perto_painel else 255.0
        if self.alpha_atual < alvo_alpha:
            self.alpha_atual = min(alvo_alpha, self.alpha_atual + 20.0)
        elif self.alpha_atual > alvo_alpha:
            self.alpha_atual = max(alvo_alpha, self.alpha_atual - 20.0)

        fator_alpha = self.alpha_atual / 255.0

        # 4. Superfície dedicada com canal Alpha
        surf_box = pygame.Surface((self.largura_box, altura_total), pygame.SRCALPHA)

        # Fundo mais escuro e contrastado para leitura nítida
        alpha_fundo = int(238 * fator_alpha)
        alpha_borda = int(250 * fator_alpha)
        pygame.draw.rect(surf_box, (12, 13, 18, alpha_fundo), (0, 0, self.largura_box, altura_total), border_radius=5)
        pygame.draw.rect(surf_box, (*CINZA_LINHO[:3], alpha_borda), (0, 0, self.largura_box, altura_total), 1, border_radius=5)

        # Moldura interna sutil
        if altura_total > 12:
            pygame.draw.rect(surf_box, (28, 30, 40, int(190 * fator_alpha)), (3, 3, self.largura_box - 6, altura_total - 6), 1, border_radius=4)

        # 5. Cabeçalho Superior do Diário de Missões
        pygame.draw.rect(surf_box, (18, 20, 28, int(230 * fator_alpha)), (4, 4, self.largura_box - 8, altura_cabecalho - 6), border_radius=3)

        # Ícone procedural de Pergaminho no cabeçalho
        desenhar_icone_notificacao(surf_box, 22, altura_cabecalho // 2, tipo="MISSAO", cor=(235, 205, 115))

        # Título do Cabeçalho
        qtd_ativas = len(missoes_ativas)
        titulo_hdr = "MISSÕES ATIVAS" if self.expandido else f"MISSÕES ATIVAS ({qtd_ativas})"
        rend_hdr = self.fonte_cabecalho.render(titulo_hdr, True, MARFIM_OFFWHITE)
        rend_hdr.set_alpha(int(255 * fator_alpha))
        surf_box.blit(rend_hdr, (38, (altura_cabecalho - rend_hdr.get_height()) // 2))

        # Badge da Tecla [O] ao lado do botão [-]/[+]
        tecla_missoes_cod = game.controles.get("Missões", pygame.K_o) if hasattr(game, 'controles') else pygame.K_o
        nome_tecla = pygame.key.name(tecla_missoes_cod).upper()
        rend_tecla = self.fonte_atalho.render(f"[{nome_tecla}]", True, (185, 195, 210))
        rend_tecla.set_alpha(int(240 * fator_alpha))
        rect_btn_local = pygame.Rect(self.largura_box - tam_btn - 10, (altura_cabecalho - tam_btn) // 2, tam_btn, tam_btn)
        surf_box.blit(rend_tecla, (rect_btn_local.left - rend_tecla.get_width() - 8, rect_btn_local.centery - rend_tecla.get_height() // 2))

        # Botão [-]/[+] Procedural
        cor_bg_btn = (*AZUL_HOVER_BG[:3], int(235 * fator_alpha)) if self.hover_toggle else (26, 28, 36, int(225 * fator_alpha))
        cor_borda_btn = (*AZUL_HOVER_MENU[:3], int(255 * fator_alpha)) if self.hover_toggle else (*CINZA_ARDOSIA[:3], int(235 * fator_alpha))
        pygame.draw.rect(surf_box, cor_bg_btn, rect_btn_local, border_radius=3)
        pygame.draw.rect(surf_box, cor_borda_btn, rect_btn_local, 1, border_radius=3)

        cor_ico_btn = AZUL_HOVER_MENU if self.hover_toggle else MARFIM_OFFWHITE
        desenhar_icone_minimizar_expandir(surf_box, rect_btn_local, expandido=self.expandido, cor=cor_ico_btn, espessura=2)

        # 6. Corpo Expandido: Exibe Missão Principal e Missão Secundária juntas
        if self.expandido:
            pygame.draw.line(
                surf_box,
                (*CINZA_ARDOSIA[:3], int(220 * fator_alpha)),
                (10, altura_cabecalho),
                (self.largura_box - 10, altura_cabecalho),
                1
            )

            y_cursor = altura_cabecalho + 8

            for idx_m, (missao, linhas_por_obj, h_bloco) in enumerate(layouts_missoes):
                eh_principal = (missao.get("categoria", "PRINCIPAL").upper() == "PRINCIPAL")
                cor_cat = (240, 205, 110) if eh_principal else (130, 200, 250)
                txt_cat = "MISSÃO PRINCIPAL" if eh_principal else "MISSÃO SECUNDÁRIA"

                # Sub-card de fundo sutil para destacar cada missão
                rect_subcard = pygame.Rect(8, y_cursor, self.largura_box - 16, h_bloco - 4)
                pygame.draw.rect(surf_box, (18, 20, 27, int(200 * fator_alpha)), rect_subcard, border_radius=4)
                pygame.draw.rect(surf_box, (36, 40, 52, int(190 * fator_alpha)), rect_subcard, 1, border_radius=4)

                # Barra lateral vertical de destaque da categoria (Ouro para Principal, Celeste para Secundária)
                pygame.draw.rect(
                    surf_box,
                    (*cor_cat, int(245 * fator_alpha)),
                    (rect_subcard.x, rect_subcard.y + 4, 4, rect_subcard.height - 8),
                    border_radius=2
                )

                # Emblema procedural + Rótulo da Categoria
                desenhar_icone_missao_badge(surf_box, rect_subcard.x + 16, y_cursor + 14, categoria=missao.get("categoria", "PRINCIPAL"), cor=cor_cat)
                rend_cat = self.fonte_categoria.render(txt_cat, True, cor_cat)
                rend_cat.set_alpha(int(250 * fator_alpha))
                surf_box.blit(rend_cat, (rect_subcard.x + 28, y_cursor + 6))

                # Título da Missão (Fonte 20pt Sunday)
                titulo_str = missao.get("titulo", "Missão")
                if len(titulo_str) > 30:
                    titulo_str = titulo_str[:28] + "..."
                rend_tit = self.fonte_titulo.render(titulo_str, True, MARFIM_OFFWHITE)
                rend_tit.set_alpha(int(255 * fator_alpha))
                surf_box.blit(rend_tit, (rect_subcard.x + 12, y_cursor + 24))

                # Lista de Objetivos da Missão
                y_obj = y_cursor + 52
                for obj, linhas in linhas_por_obj:
                    concluido = obj.get("concluido", False)
                    atual = obj.get("atual", 0)
                    alvo = obj.get("alvo", 1)

                    cor_texto_obj = (135, 225, 155) if concluido else (228, 225, 218)

                    # Ícone procedural de check / losango pendente
                    desenhar_icone_objetivo(
                        surf_box,
                        rect_subcard.x + 18,
                        y_obj + 9,
                        concluido=concluido,
                        cor_ativo=(135, 225, 155),
                        cor_pendente=cor_cat
                    )

                    # Pill de progresso [atual/alvo] à direita
                    str_progresso = f"{atual}/{alvo}"
                    rend_prog = self.fonte_contador.render(str_progresso, True, (135, 225, 155) if concluido else cor_cat)
                    rend_prog.set_alpha(int(255 * fator_alpha))
                    w_pill = rend_prog.get_width() + 12
                    h_pill = 20
                    rect_pill = pygame.Rect(rect_subcard.right - w_pill - 8, y_obj, w_pill, h_pill)
                    cor_borda_pill = (100, 180, 120, int(210 * fator_alpha)) if concluido else (55, 62, 78, int(210 * fator_alpha))
                    pygame.draw.rect(surf_box, (12, 14, 20, int(220 * fator_alpha)), rect_pill, border_radius=3)
                    pygame.draw.rect(surf_box, cor_borda_pill, rect_pill, 1, border_radius=3)
                    surf_box.blit(rend_prog, (rect_pill.centerx - rend_prog.get_width() // 2, rect_pill.centery - rend_prog.get_height() // 2))

                    # Linhas de descrição do objetivo
                    for linha in linhas:
                        rend_l = self.fonte_obj.render(linha, True, cor_texto_obj)
                        rend_l.set_alpha(int(255 * fator_alpha))
                        surf_box.blit(rend_l, (rect_subcard.x + 30, y_obj))
                        y_obj += 20

                    y_obj += 8

                y_cursor += h_bloco

                # Divisória ornamental entre a Missão Principal e a Missão Secundária
                if idx_m < len(layouts_missoes) - 1:
                    y_div = y_cursor + 5
                    cx_div = self.largura_box // 2
                    pygame.draw.line(surf_box, (*CINZA_ARDOSIA[:3], int(180 * fator_alpha)), (24, y_div), (cx_div - 8, y_div), 1)
                    pygame.draw.line(surf_box, (*CINZA_ARDOSIA[:3], int(180 * fator_alpha)), (cx_div + 8, y_div), (self.largura_box - 24, y_div), 1)
                    pts_orn = [(cx_div, y_div - 3), (cx_div + 3, y_div), (cx_div, y_div + 3), (cx_div - 3, y_div)]
                    pygame.draw.polygon(surf_box, (*CINZA_LINHO[:3], int(210 * fator_alpha)), pts_orn)
                    y_cursor += 14

        tela.blit(surf_box, (self.x_box, self.y_box))
