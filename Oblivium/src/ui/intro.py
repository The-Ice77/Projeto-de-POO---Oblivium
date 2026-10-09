# src/ui/intro.py
import pygame
from src.utils.colors import CARVAO_PROFUNDO, MARFIM_OFFWHITE, CINZA_LINHO, UI_TEXTO_APAGADO
from src.utils.resource_manager import ResourceManager
from src.utils.animations import EfeitoPetalas
from src.ui.ui_utils import quebrar_texto_em_linhas, desenhar_flor_botanica

class Intro:
    """
    Introdução Narrativa de Oblivium:
    - Estética poética e melancólica com chuva de pétalas do menu em Carvão Profundo
    - Efeito máquina de escrever (typewriter) com cursor editorial orgânico
    - Tipografia 'Just Breathe' com acabamento editorial e flor botânica discreta
    - Interação completa por Teclado (ENTER, ESPAÇO) ou Clique do Mouse para acelerar/avançar
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
        
        # Efeito de pétalas temático idêntico ao menu principal
        self.efeito_petalas = EfeitoPetalas(self.largura, self.altura, quantidade_petalas=24)
        
        self.ativo = False
        self.alpha = 255
        self.estado_efeito = "DIGITANDO" # "DIGITANDO", "HOLD", "FADE_OUT"
        
        # Sistema de máquina de escrever
        self.caractere_atual = 0.0
        self.velocidade_digitacao = 0.45 # ~27 caracteres por segundo
        self.velocidade_fade = 5
        self.tempo_hold = 2600
        self.tempo_inicio_hold = 0
        self.tempo_inicio_intro = 0

    def iniciar(self):
        self.ativo = True
        self.indice_atual = 0
        self.caractere_atual = 0.0
        self.alpha = 255
        self.estado_efeito = "DIGITANDO"
        self.tempo_inicio_intro = pygame.time.get_ticks()
        self.efeito_petalas.reiniciar(inicializar_na_tela=True)

    def avancar(self):
        """Avança suavemente: completa a digitação ou passa para a próxima frase."""
        if not self.ativo or self.indice_atual >= len(self.textos):
            return
            
        texto_atual = self.textos[self.indice_atual]
        if self.estado_efeito == "DIGITANDO":
            # Se ainda estiver digitando, completa a frase imediatamente
            self.caractere_atual = float(len(texto_atual))
            self.estado_efeito = "HOLD"
            self.tempo_inicio_hold = pygame.time.get_ticks()
        elif self.estado_efeito == "HOLD":
            # Se já terminou de digitar, inicia a transição suave de fade out
            self.estado_efeito = "FADE_OUT"

    def pular(self):
        """Encerra a introdução por completo."""
        if pygame.time.get_ticks() - self.tempo_inicio_intro > 300:
            self.ativo = False

    def atualizar(self, dt=0.016):
        if not self.ativo:
            return False
            
        # Atualiza a chuva de pétalas continuamente
        self.efeito_petalas.atualizar(dt)
        
        if self.indice_atual >= len(self.textos):
            self.ativo = False
            return False
            
        texto_atual = self.textos[self.indice_atual]
        total_chars = len(texto_atual)
        
        if self.estado_efeito == "DIGITANDO":
            self.caractere_atual += self.velocidade_digitacao
            if self.caractere_atual >= total_chars:
                self.caractere_atual = float(total_chars)
                self.estado_efeito = "HOLD"
                self.tempo_inicio_hold = pygame.time.get_ticks()
                
        elif self.estado_efeito == "HOLD":
            tempo_atual = pygame.time.get_ticks()
            if tempo_atual - self.tempo_inicio_hold > self.tempo_hold:
                self.estado_efeito = "FADE_OUT"
                
        elif self.estado_efeito == "FADE_OUT":
            self.alpha -= self.velocidade_fade * 1.6
            if self.alpha <= 0:
                self.alpha = 255
                self.caractere_atual = 0.0
                self.estado_efeito = "DIGITANDO"
                self.indice_atual += 1
                if self.indice_atual >= len(self.textos):
                    self.ativo = False
                    
        return self.ativo

    def draw(self, tela): 
        tela.fill(CARVAO_PROFUNDO)
        
        # 1. Desenha as pétalas caindo em segundo plano
        self.efeito_petalas.desenhar(tela)
        
        if self.indice_atual < len(self.textos):
            texto = self.textos[self.indice_atual]
            
            # Quebra o texto garantindo largura pré-calculada fixa
            linhas = quebrar_texto_em_linhas(texto, self.fonte, self.largura - 240)
            altura_linha = 40
            altura_total = len(linhas) * altura_linha
            y_inicial = self.altura // 2 - altura_total // 2 - 20
            
            # Flor Botânica no topo
            desenhar_flor_botanica(tela, self.largura // 2, y_inicial - 30, cor=CINZA_LINHO, escala=0.7)
            
            # Renderização de máquina de escrever estável caractere a caractere
            total_visivel = int(self.caractere_atual)
            caracteres_acumulados = 0
            piscar_cursor = (pygame.time.get_ticks() // 420) % 2 == 0
            
            for i, linha in enumerate(linhas):
                len_linha = len(linha)
                largura_linha_completa = self.fonte.size(linha)[0]
                x_inicio_linha = self.largura // 2 - largura_linha_completa // 2
                
                if total_visivel <= caracteres_acumulados:
                    break
                elif total_visivel >= caracteres_acumulados + len_linha:
                    texto_render = linha
                    caracteres_acumulados += len_linha
                    desenhar_cursor = (i == len(linhas) - 1 and self.estado_efeito == "DIGITANDO" and piscar_cursor)
                else:
                    chars_nesta = total_visivel - caracteres_acumulados
                    texto_render = linha[:chars_nesta]
                    caracteres_acumulados += len_linha
                    desenhar_cursor = (self.estado_efeito == "DIGITANDO" and piscar_cursor)
                
                if texto_render:
                    render = self.fonte.render(texto_render, True, MARFIM_OFFWHITE)
                    if self.alpha < 255:
                        render.set_alpha(int(max(0, min(255, self.alpha))))
                    tela.blit(render, (x_inicio_linha, y_inicial + i * altura_linha))
                    
                    if desenhar_cursor:
                        x_cursor = x_inicio_linha + render.get_width() + 2
                        y_cursor = y_inicial + i * altura_linha + 6
                        cursor_surf = pygame.Surface((2, 22), pygame.SRCALPHA)
                        alpha_c = int(max(0, min(255, self.alpha))) if self.alpha < 255 else 200
                        cursor_surf.fill((*MARFIM_OFFWHITE[:3], alpha_c))
                        tela.blit(cursor_surf, (x_cursor, y_cursor))
            
            # Aviso editorial no rodapé
            texto_aviso = "[ Pressione ENTER / ESPAÇO ou Clique para acelerar ]" if self.estado_efeito == "DIGITANDO" else "[ Pressione ENTER / ESPAÇO ou Clique para prosseguir ]"
            aviso = self.fonte_pular.render(texto_aviso, True, UI_TEXTO_APAGADO)
            tela.blit(aviso, (self.largura // 2 - aviso.get_width() // 2, self.altura - 45))