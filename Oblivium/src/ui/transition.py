# src/ui/transition.py
import pygame
from src.utils.colors import PRETO, MARFIM_OFFWHITE, CINZA_LINHO, CINZA_ARDOSIA, CARVAO_PROFUNDO
from src.utils.resource_manager import ResourceManager
from src.utils.animations import EfeitoPetalas
from src.ui.ui_utils import desenhar_flor_botanica

class Transition:
    """
    Sistema de Transição de Cenários e Capítulos alinhado à estética Editorial:
    - Fade suave com fundo Carvão Profundo
    - Chuva orgânica de pétalas do menu inicial caindo/flutuando durante a transição
    - Efeito máquina de escrever (typewriter) elegante para nomes de capítulos/locais
    - Tipografia em 'Sunday' em Marfim Offwhite
    - Linha divisória fina com ornamentação botânica
    """
    def __init__(self, largura, altura):
        self.largura = largura
        self.altura = altura
        
        # Cria uma superfície do tamanho da tela preenchida com Carvão Profundo
        self.superficie = pygame.Surface((largura, altura))
        self.superficie.fill(CARVAO_PROFUNDO)
        
        self.alpha = 0
        self.estado = "INATIVO" # INATIVO, ESCURECENDO, MUDANDO, EXIBINDO_TEXTO, CLAREANDO
        self.velocidade = 5     # Velocidade do efeito de fade do ecrã
        
        # Efeito de pétalas temático idêntico ao menu principal para transições atmosféricas
        self.efeito_petalas = EfeitoPetalas(
            largura_tela=largura, 
            altura_tela=altura, 
            quantidade_petalas=32,
            velocidade_y=(30.0, 75.0),
            vento_x=(-42.0, -16.0),
            alpha=(120, 215),
            escala=(0.60, 0.95)
        )
        
        # Tipografia Editorial
        self.fonte = ResourceManager.carregar_fonte("sunday", 38)
        self.fonte_sub = ResourceManager.carregar_fonte("just_breathe", 20)
        self.texto_atual = ""
        self.texto_alpha = 0
        self.texto_velocidade_fade = 5
        self.texto_estado = "DIGITANDO" # DIGITANDO, HOLD, FADE_OUT
        self.tempo_hold_texto = 0
        self.tempo_inicio_hold = 0
        
        # Sistema de máquina de escrever para a transição
        self.caractere_atual = 0.0
        self.velocidade_digitacao = 0.55 # Digitação fluida de nomes/capítulos

    def iniciar(self, texto_opcional=""):
        """
        Ativa o efeito de fade-out e transição poética. 
        Pode receber um texto opcional (ex: 'Capítulo 1: O Despertar', 'Vila de Oakhaven').
        """
        if self.estado == "INATIVO":
            self.alpha = 0
            self.texto_atual = texto_opcional
            self.texto_alpha = 255
            self.caractere_atual = 0.0
            self.texto_estado = "DIGITANDO"
            self.estado = "ESCURECENDO"
            # Reinicia e distribui as pétalas para uma brisa renovada na transição
            self.efeito_petalas.reiniciar(inicializar_na_tela=True)

    def avancar(self):
        """Acelera a digitação do texto de transição ou prossegue imediatamente."""
        if self.estado == "EXIBINDO_TEXTO":
            if self.texto_estado == "DIGITANDO":
                self.caractere_atual = float(len(self.texto_atual))
                self.texto_estado = "HOLD"
                self.tempo_inicio_hold = pygame.time.get_ticks()
            elif self.texto_estado == "HOLD":
                self.texto_estado = "FADE_OUT"

    def atualizar(self, dt=0.016):
        """Gere os estados do Fade e das pétalas. Retorna True no frame exato em que o mapa deve mudar."""
        if self.estado == "INATIVO":
            return False
            
        # Atualiza o fluxo contínuo das pétalas flutuando na brisa da transição
        self.efeito_petalas.atualizar(dt)
            
        if self.estado == "ESCURECENDO":
            self.alpha += self.velocidade
            if self.alpha >= 255:
                self.alpha = 255
                self.estado = "MUDANDO"
                return True # Avisa que a tela está 100% escura para carregar o novo mapa
                
        elif self.estado == "MUDANDO":
            if self.texto_atual:
                self.estado = "EXIBINDO_TEXTO"
                self.texto_estado = "DIGITANDO"
                self.caractere_atual = 0.0
                self.texto_alpha = 255
                self.tempo_hold_texto = max(1800, len(self.texto_atual) * 75)
            else:
                self.estado = "CLAREANDO"
                
        elif self.estado == "EXIBINDO_TEXTO":
            total_chars = len(self.texto_atual)
            
            if self.texto_estado == "DIGITANDO":
                self.caractere_atual += self.velocidade_digitacao
                if self.caractere_atual >= total_chars:
                    self.caractere_atual = float(total_chars)
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

        # 1. Desenha o fundo da transição (fade suave em Carvão Profundo)
        self.superficie.set_alpha(int(self.alpha))
        tela.blit(self.superficie, (0, 0))
        
        # 2. Desenha a brisa de pétalas do menu flutuando pela transição com transparência proporcional
        alpha_petalas = min(1.0, max(0.15, self.alpha / 220.0))
        self.efeito_petalas.desenhar(tela, alpha_multiplicador=alpha_petalas)
        
        # 3. Se houver um texto ativo, renderiza com máquina de escrever e ornamentação delicada
        if self.estado == "EXIBINDO_TEXTO" and self.texto_atual:
            largura_total_texto = self.fonte.size(self.texto_atual)[0]
            altura_texto = self.fonte.size(self.texto_atual)[1]
            x_inicio_texto = (self.largura - largura_total_texto) // 2
            y_centro = (self.altura // 2) - (altura_texto // 2) - 10
            
            # Texto datilografado
            chars_visiveis = int(self.caractere_atual)
            texto_parcial = self.texto_atual[:chars_visiveis]
            
            if texto_parcial:
                render_texto = self.fonte.render(texto_parcial, True, MARFIM_OFFWHITE)
                if self.texto_alpha < 255:
                    render_texto.set_alpha(max(0, int(self.texto_alpha)))
                tela.blit(render_texto, (x_inicio_texto, y_centro))
                
                # Cursor delicado piscando enquanto digita
                if self.texto_estado == "DIGITANDO" and (pygame.time.get_ticks() // 380) % 2 == 0:
                    cursor_x = x_inicio_texto + render_texto.get_width() + 3
                    cursor_y = y_centro + 4
                    cursor_h = altura_texto - 8
                    cursor_surf = pygame.Surface((2, cursor_h), pygame.SRCALPHA)
                    alpha_c = max(0, int(self.texto_alpha))
                    cursor_surf.fill((*MARFIM_OFFWHITE[:3], alpha_c))
                    tela.blit(cursor_surf, (cursor_x, cursor_y))
            
            # Linha decorativa fina com flor botânica proporcional
            y_linha = y_centro + altura_texto + 16
            w_linha = min(420, max(260, largura_total_texto + 80))
            x_ini = (self.largura - w_linha) // 2
            x_fim = x_ini + w_linha
            
            surf_decor = pygame.Surface((self.largura, 30), pygame.SRCALPHA)
            pygame.draw.line(surf_decor, CINZA_LINHO, (x_ini, 15), (x_fim, 15), 1)
            desenhar_flor_botanica(surf_decor, self.largura // 2, 15, cor=CINZA_LINHO, escala=0.6)
            
            if self.texto_alpha < 255:
                surf_decor.set_alpha(max(0, int(self.texto_alpha)))
            tela.blit(surf_decor, (0, y_linha - 15))