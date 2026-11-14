# src/maps/mapa_oakhaven.py
"""
Fachada de compatibilidade retroativa para os cenários da região de Oakhaven.
As implementações modulares residem em ``src/maps/oakhaven/``.
"""

from src.maps.oakhaven import (
    MapaOakhaven,
    MapaOakhavenDestruida,
    MapaNinhoDragao,
    MapaOrlaNorte,
    _carregar_tiles_terreno,
    _renderizar_grade_autotile,
)

__all__ = [
    "MapaOakhaven",
    "MapaOakhavenDestruida",
    "MapaNinhoDragao",
    "MapaOrlaNorte",
    "_carregar_tiles_terreno",
    "_renderizar_grade_autotile",
]
