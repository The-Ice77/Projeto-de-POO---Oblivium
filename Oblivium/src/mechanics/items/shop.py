# src/mechanics/items/shop.py
import copy
import json
import logging
import os

from src.mechanics.items.items import ItemChave
from src.mechanics.items.item_factory import ItemFactory
from src.utils.constants import PASTA_DATA

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

        caminho_json = os.path.join(PASTA_DATA, "lojas.json")

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
    def resetar_lojas(cls):
        """Limpa as instâncias ativas para isolamento estrito entre slots de save."""
        cls._INSTANCIAS_ATIVAS.clear()

    @classmethod
    def salvar_estado_lojas(cls):
        """Retorna o estado serializado dos estoques de todas as lojas instanciadas."""
        estado = {}
        for id_loja, loja in cls._INSTANCIAS_ATIVAS.items():
            estado[id_loja] = {
                item_id: merc.estoque_atual
                for item_id, merc in loja.mercadorias.items()
            }
        return copy.deepcopy(estado)

    @classmethod
    def carregar_estado_lojas(cls, dados_lojas):
        """Restaura o estado dos estoques a partir dos dados do save slot com isolamento estrito."""
        cls.resetar_lojas()
        if not dados_lojas or not isinstance(dados_lojas, dict):
            return
        for id_loja, estoques in dados_lojas.items():
            loja = cls.obter_ou_criar(id_loja)
            for item_id, qtd in estoques.items():
                if item_id in loja.mercadorias:
                    loja.mercadorias[item_id].estoque_atual = int(qtd)

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
            dados = copy.deepcopy(catalogo[id_norm])
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
        """Popula as mercadorias com base na definição do JSON via deepcopy."""
        catalogo = self._obter_catalogo()
        dados = copy.deepcopy(catalogo.get(id_loja, {}))
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
            ("pocao_vida_menor", 8, 15),
            ("elixir_mana_menor", 6, 12),
            ("frasco_fogo_alquimico", 4, 8),
            ("unguento_purificador", 5, 10),
            ("erva_lunar", 15, 30),
            ("po_eter", 10, 20),
            ("madeira_espinheiro", 8, 16),
            ("minerio_sombrio", 3, 6),
            ("anel_cristal_mana", 1, 1),
            ("amuleto_guardiao_antigo", 1, 1),
        ]
        self.mercadorias.clear()
        for item_id, est_ini, est_max in itens_iniciais:
            self.adicionar_mercadoria(item_id, estoque_inicial=est_ini, estoque_maximo=est_max)

    def adicionar_mercadoria(self, item_id, preco_compra=None, preco_venda=None, estoque_inicial=5, estoque_maximo=10):
        self.mercadorias[item_id] = ItemMercadoria(item_id, preco_compra, preco_venda, estoque_inicial, estoque_maximo)

    def obter_lista_mercadorias(self):
        """Retorna a lista de itens à venda."""
        return list(self.mercadorias.values())

    @staticmethod
    def _quantidade_valida(quantidade):
        return isinstance(quantidade, int) and not isinstance(quantidade, bool) and quantidade > 0

    def cotar_compra(self, item_id, quantidade=1):
        """Preço total em cobres usado tanto pela interface quanto pela transação."""
        merc = self.mercadorias.get(item_id)
        if not self._quantidade_valida(quantidade) or not merc or not merc.item_template:
            return None
        preco = merc.preco_compra
        if not isinstance(preco, int) or isinstance(preco, bool) or preco < 0:
            return None
        return preco * quantidade

    def cotar_venda(self, item_id, quantidade=1):
        """Preço total em cobres; None indica item ou quantidade não vendável."""
        if not self._quantidade_valida(quantidade):
            return None
        item = ItemFactory.criar(item_id)
        if not item or isinstance(item, ItemChave) or item.preco_venda <= 0:
            return None
        merc = self.mercadorias.get(item_id)
        preco = merc.preco_venda if merc else item.preco_venda
        if not isinstance(preco, int) or isinstance(preco, bool) or preco <= 0:
            return None
        return preco * quantidade

    @staticmethod
    def _capturar_bolsa(inventario):
        return [(slot, slot.quantidade) for slot in inventario.slots]

    @staticmethod
    def _restaurar_bolsa(inventario, estado):
        inventario.slots[:] = [slot for slot, _ in estado]
        for slot, quantidade in estado:
            slot.quantidade = quantidade

    # =========================================================================
    # COMPRA (JOGADOR COMPRA DA LOJA)
    # =========================================================================

    def comprar_item(self, item_id, quantidade, jogador):
        """
        Jogador compra `quantidade` de `item_id` da loja.
        Retorna (sucesso: bool, mensagem: str).
        """
        if not self._quantidade_valida(quantidade):
            return False, "Quantidade inválida."

        merc = self.mercadorias.get(item_id)
        custo_total = self.cotar_compra(item_id, quantidade)
        if custo_total is None:
            return False, "Item indisponível nesta loja."

        if merc.estoque_atual < quantidade:
            return False, f"Estoque insuficiente! O mercador possui apenas {merc.estoque_atual} unidade(s)."

        from src.entities.player import Player
        if jogador.dinheiro < custo_total:
            return False, f"Moedas insuficientes! Custo total: {Player.formatar_valor_moedas(custo_total)}."

        inv = jogador.inventario
        if not inv.pode_adicionar_item(merc.item_template, quantidade):
            return False, "Não há espaço na bolsa para a quantidade inteira."

        saldo_anterior = jogador.dinheiro
        estoque_anterior = merc.estoque_atual
        bolsa_anterior = self._capturar_bolsa(inv)
        try:
            sucesso, _ = inv.adicionar_item_completo(item_id, quantidade)
            if not sucesso or not jogador.gastar_dinheiro(custo_total):
                raise ValueError("A entrega ou o débito não foi confirmado.")
            if jogador.dinheiro != saldo_anterior - custo_total:
                raise ValueError("O débito divergiu da cotação.")
            merc.estoque_atual -= quantidade
        except Exception as exc:
            self._restaurar_bolsa(inv, bolsa_anterior)
            jogador.dinheiro = saldo_anterior
            merc.estoque_atual = estoque_anterior
            logger.warning("Compra cancelada sem alterar saldo, estoque ou bolsa: %s", exc)
            return False, "Não foi possível concluir a compra. Suas moedas e sua bolsa foram preservadas."

        nome_item = merc.item_template.nome if merc.item_template else item_id
        return True, f"✦ Comprou {quantidade}x {nome_item} por {Player.formatar_valor_moedas(custo_total)}!"

    # =========================================================================
    # VENDA (JOGADOR VENDE ITEM DA BOLSA PARA A LOJA)
    # =========================================================================

    def vender_item(self, item_id, quantidade, jogador):
        """
        Jogador vende `quantidade` de `item_id` para o mercador.
        Retorna (sucesso: bool, mensagem: str).
        """
        if not self._quantidade_valida(quantidade):
            return False, "Quantidade inválida."
        inv = jogador.inventario
        if not inv.tem_item(item_id, quantidade):
            return False, "Você não possui a quantidade informada deste item."

        item_temp = ItemFactory.criar(item_id)
        if not item_temp:
            return False, "Item inválido."

        total_ganho = self.cotar_venda(item_id, quantidade)
        if total_ganho is None:
            return False, f"{item_temp.nome} é um item de valor inestimável e não pode ser vendido."

        saldo_anterior = jogador.dinheiro
        bolsa_anterior = self._capturar_bolsa(inv)
        merc = self.mercadorias.get(item_id)
        estoque_anterior = merc.estoque_atual if merc else None
        qtd_anterior = inv.obter_quantidade(item_id)
        try:
            if not inv.remover_item(item_id, quantidade) or inv.obter_quantidade(item_id) != qtd_anterior - quantidade:
                raise ValueError("A remoção não foi integral.")
            jogador.ganhar_dinheiro(total_ganho)
            if jogador.dinheiro != saldo_anterior + total_ganho:
                raise ValueError("O crédito divergiu da cotação.")
            if merc:
                merc.estoque_atual = min(merc.estoque_maximo, merc.estoque_atual + quantidade)
        except Exception as exc:
            self._restaurar_bolsa(inv, bolsa_anterior)
            jogador.dinheiro = saldo_anterior
            if merc:
                merc.estoque_atual = estoque_anterior
            logger.warning("Venda cancelada sem alterar saldo, estoque ou bolsa: %s", exc)
            return False, "Não foi possível concluir a venda. Suas moedas e sua bolsa foram preservadas."

        from src.entities.player import Player
        return True, f"✦ Vendeu {quantidade}x {item_temp.nome} por {Player.formatar_valor_moedas(total_ganho)}!"

    def reabastecer(self):
        """Reabastece periodicamente o estoque do mercador."""
        for merc in self.mercadorias.values():
            merc.estoque_atual = min(merc.estoque_maximo, merc.estoque_atual + 2)
