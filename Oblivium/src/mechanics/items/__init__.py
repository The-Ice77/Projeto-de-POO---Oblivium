# src/mechanics/items/__init__.py
"""Subpacote de itens, inventário, fabricação (crafting) e lojas."""

from .items import (
    ItemBase,
    ConsumivelItem,
    EquipamentoItem,
    GrimorioItem,
    EnsinamentoFeiticoItem,
    MaterialItem,
    ItemChave,
)
from .item_factory import ItemFactory
from .inventory import ItemSlot, Inventario
from .crafting import Receita, CraftingManager
from .shop import ItemMercadoria, Loja

__all__ = [
    "ItemBase",
    "ConsumivelItem",
    "EquipamentoItem",
    "GrimorioItem",
    "EnsinamentoFeiticoItem",
    "MaterialItem",
    "ItemChave",
    "ItemFactory",
    "ItemSlot",
    "Inventario",
    "Receita",
    "CraftingManager",
    "ItemMercadoria",
    "Loja",
]
