import pygame
from entities.Entity import Entidade 

class Enemy(Entidade):
    def __init__(self, nome, vida_maxima, velocidade, x, y, sprite, dano, agressivo):
        # CORREÇÃO VITAL: A ordem agora respeita (nome, vida_maxima, x, y, velocidade, sprite)
        super().__init__(nome, vida_maxima, x, y, velocidade, sprite)

        # Atributos exclusivos do inimigo
        self.dano = dano
        self.agressivo = agressivo

        # Estado do inimigo
        self.alvo_detectado = False
        
        # --- ATRIBUTOS DE RENDERIZAÇÃO (FALLBACK) ---
        if "Anomalia" in self.nome:
            self.largura = 55
            self.altura = 75
            self.cor = (150, 0, 200) 
        else:
            self.largura = 35
            self.altura = 45
            self.cor = (150, 30, 50) 

    # --- SISTEMA DE MOVIMENTO NO MAPA (Pré-Combate) ---
    def atualizar_movimento_mapa(self, alvo_x, alvo_y):
        if not getattr(self, 'vivo', True) or not self.agressivo:
            return

        dx = alvo_x - self.x
        dy = alvo_y - self.y
        distancia = (dx**2 + dy**2) ** 0.5
        
        if distancia < 500: 
            self.alvo_detectado = True
        
        if self.alvo_detectado and distancia > 0:
            self.x += (dx / distancia) * self.velocidade
            self.y += (dy / distancia) * self.velocidade

    # --- SISTEMA DE RENDERIZAÇÃO ---
    def desenhar(self, tela):
        if not getattr(self, 'vivo', True):
            return
            
        if self.sprite:
            tela.blit(self.sprite, (int(self.x), int(self.y)))
        else:
            retangulo = pygame.Rect(int(self.x), int(self.y), self.largura, self.altura)
            pygame.draw.rect(tela, self.cor, retangulo)
            pygame.draw.rect(tela, (50, 0, 0), retangulo, 2) 

    # --- SISTEMA DE COMBATE LÓGICO ---
    def atacar(self, alvo):
        if not getattr(self, 'vivo', True):
            return
        alvo.receber_dano(self.dano)

    def morrer(self):
        self.vivo = False

    def mostrar_status(self):
        print("<-- ENEMY -->")
        print(f"Nome: {self.nome}")
        print(f"Dano: {self.dano}")
        print(f"Posição: ({self.x}, {self.y})")