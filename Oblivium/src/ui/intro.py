# src/ui/intro.py
import pygame
from src.utils.colors import CARVAO_PROFUNDO, MARFIM_OFFWHITE, CINZA_LINHO, UI_TEXTO_APAGADO, AZUL_HOVER_MENU
from src.utils.resource_manager import ResourceManager
from src.ui.ui_utils import quebrar_texto_em_linhas, desenhar_flor_botanica

class Intro:
    """
    Introdução Narrativa de Oblivium:
    - Estética poética e melancólica com fundo Carvão Profundo
    - Tipografia 'Just Breathe' com acabamento editorial e flor botânica discreta
    - Interação completa por Teclado (ENTER, ESPAÇO, E) ou Clique do Mouse
    """
    def __init__(self, largura, altura):
        self.largura = largura
        self.altura = altura
        
        self.textos = [
           "Eu me sinto tão... diferente, tão vazia...",
           "Já faz quanto tempo? Quanto desde a última vez que senti o mundo como devia?",
           "Tudo perdeu suas cores... sua beleza e até seu significado...",
           "Mas sinto que as coisas não deveriam ser assim... Não posso deixar este mundo cinza para sempre.",
           "Preciso lembrar de tudo."
        ]
        
        self.indice_atual = 0
        self.fonte = ResourceManager.carregar_fonte("just_breathe", 32)
        self.fonte_pular = ResourceManager.carregar_fonte("contrail", 16)
        
        self.ativo = False
        self.alpha = 0
        self.estado_efeito = "FADE_IN" 
        self.velocidade_fade = 4
        self.tempo_hold = 2800
        self.tempo_inicio_hold = 0
        
        # --- Timer da Intro ---
        self.tempo_inicio_intro = 0

    def iniciar(self):
        self.ativo = True
        self.indice_atual = 0
        self.alpha = 0
        self.estado_efeito = "FADE_IN"
        self.tempo_inicio_intro = pygame.time.get_ticks()

    def avancar(self):
        """Avança suavemente para a próxima frase ou encerra se for a última."""
        if not self.ativo: return
        if self.estado_efeito in ["FADE_IN", "HOLD"]:
            self.estado_efeito = "FADE_OUT"

    def pular(self):
        """Encerra a introdução por completo."""
        if pygame.time.get_ticks() - self.tempo_inicio_intro > 300:
            self.ativo = False

    def atualizar(self):
        if not self.ativo: return False
            
        if self.estado_efeito == "FADE_IN":
            self.alpha += self.velocidade_fade
            if self.alpha >= 255:
                self.alpha = 255
                self.estado_efeito = "HOLD"
                self.tempo_inicio_hold = pygame.time.get_ticks()
                
        elif self.estado_efeito == "HOLD":
            tempo_atual = pygame.time.get_ticks()
            if tempo_atual - self.tempo_inicio_hold > self.tempo_hold:
                self.estado_efeito = "FADE_OUT"
                
        elif self.estado_efeito == "FADE_OUT":
            self.alpha -= self.velocidade_fade * 1.5
            if self.alpha <= 0:
                self.alpha = 0
                self.estado_efeito = "FADE_IN" 
                self.indice_atual += 1
                if self.indice_atual >= len(self.textos):
                    self.ativo = False
        return self.ativo

    def draw(self, tela): 
        tela.fill(CARVAO_PROFUNDO)
        
        if self.indice_atual < len(self.textos):
            texto = self.textos[self.indice_atual]
            
            # Quebra o texto e centraliza
            linhas = quebrar_texto_em_linhas(texto, self.fonte, self.largura - 240)
            altura_linha = 38
            altura_total = len(linhas) * altura_linha
            y_inicial = self.altura // 2 - altura_total // 2 - 20
            
            # Flor Botânica no topo
            desenhar_flor_botanica(tela, self.largura // 2, y_inicial - 30, cor=CINZA_LINHO, escala=0.7)
            
            # Texto narrativo com fade
            for i, linha in enumerate(linhas):
                render = self.fonte.render(linha, True, MARFIM_OFFWHITE)
                render.set_alpha(int(self.alpha))
                x = self.largura // 2 - render.get_width() // 2
                tela.blit(render, (x, y_inicial + i * altura_linha))
            
            # Aviso no rodapé
            aviso = self.fonte_pular.render("[ Clique ou Pressione ESPAÇO / ENTER para prosseguir ]", True, UI_TEXTO_APAGADO)
            tela.blit(aviso, (self.largura // 2 - aviso.get_width() // 2, self.altura - 45))