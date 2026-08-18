import pygame
from src.entities.Entity import Entidade 

class Enemy(Entidade):
    def __init__(self, nome, vida_maxima, velocidade, x, y, sprite, dano, agressivo):
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
    def atualizar_movimento_mapa(self, alvo_x, alvo_y, lista_inimigos=None):
        if not getattr(self, 'vivo', True) or not self.agressivo:
            return

        # 1. Movimento em direção ao Alvo (Halia)
        dx_alvo = alvo_x - self.x
        dy_alvo = alvo_y - self.y
        distancia_alvo = (dx_alvo**2 + dy_alvo**2) ** 0.5
        
        if distancia_alvo < 500: 
            self.alvo_detectado = True
        
        vetor_x, vetor_y = 0, 0
        if self.alvo_detectado and distancia_alvo > 0:
            vetor_x = (dx_alvo / distancia_alvo) * self.velocidade
            vetor_y = (dy_alvo / distancia_alvo) * self.velocidade

        # 2. Separação (Evitar sobreposição com outros inimigos)
        if lista_inimigos:
            distancia_minima = 70 
            for outro in lista_inimigos:
                if outro is not self: 
                    dx_outro = self.x - outro.x
                    dy_outro = self.y - outro.y
                    dist_outro = (dx_outro**2 + dy_outro**2) ** 0.5
                    
                    if dist_outro < distancia_minima and dist_outro > 0:
                        
                        fator_repulsao = (distancia_minima - dist_outro) / distancia_minima
                        
                        vetor_x += (dx_outro / dist_outro) * (self.velocidade * fator_repulsao * 2)
                        vetor_y += (dy_outro / dist_outro) * (self.velocidade * fator_repulsao * 2)

        # Normalizar o vetor final para não andar rápido demais na diagonal
        tamanho_vetor = (vetor_x**2 + vetor_y**2) ** 0.5
        if tamanho_vetor > 0:
            vetor_x = (vetor_x / tamanho_vetor) * self.velocidade
            vetor_y = (vetor_y / tamanho_vetor) * self.velocidade

        self.x += vetor_x
        self.y += vetor_y

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