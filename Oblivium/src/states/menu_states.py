# src/states/menu_states.py
import pygame
from src.states.states import State

class MenuState(State):
    def __init__(self, game):
        super().__init__(game)
        
    def handle_events(self, eventos, teclas):
        for evento in eventos:
            if evento.type == pygame.KEYDOWN:
                if evento.key in [pygame.K_UP, pygame.K_w]:
                    if self.game.menu.selecionada <= 0:
                        self.game.menu.selecionada = len(self.game.menu.opcoes) - 1
                    else:
                        self.game.menu.selecionada -= 1
                elif evento.key in [pygame.K_DOWN, pygame.K_s]:
                    if self.game.menu.selecionada == -1 or self.game.menu.selecionada >= len(self.game.menu.opcoes) - 1:
                        self.game.menu.selecionada = 0
                    else:
                        self.game.menu.selecionada += 1
                elif evento.key in [pygame.K_RETURN, pygame.K_SPACE]:
                    if self.game.menu.selecionada != -1:
                        self.executar_opcao()
                    
            elif evento.type == pygame.MOUSEMOTION:
                self.game.menu.atualizar_mouse(evento.pos)
                
            elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                opcao = self.game.menu.clicar_mouse(evento.pos)
                if opcao: 
                    self.executar_opcao(opcao)

    def executar_opcao(self, opcao_clicada=None):
        if opcao_clicada is not None:
            opcao = opcao_clicada
        elif 0 <= self.game.menu.selecionada < len(self.game.menu.opcoes):
            opcao = self.game.menu.opcoes[self.game.menu.selecionada]
        else:
            return
        
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

    def update(self):
        dt = self.game.clock.get_time() / 1000.0 if hasattr(self.game, 'clock') else 0.016
        # Limita dt para evitar saltos bruscos em pausas de sistema
        dt = min(dt, 0.05) if dt > 0 else 0.016
        self.game.menu.atualizar(dt)
            
    def draw(self, tela):
        self.game.menu.desenhar(tela)