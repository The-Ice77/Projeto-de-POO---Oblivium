# src/ui/ui_utils.py
import pygame
import os
import sys
import math

# Garante que a pasta raiz do projeto ('Oblivium') esteja no sys.path
_raiz_projeto = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _raiz_projeto not in sys.path:
    sys.path.insert(0, _raiz_projeto)

from src.utils.colors import (
    UI_FUNDO_PADRAO, CINZA_CLARO, CINZA_ESCURO, CINZA_ARDOSIA, FUNDO_BARRA,
    UI_TEXTO_DESTAQUE, UI_TEXTO_APAGADO, TXT_SISTEMA_NARRADOR, PRETO, BRANCO,
    CINZA_LINHO, CARVAO_PROFUNDO, MARFIM_OFFWHITE, DOURADO_ENVELHECIDO,
    PERGAMINHO_BG, PERGAMINHO_BORDA, PERGAMINHO_TINTA, PERGAMINHO_TINTA_SUAVE,
    GIZ_SUAVE, AZUL_HOVER_MENU, AZUL_HOVER_BG
)
from src.utils.resource_manager import ResourceManager

def desenhar_painel_padrao(superficie, rect, cor_fundo=UI_FUNDO_PADRAO, cor_borda=CINZA_LINHO, largura_borda=1, border_radius=4, alpha=None):
    """
    Desenha um painel padronizado de UI no padrão editorial e sóbrio de Oblivium.
    Se alpha for fornecido, desenha com transparência controlada.
    """
    if alpha is not None and alpha < 255:
        surf_temp = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        pygame.draw.rect(surf_temp, (*cor_fundo[:3], int(alpha)), (0, 0, rect.width, rect.height), border_radius=border_radius)
        if largura_borda > 0:
            pygame.draw.rect(surf_temp, (*cor_borda[:3], int(alpha)), (0, 0, rect.width, rect.height), largura_borda, border_radius=border_radius)
        superficie.blit(surf_temp, rect.topleft)
    else:
        pygame.draw.rect(superficie, cor_fundo, rect, border_radius=border_radius)
        if largura_borda > 0:
            pygame.draw.rect(superficie, cor_borda, rect, largura_borda, border_radius=border_radius)

def desenhar_card_pergaminho(superficie, rect, cor_fundo=CARVAO_PROFUNDO, cor_borda=CINZA_LINHO, com_filigranas=True, border_radius=3):
    """
    Renderiza um cartão / painel de destaque com contornos finos e pequenas cruzes nos cantos (Dark Souls/Metroidvania style).
    """
    pygame.draw.rect(superficie, cor_fundo, rect, border_radius=border_radius)
    pygame.draw.rect(superficie, cor_borda, rect, 1, border_radius=border_radius)
    
    if com_filigranas and rect.width > 24 and rect.height > 24:
        # Cruzes / Filigranas delicadas de 4px nos cantos
        m = 6
        cantos = [
            (rect.left + m, rect.top + m),
            (rect.right - m, rect.top + m),
            (rect.left + m, rect.bottom - m),
            (rect.right - m, rect.bottom - m)
        ]
        for cx, cy in cantos:
            pygame.draw.line(superficie, cor_borda, (cx - 2, cy), (cx + 2, cy), 1)
            pygame.draw.line(superficie, cor_borda, (cx, cy - 2), (cx, cy + 2), 1)

