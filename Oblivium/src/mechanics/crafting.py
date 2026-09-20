# src/mechanics/crafting.py
import json
import os
import sys

_raiz_projeto = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _raiz_projeto not in sys.path:
    sys.path.insert(0, _raiz_projeto)

from src.mechanics.items import EquipamentoItem
from src.mechanics.item_factory import ItemFactory

class Receita:
    """Representa uma receita de alquimia, forja ou tecelagem."""
    def __init__(self, id_receita, nome, tipo, resultado_item_id, resultado_quantidade, materiais_necessarios, custo_moedas=0, requisito_sincronia=1, desbloqueada=True, descricao=""):
        self.id = id_receita
        self.nome = nome
        self.tipo = tipo.upper() # ALQUIMIA, FORJA, TECELAGEM
        self.resultado_item_id = resultado_item_id
        self.resultado_quantidade = resultado_quantidade
        self.materiais_necessarios = materiais_necessarios # {item_id: qtd}
        self.custo_moedas = custo_moedas
        self.requisito_sincronia = requisito_sincronia
        self.desbloqueada = desbloqueada
        self.descricao = descricao

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "tipo": self.tipo,
            "resultado_item_id": self.resultado_item_id,
            "resultado_quantidade": self.resultado_quantidade,
            "materiais_necessarios": self.materiais_necessarios,
            "custo_moedas": self.custo_moedas,
            "requisito_sincronia": self.requisito_sincronia,
            "desbloqueada": self.desbloqueada,
            "descricao": self.descricao
        }


