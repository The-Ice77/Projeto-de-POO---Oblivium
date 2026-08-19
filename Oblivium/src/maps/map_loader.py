# src/maps/map_loader.py
import pygame
from src.entities.item import Item 
from src.utils.resource_manager import ResourceManager
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
        self.cenario_atual = "CASA" 
        
        # ==========================================
        # CARREGAMENTO DE IMAGENS (SPRITES)
        # ==========================================
        # Fundos de Cenário
        self.fundo_casa = ResourceManager.carregar_imagem("assets/maps/fundo_casa.png", (self.largura_tela, self.altura_tela))
        self.fundo_estrada = ResourceManager.carregar_imagem("assets/maps/fundo_estrada.png", (self.largura_tela, self.altura_tela))
        
        # Objetos e Props
        self.sprite_porta_fechada = ResourceManager.carregar_imagem("assets/props/porta_fechada.png", (40, 100))
        self.sprite_porta_aberta = ResourceManager.carregar_imagem("assets/props/porta_aberta.png", (40, 100))
        
        # Móveis Atualizados: Estante e Cama
        self.sprite_estante = ResourceManager.carregar_imagem("assets/props/estante.png", (110, 180))
        self.sprite_cama = ResourceManager.carregar_imagem("assets/props/cama.png", (100, 140))
        
        self.sprite_pedra = ResourceManager.carregar_imagem("assets/props/pedra.png") # Escalonado dinamicamente no draw

        # ==========================================
        # DADOS DO CENÁRIO: CASA (HITBOXES INVISÍVEIS)
        # ==========================================
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
            pygame.Rect(90, 90, 100, 140),         # Cama 
            pygame.Rect(400, 90, 110, 80),        # Estante / Armário 
        ]
        
        self.limites_varanda = [
            pygame.Rect(550, 45, 150, 5),      
            pygame.Rect(550, 650, 150, 5),    
        ]
        self.porta_aberta = False 
        self.itens_no_chao = []

        # ==========================================
        # DADOS DO CENÁRIO: ESTRADA (HITBOXES INVISÍVEIS)
        # ==========================================
        self.area_estrada = pygame.Rect(0, 250, largura_tela, 220)
        self.barreiras_estrada = [
            pygame.Rect(0, 0, largura_tela, 250),      
            pygame.Rect(0, 470, largura_tela, 250)     
        ]

        self.hitboxes = []
        self.pedras_deslizamento = [] 
        
        self.carregar_cenario("CASA")

    def carregar_cenario(self, nome_cenario):
        self.cenario_atual = nome_cenario
        self.hitboxes = []
        self.itens_no_chao = []

        if self.cenario_atual == "CASA":
            self.hitboxes.extend(self.paredes_casa)
            self.hitboxes.extend(self.moveis)
            self.hitboxes.extend(self.limites_varanda)
            if not getattr(self, 'porta_aberta', False):
                self.hitboxes.append(self.porta)
                
            itens_brutos = [
                Item("A Bolsa de Moedas", 420, 300, 25, 25, COLOR_BOLSA_MOEDAS), 
                Item("O Livro Antigo", 300, 450, 25, 30, COLOR_LIVRO_ANTIGO),    
                Item("O Cajado Mágico", 230, 200, 10, 60, COLOR_CAJADO_MAGICO)    
            ]
            
            itens_brutos[0].id_unico = "item_moedas"
            itens_brutos[1].id_unico = "item_livro"
            itens_brutos[2].id_unico = "item_cajado"
            
            coletados = getattr(self.game, 'itens_coletados', [])
            for item in itens_brutos:
                if item.id_unico not in coletados:
                    self.itens_no_chao.append(item)
                
        elif self.cenario_atual == "ESTRADA":
            self.hitboxes.extend(self.barreiras_estrada)
            self.hitboxes.append(pygame.Rect(0, 0, 20, self.altura_tela))
            self.hitboxes.append(pygame.Rect(1220, 0, 30, self.altura_tela))
        
        elif self.cenario_atual == "ESTRADA_2":
            self.hitboxes.extend(self.barreiras_estrada)
            self.hitboxes.append(pygame.Rect(0, 0, 20, self.altura_tela))
            self.pedras_deslizamento = [
                pygame.Rect(1100, 250, 80, 70), pygame.Rect(1150, 310, 90, 80),
                pygame.Rect(1080, 320, 80, 80), pygame.Rect(1120, 390, 100, 90)
            ]
            self.hitboxes.extend(self.pedras_deslizamento)

    def abrir_porta(self):
        self.porta_aberta = True
        self.carregar_cenario("CASA")

    def desenhar(self, tela):
        if self.cenario_atual == "CASA":
            # 1. Tenta desenhar o Fundo da Casa
            if self.fundo_casa:
                tela.blit(self.fundo_casa, (0, 0))
            else:
                tela.fill(CENARIO_FUNDO_FORA)
                pygame.draw.rect(tela, CENARIO_MADEIRA_VARANDA, self.varanda_madeira)
                pygame.draw.rect(tela, CENARIO_PAREDE_CASA, self.varanda_madeira, 2) 
                pygame.draw.rect(tela, CENARIO_CHAO_CASA, self.area_chao_casa)
                for parede in self.paredes_casa:
                    pygame.draw.rect(tela, CENARIO_PAREDE_CASA, parede)
                    pygame.draw.rect(tela, CENARIO_FUNDO_FORA, parede, 2)
                for limite in self.limites_varanda:
                    pygame.draw.rect(tela, CENARIO_PAREDE_CASA, limite)

            # 2. Desenha a Porta
            if not self.porta_aberta:
                if self.sprite_porta_fechada:
                    tela.blit(self.sprite_porta_fechada, self.porta.topleft)
                else:
                    pygame.draw.rect(tela, CENARIO_PORTA, self.porta)
                    pygame.draw.rect(tela, CENARIO_PAREDE_CASA, self.porta, 2)
            else:
                if self.sprite_porta_aberta:
                    tela.blit(self.sprite_porta_aberta, self.porta.topleft)
                else:
                    pygame.draw.rect(tela, CENARIO_CHAO_CASA, self.porta, 2)

            # 3. Desenha os Móveis (Estante [0] e Cama [1])
            sprites_moveis = [self.sprite_cama, self.sprite_estante]
            for i, movel in enumerate(self.moveis):
                sprite = sprites_moveis[i] if i < len(sprites_moveis) else None
                if sprite:
                    tela.blit(sprite, movel.topleft)
                else:
                    pygame.draw.rect(tela, CENARIO_MOVEIS, movel)
                    pygame.draw.rect(tela, CENARIO_PAREDE_CASA, movel, 2)
                    
            # 4. Desenha Itens
            for item in self.itens_no_chao:
                item.desenhar(tela)
                
        elif self.cenario_atual in ["ESTRADA", "ESTRADA_2"]:
            if self.fundo_estrada:
                tela.blit(self.fundo_estrada, (0, 0))
            else:
                tela.fill(CENARIO_GRAMA_CINZA)
                pygame.draw.rect(tela, CENARIO_ESTRADA, self.area_estrada)
                for barreira in self.barreiras_estrada:
                    pygame.draw.rect(tela, CENARIO_BARREIRAS, barreira)
                    pygame.draw.rect(tela, CENARIO_FUNDO_FORA, barreira, 1) 
                
            if self.cenario_atual == "ESTRADA_2":
                for pedra in self.pedras_deslizamento:
                    if self.sprite_pedra:
                        img_escalada = pygame.transform.scale(self.sprite_pedra, (pedra.width, pedra.height))
                        tela.blit(img_escalada, pedra.topleft)
                    else:
                        pygame.draw.rect(tela, COR_PEDRA_DESLIZAMENTO, pedra)
                        pygame.draw.rect(tela, COR_BORDA_PEDRA, pedra, 2)