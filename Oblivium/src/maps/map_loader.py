# src/maps/map_loader.py
import pygame
from entities.item import Item 
from src.utils.colors import (
    CENARIO_FUNDO_FORA, CENARIO_MADEIRA_VARANDA, CENARIO_PAREDE_CASA,
    CENARIO_CHAO_CASA, CENARIO_PORTA, CENARIO_MOVEIS,
    CENARIO_GRAMA_CINZA, CENARIO_ESTRADA, CENARIO_BARREIRAS,
    COLOR_BOLSA_MOEDAS, COLOR_LIVRO_ANTIGO, COLOR_CAJADO_MAGICO,
    COR_PEDRA_DESLIZAMENTO, COR_BORDA_PEDRA  # <--- ADICIONE ESTAS DUAS AQUI
)
class Mapa:
    def __init__(self, largura_tela, altura_tela):
        self.largura_tela = largura_tela
        self.altura_tela = altura_tela
        self.cenario_atual = "CASA" # Pode ser "CASA" ou "ESTRADA"
        
        # --- DADOS DO CENÁRIO: CASA ---
        self.area_chao_casa = pygame.Rect(50, 50, 500, 600)
        self.varanda_madeira = pygame.Rect(550, 50, 150, 600)
        self.paredes_casa = [
            pygame.Rect(50, 50, 500, 40),          
            pygame.Rect(50, 50, 40, 600),          
            pygame.Rect(50, 610, 500, 40),         
            pygame.Rect(510, 50, 40, 250),         
            pygame.Rect(510, 400, 40, 250),       
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
        
        # Instanciação dos itens usando as constantes de cores corretas
        self.itens_no_chao = [
            Item("A Bolsa de Moedas", 420, 180, 25, 25, COLOR_BOLSA_MOEDAS), 
            Item("O Livro Antigo", 300, 450, 25, 30, COLOR_LIVRO_ANTIGO),    
            Item("O Cajado Mágico", 230, 200, 10, 60, COLOR_CAJADO_MAGICO)    
        ]

        # --- DADOS DO CENÁRIO: ESTRADA ---
        self.area_estrada = pygame.Rect(0, 250, largura_tela, 220)
        self.barreiras_estrada = [
            pygame.Rect(0, 0, largura_tela, 250),       # Margem superior
            pygame.Rect(0, 470, largura_tela, 250)      # Margem inferior
        ]

        self.hitboxes = []
        self.pedras_deslizamento = [] # Declarada vazia para evitar AttributeError antes do carregamento
        self.carregar_cenario("CASA")

    def carregar_cenario(self, nome_cenario):
        """Muda o estado do mapa e reconstrói as hitboxes necessárias."""
        self.cenario_atual = nome_cenario
        self.hitboxes = []
        
        if self.cenario_atual == "CASA":
            self.hitboxes.extend(self.paredes_casa)
            self.hitboxes.extend(self.moveis)
            self.hitboxes.extend(self.limites_varanda)
            if not self.porta_aberta:
                self.hitboxes.append(self.porta)
                
        elif self.cenario_atual == "ESTRADA":
            self.hitboxes.extend(self.barreiras_estrada)
            # Limites laterais fixos do Overworld
            self.hitboxes.append(pygame.Rect(0, 0, 20, self.altura_tela))
            self.hitboxes.append(pygame.Rect(1220, 0, 30, self.altura_tela))
        
        elif self.cenario_atual == "ESTRADA_2":
            self.hitboxes.extend(self.barreiras_estrada)
            self.hitboxes.append(pygame.Rect(0, 0, 20, self.altura_tela))
            
            # --- PILHA DE PEDRAS SEPARADAS (Para o Puzzle) ---
            self.pedras_deslizamento = [
                pygame.Rect(1100, 250, 80, 70),   # Pedra Superior
                pygame.Rect(1150, 310, 90, 80),   # Pedra do Meio Direita
                pygame.Rect(1080, 320, 80, 80),   # Pedra do Meio Esquerda
                pygame.Rect(1120, 390, 100, 90),  # Pedra da Base
            ]
            self.hitboxes.extend(self.pedras_deslizamento)

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
                
            # --- DESENHO DAS PEDRAS COM O NOVO DESTAQUE DE PUZZLE ---
            if self.cenario_atual == "ESTRADA_2":
                for pedra in self.pedras_deslizamento:
                    # Preenchimento com a cor mineral clara
                    pygame.draw.rect(tela, COR_PEDRA_DESLIZAMENTO, pedra)
                    # Borda destacada com o cinza azulado para dar profundidade
                    pygame.draw.rect(tela, COR_BORDA_PEDRA, pedra, 2)