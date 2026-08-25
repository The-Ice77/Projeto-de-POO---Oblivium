# src/entities/NPC.py
import pygame
from src.entities.Entity import Entidade

class NPC(Entidade):
    def __init__(self, nome, x, y, velocidade=0, vida_maxima=999):
        super().__init__(nome, vida_maxima, x, y, velocidade)
        
        # Lista de falas que este NPC vai dizer ao jogador
        self.dialogos = []

    def definir_dialogos(self, lista_dialogos):
        """Define o que o NPC vai falar ao interagir."""
        self.dialogos = lista_dialogos

    def desenhar(self, tela):
        # Utiliza o método desenhar herdado da Entidade se houver sprites
        if self.imagem_atual or self.animacoes.get(self.estado_atual).frames:
            super().desenhar(tela)
        else:
            # Retângulo provisório azul-esverdeado para os NPCs do mundo cinza
            rect_npc = pygame.Rect(int(self.x), int(self.y), self.largura, self.altura)
            pygame.draw.rect(tela, (70, 90, 100), rect_npc)
            pygame.draw.rect(tela, (100, 120, 130), rect_npc, 2)