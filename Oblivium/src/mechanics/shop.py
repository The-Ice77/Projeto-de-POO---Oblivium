# src/mechanics/shop.py
import json
import logging
import os
import sys

_raiz_projeto = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _raiz_projeto not in sys.path:
    sys.path.insert(0, _raiz_projeto)

from src.mechanics.items import ItemChave
from src.mechanics.item_factory import ItemFactory

logger = logging.getLogger(__name__)


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
    Suporta instanciação declarativa via arquivo JSON (`src/data/lojas.json`).
    """
    _CATALOGO_JSON = None
    _INSTANCIAS_ATIVAS = {}

    # Mapeamento de apelidos para resolução flexível
    _ALIASES = {
        "loja_elara": "botanica_elara",
        "elara": "botanica_elara",
        "botanica": "botanica_elara",
        "loja_torvald": "forja_torvald",
        "torvald": "forja_torvald",
        "forja": "forja_torvald",
        "viajante": "emporio_viajante",
        "geral": "emporio_viajante",
        "default": "emporio_viajante",
    }

    def __init__(self, id_loja=None, nome="Empório do Viajante", tipo="GERAL", descricao=""):
        self.id_loja = id_loja or "emporio_viajante"
        self.nome = nome
        self.tipo = tipo
        self.descricao = descricao
        self.mercadorias = {}  # {item_id: ItemMercadoria}

        if id_loja and id_loja in self._obter_catalogo():
            self._carregar_dados_json(id_loja)
        else:
            self.inicializar_estoque_padrao()

    @classmethod
    def _obter_catalogo(cls):
        """Carrega e armazena em cache o catálogo bruto de lojas de src/data/lojas.json."""
        if cls._CATALOGO_JSON is not None:
            return cls._CATALOGO_JSON

        caminho_json = os.path.join(_raiz_projeto, "Oblivium", "src", "data", "lojas.json")
        if not os.path.isfile(caminho_json):
            # Tenta caminho relativo direto sem prefixo 'Oblivium'
            caminho_json = os.path.join(_raiz_projeto, "src", "data", "lojas.json")

        if os.path.isfile(caminho_json):
            try:
                with open(caminho_json, "r", encoding="utf-8") as f:
                    cls._CATALOGO_JSON = json.load(f)
                    return cls._CATALOGO_JSON
            except Exception as e:
                logger.error("Erro ao ler catálogo de lojas em %s: %s", caminho_json, e)

        cls._CATALOGO_JSON = {}
        return cls._CATALOGO_JSON

    @classmethod
    def normalizar_id(cls, loja_id):
        """Resolve apelidos e padroniza identificadores de loja."""
        if not loja_id:
            return "emporio_viajante"
        chave = str(loja_id).strip().lower()
        return cls._ALIASES.get(chave, chave)

    @classmethod
    def obter_ou_criar(cls, loja_id):
        """
        Retorna a instância persistente da loja identificada por `loja_id`.
        Garante que estoques modificados pelo jogador permaneçam consistentes durante a sessão.
        """
        id_norm = cls.normalizar_id(loja_id)
        if id_norm in cls._INSTANCIAS_ATIVAS:
            return cls._INSTANCIAS_ATIVAS[id_norm]

        catalogo = cls._obter_catalogo()
        if id_norm in catalogo:
            dados = catalogo[id_norm]
            nova_loja = cls(
                id_loja=id_norm,
                nome=dados.get("nome", "Loja"),
                tipo=dados.get("tipo", "GERAL"),
                descricao=dados.get("descricao", "")
            )
        else:
            nova_loja = cls(id_loja=id_norm)

        cls._INSTANCIAS_ATIVAS[id_norm] = nova_loja
        return nova_loja

    def _carregar_dados_json(self, id_loja):
        """Popula as mercadorias com base na definição do JSON."""
        catalogo = self._obter_catalogo()
        dados = catalogo.get(id_loja, {})
        self.nome = dados.get("nome", self.nome)
        self.tipo = dados.get("tipo", self.tipo)
        self.descricao = dados.get("descricao", self.descricao)

        itens = dados.get("itens", [])
        self.mercadorias.clear()
        for item_info in itens:
            item_id = item_info.get("item_id")
            p_compra = item_info.get("preco_compra")
            p_venda = item_info.get("preco_venda")
            est_ini = item_info.get("estoque_inicial", 5)
            est_max = item_info.get("estoque_maximo", 10)
            self.adicionar_mercadoria(item_id, p_compra, p_venda, est_ini, est_max)

    def inicializar_estoque_padrao(self):
        """Define os itens e estoques iniciais do mercador itinerante padrão."""
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
        ]
        self.mercadorias.clear()
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
