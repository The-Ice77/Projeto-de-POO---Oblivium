# src/states/shop_states.py
import pygame
from src.states.states import State
from src.utils.colors import (
    PRETO, BRANCO, CARVAO_PROFUNDO, CINZA_ARDOSIA, CINZA_LINHO, CINZA_CLARO,
    MARFIM_OFFWHITE, UI_TEXTO_DESTAQUE, UI_TEXTO_APAGADO, BORDA_PADRAO, BORDA_DESTAQUE,
    PERGAMINHO_BG, PERGAMINHO_BORDA, PERGAMINHO_TINTA, BARRA_VIDA_JOGADOR
)
from src.utils.resource_manager import ResourceManager
from src.ui.ui_utils import (
    desenhar_painel_padrao, desenhar_tooltip_formatado, desenhar_flor_botanica,
    desenhar_card_pergaminho
)
from src.mechanics.shop import Loja
from src.mechanics.items import ConsumivelItem, EquipamentoItem, ItemChave

class ShopState(State):
    """
    Interface da Loja Mercantil alinhada à estética Dark Fantasy / Editorial:
    - Fundo escuro em Carvão Profundo com bordas duplas em Cinza Linho
    - Abas: Comprar (Mercadorias) e Vender (Itens da Bolsa de Halia)
    - Painel esquerdo: Grelha de Itens com Preços em Moedas de Ouro e Estoque
    - Painel direito: Detalhes do item selecionado, bônus e confirmação de compra/venda
    - Atalhos de Teclado e navegação total por Mouse
    """
    def __init__(self, game):
        super().__init__(game)
        self.overlay = pygame.Surface((self.game.LARGURA, self.game.ALTURA))
        self.overlay.fill((10, 10, 12))
        self.overlay.set_alpha(215)
        
        # Tipografia Editorial
        self.fonte_titulo = ResourceManager.carregar_fonte("sunday", 32)
        self.fonte_sub = ResourceManager.carregar_fonte("sunday", 20)
        self.fonte_abas = ResourceManager.carregar_fonte("contrail", 18)
        self.fonte_texto = ResourceManager.carregar_fonte("contrail", 15)
        self.fonte_mini = ResourceManager.carregar_fonte("contrail", 13)
        self.fonte_poetica = ResourceManager.carregar_fonte("just_breathe", 18)
        
        # Instância padrão da Loja
        self.loja = Loja(nome="Empório do Viajante", tipo="GERAL")
        
        # Abas
        self.abas = ["Comprar", "Vender"]
        self.aba_ativa = 0 # 0: Comprar, 1: Vender
        self.rects_abas = []
        
        # Dimensões do Painel Central
        self.largura_loja = min(1060, self.game.LARGURA - 60)
        self.altura_loja = min(620, self.game.ALTURA - 60)
        self.x_loja = (self.game.LARGURA - self.largura_loja) // 2
        self.y_loja = (self.game.ALTURA - self.altura_loja) // 2
        
        # Seleção e Hover
        self.indice_selecionado = 0
        self.pos_mouse = (0, 0)
        self.rects_itens_lista = []
        
        # Feedback e Notificações
        self.mensagem_feedback = ""
        self.timer_feedback = 0

    def exibir_mensagem(self, texto, duracao_ticks=120):
        self.mensagem_feedback = texto
        self.timer_feedback = duracao_ticks

    def handle_events(self, eventos, teclas):
        self.pos_mouse = pygame.mouse.get_pos()
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
                    self.game.mudar_estado("JOGANDO")
                    return
                elif evento.key == pygame.K_TAB or evento.key in [pygame.K_1, pygame.K_2]:
                    self.aba_ativa = 1 - self.aba_ativa
                    self.indice_selecionado = 0
                elif evento.key in [pygame.K_UP, pygame.K_w]:
                    if len(itens_atuais) > 0:
                        self.indice_selecionado = (self.indice_selecionado - 1) % len(itens_atuais)
                elif evento.key in [pygame.K_DOWN, pygame.K_s]:
                    if len(itens_atuais) > 0:
                        self.indice_selecionado = (self.indice_selecionado + 1) % len(itens_atuais)
                elif evento.key in [pygame.K_RETURN, pygame.K_SPACE]:
                    self._executar_transacao(self.indice_selecionado)

            elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                # Clique nas abas
                for i, rect_aba in enumerate(self.rects_abas):
                    if rect_aba.collidepoint(evento.pos):
                        self.aba_ativa = i
                        self.indice_selecionado = 0
                        return

                # Clique na lista de itens
                for i, rect_item in enumerate(self.rects_itens_lista):
                    if rect_item.collidepoint(evento.pos):
                        self.indice_selecionado = i
                        self._executar_transacao(i)
                        return

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
                    self.exibir_mensagem(msg)
                else:
                    self.exibir_mensagem(f"⚠ {msg}")
        else:
            # Vender
            if 0 <= indice < len(inv.slots):
                slot = inv.slots[indice]
                sucesso, msg = self.loja.vender_item(slot.item.id, 1, halia)
                if sucesso:
                    self.exibir_mensagem(msg)
                    if self.indice_selecionado >= len(inv.slots):
                        self.indice_selecionado = max(0, len(inv.slots) - 1)
                else:
                    self.exibir_mensagem(f"⚠ {msg}")

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

        # 4. Cabeçalho e Título
        txt_titulo = self.fonte_titulo.render(f"Mercador — {self.loja.nome}", True, MARFIM_OFFWHITE)
        tela.blit(txt_titulo, (self.x_loja + 35, self.y_loja + 24))

        desenhar_flor_botanica(tela, self.x_loja + self.largura_loja - 50, self.y_loja + 40, cor=CINZA_LINHO, escala=0.8)

        # 5. Abas (Comprar / Vender)
        self.rects_abas.clear()
        x_aba = self.x_loja + 480
        y_aba = self.y_loja + 26
        
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
        pygame.draw.line(tela, CINZA_ARDOSIA, (self.x_loja + 30, self.y_loja + 66), (self.x_loja + self.largura_loja - 30, self.y_loja + 66), 1)

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
            for i, merc in enumerate(itens_exibir[:9]):
                rect_card = pygame.Rect(x_inicio_lista, y_pos, w_item_card, h_item_card)
                self.rects_itens_lista.append(rect_card)

                esta_sel = (i == self.indice_selecionado)
                esta_hover = rect_card.collidepoint(self.pos_mouse)
                fundo_c = (38, 38, 48) if (esta_sel or esta_hover) else (22, 22, 26)
                borda_c = BORDA_DESTAQUE if esta_sel else (CINZA_LINHO if esta_hover else (45, 45, 52))

                pygame.draw.rect(tela, fundo_c, rect_card, border_radius=2)
                pygame.draw.rect(tela, borda_c, rect_card, 1, border_radius=2)

                nome_it = merc.item_template.nome if merc.item_template else merc.item_id
                txt_it = self.fonte_texto.render(f"{'> ' if esta_sel else '  '}{nome_it}", True, MARFIM_OFFWHITE if esta_sel else CINZA_LINHO)
                tela.blit(txt_it, (rect_card.x + 8, rect_card.centery - txt_it.get_height() // 2))

                # Preço e Estoque
                info_preco = f"{merc.preco_compra} Ouro | Est: {merc.estoque_atual}"
                txt_pr = self.fonte_mini.render(info_preco, True, (230, 210, 130) if merc.disponivel else (120, 120, 120))
                tela.blit(txt_pr, (rect_card.right - txt_pr.get_width() - 10, rect_card.centery - txt_pr.get_height() // 2))

                y_pos += h_item_card + 6

        else:
            # Lista de Itens da Halia para Venda
            itens_exibir = inv.slots if inv else []
            txt_secao = self.fonte_sub.render(f"Sua Bolsa — Itens para Vender ({len(itens_exibir)})", True, MARFIM_OFFWHITE)
            tela.blit(txt_secao, (x_inicio_lista, y_inicio_lista))

            y_pos = y_inicio_lista + 32
            for i, slot in enumerate(itens_exibir[:9]):
                rect_card = pygame.Rect(x_inicio_lista, y_pos, w_item_card, h_item_card)
                self.rects_itens_lista.append(rect_card)

                esta_sel = (i == self.indice_selecionado)
                esta_hover = rect_card.collidepoint(self.pos_mouse)
                fundo_c = (38, 38, 48) if (esta_sel or esta_hover) else (22, 22, 26)
                borda_c = BORDA_DESTAQUE if esta_sel else (CINZA_LINHO if esta_hover else (45, 45, 52))

                pygame.draw.rect(tela, fundo_c, rect_card, border_radius=2)
                pygame.draw.rect(tela, borda_c, rect_card, 1, border_radius=2)

                item = slot.item
                nome_formatado = item.nome_formatado if hasattr(item, 'nome_formatado') else item.nome
                txt_it = self.fonte_texto.render(f"{'> ' if esta_sel else '  '}{nome_formatado} x{slot.quantidade}", True, MARFIM_OFFWHITE if esta_sel else CINZA_LINHO)
                tela.blit(txt_it, (rect_card.x + 8, rect_card.centery - txt_it.get_height() // 2))

                # Preço de Venda
                preco_venda = item.preco_venda
                txt_pr = self.fonte_mini.render(f"+{preco_venda} Ouro/un", True, (160, 220, 160) if preco_venda > 0 else (120, 120, 120))
                tela.blit(txt_pr, (rect_card.right - txt_pr.get_width() - 10, rect_card.centery - txt_pr.get_height() // 2))

                y_pos += h_item_card + 6

        # Linha vertical divisória
        pygame.draw.line(tela, CINZA_ARDOSIA, (self.x_loja + 540, self.y_loja + 80), (self.x_loja + 540, self.y_loja + self.altura_loja - 55), 1)

        # 7. SEÇÃO DIREITA: DETALHES DO ITEM E CARTEIRA
        x_det = self.x_loja + 565
        y_det = self.y_loja + 85
        w_det = self.largura_loja - 600

        # Carteira do Jogador
        rect_carteira = pygame.Rect(x_det, y_det, w_det, 45)
        desenhar_card_pergaminho(tela, rect_carteira, cor_fundo=(26, 26, 32), cor_borda=CINZA_LINHO)
        txt_ouro = self.fonte_sub.render(f"✦ Suas Moedas: {dinheiro} Ouro", True, (240, 220, 130))
        tela.blit(txt_ouro, (rect_carteira.x + 14, rect_carteira.centery - txt_ouro.get_height() // 2))

        # Detalhes do item selecionado
        y_card_det = y_det + 58
        h_card_det = self.altura_loja - 200
        rect_det_card = pygame.Rect(x_det, y_card_det, w_det, h_card_det)
        desenhar_card_pergaminho(tela, rect_det_card, cor_fundo=(22, 22, 26), cor_borda=CINZA_LINHO)

        item_selecionado = None
        if self.aba_ativa == 0:
            mercs = self.loja.obter_lista_mercadorias()
            if 0 <= self.indice_selecionado < len(mercs):
                item_selecionado = mercs[self.indice_selecionado].item_template
        else:
            if inv and 0 <= self.indice_selecionado < len(inv.slots):
                item_selecionado = inv.slots[self.indice_selecionado].item

        if item_selecionado:
            nome_f = item_selecionado.nome_formatado if hasattr(item_selecionado, 'nome_formatado') else item_selecionado.nome
            txt_n = self.fonte_sub.render(nome_f, True, MARFIM_OFFWHITE)
            tela.blit(txt_n, (rect_det_card.x + 16, rect_det_card.y + 16))

            txt_cat = self.fonte_mini.render(f"Tipo: {item_selecionado.categoria}  |  Raridade: {item_selecionado.raridade}", True, CINZA_LINHO)
            tela.blit(txt_cat, (rect_det_card.x + 16, rect_det_card.y + 44))

            pygame.draw.line(tela, CINZA_ARDOSIA, (rect_det_card.x + 14, rect_det_card.y + 68), (rect_det_card.right - 14, rect_det_card.y + 68), 1)

            # Descrição do Item
            from src.ui.ui_utils import quebrar_texto_em_linhas
            linhas_desc = quebrar_texto_em_linhas(item_selecionado.descricao, self.fonte_texto, w_det - 32)
            y_linha = rect_det_card.y + 78
            for l in linhas_desc:
                r_l = self.fonte_texto.render(l, True, (210, 210, 215))
                tela.blit(r_l, (rect_det_card.x + 16, y_linha))
                y_linha += 20

            # Bônus ou Efeitos
            y_linha += 10
            if isinstance(item_selecionado, ConsumivelItem):
                if item_selecionado.tipo_consumivel == "CURA_HP":
                    tela.blit(self.fonte_mini.render(f"✦ Regenera: +{item_selecionado.valor_efeito} Pontos de Vida (HP)", True, (140, 220, 160)), (rect_det_card.x + 16, y_linha))
                elif item_selecionado.tipo_consumivel == "RESTAURA_MP":
                    tela.blit(self.fonte_mini.render(f"✦ Restaura: +{item_selecionado.valor_efeito} Pontos de Mana (MP)", True, (130, 190, 240)), (rect_det_card.x + 16, y_linha))
                elif item_selecionado.tipo_consumivel == "DANO_OFENSIVO":
                    tela.blit(self.fonte_mini.render(f"⚔ Causa: {item_selecionado.valor_efeito} de dano ({item_selecionado.condicao_aplicada or 'puro'})", True, (240, 140, 140)), (rect_det_card.x + 16, y_linha))

            elif isinstance(item_selecionado, EquipamentoItem):
                tela.blit(self.fonte_mini.render(f"✦ Slot: {item_selecionado.slot} (Nível +{item_selecionado.nivel_upgrade})", True, (220, 210, 150)), (rect_det_card.x + 16, y_linha))
                y_linha += 18
                for attr, val in item_selecionado.obter_bonus_atributos_efetivos().items():
                    tela.blit(self.fonte_mini.render(f"  + {attr.capitalize()}: +{val}", True, MARFIM_OFFWHITE), (rect_det_card.x + 16, y_linha))
                    y_linha += 18
                for stat, val in item_selecionado.obter_bonus_stats_efetivos().items():
                    tela.blit(self.fonte_mini.render(f"  + {stat.replace('_', ' ').title()}: +{val}", True, MARFIM_OFFWHITE), (rect_det_card.x + 16, y_linha))
                    y_linha += 18

            # Botão de Ação no Rodapé do Card
            lbl_btn = "[ENTER ou CLIQUE] COMPRAR 1x" if self.aba_ativa == 0 else "[ENTER ou CLIQUE] VENDER 1x"
            txt_btn = self.fonte_texto.render(lbl_btn, True, MARFIM_OFFWHITE)
            rect_btn = pygame.Rect(rect_det_card.x + 16, rect_det_card.bottom - 42, w_det - 32, 30)
            pygame.draw.rect(tela, (42, 42, 54), rect_btn, border_radius=2)
            pygame.draw.rect(tela, BORDA_DESTAQUE, rect_btn, 1, border_radius=2)
            tela.blit(txt_btn, (rect_btn.centerx - txt_btn.get_width() // 2, rect_btn.centery - txt_btn.get_height() // 2))

        # 8. RODAPÉ INFORMATIVO E FEEDBACK
        if self.mensagem_feedback:
            txt_feed = self.fonte_texto.render(self.mensagem_feedback, True, (160, 230, 180))
            tela.blit(txt_feed, (self.x_loja + 45, self.y_loja + self.altura_loja - 36))
        else:
            txt_dica = self.fonte_mini.render("[Setas/WASD] Navegar   |   [TAB] Alternar Compra/Venda   |   [ESC/E] Sair da Loja", True, CINZA_LINHO)
            tela.blit(txt_dica, (self.x_loja + 45, self.y_loja + self.altura_loja - 36))
