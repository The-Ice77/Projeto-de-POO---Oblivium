# src/states/inventory_tabs/__init__.py
"""
Módulo de Renderizadores Especializados para as Abas do Menu de Inventário de Oblivium:
- TabInventarioRenderer: Equipamentos arcanos, Grimórios e grid da Bolsa.
- TabPerfilRenderer: Recursos vitais, Moedas e Ficha D20 de Atributos.
- TabMagiaRenderer: Catálogo com scroll e ficha de detalhes de magias.
- TabCraftingRenderer: Bancada de criação, forja e alquimia.
"""
from src.states.inventory_tabs.tab_inventario import TabInventarioRenderer
from src.states.inventory_tabs.tab_perfil import TabPerfilRenderer
from src.states.inventory_tabs.tab_magia import TabMagiaRenderer
from src.states.inventory_tabs.tab_crafting import TabCraftingRenderer

__all__ = [
    "TabInventarioRenderer",
    "TabPerfilRenderer",
    "TabMagiaRenderer",
    "TabCraftingRenderer"
]
