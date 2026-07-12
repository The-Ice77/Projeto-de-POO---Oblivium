# src/entities/item.py
import pygame

class Item:
    def __init__(self, nome, x, y, largura=20, altura=20, cor=(200, 200, 200)):
        self.nome = nome
        self.x = x
        self.y = y
        self.largura = largura
        self.altura = altura
        
        # Cor provisória desbotada (para combinar com o mundo cinza)
        self.cor = cor 
        
        # Hitbox física do item no mapa
        self.rect = pygame.Rect(x, y, largura, altura)
        
    def desenhar(self, tela):
        pygame.draw.rect(tela, self.cor, self.rect)
        # Uma bordinha branca para destacar no chão escuro
        pygame.draw.rect(tela, (150, 150, 150), self.rect, 1)