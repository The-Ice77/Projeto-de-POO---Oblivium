# src/mechanics/minigames/__init__.py
from .minigame_base import MinigameBase
from .minigames_magia import MinigameTiming, MinigameMash, _tocar_sfx_seguro
from .minigame_ferraria import MinigameFerraria, ParticulaRocha
from .minigame_curandeira import MinigameCurandeira, ParticulaPetala

__all__ = [
    "MinigameBase",
    "MinigameTiming",
    "MinigameMash",
    "_tocar_sfx_seguro",
    "MinigameFerraria",
    "ParticulaRocha",
    "MinigameCurandeira",
    "ParticulaPetala",
]
