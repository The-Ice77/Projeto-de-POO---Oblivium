# src/ui/ui_utils.py
import pygame
import os
import sys

# Garante que a pasta raiz do projeto ('Oblivium') esteja no sys.path
_raiz_projeto = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _raiz_projeto not in sys.path:
    sys.path.insert(0, _raiz_projeto)

from src.utils.colors import (
    UI_FUNDO_PADRAO, CINZA_CLARO, CINZA_ESCURO, FUNDO_BARRA,
    UI_TEXTO_DESTAQUE, UI_TEXTO_APAGADO, TXT_SISTEMA_NARRADOR, PRETO, BRANCO
)

def desenhar_painel_padrao(superficie, rect, cor_fundo=UI_FUNDO_PADRAO, cor_borda=CINZA_CLARO, largura_borda=1, border_radius=0):
    """
    Desenha um painel padronizado de UI no padrão sóbrio de Oblivium.
    """
    pygame.draw.rect(superficie, cor_fundo, rect, border_radius=border_radius)
    if largura_borda > 0:
        pygame.draw.rect(superficie, cor_borda, rect, largura_borda, border_radius=border_radius)

def desenhar_barra_status_interpolada(superficie, x, y, valor_atual, valor_maximo, cor_barra, cor_fundo=FUNDO_BARRA, largura=180, altura=12):
    """
    Renderiza uma barra de status com visual consistente, preenchimento interpolado e contorno.
    """
    razao = max(0.0, min(1.0, valor_atual / valor_maximo)) if valor_maximo > 0 else 0.0
    largura_atual = int(largura * razao)

    # Fundo da barra
    pygame.draw.rect(superficie, cor_fundo, (x, y, largura, altura))
    # Preenchimento
    if largura_atual > 0:
        pygame.draw.rect(superficie, cor_barra, (x, y, largura_atual, altura))
    # Borda fina
    pygame.draw.rect(superficie, CINZA_CLARO, (x, y, largura, altura), 1)

def quebrar_texto_em_linhas(texto, fonte, largura_maxima):
    """
    Divide uma string em múltiplas linhas preservando palavras inteiras para que caibam na largura máxima.
    """
    palavras = str(texto).split(" ")
    linhas = []
    linha_atual = ""

    for palavra in palavras:
        teste = f"{linha_atual} {palavra}".strip()
        if fonte.size(teste)[0] <= largura_maxima:
            linha_atual = teste
        else:
            if linha_atual:
                linhas.append(linha_atual)
            linha_atual = palavra

    if linha_atual:
        linhas.append(linha_atual)

    return linhas

def desenhar_tooltip_formatado(superficie, rect, texto, fonte, cor_fundo=(20, 20, 25), cor_borda=CINZA_CLARO, cor_texto=UI_TEXTO_DESTAQUE):
    """
    Renderiza uma caixa de detalhes / tooltip elegante com texto centralizado verticalmente.
    """
    pygame.draw.rect(superficie, cor_fundo, rect)
    pygame.draw.rect(superficie, cor_borda, rect, 1)

    txt_render = fonte.render(texto, True, cor_texto)
    pos_y = rect.y + (rect.height - txt_render.get_height()) // 2
    superficie.blit(txt_render, (rect.x + 12, pos_y))

def desenhar_badge_status(superficie, x, y, icone, duracao, fonte, cor=TXT_SISTEMA_NARRADOR):
    """
    Renderiza o badge compacto de condição ativa (ex: '✦:2').
    """
    texto = f"{icone}:{duracao}"
    txt_render = fonte.render(texto, True, cor)
    superficie.blit(txt_render, (x, y))
    return txt_render.get_width()
