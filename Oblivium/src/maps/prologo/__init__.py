# src/maps/prologo/__init__.py
"""Subpacote de cenários do Prólogo (Cabana de Halia, Estrada da Floresta e Bloqueio Rochoso)."""

from .mapa_casa import MapaCasa
from .mapa_estrada import MapaEstrada
from .mapa_estrada_2 import MapaEstrada2

__all__ = [
    "MapaCasa",
    "MapaEstrada",
    "MapaEstrada2",
]
