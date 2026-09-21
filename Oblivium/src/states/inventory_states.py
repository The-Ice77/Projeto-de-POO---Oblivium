# src/states/inventory_states.py
import pygame
import math
from src.states.states import State
from src.utils.colors import (
    PRETO, BRANCO, CARVAO_PROFUNDO, CINZA_ARDOSIA, CINZA_LINHO, CINZA_CLARO,
    MARFIM_OFFWHITE, UI_TEXTO_DESTAQUE, UI_TEXTO_APAGADO, BORDA_PADRAO, BORDA_DESTAQUE,
    PERGAMINHO_BG, PERGAMINHO_BORDA, PERGAMINHO_TINTA, BARRA_VIDA_JOGADOR, BARRA_MANA,
    AZUL_HOVER_BG, AZUL_HOVER_MENU
)
from src.utils.resource_manager import ResourceManager
from src.ui.ui_utils import (
    desenhar_painel_padrao, desenhar_tooltip_formatado, desenhar_flor_botanica,
    desenhar_barra_status_interpolada, desenhar_card_pergaminho, quebrar_texto_em_linhas
)
from src.mechanics.items import ConsumivelItem, EquipamentoItem, GrimorioItem, MaterialItem, ItemChave
from src.mechanics.skills import ActionCatalog
from src.mechanics.grimorio import GrimorioHalia
from src.mechanics.crafting import CraftingManager, Receita
from src.mechanics.item_factory import ItemFactory

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
                tecla_inv = self.game.controles.get("Inventário", pygame.K_i)
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
                
                # Alternar abas com Q / E ou TAB
                elif evento.key == pygame.K_q:
                    self.aba_principal_ativa = (self.aba_principal_ativa - 1) % len(self.abas_principais)
                elif evento.key in [pygame.K_e, pygame.K_TAB]:
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
                    titulo="Item Fabricado",
                    mensagem=f"Obteve {rec.resultado_quantidade}x {rec.nome}.",
                    tipo="RECEITA",
                    icone="🧪"
                )
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
    # [1] ABA INVENTÁRIO
    # =========================================================================
    def _desenhar_aba_inventario(self, tela, halia):
        inv = getattr(halia, 'inventario', None) if halia else None

        # 1. EQUIPAMENTOS (Topo Esquerdo)
        txt_eq = self.fonte_sub.render("Equipamentos Arcanos", True, MARFIM_OFFWHITE)
        tela.blit(txt_eq, (self.x_menu + 45, self.y_menu + 78))

        slots_eq_dados = [
            (self.slot_roupa, "ROUPA", "Roupa"),
            (self.slot_cajado, "CAJADO", "Cajado"),
            (self.slot_acess1, "ACESSORIO_1", "Acessório I"),
            (self.slot_acess2, "ACESSORIO_2", "Acessório II")
        ]

        for rect_s, nome_s, rotulo in slots_eq_dados:
            hover = (self.slot_hover and self.slot_hover[0] == "equipamento" and self.slot_hover[1] == nome_s)
            item_eq = inv.equipados.get(nome_s) if inv else None
            
            fundo_s = (36, 36, 46) if hover else (22, 22, 26)
            borda_s = BORDA_DESTAQUE if hover else CINZA_LINHO
            pygame.draw.rect(tela, fundo_s, rect_s, border_radius=3)
            pygame.draw.rect(tela, borda_s, rect_s, 2 if hover else 1, border_radius=3)

            lbl_rot = self.fonte_mini.render(rotulo, True, (130, 130, 140))
            tela.blit(lbl_rot, (rect_s.x + 6, rect_s.y + 6))

            if item_eq:
                txt_item = self.fonte_mini.render(item_eq.nome[:9], True, MARFIM_OFFWHITE)
                tela.blit(txt_item, (rect_s.centerx - txt_item.get_width() // 2, rect_s.centery + 4))
                up = getattr(item_eq, 'nivel_upgrade', 0)
                if up > 0:
                    txt_up = self.fonte_mini.render(f"+{up}", True, (230, 210, 120))
                    tela.blit(txt_up, (rect_s.right - txt_up.get_width() - 4, rect_s.bottom - txt_up.get_height() - 3))
            else:
                lbl_vazio = self.fonte_mini.render("Vazio", True, (90, 90, 100))
                tela.blit(lbl_vazio, (rect_s.centerx - lbl_vazio.get_width() // 2, rect_s.centery + 8))

        # 2. SLOTS DE GRIMÓRIOS (4 Espaços Abaixo dos Equipamentos)
        txt_gr = self.fonte_sub.render("Grimórios Despertados (4 Espaços)", True, MARFIM_OFFWHITE)
        tela.blit(txt_gr, (self.x_menu + 45, self.y_menu + 225))

        for i, rect_g in enumerate(self.slots_grimorios):
            chave_g = f"GRIMORIO_{i+1}"
            hover_g = (self.slot_hover and self.slot_hover[0] == "equipamento" and self.slot_hover[1] == chave_g)
            item_g = inv.equipados.get(chave_g) if inv else None

            fundo_g = (36, 36, 46) if hover_g else (22, 22, 26)
            borda_g = BORDA_DESTAQUE if hover_g else CINZA_LINHO
            pygame.draw.rect(tela, fundo_g, rect_g, border_radius=3)
            pygame.draw.rect(tela, borda_g, rect_g, 2 if hover_g else 1, border_radius=3)

            lbl_g_rot = self.fonte_mini.render(f"Grimório {i+1}", True, (130, 130, 140))
            tela.blit(lbl_g_rot, (rect_g.x + 6, rect_g.y + 6))

            if item_g:
                txt_item_g = self.fonte_mini.render(item_g.nome[:9], True, (240, 225, 160))
                tela.blit(txt_item_g, (rect_g.centerx - txt_item_g.get_width() // 2, rect_g.centery + 4))
            else:
                lbl_vazio_g = self.fonte_mini.render("Vazio", True, (90, 90, 100))
                tela.blit(lbl_vazio_g, (rect_g.centerx - lbl_vazio_g.get_width() // 2, rect_g.centery + 8))

        # Painel Informativo Inferior Esquerdo
        r_inst = pygame.Rect(self.x_menu + 45, self.y_menu + 375, 360, 180)
        desenhar_card_pergaminho(tela, r_inst, cor_fundo=(20, 20, 24), cor_borda=CINZA_ARDOSIA)
        tela.blit(self.fonte_mini.render("✦ GUIA RÁPIDO DE INVENTÁRIO", True, (210, 195, 140)), (r_inst.x + 16, r_inst.y + 14))
        linhas_guia = [
            "• Passe o cursor sobre itens para ler suas propriedades.",
            "• [Clique Esquerdo] Usa consumíveis ou veste equipamentos.",
            "• [Clique Direito] Remove o equipamento para a bolsa.",
            "• Os Grimórios equipados contêm feitiços ancestrais."
        ]
        y_g = r_inst.y + 42
        for lg in linhas_guia:
            tela.blit(self.fonte_mini.render(lg, True, CINZA_LINHO), (r_inst.x + 16, y_g))
            y_g += 26

        # Linha vertical separadora
        pygame.draw.line(tela, CINZA_ARDOSIA, (self.x_menu + 445, self.y_menu + 75), (self.x_menu + 445, self.y_menu + self.altura_menu - 50), 1)

        # 3. SUB-ABAS DA BOLSA (Direita)
        self.rects_sub_abas_bolsa.clear()
        sub_x = self.x_menu + 475
        sub_y = self.y_menu + 76
        altura_sub = 28

        for s_idx, nome_sub in enumerate(self.sub_abas_bolsa):
            ativa_s = (s_idx == self.sub_aba_bolsa_ativa)
            rotulo = f"✦ {nome_sub}" if ativa_s else nome_sub
            txt_s = self.fonte_abas.render(rotulo, True, MARFIM_OFFWHITE if ativa_s else CINZA_LINHO)
            largura_s = txt_s.get_width() + 18

            rect_sub = pygame.Rect(sub_x, sub_y, largura_s, altura_sub)
            self.rects_sub_abas_bolsa.append(rect_sub)

            pygame.draw.rect(tela, (36, 36, 46) if ativa_s else (20, 20, 24), rect_sub, border_radius=2)
            pygame.draw.rect(tela, MARFIM_OFFWHITE if ativa_s else CINZA_ARDOSIA, rect_sub, 1, border_radius=2)
            tela.blit(txt_s, (rect_sub.centerx - txt_s.get_width() // 2, rect_sub.centery - txt_s.get_height() // 2))
            sub_x += largura_s + 8

        # 4. GRELHA DE ITENS DA BOLSA
        cat_atual = self.mapa_sub_categorias[self.sub_aba_bolsa_ativa]
        itens_filtrados = inv.obter_itens_por_categoria(cat_atual) if inv else []

        for idx_slot, rect_g in enumerate(self.slots_gerais):
            hover_g = (self.slot_hover and self.slot_hover[0] == "bolsa" and rect_g.collidepoint(self.pos_mouse))
            fundo_g = (34, 34, 42) if hover_g else (18, 18, 22)
            borda_g = BORDA_DESTAQUE if hover_g else CINZA_ARDOSIA

            pygame.draw.rect(tela, fundo_g, rect_g, border_radius=3)
            pygame.draw.rect(tela, borda_g, rect_g, 2 if hover_g else 1, border_radius=3)

            if idx_slot < len(itens_filtrados):
                idx_real, item_slot = itens_filtrados[idx_slot]
                item = item_slot.item
                qtd = item_slot.quantidade

                nome_formatado = item.nome_formatado if hasattr(item, 'nome_formatado') else item.nome
                txt_item = self.fonte_mini.render(nome_formatado[:14] + ("..." if len(nome_formatado) > 14 else ""), True, MARFIM_OFFWHITE)
                tela.blit(txt_item, (rect_g.x + 8, rect_g.y + 10))

                cat_txt = "Grimório" if item.categoria == "GRIMORIO" else item.categoria.capitalize()
                txt_cat = self.fonte_mini.render(cat_txt[:10], True, (130, 130, 145))
                tela.blit(txt_cat, (rect_g.x + 8, rect_g.y + 36))

                if qtd > 1 or item.acumulavel:
                    txt_qtd = self.fonte_mini.render(f"x{qtd}", True, (230, 215, 150))
                    tela.blit(txt_qtd, (rect_g.right - txt_qtd.get_width() - 8, rect_g.bottom - txt_qtd.get_height() - 6))

    # =========================================================================
    # [2] ABA PERFIL
    # =========================================================================
    def _desenhar_aba_perfil(self, tela, halia):
        if not halia:
            return

        memorias = getattr(halia, 'fragmentos_memoria', 0)
        attrs_totais = halia.obter_atributos_totais()
        attrs_base = halia.atributos

        # Cabeçalho Superior: Estágio da Memória limpo
        txt_cab = self.fonte_destaque.render(f"Halia — Estágio da Memória: {memorias}", True, MARFIM_OFFWHITE)
        tela.blit(txt_cab, (self.x_menu + 45, self.y_menu + 75))

        # BLOCO 1 (Esquerda): RECURSOS E ESTATÍSTICAS
        r_bloco1 = pygame.Rect(self.x_menu + 45, self.y_menu + 110, 505, 450)
        desenhar_painel_padrao(tela, r_bloco1, cor_fundo=(20, 20, 25), cor_borda=CINZA_LINHO, border_radius=4)
        tela.blit(self.fonte_sub.render("Recursos & Capacidade de Combate", True, MARFIM_OFFWHITE), (r_bloco1.x + 20, r_bloco1.y + 16))
        pygame.draw.line(tela, CINZA_ARDOSIA, (r_bloco1.x + 20, r_bloco1.y + 46), (r_bloco1.right - 20, r_bloco1.y + 46), 1)

        # 1. Barras de Vida e Mana
        tela.blit(self.fonte_texto.render(f"Pontos de Vida (HP): {halia.vida_atual} / {halia.vida_maxima}", True, MARFIM_OFFWHITE), (r_bloco1.x + 20, r_bloco1.y + 58))
        desenhar_barra_status_interpolada(tela, r_bloco1.x + 20, r_bloco1.y + 84, halia.vida_atual, halia.vida_maxima, BARRA_VIDA_JOGADOR, largura=465, altura=14)

        tela.blit(self.fonte_texto.render(f"Reserva de Mana (MP): {halia.mana_atual} / {halia.mana_maxima}", True, MARFIM_OFFWHITE), (r_bloco1.x + 20, r_bloco1.y + 112))
        desenhar_barra_status_interpolada(tela, r_bloco1.x + 20, r_bloco1.y + 138, halia.mana_atual, halia.mana_maxima, BARRA_MANA, largura=465, altura=14)

        # 2. Carteira Decomposta
        pygame.draw.line(tela, CINZA_ARDOSIA, (r_bloco1.x + 20, r_bloco1.y + 170), (r_bloco1.right - 20, r_bloco1.y + 170), 1)
        tela.blit(self.fonte_mini.render("CARTEIRA (20 Cobre = 1 Prata | 10 Prata = 1 Ouro)", True, (210, 195, 140)), (r_bloco1.x + 20, r_bloco1.y + 180))

        str_moedas = f"🪙 {halia.moedas_ouro} Ouro   |   🥈 {halia.moedas_prata} Prata   |   🥉 {halia.moedas_cobre} Cobre"
        tela.blit(self.fonte_destaque.render(str_moedas, True, MARFIM_OFFWHITE), (r_bloco1.x + 20, r_bloco1.y + 206))

        # 3. Parâmetros de Combate
        pygame.draw.line(tela, CINZA_ARDOSIA, (r_bloco1.x + 20, r_bloco1.y + 242), (r_bloco1.right - 20, r_bloco1.y + 242), 1)
        tela.blit(self.fonte_mini.render("PARÂMETROS DE COMBATE", True, (210, 195, 140)), (r_bloco1.x + 20, r_bloco1.y + 252))

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
            tela.blit(self.fonte_texto.render(rotulo_sc, True, CINZA_LINHO), (r_bloco1.x + 24, y_sc))
            tela.blit(self.fonte_destaque.render(valor_sc, True, MARFIM_OFFWHITE), (r_bloco1.right - 100, y_sc - 2))
            y_sc += 30

        # BLOCO 2 (Direita): OS 6 ATRIBUTOS
        r_bloco2 = pygame.Rect(self.x_menu + 570, self.y_menu + 110, 505, 450)
        desenhar_painel_padrao(tela, r_bloco2, cor_fundo=(20, 20, 25), cor_borda=CINZA_LINHO, border_radius=4)
        tela.blit(self.fonte_sub.render("Atributos Primários (D20 Core)", True, MARFIM_OFFWHITE), (r_bloco2.x + 20, r_bloco2.y + 16))
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

            txt_sig = self.fonte_destaque.render(sigla, True, (230, 215, 140))
            tela.blit(txt_sig, (r_card_a.x + 14, r_card_a.y + 16))

            txt_nm = self.fonte_texto.render(nome_a, True, MARFIM_OFFWHITE)
            tela.blit(txt_nm, (r_card_a.x + 65, r_card_a.y + 18))

            bonus = v_total - v_base
            str_b = f"(Base {v_base} + Eq {bonus})" if bonus > 0 else f"(Base {v_base})"
            tela.blit(self.fonte_mini.render(str_b, True, (140, 140, 155)), (r_card_a.x + 190, r_card_a.y + 20))

            mod = (v_total - 10) // 2
            mod_str = f"+{mod}" if mod >= 0 else f"{mod}"
            cor_mod = (140, 230, 170) if mod >= 0 else (240, 130, 130)
            
            txt_tot = self.fonte_destaque.render(f"{v_total}", True, MARFIM_OFFWHITE)
            tela.blit(txt_tot, (r_card_a.right - 120, r_card_a.y + 16))

            txt_mod = self.fonte_destaque.render(f"[{mod_str}]", True, cor_mod)
            tela.blit(txt_mod, (r_card_a.right - 65, r_card_a.y + 16))

            y_attr_card += 62

    # =========================================================================
    # [3] ABA MAGIA (2 Colunas com Scroll)
    # =========================================================================
    def _desenhar_aba_magia(self, tela, halia):
        flashback_concluido = getattr(self.game, 'flashback_magia_concluido', False) or (halia and halia.fragmentos_memoria > 0)

        if not flashback_concluido:
            r_selo = pygame.Rect(self.x_menu + 180, self.y_menu + 110, self.largura_menu - 360, 420)
            desenhar_card_pergaminho(tela, r_selo, cor_fundo=(18, 18, 22), cor_borda=(70, 70, 85))

            desenhar_flor_botanica(tela, r_selo.centerx, r_selo.y + 80, cor=(90, 90, 110), escala=1.5)

            txt_selo_tit = self.fonte_destaque.render("✦ Conhecimento Arcano Selado ✦", True, (220, 205, 150))
            tela.blit(txt_selo_tit, (r_selo.centerx - txt_selo_tit.get_width() // 2, r_selo.y + 160))

            linhas_selo = [
                "Os feitiços arcanos e os mistérios ancestrais de Halia repousam em silêncio.",
                "As páginas do Grimório ainda aguardam o despertar da memória arcana.",
                "Investigue os obstáculos da estrada para reconectar-se com sua essência mágica."
            ]

            y_s = r_selo.y + 215
            for ls in linhas_selo:
                txt_ls = self.fonte_texto.render(ls, True, CINZA_LINHO)
                tela.blit(txt_ls, (r_selo.centerx - txt_ls.get_width() // 2, y_s))
                y_s += 30
            return

        # CATÁLOGO DE MAGIAS DESBLOQUEADAS EM 2 COLUNAS
        magias_ids = getattr(halia, 'magias_desbloqueadas', ["bola_de_fogo", "levitar", "brisa_curativa"])
        if not magias_ids:
            magias_ids = ["bola_de_fogo", "levitar", "brisa_curativa"]

        if self.magia_selecionada_idx >= len(magias_ids):
            self.magia_selecionada_idx = 0

        w_lista = 390
        h_coluna = 465
        x_lista = self.x_menu + 45
        y_coluna = self.y_menu + 85

        r_painel_lista = pygame.Rect(x_lista, y_coluna, w_lista, h_coluna)
        desenhar_painel_padrao(tela, r_painel_lista, cor_fundo=(20, 20, 25), cor_borda=CINZA_LINHO, border_radius=4)
        
        tela.blit(self.fonte_sub.render(f"Grimório ({len(magias_ids)} Despertadas)", True, MARFIM_OFFWHITE), (x_lista + 18, y_coluna + 14))
        pygame.draw.line(tela, CINZA_ARDOSIA, (x_lista + 18, y_coluna + 42), (x_lista + w_lista - 18, y_coluna + 42), 1)

        y_itens_inicio = y_coluna + 50
        h_viewport = h_coluna - 60
        r_viewport = pygame.Rect(x_lista + 10, y_itens_inicio, w_lista - 20, h_viewport)
        
        antigo_clip = tela.get_clip()
        tela.set_clip(r_viewport)

        self.rects_lista_magias.clear()
        h_card_m = 76
        espacamento_m = 8
        altura_total_lista = len(magias_ids) * (h_card_m + espacamento_m)
        max_scroll = max(0, altura_total_lista - h_viewport)
        self.scroll_magias = max(0, min(self.scroll_magias, max_scroll))

        for idx_m, id_magia in enumerate(magias_ids):
            acao = ActionCatalog.get(id_magia)
            nome = acao.nome if acao else id_magia.replace("_", " ").title()
            custo = acao.custo_mana if acao else 0
            elemento = acao.elemento if acao else "ARCANO"

            pos_y_card = y_itens_inicio + (idx_m * (h_card_m + espacamento_m)) - self.scroll_magias
            r_card_item = pygame.Rect(x_lista + 14, pos_y_card, w_lista - 38, h_card_m)
            self.rects_lista_magias.append(r_card_item)

            esta_selecionada = (idx_m == self.magia_selecionada_idx)
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
                borda_c = CINZA_ARDOSIA

            pygame.draw.rect(tela, fundo_c, r_card_item, border_radius=3)
            pygame.draw.rect(tela, borda_c, r_card_item, 2 if esta_selecionada else 1, border_radius=3)

            if esta_selecionada:
                pygame.draw.rect(tela, (230, 215, 140), (r_card_item.x + 3, r_card_item.y + 6, 4, r_card_item.height - 12), border_radius=2)

            cor_nome = (245, 230, 165) if esta_selecionada else MARFIM_OFFWHITE
            txt_nm = self.fonte_destaque.render(f"✦ {nome}", True, cor_nome)
            tela.blit(txt_nm, (r_card_item.x + 16, r_card_item.y + 12))

            txt_elem = self.fonte_mini.render(f"{elemento.capitalize()}", True, (140, 190, 240))
            tela.blit(txt_elem, (r_card_item.x + 16, r_card_item.y + 42))

            txt_custo = self.fonte_mini.render(f"{custo} MP", True, (160, 240, 180))
            tela.blit(txt_custo, (r_card_item.right - txt_custo.get_width() - 14, r_card_item.y + 42))

        tela.set_clip(antigo_clip)

        if max_scroll > 0:
            trilho_x = x_lista + w_lista - 14
            trilho_y = y_itens_inicio
            trilho_h = h_viewport
            pygame.draw.rect(tela, (18, 18, 22), (trilho_x, trilho_y, 5, trilho_h), border_radius=2)

            tamanho_thumb = max(24, int((h_viewport / altura_total_lista) * trilho_h))
            thumb_y = trilho_y + int((self.scroll_magias / max_scroll) * (trilho_h - tamanho_thumb))
            pygame.draw.rect(tela, (160, 160, 180), (trilho_x, thumb_y, 5, tamanho_thumb), border_radius=2)

        # COLUNA DIREITA: DETALHES COMPLETOS
        w_detalhes = 620
        x_detalhes = self.x_menu + 465
        r_painel_det = pygame.Rect(x_detalhes, y_coluna, w_detalhes, h_coluna)
        desenhar_painel_padrao(tela, r_painel_det, cor_fundo=(20, 20, 25), cor_borda=CINZA_LINHO, border_radius=4)

        id_selecionada = magias_ids[self.magia_selecionada_idx]
        acao_sel = ActionCatalog.get(id_selecionada)
        nome_sel = acao_sel.nome if acao_sel else id_selecionada.replace("_", " ").title()
        custo_sel = acao_sel.custo_mana if acao_sel else 0
        elem_sel = acao_sel.elemento if acao_sel else "ARCANO"
        desc_sel = acao_sel.descricao if acao_sel else "Feitiço ancestral canalizado através da vontade mágica de Halia."
        tipo_acao = acao_sel.tipo if acao_sel else "OFENSIVA"

        txt_tit_det = self.fonte_sub.render(nome_sel, True, (245, 230, 165))
        tela.blit(txt_tit_det, (x_detalhes + 24, y_coluna + 16))
        desenhar_flor_botanica(tela, x_detalhes + txt_tit_det.get_width() + 45, y_coluna + 26, cor=(210, 195, 140), escala=0.55)

        pygame.draw.line(tela, CINZA_ARDOSIA, (x_detalhes + 24, y_coluna + 46), (x_detalhes + w_detalhes - 24, y_coluna + 46), 1)

        badges = [
            ("Elemento", elem_sel.capitalize(), (140, 190, 240)),
            ("Custo", f"{custo_sel} MP", (160, 240, 180)),
            ("Categoria", tipo_acao.capitalize(), (230, 210, 140))
        ]
        x_badge = x_detalhes + 24
        y_badge = y_coluna + 58
        for rotulo_b, valor_b, cor_v in badges:
            txt_b = self.fonte_mini.render(f"{rotulo_b}: {valor_b}", True, cor_v)
            r_b = pygame.Rect(x_badge, y_badge, txt_b.get_width() + 18, 26)
            pygame.draw.rect(tela, (26, 26, 34), r_b, border_radius=3)
            pygame.draw.rect(tela, CINZA_ARDOSIA, r_b, 1, border_radius=3)
            tela.blit(txt_b, (r_b.centerx - txt_b.get_width() // 2, r_b.centery - txt_b.get_height() // 2))
            x_badge += r_b.width + 12

        attrs_tot = halia.obter_atributos_totais() if halia else None
        mod_int = attrs_tot.mod_int if attrs_tot else 0
        dano_base = getattr(acao_sel, 'poder_base', 12) if acao_sel else 12
        dano_estimado = dano_base + (mod_int * 2)

        pygame.draw.line(tela, CINZA_ARDOSIA, (x_detalhes + 24, y_coluna + 100), (x_detalhes + w_detalhes - 24, y_coluna + 100), 1)

        r_card_poder = pygame.Rect(x_detalhes + 24, y_coluna + 112, w_detalhes - 48, 56)
        pygame.draw.rect(tela, (24, 24, 30), r_card_poder, border_radius=3)
        pygame.draw.rect(tela, CINZA_ARDOSIA, r_card_poder, 1, border_radius=3)

        tela.blit(self.fonte_mini.render("ESCALAMENTO ARCANO (INTELECTO)", True, (210, 195, 140)), (r_card_poder.x + 14, r_card_poder.y + 10))
        str_poder = f"Potência Estimada: ~{dano_estimado} pts (Base {dano_base} + Mod INT x2: +{mod_int*2})"
        tela.blit(self.fonte_destaque.render(str_poder, True, MARFIM_OFFWHITE), (r_card_poder.x + 14, r_card_poder.y + 28))

        tela.blit(self.fonte_mini.render("DESCRIÇÃO DO FEITIÇO", True, (210, 195, 140)), (x_detalhes + 24, y_coluna + 184))
        linhas_desc = quebrar_texto_em_linhas(desc_sel, self.fonte_texto, w_detalhes - 54)
        y_txt_d = y_coluna + 208
        for ld in linhas_desc:
            tela.blit(self.fonte_texto.render(ld, True, MARFIM_OFFWHITE), (x_detalhes + 24, y_txt_d))
            y_txt_d += 22

        r_ref = pygame.Rect(x_detalhes + 24, y_coluna + 310, w_detalhes - 48, 130)
        desenhar_card_pergaminho(tela, r_ref, cor_fundo=(22, 22, 26), cor_borda=CINZA_ARDOSIA)
        tela.blit(self.fonte_mini.render("✦ NOTA DE CANALIZAÇÃO", True, (220, 205, 140)), (r_ref.x + 16, r_ref.y + 12))
        
        reflexoes = {
            "bola_de_fogo": "A chama incinera obstáculos e abre caminhos obstruídos por galhos secos e vinhas do esquecimento.",
            "levitar": "A gravidade dobra-se à mente, permitindo erguer rochas colossais e afastar perigos sem confronto direto.",
            "brisa_curativa": "Um sopro vital restaurador que dissipa a fadiga física e acalma as feridas sofridas em combate."
        }
        nota_texto = reflexoes.get(id_selecionada, "Feitiço gravado nas memórias ancestrais da ordem dos guardiões arcanos.")
        linhas_ref = quebrar_texto_em_linhas(nota_texto, self.fonte_texto, w_detalhes - 85)
        y_tr = r_ref.y + 36
        for lr in linhas_ref:
            tela.blit(self.fonte_texto.render(lr, True, CINZA_LINHO), (r_ref.x + 16, y_tr))
            y_tr += 22

    # =========================================================================
    # [4] ABA CRAFTING (Bloqueada)
    # =========================================================================
    def _desenhar_aba_crafting(self, tela, halia):
        r_selo = pygame.Rect(self.x_menu + 180, self.y_menu + 110, self.largura_menu - 360, 420)
        desenhar_card_pergaminho(tela, r_selo, cor_fundo=(18, 18, 22), cor_borda=(70, 70, 85))

        desenhar_flor_botanica(tela, r_selo.centerx, r_selo.y + 80, cor=(100, 100, 125), escala=1.5)

        txt_selo_tit = self.fonte_destaque.render("✦ Bancada de Criação & Alquimia Selada ✦", True, (220, 205, 150))
        tela.blit(txt_selo_tit, (r_selo.centerx - txt_selo_tit.get_width() // 2, r_selo.y + 160))

        linhas_selo = [
            "A confecção de itens, transmutação e refinamento de equipamentos exigem uma bancada apropriada.",
            "Explore o mundo de Oblivium e descubra receitas ancestrais para desbloquear suas criações.",
            "Encontre bancadas de alquimia ou forjas arcanas pelo mapa para manipular reagentes."
        ]

        y_s = r_selo.y + 215
        for ls in linhas_selo:
            txt_ls = self.fonte_texto.render(ls, True, CINZA_LINHO)
            tela.blit(txt_ls, (r_selo.centerx - txt_ls.get_width() // 2, y_s))
            y_s += 30

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