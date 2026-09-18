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


class BotaoGrafico:
    """
    Componente POO de botão visual que suporta imagens de estado normal e hover,
    transição interpolada suave, efeitos de pulso e fallback procedural para texto.
    """
    def __init__(self, identificador, imagem_normal=None, imagem_hover=None, x=0, y=0, fonte_fallback=None):
        self.identificador = identificador
        self.imagem_normal = imagem_normal
        self.imagem_hover = imagem_hover
        self.fonte_fallback = fonte_fallback or pygame.font.Font(None, 40)
        
        self.x = x
        self.y = y
        self.hover_progresso = 0.0  # 0.0 (normal) a 1.0 (totalmente hover)
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
        velocidade = 7.0  # Transição suave e fluida
        
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
        import math
        # Se temos sprites estilizados para normal e hover
        if self.imagem_normal and self.imagem_hover:
            progresso = 1.0 if selecionado else self.hover_progresso
            
            # 1. Renderiza o botão normal com fade-out suave
            alpha_norm = int(255 * (1.0 - progresso))
            if alpha_norm > 5:
                if alpha_norm >= 250:
                    superficie.blit(self.imagem_normal, (self.x, self.y))
                else:
                    surf_norm = self.imagem_normal.copy()
                    surf_norm.set_alpha(alpha_norm)
                    superficie.blit(surf_norm, (self.x, self.y))

            # 2. Renderiza a versão hover com fade-in suave e respiração orgânica
            if progresso > 0.02:
                fator_brilho = 0.94 + 0.06 * math.sin(self.timer_animacao)
                alpha_hov = int(255 * progresso * fator_brilho)
                alpha_hov = max(0, min(255, alpha_hov))
                
                # Alinha o centro do sprite de hover perfeitamente com o centro da hitbox
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
            # Fallback procedural
            cor = UI_TEXTO_DESTAQUE if (selecionado or self.hover_progresso > 0.5) else UI_TEXTO_APAGADO
            prefixo = "> " if (selecionado or self.hover_progresso > 0.5) else ""
            txt_render = self.fonte_fallback.render(f"{prefixo}{self.identificador}", True, cor)
            superficie.blit(txt_render, (self.x, self.y))
