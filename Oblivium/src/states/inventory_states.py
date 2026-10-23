# src/states/inventory_states.py
import pygame
from src.states.states import State
from src.utils.colors import (
    CARVAO_PROFUNDO, CINZA_ARDOSIA, CINZA_LINHO,
    MARFIM_OFFWHITE, BORDA_DESTAQUE
)
from src.utils.resource_manager import ResourceManager
from src.ui.ui_utils import (
    desenhar_painel_padrao, desenhar_flor_botanica,
    quebrar_texto_em_linhas
)
from src.mechanics.items import ConsumivelItem, EquipamentoItem, GrimorioItem
from src.mechanics.skills import ActionCatalog
from src.mechanics.crafting import CraftingManager
from src.states.inventory_tabs import (
    TabInventarioRenderer,
    TabPerfilRenderer,
    TabMagiaRenderer,
    TabCraftingRenderer
)

class InventoryState(State):
    """
    Interface de Menu Geral de Oblivium:
    - [1] INVENTÁRIO: Equipamentos no topo (Roupa, Cajado, Acessórios I e II),
      4 Slots de Grimórios abaixo (Grimórios I, II, III e IV),
      Grelha da bolsa à direita e Tooltip Flutuante que acompanha o mouse.
    - [2] PERFIL: Dividido em 2 blocos limpos e arejados:
      - Bloco 1: Vida, Mana, Esquiva, Bloqueio/Defesa, Crítico, Poder Mágico e Carteira (Ouro, Prata e Cobre).
      - Bloco 2: Os 6 Atributos (INT, SAB, PRE, CON, DES, FOR) com valores e modificadores D20.
    - [3] MAGIA: 2 Colunas (Lista com Scroll na esquerda, Detalhes completos na direita).
    - [4] CRAFTING: Bancada de Fabricação de Alquimia, Forja e Refinamento de Equipamentos.
    """
    def __init__(self, game):
        super().__init__(game)
        self.overlay = pygame.Surface((self.game.LARGURA, self.game.ALTURA))
        self.overlay.fill((8, 8, 11))
        self.overlay.set_alpha(225)
        
        # Tipografia Editorial
        self.fonte_titulo = ResourceManager.carregar_fonte("sunday", 28)
        self.fonte_sub = ResourceManager.carregar_fonte("sunday", 19)
        self.fonte_abas_principais = ResourceManager.carregar_fonte("sunday", 17)
        self.fonte_abas = ResourceManager.carregar_fonte("contrail", 17)
        self.fonte_destaque = ResourceManager.carregar_fonte("contrail", 19)
        self.fonte_texto = ResourceManager.carregar_fonte("contrail", 16)
        self.fonte_mini = ResourceManager.carregar_fonte("contrail", 13)
        self.fonte_poetica = ResourceManager.carregar_fonte("just_breathe", 20)
        
        # 4 Abas Principais do Menu
        self.abas_principais = ["Inventário", "Perfil", "Magia", "Crafting"]
        self.aba_principal_ativa = 0  # 0: INVENTÁRIO, 1: PERFIL, 2: MAGIA, 3: CRAFTING
        self.rects_abas_principais = []

        # Sub-abas da Bolsa no Inventário
        self.sub_abas_bolsa = ["Bolsa", "Equipamentos", "Materiais", "Outros"]
        self.mapa_sub_categorias = {
            0: "TODOS",
            1: "EQUIPAMENTO",
            2: "MATERIAL",
            3: "CHAVE"
        }
        self.sub_aba_bolsa_ativa = 0
        self.rects_sub_abas_bolsa = []
        
        # Dimensões do Painel Central
        self.largura_menu = min(1140, self.game.LARGURA - 40)
        self.altura_menu = min(640, self.game.ALTURA - 40)
        self.x_menu = (self.game.LARGURA - self.largura_menu) // 2
        self.y_menu = (self.game.ALTURA - self.altura_menu) // 2
        
        # Slots de Equipamentos (Topo Esquerdo: 4 slots)
        self.slot_roupa = pygame.Rect(self.x_menu + 45, self.y_menu + 115, 84, 82)
        self.slot_cajado = pygame.Rect(self.x_menu + 137, self.y_menu + 115, 84, 82)
        self.slot_acess1 = pygame.Rect(self.x_menu + 229, self.y_menu + 115, 84, 82)
        self.slot_acess2 = pygame.Rect(self.x_menu + 321, self.y_menu + 115, 84, 82)
        
        # 4 Slots de Grimórios (Abaixo dos Equipamentos)
        self.slots_grimorios = [
            pygame.Rect(self.x_menu + 45 + (i * 92), self.y_menu + 260, 84, 82)
            for i in range(4)
        ]
        
        # Grelha de Itens da Bolsa (Painel Direito: 4 colunas x 4 linhas)
        self.slots_gerais = []
        self._recalcular_grid_slots()
                
        # Estado de Magias
        self.magia_selecionada_idx = 0
        self.scroll_magias = 0
        self.rects_lista_magias = []

        # Estado de Crafting
        self.receita_selecionada_idx = 0
        self.scroll_crafting = 0
        self.rects_lista_receitas = []
        self.rect_botao_fabricar = None

        # Estado de Navegação e Hover
        self.pos_mouse = (0, 0)
        self.slot_hover = None
        self.tooltip_info = None

        # Feedback
        self.mensagem_feedback = ""
        self.timer_feedback = 0

        # Renderizadores Modulares para cada Aba do Menu
        self.tab_inventario = TabInventarioRenderer(self)
        self.tab_perfil = TabPerfilRenderer(self)
        self.tab_magia = TabMagiaRenderer(self)
        self.tab_crafting = TabCraftingRenderer(self)

    def _recalcular_grid_slots(self):
        """Calcula os retângulos da grelha de itens na direita do inventário."""
        self.slots_gerais.clear()
        linhas, colunas = 4, 4
        inicio_x_grid = self.x_menu + 475
        inicio_y_grid = self.y_menu + 120
        tamanho_w, tamanho_h = 138, 95
        
        for l in range(linhas):
            for c in range(colunas):
                r = pygame.Rect(
                    inicio_x_grid + (c * (tamanho_w + 8)),
                    inicio_y_grid + (l * (tamanho_h + 8)),
                    tamanho_w,
                    tamanho_h
                )
                self.slots_gerais.append(r)

    def exibir_mensagem(self, texto, duracao_ticks=150):
        """Exibe notificação na barra inferior do menu."""
        self.mensagem_feedback = texto
        self.timer_feedback = duracao_ticks

    def handle_events(self, eventos, teclas):
        self.pos_mouse = pygame.mouse.get_pos()
        self.slot_hover = None
        self.tooltip_info = None

        halia = getattr(self.game, 'halia', None)
        inv = getattr(halia, 'inventario', None) if halia else None

        # 1. Hover e Tooltips na Aba de Inventário
        if self.aba_principal_ativa == 0:
            # Slots de Equipamento (Roupa, Cajado, Acessórios)
            slots_eq = [
                (self.slot_roupa, "ROUPA", "Slot de Roupa", "Espaço para mantos e túnicas arcanas."),
                (self.slot_cajado, "CAJADO", "Slot de Cajado", "Espaço para foco arcano e cajados mágicos."),
                (self.slot_acess1, "ACESSORIO_1", "Acessório I", "Espaço para anéis, medalhões e relíquias."),
                (self.slot_acess2, "ACESSORIO_2", "Acessório II", "Espaço para anéis, medalhões e relíquias.")
            ]
            for r_s, nome_s, tit_padrao, desc_padrao in slots_eq:
                if r_s.collidepoint(self.pos_mouse):
                    self.slot_hover = ("equipamento", nome_s)
                    item = inv.equipados.get(nome_s) if inv else None
                    if item:
                        self.tooltip_info = self._gerar_tooltip_item(item)
                    else:
                        self.tooltip_info = (tit_padrao, desc_padrao, "Vazio")
                    break

            # 4 Slots de Grimórios
            if not self.slot_hover:
                for i, r_g in enumerate(self.slots_grimorios):
                    if r_g.collidepoint(self.pos_mouse):
                        chave_g = f"GRIMORIO_{i+1}"
                        self.slot_hover = ("equipamento", chave_g)
                        item_g = inv.equipados.get(chave_g) if inv else None
                        if item_g:
                            self.tooltip_info = self._gerar_tooltip_item(item_g)
                        else:
                            self.tooltip_info = (f"Grimório {i+1}", "Espaço para tomos arcanos e livros de feitiços.", "Vazio")
                        break

            # Slots da Bolsa
            if not self.slot_hover and inv:
                cat_filtro = self.mapa_sub_categorias[self.sub_aba_bolsa_ativa]
                itens_filtrados = inv.obter_itens_por_categoria(cat_filtro)

                for idx_slot, rect_s in enumerate(self.slots_gerais):
                    if rect_s.collidepoint(self.pos_mouse):
                        if idx_slot < len(itens_filtrados):
                            idx_real, item_slot = itens_filtrados[idx_slot]
                            self.slot_hover = ("bolsa", idx_real, item_slot)
                            self.tooltip_info = self._gerar_tooltip_item(item_slot.item, item_slot.quantidade)
                        break

        # Processamento de Teclado e Mouse
        for evento in eventos:
            if evento.type == pygame.KEYDOWN:
                tecla_inv = self.game.controles.get("Inventário", pygame.K_TAB)
                if evento.key in [pygame.K_ESCAPE, tecla_inv]:
                    self.game.mudar_estado("JOGANDO")
                    return

                flashback_ok = getattr(self.game, 'flashback_magia_concluido', False) or (halia and halia.fragmentos_memoria > 0)

                # Atalhos de Abas Principais (1: Inventário, 2: Perfil, 3: Magia, 4: Crafting)
                if evento.key == pygame.K_1:
                    self.aba_principal_ativa = 0
                elif evento.key == pygame.K_2:
                    self.aba_principal_ativa = 1
                elif evento.key == pygame.K_3:
                    self.aba_principal_ativa = 2
                elif evento.key == pygame.K_4:
                    self.aba_principal_ativa = 3
                
                # Alternar abas com Q / E
                elif evento.key == pygame.K_q:
                    self.aba_principal_ativa = (self.aba_principal_ativa - 1) % len(self.abas_principais)
                elif evento.key == pygame.K_e:
                    self.aba_principal_ativa = (self.aba_principal_ativa + 1) % len(self.abas_principais)

                # Navegação vertical na lista de magias
                elif self.aba_principal_ativa == 2 and flashback_ok:
                    magias_ids = getattr(halia, 'magias_desbloqueadas', ["bola_de_fogo", "levitar", "brisa_curativa"])
                    if evento.key == pygame.K_UP:
                        self.magia_selecionada_idx = max(0, self.magia_selecionada_idx - 1)
                        self._ajustar_scroll_magia()
                    elif evento.key == pygame.K_DOWN:
                        self.magia_selecionada_idx = min(len(magias_ids) - 1, self.magia_selecionada_idx + 1)
                        self._ajustar_scroll_magia()

                # Navegação e Atalhos na Aba Crafting
                elif self.aba_principal_ativa == 3:
                    receitas = CraftingManager.obter_todas_receitas()
                    if evento.key == pygame.K_UP:
                        self.receita_selecionada_idx = max(0, self.receita_selecionada_idx - 1)
                        self._ajustar_scroll_crafting()
                    elif evento.key == pygame.K_DOWN:
                        self.receita_selecionada_idx = min(len(receitas) - 1, self.receita_selecionada_idx + 1)
                        self._ajustar_scroll_crafting()
                    elif evento.key in [pygame.K_RETURN, pygame.K_SPACE]:
                        self._executar_crafting_selecionado(halia)

            elif evento.type == pygame.MOUSEWHEEL:
                if self.aba_principal_ativa == 2:
                    self.scroll_magias = max(0, self.scroll_magias - (evento.y * 36))
                elif self.aba_principal_ativa == 3:
                    self.scroll_crafting = max(0, self.scroll_crafting - (evento.y * 36))

            elif evento.type == pygame.MOUSEBUTTONDOWN:
                if evento.button == 1:  # Clique Esquerdo
                    flashback_ok = getattr(self.game, 'flashback_magia_concluido', False) or (halia and halia.fragmentos_memoria > 0)
                    
                    # Clique nas Abas Principais
                    for i, r_aba in enumerate(self.rects_abas_principais):
                        if r_aba.collidepoint(evento.pos):
                            self.aba_principal_ativa = i
                            return

                    # Interações na Aba Magia (Seleção por clique)
                    if self.aba_principal_ativa == 2 and flashback_ok:
                        for idx_m, r_m in enumerate(self.rects_lista_magias):
                            if r_m.collidepoint(evento.pos):
                                self.magia_selecionada_idx = idx_m
                                return

                    # Interações na Aba Crafting (Seleção e Botão Fabricar)
                    if self.aba_principal_ativa == 3:
                        for idx_r, r_rec in enumerate(self.rects_lista_receitas):
                            if r_rec.collidepoint(evento.pos):
                                self.receita_selecionada_idx = idx_r
                                return

                        if self.rect_botao_fabricar and self.rect_botao_fabricar.collidepoint(evento.pos):
                            self._executar_crafting_selecionado(halia)
                            return

                    # Sub-abas da Bolsa no Inventário
                    if self.aba_principal_ativa == 0:
                        for s_idx, r_sub in enumerate(self.rects_sub_abas_bolsa):
                            if r_sub.collidepoint(evento.pos):
                                self.sub_aba_bolsa_ativa = s_idx
                                return

                        # Usar / Equipar Item da Bolsa
                        if self.slot_hover and self.slot_hover[0] == "bolsa" and inv:
                            idx_real = self.slot_hover[1]
                            item_slot = self.slot_hover[2]
                            item = item_slot.item

                            if isinstance(item, ConsumivelItem):
                                res = item.usar(halia, em_combate=False)
                                if res["sucesso"]:
                                    inv.remover_item(item.id, 1)
                                    halia.recalcular_status_derivados(manter_porcentagem=False)
                                    self.exibir_mensagem(f"✦ {res['mensagem']}")
                                else:
                                    self.exibir_mensagem(f"⚠ {res['mensagem']}")

                            elif isinstance(item, EquipamentoItem):
                                slot_destino = item.slot
                                if "ACESSORIO" in slot_destino:
                                    slot_destino = "ACESSORIO_1" if inv.equipados["ACESSORIO_1"] is None else "ACESSORIO_2"

                                sucesso, msg = inv.equipar(slot_destino, idx_real)
                                if sucesso:
                                    halia.recalcular_status_derivados(manter_porcentagem=False)
                                    self.exibir_mensagem(f"✦ {msg}")
                                else:
                                    self.exibir_mensagem(f"⚠ {msg}")

                            elif isinstance(item, GrimorioItem) or getattr(item, 'categoria', '') == "GRIMORIO":
                                slot_g = None
                                for g_key in ["GRIMORIO_1", "GRIMORIO_2", "GRIMORIO_3", "GRIMORIO_4"]:
                                    if inv.equipados[g_key] is None:
                                        slot_g = g_key
                                        break
                                slot_g = slot_g or "GRIMORIO_1"
                                sucesso, msg = inv.equipar(slot_g, idx_real)
                                if sucesso:
                                    self.exibir_mensagem(f"✦ {msg}")

                elif evento.button == 3:  # Clique Direito (Desequipar)
                    if self.aba_principal_ativa == 0 and self.slot_hover and self.slot_hover[0] == "equipamento" and inv:
                        slot_nome = self.slot_hover[1]
                        if inv.equipados.get(slot_nome):
                            sucesso, msg = inv.desequipar(slot_nome)
                            if sucesso:
                                halia.recalcular_status_derivados(manter_porcentagem=False)
                                self.exibir_mensagem(f"✦ {msg}")
                            else:
                                self.exibir_mensagem(f"⚠ {msg}")

    def _ajustar_scroll_magia(self):
        """Garante que a magia selecionada permaneça visível no viewport com scroll."""
        h_card = 82
        y_selecionado = self.magia_selecionada_idx * h_card
        viewport_h = 420
        if y_selecionado < self.scroll_magias:
            self.scroll_magias = y_selecionado
        elif y_selecionado + h_card > self.scroll_magias + viewport_h:
            self.scroll_magias = y_selecionado + h_card - viewport_h

    def _ajustar_scroll_crafting(self):
        """Garante que a receita selecionada permaneça visível no viewport."""
        h_card = 82
        y_selecionado = self.receita_selecionada_idx * h_card
        viewport_h = 420
        if y_selecionado < self.scroll_crafting:
            self.scroll_crafting = y_selecionado
        elif y_selecionado + h_card > self.scroll_crafting + viewport_h:
            self.scroll_crafting = y_selecionado + h_card - viewport_h

    def _executar_crafting_selecionado(self, halia):
        """Executa a fabricação da receita selecionada com feedback na UI."""
        if not halia:
            return
        receitas = CraftingManager.obter_todas_receitas()
        if not receitas or self.receita_selecionada_idx >= len(receitas):
            return

        rec = receitas[self.receita_selecionada_idx]
        sucesso, msg = CraftingManager.fabricar(rec.id, halia)
        if sucesso:
            self.exibir_mensagem(msg)
            if hasattr(self.game, 'notificacoes') and self.game.notificacoes:
                self.game.notificacoes.notificar(
                    "notificacao_item_fabricado",
                    quantidade=rec.resultado_quantidade,
                    nome=rec.nome
                )
            if hasattr(self.game, 'conquistas') and self.game.conquistas:
                self.game.conquistas.desbloquear("primeira_receita")
            halia.recalcular_status_derivados(manter_porcentagem=False)
        else:
            self.exibir_mensagem(f"⚠ {msg}")

    def _gerar_tooltip_item(self, item, quantidade=None):
        """Gera título, descrição e detalhes para a caixa flutuante de tooltip."""
        nome = item.nome_formatado if hasattr(item, 'nome_formatado') else item.nome
        if quantidade and quantidade > 1:
            nome = f"{nome} (x{quantidade})"
        
        linhas_detalhes = []
        cat = "Grimório" if item.categoria == "GRIMORIO" else item.categoria.capitalize()
        linhas_detalhes.append(f"Tipo: {cat}  |  Raridade: {item.raridade}")

        if isinstance(item, ConsumivelItem):
            if item.tipo_consumivel == "CURA_HP":
                linhas_detalhes.append(f"✦ Efeito: Restaura +{item.valor_efeito} Pontos de Vida (HP)")
            elif item.tipo_consumivel == "RESTAURA_MP":
                linhas_detalhes.append(f"✦ Efeito: Restaura +{item.valor_efeito} Pontos de Mana (MP)")
            elif item.tipo_consumivel == "DANO_OFENSIVO":
                linhas_detalhes.append(f"⚔ Efeito: Causa {item.valor_efeito} de dano")
            elif item.tipo_consumivel == "CURA_CONDICAO":
                linhas_detalhes.append("✦ Efeito: Purifica venenos e aflições")

        elif isinstance(item, EquipamentoItem):
            up = getattr(item, 'nivel_upgrade', 0)
            linhas_detalhes.append(f"Slot: {item.slot} (Nível +{up})")
            if hasattr(item, 'obter_bonus_atributos_efetivos'):
                for attr, val in item.obter_bonus_atributos_efetivos().items():
                    linhas_detalhes.append(f"  + {attr.capitalize()}: +{val}")
            if hasattr(item, 'obter_bonus_stats_efetivos'):
                for stat, val in item.obter_bonus_stats_efetivos().items():
                    nome_s = stat.replace("_", " ").title()
                    linhas_detalhes.append(f"  + {nome_s}: +{val}")

        elif isinstance(item, GrimorioItem) or getattr(item, 'categoria', '') == "GRIMORIO":
            magia = getattr(item, 'magia_id', 'Chama Ancestral').replace('_', ' ').title()
            linhas_detalhes.append(f"• Feitiço Vinculado: {magia}")

        detalhes_str = "\n".join(linhas_detalhes)
        return (nome, item.descricao, detalhes_str)

    def update(self):
        if self.timer_feedback > 0:
            self.timer_feedback -= 1
            if self.timer_feedback == 0:
                self.mensagem_feedback = ""

    def draw(self, tela):
        # 1. Fundo do jogo com escurecimento
        if "JOGANDO" in self.game.estados:
            self.game.estados["JOGANDO"].draw(tela)
        tela.blit(self.overlay, (0, 0))

        # 2. Painel Mestre
        rect_mestre = pygame.Rect(self.x_menu, self.y_menu, self.largura_menu, self.altura_menu)
        desenhar_painel_padrao(tela, rect_mestre, cor_fundo=CARVAO_PROFUNDO, cor_borda=CINZA_LINHO, largura_borda=1, border_radius=4, alpha=250)
        pygame.draw.rect(tela, (28, 28, 34), rect_mestre.inflate(-10, -10), 1, border_radius=2)

        # 3. Cabeçalho com as 4 Abas Principais
        self._desenhar_cabecalho_abas(tela)

        # 4. Conteúdo da Aba Ativa
        halia = getattr(self.game, 'halia', None)
        if self.aba_principal_ativa == 0:
            self._desenhar_aba_inventario(tela, halia)
        elif self.aba_principal_ativa == 1:
            self._desenhar_aba_perfil(tela, halia)
        elif self.aba_principal_ativa == 2:
            self._desenhar_aba_magia(tela, halia)
        elif self.aba_principal_ativa == 3:
            self._desenhar_aba_crafting(tela, halia)

        # 5. Rodapé
        self._desenhar_rodape(tela)

        # 6. Tooltip Flutuante (Renderizado por cima de tudo)
        if self.tooltip_info:
            tit, desc, extra = self.tooltip_info
            texto_corpo = f"{desc}\n\n{extra}" if extra else desc
            self._desenhar_tooltip_flutuante(tela, self.pos_mouse[0] + 18, self.pos_mouse[1] + 18, tit, texto_corpo)

        # 7. Aplica o Filtro de Memória sobre todo o Inventário (Painel, Abas, Tooltips e Ícones)
        if hasattr(self.game, 'filtro_memoria') and self.game.filtro_memoria:
            self.game.filtro_memoria.aplicar_filtro(tela)

    def _desenhar_cabecalho_abas(self, tela):
        """Renderiza os botões superiores das 4 abas principais."""
        self.rects_abas_principais.clear()
        txt_nome = self.fonte_titulo.render("Halia", True, MARFIM_OFFWHITE)
        tela.blit(txt_nome, (self.x_menu + 35, self.y_menu + 20))
        desenhar_flor_botanica(tela, self.x_menu + 120, self.y_menu + 32, cor=CINZA_LINHO, escala=0.65)

        x_aba = self.x_menu + 260
        y_aba = self.y_menu + 18
        largura_btn = 150
        altura_btn = 34

        for i, nome_aba in enumerate(self.abas_principais):
            ativa = (i == self.aba_principal_ativa)
            rect_btn = pygame.Rect(x_aba, y_aba, largura_btn, altura_btn)
            self.rects_abas_principais.append(rect_btn)

            if ativa:
                fundo = (38, 38, 48)
                cor_borda = MARFIM_OFFWHITE
                cor_texto = MARFIM_OFFWHITE
                label = f"✦ [{i+1}] {nome_aba}"
            else:
                fundo = (22, 22, 28)
                cor_borda = CINZA_ARDOSIA
                cor_texto = CINZA_LINHO
                label = f"[{i+1}] {nome_aba}"

            pygame.draw.rect(tela, fundo, rect_btn, border_radius=3)
            pygame.draw.rect(tela, cor_borda, rect_btn, 2 if ativa else 1, border_radius=3)

            if ativa:
                pygame.draw.line(tela, (230, 215, 160), (rect_btn.left + 6, rect_btn.bottom - 2), (rect_btn.right - 6, rect_btn.bottom - 2), 2)

            txt_btn = self.fonte_abas_principais.render(label, True, cor_texto)
            tela.blit(txt_btn, (rect_btn.centerx - txt_btn.get_width() // 2, rect_btn.centery - txt_btn.get_height() // 2))
            x_aba += largura_btn + 12

        pygame.draw.line(tela, CINZA_ARDOSIA, (self.x_menu + 25, self.y_menu + 62), (self.x_menu + self.largura_menu - 25, self.y_menu + 62), 1)

    # =========================================================================
    # RENDERIZAÇÃO DAS ABAS (DELEGADAS AOS RENDERIZADORES ESPECIALIZADOS)
    # =========================================================================
    def _desenhar_aba_inventario(self, tela, halia):
        self.tab_inventario.desenhar(tela, halia)

    def _desenhar_aba_perfil(self, tela, halia):
        self.tab_perfil.desenhar(tela, halia)

    def _desenhar_aba_magia(self, tela, halia):
        self.tab_magia.desenhar(tela, halia)

    def _desenhar_aba_crafting(self, tela, halia):
        self.tab_crafting.desenhar(tela, halia)

    # =========================================================================
    # TOOLTIP FLUTUANTE
    # =========================================================================
    def _desenhar_tooltip_flutuante(self, tela, x, y, titulo, descricao):
        """Renderiza a caixinha flutuante com informações do item acompanhando o cursor."""
        largura_max = 340
        linhas_desc = quebrar_texto_em_linhas(descricao, self.fonte_mini, largura_max - 28)
        
        altura_estimada = 44 + (len(linhas_desc) * 18) + 16
        
        # Garante que não ultrapasse as bordas da tela
        if x + largura_max > self.game.LARGURA - 15:
            x = self.game.LARGURA - largura_max - 15
        if y + altura_estimada > self.game.ALTURA - 15:
            y = self.game.ALTURA - altura_estimada - 15
        if x < 15:
            x = 15
        if y < 15:
            y = 15

        r_tool = pygame.Rect(x, y, largura_max, altura_estimada)
        desenhar_painel_padrao(tela, r_tool, cor_fundo=(16, 16, 20), cor_borda=MARFIM_OFFWHITE, largura_borda=1, border_radius=3, alpha=250)

        # Título
        txt_t = self.fonte_destaque.render(titulo, True, (240, 225, 160))
        tela.blit(txt_t, (r_tool.x + 14, r_tool.y + 10))
        pygame.draw.line(tela, CINZA_ARDOSIA, (r_tool.x + 14, r_tool.y + 32), (r_tool.right - 14, r_tool.y + 32), 1)

        # Linhas de Texto
        y_txt = r_tool.y + 40
        for l in linhas_desc:
            cor_l = (150, 220, 170) if "+" in l else ((140, 190, 240) if "•" in l or "✦" in l else MARFIM_OFFWHITE)
            txt_l = self.fonte_mini.render(l, True, cor_l)
            tela.blit(txt_l, (r_tool.x + 14, y_txt))
            y_txt += 18

    # =========================================================================
    # RODAPÉ
    # =========================================================================
    def _desenhar_rodape(self, tela):
        y_rodape = self.y_menu + self.altura_menu - 36
        if self.mensagem_feedback:
            txt_f = self.fonte_destaque.render(self.mensagem_feedback, True, (150, 240, 180))
            tela.blit(txt_f, (self.x_menu + 45, y_rodape))
        else:
            txt_guia = self.fonte_mini.render("[1/2/3/4/Q/E] Trocar Abas   |   [Clique Esq] Usar / Equipar / Criar   |   [Clique Dir] Desequipar   |   [ESC/I] Fechar", True, CINZA_LINHO)
            tela.blit(txt_guia, (self.x_menu + 45, y_rodape))