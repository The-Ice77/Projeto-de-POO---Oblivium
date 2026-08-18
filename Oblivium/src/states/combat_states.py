# src/states/combat_states.py
import pygame
from src.states.states import State

class CombatState(State):
    def __init__(self, game):
        super().__init__(game)

    def handle_events(self, eventos, teclas):
        
        for evento in eventos:
            self.game.tela_combate.processar_eventos(evento)

    def update(self):
        # Verifica se o combate acabou (Vitória ou Fuga)
        resultado = self.game.tela_combate.atualizar()
        if resultado == "FUGIU" or resultado == "VITORIA":
            # Se for apenas o tutorial, voltamos para o mapa de exploração
            self.game.mudar_estado("JOGANDO")
            self.game.inimigos_em_cena.clear()

    def draw(self, tela):
        # Desenha o fundo, barras e menus do combate
        self.game.tela_combate.desenhar(tela)
        # Garante que o efeito de transição de tela apareça por cima de tudo se necessário
        self.game.transicao.desenhar(tela)