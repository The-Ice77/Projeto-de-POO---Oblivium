# src/entities/npc.py
import pygame

class NPC:
    def __init__(self, nome, x, y, velocidade=0, sprite=None):
        self.nome = nome
        self.x = float(x)
        self.y = float(y)
        self.velocidade = velocidade
        self.sprite = sprite
        self.vivo = True
        
        # Dimensões da hitbox do NPC para interação
        self.largura = 40
        self.altura = 40
        
        # Lista de falas que este NPC vai dizer ao jogador
        self.dialogos = []

    def definir_dialogos(self, lista_dialogos):
        """Define o que o NPC vai falar ao interagir."""
        self.dialogos = lista_dialogos

    def mover(self, dx, dy):
        if not self.vivo or self.velocidade == 0:
            return
        self.x += dx * self.velocidade
        self.y += dy * self.velocidade

    def desenhar(self, tela):
        if not self.vivo:
            return
            
        if self.sprite is not None:
            tela.blit(self.sprite, (int(self.x), int(self.y)))
        else:
            # Retângulo provisório azul-esverdeado para os NPCs do mundo cinza
            rect_npc = pygame.Rect(int(self.x), int(self.y), self.largura, self.altura)
            pygame.draw.rect(tela, (70, 90, 100), rect_npc)
            pygame.draw.rect(tela, (100, 120, 130), rect_npc, 2)