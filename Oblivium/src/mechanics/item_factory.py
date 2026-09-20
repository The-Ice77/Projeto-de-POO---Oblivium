# src/mechanics/item_factory.py
import json
import os
import sys

_raiz_projeto = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _raiz_projeto not in sys.path:
    sys.path.insert(0, _raiz_projeto)

from src.mechanics.items import (
    ItemBase, ConsumivelItem, EquipamentoItem, GrimorioItem, MaterialItem, ItemChave
)

class ItemFactory:
    """
    Fábrica centralizada de itens (Factory Method / Registry).
    Lê o catálogo de src/data/items.json e instancia os objetos polimórficos correspondentes.
    """
    _catalogo_cache = None
    _CAMINHO_JSON = os.path.join(os.path.dirname(__file__), "..", "data", "items.json")

    @classmethod
    def carregar_catalogo(cls, recarregar=False):
        """Carrega e armazena em cache os dados do JSON de itens."""
        if cls._catalogo_cache is not None and not recarregar:
            return cls._catalogo_cache

        catalogo = {}
        if os.path.exists(cls._CAMINHO_JSON):
            try:
                with open(cls._CAMINHO_JSON, "r", encoding="utf-8") as f:
                    dados = json.load(f)
                    for categoria_chave, itens in dados.items():
                        for item_id, item_info in itens.items():
                            catalogo[item_id] = item_info
            except Exception as e:
                print(f"[ItemFactory] Erro ao carregar items.json: {e}. Usando catálogo fallback.")
                catalogo = cls._obter_fallback()
        else:
            catalogo = cls._obter_fallback()

        cls._catalogo_cache = catalogo
        return cls._catalogo_cache

    @classmethod
    def criar_item(cls, item_id, nivel_upgrade=0, **kwargs):
        """Alias de conveniência para criar()."""
        return cls.criar(item_id, nivel_upgrade=nivel_upgrade)

    @classmethod
    def criar(cls, item_id, nivel_upgrade=0):
        """
        Cria uma nova instância polimórfica de ItemBase baseada no item_id.
        """
        catalogo = cls.carregar_catalogo()
        info = catalogo.get(item_id)
        if not info:
            print(f"[ItemFactory] Item '{item_id}' não encontrado no catálogo!")
            return None

        categoria = info.get("categoria", "").upper()

        if categoria == "CONSUMIVEL":
            return ConsumivelItem(
                id_item=info["id"],
                nome=info["nome"],
                descricao=info.get("descricao", ""),
                tipo_consumivel=info.get("tipo_consumivel", "CURA_HP"),
                valor_efeito=info.get("valor_efeito", 0),
                usavel_combate=info.get("usavel_combate", True),
                usavel_fora=info.get("usavel_fora", True),
                condicao_aplicada=info.get("condicao_aplicada", None),
                raridade=info.get("raridade", "COMUM"),
                preco_compra=info.get("preco_compra", 0),
                preco_venda=info.get("preco_venda", 0),
                acumulavel=info.get("acumulavel", True),
                quantidade_maxima=info.get("quantidade_maxima", 20),
                icone_sprite=info.get("icone_sprite", None)
            )

        elif categoria == "EQUIPAMENTO":
            return EquipamentoItem(
                id_item=info["id"],
                nome=info["nome"],
                descricao=info.get("descricao", ""),
                slot=info.get("slot", "ROUPA"),
                bonus_atributos=info.get("bonus_atributos", {}),
                bonus_stats=info.get("bonus_stats", {}),
                nivel_upgrade=nivel_upgrade if nivel_upgrade > 0 else info.get("nivel_upgrade", 0),
                tier=info.get("tier", 1),
                raridade=info.get("raridade", "COMUM"),
                preco_compra=info.get("preco_compra", 0),
                preco_venda=info.get("preco_venda", 0),
                icone_sprite=info.get("icone_sprite", None)
            )

        elif categoria == "GRIMORIO":
            return GrimorioItem(
                id_item=info["id"],
                nome=info["nome"],
                descricao=info.get("descricao", ""),
                magia_id=info.get("magia_id", None),
                bonus_stats=info.get("bonus_stats", {}),
                raridade=info.get("raridade", "RARO"),
                preco_compra=info.get("preco_compra", 0),
                preco_venda=info.get("preco_venda", 0),
                icone_sprite=info.get("icone_sprite", None)
            )

        elif categoria == "MATERIAL":
            return MaterialItem(
                id_item=info["id"],
                nome=info["nome"],
                descricao=info.get("descricao", ""),
                raridade=info.get("raridade", "COMUM"),
                preco_compra=info.get("preco_compra", 0),
                preco_venda=info.get("preco_venda", 0),
                acumulavel=info.get("acumulavel", True),
                quantidade_maxima=info.get("quantidade_maxima", 99),
                icone_sprite=info.get("icone_sprite", None)
            )

        elif categoria == "CHAVE":
            return ItemChave(
                id_item=info["id"],
                nome=info["nome"],
                descricao=info.get("descricao", ""),
                raridade=info.get("raridade", "INCOMUM"),
                preco_compra=info.get("preco_compra", 0),
                preco_venda=0,
                acumulavel=False,
                quantidade_maxima=1,
                icone_sprite=info.get("icone_sprite", None)
            )

        # Fallback para item genérico
        return ConsumivelItem(
            id_item=info.get("id", item_id),
            nome=info.get("nome", item_id),
            descricao=info.get("descricao", "")
        )

    @classmethod
    def obter_todos_itens(cls):
        """Retorna todos os IDs e nomes cadastrados."""
        return cls.carregar_catalogo()

    @classmethod
    def _obter_fallback(cls):
        """Catálogo de segurança em memória caso o arquivo JSON falhe."""
        return {
            "pocao_vida_menor": {
                "id": "pocao_vida_menor",
                "nome": "Poção de Vida Menor",
                "categoria": "CONSUMIVEL",
                "tipo_consumivel": "CURA_HP",
                "valor_efeito": 35,
                "preco_compra": 25,
                "preco_venda": 12
            },
            "manto_arcanista": {
                "id": "manto_arcanista",
                "nome": "Manto Arcanista",
                "categoria": "EQUIPAMENTO",
                "slot": "ROUPA",
                "preco_compra": 60,
                "preco_venda": 30
            }
        }
