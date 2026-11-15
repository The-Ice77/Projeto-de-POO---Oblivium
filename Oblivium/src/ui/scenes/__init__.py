# src/ui/scenes/__init__.py
"""Subpacote de cenas narrativas e telas especiais de UI (Intro, Flashback e Despertar de Memória)."""

from .intro import Intro
from .flashback import Flashback
from .tela_despertar import TelaDespertarMemoria
from .texto_editorial import ApresentacaoTextoEditorial, obter_multiplicador_velocidade_texto

__all__ = [
    "ApresentacaoTextoEditorial",
    "Intro",
    "Flashback",
    "TelaDespertarMemoria",
    "obter_multiplicador_velocidade_texto",
]