class CraftingManager:
    """
    Gerenciador de Fabricação de Itens e Aprimoramento de Equipamentos.
    """
    _CAMINHO_JSON = os.path.join(os.path.dirname(__file__), "..", "data", "receitas.json")
    _receitas_cache = None
    _custos_upgrade_cache = None

    @classmethod
    def carregar_dados(cls, recarregar=False):
        if cls._receitas_cache is not None and not recarregar:
            return cls._receitas_cache, cls._custos_upgrade_cache

        receitas = {}
        custos_upgrade = {
            "1": {"minerio_sombrio": 1, "moedas": 20},
            "2": {"minerio_sombrio": 2, "moedas": 45},
            "3": {"minerio_sombrio": 3, "moedas": 80},
            "4": {"minerio_sombrio": 5, "moedas": 130},
            "5": {"minerio_sombrio": 8, "moedas": 200}
        }

        if os.path.exists(cls._CAMINHO_JSON):
            try:
                with open(cls._CAMINHO_JSON, "r", encoding="utf-8") as f:
                    dados = json.load(f)
                    for r_id, r_info in dados.get("receitas", {}).items():
                        receitas[r_id] = Receita(
                            id_receita=r_info["id"],
                            nome=r_info.get("nome", r_id),
                            tipo=r_info.get("tipo", "ALQUIMIA"),
                            resultado_item_id=r_info["resultado_item_id"],
                            resultado_quantidade=r_info.get("resultado_quantidade", 1),
                            materiais_necessarios=r_info.get("materiais_necessarios", {}),
                            custo_moedas=r_info.get("custo_moedas", 0),
                            requisito_sincronia=r_info.get("requisito_sincronia", 1),
                            desbloqueada=r_info.get("desbloqueada", True),
                            descricao=r_info.get("descricao", "")
                        )
                    if "custos_upgrade" in dados:
                        custos_upgrade = dados["custos_upgrade"]
            except Exception as e:
                print(f"[CraftingManager] Erro ao ler receitas.json: {e}")

        cls._receitas_cache = receitas
        cls._custos_upgrade_cache = custos_upgrade
        return cls._receitas_cache, cls._custos_upgrade_cache

    @classmethod
    def obter_todas_receitas(cls):
        receitas, _ = cls.carregar_dados()
        return list(receitas.values())

    @classmethod
    def obter_receitas_desbloqueadas(cls, nivel_sincronia=1):
        receitas, _ = cls.carregar_dados()
        return [
            r for r in receitas.values()
            if r.desbloqueada and r.requisito_sincronia <= nivel_sincronia
        ]

    # =========================================================================
    # FABRICAÇÃO DE ITENS (CRAFTING)
    # =========================================================================

    @classmethod
    def pode_fabricar(cls, receita, jogador):
        """Verifica se o jogador atende a todos os pré-requisitos para fabricar a receita."""
        if not receita.desbloqueada:
            return False, "Esta receita ainda não foi descoberta."

        if jogador.nivel_sincronia < receita.requisito_sincronia:
            return False, f"Requer Estágio de Memória {receita.requisito_sincronia}."

        if jogador.dinheiro < receita.custo_moedas:
            return False, f"Moedas insuficientes! Requer {receita.custo_moedas} moedas."

        # Checa materiais no inventário
        inv = jogador.inventario
        for mat_id, qtd_nec in receita.materiais_necessarios.items():
            if not inv.tem_item(mat_id, qtd_nec):
                item_info = ItemFactory.criar(mat_id)
                nome_mat = item_info.nome if item_info else mat_id
                return False, f"Material insuficiente: {nome_mat} ({inv.obter_quantidade(mat_id)}/{qtd_nec})."

        if inv.esta_cheio and not inv.tem_item(receita.resultado_item_id, 1):
            return False, "Bolsa cheia! Libere espaço antes de fabricar."

        return True, "Pronto para fabricar."

    @classmethod
    def fabricar(cls, receita_id, jogador):
        """
        Executa a criação do item: deduz materiais e moedas, entrega o resultado.
        Retorna (sucesso: bool, mensagem: str).
        """
        receitas, _ = cls.carregar_dados()
        receita = receitas.get(receita_id)
        if not receita:
            return False, "Receita inexistente."

        pode, msg = cls.pode_fabricar(receita, jogador)
        if not pode:
            return False, msg

        inv = jogador.inventario

        # 1. Deduz materiais
        for mat_id, qtd_nec in receita.materiais_necessarios.items():
            inv.remover_item(mat_id, qtd_nec)

        # 2. Deduz moedas
        jogador.gastar_dinheiro(receita.custo_moedas)

        # 3. Entrega o item fabricado
        sucesso, msg_add = inv.adicionar_item(receita.resultado_item_id, receita.resultado_quantidade)
        
        item_res = ItemFactory.criar(receita.resultado_item_id)
        nome_res = item_res.nome if item_res else receita.resultado_item_id
        return True, f"✦ {receita.resultado_quantidade}x {nome_res} fabricado(s) com sucesso!"

    # =========================================================================
    # APRIMORAMENTO / UPGRADE DE EQUIPAMENTOS
    # =========================================================================

    @classmethod
    def obter_custo_upgrade(cls, equipamento):
        """Retorna o dicionário de custo de materiais e moedas para o próximo nível de upgrade."""
        if not isinstance(equipamento, EquipamentoItem) or not equipamento.pode_aprimorar():
            return None

        _, custos = cls.carregar_dados()
        prox_nivel = str(equipamento.nivel_upgrade + 1)
        return custos.get(prox_nivel, {"minerio_sombrio": 1, "moedas": 20})

    @classmethod
    def pode_aprimorar_equipamento(cls, equipamento, jogador):
        """Verifica se o jogador pode realizar o refino do equipamento."""
        if not isinstance(equipamento, EquipamentoItem):
            return False, "Apenas equipamentos podem ser aprimorados."

        if not equipamento.pode_aprimorar():
            return False, f"{equipamento.nome} já atingiu o nível máximo de aprimoramento (+5)."

        custo = cls.obter_custo_upgrade(equipamento)
        if not custo:
            return False, "Custo de aprimoramento indefinido."

        moedas_nec = custo.get("moedas", 0)
        if jogador.dinheiro < moedas_nec:
            return False, f"Moedas insuficientes! Requer {moedas_nec} moedas."

        inv = jogador.inventario
        minerio_nec = custo.get("minerio_sombrio", 0)
        if minerio_nec > 0 and not inv.tem_item("minerio_sombrio", minerio_nec):
            return False, f"Minério Sombrio insuficiente ({inv.obter_quantidade('minerio_sombrio')}/{minerio_nec})."

        return True, "Pronto para aprimorar."

    @classmethod
    def aprimorar_equipamento(cls, equipamento, jogador):
        """Executa o aprimoramento do equipamento e atualiza os status do jogador."""
        pode, msg = cls.pode_aprimorar_equipamento(equipamento, jogador)
        if not pode:
            return False, msg

        custo = cls.obter_custo_upgrade(equipamento)
        inv = jogador.inventario

        # Deduz materiais e moedas
        minerio_nec = custo.get("minerio_sombrio", 0)
        if minerio_nec > 0:
            inv.remover_item("minerio_sombrio", minerio_nec)

        moedas_nec = custo.get("moedas", 0)
        jogador.gastar_dinheiro(moedas_nec)

        # Executa o refino
        equipamento.aprimorar()
        jogador.recalcular_status_derivados(manter_porcentagem=False)

        return True, f"✦ {equipamento.nome} foi aprimorado para +{equipamento.nivel_upgrade}!"
