# src/entities/Entity.py
import pygame
import math

class Entidade:
    def __init__(self, nome, vida_maxima, x, y, velocidade):
        self.nome = nome
        self.vida_maxima = vida_maxima
        self.vida_atual = vida_maxima
        self.x = float(x)
        self.y = float(y)
        self.velocidade = velocidade
        self.vivo = True
        
        self.largura = 40
        self.altura = 40
        
        # ==========================================
        # SISTEMA DE ANIMAÇÃO E SPRITES
        # ==========================================
        # Dicionário que guardará listas de superfícies (frames) por estado
        self.animacoes = {
            "idle": [],
            "andar": [],
            "atacar": [],
            "morrer": []
        }
        
        self.estado_atual = "idle"
        self.frame_atual = 0.0
        self.velocidade_animacao = 0.15  # Quão rápido os frames passam
        self.virado_direita = True       # Controla o flip horizontal da imagem
        
        # Imagem atual a ser renderizada
        self.imagem_atual = None

    def atualizar_animacao(self):
        """Atualiza o frame atual da animação baseada no estado da entidade."""
        if not self.vivo and self.estado_atual != "morrer":
            self.mudar_estado("morrer")
            
        frames_estado = self.animacoes.get(self.estado_atual, [])
        
        if frames_estado:
            self.frame_atual += self.velocidade_animacao
            
            # Se a animação chegou ao fim
            if self.frame_atual >= len(frames_estado):
                if self.estado_atual == "morrer":
                    self.frame_atual = len(frames_estado) - 1 # Trava no último frame morto
                else:
                    self.frame_atual = 0.0 # Faz o loop da animação
                    
            imagem_base = frames_estado[int(self.frame_atual)]
            
            # Espelha a imagem se estiver virado para a esquerda
            if not self.virado_direita:
                self.imagem_atual = pygame.transform.flip(imagem_base, True, False)
            else:
                self.imagem_atual = imagem_base
        else:
            self.imagem_atual = None

    def mudar_estado(self, novo_estado):
        """Altera o estado da animação e reseta o frame se o estado for novo."""
        if self.estado_atual != novo_estado:
            self.estado_atual = novo_estado
            self.frame_atual = 0.0

    def mover(self, dx, dy, hitboxes_mapa):
        if not self.vivo or (dx == 0 and dy == 0):
            self.mudar_estado("idle")
            return
            
        self.mudar_estado("andar")
        
        # Define para onde a entidade está a olhar
        if dx > 0:
            self.virado_direita = True
        elif dx < 0:
            self.virado_direita = False
            
        tamanho = math.hypot(dx, dy)
        dx = dx / tamanho
        dy = dy / tamanho
        
        self.x += dx * self.velocidade
        rect_teste_x = pygame.Rect(int(self.x), int(self.y), self.largura, self.altura)
        
        for parede in hitboxes_mapa:
            if rect_teste_x.colliderect(parede):
                if dx > 0: self.x = parede.left - self.largura
                elif dx < 0: self.x = parede.right

        self.y += dy * self.velocidade
        rect_teste_y = pygame.Rect(int(self.x), int(self.y), self.largura, self.altura)
        
        for parede in hitboxes_mapa:
            if rect_teste_y.colliderect(parede):
                if dy > 0: self.y = parede.top - self.altura
                elif dy < 0: self.y = parede.bottom

    def desenhar(self, tela):
        # Atualiza o frame antes de desenhar
        self.atualizar_animacao()
        
        if self.imagem_atual:
            tela.blit(self.imagem_atual, (int(self.x), int(self.y)))
        else:
            # Fallback limpo (Apenas o quadrado colorido)
            cor = (34, 139, 34) if self.vivo else (100, 100, 100)
            pygame.draw.rect(tela, cor, (int(self.x), int(self.y), self.largura, self.altura))

    # (Mantenha os métodos receber_dano, curar e mostrar_status iguais)
    def receber_dano(self, dano):
        if not self.vivo: return
        self.vida_atual -= dano
        if self.vida_atual <= 0:
            self.vida_atual = 0
            self.vivo = False
            self.morrer()
            
    def curar(self, cura):
        if not self.vivo: return
        self.vida_atual = min(self.vida_maxima, self.vida_atual + cura)
        
    def morrer(self):
        self.mudar_estado("morrer")