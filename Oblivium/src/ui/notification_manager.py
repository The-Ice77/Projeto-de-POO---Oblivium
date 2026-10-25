# src/ui/notification_manager.py
import pygame
import os
import sys
import json

_raiz_projeto = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _raiz_projeto not in sys.path:
    sys.path.insert(0, _raiz_projeto)

from src.utils.colors import (
    CARVAO_PROFUNDO, MARFIM_OFFWHITE, CINZA_LINHO, CINZA_ARDOSIA, BORDA_DESTAQUE
)
from src.utils.resource_manager import ResourceManager
from src.ui.ui_utils import (
    desenhar_painel_padrao,
    quebrar_texto_em_linhas
)
from src.ui.icon_registry import (
    desenhar_icone_fechar,
    desenhar_icone_conquista,
    desenhar_icone_notificacao
)


class NotificacaoToast:
    """Representa um banner individual de notificação push."""
    def __init__(self, titulo, mensagem, tipo="ITEM", duracao_ticks=150, icone="✦", subtitulo=None, descricao=None, eh_platina=False, id_conquista="", cor_icone=None):
        self.titulo = str(titulo)
        self.mensagem = str(mensagem) if mensagem is not None else ""
        self.tipo = tipo.upper()  # ITEM, RECEITA, MEMORIA, MISSAO, ALERTA, CONQUISTA, SISTEMA
        self.subtitulo = subtitulo
        self.descricao = descricao
        self.eh_platina = eh_platina
        self.id_conquista = id_conquista or ""
        self.duracao_maxima = duracao_ticks
        self.tempo_vida = duracao_ticks
        self.icone = icone or "✦"
        self.alpha = 0
        self.offset_y = -22  # Descida suave do topo (Slide-down)

        # Configuração de cores e styling por tipo
        if self.tipo == "CONQUISTA":
            if self.eh_platina:
                self.cor_borda = (240, 215, 115)
                self.cor_destaque = (255, 235, 145)
            else:
                self.cor_borda = (160, 195, 225)
                self.cor_destaque = (210, 235, 255)
        elif self.tipo in ["MEMORIA", "MISSAO", "SINCRONIA"]:
            self.cor_borda = BORDA_DESTAQUE
            if self.tipo in ["MEMORIA", "SINCRONIA"]:
                self.cor_destaque = (160, 240, 180)
            else:
                self.cor_destaque = (240, 200, 120)
        elif self.tipo == "ITEM":
            self.cor_borda = (75, 75, 90)
            self.cor_destaque = (225, 215, 145)
        elif self.tipo == "RECEITA":
            self.cor_borda = (75, 85, 105)
            self.cor_destaque = (140, 210, 240)
        elif self.tipo == "SISTEMA":
            self.cor_borda = (65, 75, 80)
            self.cor_destaque = (170, 225, 205)
        else:
            self.cor_borda = CINZA_LINHO
            self.cor_destaque = MARFIM_OFFWHITE

        self.cor_icone = tuple(cor_icone) if cor_icone else self.cor_destaque

    def update(self):
        self.tempo_vida -= 1

        # Animação de entrada (Slide down + Fade in) - 15 frames (~250ms)
        tempo_decorrido = self.duracao_maxima - self.tempo_vida
        if tempo_decorrido < 15:
            fator_entrada = tempo_decorrido / 15.0
            self.alpha = int(255 * fator_entrada)
            self.offset_y = int(-22 * (1.0 - fator_entrada))
        # Animação de saída (Fade out suave + elevação sutil) - 18 frames (~300ms)
        elif self.tempo_vida < 18:
            fator_saida = max(0.0, self.tempo_vida / 18.0)
            self.alpha = int(255 * fator_saida)
            self.offset_y = int(-8 * (1.0 - fator_saida))
        else:
            self.alpha = 255
            self.offset_y = 0

    @property
    def expirou(self):
        return self.tempo_vida <= 0


