# src/states/menus/__init__.py
"""Subpacote de estados de menus, pausa, configurações, controles, slots, conquistas e créditos."""

from .menu_states import MenuState
from .pause_states import PauseState
from .settings_states import SettingsState
from .controles_state import ControlesState
from .selecao_controles_state import SelecaoControlesState
from .slots_states import SlotsState, formatar_tempo
from .conquistas_state import ConquistasState
from .credits_states import CreditsState

__all__ = [
    "MenuState",
    "PauseState",
    "SettingsState",
    "ControlesState",
    "SelecaoControlesState",
    "SlotsState",
    "formatar_tempo",
    "ConquistasState",
    "CreditsState",
]
