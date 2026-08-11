# Candidata a ser abstrata

import pygame
import math

class Entidade:
    def __init__(self, nome, vida_maxima, x, y, velocidade, sprite):
        self.nome = nome
        self.vida_maxima = vida_maxima
        self.vida_atual = vida_maxima
        self.x = float(x)
        self.y = float(y)
        self.velocidade = velocidade
        self.sprite = sprite
        self.vivo = True
        
        # Dimensões provisórias da Hitbox da entidade
        self.largura = 40
        self.altura = 40
    
    def mover(self, dx, dy, hitboxes_mapa):
        if not self.vivo or (dx == 0 and dy == 0):
            return
            
        tamanho = math.hypot(dx, dy)
        dx = dx / tamanho
        dy = dy / tamanho
        
        # movimento e colisão no x
        self.x += dx * self.velocidade
        rect_teste_x = pygame.Rect(int(self.x), int(self.y), self.largura, self.altura)
        
        for parede in hitboxes_mapa:
            if rect_teste_x.colliderect(parede):
                if dx > 0: # Batendo na parede indo para a direita
                    self.x = parede.left - self.largura
                elif dx < 0: # Batendo na parede indo para a esquerda
                    self.x = parede.right

        # movimento e colisão no y
        self.y += dy * self.velocidade
        rect_teste_y = pygame.Rect(int(self.x), int(self.y), self.largura, self.altura)
        
        for parede in hitboxes_mapa:
            if rect_teste_y.colliderect(parede):
                if dy > 0: # Batendo na parede indo para baixo
                    self.y = parede.top - self.altura
                elif dy < 0: # Batendo na parede indo para cima
                    self.y = parede.bottom

 

    # opção para se desenhar
    def desenhar(self, tela):
        if not self.vivo:
            return # Opcional: não desenhar se estiver morto ou desenhar indicativo de morto ( caveira )
            
        if self.sprite is not None:
            # Quando tiver a pixel art pronta
            tela.blit(self.sprite, (int(self.x), int(self.y)))
        else:
            # Retângulo provisório caso não tenha sprite definido
            # O player pode ser verde, inimigos podem ser vermelhos futuramente
            pygame.draw.rect(tela, (34, 139, 34), (int(self.x), int(self.y), 40, 40))
    
    # sistema de dano
    def receber_dano(self, dano):
        if not self.vivo:
            print(f"{self.nome} já está morto")
            return
        
        self.vida_atual -= dano

        # CORREÇÃO: Estava self.vida em vez de self.vida_atual
        if self.vida_atual <= 0:
            self.vida_atual = 0
            self.vivo = False
            self.morrer()
    
    # sistema de cura
    def curar(self, cura):
        if not self.vivo:
            print(f'{self.nome} não pode receber cura')
            return
        
        self.vida_atual += cura
        
        if self.vida_atual > self.vida_maxima:
            self.vida_atual = self.vida_maxima

        print(f'{self.nome} recuperou {cura} de vida. Vida atual: {self.vida_atual}/{self.vida_maxima}')
    
    # sistema de morte
    def morrer(self):
        print(f'{self.nome} foi derrotado!')

    def mostrar_status(self):
        print("<-- Status -->")
        print(f"Nome: {self.nome}")
        print(f"Vida: {self.vida_atual}/{self.vida_maxima}")
        print(f"Posição: ({int(self.x)}, {int(self.y)})")
        print(f"Velocidade: {self.velocidade}")
        print(f'Estado: {"Vivo" if self.vivo else "Morto"}')
