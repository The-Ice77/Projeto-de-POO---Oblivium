# src/states/intro_states.py
import inspect
import pygame
from src.states.states import State

class IntroState(State):
    def __init__(self, game):
        super().__init__(game)
        
    def handle_events(self, eventos, teclas):
        for evento in eventos:
            if evento.type == pygame.KEYDOWN:
                if evento.key in [pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE, pygame.K_e]:
                    self.game.intro.avancar()
                elif evento.key == pygame.K_ESCAPE:
                    self.game.intro.pular()
            elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                self.game.intro.avancar()

    def update(self):
        # Se a introdução terminar de rodar, muda automaticamente para o jogo livre
        dt = getattr(self.game, "dt", 1.0 / 60.0)
        atualizar_fn = self.game.intro.atualizar
        aceita_dt = any(
            p.kind in (
                inspect.Parameter.POSITIONAL_ONLY,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                inspect.Parameter.VAR_POSITIONAL,
            )
            for p in inspect.signature(atualizar_fn).parameters.values()
        )
        ativo = atualizar_fn(dt) if aceita_dt else atualizar_fn()
        if not ativo:
            pygame.event.clear()
            # Inicializa o diálogo inicial da Halia na caixa de diálogo global
            self.game.caixa_dialogo.iniciar_dialogo("despertar_cabana")
            self.game.mudar_estado("JOGANDO")

    def draw(self, tela):
        self.game.intro.draw(tela)