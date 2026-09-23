# src/ui/notification_manager.py
import pygame
import os
import sys

_raiz_projeto = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _raiz_projeto not in sys.path:
    sys.path.insert(0, _raiz_projeto)

from src.utils.colors import (
    CARVAO_PROFUNDO, MARFIM_OFFWHITE, CINZA_LINHO, CINZA_ARDOSIA, BORDA_DESTAQUE,
    BARRA_VIDA_JOGADOR, BARRA_MANA, UI_TEXTO_DESTAQUE, AZUL_HOVER_BG, AZUL_HOVER_MENU
)
from src.utils.resource_manager import ResourceManager
from src.ui.ui_utils import desenhar_painel_padrao, desenhar_card_pergaminho, quebrar_texto_em_linhas

class NotificacaoToast:
    """Representa um banner individual de notificação push."""
    def __init__(self, titulo, mensagem, tipo="ITEM", duracao_ticks=180, icone="✦"):
        self.titulo = titulo
        self.mensagem = mensagem
        self.tipo = tipo.upper() # ITEM, RECEITA, MEMORIA, MISSAO, ALERTA
        self.duracao_maxima = duracao_ticks
        self.tempo_vida = duracao_ticks
        self.icone = icone
        self.alpha = 0
        self.offset_x = 50 # Efeito de deslizamento (Slide-in)

        # Configuração de cores por tipo
        self.cor_borda = BORDA_DESTAQUE if self.tipo in ["MEMORIA", "MISSAO", "SINCRONIA"] else CINZA_LINHO
        if self.tipo == "ITEM":
            self.cor_destaque = (220, 210, 140)
        elif self.tipo == "RECEITA":
            self.cor_destaque = (140, 210, 240)
        elif self.tipo in ["MEMORIA", "SINCRONIA"]:
            self.cor_destaque = (160, 240, 180)
        elif self.tipo == "MISSAO":
            self.cor_destaque = (240, 180, 120)
        elif self.tipo == "SISTEMA":
            self.cor_destaque = (170, 225, 205)
        else:
            self.cor_destaque = MARFIM_OFFWHITE

    def update(self):
        self.tempo_vida -= 1
        
        # Animação de entrada (Slide in + Fade in)
        if self.duracao_maxima - self.tempo_vida < 15:
            self.alpha = min(255, self.alpha + 18)
            self.offset_x = max(0, self.offset_x - 4)
        # Animação de saída (Fade out)
        elif self.tempo_vida < 20:
            self.alpha = max(0, self.alpha - 14)
            self.offset_x += 3
        else:
            self.alpha = 255
            self.offset_x = 0

    @property
    def expirou(self):
        return self.tempo_vida <= 0


import json

