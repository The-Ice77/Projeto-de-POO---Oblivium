# states/state.py
# Candidata a ser abstrata
import pygame

class State:
    def __init__(self, game):
        self.game = game

    def handle_events(self, eventos, teclas):
        pass

    def update(self):
        pass

    def draw(self, tela):
        pass
