# src/states/states.py
from abc import ABC, abstractmethod
import pygame

class State(ABC):
    """
    Classe base abstrata para todos os estados do jogo no Padrão State.
    Define o contrato essencial de eventos, atualização lógica e renderização.
    """
    def __init__(self, game):
        self.game = game

    @abstractmethod
    def handle_events(self, eventos, teclas):
        """Processa eventos de entrada (teclado, mouse) do estado."""
        pass

    @abstractmethod
    def update(self):
        """Atualiza a lógica interna e temporizadores do estado."""
        pass

    @abstractmethod
    def draw(self, tela):
        """Renderiza os elementos visuais do estado na tela."""
        pass
