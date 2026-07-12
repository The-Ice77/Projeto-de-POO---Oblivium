# src/ui/flashback.py
import pygame
from src.utils.colors import (
    PRETO, TXT_ECO_PASSADO, TXT_PENSAMENTO_FANTASMA, 
    TXT_SISTEMA_NARRADOR, UI_TEXTO_APAGADO
)

class Flashback:
    def __init__(self, largura, altura):
        self.largura = largura
        self.altura = altura
        self.superficie_preta = pygame.Surface((largura, altura))
        self.superficie_preta.fill(PRETO)
        
        self.fonte_flashback = pygame.font.Font(None, 36) # Fonte um pouco maior para a cena
        self.estado = "INATIVO" # INATIVO, ESCURECENDO, ESCURIDAO, CLAREANDO
        self.alpha = 0
        self.velocidade = 5 
        
        # --- VARIÁVEIS PARA O FADE DO TEXTO ---
        self.texto_alpha = 0
        self.texto_estado = "FADE_IN" # FADE_IN, WAIT, FADE_OUT
        self.velocidade_texto = 4     # Velocidade em que o texto aparece/some
        
        self.textos = []
        self.indice_texto = 0
        self.tempo_ultimo_input = 0

    def iniciar(self, textos_memorias):
        self.textos = textos_memorias
        self.indice_texto = 0
        self.estado = "ESCURECENDO"
        self.alpha = 0
        
        # Reseta os controles do texto para a primeira frase
        self.texto_alpha = 0
        self.texto_estado = "FADE_IN"
        self.tempo_ultimo_input = pygame.time.get_ticks()

    def processar_input(self):
        """Gerencia o avanço dos textos centrais com Enter ou Clique."""
        # Só permite avançar se o texto estiver totalmente visível e à espera
        if self.estado != "ESCURIDAO" or self.texto_estado != "WAIT": 
            return

        tempo_atual = pygame.time.get_ticks()
        if tempo_atual - self.tempo_ultimo_input < 300: return
        self.tempo_ultimo_input = tempo_atual

        # Em vez de pular direto para o próximo, inicia o desaparecimento do texto atual
        self.texto_estado = "FADE_OUT"

    def atualizar(self):
        if self.estado == "INATIVO":
            return False

        if self.estado == "ESCURECENDO":
            self.alpha += self.velocidade
            if self.alpha >= 255:
                self.alpha = 255
                self.estado = "ESCURIDAO"

        elif self.estado == "ESCURIDAO":
            # --- Ciclo de Fade dos Textos ---
            if self.texto_estado == "FADE_IN":
                self.texto_alpha += self.velocidade_texto
                if self.texto_alpha >= 255:
                    self.texto_alpha = 255
                    self.texto_estado = "WAIT" # Texto apareceu, agora aguarda o input do jogador
            
            elif self.texto_estado == "FADE_OUT":
                self.texto_alpha -= self.velocidade_texto
                if self.texto_alpha <= 0:
                    self.texto_alpha = 0
                    # Quando o texto sumir completamente, passa para a próxima frase
                    self.indice_texto += 1
                    
                    if self.indice_texto >= len(self.textos):
                        self.estado = "CLAREANDO" # Acabaram as memórias, sai do flashback
                    else:
                        self.texto_estado = "FADE_IN" # Inicia o fade da próxima frase

        elif self.estado == "CLAREANDO":
            self.alpha -= self.velocidade
            if self.alpha <= 0:
                self.alpha = 0
                self.estado = "INATIVO"
                return True # Flashback concluído!

        return False

    def _quebrar_texto(self, texto, largura_maxima):
        palavras = texto.split(' ')
        linhas = []
        linha_atual = ""
        for palavra in palavras:
            teste_linha = linha_atual + palavra + " "
            if self.fonte_flashback.size(teste_linha)[0] <= largura_maxima:
                linha_atual = teste_linha
            else:
                if linha_atual: 
                    linhas.append(linha_atual)
                linha_atual = palavra + " "
        if linha_atual: 
            linhas.append(linha_atual)
        return linhas

    def desenhar(self, tela):
        if self.estado == "INATIVO": return

        # 1. Desenha o fundo preto com o alpha atual
        self.superficie_preta.set_alpha(self.alpha)
        tela.blit(self.superficie_preta, (0, 0))

        # 2. Se estiver em escuridão total, renderiza o texto centralizado com o seu próprio fade
        if self.estado == "ESCURIDAO" and self.indice_texto < len(self.textos):
            dados_texto = self.textos[self.indice_texto]
            autor = dados_texto.get("autor", "")
            frase = dados_texto.get("texto", "")
            
            # Formata o texto e escolhe a cor dependendo de quem fala
            if autor == "Eco do Passado":
                texto_final = f'"{frase}"'
                cor_texto = TXT_ECO_PASSADO
            elif autor == "Pensamento":
                texto_final = f"({frase})"
                cor_texto = TXT_PENSAMENTO_FANTASMA
            else:
                texto_final = frase
                cor_texto = TXT_SISTEMA_NARRADOR

            # Quebra o texto para não vazar da tela lateralmente
            linhas = self._quebrar_texto(texto_final, self.largura - 200)
            
            # Calcula o Y inicial para deixar o bloco perfeitamente centralizado na tela verticalmente
            altura_bloco = len(linhas) * 35
            y_inicial = (self.altura // 2) - (altura_bloco // 2)

            # Desenha as linhas principais do texto
            for i, linha in enumerate(linhas):
                render = self.fonte_flashback.render(linha.strip(), True, cor_texto)
                # Aplica o nível de transparência atual para gerar o fade in/out
                render.set_alpha(self.texto_alpha)
                
                # Centraliza horizontalmente
                x_centralizado = (self.largura // 2) - (render.get_width() // 2)
                tela.blit(render, (x_centralizado, y_inicial + (i * 35)))

            # Desenha o rodapé de avanço apenas quando o texto estiver visível e à espera
            if self.texto_estado == "WAIT":
                avancar = pygame.font.Font(None, 20).render("Clique ou pressione [ENTER] para recordar", True, UI_TEXTO_APAGADO)
                tela.blit(avancar, ((self.largura // 2) - (avancar.get_width() // 2), self.altura - 50))