# src/mechanics/minigame_base.py
from abc import ABC, abstractmethod


class MinigameBase(ABC):
    """
    Contrato base para minigames interativos de Oblivium.
    Unifica ciclo de ativação, entrada, atualização e renderização sem remover
    apelidos específicos usados por versões anteriores.
    """

    def __init__(self):
        self.ativo = False

    @abstractmethod
    def iniciar(self, *args, **kwargs):
        """Inicia e ativa o minigame."""

    @abstractmethod
    def handle_events(self, eventos, teclas=None):
        """Processa os eventos/entradas do minigame."""

    @abstractmethod
    def atualizar(self, dt=None):
        """Atualiza a lógica do minigame."""

    @abstractmethod
    def desenhar(self, tela):
        """Renderiza o minigame na tela."""

    # Apelidos de retrocompatibilidade (§3)
    def draw(self, tela):
        return self.desenhar(tela)

    def update(self, dt=None):
        return self.atualizar(dt)
