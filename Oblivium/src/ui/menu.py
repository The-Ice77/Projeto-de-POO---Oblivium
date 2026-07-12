# src/ui/menu.py
import pygame
from src.utils.colors import UI_FUNDO_PADRAO, UI_TEXTO_APAGADO, UI_TEXTO_DESTAQUE

class Menu:
    def __init__(self):
        self.opcoes = ["Jogar", "Créditos", "Sair"]
        self.selecionada = 0
        self.fonte_titulo = pygame.font.Font(None, 80)
        self.fonte_subtitulo = pygame.font.Font(None, 40)
        self.fonte_menu = pygame.font.Font(None, 50)
        
        # Vinculado diretamente à paleta de cores unificada do arquivo utils/colors.py
        self.cor_fundo = UI_FUNDO_PADRAO
        self.cor_texto = UI_TEXTO_APAGADO
        self.cor_destaque = UI_TEXTO_DESTAQUE
        
        # Lista para guardar a posição (hitbox) de cada opção no ecrã
        self.rects_opcoes = []

    def desenhar(self, tela):
        tela.fill(self.cor_fundo)
        
        # Títulos alinhados na lateral (Margem esquerda = 80 pixels)
        margem_x = 80
        
        titulo = self.fonte_titulo.render("Oblivium", True, self.cor_destaque)
        subtitulo = self.fonte_subtitulo.render("Um Jogo Sobre Lembrar", True, self.cor_texto)
        
        tela.blit(titulo, (margem_x, 100))
        tela.blit(subtitulo, (margem_x, 160))

        # Limpar os retângulos antigos antes de desenhar o novo frame
        self.rects_opcoes.clear()

        # Desenhar opções do menu
        for i, opcao in enumerate(self.opcoes):
            if i == self.selecionada:
                texto = f"> {opcao}"
                cor = self.cor_destaque
            else:
                texto = opcao
                cor = self.cor_texto

            render = self.fonte_menu.render(texto, True, cor)
            
            # Posição lateral das opções
            x = margem_x
            y = 300 + i * 60
            
            tela.blit(render, (x, y))
            
            # Criar um rect invisível do tamanho exato da palavra e guardar
            rect = pygame.Rect(x, y, render.get_width(), render.get_height())
            self.rects_opcoes.append(rect)

    def atualizar_mouse(self, pos_mouse):
        for i, rect in enumerate(self.rects_opcoes):
            if rect.collidepoint(pos_mouse):
                self.selecionada = i

    def clicar_mouse(self, pos_mouse):
        for i, rect in enumerate(self.rects_opcoes):
            if rect.collidepoint(pos_mouse):
                return self.opcoes[i]
        return None