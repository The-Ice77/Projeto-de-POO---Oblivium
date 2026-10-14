# src/entities/NPC.py
import pygame
from src.entities.Entity import Entidade

class NPC(Entidade):
    def __init__(self, nome, x, y, velocidade=0, vida_maxima=999):
        super().__init__(nome, vida_maxima, x, y, velocidade)
        
        # Identificador do diálogo no JSON ou lista de falas diretas
        self.dialogos = []
        self.dialogo_id = None

    def definir_dialogos(self, lista_ou_id):
        """Define o que o NPC vai falar ao interagir (aceita ID em string ou lista)."""
        if isinstance(lista_ou_id, str):
            self.dialogo_id = lista_ou_id
        self.dialogos = lista_ou_id

    def desenhar(self, tela):
        # Utiliza o método desenhar herdado da Entidade se houver sprites
        anim = self.animacoes.get(self.estado_atual)
        if self.imagem_atual or (anim and getattr(anim, 'frames', None)):
            super().desenhar(tela)
        else:
            # Retângulo provisório azul-esverdeado para os NPCs do mundo cinza
            rect_npc = pygame.Rect(int(self.x), int(self.y), self.largura, self.altura)
            pygame.draw.rect(tela, (70, 90, 100), rect_npc)
            pygame.draw.rect(tela, (100, 120, 130), rect_npc, 2)