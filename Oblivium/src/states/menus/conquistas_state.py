# src/states/conquistas_state.py
import pygame
from src.states.states import State
from src.utils.colors import (
    PRETO, CARVAO_PROFUNDO, CINZA_ARDOSIA, CINZA_LINHO,
    MARFIM_OFFWHITE, UI_TEXTO_APAGADO,
    AZUL_HOVER_MENU, AZUL_HOVER_BG
)
from src.utils.resource_manager import ResourceManager
from src.ui.ui_utils import desenhar_painel_padrao
from src.ui.icon_registry import (
    desenhar_icone_conquista,
    desenhar_icone_fechar,
    desenhar_icone_missao_badge
)


class ConquistasState(State):
    """
    Tela de Conquistas e Marcos de Oblivium (Estilo Steam / Platina).
    
    Características:
    - Moldura em Carvão Profundo com contornos delicados em Cinza Linho / Marfim.
    - Barra de Platina no topo com percentual geral de conclusão.
    - Filtros por categoria: Todas, Desbloqueadas e Bloqueadas.
    - Emblemas procedurais exclusivos gerados em código para cada conquista.
    - Lista de cards com scroll contínuo e suporte a teclado e roda do mouse.
    """

    def __init__(self, game):
        super().__init__(game)

        # Tipografia Editorial Dark Fantasy
        self.fonte_titulo = ResourceManager.carregar_fonte("sunday", 34)
        self.fonte_subtitulo = ResourceManager.carregar_fonte("just_breathe", 18)
        self.fonte_card_titulo = ResourceManager.carregar_fonte("sunday", 18)
        self.fonte_card_desc = ResourceManager.carregar_fonte("contrail", 14)
        self.fonte_card_data = ResourceManager.carregar_fonte("contrail", 12)
        self.fonte_status = ResourceManager.carregar_fonte("contrail", 14)
        self.fonte_filtro = ResourceManager.carregar_fonte("contrail", 16)
        self.fonte_rodape = ResourceManager.carregar_fonte("contrail", 15)

        # Filtros
        self.filtros = ["Todas", "Desbloqueadas", "Bloqueadas"]
        self.filtro_ativo_idx = 0
        self.rects_filtros = []

        # Scroll
        self.scroll_y = 0.0
        self.max_scroll = 0.0

        # Dimensões do Painel
        self.largura_bloco = 880
        self.altura_bloco = 590

        # Retângulos de Botões
        self.rect_botao_voltar = pygame.Rect(0, 0, 0, 0)
        self.rect_fechar = pygame.Rect(0, 0, 0, 0)

        # Overlay escurecido para quando acessado de telas de gameplay/pause
        self.overlay = pygame.Surface((self.game.LARGURA, self.game.ALTURA))
        self.overlay.fill((10, 10, 14))
        self.overlay.set_alpha(210)

    def _tocar_sfx(self, alias):
        if hasattr(self.game, 'audio') and self.game.audio:
            self.game.audio.tocar_sfx(alias)

    def _obter_conquistas_filtradas(self):
        """Retorna a lista de conquistas correspondente ao filtro ativo."""
        if not hasattr(self.game, 'conquistas') or not self.game.conquistas:
            return []

        todas = self.game.conquistas.obter_todas()
        nome_filtro = self.filtros[self.filtro_ativo_idx]

        if nome_filtro == "Desbloqueadas":
            return [c for c in todas if c.get("desbloqueada", False)]
        elif nome_filtro == "Bloqueadas":
            return [c for c in todas if not c.get("desbloqueada", False)]
        return todas

    def voltar_origem(self):
        self._tocar_sfx("ui_voltar")
        origem = getattr(self.game, 'origem_conquistas', 'MENU')
        self.game.mudar_estado(origem)

    def handle_events(self, eventos, teclas):
        for evento in eventos:
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    self.voltar_origem()
                    return

                elif evento.key in [pygame.K_LEFT, pygame.K_a]:
                    self.filtro_ativo_idx = (self.filtro_ativo_idx - 1) % len(self.filtros)
                    self.scroll_y = 0.0
                    self._tocar_sfx("ui_cursor")

                elif evento.key in [pygame.K_RIGHT, pygame.K_d, pygame.K_TAB]:
                    self.filtro_ativo_idx = (self.filtro_ativo_idx + 1) % len(self.filtros)
                    self.scroll_y = 0.0
                    self._tocar_sfx("ui_cursor")

                elif evento.key in [pygame.K_UP, pygame.K_w]:
                    self.scroll_y = max(0.0, self.scroll_y - 45)
                    self._tocar_sfx("ui_cursor")

                elif evento.key in [pygame.K_DOWN, pygame.K_s]:
                    self.scroll_y = min(self.max_scroll, self.scroll_y + 45)
                    self._tocar_sfx("ui_cursor")

                elif evento.key == pygame.K_PAGEUP:
                    self.scroll_y = max(0.0, self.scroll_y - 180)

                elif evento.key == pygame.K_PAGEDOWN:
                    self.scroll_y = min(self.max_scroll, self.scroll_y + 180)

                elif evento.key == pygame.K_HOME:
                    self.scroll_y = 0.0

                elif evento.key == pygame.K_END:
                    self.scroll_y = self.max_scroll

            elif evento.type == pygame.MOUSEWHEEL:
                self.scroll_y = max(0.0, min(self.max_scroll, self.scroll_y - (evento.y * 36)))

            elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                # 1. Clique nos filtros
                for i, r in enumerate(self.rects_filtros):
                    if r.collidepoint(evento.pos):
                        if self.filtro_ativo_idx != i:
                            self.filtro_ativo_idx = i
                            self.scroll_y = 0.0
                            self._tocar_sfx("ui_cursor")
                        return

                # 2. Clique no botão Voltar ou no botão [X] superior
                if self.rect_botao_voltar.collidepoint(evento.pos) or self.rect_fechar.collidepoint(evento.pos):
                    self.voltar_origem()
                    return

    def update(self):
        if getattr(self.game, 'origem_conquistas', 'MENU') == "MENU":
            if hasattr(self.game, 'menu') and hasattr(self.game.menu, 'efeito_petalas'):
                dt = self.game.clock.get_time() / 1000.0 if hasattr(self.game, 'clock') else 0.016
                dt = min(dt, 0.05) if dt > 0 else 0.016
                self.game.menu.efeito_petalas.atualizar(dt)

    def draw(self, tela):
        # 1. Fundo contextual
        if getattr(self.game, 'origem_conquistas', 'MENU') == "PAUSE":
            origem_p = getattr(self.game, 'origem_pause', 'JOGANDO')
            if origem_p == "COMBATE" and "COMBATE" in self.game.estados:
                self.game.estados["COMBATE"].draw(tela)
            elif "JOGANDO" in self.game.estados:
                self.game.estados["JOGANDO"].draw(tela)
            tela.blit(self.overlay, (0, 0))
        else:
            tela.fill(PRETO)
            if hasattr(self.game, 'menu') and hasattr(self.game.menu, 'efeito_petalas'):
                self.game.menu.efeito_petalas.desenhar(tela)

        pos_mouse = pygame.mouse.get_pos()

        # 2. Painel Central
        x = (self.game.LARGURA - self.largura_bloco) // 2
        y = (self.game.ALTURA - self.altura_bloco) // 2

        rect_painel = pygame.Rect(x, y, self.largura_bloco, self.altura_bloco)
        desenhar_painel_padrao(tela, rect_painel, cor_fundo=CARVAO_PROFUNDO, cor_borda=CINZA_LINHO, alpha=248)

        # Moldura interna decorativa
        rect_interno = rect_painel.inflate(-10, -10)
        pygame.draw.rect(tela, (28, 28, 34), rect_interno, 1, border_radius=2)

        # 3. Cabeçalho (Título e Subtítulo)
        txt_titulo = self.fonte_titulo.render("Conquistas", True, MARFIM_OFFWHITE)
        tela.blit(txt_titulo, (x + 36, y + 20))

        txt_sub = self.fonte_subtitulo.render("Marcos especiais, triunfos arcanos e memórias restauradas", True, CINZA_LINHO)
        tela.blit(txt_sub, (x + 38, y + 56))

        # Botão Fechar [X] no canto superior direito
        self.rect_fechar = pygame.Rect(x + self.largura_bloco - 60, y + 22, 26, 26)
        hover_fechar = self.rect_fechar.collidepoint(pos_mouse)
        pygame.draw.rect(tela, (45, 22, 26) if hover_fechar else (22, 24, 30), self.rect_fechar, border_radius=3)
        pygame.draw.rect(tela, (230, 95, 95) if hover_fechar else CINZA_ARDOSIA, self.rect_fechar, 1, border_radius=3)
        desenhar_icone_fechar(tela, self.rect_fechar, cor=(255, 160, 160) if hover_fechar else CINZA_LINHO, espessura=2)

        # 4. Progresso da Platina (Ao lado do botão fechar)
        desbloqueadas, total, porcentagem = (0, 0, 0)
        if hasattr(self.game, 'conquistas') and self.game.conquistas:
            desbloqueadas, total, porcentagem = self.game.conquistas.obter_progresso()

        gauge_w = 180
        gauge_h = 10
        gauge_x = self.rect_fechar.left - 18 - gauge_w
        gauge_y = y + 44

        # Rótulo de Platina com emblema procedural
        texto_platina = f"Platina: {desbloqueadas}/{total} ({porcentagem}%)"
        cor_platina = (255, 225, 115) if porcentagem == 100 else MARFIM_OFFWHITE
        txt_plat_render = self.fonte_status.render(texto_platina, True, cor_platina)
        tx_plat = gauge_x + gauge_w - txt_plat_render.get_width()
        tela.blit(txt_plat_render, (tx_plat, y + 22))
        desenhar_icone_missao_badge(tela, tx_plat - 12, y + 30, categoria="PRINCIPAL", cor=(255, 220, 110) if porcentagem == 100 else (160, 205, 245))

        # Barra Medidora da Platina
        rect_gauge_bg = pygame.Rect(gauge_x, gauge_y, gauge_w, gauge_h)
        pygame.draw.rect(tela, (20, 22, 28), rect_gauge_bg, border_radius=2)
        pygame.draw.rect(tela, (45, 52, 65), rect_gauge_bg, 1, border_radius=2)

        if porcentagem > 0:
            largura_preenchida = int((gauge_w - 2) * (porcentagem / 100.0))
            cor_barra_plat = (245, 210, 100) if porcentagem == 100 else (140, 190, 235)
            rect_preenchido = pygame.Rect(gauge_x + 1, gauge_y + 1, max(2, largura_preenchida), gauge_h - 2)
            pygame.draw.rect(tela, cor_barra_plat, rect_preenchido, border_radius=1)

        # Linha Divisória Superior
        pygame.draw.line(tela, CINZA_ARDOSIA, (x + 30, y + 82), (x + self.largura_bloco - 30, y + 82), 1)

        # 5. Filtros Interativos
        pos_x_filtro = x + 36
        pos_y_filtro = y + 92
        self.rects_filtros.clear()

        todas_c = self.game.conquistas.obter_todas() if hasattr(self.game, 'conquistas') and self.game.conquistas else []
        desbloq_count = sum(1 for c in todas_c if c.get("desbloqueada", False))
        bloq_count = len(todas_c) - desbloq_count

        rotulos_filtros = [
            f"Todas ({len(todas_c)})",
            f"Desbloqueadas ({desbloq_count})",
            f"Bloqueadas ({bloq_count})"
        ]

        for idx_f, rotulo in enumerate(rotulos_filtros):
            esta_ativo = (idx_f == self.filtro_ativo_idx)
            largura_btn = self.fonte_filtro.size(rotulo)[0] + 28
            rect_f = pygame.Rect(pos_x_filtro, pos_y_filtro, largura_btn, 28)
            self.rects_filtros.append(rect_f)

            hover_f = rect_f.collidepoint(pos_mouse)

            if esta_ativo:
                pygame.draw.rect(tela, AZUL_HOVER_BG, rect_f, border_radius=3)
                pygame.draw.rect(tela, AZUL_HOVER_MENU, rect_f, 1, border_radius=3)
                cor_f_txt = (220, 240, 255)
            elif hover_f:
                pygame.draw.rect(tela, (25, 28, 36), rect_f, border_radius=3)
                pygame.draw.rect(tela, CINZA_LINHO, rect_f, 1, border_radius=3)
                cor_f_txt = MARFIM_OFFWHITE
            else:
                pygame.draw.rect(tela, (20, 20, 24), rect_f, border_radius=3)
                pygame.draw.rect(tela, (40, 42, 50), rect_f, 1, border_radius=3)
                cor_f_txt = CINZA_LINHO

            rend_f = self.fonte_filtro.render(rotulo, True, cor_f_txt)
            tela.blit(rend_f, (rect_f.centerx - rend_f.get_width() // 2, rect_f.centery - rend_f.get_height() // 2))

            pos_x_filtro += largura_btn + 12

        # 6. Lista de Conquistas com Scroll
        conquistas_filtradas = self._obter_conquistas_filtradas()

        x_lista = x + 35
        y_lista = y + 132
        w_lista = self.largura_bloco - 70
        h_lista = 405

        h_card = 68
        gap = 8
        altura_total = len(conquistas_filtradas) * (h_card + gap)
        self.max_scroll = max(0.0, float(altura_total - h_lista))
        self.scroll_y = max(0.0, min(self.max_scroll, self.scroll_y))

        clip_antigo = tela.get_clip()
        tela.set_clip(pygame.Rect(x_lista, y_lista, w_lista, h_lista))

        w_card = w_lista - 16
        for i, c in enumerate(conquistas_filtradas):
            y_card = y_lista + (i * (h_card + gap)) - int(self.scroll_y)

            if y_card + h_card < y_lista or y_card > y_lista + h_lista:
                continue

            rect_card = pygame.Rect(x_lista, y_card, w_card, h_card)
            desbloqueada = c.get("desbloqueada", False)
            secreta = c.get("secreta", False)
            cor_tema = tuple(c.get("cor", (180, 215, 245)))

            if desbloqueada:
                eh_mestre_platina = (c.get("id") == "mestre_platinador")
                cor_fundo_card = (22, 26, 36)
                cor_borda_card = (240, 215, 115) if eh_mestre_platina else (150, 185, 220)
                cor_titulo = (255, 235, 150) if eh_mestre_platina else MARFIM_OFFWHITE
                cor_desc = (195, 200, 210)
            else:
                cor_fundo_card = (16, 17, 21)
                cor_borda_card = (38, 42, 50)
                cor_titulo = (145, 150, 162)
                cor_desc = UI_TEXTO_APAGADO

            pygame.draw.rect(tela, cor_fundo_card, rect_card, border_radius=4)
            pygame.draw.rect(tela, cor_borda_card, rect_card, 1, border_radius=4)

            # Caixa do Ícone Lateral com Arte Procedural Exclusiva
            rect_ico_box = pygame.Rect(x_lista + 8, y_card + 9, 50, 50)
            cor_bg_ico = (24, 30, 42) if desbloqueada else (12, 13, 16)
            pygame.draw.rect(tela, cor_bg_ico, rect_ico_box, border_radius=3)
            pygame.draw.rect(tela, cor_tema if desbloqueada else (45, 48, 58), rect_ico_box, 1, border_radius=3)

            desenhar_icone_conquista(
                tela,
                rect_ico_box,
                c.get("id", ""),
                cor=cor_tema,
                desbloqueada=desbloqueada,
                secreta=secreta
            )

            # Título da Conquista
            tit_texto = "??? (Conquista Secreta)" if (secreta and not desbloqueada) else c.get("titulo", "Conquista")
            tit_render = self.fonte_card_titulo.render(tit_texto, True, cor_titulo)
            tela.blit(tit_render, (x_lista + 68, y_card + 10))

            # Descrição da Conquista
            if not desbloqueada and secreta:
                texto_desc = "Conquista oculta. Superar um desafio extraordinário revelará este marco."
            else:
                texto_desc = c.get("descricao", "")

            if len(texto_desc) > 88:
                texto_desc = texto_desc[:85] + "..."

            rend_desc = self.fonte_card_desc.render(texto_desc, True, cor_desc)
            tela.blit(rend_desc, (x_lista + 68, y_card + 36))

            # Status ou Data de Desbloqueio (Canto direito do card)
            if desbloqueada and c.get("data_desbloqueio"):
                data_str = f"Desbloqueada em {c['data_desbloqueio']}"
                rend_data = self.fonte_card_data.render(data_str, True, (150, 215, 175))
                tela.blit(rend_data, (x_lista + w_card - rend_data.get_width() - 14, y_card + 12))
            elif not desbloqueada:
                status_str = "Bloqueada"
                rend_status = self.fonte_card_data.render(status_str, True, UI_TEXTO_APAGADO)
                tela.blit(rend_status, (x_lista + w_card - rend_status.get_width() - 14, y_card + 12))

        tela.set_clip(clip_antigo)

        # 7. Trilho e Slider da Scrollbar
        if self.max_scroll > 0:
            scroll_x = x_lista + w_lista - 8
            scroll_track_h = h_lista
            pygame.draw.rect(tela, (20, 22, 28), (scroll_x, y_lista, 6, scroll_track_h), border_radius=3)

            altura_thumb = max(24, int(scroll_track_h * (h_lista / altura_total)))
            razao_scroll = self.scroll_y / self.max_scroll
            y_thumb = y_lista + int((scroll_track_h - altura_thumb) * razao_scroll)
            pygame.draw.rect(tela, (140, 175, 210), (scroll_x, y_thumb, 6, altura_thumb), border_radius=3)

        # 8. Rodapé (Atalhos e Botão Voltar)
        pygame.draw.line(tela, CINZA_ARDOSIA, (x + 30, y + self.altura_bloco - 42), (x + self.largura_bloco - 30, y + self.altura_bloco - 42), 1)

        txt_atalhos = self.fonte_rodape.render("[Setas / Scroll] Rolar   |   [A / D / TAB] Filtros   |   [ESC] Retornar", True, UI_TEXTO_APAGADO)
        tela.blit(txt_atalhos, (x + 36, y + self.altura_bloco - 30))

        largura_btn_voltar = 100
        altura_btn_voltar = 28
        self.rect_botao_voltar = pygame.Rect(x + self.largura_bloco - 36 - largura_btn_voltar, y + self.altura_bloco - 36, largura_btn_voltar, altura_btn_voltar)

        hover_voltar = self.rect_botao_voltar.collidepoint(pos_mouse)
        if hover_voltar:
            pygame.draw.rect(tela, AZUL_HOVER_BG, self.rect_botao_voltar, border_radius=3)
            pygame.draw.rect(tela, AZUL_HOVER_MENU, self.rect_botao_voltar, 1, border_radius=3)
            cor_v_txt = MARFIM_OFFWHITE
        else:
            pygame.draw.rect(tela, (22, 23, 28), self.rect_botao_voltar, border_radius=3)
            pygame.draw.rect(tela, (50, 54, 66), self.rect_botao_voltar, 1, border_radius=3)
            cor_v_txt = CINZA_LINHO

        txt_voltar_rend = self.fonte_rodape.render("Voltar", True, cor_v_txt)
        tela.blit(txt_voltar_rend, (self.rect_botao_voltar.centerx - txt_voltar_rend.get_width() // 2, self.rect_botao_voltar.centery - txt_voltar_rend.get_height() // 2))
