# src/entities/Entity.py
import pygame
import math
from src.utils.resource_manager import Animacao

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
        # Dicionário que guarda objetos da classe Animacao por estado
        self.animacoes = {
            "idle": Animacao([]),
            "andar": Animacao([]),
            "atacar": Animacao([], loop=False),
            "morrer": Animacao([], loop=False)
        }
        
        self.estado_atual = "idle"
        self.virado_direita = True       # Controla o flip horizontal da imagem
        
        # Imagem atual a ser renderizada
        self.imagem_atual = None

    def definir_animacao(self, estado, animacao):
        """
        Define ou sobrescreve a animação de um estado específico da Entidade.
        Ideal para injetar as artes após a criação da instância.
        """
        self.animacoes[estado] = animacao

    def aplicar_pacote_animacoes(self, pacote):
        """
        Recebe um dicionário onde a chave é o estado ("idle", "andar")
        e o valor é o objeto Animacao.
        """
        for estado, animacao in pacote.items():
            self.animacoes[estado] = animacao

    def atualizar_animacao(self):
        """Atualiza o frame atual da animação baseada no estado da entidade."""
        if not self.vivo and self.estado_atual != "morrer":
            self.mudar_estado("morrer")
            
        animacao = self.animacoes.get(self.estado_atual)
        
        if animacao and animacao.frames:
            animacao.atualizar()
            imagem_base = animacao.get_imagem()
            
            if imagem_base:
                # Espelha a imagem se estiver virado para a esquerda
                if not self.virado_direita:
                    self.imagem_atual = pygame.transform.flip(imagem_base, True, False)
                else:
                    self.imagem_atual = imagem_base
            else:
                self.imagem_atual = None
        else:
            self.imagem_atual = None

    def mudar_estado(self, novo_estado):
        """Altera o estado da animação e reseta o frame se o estado for novo."""
        if self.estado_atual != novo_estado:
            self.estado_atual = novo_estado
            if novo_estado in self.animacoes:
                self.animacoes[novo_estado].resetar()

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
            largura_img = self.imagem_atual.get_width()
            altura_img = self.imagem_atual.get_height()
            
            # Centraliza horizontalmente e alinha a base da imagem com a base da hitbox
            offset_x = (largura_img - self.largura) / 2
            offset_y = altura_img - self.altura
            
            tela.blit(self.imagem_atual, (int(self.x - offset_x), int(self.y - offset_y)))
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