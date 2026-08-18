# src/states/inventory_states.py
import pygame
from src.states.states import State
from src.utils.colors import (
    PRETO, BRANCO, UI_FUNDO_PADRAO, CINZA_CLARO, 
    UI_TEXTO_DESTAQUE, UI_TEXTO_APAGADO
)

class InventoryState(State):
    def __init__(self, game):
        super().__init__(game)
        self.overlay = pygame.Surface((self.game.LARGURA, self.game.ALTURA))
        self.overlay.fill(PRETO)
        self.overlay.set_alpha(200) # Fundo semi-transparente
        
        self.fonte_titulo = pygame.font.Font(None, 45)
        self.fonte_sub = pygame.font.Font(None, 28)
        self.fonte_texto = pygame.font.Font(None, 22)
        
        # --- ESTRUTURA DE SLOTS DE EQUIPAMENTO E ITENS ---
        # Definimos os retângulos (Rects) para gerocar cliques e arrastar no futuro
        self.largura_inv, self.altura_inv = 1000, 620
        self.x_inv = (self.game.LARGURA - self.largura_inv) // 2
        self.y_inv = (self.game.ALTURA - self.altura_inv) // 2
        
        # Slots de Equipamento (Esquerda)
        # 1. Roupa / Armadura
        self.slot_roupa = pygame.Rect(self.x_inv + 40, self.y_inv + 110, 80, 110)
        # 2. Cajado
        self.slot_cajado = pygame.Rect(self.x_inv + 140, self.y_inv + 110, 70, 110)
        
        # 3. Grimórios (Até 4 slots alinhados)
        self.slots_grimorios = [
            pygame.Rect(self.x_inv + 40 + (i * 90), self.y_inv + 265, 80, 80)
            for i in range(4)
        ]
        
        # 4. Grelha de Itens Dispersos / Inventário Geral (Direita)
        self.slots_gerais = []
        linhas, colunas = 4, 4
        inicio_x_grid = self.x_inv + 480
        inicio_y_grid = self.y_inv + 110
        tamanho_celula = 95
        
        for l in range(linhas):
            for c in range(colunas):
                r = pygame.Rect(inicio_x_grid + (c * tamanho_celula), inicio_y_grid + (l * tamanho_celula), 85, 85)
                self.slots_gerais.append(r)
                
        # Controle de Arrastar (Drag-and-Drop)
        self.item_selecionado = None

    def handle_events(self, eventos, teclas):
        for evento in eventos:
            if evento.type == pygame.KEYDOWN:
                # Fechar com ESC ou apertando 'I' de novo
                if evento.key == pygame.K_ESCAPE or evento.key == self.game.controles.get("Inventário", pygame.K_i):
                    self.game.mudar_estado("JOGANDO")
                    return
                    
            elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                pos = evento.pos
                # Futura lógica de clique/arrastar nos slots
                pass

    def update(self):
        pass

    def draw(self, tela):
        # Desenha o jogo por baixo
        self.game.estados["JOGANDO"].draw(tela)
        
        # Desenha a película escura por cima
        tela.blit(self.overlay, (0, 0))
 
        # PAINEL PRINCIPAL (Bordas Estritamente Quadradas)

        pygame.draw.rect(tela, UI_FUNDO_PADRAO, (self.x_inv, self.y_inv, self.largura_inv, self.altura_inv))
        pygame.draw.rect(tela, CINZA_CLARO, (self.x_inv, self.y_inv, self.largura_inv, self.altura_inv), 2)
        
        # Título
        txt_titulo = self.fonte_titulo.render("Inventário e Equipamentos", True, UI_TEXTO_DESTAQUE)
        tela.blit(txt_titulo, (self.x_inv + 40, self.y_inv + 30))
        
        # SEÇÃO ESQUERDA: EQUIPAMENTOS

        txt_eq = self.fonte_sub.render("Equipamento Atual", True, CINZA_CLARO)
        tela.blit(txt_eq, (self.x_inv + 40, self.y_inv + 80))
        
        # Slot Roupa
        pygame.draw.rect(tela, (25, 25, 30), self.slot_roupa)
        pygame.draw.rect(tela, CINZA_CLARO, self.slot_roupa, 1)
        lbl_roupa = self.fonte_texto.render("Roupa", True, UI_TEXTO_APAGADO)
        tela.blit(lbl_roupa, (self.slot_roupa.x + 15, self.slot_roupa.centery - 10))
        
        # Slot Cajado
        pygame.draw.rect(tela, (25, 25, 30), self.slot_cajado)
        pygame.draw.rect(tela, CINZA_CLARO, self.slot_cajado, 1)
        lbl_cajado = self.fonte_texto.render("Cajado", True, UI_TEXTO_APAGADO)
        tela.blit(lbl_cajado, (self.slot_cajado.x + 12, self.slot_cajado.centery - 10))
        
        # Slots Grimórios (4)
        txt_gr = self.fonte_sub.render("Grimórios Equipados (0/4)", True, CINZA_CLARO)
        tela.blit(txt_gr, (self.x_inv + 40, self.y_inv + 235))
        
        for i, rect_g in enumerate(self.slots_grimorios):
            pygame.draw.rect(tela, (25, 25, 30), rect_g)
            pygame.draw.rect(tela, CINZA_CLARO, rect_g, 1)
            lbl_num = self.fonte_texto.render(str(i+1), True, UI_TEXTO_APAGADO)
            tela.blit(lbl_num, (rect_g.x + 8, rect_g.y + 6))

        # SEÇÃO DIREITA: ITENS DISPERSOS / GRELHA

        txt_geral = self.fonte_sub.render("Bolsa / Itens Gerais", True, CINZA_CLARO)
        tela.blit(txt_geral, (self.x_inv + 480, self.y_inv + 80))
        
        for rect_geral in self.slots_gerais:
            pygame.draw.rect(tela, (25, 25, 30), rect_geral)
            pygame.draw.rect(tela, CINZA_CLARO, rect_geral, 1)

        # Instrução de rodapé
        txt_rodape = self.fonte_texto.render("[ESC] ou [I] para fechar", True, UI_TEXTO_APAGADO)
        tela.blit(txt_rodape, (self.x_inv + 40, self.y_inv + self.altura_inv - 35))