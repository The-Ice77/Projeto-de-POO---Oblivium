# src/maps/map_loader.py
import pygame
from entities.item import Item 
from src.utils.colors import (
    CENARIO_FUNDO_FORA, CENARIO_MADEIRA_VARANDA, CENARIO_PAREDE_CASA,
    CENARIO_CHAO_CASA, CENARIO_PORTA, CENARIO_MOVEIS,
    CENARIO_GRAMA_CINZA, CENARIO_ESTRADA, CENARIO_BARREIRAS,
    COLOR_BOLSA_MOEDAS, COLOR_LIVRO_ANTIGO, COLOR_CAJADO_MAGICO,
    COR_PEDRA_DESLIZAMENTO, COR_BORDA_PEDRA
)

class Mapa:
    def __init__(self, game, largura_tela, altura_tela):
        self.game = game
        self.largura_tela = largura_tela
        self.altura_tela = altura_tela
        self.cenario_atual = "CASA" # Pode ser "CASA" ou "ESTRADA"
        
        # --- DADOS DO CENÁRIO: CASA ---
        self.area_chao_casa = pygame.Rect(50, 50, 500, 600)  # Termina em y = 650
        self.varanda_madeira = pygame.Rect(550, 50, 150, 600) # Termina em y = 650
        
        self.paredes_casa = [
            pygame.Rect(50, 50, 500, 40),          # Parede superior (topo em y=50)
            pygame.Rect(50, 50, 40, 600),          # Parede esquerda (começa em x=50)
            pygame.Rect(50, 610, 500, 40),         # Parede inferior (fica entre y=610 e y=650, fechando perfeitamente)
            pygame.Rect(510, 50, 40, 250),         # Parede direita superior (antes da porta)
            pygame.Rect(510, 400, 40, 250),        # Parede direita inferior (depois da porta)
        ]
        
        self.porta = pygame.Rect(510, 300, 40, 100)
        self.moveis = [
            pygame.Rect(90, 90, 110, 180),         
            pygame.Rect(410, 90, 100, 60),         
        ]
        self.limites_varanda = [
            pygame.Rect(550, 45, 150, 5),      
            pygame.Rect(550, 650, 150, 5),    
        ]
        self.porta_aberta = False 
        
        # Instanciação padrão dos itens no chão da casa
        self.itens_no_chao = [
            Item("A Bolsa de Moedas", 420, 180, 25, 25, COLOR_BOLSA_MOEDAS), 
            Item("O Livro Antigo", 300, 450, 25, 30, COLOR_LIVRO_ANTIGO),    
            Item("O Cajado Mágico", 230, 200, 10, 60, COLOR_CAJADO_MAGICO)    
        ]

        # --- DADOS DO CENÁRIO: ESTRADA ---
        self.area_estrada = pygame.Rect(0, 250, largura_tela, 220)
        self.barreiras_estrada = [
            pygame.Rect(0, 0, largura_tela, 250),      # Margem superior
            pygame.Rect(0, 470, largura_tela, 250)     # Margem inferior
        ]

        self.hitboxes = []
        self.pedras_deslizamento = [] 
        
        # Carrega o cenário inicial e aplica o filtro de itens coletados de imediato
        self.carregar_cenario("CASA")

    def carregar_cenario(self, nome_cenario):
        """Muda o estado do mapa, reconstrói as hitboxes e filtra os itens já apanhados."""
        self.cenario_atual = nome_cenario
        self.hitboxes = []

        if self.cenario_atual == "CASA":
            self.hitboxes.extend(self.paredes_casa)
            self.hitboxes.extend(self.moveis)
            self.hitboxes.extend(self.limites_varanda)
            if not self.porta_aberta:
                self.hitboxes.append(self.porta)
                
            # Restaura a lista original de itens da casa sempre que o cenário for carregado
            self.itens_no_chao = [
                Item("A Bolsa de Moedas", 420, 180, 25, 25, COLOR_BOLSA_MOEDAS), 
                Item("O Livro Antigo", 300, 450, 25, 30, COLOR_LIVRO_ANTIGO),    
                Item("O Cajado Mágico", 230, 200, 10, 60, COLOR_CAJADO_MAGICO)    
            ]
            
        elif self.cenario_atual == "ESTRADA":
            self.hitboxes.extend(self.barreiras_estrada)
            self.hitboxes.append(pygame.Rect(0, 0, 20, self.altura_tela))
            self.hitboxes.append(pygame.Rect(1220, 0, 30, self.altura_tela))
            self.itens_no_chao = [] 
        
        elif self.cenario_atual == "ESTRADA_2":
            self.hitboxes.extend(self.barreiras_estrada)
            self.hitboxes.append(pygame.Rect(0, 0, 20, self.altura_tela))
            
            self.pedras_deslizamento = [
                pygame.Rect(1100, 250, 80, 70),   # Pedra Superior
                pygame.Rect(1150, 310, 90, 80),   # Pedra do Meio Direita
                pygame.Rect(1080, 320, 80, 80),   # Pedra do Meio Esquerda
                pygame.Rect(1120, 390, 100, 90),  # Pedra da Base
            ]
            self.hitboxes.extend(self.pedras_deslizamento)
            self.itens_no_chao = []

        # Aplica o filtro global de itens coletados diretamente na raiz do carregamento
        if hasattr(self.game, 'itens_coletados') and self.game.itens_coletados:
            itens_filtrados = []
            for indice, item in enumerate(self.itens_no_chao):
                id_unico = f"{nome_cenario}_item_{indice}"
                if id_unico not in self.game.itens_coletados:
                    itens_filtrados.append(item)
            self.itens_no_chao = itens_filtrados

    def abrir_porta(self):
        self.porta_aberta = True
        self.carregar_cenario("CASA")

    def desenhar(self, tela):
        if self.cenario_atual == "CASA":
            tela.fill(CENARIO_FUNDO_FORA)
            pygame.draw.rect(tela, CENARIO_MADEIRA_VARANDA, self.varanda_madeira)
            pygame.draw.rect(tela, CENARIO_PAREDE_CASA, self.varanda_madeira, 2) 
            
            for limite in self.limites_varanda:
                pygame.draw.rect(tela, CENARIO_PAREDE_CASA, limite)
                
            pygame.draw.rect(tela, CENARIO_CHAO_CASA, self.area_chao_casa)
            
            for item in self.itens_no_chao:
                item.desenhar(tela)
                
            for parede in self.paredes_casa:
                pygame.draw.rect(tela, CENARIO_PAREDE_CASA, parede)
                pygame.draw.rect(tela, CENARIO_FUNDO_FORA, parede, 2) 
                
            if not self.porta_aberta:
                pygame.draw.rect(tela, CENARIO_PORTA, self.porta)
                pygame.draw.rect(tela, CENARIO_PAREDE_CASA, self.porta, 2)
            else:
                pygame.draw.rect(tela, CENARIO_CHAO_CASA, self.porta, 2)
                
            for movel in self.moveis:
                pygame.draw.rect(tela, CENARIO_MOVEIS, movel)
                pygame.draw.rect(tela, CENARIO_PAREDE_CASA, movel, 2)
                
        elif self.cenario_atual in ["ESTRADA", "ESTRADA_2"]:
            tela.fill(CENARIO_GRAMA_CINZA)
            pygame.draw.rect(tela, CENARIO_ESTRADA, self.area_estrada)
            
            for barreira in self.barreiras_estrada:
                pygame.draw.rect(tela, CENARIO_BARREIRAS, barreira)
                pygame.draw.rect(tela, CENARIO_FUNDO_FORA, barreira, 1) 
                
            if self.cenario_atual == "ESTRADA_2":
                for pedra in self.pedras_deslizamento:
                    pygame.draw.rect(tela, COR_PEDRA_DESLIZAMENTO, pedra)
                    pygame.draw.rect(tela, COR_BORDA_PEDRA, pedra, 2)