def desenhar_barra_status_interpolada(superficie, x, y, *args, **kwargs):
    """
    Renderiza uma barra de status com preenchimento interpolado e contorno sutil de 1px.
    Suporta ambas as assinaturas:
      1) (superficie, x, y, valor_atual, valor_maximo, cor_barra, cor_fundo=FUNDO_BARRA, largura=180, altura=12, rotulo_texto=None, fonte=None)
      2) (superficie, x, y, largura, altura, valor_atual, valor_maximo, cor_barra, cor_fundo=..., cor_borda=...)
    """
    # Detecta formato da chamada
    if len(args) >= 4 and isinstance(args[2], (int, float)) and isinstance(args[3], (int, float)):
        # Formato 2: largura, altura, valor_atual, valor_maximo, cor_barra, ...
        largura = args[0]
        altura = args[1]
        valor_atual = args[2]
        valor_maximo = args[3]
        cor_barra = args[4] if len(args) > 4 else BARRA_VIDA_JOGADOR
        cor_fundo = args[5] if len(args) > 5 else kwargs.get("cor_fundo", FUNDO_BARRA)
        cor_borda = args[6] if len(args) > 6 else kwargs.get("cor_borda", CINZA_LINHO)
        rotulo_texto = kwargs.get("rotulo_texto", None)
        fonte = kwargs.get("fonte", None)
    else:
        # Formato 1: valor_atual, valor_maximo, cor_barra, ...
        valor_atual = args[0] if len(args) > 0 else kwargs.get("valor_atual", 100)
        valor_maximo = args[1] if len(args) > 1 else kwargs.get("valor_maximo", 100)
        cor_barra = args[2] if len(args) > 2 else kwargs.get("cor_barra", BARRA_VIDA_JOGADOR)
        cor_fundo = args[3] if len(args) > 3 else kwargs.get("cor_fundo", FUNDO_BARRA)
        largura = kwargs.get("largura", 180)
        altura = kwargs.get("altura", 12)
        cor_borda = kwargs.get("cor_borda", CINZA_LINHO)
        rotulo_texto = kwargs.get("rotulo_texto", None)
        fonte = kwargs.get("fonte", None)

    razao = max(0.0, min(1.0, float(valor_atual) / float(valor_maximo))) if valor_maximo > 0 else 0.0
    largura_atual = int(largura * razao)

    # Fundo da barra
    pygame.draw.rect(superficie, cor_fundo, (x, y, largura, altura), border_radius=2)
    # Preenchimento
    if largura_atual > 0:
        pygame.draw.rect(superficie, cor_barra, (x, y, largura_atual, altura), border_radius=2)
    # Borda fina de 1px
    pygame.draw.rect(superficie, cor_borda, (x, y, largura, altura), 1, border_radius=2)

    # Rótulo de texto centralizado sobre a barra (se fornecido)
    if rotulo_texto and fonte:
        txt = fonte.render(rotulo_texto, True, MARFIM_OFFWHITE)
        tx = x + (largura - txt.get_width()) // 2
        ty = y + (altura - txt.get_height()) // 2
        superficie.blit(txt, (tx, ty))

def quebrar_texto_em_linhas(texto, fonte, largura_maxima):
    """
    Divide uma string em múltiplas linhas respeitando quebras explícitas (\n),
    preservando palavras inteiras e espaços naturais sem gerar overflow ou artefatos.
    """
    if not texto:
        return []

    linhas = []
    # Trata cada parágrafo separado por quebra de linha explícita
    for paragrafo in str(texto).split("\n"):
        palavras = paragrafo.split(" ")
        linha_atual = ""

        for palavra in palavras:
            if not palavra:
                # Preserva múltiplos espaços se houver
                if linha_atual:
                    linha_atual += " "
                continue

            if not linha_atual:
                candidato = palavra
            else:
                candidato = f"{linha_atual} {palavra}"

            if fonte.size(candidato)[0] <= largura_maxima:
                linha_atual = candidato
            else:
                if linha_atual:
                    linhas.append(linha_atual)
                linha_atual = palavra

        if linha_atual:
            linhas.append(linha_atual)
        elif not palavras or paragrafo == "":
            linhas.append("")

    return linhas

