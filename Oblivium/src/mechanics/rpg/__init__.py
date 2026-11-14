# src/mechanics/rpg/__init__.py
"""Subpacote de regras de RPG: atributos, condições, habilidades e grimório."""

from .attributes import Atributos
from .conditions import Condicao
from .skills import (
    AcaoCombate,
    AtaqueFisico,
    MagiaOfensiva,
    MagiaCura,
    AcaoDefender,
    AcaoFoco,
    SkillsRegistry,
    ActionCatalog,
)
from .grimorio import GrimorioHalia

__all__ = [
    "Atributos",
    "Condicao",
    "AcaoCombate",
    "AtaqueFisico",
    "MagiaOfensiva",
    "MagiaCura",
    "AcaoDefender",
    "AcaoFoco",
    "SkillsRegistry",
    "ActionCatalog",
    "GrimorioHalia",
]
