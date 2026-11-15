# src/states/states.py
from abc import ABC, abstractmethod

class State(ABC):
    """
    Classe base abstrata para todos os estados do jogo no Padrão State.
    Define o contrato essencial de eventos, atualização lógica e renderização.
    """
    def __init__(self, game):
        self.game = game

    def ao_entrar(self, estado_anterior=None):
        """Apresentação de uma entrada real, sem repetir no construtor ou a cada quadro."""

    def ao_sair(self, proximo_estado=None):
        """Libera a apresentação do estado antes de entrar no próximo."""

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