def desenhar_tooltip_formatado(superficie, *args, **kwargs):
    """
    Renderiza um cartão de tooltip em pergaminho editorial com tipografia Just Breathe e cantos ornamentados.
    Suporta:
      - (superficie, rect, titulo, descricao, tipo="Item", ...)
      - (superficie, x, y, titulo, descricao, tipo="Item", ...)
    """
    if len(args) > 0 and (isinstance(args[0], pygame.Rect) or (isinstance(args[0], (tuple, list)) and len(args[0]) == 4)):
        rect = pygame.Rect(args[0])
        titulo = args[1] if len(args) > 1 else kwargs.get("titulo", "")
        descricao = args[2] if len(args) > 2 else kwargs.get("descricao", "")
        tipo = args[3] if len(args) > 3 else kwargs.get("tipo", "Item")
        atributos = args[4] if len(args) > 4 else kwargs.get("atributos", None)
    else:
        x = args[0] if len(args) > 0 else kwargs.get("x", 0)
        y = args[1] if len(args) > 1 else kwargs.get("y", 0)
        titulo = args[2] if len(args) > 2 else kwargs.get("titulo", "")
        descricao = args[3] if len(args) > 3 else kwargs.get("descricao", "")
        tipo = args[4] if len(args) > 4 else kwargs.get("tipo", "Item")
        atributos = args[5] if len(args) > 5 else kwargs.get("atributos", None)
        
        # Ajusta dimensões automáticas do tooltip
        largura_t = 280
        altura_t = 120 if not atributos else 120 + len(atributos) * 22
        
        # Garante que não ultrapasse os limites da tela
        if x + largura_t > superficie.get_width():
            x = superficie.get_width() - largura_t - 10
        if y + altura_t > superficie.get_height():
            y = superficie.get_height() - altura_t - 10
            
        rect = pygame.Rect(x, y, largura_t, altura_t)

    f_tit = kwargs.get("fonte_tit") or ResourceManager.carregar_fonte("sunday", 22)
    f_desc = kwargs.get("fonte_desc") or ResourceManager.carregar_fonte("just_breathe", 18)
    f_stat = kwargs.get("fonte_stat") or ResourceManager.carregar_fonte("contrail", 16)

    desenhar_card_pergaminho(superficie, rect, CARVAO_PROFUNDO, CINZA_LINHO, com_filigranas=True)
    
    # 1. Título do Item
    r_tit = f_tit.render(titulo, True, MARFIM_OFFWHITE)
    superficie.blit(r_tit, (rect.x + 14, rect.y + 12))
    
    # 2. Subtítulo / Tipo
    r_tipo = f_desc.render(tipo, True, CINZA_LINHO)
    superficie.blit(r_tipo, (rect.x + 14, rect.y + 12 + r_tit.get_height() + 2))
    
    y_atual = rect.y + 12 + r_tit.get_height() + r_tipo.get_height() + 8
    
    # 3. Descrição poética com quebra de linha
    if descricao:
        linhas = quebrar_texto_em_linhas(descricao, f_desc, rect.width - 28)
        for l in linhas:
            r_l = f_desc.render(l, True, CINZA_CLARO)
            superficie.blit(r_l, (rect.x + 14, y_atual))
            y_atual += 18
        y_atual += 6

    # 4. Atributos (+12 Ataque Mágico, etc.)
    if atributos:
        for attr in atributos:
            r_attr = f_stat.render(f"✦ {attr}", True, MARFIM_OFFWHITE)
            superficie.blit(r_attr, (rect.x + 14, y_atual))
            y_atual += 18

