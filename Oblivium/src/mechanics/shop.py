# src/mechanics/shop.py
import os
import sys

_raiz_projeto = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _raiz_projeto not in sys.path:
    sys.path.insert(0, _raiz_projeto)

from src.mechanics.items import ItemBase, ItemChave
from src.mechanics.item_factory import ItemFactory

class ItemMercadoria:
    """Representa um item à venda no estoque de um mercador."""
    def __init__(self, item_id, preco_compra=None, preco_venda=None, estoque_inicial=5, estoque_maximo=10):
        self.item_id = item_id
        self.item_template = ItemFactory.criar(item_id)
        self.preco_compra = preco_compra if preco_compra is not None else (self.item_template.preco_compra if self.item_template else 10)
        self.preco_venda = preco_venda if preco_venda is not None else (self.item_template.preco_venda if self.item_template else 5)
        self.estoque_atual = estoque_inicial
        self.estoque_maximo = estoque_maximo

    @property
    def disponivel(self):
        return self.estoque_atual > 0


class Loja:
    """
    Gerencia a economia de compra e venda de um mercador com estoque dinâmico e limitado.
    """
    def __init__(self, nome="Empório do Viajante", tipo="GERAL"):
        self.nome = nome
        self.tipo = tipo
        self.mercadorias = {} # {item_id: ItemMercadoria}
        self.inicializar_estoque_padrao()

    def inicializar_estoque_padrao(self):
        """Define os itens e estoques iniciais do mercador itinerante."""
        itens_iniciais = [
            ("pocao_vida_menor", 25, 12, 8, 15),
            ("elixir_mana_menor", 30, 15, 6, 12),
            ("frasco_fogo_alquimico", 45, 20, 4, 8),
            ("unguento_purificador", 40, 18, 5, 10),
            ("erva_lunar", 10, 5, 15, 30),
            ("po_eter", 15, 7, 10, 20),
            ("madeira_espinheiro", 12, 6, 8, 16),
            ("minerio_sombrio", 35, 18, 3, 6),
            ("anel_cristal_mana", 90, 45, 1, 1),
            ("amuleto_guardiao_antigo", 95, 48, 1, 1),
            ("mapa_continental", 50, 0, 1, 1)
        ]
        for item_id, p_compra, p_venda, est_ini, est_max in itens_iniciais:
            self.adicionar_mercadoria(item_id, p_compra, p_venda, est_ini, est_max)

    def adicionar_mercadoria(self, item_id, preco_compra=None, preco_venda=None, estoque_inicial=5, estoque_maximo=10):
        self.mercadorias[item_id] = ItemMercadoria(item_id, preco_compra, preco_venda, estoque_inicial, estoque_maximo)

    def obter_lista_mercadorias(self):
        """Retorna a lista de itens à venda."""
        return list(self.mercadorias.values())

    # =========================================================================
    # COMPRA (JOGADOR COMPRA DA LOJA)
    # =========================================================================

    def comprar_item(self, item_id, quantidade, jogador):
        """
        Jogador compra `quantidade` de `item_id` da loja.
        Retorna (sucesso: bool, mensagem: str).
        """
        merc = self.mercadorias.get(item_id)
        if not merc:
            return False, "Item indisponível nesta loja."

        if quantidade <= 0:
            return False, "Quantidade inválida."

        if merc.estoque_atual < quantidade:
            return False, f"Estoque insuficiente! O mercador possui apenas {merc.estoque_atual} unidade(s)."

        custo_total = merc.preco_compra * quantidade
        if jogador.dinheiro < custo_total:
            return False, f"Moedas insuficientes! Custo total: {custo_total} moedas."

        inv = jogador.inventario
        if inv.esta_cheio and not inv.tem_item(item_id, 1):
            return False, "Sua bolsa está cheia! Libere espaço antes de comprar."

        # Efetua transação
        jogador.gastar_dinheiro(custo_total)
        merc.estoque_atual -= quantidade
        inv.adicionar_item(item_id, quantidade)

        nome_item = merc.item_template.nome if merc.item_template else item_id
        return True, f"✦ Comprou {quantidade}x {nome_item} por {custo_total} moedas!"

    # =========================================================================
    # VENDA (JOGADOR VENDE ITEM DA BOLSA PARA A LOJA)
    # =========================================================================

    def vender_item(self, item_id, quantidade, jogador):
        """
        Jogador vende `quantidade` de `item_id` para o mercador.
        Retorna (sucesso: bool, mensagem: str).
        """
        inv = jogador.inventario
        if not inv.tem_item(item_id, quantidade):
            return False, "Você não possui a quantidade informada deste item."

        item_temp = ItemFactory.criar(item_id)
        if not item_temp:
            return False, "Item inválido."

        if isinstance(item_temp, ItemChave) or item_temp.preco_venda <= 0:
            return False, f"{item_temp.nome} é um item de valor inestimável e não pode ser vendido."

        # Calcula valor recebido
        preco_unitario = item_temp.preco_venda
        if item_id in self.mercadorias:
            preco_unitario = self.mercadorias[item_id].preco_venda

        total_ganho = preco_unitario * quantidade

        # Efetua transação
        inv.remover_item(item_id, quantidade)
        jogador.ganhar_dinheiro(total_ganho)

        # Repõe estoque na loja se for um item catalogado
        if item_id in self.mercadorias:
            self.mercadorias[item_id].estoque_atual = min(
                self.mercadorias[item_id].estoque_maximo,
                self.mercadorias[item_id].estoque_atual + quantidade
            )

        return True, f"✦ Vendeu {quantidade}x {item_temp.nome} por {total_ganho} moedas!"

    def reabastecer(self):
        """Reabastece periodicamente o estoque do mercador."""
        for merc in self.mercadorias.values():
            merc.estoque_atual = min(merc.estoque_maximo, merc.estoque_atual + 2)