class NotificationManager:
    """
    Gerenciador global de notificações push em estilo Toast e Histórico de Notificações.
    - Suporte a catálogo centralizado de notificações padrões (notificacoes.json).
    - Empilhamento vertical suave no canto superior direito.
    - Histórico acessível clicando em qualquer toast ou pressionando a tecla [H].
    - Exibe as últimas 4 notificações com visual editorial.
    """
    def __init__(self, largura_tela=1280, altura_tela=720):
        self.largura_tela = largura_tela
        self.altura_tela = altura_tela
        self.notificacoes = []
        self.MAX_SIMULTANEAS = 4

        # Catálogo de Notificações Padrões
        self.catalogo_padrao = self._carregar_catalogo_padrao()

        # Histórico Completo de Notificações
        self.historico = []
        self.mostrar_historico = False
        self.rects_toasts_ativos = []
        self.rect_painel_historico = None
        self.rect_fechar_historico = None

        # Tipografia
        self.fonte_titulo = ResourceManager.carregar_fonte("sunday", 18)
        self.fonte_titulo_modal = ResourceManager.carregar_fonte("sunday", 24)
        self.fonte_texto = ResourceManager.carregar_fonte("contrail", 14)
        self.fonte_texto_modal = ResourceManager.carregar_fonte("contrail", 15)
        self.fonte_mini = ResourceManager.carregar_fonte("contrail", 13)
        self.fonte_icone = ResourceManager.carregar_fonte("sunday", 22)
        self.fonte_icone_grande = ResourceManager.carregar_fonte("sunday", 26)

    def _carregar_catalogo_padrao(self):
        caminho = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "notificacoes.json"))
        if os.path.exists(caminho):
            try:
                with open(caminho, "r", encoding="utf-8") as f:
                    dados = json.load(f)
                    return dados.get("notificacoes", {})
            except Exception as e:
                print(f"[NotificationManager] Erro ao carregar notificacoes.json: {e}")
        # Fallback padrão seguro
        return {
            "notificacao_level": {"titulo": "Novo Nível!", "mensagem": "Você alcançou o Nível {nivel}!", "tipo": "MEMORIA", "icone": "✦", "duracao_ticks": 240},
            "notificacao_sincronia": {"titulo": "Sincronia Aumentada", "mensagem": "Sua sincronia arcana alcançou o Nível {nivel}!", "tipo": "SINCRONIA", "icone": "✦", "duracao_ticks": 240},
            "notificacao_memoria": {"titulo": "Memória Desperta", "mensagem": "Você alcançou o Estágio {estagio} da sua memória arcana!", "tipo": "MEMORIA", "icone": "✦", "duracao_ticks": 240},
            "notificacao_item": {"titulo": "Item Adicionado", "mensagem": "Guardou {quantidade}{item} na bolsa.", "tipo": "ITEM", "icone": "✦", "duracao_ticks": 180},
            "notificacao_receita": {"titulo": "Nova Receita Descoberta", "mensagem": "Aprendeu a confeccionar {receita}.", "tipo": "RECEITA", "icone": "📜", "duracao_ticks": 220},
            "notificacao_item_fabricado": {"titulo": "Item Fabricado", "mensagem": "Obteve {quantidade}x {nome}.", "tipo": "RECEITA", "icone": "🧪", "duracao_ticks": 200},
            "notificacao_missao": {"titulo": "Missão Atualizada", "mensagem": "{missao}", "tipo": "MISSAO", "icone": "✦", "duracao_ticks": 220},
            "notificacao_alerta": {"titulo": "{titulo}", "mensagem": "{mensagem}", "tipo": "ALERTA", "icone": "⚠", "duracao_ticks": 200},
            "notificacao_salvo": {"titulo": "Jogo Salvo", "mensagem": "Progresso salvo com sucesso no {slot}.", "tipo": "SISTEMA", "icone": "💾", "duracao_ticks": 180},
            "notificacao_autosave": {"titulo": "Salvamento Automático", "mensagem": "Checkpoint registrado no {slot}.", "tipo": "SISTEMA", "icone": "💾", "duracao_ticks": 160},
            "notificacao_carregar": {"titulo": "Jogo Carregado", "mensagem": "Progresso carregado com sucesso do {slot}.", "tipo": "SISTEMA", "icone": "📂", "duracao_ticks": 180}
        }

    def notificar(self, identificador_ou_titulo, mensagem=None, tipo="ITEM", duracao_ticks=180, icone="✦", **kwargs):
        """
        Adiciona uma nova notificação push à pilha e ao histórico.
        Suporta:
        1. Chamada por chave do catálogo: notificar("notificacao_level", nivel=2)
        2. Chamada direta clássica: notificar("Título", "Mensagem", tipo="ITEM")
        """
        if identificador_ou_titulo in self.catalogo_padrao:
            template = self.catalogo_padrao[identificador_ou_titulo]
            substituicoes = dict(kwargs)
            if mensagem is not None and "mensagem" not in substituicoes:
                substituicoes["mensagem"] = mensagem
                substituicoes["item"] = mensagem
            
            titulo_raw = template.get("titulo", "")
            mensagem_raw = template.get("mensagem", "")
            
            # Formatação segura sem quebrar se faltar parâmetro
            try:
                titulo = titulo_raw.format(**substituicoes)
            except Exception:
                titulo = titulo_raw
                
            try:
                mensagem_final = mensagem_raw.format(**substituicoes)
            except Exception:
                mensagem_final = mensagem_raw
                
            tipo_final = kwargs.get("tipo", template.get("tipo", tipo))
            duracao_final = kwargs.get("duracao_ticks", template.get("duracao_ticks", duracao_ticks))
            icone_final = kwargs.get("icone", template.get("icone", icone))
            
            self._adicionar_toast(titulo, mensagem_final, tipo_final, duracao_final, icone_final)
        else:
            msg_final = mensagem if mensagem is not None else ""
            self._adicionar_toast(identificador_ou_titulo, msg_final, tipo, duracao_ticks, icone)

    def notificar_padrao(self, chave, **kwargs):
        """Atalho explícito para disparar notificação padrão a partir do catálogo."""
        self.notificar(chave, **kwargs)

    def _adicionar_toast(self, titulo, mensagem, tipo, duracao_ticks, icone):
        toast = NotificacaoToast(titulo, mensagem, tipo, duracao_ticks, icone)
        self.notificacoes.append(toast)
        if len(self.notificacoes) > self.MAX_SIMULTANEAS:
            self.notificacoes.pop(0)

        # Registra no histórico permanente
        self.historico.append({
            "titulo": titulo,
            "mensagem": mensagem,
            "tipo": str(tipo).upper(),
            "icone": icone,
            "cor_destaque": toast.cor_destaque,
            "cor_borda": toast.cor_borda
        })

    def notificar_item_coletado(self, nome_item, quantidade=1):
        if isinstance(quantidade, str):
            self.notificar("notificacao_item_especial", item=nome_item, mensagem=quantidade)
        else:
            qtd_str = f"x{quantidade} " if (isinstance(quantidade, (int, float)) and quantidade > 1) else ""
            self.notificar("notificacao_item", item=nome_item, quantidade=qtd_str)

    def notificar_receita_desbloqueada(self, nome_receita):
        self.notificar("notificacao_receita", receita=nome_receita)

    def notificar_memoria_desperta(self, estagio):
        self.notificar("notificacao_memoria", estagio=estagio)

    def notificar_sincronia_aumentada(self, nivel):
        self.notificar("notificacao_sincronia", nivel=nivel)

    def alternar_historico(self):
        self.mostrar_historico = not self.mostrar_historico

    def abrir_historico(self):
        self.mostrar_historico = True

    def fechar_historico(self):
        self.mostrar_historico = False

    def handle_event(self, evento):
        """Processa um evento individual. Retorna True se o evento foi consumido."""
        if evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_h:
                self.alternar_historico()
                return True
            elif evento.key == pygame.K_ESCAPE and self.mostrar_historico:
                self.fechar_historico()
                return True

        elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            # 1. Se o histórico estiver aberto
            if self.mostrar_historico:
                if self.rect_fechar_historico and self.rect_fechar_historico.collidepoint(evento.pos):
                    self.fechar_historico()
                    return True
                elif self.rect_painel_historico and not self.rect_painel_historico.collidepoint(evento.pos):
                    self.fechar_historico()
                    return True
                elif self.rect_painel_historico and self.rect_painel_historico.collidepoint(evento.pos):
                    return True # Consome clique dentro do modal
            # 2. Se houver toasts visíveis, clicar neles abre o histórico
            else:
                for rect_t in self.rects_toasts_ativos:
                    if rect_t.collidepoint(evento.pos):
                        self.abrir_historico()
                        return True
        return False

    def handle_events(self, eventos):
        """Filtra e retorna apenas a lista de eventos que NÃO foram consumidos pelo histórico/toasts."""
        eventos_restantes = []
        for evento in eventos:
            if not self.handle_event(evento):
                eventos_restantes.append(evento)
        return eventos_restantes

    def update(self):
        for toast in self.notificacoes:
            toast.update()
        self.notificacoes = [t for t in self.notificacoes if not t.expirou]

    def draw(self, tela):
        # 1. Desenha os toasts ativos no canto superior direito
        self.rects_toasts_ativos.clear()
        
        if self.notificacoes:
            w_card = 340
            h_card = 62
            espacamento = 10
            x_base = self.largura_tela - w_card - 25
            y_base = 25

            for i, toast in enumerate(self.notificacoes):
                y_pos = y_base + (i * (h_card + espacamento))
                x_pos = x_base + toast.offset_x

                rect_toast_tela = pygame.Rect(x_pos, y_pos, w_card, h_card)
                self.rects_toasts_ativos.append(rect_toast_tela)

                # Superfície com canal alfa
                surf_toast = pygame.Surface((w_card, h_card), pygame.SRCALPHA)
                
                # Fundo e borda
                pygame.draw.rect(surf_toast, (*CARVAO_PROFUNDO[:3], int(toast.alpha * 0.94)), (0, 0, w_card, h_card), border_radius=3)
                pygame.draw.rect(surf_toast, (*toast.cor_borda[:3], int(toast.alpha)), (0, 0, w_card, h_card), 1, border_radius=3)

                # Ícone lateral
                txt_ico = self.fonte_icone.render(toast.icone, True, toast.cor_destaque)
                txt_ico.set_alpha(toast.alpha)
                surf_toast.blit(txt_ico, (14, (h_card - txt_ico.get_height()) // 2))

                # Título
                txt_tit = self.fonte_titulo.render(toast.titulo, True, toast.cor_destaque)
                txt_tit.set_alpha(toast.alpha)
                surf_toast.blit(txt_tit, (46, 10))

                # Mensagem
                msg_curta = toast.mensagem if len(toast.mensagem) <= 38 else toast.mensagem[:35] + "..."
                txt_msg = self.fonte_texto.render(msg_curta, True, MARFIM_OFFWHITE)
                txt_msg.set_alpha(toast.alpha)
                surf_toast.blit(txt_msg, (46, 32))

                # Barra sutil de tempo restante na base do toast
                razao_vida = max(0.0, min(1.0, toast.tempo_vida / toast.duracao_maxima))
                w_prog = int((w_card - 8) * razao_vida)
                if w_prog > 0:
                    pygame.draw.line(surf_toast, (*toast.cor_destaque[:3], int(toast.alpha * 0.7)), (4, h_card - 3), (4 + w_prog, h_card - 3), 2)

                tela.blit(surf_toast, (x_pos, y_pos))

        # 2. Modal do Histórico das Últimas 4 Notificações
        if self.mostrar_historico:
            self._desenhar_modal_historico(tela)

    def _desenhar_modal_historico(self, tela):
        """Renderiza a janela flutuante com as últimas 4 notificações."""
        # Película escura de fundo
        overlay = pygame.Surface((self.largura_tela, self.altura_tela), pygame.SRCALPHA)
        overlay.fill((8, 8, 12, 200))
        tela.blit(overlay, (0, 0))

        largura_p = min(680, self.largura_tela - 60)
        altura_p = min(540, self.altura_tela - 60)
        x_p = (self.largura_tela - largura_p) // 2
        y_p = (self.altura_tela - altura_p) // 2

        self.rect_painel_historico = pygame.Rect(x_p, y_p, largura_p, altura_p)
        desenhar_painel_padrao(tela, self.rect_painel_historico, cor_fundo=CARVAO_PROFUNDO, cor_borda=CINZA_LINHO, largura_borda=1, border_radius=4, alpha=252)

        # Moldura decorativa interna
        pygame.draw.rect(tela, (28, 28, 36), self.rect_painel_historico.inflate(-10, -10), 1, border_radius=2)

        # Cabeçalho
        txt_tit = self.fonte_titulo_modal.render("✦ Histórico de Notificações Recentes ✦", True, MARFIM_OFFWHITE)
        tela.blit(txt_tit, (x_p + (largura_p - txt_tit.get_width()) // 2, y_p + 22))

        # Botão Fechar [✕]
        self.rect_fechar_historico = pygame.Rect(x_p + largura_p - 44, y_p + 18, 28, 28)
        pos_m = pygame.mouse.get_pos()
        hover_fechar = self.rect_fechar_historico.collidepoint(pos_m)
        pygame.draw.rect(tela, (42, 42, 54) if hover_fechar else (24, 24, 30), self.rect_fechar_historico, border_radius=3)
        pygame.draw.rect(tela, MARFIM_OFFWHITE if hover_fechar else CINZA_ARDOSIA, self.rect_fechar_historico, 1, border_radius=3)
        txt_x = self.fonte_mini.render("✕", True, MARFIM_OFFWHITE if hover_fechar else CINZA_LINHO)
        tela.blit(txt_x, (self.rect_fechar_historico.centerx - txt_x.get_width() // 2, self.rect_fechar_historico.centery - txt_x.get_height() // 2))

        # Divisória
        pygame.draw.line(tela, CINZA_ARDOSIA, (x_p + 25, y_p + 60), (x_p + largura_p - 25, y_p + 60), 1)

        # Últimas 4 notificações
        ultimas_4 = self.historico[-4:] if self.historico else []
        ultimas_4.reverse() # Mais recentes no topo

        if not ultimas_4:
            txt_vazio = self.fonte_texto_modal.render("Nenhuma notificação registrada recentemente.", True, (130, 130, 145))
            tela.blit(txt_vazio, (x_p + (largura_p - txt_vazio.get_width()) // 2, y_p + 230))
        else:
            y_card = y_p + 76
            h_card = 92
            w_c = largura_p - 50

            for i, notif in enumerate(ultimas_4):
                r_c = pygame.Rect(x_p + 25, y_card, w_c, h_card)
                pygame.draw.rect(tela, (22, 22, 28), r_c, border_radius=3)
                pygame.draw.rect(tela, notif["cor_borda"], r_c, 1, border_radius=3)

                # Ícone
                ico = self.fonte_icone_grande.render(notif["icone"], True, notif["cor_destaque"])
                tela.blit(ico, (r_c.x + 18, r_c.centery - ico.get_height() // 2))

                # Título e Tipo
                t_tit = self.fonte_titulo.render(notif["titulo"], True, notif["cor_destaque"])
                tela.blit(t_tit, (r_c.x + 58, r_c.y + 12))

                tipo_txt = self.fonte_mini.render(f"[{notif['tipo']}]", True, (120, 120, 135))
                tela.blit(tipo_txt, (r_c.right - tipo_txt.get_width() - 16, r_c.y + 14))

                # Mensagem com quebra automática
                linhas = quebrar_texto_em_linhas(notif["mensagem"], self.fonte_texto_modal, w_c - 75)
                y_txt_m = r_c.y + 36
                for linha in linhas[:2]:
                    t_lin = self.fonte_texto_modal.render(linha, True, MARFIM_OFFWHITE)
                    tela.blit(t_lin, (r_c.x + 58, y_txt_m))
                    y_txt_m += 20

                y_card += h_card + 12

        # Rodapé
        txt_rod = self.fonte_mini.render("[H] Fechar   •   [ESC] Retomar   •   [Clique Fora] Fechar Histórico", True, CINZA_LINHO)
        tela.blit(txt_rod, (x_p + (largura_p - txt_rod.get_width()) // 2, y_p + altura_p - 30))
