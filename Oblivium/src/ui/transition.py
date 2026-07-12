# src/ui/transition.py
import pygame
from src.utils.colors import PRETO, BRANCO

class Transition:
    def __init__(self, largura, altura):
        self.largura = largura
        self.altura = altura
        
        # Cria uma superfície preta do tamanho do ecrã usando a paleta global
        self.superficie = pygame.Surface((largura, altura))
        self.superficie.fill(PRETO)
        
        self.alpha = 0
        self.estado = "INATIVO" # INATIVO, ESCURECENDO, MUDANDO, EXIBINDO_TEXTO, CLAREANDO
        self.velocidade = 5     # Velocidade do efeito de fade do ecrã
        
        # --- NOVO: SISTEMA DE TEXTO DE TRANSIÇÃO ---
        self.fonte = pygame.font.Font(None, 46)
        self.texto_atual = ""
        self.texto_alpha = 0
        self.texto_velocidade_fade = 4
        self.texto_estado = "FADE_IN" # FADE_IN, HOLD, FADE_OUT
        self.tempo_hold_texto = 0
        self.tempo_inicio_hold = 0

    def iniciar(self, texto_opcional=""):
        """
        Ativa o efeito de fade-out. 
        Pode receber um texto opcional (ex: 'Capítulo 1: O Despertar', 'Vila de Oakhaven').
        """
        if self.estado == "INATIVO":
            self.alpha = 0
            self.texto_atual = texto_opcional
            self.texto_alpha = 0
            self.texto_estado = "FADE_IN"
            self.estado = "ESCURECENDO"

    def atualizar(self):
        """Gere os estados do Fade. Retorna True no frame exato em que o mapa deve mudar."""
        if self.estado == "INATIVO":
            return False
            
        if self.estado == "ESCURECENDO":
            self.alpha += self.velocidade
            if self.alpha >= 255:
                self.alpha = 255
                self.estado = "MUDANDO"
                return True # Avisa o main.py que o ecrã está 100% preto para carregar o novo mapa
                
        elif self.estado == "MUDANDO":
            # Se houver texto para exibir, vai para o estado de exibição. Se não, clareia direto.
            if self.texto_atual:
                self.estado = "EXIBINDO_TEXTO"
                # Cálculo dinâmico de tempo de leitura: 
                # Garante um mínimo de 1.5 segundos (1500ms) + 60ms por caractere
                self.tempo_hold_texto = max(1500, len(self.texto_atual) * 60)
            else:
                self.estado = "CLAREANDO"
                
        elif self.estado == "EXIBINDO_TEXTO":
            # Máquina de estados interna para o Fade do Texto
            if self.texto_estado == "FADE_IN":
                self.texto_alpha += self.texto_velocidade_fade
                if self.texto_alpha >= 255:
                    self.texto_alpha = 255
                    self.texto_estado = "HOLD"
                    self.tempo_inicio_hold = pygame.time.get_ticks()
                    
            elif self.texto_estado == "HOLD":
                tempo_atual = pygame.time.get_ticks()
                if tempo_atual - self.tempo_inicio_hold > self.tempo_hold_texto:
                    self.texto_estado = "FADE_OUT"
                    
            elif self.texto_estado == "FADE_OUT":
                self.texto_alpha -= self.texto_velocidade_fade
                if self.texto_alpha <= 0:
                    self.texto_alpha = 0
                    self.estado = "CLAREANDO" # Texto terminou, podemos revelar o novo mapa

        elif self.estado == "CLAREANDO":
            self.alpha -= self.velocidade
            if self.alpha <= 0:
                self.alpha = 0
                self.estado = "INATIVO"
                
        return False

    def desenhar(self, tela):
        if self.estado == "INATIVO": 
            return

        # 1. Desenha o fundo da transição (PRETO)
        self.superficie.set_alpha(self.alpha)
        tela.blit(self.superficie, (0, 0))
        
        # 2. Se houver um texto ativo e estiver no estado correto, renderiza-o centralizado
        if self.estado == "EXIBINDO_TEXTO" and self.texto_atual:
            render_texto = self.fonte.render(self.texto_atual, True, BRANCO)
            render_texto.set_alpha(self.texto_alpha)
            
            # Centralização matemática perfeita na horizontal e vertical
            x_centro = (self.largura // 2) - (render_texto.get_width() // 2)
            y_centro = (self.altura // 2) - (render_texto.get_height() // 2)
            
            tela.blit(render_texto, (x_centro, y_centro))