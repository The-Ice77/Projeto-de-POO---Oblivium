# src/ui/intro.py
import pygame
from src.utils.colors import PRETO, BRANCO, UI_TEXTO_APAGADO

class Intro:
    def __init__(self, largura, altura):
        self.largura = largura
        self.altura = altura
        
        self.textos = [
           "Eu me sinto tão... Diferente, tão vazia...",
           "Já faz quanto tempo? Quanto desde a última vez que senti o mundo como devia?",
           " Tudo perdeu suas cores... Sua beleza e até seu significado...",
           "Mas, sinto que as coisas não deveriam ser assim, não posso deixar esse mundo cinza pra sempre, tenho que encontrar minha resposta",
           "Preciso lembrar de tudo"
        ]
        
        self.indice_atual = 0
        self.fonte = pygame.font.Font(None, 40)
        self.fonte_pular = pygame.font.Font(None, 24) 
        
        self.ativo = False
        self.alpha = 0
        self.estado_efeito = "FADE_IN" 
        self.velocidade_fade = 3       
        self.tempo_hold = 2000         
        self.tempo_inicio_hold = 0
        
        # --- Timer da Intro ---
        self.tempo_inicio_intro = 0

    def iniciar(self):
        self.ativo = True
        self.indice_atual = 0
        self.alpha = 0
        self.estado_efeito = "FADE_IN"
        self.tempo_inicio_intro = pygame.time.get_ticks()

    def pular(self):
        if pygame.time.get_ticks() - self.tempo_inicio_intro > 500:
            self.ativo = False

    def _quebrar_texto(self, texto, fonte, largura_maxima):
        palavras = texto.split(' ')
        linhas = []
        linha_atual = ""
        for palavra in palavras:
            teste_linha = linha_atual + palavra + " "
            if fonte.size(teste_linha)[0] <= largura_maxima:
                linha_atual = teste_linha
            else:
                if linha_atual: 
                    linhas.append(linha_atual)
                linha_atual = palavra + " "
        if linha_atual: 
            linhas.append(linha_atual)
        return linhas

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
            self.alpha -= self.velocidade_fade
            if self.alpha <= 0:
                self.alpha = 0
                self.estado_efeito = "FADE_IN" 
                self.indice_atual += 1
                if self.indice_atual >= len(self.textos):
                    self.ativo = False
        return self.ativo

    def draw(self, tela): 
        tela.fill(PRETO) 
        
        if self.indice_atual < len(self.textos):
            texto = self.textos[self.indice_atual]
            
            # Quebra o texto e calcula a altura total para centralizar perfeitamente
            linhas = self._quebrar_texto(texto, self.fonte, self.largura - 150)
            altura_linha = 40
            altura_total = len(linhas) * altura_linha
            y_inicial = self.altura // 2 - altura_total // 2
            
            # 2. Desenha o texto da intro (BRANCO)
            for i, linha in enumerate(linhas):
                render = self.fonte.render(linha, True, BRANCO)
                render.set_alpha(self.alpha)
                x = self.largura // 2 - render.get_width() // 2
                tela.blit(render, (x, y_inicial + i * altura_linha))
            
            # 3. Desenha o aviso para saltar a animação (UI_TEXTO_APAGADO)
            aviso = self.fonte_pular.render("Pressione [ENTER] para pular", True, UI_TEXTO_APAGADO)
            tela.blit(aviso, (self.largura - aviso.get_width() - 20, self.altura - 40))