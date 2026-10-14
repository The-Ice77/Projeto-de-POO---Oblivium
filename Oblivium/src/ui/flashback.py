# src/ui/flashback.py
import pygame
from src.utils.colors import (
    PRETO, TXT_ECO_PASSADO, TXT_PENSAMENTO_FANTASMA, 
    TXT_SISTEMA_NARRADOR, UI_TEXTO_APAGADO, MARFIM_OFFWHITE
)
from src.utils.resource_manager import ResourceManager
from src.utils.animations import EfeitoPetalas

class Flashback:
    """
    Sistema de Memórias e Flashbacks de Halia:
    - Escuridão imersiva com chuva sutil de pétalas de memória do menu inicial
    - Efeito máquina de escrever (typewriter) com digitação poética das memórias
    - Avanço intuitivo: acelerar frase atual ou avançar para a próxima com Enter/Clique/Espaço
    """
    def __init__(self, largura, altura):
        self.largura = largura
        self.altura = altura
        self.superficie_preta = pygame.Surface((largura, altura))
        self.superficie_preta.fill(PRETO)
        
        self.fonte_flashback = ResourceManager.carregar_fonte("just_breathe", 36)
        self.fonte_avanco = ResourceManager.carregar_fonte("contrail", 18)
        self.estado = "INATIVO" # INATIVO, ESCURECENDO, ESCURIDAO, CLAREANDO
        self.alpha = 0
        self.velocidade = 5 
        
        # Pétalas de memória em segundo plano
        self.efeito_petalas = EfeitoPetalas(
            largura, altura, 
            quantidade_petalas=20, 
            alpha=(100, 180),
            escala=(0.55, 0.85)
        )
        
        # --- MÁQUINA DE ESCREVER DO FLASHBACK ---
        self.texto_alpha = 255
        self.texto_estado = "DIGITANDO" # "DIGITANDO", "WAIT", "FADE_OUT"
        self.velocidade_texto = 5     
        self.caractere_atual = 0.0
        self.velocidade_digitacao = 0.50 # ~30 caracteres por segundo
        
        self.textos = []
        self.indice_texto = 0
        self.tempo_ultimo_input = 0

    def iniciar(self, textos_memorias):
        self.textos = textos_memorias
        self.indice_texto = 0
        self.estado = "ESCURECENDO"
        self.alpha = 0
        
        # Reseta os controles do texto para a primeira frase
        self.texto_alpha = 255
        self.texto_estado = "DIGITANDO"
        self.caractere_atual = 0.0
        self.tempo_ultimo_input = pygame.time.get_ticks()
        self.efeito_petalas.reiniciar(inicializar_na_tela=True)

    def _obter_texto_formatado_atual(self):
        """Retorna o texto completo da memória atual com a formatação por autor."""
        if not self.textos or self.indice_texto >= len(self.textos):
            return "", TXT_SISTEMA_NARRADOR
            
        dados_texto = self.textos[self.indice_texto]
        autor = dados_texto.get("autor", "")
        frase = dados_texto.get("texto", "")
        
        if autor == "Eco do Passado":
            texto_final = f'"{frase}"'
            cor_texto = TXT_ECO_PASSADO
        elif autor == "Pensamento":
            texto_final = f"({frase})"
            cor_texto = TXT_PENSAMENTO_FANTASMA
        else:
            texto_final = frase
            cor_texto = TXT_SISTEMA_NARRADOR
            
        return texto_final, cor_texto

    def processar_input(self):
        """Gerencia o avanço dos textos: acelera digitação ou passa para a próxima frase."""
        if self.estado != "ESCURIDAO": 
            return

        tempo_atual = pygame.time.get_ticks()
        if tempo_atual - self.tempo_ultimo_input < 200: 
            return
        self.tempo_ultimo_input = tempo_atual

        texto_final, _ = self._obter_texto_formatado_atual()
        
        if self.texto_estado == "DIGITANDO":
            # Se o jogador apertar enquanto digita, completa a frase na hora
            self.caractere_atual = float(len(texto_final))
            self.texto_estado = "WAIT"
        elif self.texto_estado == "WAIT":
            # Se já terminou de digitar, inicia o fade out para a próxima memória
            self.texto_estado = "FADE_OUT"

    def atualizar(self, dt=0.016):
        if self.estado == "INATIVO":
            return False

        # Atualiza a chuva sutil de pétalas
        self.efeito_petalas.atualizar(dt)

        if self.estado == "ESCURECENDO":
            self.alpha += self.velocidade
            if self.alpha >= 255:
                self.alpha = 255
                self.estado = "ESCURIDAO"

        elif self.estado == "ESCURIDAO":
            texto_final, _ = self._obter_texto_formatado_atual()
            total_chars = len(texto_final)
            
            if self.texto_estado == "DIGITANDO":
                self.caractere_atual += self.velocidade_digitacao
                if self.caractere_atual >= total_chars:
                    self.caractere_atual = float(total_chars)
                    self.texto_estado = "WAIT"
            
            elif self.texto_estado == "FADE_OUT":
                self.texto_alpha -= self.velocidade_texto * 1.5
                if self.texto_alpha <= 0:
                    self.texto_alpha = 255
                    self.caractere_atual = 0.0
                    self.indice_texto += 1
                    
                    if self.indice_texto >= len(self.textos):
                        self.estado = "CLAREANDO" # Acabaram as memórias, sai do flashback
                    else:
                        self.texto_estado = "DIGITANDO" # Digita a próxima memória

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
                    linhas.append(linha_atual.rstrip())
                linha_atual = palavra + " "
        if linha_atual: 
            linhas.append(linha_atual.rstrip())
        return linhas

    def desenhar(self, tela):
        if self.estado == "INATIVO": 
            return

        # 1. Desenha o fundo preto com o alpha atual
        self.superficie_preta.set_alpha(self.alpha)
        tela.blit(self.superficie_preta, (0, 0))

        # 2. Desenha as pétalas de memória suaves emergindo e flutuando
        if self.estado in ("ESCURECENDO", "ESCURIDAO", "CLAREANDO"):
            alpha_petalas = min(1.0, max(0.08, self.alpha / 220.0))
            self.efeito_petalas.desenhar(tela, alpha_multiplicador=alpha_petalas)

        # 3. Se estiver em escuridão total, renderiza o texto sendo digitado
        if self.estado == "ESCURIDAO" and self.indice_texto < len(self.textos):
            texto_final, cor_texto = self._obter_texto_formatado_atual()

            # Quebra o texto completo para garantir layout estável
            linhas = self._quebrar_texto(texto_final, self.largura - 240)
            
            altura_linha = 40
            altura_bloco = len(linhas) * altura_linha
            y_inicial = (self.altura // 2) - (altura_bloco // 2)

            total_visivel = int(self.caractere_atual)
            caracteres_acumulados = 0
            piscar_cursor = (pygame.time.get_ticks() // 420) % 2 == 0

            for i, linha in enumerate(linhas):
                len_linha = len(linha)
                largura_linha_completa = self.fonte_flashback.size(linha)[0]
                x_inicio_linha = (self.largura // 2) - (largura_linha_completa // 2)
                
                if total_visivel <= caracteres_acumulados:
                    break
                elif total_visivel >= caracteres_acumulados + len_linha:
                    texto_render = linha
                    caracteres_acumulados += len_linha
                    desenhar_cursor = (i == len(linhas) - 1 and self.texto_estado == "DIGITANDO" and piscar_cursor)
                else:
                    chars_nesta = total_visivel - caracteres_acumulados
                    texto_render = linha[:chars_nesta]
                    caracteres_acumulados += len_linha
                    desenhar_cursor = (self.texto_estado == "DIGITANDO" and piscar_cursor)

                if texto_render:
                    render = self.fonte_flashback.render(texto_render, True, cor_texto)
                    if self.texto_alpha < 255:
                        render.set_alpha(int(max(0, min(255, self.texto_alpha))))
                    tela.blit(render, (x_inicio_linha, y_inicial + (i * altura_linha)))

                    if desenhar_cursor:
                        x_cursor = x_inicio_linha + render.get_width() + 2
                        y_cursor = y_inicial + (i * altura_linha) + 8
                        cursor_surf = pygame.Surface((2, 24), pygame.SRCALPHA)
                        alpha_c = int(max(0, min(255, self.texto_alpha))) if self.texto_alpha < 255 else 200
                        cursor_surf.fill((*cor_texto[:3], alpha_c))
                        tela.blit(cursor_surf, (x_cursor, y_cursor))

            # Desenha o rodapé de avanço / aceleração
            if self.texto_estado == "DIGITANDO":
                aviso_txt = "Clique ou pressione [ENTER / ESPAÇO] para acelerar"
            else:
                aviso_txt = "Clique ou pressione [ENTER / ESPAÇO] para recordar"
                
            avancar = self.fonte_avanco.render(aviso_txt, True, UI_TEXTO_APAGADO)
            tela.blit(avancar, ((self.largura // 2) - (avancar.get_width() // 2), self.altura - 50))