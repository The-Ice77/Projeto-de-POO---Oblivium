# src/states/intro_states.py
import pygame
from src.states.states import State

class IntroState(State):
    def __init__(self, game):
        super().__init__(game)
        
    def handle_events(self, eventos, teclas):
        for evento in eventos:
            if evento.type == pygame.KEYDOWN and evento.key == pygame.K_RETURN:
                self.game.intro.pular()

    def update(self):
        # Se a introdução terminar de rodar, muda automaticamente para o jogo livre
        if not self.game.intro.atualizar():
            pygame.event.clear()
            # Inicializa o diálogo inicial da Halia na caixa de diálogo global
            self.game.caixa_dialogo.iniciar_dialogo([
                {"autor": "Pensamento", "texto": "Hm... Que péssima noite de sono. Minhas costas estão me matando depois de dormir aqui."},
                {"autor": "Pensamento", "texto": "Eu preciso pegar as minhas coisas e ir logo, o carroceiro que contratei já deve estar me esperando do lado de fora da casa."},
                {"autor": "Narrador", "texto": "Encontre e pegue: A Bolsa de moedas, O Livro antigo e O Cajado mágico de Halia."},
                {"autor": "Narrador", "texto": "Para coletar os itens encontrados se mova utilizando W,A,S,D ou as setas do teclado e aparte a tecla E"}
            ])
            self.game.mudar_estado("JOGANDO")

    def draw(self, tela):
        # DE:
        # self.game.intro.desenhar(tela)
        
        # PARA:
        self.game.intro.draw(tela)