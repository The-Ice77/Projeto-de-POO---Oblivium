# src/mechanics/cena_base.py
from abc import ABC, abstractmethod


class CenaBase(ABC):
    """
    Contrato base para cenas narrativas, flashbacks, telas solenes e cutscenes.
    Garante ciclo de vida uniforme (`iniciar`, `handle_event`, `atualizar`,
    `desenhar`, `pular`, `finalizar`) e execução idempotente de conclusão.
    """

    def __init__(self, game=None, on_concluido=None):
        self.game = game
        self.ativo = False
        self.concluido = False
        self.on_concluido = on_concluido
        self._callback_executado = False

    def _reiniciar_estado_execucao(self, on_concluido=None):
        """Prepara flags internas para um novo ciclo da cena."""
        self.concluido = False
        self._callback_executado = False
        if on_concluido is not None:
            self.on_concluido = on_concluido

    def _executar_callback_conclusao(self):
        """Executa o callback de conclusão no máximo uma única vez por ciclo."""
        if self._callback_executado:
            return False
        self._callback_executado = True
        if callable(self.on_concluido):
            self.on_concluido()
        return True

    @abstractmethod
    def iniciar(self, *args, **kwargs):
        """Ativa e inicializa a cena."""

    def handle_event(self, evento):
        """Processa eventos de entrada enquanto a cena estiver ativa."""
        return False

    @abstractmethod
    def atualizar(self, dt=None):
        """Atualiza o estado da cena no quadro atual."""

    @abstractmethod
    def desenhar(self, tela):
        """Renderiza a cena na superfície alvo."""

    def finalizar(self):
        """Encerra a cena e dispara o callback de conclusão uma única vez."""
        self.ativo = False
        self.concluido = True
        return self._executar_callback_conclusao()

    def pular(self):
        """Pula a cena preservando todas as consequências narrativas de conclusão."""
        return self.finalizar()

    # Apelidos de retrocompatibilidade (§3)
    def draw(self, tela):
        return self.desenhar(tela)

    def update(self, dt=None):
        return self.atualizar(dt)
