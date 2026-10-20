import pygame
from Oblivium.src.mechanics.combat_narrator import CombatNarrator


class CombatInputHandler:
    """
    Controlador de Entradas e Navegação de Menus de Combate de Oblivium.
    - Suporta navegação por Mouse (hover, cliques e roda de rolagem/scroll).
    - Suporta navegação por Teclado (Setas/WASD, Enter/Espaço/E, PageUp/PageDown, ESC).
    - Gerencia seleção de ações, submenus (Ataques, Magias, Concentração, Itens) e alvos.
    """

    def __init__(self, combat_screen):
        self.cs = combat_screen

    # =========================================================================
    # ROLAGEM E AJUSTE DE VISUALIZAÇÃO DE SUBMENUS
    # =========================================================================

    def ajustar_scroll_submenu(self, estado):
        """Garante que o item selecionado pelo teclado esteja sempre visível na janela de rolagem."""
        max_itens = self.cs.ITENS_POR_PAGINA_SUBMENU
        if estado == "SUBMENU_ATAQUE":
            total = len(self.cs.ataques_fisicos_disponiveis)
            idx = self.cs.indice_ataque_fisico
            if total <= max_itens:
                self.cs.scroll_ataque = 0
            else:
                if idx < self.cs.scroll_ataque:
                    self.cs.scroll_ataque = idx
                elif idx >= self.cs.scroll_ataque + max_itens:
                    self.cs.scroll_ataque = idx - max_itens + 1
                self.cs.scroll_ataque = max(0, min(self.cs.scroll_ataque, total - max_itens))

        elif estado == "SUBMENU_MAGIA":
            total = len(self.cs.magias_disponiveis)
            idx = self.cs.indice_magia
            if total <= max_itens:
                self.cs.scroll_magia = 0
            else:
                if idx < self.cs.scroll_magia:
                    self.cs.scroll_magia = idx
                elif idx >= self.cs.scroll_magia + max_itens:
                    self.cs.scroll_magia = idx - max_itens + 1
                self.cs.scroll_magia = max(0, min(self.cs.scroll_magia, total - max_itens))

        elif estado == "SUBMENU_CONCENTRAR":
            total = len(self.cs.opcoes_concentrar)
            idx = self.cs.indice_concentrar
            if total <= max_itens:
                self.cs.scroll_concentrar = 0
            else:
                if idx < self.cs.scroll_concentrar:
                    self.cs.scroll_concentrar = idx
                elif idx >= self.cs.scroll_concentrar + max_itens:
                    self.cs.scroll_concentrar = idx - max_itens + 1
                self.cs.scroll_concentrar = max(0, min(self.cs.scroll_concentrar, total - max_itens))

        elif estado == "SUBMENU_ITENS":
            total = len(self.cs.itens_combate_disponiveis)
            idx = self.cs.indice_item_combate
            if total <= max_itens:
                self.cs.scroll_item_combate = 0
            else:
                if idx < self.cs.scroll_item_combate:
                    self.cs.scroll_item_combate = idx
                elif idx >= self.cs.scroll_item_combate + max_itens:
                    self.cs.scroll_item_combate = idx - max_itens + 1
                self.cs.scroll_item_combate = max(0, min(self.cs.scroll_item_combate, total - max_itens))

    def rolar_submenu(self, estado, delta):
        """Rola a visualização do submenu para cima ou para baixo pelo mouse ou botões de seta."""
        max_itens = self.cs.ITENS_POR_PAGINA_SUBMENU
        if estado == "SUBMENU_ATAQUE":
            total = len(self.cs.ataques_fisicos_disponiveis)
            max_scroll = max(0, total - max_itens)
            self.cs.scroll_ataque = max(0, min(max_scroll, self.cs.scroll_ataque + delta))
            if self.cs.indice_ataque_fisico < self.cs.scroll_ataque:
                self.cs.indice_ataque_fisico = self.cs.scroll_ataque
            elif self.cs.indice_ataque_fisico >= self.cs.scroll_ataque + max_itens:
                self.cs.indice_ataque_fisico = self.cs.scroll_ataque + max_itens - 1

        elif estado == "SUBMENU_MAGIA":
            total = len(self.cs.magias_disponiveis)
            max_scroll = max(0, total - max_itens)
            self.cs.scroll_magia = max(0, min(max_scroll, self.cs.scroll_magia + delta))
            if self.cs.indice_magia < self.cs.scroll_magia:
                self.cs.indice_magia = self.cs.scroll_magia
            elif self.cs.indice_magia >= self.cs.scroll_magia + max_itens:
                self.cs.indice_magia = self.cs.scroll_magia + max_itens - 1

        elif estado == "SUBMENU_CONCENTRAR":
            total = len(self.cs.opcoes_concentrar)
            max_scroll = max(0, total - max_itens)
            self.cs.scroll_concentrar = max(0, min(max_scroll, self.cs.scroll_concentrar + delta))
            if self.cs.indice_concentrar < self.cs.scroll_concentrar:
                self.cs.indice_concentrar = self.cs.scroll_concentrar
            elif self.cs.indice_concentrar >= self.cs.scroll_concentrar + max_itens:
                self.cs.indice_concentrar = self.cs.scroll_concentrar + max_itens - 1

        elif estado == "SUBMENU_ITENS":
            total = len(self.cs.itens_combate_disponiveis)
            max_scroll = max(0, total - max_itens)
            self.cs.scroll_item_combate = max(0, min(max_scroll, self.cs.scroll_item_combate + delta))
            if self.cs.indice_item_combate < self.cs.scroll_item_combate:
                self.cs.indice_item_combate = self.cs.scroll_item_combate
            elif self.cs.indice_item_combate >= self.cs.scroll_item_combate + max_itens:
                self.cs.indice_item_combate = self.cs.scroll_item_combate + max_itens - 1

    # =========================================================================
    # PROCESSAMENTO PRINCIPAL DE EVENTOS (MOUSE E TECLADO)
    # =========================================================================

    def processar_eventos(self, evento):
        """Processa eventos de mouse e teclado para navegação no combate."""
        # 1. Movimento do Mouse (Hover)
        if evento.type == pygame.MOUSEMOTION:
            pos = evento.pos
            if self.cs.estado_combate == "MENU_PRINCIPAL":
                for idx, r in enumerate(self.cs.rects_menu_principal):
                    if r.collidepoint(pos):
                        self.cs.indice_menu = idx
                        break

            elif self.cs.estado_combate == "SUBMENU_ATAQUE":
                for r, real_idx in self.cs.rects_ataques_fisicos:
                    if r.collidepoint(pos):
                        self.cs.indice_ataque_fisico = real_idx
                        break

            elif self.cs.estado_combate == "SUBMENU_MAGIA":
                for r, real_idx in self.cs.rects_magias:
                    if r.collidepoint(pos):
                        self.cs.indice_magia = real_idx
                        break

            elif self.cs.estado_combate == "SUBMENU_CONCENTRAR":
                for r, real_idx in self.cs.rects_concentrar:
                    if r.collidepoint(pos):
                        self.cs.indice_concentrar = real_idx
                        break

            elif self.cs.estado_combate == "SUBMENU_ITENS":
                for r, real_idx in self.cs.rects_itens_combate:
                    if r.collidepoint(pos):
                        self.cs.indice_item_combate = real_idx
                        break

            elif self.cs.estado_combate == "SELECIONANDO_ALVO":
                for idx, r in enumerate(self.cs.rects_inimigos):
                    if r.collidepoint(pos):
                        self.cs.indice_alvo = idx
                        break

        # 2. Roda do Mouse (Rolagem / Scroll)
        elif evento.type == pygame.MOUSEWHEEL:
            delta = -evento.y
            if self.cs.estado_combate == "SUBMENU_ATAQUE":
                self.rolar_submenu("SUBMENU_ATAQUE", delta)
            elif self.cs.estado_combate == "SUBMENU_MAGIA":
                self.rolar_submenu("SUBMENU_MAGIA", delta)
            elif self.cs.estado_combate == "SUBMENU_CONCENTRAR":
                self.rolar_submenu("SUBMENU_CONCENTRAR", delta)
            elif self.cs.estado_combate == "SUBMENU_ITENS":
                self.rolar_submenu("SUBMENU_ITENS", delta)

        # 3. Clique do Mouse (Botão Esquerdo e Botões de Scroll)
        elif evento.type == pygame.MOUSEBUTTONDOWN:
            pos = evento.pos
            
            # Suporte a Scroll via botões 4 e 5 do mouse
            if evento.button in (4, 5):
                delta = -1 if evento.button == 4 else 1
                if self.cs.estado_combate == "SUBMENU_ATAQUE":
                    self.rolar_submenu("SUBMENU_ATAQUE", delta)
                elif self.cs.estado_combate == "SUBMENU_MAGIA":
                    self.rolar_submenu("SUBMENU_MAGIA", delta)
                elif self.cs.estado_combate == "SUBMENU_CONCENTRAR":
                    self.rolar_submenu("SUBMENU_CONCENTRAR", delta)
                elif self.cs.estado_combate == "SUBMENU_ITENS":
                    self.rolar_submenu("SUBMENU_ITENS", delta)
                return

            if evento.button == 1:
                # Telas finais: Clique em qualquer lugar fecha
                if self.cs.estado_combate in ["VITORIA", "DERROTA", "FUGIU"]:
                    self.cs._concluir_fechamento_combate()
                    return

                if self.cs.estado_combate == "MENU_PRINCIPAL":
                    for idx, r in enumerate(self.cs.rects_menu_principal):
                        if r.collidepoint(pos):
                            self.cs.indice_menu = idx
                            self.selecionar_opcao_menu_principal()
                            return

                elif self.cs.estado_combate == "SUBMENU_ATAQUE":
                    if self.cs.rect_botao_voltar.collidepoint(pos):
                        self.cs.estado_combate = "MENU_PRINCIPAL"
                        return
                    if self.cs.rect_scroll_cima.collidepoint(pos):
                        self.rolar_submenu("SUBMENU_ATAQUE", -1)
                        return
                    if self.cs.rect_scroll_baixo.collidepoint(pos):
                        self.rolar_submenu("SUBMENU_ATAQUE", 1)
                        return
                    for r, real_idx in self.cs.rects_ataques_fisicos:
                        if r.collidepoint(pos):
                            self.cs.indice_ataque_fisico = real_idx
                            self.selecionar_ataque_fisico()
                            return

                elif self.cs.estado_combate == "SUBMENU_MAGIA":
                    if self.cs.rect_botao_voltar.collidepoint(pos):
                        self.cs.estado_combate = "MENU_PRINCIPAL"
                        return
                    if self.cs.rect_scroll_cima.collidepoint(pos):
                        self.rolar_submenu("SUBMENU_MAGIA", -1)
                        return
                    if self.cs.rect_scroll_baixo.collidepoint(pos):
                        self.rolar_submenu("SUBMENU_MAGIA", 1)
                        return
                    for r, real_idx in self.cs.rects_magias:
                        if r.collidepoint(pos):
                            self.cs.indice_magia = real_idx
                            self.selecionar_magia_grimorio()
                            return

                elif self.cs.estado_combate == "SUBMENU_CONCENTRAR":
                    if self.cs.rect_botao_voltar.collidepoint(pos):
                        self.cs.estado_combate = "MENU_PRINCIPAL"
                        return
                    if self.cs.rect_scroll_cima.collidepoint(pos):
                        self.rolar_submenu("SUBMENU_CONCENTRAR", -1)
                        return
                    if self.cs.rect_scroll_baixo.collidepoint(pos):
                        self.rolar_submenu("SUBMENU_CONCENTRAR", 1)
                        return
                    for r, real_idx in self.cs.rects_concentrar:
                        if r.collidepoint(pos):
                            self.cs.indice_concentrar = real_idx
                            self.selecionar_acao_concentrar()
                            return

                elif self.cs.estado_combate == "SUBMENU_ITENS":
                    if self.cs.rect_botao_voltar.collidepoint(pos):
                        self.cs.estado_combate = "MENU_PRINCIPAL"
                        return
                    if self.cs.rect_scroll_cima.collidepoint(pos):
                        self.rolar_submenu("SUBMENU_ITENS", -1)
                        return
                    if self.cs.rect_scroll_baixo.collidepoint(pos):
                        self.rolar_submenu("SUBMENU_ITENS", 1)
                        return
                    for r, real_idx in self.cs.rects_itens_combate:
                        if r.collidepoint(pos):
                            self.cs.indice_item_combate = real_idx
                            self.selecionar_item_combate()
                            return

                elif self.cs.estado_combate == "SELECIONANDO_ALVO":
                    for idx, r in enumerate(self.cs.rects_inimigos):
                        if r.collidepoint(pos):
                            self.cs.indice_alvo = idx
                            inimigos_vivos = self.cs._obter_inimigos_vivos()
                            if idx < len(inimigos_vivos):
                                alvo = inimigos_vivos[idx]
                                if self.cs.item_combate_selecionado:
                                    self.cs._executar_uso_item_ofensivo(self.cs.item_combate_selecionado, alvo)
                                else:
                                    self.cs._executar_acao_jogador(self.cs.acao_selecionada, alvo)
                            return

        # 4. Teclado
        elif evento.type == pygame.KEYDOWN:
            if self.cs.estado_combate in ["VITORIA", "DERROTA", "FUGIU"]:
                if evento.key in [pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE]:
                    self.cs._concluir_fechamento_combate()
                return

            if self.cs.estado_combate == "MENU_PRINCIPAL":
                if evento.key in [pygame.K_UP, pygame.K_w]:
                    self.cs.indice_menu = (self.cs.indice_menu - 1) % len(self.cs.opcoes_menu_principal)
                    self.cs._tocar_sfx("ui_cursor")
                elif evento.key in [pygame.K_DOWN, pygame.K_s]:
                    self.cs.indice_menu = (self.cs.indice_menu + 1) % len(self.cs.opcoes_menu_principal)
                    self.cs._tocar_sfx("ui_cursor")
                elif evento.key in [pygame.K_RETURN, pygame.K_SPACE, pygame.K_e]:
                    self.selecionar_opcao_menu_principal()

            elif self.cs.estado_combate == "SUBMENU_ATAQUE":
                if not self.cs.ataques_fisicos_disponiveis:
                    self.cs.estado_combate = "MENU_PRINCIPAL"
                    return
                if evento.key in [pygame.K_UP, pygame.K_w]:
                    self.cs.indice_ataque_fisico = (self.cs.indice_ataque_fisico - 1) % len(self.cs.ataques_fisicos_disponiveis)
                    self.ajustar_scroll_submenu("SUBMENU_ATAQUE")
                    self.cs._tocar_sfx("ui_cursor")
                elif evento.key in [pygame.K_DOWN, pygame.K_s]:
                    self.cs.indice_ataque_fisico = (self.cs.indice_ataque_fisico + 1) % len(self.cs.ataques_fisicos_disponiveis)
                    self.ajustar_scroll_submenu("SUBMENU_ATAQUE")
                    self.cs._tocar_sfx("ui_cursor")
                elif evento.key == pygame.K_PAGEUP:
                    self.rolar_submenu("SUBMENU_ATAQUE", -self.cs.ITENS_POR_PAGINA_SUBMENU)
                    self.cs._tocar_sfx("ui_cursor")
                elif evento.key == pygame.K_PAGEDOWN:
                    self.rolar_submenu("SUBMENU_ATAQUE", self.cs.ITENS_POR_PAGINA_SUBMENU)
                    self.cs._tocar_sfx("ui_cursor")
                elif evento.key in [pygame.K_RETURN, pygame.K_SPACE, pygame.K_e]:
                    self.selecionar_ataque_fisico()
                elif evento.key == pygame.K_ESCAPE:
                    self.cs._tocar_sfx("ui_voltar")
                    self.cs.estado_combate = "MENU_PRINCIPAL"

            elif self.cs.estado_combate == "SUBMENU_MAGIA":
                if not self.cs.magias_disponiveis:
                    self.cs.estado_combate = "MENU_PRINCIPAL"
                    return
                if evento.key in [pygame.K_UP, pygame.K_w]:
                    self.cs.indice_magia = (self.cs.indice_magia - 1) % len(self.cs.magias_disponiveis)
                    self.ajustar_scroll_submenu("SUBMENU_MAGIA")
                    self.cs._tocar_sfx("ui_cursor")
                elif evento.key in [pygame.K_DOWN, pygame.K_s]:
                    self.cs.indice_magia = (self.cs.indice_magia + 1) % len(self.cs.magias_disponiveis)
                    self.ajustar_scroll_submenu("SUBMENU_MAGIA")
                    self.cs._tocar_sfx("ui_cursor")
                elif evento.key == pygame.K_PAGEUP:
                    self.rolar_submenu("SUBMENU_MAGIA", -self.cs.ITENS_POR_PAGINA_SUBMENU)
                    self.cs._tocar_sfx("ui_cursor")
                elif evento.key == pygame.K_PAGEDOWN:
                    self.rolar_submenu("SUBMENU_MAGIA", self.cs.ITENS_POR_PAGINA_SUBMENU)
                    self.cs._tocar_sfx("ui_cursor")
                elif evento.key in [pygame.K_RETURN, pygame.K_SPACE, pygame.K_e]:
                    self.selecionar_magia_grimorio()
                elif evento.key == pygame.K_ESCAPE:
                    self.cs._tocar_sfx("ui_voltar")
                    self.cs.estado_combate = "MENU_PRINCIPAL"

            elif self.cs.estado_combate == "SUBMENU_CONCENTRAR":
                if not self.cs.opcoes_concentrar:
                    self.cs.estado_combate = "MENU_PRINCIPAL"
                    return
                if evento.key in [pygame.K_UP, pygame.K_w]:
                    self.cs.indice_concentrar = (self.cs.indice_concentrar - 1) % len(self.cs.opcoes_concentrar)
                    self.ajustar_scroll_submenu("SUBMENU_CONCENTRAR")
                    self.cs._tocar_sfx("ui_cursor")
                elif evento.key in [pygame.K_DOWN, pygame.K_s]:
                    self.cs.indice_concentrar = (self.cs.indice_concentrar + 1) % len(self.cs.opcoes_concentrar)
                    self.ajustar_scroll_submenu("SUBMENU_CONCENTRAR")
                    self.cs._tocar_sfx("ui_cursor")
                elif evento.key == pygame.K_PAGEUP:
                    self.rolar_submenu("SUBMENU_CONCENTRAR", -self.cs.ITENS_POR_PAGINA_SUBMENU)
                    self.cs._tocar_sfx("ui_cursor")
                elif evento.key == pygame.K_PAGEDOWN:
                    self.rolar_submenu("SUBMENU_CONCENTRAR", self.cs.ITENS_POR_PAGINA_SUBMENU)
                    self.cs._tocar_sfx("ui_cursor")
                elif evento.key in [pygame.K_RETURN, pygame.K_SPACE, pygame.K_e]:
                    self.selecionar_acao_concentrar()
                elif evento.key == pygame.K_ESCAPE:
                    self.cs._tocar_sfx("ui_voltar")
                    self.cs.estado_combate = "MENU_PRINCIPAL"

            elif self.cs.estado_combate == "SUBMENU_ITENS":
                if not self.cs.itens_combate_disponiveis:
                    self.cs.estado_combate = "MENU_PRINCIPAL"
                    return
                if evento.key in [pygame.K_UP, pygame.K_w]:
                    self.cs.indice_item_combate = (self.cs.indice_item_combate - 1) % len(self.cs.itens_combate_disponiveis)
                    self.ajustar_scroll_submenu("SUBMENU_ITENS")
                    self.cs._tocar_sfx("ui_cursor")
                elif evento.key in [pygame.K_DOWN, pygame.K_s]:
                    self.cs.indice_item_combate = (self.cs.indice_item_combate + 1) % len(self.cs.itens_combate_disponiveis)
                    self.ajustar_scroll_submenu("SUBMENU_ITENS")
                    self.cs._tocar_sfx("ui_cursor")
                elif evento.key == pygame.K_PAGEUP:
                    self.rolar_submenu("SUBMENU_ITENS", -self.cs.ITENS_POR_PAGINA_SUBMENU)
                    self.cs._tocar_sfx("ui_cursor")
                elif evento.key == pygame.K_PAGEDOWN:
                    self.rolar_submenu("SUBMENU_ITENS", self.cs.ITENS_POR_PAGINA_SUBMENU)
                    self.cs._tocar_sfx("ui_cursor")
                elif evento.key in [pygame.K_RETURN, pygame.K_SPACE, pygame.K_e]:
                    self.selecionar_item_combate()
                elif evento.key == pygame.K_ESCAPE:
                    self.cs._tocar_sfx("ui_voltar")
                    self.cs.estado_combate = "MENU_PRINCIPAL"

            elif self.cs.estado_combate == "SELECIONANDO_ALVO":
                inimigos_vivos = self.cs._obter_inimigos_vivos()
                if not inimigos_vivos:
                    return

                if evento.key in [pygame.K_UP, pygame.K_w]:
                    self.cs.indice_alvo = (self.cs.indice_alvo - 1) % len(inimigos_vivos)
                    self.cs._tocar_sfx("ui_cursor")
                elif evento.key in [pygame.K_DOWN, pygame.K_s]:
                    self.cs.indice_alvo = (self.cs.indice_alvo + 1) % len(inimigos_vivos)
                    self.cs._tocar_sfx("ui_cursor")
                elif evento.key in [pygame.K_RETURN, pygame.K_SPACE, pygame.K_e]:
                    alvo = inimigos_vivos[self.cs.indice_alvo]
                    if self.cs.item_combate_selecionado:
                        self.cs._executar_uso_item_ofensivo(self.cs.item_combate_selecionado, alvo)
                    else:
                        self.cs._executar_acao_jogador(self.cs.acao_selecionada, alvo)
                elif evento.key == pygame.K_ESCAPE:
                    self.cs._tocar_sfx("ui_voltar")
                    self.cs.estado_combate = "MENU_PRINCIPAL"

    # =========================================================================
    # LÓGICA DE SELEÇÃO DE AÇÕES E NAVEGAÇÃO ENTRE SUBMENUS
    # =========================================================================

    def selecionar_opcao_menu_principal(self):
        """Seleciona uma das opções do menu principal ou abre o submenu respectivo."""
        opcao = self.cs.opcoes_menu_principal[self.cs.indice_menu]

        if opcao == "Atacar":
            self.cs._tocar_sfx("ui_confirmar")
            self.cs._carregar_ataques_fisicos_jogador()
            self.cs.estado_combate = "SUBMENU_ATAQUE"
            self.cs.indice_ataque_fisico = 0
            self.cs.scroll_ataque = 0

        elif opcao == "Magias":
            self.cs._tocar_sfx("ui_confirmar")
            self.cs._carregar_magias_jogador()
            self.cs.estado_combate = "SUBMENU_MAGIA"
            self.cs.indice_magia = 0
            self.cs.scroll_magia = 0

        elif opcao == "Concentrar":
            self.cs._tocar_sfx("ui_confirmar")
            self.cs._carregar_acoes_concentrar()
            self.cs.estado_combate = "SUBMENU_CONCENTRAR"
            self.cs.indice_concentrar = 0
            self.cs.scroll_concentrar = 0

        elif opcao == "Itens":
            self.cs._carregar_itens_combate_jogador()
            if not self.cs.itens_combate_disponiveis:
                self.cs._tocar_sfx("ui_erro")
                self.cs.adicionar_log(CombatNarrator.obter_mensagem("sem_consumiveis"))
                return
            self.cs._tocar_sfx("ui_confirmar")
            self.cs.estado_combate = "SUBMENU_ITENS"
            self.cs.indice_item_combate = 0
            self.cs.scroll_item_combate = 0

        elif opcao == "Fugir":
            self.cs._tentar_fuga()

    def selecionar_item_combate(self):
        """Seleciona o item consumível do inventário para uso."""
        if not self.cs.itens_combate_disponiveis:
            return
        idx_real, item_slot = self.cs.itens_combate_disponiveis[self.cs.indice_item_combate]
        item = item_slot.item
        
        self.cs._tocar_sfx("ui_confirmar")
        if getattr(item, 'tipo_consumivel', '') == "DANO_OFENSIVO":
            inimigos_vivos = self.cs._obter_inimigos_vivos()
            if len(inimigos_vivos) == 1:
                self.cs._executar_uso_item_ofensivo(item, inimigos_vivos[0])
            else:
                self.cs.item_combate_selecionado = item
                self.cs.estado_combate = "SELECIONANDO_ALVO"
                self.cs.indice_alvo = 0
        else:
            self.cs._executar_uso_item_suporte(item)

    def selecionar_ataque_fisico(self):
        """Seleciona o ataque físico do submenu para execução contra o alvo."""
        if not self.cs.ataques_fisicos_disponiveis:
            return

        ataque = self.cs.ataques_fisicos_disponiveis[self.cs.indice_ataque_fisico]
        if ataque.custo_mana > 0 and self.cs.jogador.mana_atual < ataque.custo_mana:
            self.cs._tocar_sfx("ui_erro")
            self.cs.adicionar_log(CombatNarrator.obter_mensagem("mana_insuficiente", mana_atual=self.cs.jogador.mana_atual, custo_mana=ataque.custo_mana))
            return

        self.cs._tocar_sfx("ui_confirmar")
        inimigos_vivos = self.cs._obter_inimigos_vivos()
        if len(inimigos_vivos) == 1:
            self.cs._executar_acao_jogador(ataque, inimigos_vivos[0])
        else:
            self.cs.acao_selecionada = ataque
            self.cs.estado_combate = "SELECIONANDO_ALVO"
            self.cs.indice_alvo = 0

    def selecionar_acao_concentrar(self):
        """Executa a ação tática de Concentração ou Defesa selecionada no submenu."""
        if not self.cs.opcoes_concentrar:
            return
        self.cs._tocar_sfx("ui_confirmar")
        acao = self.cs.opcoes_concentrar[self.cs.indice_concentrar]
        self.cs._executar_acao_jogador(acao, self.cs.jogador)

    def selecionar_magia_grimorio(self):
        """Seleciona a magia do Grimório de Halia para execução contra o alvo ou em si mesma."""
        if not self.cs.magias_disponiveis:
            return

        magia = self.cs.magias_disponiveis[self.cs.indice_magia]
        if self.cs.jogador.mana_atual < magia.custo_mana:
            self.cs._tocar_sfx("ui_erro")
            self.cs.adicionar_log(CombatNarrator.obter_mensagem("mana_insuficiente", mana_atual=self.cs.jogador.mana_atual, custo_mana=magia.custo_mana))
            return

        self.cs._tocar_sfx("ui_confirmar")

        alvo_tipo_padrao = getattr(magia, 'tipo_alvo', getattr(magia, 'alvo_tipo', 'inimigo_unico')).lower()
        if alvo_tipo_padrao in ["aliado", "proprio"]:
            self.cs._executar_acao_jogador(magia, self.cs.jogador)
        elif alvo_tipo_padrao in ["todos_inimigos", "todos"]:
            self.cs._executar_acao_jogador(magia, self.cs.inimigos)
        else: # inimigo_unico
            inimigos_vivos = self.cs._obter_inimigos_vivos()
            if len(inimigos_vivos) == 1:
                self.cs._executar_acao_jogador(magia, inimigos_vivos[0])
            else:
                self.cs.acao_selecionada = magia
                self.cs.estado_combate = "SELECIONANDO_ALVO"
                self.cs.indice_alvo = 0