class NotificationManager:
    """
    Gerenciador global de notificações push em estilo Toast e Histórico de Notificações.
    - Anti-Poluição: Sistema de fila estrita com no máximo 1 banner ativo simultâneo.
    - Layout Steam Dark Fantasy dedicado para Conquistas (420x70px com brasão heráldico procedural).
    - Toasts comuns compactos (330x52px) com ícones vetoriais gerados em código.
    - Histórico acessível via tecla [H] ou clique nos banners.
    """
    def __init__(self, largura_tela=1280, altura_tela=720):
        self.largura_tela = largura_tela
        self.altura_tela = altura_tela
        self.notificacoes = []      # Lista com o toast ativo (máx 1 simultâneo)
        self.fila_espera = []       # Fila sequencial anti-spam
        self.MAX_SIMULTANEAS = 1    # Estritamente 1 notificação por vez no topo da tela!

        # Catálogo de Notificações Padrões
        self.catalogo_padrao = self._carregar_catalogo_padrao()

        # Histórico Completo de Notificações
        self.historico = []
        self.mostrar_historico = False
        self.rects_toasts_ativos = []
        self.rect_painel_historico = None
        self.rect_fechar_historico = None

        # Tipografia Refinada
        self.fonte_kicker = ResourceManager.carregar_fonte("contrail", 12)
        self.fonte_conquista_titulo = ResourceManager.carregar_fonte("sunday", 17)
        self.fonte_titulo_toast = ResourceManager.carregar_fonte("sunday", 15)
        self.fonte_titulo = ResourceManager.carregar_fonte("sunday", 17)
        self.fonte_titulo_modal = ResourceManager.carregar_fonte("sunday", 24)
        self.fonte_texto = ResourceManager.carregar_fonte("contrail", 13)
        self.fonte_texto_modal = ResourceManager.carregar_fonte("contrail", 15)
        self.fonte_mini = ResourceManager.carregar_fonte("contrail", 12)

    def _carregar_catalogo_padrao(self):
        caminho = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "notificacoes.json"))
        if os.path.exists(caminho):
            try:
                with open(caminho, "r", encoding="utf-8") as f:
                    dados = json.load(f)
                    return dados.get("notificacoes", {})
            except Exception as e:
                print(f"[NotificationManager] Erro ao carregar notificacoes.json: {e}")
        return {}

    def notificar(self, identificador_ou_titulo, mensagem=None, tipo="ITEM", duracao_ticks=150, icone="✦", **kwargs):
        """
        Adiciona uma nova notificação push à fila com proteção anti-duplicação.
        """
        if identificador_ou_titulo in self.catalogo_padrao:
            template = self.catalogo_padrao[identificador_ou_titulo]
            substituicoes = dict(kwargs)
            if mensagem is not None and "mensagem" not in substituicoes:
                substituicoes["mensagem"] = mensagem
                substituicoes["item"] = mensagem

            titulo_raw = str(template.get("titulo", ""))
            mensagem_raw = str(template.get("mensagem", ""))

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

    def _adicionar_toast(self, titulo, mensagem, tipo, duracao_ticks, icone, subtitulo=None, descricao=None, eh_platina=False, id_conquista="", cor_icone=None):
        # Proteção anti-duplicação consecutiva (de-bounce)
        for t in self.notificacoes + self.fila_espera:
            if t.titulo == titulo and t.mensagem == mensagem and t.tipo == tipo:
                return

        toast = NotificacaoToast(
            titulo=titulo,
            mensagem=mensagem,
            tipo=tipo,
            duracao_ticks=duracao_ticks,
            icone=icone,
            subtitulo=subtitulo,
            descricao=descricao,
            eh_platina=eh_platina,
            id_conquista=id_conquista,
            cor_icone=cor_icone
        )

        # Conquistas recebem prioridade máxima de exibição na fila
        if toast.tipo == "CONQUISTA":
            if not self.notificacoes:
                self.notificacoes.append(toast)
            else:
                self.fila_espera.insert(0, toast)
        else:
            if not self.notificacoes:
                self.notificacoes.append(toast)
            else:
                self.fila_espera.append(toast)

        # Registra no histórico permanente
        self.historico.append({
            "titulo": titulo,
            "mensagem": descricao if descricao else mensagem,
            "tipo": str(tipo).upper(),
            "icone": icone,
            "id_conquista": id_conquista,
            "cor_icone": toast.cor_icone,
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

    def notificar_conquista(self, conquista):
        """
        Dispara banner comemorativo no formato Steam Dark Fantasy para uma nova conquista.
        Exibe cabeçalho dourado, arte procedural do brasão, nome proeminente e descrição.
        """
        if isinstance(conquista, dict):
            cid = conquista.get("id", "")
            nome = conquista.get("titulo", "Nova Conquista")
            desc = conquista.get("descricao", "")
            ico = conquista.get("icone", "✦")
            cor_c = conquista.get("cor", (180, 215, 245))
            eh_platina = (cid == "mestre_platinador")
        else:
            cid = ""
            nome = str(conquista)
            desc = ""
            ico = "✦"
            cor_c = (180, 215, 245)
            eh_platina = False

        self._adicionar_toast(
            titulo=nome,
            mensagem=desc,
            tipo="CONQUISTA",
            duracao_ticks=210,
            icone=ico,
            subtitulo="CONQUISTA DESBLOQUEADA",
            descricao=desc,
            eh_platina=eh_platina,
            id_conquista=cid,
            cor_icone=cor_c
        )

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
            if self.mostrar_historico:
                if self.rect_fechar_historico and self.rect_fechar_historico.collidepoint(evento.pos):
                    self.fechar_historico()
                    return True
                elif self.rect_painel_historico and not self.rect_painel_historico.collidepoint(evento.pos):
                    self.fechar_historico()
                    return True
                elif self.rect_painel_historico and self.rect_painel_historico.collidepoint(evento.pos):
                    return True
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

        # Remove toast expirado
        self.notificacoes = [t for t in self.notificacoes if not t.expirou]

        # Fila sequencial: quando a notificação atual some, a próxima entra suavemente
        if not self.notificacoes and self.fila_espera:
            proximo = self.fila_espera.pop(0)
            self.notificacoes.append(proximo)

    def draw(self, tela):
        self.rects_toasts_ativos.clear()

        if self.notificacoes:
            toast = self.notificacoes[0]
            if toast.tipo == "CONQUISTA":
                self._desenhar_toast_conquista(tela, toast)
            else:
                self._desenhar_toast_comum(tela, toast)

        if self.mostrar_historico:
            self._desenhar_modal_historico(tela)

    def _desenhar_toast_conquista(self, tela, toast):
        """Renderiza banner prestigioso estilo Steam / Dark Fantasy para Conquistas com ícone procedural."""
        w_card = 420
        h_card = 70
        x_pos = (self.largura_tela - w_card) // 2
        y_pos = 20 + toast.offset_y

        rect_toast_tela = pygame.Rect(x_pos, y_pos, w_card, h_card)
        self.rects_toasts_ativos.append(rect_toast_tela)

        surf_toast = pygame.Surface((w_card, h_card), pygame.SRCALPHA)

        # Fundo Dark Fantasy profundo
        pygame.draw.rect(surf_toast, (*CARVAO_PROFUNDO[:3], 245), (0, 0, w_card, h_card), border_radius=4)

        # Borda externa
        cor_borda = (240, 215, 115) if toast.eh_platina else (160, 195, 225)
        pygame.draw.rect(surf_toast, cor_borda, (0, 0, w_card, h_card), 1, border_radius=4)

        # Borda interna sutil decorativa (inset 2px)
        rect_inner = pygame.Rect(2, 2, w_card - 4, h_card - 4)
        pygame.draw.rect(surf_toast, (35, 48, 64), rect_inner, 1, border_radius=3)

        # Brasão Heráldico Lateral (Esquerda 48x48) com Arte Procedural Exclusiva
        rect_brasao = pygame.Rect(11, 11, 48, 48)
        pygame.draw.rect(surf_toast, (20, 24, 32), rect_brasao, border_radius=3)
        pygame.draw.rect(surf_toast, toast.cor_icone, rect_brasao, 1, border_radius=3)

        desenhar_icone_conquista(
            surf_toast,
            rect_brasao,
            toast.id_conquista,
            cor=toast.cor_icone,
            desbloqueada=True,
            secreta=False
        )

        # Bloco de Texto (Direita)
        x_txt = 70

        # Linha 1: Kicker elegante
        kicker_str = "CONQUISTA PLATINA DESBLOQUEADA" if toast.eh_platina else "CONQUISTA DESBLOQUEADA"
        cor_kicker = (255, 225, 115) if toast.eh_platina else (160, 205, 240)
        # Pequeno losango antes do kicker
        pts_k = [(x_txt + 4, 15), (x_txt + 8, 11), (x_txt + 12, 15), (x_txt + 8, 19)]
        pygame.draw.polygon(surf_toast, cor_kicker, pts_k)

        txt_kicker = self.fonte_kicker.render(kicker_str, True, cor_kicker)
        surf_toast.blit(txt_kicker, (x_txt + 17, 8))

        # Linha 2: Nome da Conquista
        tit_curto = toast.titulo if len(toast.titulo) <= 32 else toast.titulo[:29] + "..."
        txt_tit = self.fonte_conquista_titulo.render(tit_curto, True, (246, 243, 236))
        surf_toast.blit(txt_tit, (x_txt, 25))

        # Linha 3: Descrição da Façanha
        desc_str = toast.descricao if toast.descricao else toast.mensagem
        if len(desc_str) > 52:
            desc_str = desc_str[:49] + "..."
        txt_desc = self.fonte_texto.render(desc_str, True, (185, 190, 200))
        surf_toast.blit(txt_desc, (x_txt, 47))

        # Barra sutil de duração na base
        razao_vida = max(0.0, min(1.0, toast.tempo_vida / toast.duracao_maxima))
        w_prog = int((w_card - 16) * razao_vida)
        if w_prog > 0:
            pygame.draw.line(surf_toast, cor_borda, (8, h_card - 2), (8 + w_prog, h_card - 2), 2)

        surf_toast.set_alpha(toast.alpha)
        tela.blit(surf_toast, (x_pos, y_pos))

    def _desenhar_toast_comum(self, tela, toast):
        """Renderiza banner compacto e discreto para missões, itens, checkpoints e alertas com ícone procedural."""
        w_card = 340
        h_card = 54
        x_pos = (self.largura_tela - w_card) // 2
        y_pos = 20 + toast.offset_y

        rect_toast_tela = pygame.Rect(x_pos, y_pos, w_card, h_card)
        self.rects_toasts_ativos.append(rect_toast_tela)

        surf_toast = pygame.Surface((w_card, h_card), pygame.SRCALPHA)

        # Fundo e borda fina
        pygame.draw.rect(surf_toast, (*CARVAO_PROFUNDO[:3], 242), (0, 0, w_card, h_card), border_radius=3)
        pygame.draw.rect(surf_toast, toast.cor_borda[:3], (0, 0, w_card, h_card), 1, border_radius=3)

        # Bloco de Ícone lateral procedural
        rect_ico = pygame.Rect(8, 8, 36, 36)
        pygame.draw.rect(surf_toast, (20, 22, 28), rect_ico, border_radius=3)
        pygame.draw.rect(surf_toast, (50, 54, 66), rect_ico, 1, border_radius=3)
        desenhar_icone_notificacao(surf_toast, rect_ico.centerx, rect_ico.centery, tipo=toast.tipo, cor=toast.cor_destaque)

        # Título
        tit_curto = toast.titulo if len(toast.titulo) <= 30 else toast.titulo[:27] + "..."
        txt_tit = self.fonte_titulo_toast.render(tit_curto, True, toast.cor_destaque)
        surf_toast.blit(txt_tit, (52, 8))

        # Mensagem
        msg_curta = toast.mensagem if len(toast.mensagem) <= 40 else toast.mensagem[:37] + "..."
        txt_msg = self.fonte_texto.render(msg_curta, True, MARFIM_OFFWHITE)
        surf_toast.blit(txt_msg, (52, 28))

        # Linha de tempo restante sutil
        razao_vida = max(0.0, min(1.0, toast.tempo_vida / toast.duracao_maxima))
        w_prog = int((w_card - 8) * razao_vida)
        if w_prog > 0:
            pygame.draw.line(surf_toast, toast.cor_destaque[:3], (4, h_card - 2), (4 + w_prog, h_card - 2), 1)

        surf_toast.set_alpha(toast.alpha)
        tela.blit(surf_toast, (x_pos, y_pos))

    def _desenhar_modal_historico(self, tela):
        """Renderiza a janela flutuante com as últimas 4 notificações e botão [X] procedural."""
        overlay = pygame.Surface((self.largura_tela, self.altura_tela), pygame.SRCALPHA)
        overlay.fill((8, 8, 12, 200))
        tela.blit(overlay, (0, 0))

        largura_p = min(680, self.largura_tela - 60)
        altura_p = min(540, self.altura_tela - 60)
        x_p = (self.largura_tela - largura_p) // 2
        y_p = (self.altura_tela - altura_p) // 2

        self.rect_painel_historico = pygame.Rect(x_p, y_p, largura_p, altura_p)
        desenhar_painel_padrao(tela, self.rect_painel_historico, cor_fundo=CARVAO_PROFUNDO, cor_borda=CINZA_LINHO, largura_borda=1, border_radius=4, alpha=252)

        pygame.draw.rect(tela, (28, 28, 36), self.rect_painel_historico.inflate(-10, -10), 1, border_radius=2)

        txt_tit = self.fonte_titulo_modal.render("Histórico de Notificações Recentes", True, MARFIM_OFFWHITE)
        tela.blit(txt_tit, (x_p + (largura_p - txt_tit.get_width()) // 2, y_p + 22))

        self.rect_fechar_historico = pygame.Rect(x_p + largura_p - 46, y_p + 18, 28, 28)
        pos_m = pygame.mouse.get_pos()
        hover_fechar = self.rect_fechar_historico.collidepoint(pos_m)
        pygame.draw.rect(tela, (48, 22, 26) if hover_fechar else (24, 24, 30), self.rect_fechar_historico, border_radius=3)
        pygame.draw.rect(tela, (230, 95, 95) if hover_fechar else CINZA_ARDOSIA, self.rect_fechar_historico, 1, border_radius=3)
        desenhar_icone_fechar(tela, self.rect_fechar_historico, cor=(255, 165, 165) if hover_fechar else CINZA_LINHO, espessura=2)

        pygame.draw.line(tela, CINZA_ARDOSIA, (x_p + 25, y_p + 60), (x_p + largura_p - 25, y_p + 60), 1)

        ultimas_4 = self.historico[-4:] if self.historico else []
        ultimas_4.reverse()

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

                # Caixa de ícone lateral no histórico
                rect_ico_h = pygame.Rect(r_c.x + 12, r_c.centery - 22, 44, 44)
                pygame.draw.rect(tela, (16, 18, 24), rect_ico_h, border_radius=3)
                pygame.draw.rect(tela, notif["cor_borda"], rect_ico_h, 1, border_radius=3)

                if notif.get("tipo") == "CONQUISTA":
                    desenhar_icone_conquista(
                        tela,
                        rect_ico_h,
                        notif.get("id_conquista", ""),
                        cor=notif.get("cor_icone", notif["cor_destaque"]),
                        desbloqueada=True
                    )
                else:
                    desenhar_icone_notificacao(
                        tela,
                        rect_ico_h.centerx,
                        rect_ico_h.centery,
                        tipo=notif.get("tipo", "SISTEMA"),
                        cor=notif["cor_destaque"]
                    )

                t_tit = self.fonte_titulo.render(notif["titulo"], True, notif["cor_destaque"])
                tela.blit(t_tit, (r_c.x + 68, r_c.y + 12))

                tipo_txt = self.fonte_mini.render(f"[{notif['tipo']}]", True, (120, 120, 135))
                tela.blit(tipo_txt, (r_c.right - tipo_txt.get_width() - 16, r_c.y + 14))

                linhas = quebrar_texto_em_linhas(notif["mensagem"], self.fonte_texto_modal, w_c - 85)
                y_txt_m = r_c.y + 38
                for linha in linhas[:2]:
                    t_lin = self.fonte_texto_modal.render(linha, True, MARFIM_OFFWHITE)
                    tela.blit(t_lin, (r_c.x + 68, y_txt_m))
                    y_txt_m += 20

                y_card += h_card + 12

        txt_rod = self.fonte_mini.render("[H] Fechar   |   [ESC] Retomar   |   [Clique Fora] Fechar Histórico", True, CINZA_LINHO)
        tela.blit(txt_rod, (x_p + (largura_p - txt_rod.get_width()) // 2, y_p + altura_p - 30))
