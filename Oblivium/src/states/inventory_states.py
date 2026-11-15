# src/states/inventory_states.py
import pygame
from src.states.states import State
from src.utils.colors import (
    CARVAO_PROFUNDO, CINZA_ARDOSIA, CINZA_LINHO,
    MARFIM_OFFWHITE, BOTAO_FECHAR_HOVER,
    AZUL_HOVER_MENU, BRANCO, DOURADO_ENVELHECIDO
)
from src.utils.resource_manager import ResourceManager
from src.ui.ui_utils import (
    desenhar_painel_padrao, desenhar_flor_botanica,
    desenhar_icone_fechar, desenhar_estrela_quatro_pontas,
    quebrar_texto_em_linhas
)
from src.mechanics.items import ConsumivelItem, EquipamentoItem, GrimorioItem, EnsinamentoFeiticoItem
from src.mechanics.rpg.grimorio import GrimorioHalia
from src.states.inventory_tabs import (
    TabInventarioRenderer,
    TabPerfilRenderer,
    TabMagiaRenderer,
    TabCraftingRenderer
)

class InventoryState(State):
    """
    Menu de inventário, perfil, magia e bancada selada.
    Inventário reúne equipamentos, quatro grimórios, bolsa e tooltips.
    Perfil apresenta recursos, atributos, parâmetros de combate e carteira.
    Magia oferece lista navegável e detalhes do feitiço selecionado.
    Crafting informa a necessidade de uma bancada apropriada no mundo.
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
        self.rect_fechar = pygame.Rect(self.x_menu + self.largura_menu - 54, self.y_menu + 20, 28, 28)
        self.hover_fechar = False
        
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

        # A bancada permanece selada nesta tela.
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

    def _consumir_item_da_bolsa(self, inv, halia, item, sfx_sucesso, on_sucesso=None, idx_slot=None):
        """Remove uma unidade da bolsa antes do uso e estorna se a aplicação falhar."""
        if not inv or not inv.tem_item(item.id, 1) or not inv.remover_item(item.id, 1):
            self._tocar_sfx("ui_erro")
            self.exibir_mensagem("Aviso: Item indisponível na bolsa.")
            return False
        res = item.usar(halia, em_combate=False)
        if res.get("sucesso"):
            if on_sucesso:
                on_sucesso()
            halia.recalcular_status_derivados(manter_porcentagem=False)
            self._tocar_sfx(sfx_sucesso)
            self.exibir_mensagem(f"• {res['mensagem']}")
            return True
        inv.estornar_item(item, idx_preferido=idx_slot)
        self._tocar_sfx("ui_erro")
        self.exibir_mensagem(f"Aviso: {res.get('mensagem', 'Não foi possível usar este item.')}")
        return False

    def exibir_mensagem(self, texto, duracao_ticks=150):
        """Exibe notificação na barra inferior do menu."""
        self.mensagem_feedback = texto
        self.timer_feedback = duracao_ticks

    def ao_entrar(self, estado_anterior=None):
        """Sonoriza apenas a abertura pelo mundo ou pelo menu de pausa."""
        if estado_anterior in ("JOGANDO", "PAUSE"):
            self._tocar_sfx("livro_abrir")

    def ao_sair(self, proximo_estado=None):
        """Não sonoriza descarte de estado, carregamento ou reinicialização."""
        if proximo_estado == "JOGANDO":
            self._tocar_sfx("ui_voltar")

    def _selecionar_aba(self, indice):
        if indice != self.aba_principal_ativa:
            self.aba_principal_ativa = indice
            self.slot_hover = None
            self.tooltip_info = None
            self._tocar_sfx("pagina_virar")

    def _obter_magias(self, halia):
        return getattr(halia, 'magias_desbloqueadas', None) or ["bola_de_fogo", "levitar"]

    def _grimorio_desbloqueado(self, halia):
        if halia and hasattr(halia, "tem_grimorio_desbloqueado"):
            return halia.tem_grimorio_desbloqueado()
        return getattr(self.game, 'flashback_magia_concluido', False) or (halia and halia.fragmentos_memoria > 0)

    def _viewport_magias(self):
        # Mesma área recortada por TabMagiaRenderer.
        return pygame.Rect(self.x_menu + 55, self.y_menu + 135, 370, 405)

    def _selecionar_magia(self, indice, halia):
        ultimo_indice = len(self._obter_magias(halia)) - 1
        indice = max(0, min(indice, ultimo_indice))
        if indice != self.magia_selecionada_idx:
            self.magia_selecionada_idx = indice
            self._ajustar_scroll_magia()
            self._tocar_sfx("ui_cursor")

    def _rolar_magias(self, deslocamento, halia):
        max_scroll = max(0, len(self._obter_magias(halia)) * 84 - self._viewport_magias().height)
        novo_scroll = max(0, min(self.scroll_magias + deslocamento, max_scroll))
        if novo_scroll == self.scroll_magias:
            return
        self.scroll_magias = novo_scroll
        audio = getattr(self.game, "audio", None)
        if audio:
            if hasattr(audio, "tocar_sfx_com_cooldown"):
                audio.tocar_sfx_com_cooldown("ui_cursor", cooldown_s=0.10, volume_extra=0.35)
            else:
                self._tocar_sfx("ui_cursor")

    def _slot_na_posicao(self, posicao, inv):
        """Resolve hover e clique sobre os mesmos slots do inventário atual."""
        if self.aba_principal_ativa != 0:
            return None
        slots = [
            (self.slot_roupa, "ROUPA"), (self.slot_cajado, "CAJADO"),
            (self.slot_acess1, "ACESSORIO_1"), (self.slot_acess2, "ACESSORIO_2"),
        ]
        slots.extend((rect, f"GRIMORIO_{i+1}") for i, rect in enumerate(self.slots_grimorios))
        for rect, nome in slots:
            if rect.collidepoint(posicao):
                return ("equipamento", nome)
        if inv:
            itens = inv.obter_itens_por_categoria(self.mapa_sub_categorias[self.sub_aba_bolsa_ativa])
            for indice, rect in enumerate(self.slots_gerais):
                if rect.collidepoint(posicao):
                    if indice < len(itens):
                        indice_real, item_slot = itens[indice]
                        return ("bolsa", indice_real, item_slot)
                    break
        return None

    def _tooltip_do_slot(self, slot, inv):
        if not slot:
            return None
        if slot[0] == "bolsa":
            item_slot = slot[2]
            return self._gerar_tooltip_item(item_slot.item, item_slot.quantidade)
        nome = slot[1]
        item = inv.equipados.get(nome) if inv else None
        if item:
            return self._gerar_tooltip_item(item)
        if nome.startswith("GRIMORIO_"):
            return (f"Grimório {nome.rsplit('_', 1)[1]}", "Espaço para tomos arcanos e livros de feitiços.", "Vazio")
        padroes = {
            "ROUPA": ("Slot de Roupa", "Espaço para mantos e túnicas arcanas."),
            "CAJADO": ("Slot de Cajado", "Espaço para foco arcano e cajados mágicos."),
            "ACESSORIO_1": ("Acessório I", "Espaço para anéis, medalhões e relíquias."),
            "ACESSORIO_2": ("Acessório II", "Espaço para anéis, medalhões e relíquias."),
        }
        return (*padroes[nome], "Vazio")

    def handle_events(self, eventos, teclas):
        self.pos_mouse = pygame.mouse.get_pos()
        self.hover_fechar = self.rect_fechar.collidepoint(self.pos_mouse)
        halia = getattr(self.game, 'halia', None)
        inv = getattr(halia, 'inventario', None) if halia else None
        self.slot_hover = self._slot_na_posicao(self.pos_mouse, inv)
        self.tooltip_info = self._tooltip_do_slot(self.slot_hover, inv)

        # Processamento de Teclado e Mouse
        for evento in eventos:
            if evento.type == pygame.KEYDOWN:
                tecla_inv = self.game.controles.get("Inventário", pygame.K_TAB)
                if evento.key in [pygame.K_ESCAPE, tecla_inv]:
                    self.game.mudar_estado("JOGANDO")
                    return

                flashback_ok = self._grimorio_desbloqueado(halia)

                # Atalhos de Abas Principais (1: Inventário, 2: Perfil, 3: Magia, 4: Crafting)
                if evento.key == pygame.K_1:
                    self._selecionar_aba(0)
                    return
                elif evento.key == pygame.K_2:
                    self._selecionar_aba(1)
                    return
                elif evento.key == pygame.K_3:
                    self._selecionar_aba(2)
                    return
                elif evento.key == pygame.K_4:
                    self._selecionar_aba(3)
                    return
                
                # Alternar abas com Q / E
                elif evento.key == pygame.K_q:
                    self._selecionar_aba((self.aba_principal_ativa - 1) % len(self.abas_principais))
                    return
                elif evento.key == pygame.K_e:
                    self._selecionar_aba((self.aba_principal_ativa + 1) % len(self.abas_principais))
                    return

                # Navegação vertical na lista de magias
                elif self.aba_principal_ativa == 2 and flashback_ok:
                    if evento.key == pygame.K_UP:
                        self._selecionar_magia(self.magia_selecionada_idx - 1, halia)
                    elif evento.key == pygame.K_DOWN:
                        self._selecionar_magia(self.magia_selecionada_idx + 1, halia)

                # Navegação e Atalhos na Aba Crafting
                elif self.aba_principal_ativa == 3:
                    if evento.key in [pygame.K_RETURN, pygame.K_SPACE]:
                        self._executar_crafting_selecionado(halia)
                        return

            elif evento.type == pygame.MOUSEWHEEL:
                flashback_ok = self._grimorio_desbloqueado(halia)
                if self.aba_principal_ativa == 2 and flashback_ok:
                    self._rolar_magias(-(evento.y * 36), halia)

            elif evento.type == pygame.MOUSEBUTTONDOWN:
                slot_clicado = self._slot_na_posicao(evento.pos, inv)
                if evento.button == 1:  # Clique Esquerdo
                    if self.rect_fechar.collidepoint(evento.pos):
                        self.game.mudar_estado("JOGANDO")
                        return

                    flashback_ok = self._grimorio_desbloqueado(halia)
                    
                    # Clique nas Abas Principais
                    for i, r_aba in enumerate(self.rects_abas_principais):
                        if r_aba.collidepoint(evento.pos):
                            self._selecionar_aba(i)
                            return

                    # Interações na Aba Magia (Seleção por clique)
                    if self.aba_principal_ativa == 2 and flashback_ok:
                        for idx_m, r_m in enumerate(self.rects_lista_magias):
                            if r_m.collidepoint(evento.pos) and self._viewport_magias().collidepoint(evento.pos):
                                self._selecionar_magia(idx_m, halia)
                                return

                    # Interações na Aba Crafting (Seleção e Botão Fabricar)
                    if self.aba_principal_ativa == 3:
                        if self.rect_botao_fabricar and self.rect_botao_fabricar.collidepoint(evento.pos):
                            self._executar_crafting_selecionado(halia)
                            return

                    # Sub-abas da Bolsa no Inventário
                    if self.aba_principal_ativa == 0:
                        for s_idx, r_sub in enumerate(self.rects_sub_abas_bolsa):
                            if r_sub.collidepoint(evento.pos):
                                if s_idx != self.sub_aba_bolsa_ativa:
                                    self.sub_aba_bolsa_ativa = s_idx
                                    self.slot_hover = None
                                    self.tooltip_info = None
                                    self._tocar_sfx("ui_cursor")
                                return

                        # Usar / Equipar Item da Bolsa
                        if slot_clicado and slot_clicado[0] == "bolsa" and inv:
                            idx_real = slot_clicado[1]
                            item_slot = slot_clicado[2]
                            item = item_slot.item

                            if isinstance(item, ConsumivelItem):
                                self._consumir_item_da_bolsa(inv, halia, item, "item_pocao", idx_slot=idx_real)

                            elif isinstance(item, EnsinamentoFeiticoItem) or getattr(item, 'categoria', '') == "ENSINAMENTO":
                                self._consumir_item_da_bolsa(
                                    inv, halia, item, "pagina_virar", on_sucesso=halia.atualizar_grimorio, idx_slot=idx_real
                                )

                            elif isinstance(item, EquipamentoItem):
                                slot_destino = item.slot
                                if "ACESSORIO" in slot_destino:
                                    slot_destino = "ACESSORIO_1" if inv.equipados["ACESSORIO_1"] is None else "ACESSORIO_2"

                                sucesso, msg = inv.equipar(slot_destino, idx_real)
                                if sucesso:
                                    halia.recalcular_status_derivados(manter_porcentagem=False)
                                    self._tocar_sfx("desembainhar" if slot_destino == "CAJADO" else "equipar_armadura")
                                    self.exibir_mensagem(f"• {msg}")
                                else:
                                    self._tocar_sfx("ui_erro")
                                    self.exibir_mensagem(f"Aviso: {msg}")

                            elif isinstance(item, GrimorioItem) or getattr(item, 'categoria', '') == "GRIMORIO":
                                pode_tomo, motivo_tomo = item.pode_usar(halia, em_combate=False)
                                if not pode_tomo:
                                    self._tocar_sfx("ui_trancado")
                                    self.exibir_mensagem(f"Aviso: {motivo_tomo}")
                                else:
                                    slot_g = next(
                                        (g_k for g_k in ["GRIMORIO_1", "GRIMORIO_2", "GRIMORIO_3", "GRIMORIO_4"] if inv.equipados[g_k] is None),
                                        "GRIMORIO_1",
                                    )
                                    sucesso, msg = inv.equipar(slot_g, idx_real)
                                    if sucesso:
                                        halia.atualizar_grimorio()
                                        halia.recalcular_status_derivados(manter_porcentagem=False)
                                        self._tocar_sfx("livro_abrir")
                                        self.exibir_mensagem(f"• {msg}")
                                    else:
                                        self._tocar_sfx("ui_erro")
                                        self.exibir_mensagem(f"Aviso: {msg}")
                            self.slot_hover = None
                            self.tooltip_info = None
                            return

                elif evento.button == 3:  # Clique Direito (Desequipar)
                    if self.aba_principal_ativa == 0 and slot_clicado and slot_clicado[0] == "equipamento" and inv:
                        slot_nome = slot_clicado[1]
                        if inv.equipados.get(slot_nome):
                            sucesso, msg = inv.desequipar(slot_nome)
                            if sucesso:
                                halia.recalcular_status_derivados(manter_porcentagem=False)
                                halia.atualizar_grimorio()
                                self._tocar_sfx("toggle_off")
                                self.exibir_mensagem(f"• {msg}")
                            else:
                                self._tocar_sfx("ui_erro")
                                self.exibir_mensagem(f"Aviso: {msg}")
                            self.slot_hover = None
                            self.tooltip_info = None
                            return

    def _ajustar_scroll_magia(self):
        """Garante que a magia selecionada permaneça visível no viewport com scroll."""
        h_card = 84
        y_selecionado = self.magia_selecionada_idx * h_card
        viewport_h = self._viewport_magias().height
        if y_selecionado < self.scroll_magias:
            self.scroll_magias = y_selecionado
        elif y_selecionado + 76 > self.scroll_magias + viewport_h:
            self.scroll_magias = y_selecionado + 76 - viewport_h
        halia = getattr(self.game, 'halia', None)
        max_scroll = max(0, len(self._obter_magias(halia)) * h_card - viewport_h)
        self.scroll_magias = max(0, min(self.scroll_magias, max_scroll))

    def _executar_crafting_selecionado(self, halia):
        """A aba selada não oferece fabricação fora de uma bancada."""
        self._tocar_sfx("ui_trancado")
        self.exibir_mensagem("Aviso: A fabricação exige uma bancada apropriada.")

    def _gerar_tooltip_item(self, item, quantidade=None):
        """Gera título, descrição e detalhes ricos e estruturados para o tooltip flutuante."""
        nome = item.nome_formatado if hasattr(item, 'nome_formatado') else item.nome
        if quantidade and quantidade > 1:
            nome = f"{nome} (x{quantidade})"
        linhas_detalhes = []
        cat = "Grimório" if item.categoria == "GRIMORIO" else item.categoria.capitalize()
        linhas_detalhes.append(f"Tipo: {cat}  |  Raridade: {item.raridade}")
        halia = getattr(self.game, 'halia', None) or getattr(self.game, 'jogador', None)
        inv = getattr(halia, 'inventario', None) if halia else None
        if isinstance(item, ConsumivelItem):
            if item.tipo_consumivel == "CURA_HP":
                linhas_detalhes.append(f"• Efeito: Restaura +{item.valor_efeito} Pontos de Vida (HP)")
            elif item.tipo_consumivel == "RESTAURA_MP":
                linhas_detalhes.append(f"• Efeito: Restaura +{item.valor_efeito} Pontos de Mana (MP)")
            elif item.tipo_consumivel == "DANO_OFENSIVO":
                linhas_detalhes.append(f"• Efeito: Causa {item.valor_efeito} de dano ofensivo")
                if getattr(item, 'condicao_aplicada', None):
                    linhas_detalhes.append(f"  + Aplica: {item.condicao_aplicada.capitalize()}")
            elif item.tipo_consumivel == "CURA_CONDICAO":
                linhas_detalhes.append("• Efeito: Purifica aflições, venenos e queimaduras")
            linhas_detalhes.append("• [Clique Esquerdo] Usar consumível")
        elif isinstance(item, EquipamentoItem):
            up = getattr(item, 'nivel_upgrade', 0)
            refino_txt = f"+ {up}/5" if up > 0 else "Padrão (+0)"
            linhas_detalhes.append(f"Slot: {item.slot}  |  Refino: {refino_txt}")
            if hasattr(item, 'obter_bonus_atributos_efetivos'):
                for attr, val in item.obter_bonus_atributos_efetivos().items():
                    if val != 0:
                        linhas_detalhes.append(f"  + {attr.capitalize()}: +{val}")
            nome_map = {
                "poder_magico": "Poder Mágico",
                "defesa_fisica": "Defesa Física",
                "defesa_magica": "Defesa Mágica",
                "vida_maxima_bonus": "Vida Máxima",
                "mana_maxima_bonus": "Mana Máxima",
                "dano_fogo_bonus": "Dano de Fogo",
                "dano_gelo_bonus": "Dano de Gelo",
                "cura_bonus": "Bônus de Cura"
            }
            if hasattr(item, 'obter_bonus_stats_efetivos'):
                for stat, val in item.obter_bonus_stats_efetivos().items():
                    if val != 0:
                        label = nome_map.get(stat, stat.replace('_', ' ').title())
                        sufixo = "%" if "bonus" in stat and "maxima" not in stat else " pts"
                        linhas_detalhes.append(f"  + {label}: +{val}{sufixo}")
            linhas_detalhes.append("• [Clique] Equipar no slot correspondente")
        elif isinstance(item, (EnsinamentoFeiticoItem, GrimorioItem)) or getattr(item, 'categoria', '') in ("ENSINAMENTO", "GRIMORIO"):
            eh_grimorio = isinstance(item, GrimorioItem) or getattr(item, 'categoria', '') == "GRIMORIO"
            st = GrimorioHalia.obter_status_aquisicao_item(item, halia) or {}
            magia_id = st.get("magia_id") or getattr(item, 'magia_id', 'arcano')
            magia_nome = st.get("nome_magia") or magia_id.replace('_', ' ').title()
            conhece = st.get("ja_conhece", False)
            pode_usar = st.get("pode_usar", True)
            req_txt = st.get("requisito_texto", "")
            bonus_p, red_c = getattr(item, 'bonus_poder', 0), getattr(item, 'reducao_custo', 0)

            if not eh_grimorio:
                if not conhece:
                    linhas_detalhes.append(f"• Feitiço: ✦ {magia_nome} [NOVO]")
                else:
                    lvl = getattr(halia, 'maestria_feiticos', {}).get(magia_id, {}).get('nivel_maestria', 1)
                    linhas_detalhes.append(f"• Feitiço: ✦ {magia_nome} [APRIMORAR: Nv.{lvl} → Nv.{lvl+1}]")
                if req_txt:
                    linhas_detalhes.append(f"• {req_txt}")
                if bonus_p > 0:
                    linhas_detalhes.append(f"  + Potência Arcana: +{bonus_p} pts")
                if red_c > 0:
                    linhas_detalhes.append(f"  + Eficiência de Mana: -{red_c} MP")
                linhas_detalhes.append(f"  + Experiência de Estudo: +{getattr(item, 'xp_concedida', 35)} XP")
                linhas_detalhes.append(f"• Bloqueado: {st.get('motivo_bloqueio')}" if not pode_usar else "• [Clique Esquerdo] Estudar e assimilar ensinamento")
            else:
                linhas_detalhes.append(f"• Feitiço Vinculado: ✦ {magia_nome}")
                slot_eq = next(
                    (g for g in ['GRIMORIO_1', 'GRIMORIO_2', 'GRIMORIO_3', 'GRIMORIO_4']
                     if inv and (inv.equipados.get(g) == item or (inv.equipados.get(g) and inv.equipados.get(g).id == item.id))),
                    None,
                )
                linhas_detalhes.append(f"• Estado: [EQUIPADO no Slot {slot_eq.replace('GRIMORIO_', '')} - BÔNUS ATIVOS]" if slot_eq else "• Estado: [Na Bolsa - Não Equipado]")
                if req_txt and not slot_eq:
                    linhas_detalhes.append(f"• {req_txt}")
                if bonus_p > 0:
                    linhas_detalhes.append(f"  + Potência Mágica: +{bonus_p} pts")
                if red_c > 0:
                    linhas_detalhes.append(f"  + Redução de Custo: -{red_c} MP")
                rot_stat = {'dano_fogo_bonus': 'Ressonância de Fogo', 'dano_gelo_bonus': 'Ressonância Glacial', 'cura_bonus': 'Ressonância Vital'}
                for stat_k, val_k in (getattr(item, 'bonus_stats', None) or {}).items():
                    suf_k = "%" if stat_k in rot_stat else ""
                    linhas_detalhes.append(f"  + {rot_stat.get(stat_k, stat_k.replace('_', ' ').title())}: +{val_k}{suf_k}")
                if halia and magia_id in getattr(halia, 'maestria_feiticos', {}):
                    m_h = halia.maestria_feiticos[magia_id]
                    linhas_detalhes.append(f"• Maestria de Halia: Nv. {m_h.get('nivel_maestria', 1)} (+{m_h.get('bonus_poder', 0)} Pod, -{m_h.get('reducao_custo', 0)} MP)")
                if slot_eq:
                    linhas_detalhes.append("• [Clique Direito no Slot] Desequipar para a bolsa")
                elif not pode_usar:
                    linhas_detalhes.append(f"• Bloqueado: {st.get('motivo_bloqueio')}")
                else:
                    linhas_detalhes.append("• [Clique Esquerdo] Equipar nos 4 Slots de Grimório")
        detalhes_str = "\n".join(linhas_detalhes)
        return (nome, item.descricao, detalhes_str)

    def _tocar_sfx(self, alias):
        if getattr(self.game, "audio", None):
            self.game.audio.tocar_sfx(alias)

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
        """Renderiza os botões superiores das 4 abas principais e o botão fechar [X]."""
        self.rects_abas_principais.clear()
        txt_nome = self.fonte_titulo.render("Halia", True, MARFIM_OFFWHITE)
        tela.blit(txt_nome, (self.x_menu + 35, self.y_menu + 20))
        desenhar_flor_botanica(tela, self.x_menu + 120, self.y_menu + 32, cor=CINZA_LINHO, escala=0.65)

        x_aba = self.x_menu + 250
        y_aba = self.y_menu + 18
        largura_btn = 152
        altura_btn = 34

        for i, nome_aba in enumerate(self.abas_principais):
            ativa = (i == self.aba_principal_ativa)
            rect_btn = pygame.Rect(x_aba, y_aba, largura_btn, altura_btn)
            self.rects_abas_principais.append(rect_btn)

            label = f"[{i+1}] {nome_aba}"
            if ativa:
                fundo = (38, 38, 48)
                cor_borda = MARFIM_OFFWHITE
                cor_texto = MARFIM_OFFWHITE
            else:
                fundo = (22, 22, 28)
                cor_borda = CINZA_ARDOSIA
                cor_texto = CINZA_LINHO

            pygame.draw.rect(tela, fundo, rect_btn, border_radius=3)
            pygame.draw.rect(tela, cor_borda, rect_btn, 2 if ativa else 1, border_radius=3)

            txt_btn = self.fonte_abas_principais.render(label, True, cor_texto)
            if ativa:
                pygame.draw.line(tela, (230, 215, 160), (rect_btn.left + 6, rect_btn.bottom - 2), (rect_btn.right - 6, rect_btn.bottom - 2), 2)
                tx = rect_btn.centerx - txt_btn.get_width() // 2 + 6
                desenhar_estrela_quatro_pontas(tela, tx - 11, rect_btn.centery, 4, 1, DOURADO_ENVELHECIDO)
                tela.blit(txt_btn, (tx, rect_btn.centery - txt_btn.get_height() // 2))
            else:
                tela.blit(txt_btn, (rect_btn.centerx - txt_btn.get_width() // 2, rect_btn.centery - txt_btn.get_height() // 2))
            x_aba += largura_btn + 12

        # Botão Fechar [ X ] no topo direito
        self.rect_fechar = pygame.Rect(self.x_menu + self.largura_menu - 54, self.y_menu + 20, 28, 28)
        cor_bg_f = BOTAO_FECHAR_HOVER if self.hover_fechar else (26, 26, 32)
        cor_bd_f = AZUL_HOVER_MENU if self.hover_fechar else CINZA_ARDOSIA
        pygame.draw.rect(tela, cor_bg_f, self.rect_fechar, border_radius=3)
        pygame.draw.rect(tela, cor_bd_f, self.rect_fechar, 1, border_radius=3)
        desenhar_icone_fechar(tela, self.rect_fechar, cor=BRANCO if self.hover_fechar else CINZA_LINHO, espessura=2)

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
        w_tit_est = self.fonte_destaque.size(titulo)[0]
        largura_max = max(340, min(430, w_tit_est + 36))

        # Trunca título se ainda assim ultrapassar a largura máxima
        titulo_render = titulo
        if self.fonte_destaque.size(titulo_render)[0] > (largura_max - 28):
            while len(titulo_render) > 3 and self.fonte_destaque.size(f"{titulo_render}...")[0] > (largura_max - 28):
                titulo_render = titulo_render[:-1]
            titulo_render = f"{titulo_render}..."

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
        txt_t = self.fonte_destaque.render(titulo_render, True, (240, 225, 160))
        tela.blit(txt_t, (r_tool.x + 14, r_tool.y + 10))
        pygame.draw.line(tela, CINZA_ARDOSIA, (r_tool.x + 14, r_tool.y + 32), (r_tool.right - 14, r_tool.y + 32), 1)

        # Linhas de Texto
        y_txt = r_tool.y + 40
        for l in linhas_desc:
            eh_alerta = ("Bloqueado" in l or "Requer " in l or "Aviso:" in l)
            cor_l = (245, 165, 130) if eh_alerta else ((150, 220, 170) if "+" in l else ((140, 190, 240) if "•" in l else MARFIM_OFFWHITE))
            txt_l = self.fonte_mini.render(l, True, cor_l)
            tela.blit(txt_l, (r_tool.x + 14, y_txt))
            y_txt += 18

    # =========================================================================
    # RODAPÉ
    # =========================================================================
    def _desenhar_rodape(self, tela):
        y_rodape = self.y_menu + self.altura_menu - 36
        if self.mensagem_feedback:
            cor_fb = (245, 185, 120) if self.mensagem_feedback.startswith("Aviso:") else (150, 240, 180)
            txt_f = self.fonte_destaque.render(self.mensagem_feedback, True, cor_fb)
            tela.blit(txt_f, (self.x_menu + 45, y_rodape))
        else:
            txt_guia = self.fonte_mini.render("[1/2/3/4/Q/E] Trocar Abas   |   [Clique Esq] Usar / Equipar / Criar   |   [Clique Dir] Desequipar   |   [ESC/TAB] Fechar", True, CINZA_LINHO)
            tela.blit(txt_guia, (self.x_menu + 45, y_rodape))
