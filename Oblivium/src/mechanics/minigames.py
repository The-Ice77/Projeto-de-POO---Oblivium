# src/mechanics/minigames.py
import pygame
from src.utils.colors import (
    FUNDO_BARRA, BRANCO, BARRA_VIDA_JOGADOR, FOGO_BORDA,
    TXT_SISTEMA_NARRADOR, BARRA_MANA, TXT_PENSAMENTO_INTERNO
)

class MinigameTiming:
    def __init__(self, largura_tela, altura_tela):
        self.largura_tela = largura_tela
        self.altura_tela = altura_tela
        self.bx = (largura_tela // 2) - 150
        self.by = altura_tela - 150
        self.cursor_x = 0
        self.cursor_dir = 1
        self.velocidade_cursor = 10
        self.fonte = pygame.font.Font(None, 32)
        self.ativo = False

    def iniciar(self):
        self.cursor_x = 0
        self.cursor_dir = 1
        self.ativo = True

    def atualizar(self):
        if not self.ativo: return
        
        # O Cursor vai e volta rapidamente dentro do limite de 300 pixels da barra
        self.cursor_x += self.velocidade_cursor * self.cursor_dir
        if self.cursor_x > 300 or self.cursor_x < 0:
            self.cursor_dir *= -1

    def checar_sucesso(self):
        """Finaliza o minigame e retorna True se acertou a área verde, ou False se errou."""
        zona_min = self.bx + 120
        zona_max = self.bx + 180
        pos_absoluta = self.bx + self.cursor_x
        
        self.ativo = False # Desativa o minigame após o palpite
        return zona_min <= pos_absoluta <= zona_max

    def desenhar(self, tela):
        if not self.ativo: return
        
        # 1. Fundo da barra (Usando FUNDO_BARRA e BRANCO)
        pygame.draw.rect(tela, FUNDO_BARRA, (self.bx, self.by, 300, 40))
        pygame.draw.rect(tela, BRANCO, (self.bx, self.by, 300, 40), 2)
        
        # 2. Zona Alvo (Usando BARRA_VIDA_JOGADOR para o verde)
        pygame.draw.rect(tela, BARRA_VIDA_JOGADOR, (self.bx + 120, self.by, 60, 40))
        
        # 3. Cursor em Movimento (Usando FOGO_BORDA para o tom avermelhado/laranja)
        pygame.draw.rect(tela, FOGO_BORDA, (self.bx + self.cursor_x - 5, self.by - 10, 10, 60))
        
        # 4. Texto de instrução (Usando TXT_SISTEMA_NARRADOR para o amarelo/ouro indicador)
        texto = self.fonte.render("Pressione [ESPAÇO] na área verde!", True, TXT_SISTEMA_NARRADOR)
        tela.blit(texto, ((self.largura_tela // 2) - (texto.get_width() // 2), self.by - 40))


class MinigameMash:
    def __init__(self, largura_tela, altura_tela):
        self.largura_tela = largura_tela
        self.altura_tela = altura_tela
        self.bx = (largura_tela // 2) - 150
        self.by = altura_tela - 150
        self.progresso = 0
        self.decaimento = 0.6      # Força da gravidade drenando a barra continuamente
        self.ganho_por_clique = 8  # Quanto a barra enche a cada esmagada de tecla
        self.fonte = pygame.font.Font(None, 32)
        self.ativo = False

    def iniciar(self):
        self.progresso = 40  # A barra já começa preenchida com a força inicial!
        self.ativo = True

    def atualizar(self):
        """Drena a barra continuamente. Retorna 'VENCEU', 'PERDEU' ou None."""
        if not self.ativo: return None
        
        self.progresso -= self.decaimento
        
        # Condição de Derrota: A barra zerou (as pedras caíram)
        if self.progresso <= 0:
            self.ativo = False
            return "PERDEU"
        
        # Condição de Vitória: Preencheu a concentração em 100%
        if self.progresso >= 100:
            self.ativo = False
            return "VENCEU"
            
        return None

    def esmagar(self):
        """Acionado externamente quando o jogador pressiona ESPAÇO."""
        if self.ativo:
            self.progresso += self.ganho_por_clique

    def desenhar(self, tela):
        if not self.ativo: return
        
        # 1. Fundo da barra (Usando FUNDO_BARRA e BRANCO)
        pygame.draw.rect(tela, FUNDO_BARRA, (self.bx, self.by, 300, 40))
        pygame.draw.rect(tela, BRANCO, (self.bx, self.by, 300, 40), 2)
        
        # 2. Preenchimento de Mana Azul de acordo com o progresso (Usando BARRA_MANA)
        largura_progresso = (self.progresso / 100) * 300
        pygame.draw.rect(tela, BARRA_MANA, (self.bx, self.by, largura_progresso, 40))
        
        # 3. Texto de instrução (Usando TXT_PENSAMENTO_INTERNO para o azul claro suave)
        texto = self.fonte.render("Esmague [ESPAÇO] para sustentar a magia!", True, TXT_PENSAMENTO_INTERNO)
        tela.blit(texto, ((self.largura_tela // 2) - (texto.get_width() // 2), self.by - 40))