# src/states/menu_states.py
import pygame
from src.states.states import State

class MenuState(State):
    def __init__(self, game):
        super().__init__(game)
        
    def handle_events(self, eventos, teclas):
        for evento in eventos:
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_UP:
                    self.game.menu.selecionada = (self.game.menu.selecionada - 1) % len(self.game.menu.opcoes)
                elif evento.key == pygame.K_DOWN:
                    self.game.menu.selecionada = (self.game.menu.selecionada + 1) % len(self.game.menu.opcoes)
                elif evento.key == pygame.K_RETURN:
                    self.executar_opcao()
                    
            elif evento.type == pygame.MOUSEMOTION:
                self.game.menu.atualizar_mouse(evento.pos)
                
            elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                opcao = self.game.menu.clicar_mouse(evento.pos)
                if opcao: 
                    self.executar_opcao(opcao)

    def executar_opcao(self, opcao_clicada=None):
        opcao = opcao_clicada or self.game.menu.opcoes[self.game.menu.selecionada]
        
        if opcao == "Continuar":
            self.game.acao_slots = "CARREGAR"
            self.game.origem_slots = "MENU"
            self.game.mudar_estado("SLOTS")
            
        elif opcao == "Novo Jogo" or opcao == "Jogar":
            # Abre a tela de saves exigindo que o jogador escolha um slot vazio
            self.game.acao_slots = "NOVO_JOGO"
            self.game.origem_slots = "MENU"
            self.game.mudar_estado("SLOTS")
            
        elif opcao == "Configurações":
            self.game.origem_configuracoes = "MENU"
            self.game.mudar_estado("CONFIGURACOES")
            
        elif opcao == "Créditos":
            self.game.mudar_estado("CREDITOS")
            
        elif opcao == "Sair":
            self.game.running = False
            
    def draw(self, tela):
        # O desenho real dos textos ("Jogar", "Sair") e do fundo acontece na UI do Menu,
        # onde as constantes FUNDO_MENU, TEXTO_MENU_PADRAO e TEXTO_MENU_SELECIONADO devem ser usadas.
        self.game.menu.desenhar(tela)