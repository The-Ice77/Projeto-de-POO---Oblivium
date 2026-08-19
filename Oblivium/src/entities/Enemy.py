# src/entities/Enemy.py
import pygame
from src.entities.Entity import Entidade 

class Enemy(Entidade):
    # Aceitamos o 'sprite' na assinatura para não quebrar instâncias antigas, mas não o usamos
    def __init__(self, nome, vida_maxima, velocidade, x, y, sprite=None, dano=10, agressivo=True):
        
        # Chama a classe mãe (Entidade) usando a nova assinatura sem sprite
        super().__init__(nome, vida_maxima, x, y, velocidade)

        # Atributos exclusivos do inimigo
        self.dano = dano
        self.agressivo = agressivo
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
        if not getattr(self, 'vivo', True) or not getattr(self, 'agressivo', True):
            return

        dx_alvo = alvo_x - self.x
        dy_alvo = alvo_y - self.y
        distancia_alvo = (dx_alvo**2 + dy_alvo**2) ** 0.5
        
        if distancia_alvo < 500: 
            self.alvo_detectado = True
        
        vetor_x, vetor_y = 0, 0
        if getattr(self, 'alvo_detectado', False) and distancia_alvo > 0:
            vetor_x = (dx_alvo / distancia_alvo) * self.velocidade
            vetor_y = (dy_alvo / distancia_alvo) * self.velocidade

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

        tamanho_vetor = (vetor_x**2 + vetor_y**2) ** 0.5
        if tamanho_vetor > 0:
            vetor_x = (vetor_x / tamanho_vetor) * self.velocidade
            vetor_y = (vetor_y / tamanho_vetor) * self.velocidade

        # Utiliza o método mover herdado de Entidade para atualizar a direção (virado_direita) de forma segura
        if hasattr(self, 'mover'):
            # Passamos [] para as hitboxes para ele andar livremente, 
            # mas aproveitamos a atualização do estado da animação e da direção
            self.mover(vetor_x, vetor_y, [])
        else:
            self.x += vetor_x
            self.y += vetor_y

    # --- SISTEMA DE RENDERIZAÇÃO ROBUSTO ---
    # --- SISTEMA DE RENDERIZAÇÃO ROBUSTO ---
    def desenhar(self, tela):
        if not getattr(self, 'vivo', True):
            return
            
        if hasattr(self, 'atualizar_animacao'):
            self.atualizar_animacao()
            
        imagem = getattr(self, 'imagem_atual', None)
            
        if imagem:
            tela.blit(imagem, (int(self.x), int(self.y)))
        else:
            # Fallback limpo
            largura_segura = getattr(self, 'largura', 40)
            altura_segura = getattr(self, 'altura', 40)
            cor_segura = getattr(self, 'cor', (150, 30, 50))
            
            retangulo = pygame.Rect(int(self.x), int(self.y), largura_segura, altura_segura)
            pygame.draw.rect(tela, cor_segura, retangulo)
            pygame.draw.rect(tela, (50, 0, 0), retangulo, 2)

    # --- SISTEMA DE COMBATE LÓGICO ---
    def atacar(self, alvo):
        if not getattr(self, 'vivo', True):
            return
        # Busca o dano de forma segura, se não existir aplica 0
        alvo.receber_dano(getattr(self, 'dano', 0))

    def morrer(self):
        self.vivo = False

    def mostrar_status(self):
        print("<-- ENEMY -->")
        print(f"Nome: {getattr(self, 'nome', 'Desconhecido')}")
        print(f"Dano: {getattr(self, 'dano', 0)}")
        print(f"Posição: ({self.x}, {self.y})")