def desenhar_indicador_tecla(superficie, x, y, tecla="E", acao="para interagir", fonte=None):
    """
    Renderiza o badge retangular nítido de tecla de ação: [ Pressione E para interagir ].
    Formato estritamente retangular com contorno fino de 1px sem artefatos visuais.
    """
    f = fonte or ResourceManager.carregar_fonte("contrail", 16)
    txt_prefixo = "Pressione "
    txt_tecla = f" {tecla} "
    txt_sufixo = f" {acao}"

    r_pre = f.render(txt_prefixo, True, GIZ_SUAVE)
    r_tec = f.render(txt_tecla, True, MARFIM_OFFWHITE)
    r_suf = f.render(txt_sufixo, True, GIZ_SUAVE)

    largura_total = r_pre.get_width() + r_tec.get_width() + 10 + r_suf.get_width() + 20
    altura_box = 28
    rect_box = pygame.Rect(x - largura_total // 2, y, largura_total, altura_box)

    # Fundo retangular sólido e borda nítida de 1px
    pygame.draw.rect(superficie, (10, 10, 14), rect_box)
    pygame.draw.rect(superficie, CINZA_LINHO, rect_box, 1)

    # Desenho dos textos e caixa da tecla
    cur_x = rect_box.x + 10
    superficie.blit(r_pre, (cur_x, rect_box.centery - r_pre.get_height() // 2))
    cur_x += r_pre.get_width()

    # Caixa da tecla
    tec_box = pygame.Rect(cur_x, rect_box.centery - 9, r_tec.get_width() + 4, 18)
    pygame.draw.rect(superficie, (26, 34, 46), tec_box)
    pygame.draw.rect(superficie, AZUL_HOVER_MENU, tec_box, 1)
    superficie.blit(r_tec, (tec_box.x + 2, tec_box.centery - r_tec.get_height() // 2))
    cur_x += tec_box.width + 4

    superficie.blit(r_suf, (cur_x, rect_box.centery - r_suf.get_height() // 2))

def desenhar_flor_botanica(superficie, cx, cy, raio=10, cor=MARFIM_OFFWHITE, escala=1.0):
    """
    Desenha proceduralmente uma flor/buquê botânico minimalista estilizado (5 pétalas ovais + centro).
    """
    raio_efetivo = max(3, int(raio * escala))
    for i in range(5):
        ang = math.radians(i * (360 / 5) - 90)
        px = cx + int(math.cos(ang) * raio_efetivo * 0.7)
        py = cy + int(math.sin(ang) * raio_efetivo * 0.7)
        pygame.draw.circle(superficie, cor, (px, py), max(2, int(raio_efetivo * 0.45)), 1)
    pygame.draw.circle(superficie, cor, (cx, cy), max(1, int(raio_efetivo * 0.25)))


class BotaoGrafico:
    """
    Componente POO de botão visual que suporta imagens de estado normal e hover,
    transição interpolada suave, efeitos de pulso e fallback procedural para texto.
    """
    def __init__(self, identificador, imagem_normal=None, imagem_hover=None, x=0, y=0, fonte_fallback=None):
        self.identificador = identificador
        self.imagem_normal = imagem_normal
        self.imagem_hover = imagem_hover
        self.fonte_fallback = fonte_fallback or ResourceManager.carregar_fonte("contrail", 38)
        
        self.x = x
        self.y = y
        self.hover_progresso = 0.0
        self.timer_animacao = 0.0
        
        self._recalcular_rect()

    def _recalcular_rect(self):
        if self.imagem_normal:
            w = self.imagem_normal.get_width()
            h = self.imagem_normal.get_height()
        elif self.imagem_hover:
            w = self.imagem_hover.get_width()
            h = self.imagem_hover.get_height()
        else:
            w, h = self.fonte_fallback.size(self.identificador)
            
        self.rect = pygame.Rect(self.x, self.y, w, h)

    def definir_posicao(self, x, y):
        self.x = x
        self.y = y
        self._recalcular_rect()

    def atualizar(self, esta_selecionado_ou_hover, dt=0.016):
        alvo = 1.0 if esta_selecionado_ou_hover else 0.0
        velocidade = 7.0
        
        if self.hover_progresso < alvo:
            self.hover_progresso = min(alvo, self.hover_progresso + velocidade * dt)
        elif self.hover_progresso > alvo:
            self.hover_progresso = max(alvo, self.hover_progresso - velocidade * dt)
            
        if self.hover_progresso > 0.01:
            self.timer_animacao += dt * 3.5
        else:
            self.timer_animacao = 0.0

    def colide(self, pos_mouse):
        return self.rect.collidepoint(pos_mouse)

    def desenhar(self, superficie, selecionado=False):
        if self.imagem_normal and self.imagem_hover:
            progresso = 1.0 if selecionado else self.hover_progresso
            
            alpha_norm = int(255 * (1.0 - progresso))
            if alpha_norm > 5:
                if alpha_norm >= 250:
                    superficie.blit(self.imagem_normal, (self.x, self.y))
                else:
                    surf_norm = self.imagem_normal.copy()
                    surf_norm.set_alpha(alpha_norm)
                    superficie.blit(surf_norm, (self.x, self.y))

            if progresso > 0.02:
                fator_brilho = 0.94 + 0.06 * math.sin(self.timer_animacao)
                alpha_hov = int(255 * progresso * fator_brilho)
                alpha_hov = max(0, min(255, alpha_hov))
                
                hx = self.rect.centerx - self.imagem_hover.get_width() // 2
                hy = self.rect.centery - self.imagem_hover.get_height() // 2
                
                if alpha_hov >= 250:
                    superficie.blit(self.imagem_hover, (hx, hy))
                else:
                    surf_hov = self.imagem_hover.copy()
                    surf_hov.set_alpha(alpha_hov)
                    superficie.blit(surf_hov, (hx, hy))
                
        elif self.imagem_normal:
            superficie.blit(self.imagem_normal, (self.x, self.y))
        else:
            cor = UI_TEXTO_DESTAQUE if (selecionado or self.hover_progresso > 0.5) else UI_TEXTO_APAGADO
            prefixo = "✦ " if (selecionado or self.hover_progresso > 0.5) else "  "
            sufixo = " ✦" if (selecionado or self.hover_progresso > 0.5) else ""
            txt_render = self.fonte_fallback.render(f"{prefixo}{self.identificador}{sufixo}", True, cor)
            superficie.blit(txt_render, (self.x, self.y))

def desenhar_badge_status(superficie, x, y, texto, cor_texto=MARFIM_OFFWHITE, cor_fundo=CARVAO_PROFUNDO, cor_borda=CINZA_LINHO):
    """Renderiza um badge/selo de status de combate compacto."""
    fonte = ResourceManager.carregar_fonte("contrail", 14)
    r_txt = fonte.render(texto, True, cor_texto)
    w = r_txt.get_width() + 12
    h = r_txt.get_height() + 6
    rect = pygame.Rect(x, y, w, h)
    pygame.draw.rect(superficie, cor_fundo, rect, border_radius=2)
    pygame.draw.rect(superficie, cor_borda, rect, 1, border_radius=2)
    superficie.blit(r_txt, (x + 6, y + 3))
    return rect


