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
        # O motor de combate gerencia turnos e dispara callbacks ao finalizar
        self.game.tela_combate.atualizar()

    def draw(self, tela):
        # Desenha a arena de combate, HUD, menus e efeitos
        self.game.tela_combate.desenhar(tela)
        # Transições de tela
        if hasattr(self.game, 'transicao') and self.game.transicao.estado != "INATIVO":
            self.game.transicao.desenhar(tela)