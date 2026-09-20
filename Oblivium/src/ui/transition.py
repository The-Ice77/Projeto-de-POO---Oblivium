# src/ui/transition.py
import pygame
from src.utils.colors import PRETO, MARFIM_OFFWHITE, CINZA_LINHO, CINZA_ARDOSIA, CARVAO_PROFUNDO
from src.utils.resource_manager import ResourceManager
from src.ui.ui_utils import desenhar_flor_botanica

class Transition:
    """
    Sistema de Transição de Cenários e Capítulos alinhado à estética Editorial:
    - Fade suave com fundo Carvão Profundo
    - Tipografia em 'Sunday' em Marfim Offwhite
    - Linha divisória fina com ornamentação botânica
    """
    def __init__(self, largura, altura):
        self.largura = largura
        self.altura = altura
        
        # Cria uma superfície preta do tamanho do ecrã
        self.superficie = pygame.Surface((largura, altura))
        self.superficie.fill(CARVAO_PROFUNDO)
        
        self.alpha = 0
        self.estado = "INATIVO" # INATIVO, ESCURECENDO, MUDANDO, EXIBINDO_TEXTO, CLAREANDO
        self.velocidade = 5     # Velocidade do efeito de fade do ecrã
        
        # Tipografia Editorial
        self.fonte = ResourceManager.carregar_fonte("sunday", 38)
        self.fonte_sub = ResourceManager.carregar_fonte("just_breathe", 20)
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
                return True # Avisa que o ecrã está 100% preto para carregar o novo mapa
                
        elif self.estado == "MUDANDO":
            if self.texto_atual:
                self.estado = "EXIBINDO_TEXTO"
                self.tempo_hold_texto = max(1500, len(self.texto_atual) * 60)
            else:
                self.estado = "CLAREANDO"
                
        elif self.estado == "EXIBINDO_TEXTO":
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
                    self.estado = "CLAREANDO"

        elif self.estado == "CLAREANDO":
            self.alpha -= self.velocidade
            if self.alpha <= 0:
                self.alpha = 0
                self.estado = "INATIVO"
                
        return False

    def desenhar(self, tela):
        if self.estado == "INATIVO": 
            return

        # 1. Desenha o fundo da transição
        self.superficie.set_alpha(self.alpha)
        tela.blit(self.superficie, (0, 0))
        
        # 2. Se houver um texto ativo, renderiza com ornamentação delicada
        if self.estado == "EXIBINDO_TEXTO" and self.texto_atual:
            surf_texto = pygame.Surface((self.largura, self.altura), pygame.SRCALPHA)
            
            render_texto = self.fonte.render(self.texto_atual, True, MARFIM_OFFWHITE)
            x_centro = (self.largura // 2) - (render_texto.get_width() // 2)
            y_centro = (self.altura // 2) - (render_texto.get_height() // 2)
            
            surf_texto.blit(render_texto, (x_centro, y_centro))
            
            # Linha decorativa fina com seta e flor botânica
            y_linha = y_centro + render_texto.get_height() + 14
            w_linha = min(360, render_texto.get_width() + 60)
            x_ini = (self.largura - w_linha) // 2
            x_fim = x_ini + w_linha
            
            pygame.draw.line(surf_texto, CINZA_LINHO, (x_ini, y_linha), (x_fim, y_linha), 1)
            desenhar_flor_botanica(surf_texto, self.largura // 2, y_linha, cor=CINZA_LINHO, escala=0.6)
            
            surf_texto.set_alpha(self.texto_alpha)
            tela.blit(surf_texto, (0, 0))