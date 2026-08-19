# src/entities/item.py
import pygame

class Item:
    def __init__(self, nome, x, y, largura=20, altura=20, cor=(200, 200, 200), sprite=None):
        self.nome = nome
        self.x = float(x)
        self.y = float(y)
        self.largura = largura
        self.altura = altura
        self.cor = cor 
        
        self.rect = pygame.Rect(self.x, self.y, self.largura, self.altura)
        
        # --- SUPORTE A SPRITES ---
        self.imagem = sprite
        if self.imagem:
            # Garante que a imagem tenha o tamanho correto da hitbox
            self.imagem = pygame.transform.scale(self.imagem, (self.largura, self.altura))
        
    def desenhar(self, tela):
        if self.imagem:
            tela.blit(self.imagem, (int(self.x), int(self.y)))
        else:
            # Fallback visual (Retângulo provisório)
            pygame.draw.rect(tela, self.cor, self.rect)
            pygame.draw.rect(tela, (150, 150, 150), self.rect, 1)