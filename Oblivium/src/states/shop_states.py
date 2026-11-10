# src/states/shop_states.py
import pygame
from src.states.states import State
from src.utils.colors import (
    CARVAO_PROFUNDO, CINZA_ARDOSIA, CINZA_LINHO,
    MARFIM_OFFWHITE, BORDA_DESTAQUE, BOTAO_FECHAR_HOVER,
    AZUL_HOVER_MENU, BRANCO
)
from src.utils.resource_manager import ResourceManager
from src.ui.ui_utils import (
    desenhar_painel_padrao, desenhar_flor_botanica,
    desenhar_card_pergaminho, quebrar_texto_em_linhas
)
from src.ui.icon_registry import (
    IconRegistry, desenhar_icone_fechar, desenhar_icone_moeda
)
from src.mechanics.shop import Loja
from src.mechanics.items import ConsumivelItem, EquipamentoItem, ItemChave


class ShopState(State):
    """
    Interface da Loja Mercantil alinhada à estética Dark Fantasy / Editorial de Oblivium:
    - Fundo escuro em Carvão Profundo com bordas duplas em Cinza Linho
    - Suporte a múltiplas lojas declarativas via JSON (Curandeira Elara, Ferreiro Torvald, Empório Itinerante)
    - Abas: Comprar (Mercadorias do mercador) e Vender (Itens da Bolsa de Halia)
    - Painel esquerdo: Grelha/Lista de Itens com Preços em Ouro e Estoque disponível
    - Painel direito: Detalhes completos do item inspecionado (nome, ícone, raridade, tipo, descrição, efeitos, bônus)
    - Botão explícito de Ação [ COMPRAR ] / [ VENDER ] com confirmação deliberada:
      * Clicar no item da lista APENAS seleciona e inspeciona o item.
      * A compra ou venda só ocorre quando o jogador clica deliberadamente no botão de confirmação ou tecla ENTER.
    """

    def __init__(self, game):
        super().__init__(game)
        self.overlay = pygame.Surface((self.game.LARGURA, self.game.ALTURA))
        self.overlay.fill((10, 10, 12))
        self.overlay.set_alpha(215)

        # Tipografia Editorial
        self.fonte_titulo = ResourceManager.carregar_fonte("sunday", 28)
        self.fonte_sub = ResourceManager.carregar_fonte("sunday", 20)
        self.fonte_abas = ResourceManager.carregar_fonte("contrail", 18)
        self.fonte_texto = ResourceManager.carregar_fonte("contrail", 15)
        self.fonte_mini = ResourceManager.carregar_fonte("contrail", 13)
        self.fonte_poetica = ResourceManager.carregar_fonte("just_breathe", 18)

        # Loja ativa (inicia com Empório do Viajante, configurável dinamicamente)
        self.loja = Loja.obter_ou_criar("emporio_viajante")

        # Abas
        self.abas = ["Comprar", "Vender"]
        self.aba_ativa = 0  # 0: Comprar, 1: Vender
        self.rects_abas = []

        # Dimensões do Painel Central
        self.largura_loja = min(1060, self.game.LARGURA - 60)
        self.altura_loja = min(620, self.game.ALTURA - 60)
        self.x_loja = (self.game.LARGURA - self.largura_loja) // 2
        self.y_loja = (self.game.ALTURA - self.altura_loja) // 2
        self.rect_fechar = pygame.Rect(self.x_loja + self.largura_loja - 52, self.y_loja + 22, 28, 28)
        self.hover_fechar = False

        # Botão de Ação Deliberada (Comprar / Vender no card direito)
        self.rect_botao_acao = None
        self.hover_botao_acao = False

        # Seleção e Navegação
        self.indice_selecionado = 0
        self.pos_mouse = (0, 0)
        self.rects_itens_lista = []
        self.offset_scroll = 0

        # Feedback e Notificações
        self.mensagem_feedback = ""
        self.timer_feedback = 0

    def configurar_loja(self, loja_id=None):
        """Alterna a loja ativa carregando seus dados do catálogo persistente de lojas.json."""
        self.loja = Loja.obter_ou_criar(loja_id or "emporio_viajante")
        self.indice_selecionado = 0
        self.offset_scroll = 0
        self.aba_ativa = 0
        self.mensagem_feedback = ""
        self.timer_feedback = 0
        self.teve_transacao = False

    def _fechar_loja(self):
        """Fecha a interface da loja e persiste compras/vendas em autosave caso tenha havido transações."""
        if hasattr(self.game, 'audio') and self.game.audio:
            self.game.audio.tocar_sfx("ui_confirmar")
        if getattr(self, 'teve_transacao', False):
            if self.game and getattr(self.game, 'slot_atual', None):
                self.game.salvar_estado(self.game.slot_atual, tipo="autosave", silenciar_notificacao=True)
            self.teve_transacao = False
        self.game.mudar_estado("JOGANDO")

    def exibir_mensagem(self, texto, duracao_ticks=150):
        self.mensagem_feedback = texto
        self.timer_feedback = duracao_ticks

    def handle_events(self, eventos, teclas):
        self.pos_mouse = pygame.mouse.get_pos()
        self.hover_fechar = self.rect_fechar.collidepoint(self.pos_mouse)
        if self.rect_botao_acao:
            self.hover_botao_acao = self.rect_botao_acao.collidepoint(self.pos_mouse)
        else:
            self.hover_botao_acao = False

        halia = getattr(self.game, 'halia', None)
        inv = getattr(halia, 'inventario', None) if halia else None

        # Lista de itens dependendo da aba
        if self.aba_ativa == 0:
            itens_atuais = self.loja.obter_lista_mercadorias()
        else:
            itens_atuais = inv.slots if inv else []

        for evento in eventos:
            if evento.type == pygame.KEYDOWN:
                if evento.key in [pygame.K_ESCAPE, pygame.K_e]:
                    self._fechar_loja()
                    return
                elif evento.key == pygame.K_TAB or evento.key in [pygame.K_1, pygame.K_2]:
                    self.aba_ativa = 1 - self.aba_ativa
                    self.indice_selecionado = 0
                    self.offset_scroll = 0
                    if hasattr(self.game, 'audio') and self.game.audio:
                        self.game.audio.tocar_sfx("ui_navegar")
                elif evento.key in [pygame.K_UP, pygame.K_w]:
                    if len(itens_atuais) > 0:
                        self.indice_selecionado = (self.indice_selecionado - 1) % len(itens_atuais)
                        self._ajustar_scroll(len(itens_atuais))
                        if hasattr(self.game, 'audio') and self.game.audio:
                            self.game.audio.tocar_sfx("ui_navegar")
                elif evento.key in [pygame.K_DOWN, pygame.K_s]:
                    if len(itens_atuais) > 0:
                        self.indice_selecionado = (self.indice_selecionado + 1) % len(itens_atuais)
                        self._ajustar_scroll(len(itens_atuais))
                        if hasattr(self.game, 'audio') and self.game.audio:
                            self.game.audio.tocar_sfx("ui_navegar")
                elif evento.key in [pygame.K_RETURN, pygame.K_SPACE]:
                    # Atalho de teclado para acionar a confirmação do item inspecionado
                    self._executar_transacao(self.indice_selecionado)

            elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                if self.rect_fechar.collidepoint(evento.pos):
                    self._fechar_loja()
                    return

                # Clique nas abas
                for i, rect_aba in enumerate(self.rects_abas):
                    if rect_aba.collidepoint(evento.pos):
                        if self.aba_ativa != i:
                            self.aba_ativa = i
                            self.indice_selecionado = 0
                            self.offset_scroll = 0
                            if hasattr(self.game, 'audio') and self.game.audio:
                                self.game.audio.tocar_sfx("ui_navegar")
                        return

                # Clique no BOTÃO DE AÇÃO DELIBERADA [ COMPRAR ] / [ VENDER ]
                if self.rect_botao_acao and self.rect_botao_acao.collidepoint(evento.pos):
                    self._executar_transacao(self.indice_selecionado)
                    return

                # Clique na lista de itens: APENAS SELECIONA E INSPECIONA O ITEM!
                for idx_item, rect_item in self.rects_itens_lista:
                    if rect_item.collidepoint(evento.pos):
                        if self.indice_selecionado != idx_item:
                            self.indice_selecionado = idx_item
                            if hasattr(self.game, 'audio') and self.game.audio:
                                self.game.audio.tocar_sfx("ui_navegar")
                        return

            elif evento.type == pygame.MOUSEWHEEL:
                if len(itens_atuais) > 9:
                    self.offset_scroll = max(0, min(len(itens_atuais) - 9, self.offset_scroll - evento.y))

    def _ajustar_scroll(self, total_itens, max_visiveis=9):
        """Mantém o item selecionado visível dentro da janela de rolagem da lista."""
        if total_itens <= max_visiveis:
            self.offset_scroll = 0
            return
        if self.indice_selecionado < self.offset_scroll:
            self.offset_scroll = self.indice_selecionado
        elif self.indice_selecionado >= self.offset_scroll + max_visiveis:
            self.offset_scroll = self.indice_selecionado - max_visiveis + 1

    def _executar_transacao(self, indice):
        halia = getattr(self.game, 'halia', None)
        inv = getattr(halia, 'inventario', None) if halia else None
        if not halia or not inv:
            return

        if self.aba_ativa == 0:
            # Comprar
            mercadorias = self.loja.obter_lista_mercadorias()
            if 0 <= indice < len(mercadorias):
                merc = mercadorias[indice]
                sucesso, msg = self.loja.comprar_item(merc.item_id, 1, halia)
                if sucesso:
                    self.teve_transacao = True
                    self.exibir_mensagem(msg)
                    if hasattr(self.game, 'audio') and self.game.audio:
                        self.game.audio.tocar_sfx("item_coletar")
                else:
                    self.exibir_mensagem(f"Aviso: {msg}")
                    if hasattr(self.game, 'audio') and self.game.audio:
                        self.game.audio.tocar_sfx("ui_confirmar")
        else:
            # Vender
            if 0 <= indice < len(inv.slots):
                slot = inv.slots[indice]
                sucesso, msg = self.loja.vender_item(slot.item.id, 1, halia)
                if sucesso:
                    self.teve_transacao = True
                    self.exibir_mensagem(msg)
                    if hasattr(self.game, 'audio') and self.game.audio:
                        self.game.audio.tocar_sfx("item_coletar")
                    if self.indice_selecionado >= len(inv.slots):
                        self.indice_selecionado = max(0, len(inv.slots) - 1)
                else:
                    self.exibir_mensagem(f"Aviso: {msg}")
                    if hasattr(self.game, 'audio') and self.game.audio:
                        self.game.audio.tocar_sfx("ui_confirmar")

    def update(self):
        if self.timer_feedback > 0:
            self.timer_feedback -= 1
            if self.timer_feedback == 0:
                self.mensagem_feedback = ""

    def draw(self, tela):
        # 1. Renderiza o jogo de fundo
        if "JOGANDO" in self.game.estados:
            self.game.estados["JOGANDO"].draw(tela)

        # 2. Película escura
        tela.blit(self.overlay, (0, 0))

        # 3. Painel Principal
        rect_painel = pygame.Rect(self.x_loja, self.y_loja, self.largura_loja, self.altura_loja)
        desenhar_painel_padrao(tela, rect_painel, cor_fundo=CARVAO_PROFUNDO, cor_borda=CINZA_LINHO, alpha=245)

        # Moldura interna
        rect_interno = rect_painel.inflate(-10, -10)
        pygame.draw.rect(tela, (30, 30, 36), rect_interno, 1, border_radius=2)

        # 4. Cabeçalho e Título da Loja
        txt_titulo = self.fonte_titulo.render(self.loja.nome, True, MARFIM_OFFWHITE)
        tela.blit(txt_titulo, (self.x_loja + 35, self.y_loja + 18))

        tipo_cor = (130, 220, 160) if self.loja.tipo == "ALQUIMIA" else ((240, 180, 100) if self.loja.tipo == "FERRARIA" else CINZA_LINHO)
        txt_tipo = self.fonte_mini.render(f"Especialidade: {self.loja.tipo}  |  {self.loja.descricao}", True, tipo_cor)
        tela.blit(txt_tipo, (self.x_loja + 36, self.y_loja + 48))

        desenhar_flor_botanica(tela, self.x_loja + self.largura_loja - 90, self.y_loja + 36, cor=CINZA_LINHO, escala=0.7)

        # Botão Fechar [ X ] no topo direito
        self.rect_fechar = pygame.Rect(self.x_loja + self.largura_loja - 52, self.y_loja + 20, 28, 28)
        cor_bg_f = BOTAO_FECHAR_HOVER if self.hover_fechar else (26, 26, 32)
        cor_bd_f = AZUL_HOVER_MENU if self.hover_fechar else CINZA_ARDOSIA
        pygame.draw.rect(tela, cor_bg_f, self.rect_fechar, border_radius=3)
        pygame.draw.rect(tela, cor_bd_f, self.rect_fechar, 1, border_radius=3)
        desenhar_icone_fechar(tela, self.rect_fechar, cor=BRANCO if self.hover_fechar else CINZA_LINHO, espessura=2)

        # 5. Abas (Comprar / Vender)
        self.rects_abas.clear()
        x_aba = self.x_loja + 520
        y_aba = self.y_loja + 22

        for i, nome_aba in enumerate(self.abas):
            esta_ativa = (i == self.aba_ativa)
            r_aba_txt = self.fonte_abas.render(f"[{i+1}] {nome_aba}", True, MARFIM_OFFWHITE if esta_ativa else CINZA_LINHO)
            w_aba = r_aba_txt.get_width() + 20
            h_aba = 28
            rect_aba = pygame.Rect(x_aba, y_aba, w_aba, h_aba)
            self.rects_abas.append(rect_aba)

            if esta_ativa:
                pygame.draw.rect(tela, (38, 38, 48), rect_aba, border_radius=2)
                pygame.draw.rect(tela, CINZA_LINHO, rect_aba, 1, border_radius=2)
                pygame.draw.line(tela, MARFIM_OFFWHITE, (rect_aba.left + 4, rect_aba.bottom - 2), (rect_aba.right - 4, rect_aba.bottom - 2), 2)

            tela.blit(r_aba_txt, (rect_aba.centerx - r_aba_txt.get_width() // 2, rect_aba.centery - r_aba_txt.get_height() // 2))
            x_aba += w_aba + 8

        # Linha separadora do cabeçalho
        pygame.draw.line(tela, CINZA_ARDOSIA, (self.x_loja + 30, self.y_loja + 72), (self.x_loja + self.largura_loja - 30, self.y_loja + 72), 1)

        # 6. SEÇÃO ESQUERDA: LISTA DE MERCADORIAS / ITENS DA BOLSA
        halia = getattr(self.game, 'halia', None)
        inv = getattr(halia, 'inventario', None) if halia else None
        dinheiro = getattr(halia, 'dinheiro', 0) if halia else 0

        self.rects_itens_lista.clear()
        w_item_card = 480
        h_item_card = 42
        x_inicio_lista = self.x_loja + 35
        y_inicio_lista = self.y_loja + 85

        if self.aba_ativa == 0:
            # Lista de Mercadorias para Compra
            itens_exibir = self.loja.obter_lista_mercadorias()
            txt_secao = self.fonte_sub.render(f"Mercadorias Disponíveis ({len(itens_exibir)})", True, MARFIM_OFFWHITE)
            tela.blit(txt_secao, (x_inicio_lista, y_inicio_lista))

            y_pos = y_inicio_lista + 32
            visiveis = itens_exibir[self.offset_scroll:self.offset_scroll + 9]
            for pos_rel, merc in enumerate(visiveis):
                i = self.offset_scroll + pos_rel
                rect_card = pygame.Rect(x_inicio_lista, y_pos, w_item_card, h_item_card)
                self.rects_itens_lista.append((i, rect_card))

                esta_sel = (i == self.indice_selecionado)
                esta_hover = rect_card.collidepoint(self.pos_mouse)
                fundo_c = (42, 42, 56) if esta_sel else ((32, 32, 40) if esta_hover else (22, 22, 26))
                borda_c = BORDA_DESTAQUE if esta_sel else (CINZA_LINHO if esta_hover else (45, 45, 52))

                pygame.draw.rect(tela, fundo_c, rect_card, border_radius=2)
                pygame.draw.rect(tela, borda_c, rect_card, 1, border_radius=2)

                nome_it = merc.item_template.nome if merc.item_template else merc.item_id
                marcador = "▶ " if esta_sel else "   "
                txt_it = self.fonte_texto.render(f"{marcador}{nome_it}", True, MARFIM_OFFWHITE if esta_sel else CINZA_LINHO)
                tela.blit(txt_it, (rect_card.x + 8, rect_card.centery - txt_it.get_height() // 2))

                # Preço e Estoque
                info_preco = f"{merc.preco_compra} Ouro | Est: {merc.estoque_atual}"
                cor_preco = (240, 220, 130) if merc.disponivel else (120, 120, 120)
                txt_pr = self.fonte_mini.render(info_preco, True, cor_preco)
                tela.blit(txt_pr, (rect_card.right - txt_pr.get_width() - 10, rect_card.centery - txt_pr.get_height() // 2))

                y_pos += h_item_card + 6

        else:
            # Lista de Itens da Halia para Venda
            itens_exibir = inv.slots if inv else []
            txt_secao = self.fonte_sub.render(f"Sua Bolsa — Itens para Vender ({len(itens_exibir)})", True, MARFIM_OFFWHITE)
            tela.blit(txt_secao, (x_inicio_lista, y_inicio_lista))

            y_pos = y_inicio_lista + 32
            visiveis = itens_exibir[self.offset_scroll:self.offset_scroll + 9]
            for pos_rel, slot in enumerate(visiveis):
                i = self.offset_scroll + pos_rel
                rect_card = pygame.Rect(x_inicio_lista, y_pos, w_item_card, h_item_card)
                self.rects_itens_lista.append((i, rect_card))

                esta_sel = (i == self.indice_selecionado)
                esta_hover = rect_card.collidepoint(self.pos_mouse)
                fundo_c = (42, 42, 56) if esta_sel else ((32, 32, 40) if esta_hover else (22, 22, 26))
                borda_c = BORDA_DESTAQUE if esta_sel else (CINZA_LINHO if esta_hover else (45, 45, 52))

                pygame.draw.rect(tela, fundo_c, rect_card, border_radius=2)
                pygame.draw.rect(tela, borda_c, rect_card, 1, border_radius=2)

                item = slot.item
                nome_formatado = item.nome_formatado if hasattr(item, 'nome_formatado') else item.nome
                marcador = "▶ " if esta_sel else "   "
                txt_it = self.fonte_texto.render(f"{marcador}{nome_formatado} x{slot.quantidade}", True, MARFIM_OFFWHITE if esta_sel else CINZA_LINHO)
                tela.blit(txt_it, (rect_card.x + 8, rect_card.centery - txt_it.get_height() // 2))

                # Preço de Venda
                preco_venda = item.preco_venda
                cor_v = (160, 220, 160) if preco_venda > 0 else (120, 120, 120)
                txt_pr = self.fonte_mini.render(f"+{preco_venda} Ouro/un", True, cor_v)
                tela.blit(txt_pr, (rect_card.right - txt_pr.get_width() - 10, rect_card.centery - txt_pr.get_height() // 2))

                y_pos += h_item_card + 6

        # Linha vertical divisória
        pygame.draw.line(tela, CINZA_ARDOSIA, (self.x_loja + 540, self.y_loja + 80), (self.x_loja + 540, self.y_loja + self.altura_loja - 55), 1)

        # 7. SEÇÃO DIREITA: DETALHES DO ITEM E CARTEIRA
        x_det = self.x_loja + 565
        y_det = self.y_loja + 85
        w_det = self.largura_loja - 600

        # Carteira do Jogador com Sprite da Bolsa de Moedas
        rect_carteira = pygame.Rect(x_det, y_det, w_det, 45)
        desenhar_card_pergaminho(tela, rect_carteira, cor_fundo=(26, 26, 32), cor_borda=CINZA_LINHO)
        sprite_bolsa_ouro = ResourceManager.carregar_imagem("props/Bolsa de Moedas.png", (26, 26))
        if sprite_bolsa_ouro:
            tela.blit(sprite_bolsa_ouro, (rect_carteira.x + 12, rect_carteira.centery - 13))
        else:
            desenhar_icone_moeda(tela, rect_carteira.x + 22, rect_carteira.centery, tipo="OURO", raio=9)
        txt_ouro = self.fonte_sub.render(f"Suas Moedas: {dinheiro} Ouro", True, (240, 220, 130))
        tela.blit(txt_ouro, (rect_carteira.x + 44, rect_carteira.centery - txt_ouro.get_height() // 2))

        # Detalhes do item selecionado
        y_card_det = y_det + 55
        h_card_det = self.altura_loja - 200
        rect_det_card = pygame.Rect(x_det, y_card_det, w_det, h_card_det)
        desenhar_card_pergaminho(tela, rect_det_card, cor_fundo=(22, 22, 26), cor_borda=CINZA_LINHO)

        item_selecionado = None
        merc_selecionada = None
        slot_selecionado = None

        if self.aba_ativa == 0:
            mercs = self.loja.obter_lista_mercadorias()
            if 0 <= self.indice_selecionado < len(mercs):
                merc_selecionada = mercs[self.indice_selecionado]
                item_selecionado = merc_selecionada.item_template
        else:
            if inv and 0 <= self.indice_selecionado < len(inv.slots):
                slot_selecionado = inv.slots[self.indice_selecionado]
                item_selecionado = slot_selecionado.item

        self.rect_botao_acao = None

        if item_selecionado:
            # Sprite do item selecionado
            sprite_sel = IconRegistry.obter_sprite_item(item_selecionado, (42, 42))
            if sprite_sel:
                rect_ico_det = pygame.Rect(rect_det_card.right - 64, rect_det_card.y + 12, 48, 48)
                pygame.draw.rect(tela, (16, 16, 20), rect_ico_det, border_radius=3)
                pygame.draw.rect(tela, CINZA_ARDOSIA, rect_ico_det, 1, border_radius=3)
                tela.blit(sprite_sel, sprite_sel.get_rect(center=rect_ico_det.center))

            nome_f = item_selecionado.nome_formatado if hasattr(item_selecionado, 'nome_formatado') else item_selecionado.nome
            txt_n = self.fonte_sub.render(nome_f, True, MARFIM_OFFWHITE)
            tela.blit(txt_n, (rect_det_card.x + 16, rect_det_card.y + 16))

            txt_cat = self.fonte_mini.render(f"Tipo: {item_selecionado.categoria}  |  Raridade: {item_selecionado.raridade}", True, CINZA_LINHO)
            tela.blit(txt_cat, (rect_det_card.x + 16, rect_det_card.y + 44))

            pygame.draw.line(tela, CINZA_ARDOSIA, (rect_det_card.x + 14, rect_det_card.y + 68), (rect_det_card.right - 14, rect_det_card.y + 68), 1)

            # Descrição do Item
            linhas_desc = quebrar_texto_em_linhas(item_selecionado.descricao, self.fonte_texto, w_det - 32)
            y_linha = rect_det_card.y + 78
            for l in linhas_desc:
                r_l = self.fonte_texto.render(l, True, (210, 210, 215))
                tela.blit(r_l, (rect_det_card.x + 16, y_linha))
                y_linha += 20

            # Bônus ou Efeitos
            y_linha += 8
            if isinstance(item_selecionado, ConsumivelItem):
                if item_selecionado.tipo_consumivel == "CURA_HP":
                    tela.blit(self.fonte_mini.render(f"• Regenera: +{item_selecionado.valor_efeito} Pontos de Vida (HP)", True, (140, 220, 160)), (rect_det_card.x + 16, y_linha))
                elif item_selecionado.tipo_consumivel == "RESTAURA_MP":
                    tela.blit(self.fonte_mini.render(f"• Restaura: +{item_selecionado.valor_efeito} Pontos de Mana (MP)", True, (130, 190, 240)), (rect_det_card.x + 16, y_linha))
                elif item_selecionado.tipo_consumivel == "DANO_OFENSIVO":
                    tela.blit(self.fonte_mini.render(f"• Causa: {item_selecionado.valor_efeito} de dano ({item_selecionado.condicao_aplicada or 'fogo'})", True, (240, 140, 140)), (rect_det_card.x + 16, y_linha))
                elif item_selecionado.tipo_consumivel == "CURA_CONDICAO":
                    tela.blit(self.fonte_mini.render("• Purifica: Remove todas as aflições e venenos", True, (160, 230, 200)), (rect_det_card.x + 16, y_linha))

            elif isinstance(item_selecionado, EquipamentoItem):
                tela.blit(self.fonte_mini.render(f"• Slot de Equipamento: {item_selecionado.slot}", True, (220, 210, 150)), (rect_det_card.x + 16, y_linha))
                y_linha += 18
                for attr, val in item_selecionado.obter_bonus_atributos_efetivos().items():
                    tela.blit(self.fonte_mini.render(f"  + {attr.capitalize()}: +{val}", True, MARFIM_OFFWHITE), (rect_det_card.x + 16, y_linha))
                    y_linha += 18
                for stat, val in item_selecionado.obter_bonus_stats_efetivos().items():
                    tela.blit(self.fonte_mini.render(f"  + {stat.replace('_', ' ').title()}: +{val}", True, MARFIM_OFFWHITE), (rect_det_card.x + 16, y_linha))
                    y_linha += 18

            # =================================================================
            # BOTÃO EXPLÍCITO DE AÇÃO DELIBERADA [ COMPRAR ] / [ VENDER ]
            # =================================================================
            rect_btn = pygame.Rect(rect_det_card.x + 16, rect_det_card.bottom - 46, w_det - 32, 34)
            self.rect_botao_acao = rect_btn
            esta_hover_btn = rect_btn.collidepoint(self.pos_mouse)

            if self.aba_ativa == 0 and merc_selecionada:
                preco_compra = merc_selecionada.preco_compra
                tem_estoque = merc_selecionada.disponivel
                tem_moedas = (dinheiro >= preco_compra)

                if tem_estoque and tem_moedas:
                    bg_btn = (56, 50, 28) if esta_hover_btn else (42, 38, 22)
                    bd_btn = (245, 215, 120) if esta_hover_btn else BORDA_DESTAQUE
                    txt_btn_str = f"✦ COMPRAR 1x  —  {preco_compra} Ouro"
                    cor_txt = MARFIM_OFFWHITE
                elif not tem_estoque:
                    bg_btn = (26, 26, 30)
                    bd_btn = (60, 60, 68)
                    txt_btn_str = "ESTOQUE ESGOTADO"
                    cor_txt = (120, 120, 130)
                else:
                    bg_btn = (46, 26, 26)
                    bd_btn = (140, 60, 60)
                    txt_btn_str = f"OURO INSUFICIENTE  ({preco_compra} Ouro)"
                    cor_txt = (220, 130, 130)

            elif self.aba_ativa == 1 and slot_selecionado:
                preco_venda = item_selecionado.preco_venda
                pode_vender = (not isinstance(item_selecionado, ItemChave) and preco_venda > 0)

                if pode_vender:
                    bg_btn = (28, 48, 36) if esta_hover_btn else (22, 38, 28)
                    bd_btn = (130, 220, 160) if esta_hover_btn else (80, 160, 110)
                    txt_btn_str = f"✦ VENDER 1x  —  +{preco_venda} Ouro"
                    cor_txt = MARFIM_OFFWHITE
                else:
                    bg_btn = (26, 26, 30)
                    bd_btn = (60, 60, 68)
                    txt_btn_str = "ITEM NÃO VENDÁVEL"
                    cor_txt = (120, 120, 130)
            else:
                bg_btn = (26, 26, 30)
                bd_btn = (60, 60, 68)
                txt_btn_str = "SELECIONE UM ITEM"
                cor_txt = (120, 120, 130)

            pygame.draw.rect(tela, bg_btn, rect_btn, border_radius=3)
            pygame.draw.rect(tela, bd_btn, rect_btn, 1, border_radius=3)
            r_txt_btn = self.fonte_texto.render(txt_btn_str, True, cor_txt)
            tela.blit(r_txt_btn, (rect_btn.centerx - r_txt_btn.get_width() // 2, rect_btn.centery - r_txt_btn.get_height() // 2))

        else:
            txt_vazio = self.fonte_mini.render("Nenhum item selecionado para inspeção.", True, CINZA_LINHO)
            tela.blit(txt_vazio, (rect_det_card.centerx - txt_vazio.get_width() // 2, rect_det_card.centery - 10))

        # 8. RODAPÉ INFORMATIVO E FEEDBACK
        if self.mensagem_feedback:
            txt_feed = self.fonte_texto.render(self.mensagem_feedback, True, (160, 230, 180))
            tela.blit(txt_feed, (self.x_loja + 45, self.y_loja + self.altura_loja - 36))
        else:
            txt_dica = self.fonte_mini.render("[Clique / Setas] Selecionar e Inspecionar Item   |   [Botão de Ação / ENTER] Confirmar   |   [ESC/E] Sair", True, CINZA_LINHO)
            tela.blit(txt_dica, (self.x_loja + 45, self.y_loja + self.altura_loja - 36))
