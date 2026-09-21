# src/mechanics/inventory.py
import os
import sys

_raiz_projeto = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _raiz_projeto not in sys.path:
    sys.path.insert(0, _raiz_projeto)

from src.mechanics.items import ItemBase, ConsumivelItem, EquipamentoItem, GrimorioItem, MaterialItem, ItemChave
from src.mechanics.item_factory import ItemFactory

class ItemSlot:
    """Representa um slot ocupado ou gerenciado dentro do inventário."""
    def __init__(self, item, quantidade=1):
        self.item = item
        self.quantidade = max(1, quantidade)

    def to_dict(self):
        return {
            "item_id": self.item.id,
            "quantidade": self.quantidade,
            "nivel_upgrade": getattr(self.item, 'nivel_upgrade', 0)
        }

    @classmethod
    def from_dict(cls, dados):
        item_id = dados.get("item_id")
        qtd = dados.get("quantidade", 1)
        up = dados.get("nivel_upgrade", 0)
        item = ItemFactory.criar(item_id, nivel_upgrade=up)
        if item:
            return cls(item, qtd)
        return None


class Inventario:
    """
    Componente central de inventário de Halia.
    Controla capacidade da bolsa, categorização, empilhamento, equipamentos equipados e bônus dinâmicos.
    """
    SLOTS_INICIAIS = 16
    SLOTS_MAXIMOS = 32

    def __init__(self, capacidade=SLOTS_INICIAIS):
        self.capacidade = max(1, min(self.SLOTS_MAXIMOS, capacidade))
        self.slots = [] # Lista de ItemSlot
        
        # Slots de equipamentos ativos
        self.equipados = {
            "ROUPA": None,        # EquipamentoItem
            "CAJADO": None,       # EquipamentoItem
            "ACESSORIO_1": None,  # EquipamentoItem
            "ACESSORIO_2": None,  # EquipamentoItem
            "GRIMORIO_1": None,   # GrimorioItem (Tomo 1)
            "GRIMORIO_2": None,   # GrimorioItem (Tomo 2)
            "GRIMORIO_3": None,   # GrimorioItem (Tomo 3)
            "GRIMORIO_4": None    # GrimorioItem (Tomo 4)
        }

    @property
    def total_slots_ocupados(self):
        return len(self.slots)

    @property
    def slots_livres(self):
        return max(0, self.capacidade - len(self.slots))

    @property
    def esta_cheio(self):
        return len(self.slots) >= self.capacidade

    def expandir_bolsa(self, slots_extras):
        """Aumenta a capacidade de armazenamento da bolsa."""
        self.capacidade = min(self.SLOTS_MAXIMOS, self.capacidade + slots_extras)
        return self.capacidade

    # =========================================================================
    # ADIÇÃO E REMOÇÃO DE ITENS
    # =========================================================================

    def adicionar_item(self, item_ou_id, quantidade=1, nivel_upgrade=0):
        """
        Adiciona um item ao inventário.
        Se for acumulável, tenta empilhar em slot existente antes de abrir novo slot.
        Retorna (sucesso: bool, mensagem: str).
        """
        if isinstance(item_ou_id, str):
            item = ItemFactory.criar(item_ou_id, nivel_upgrade=nivel_upgrade)
        else:
            item = item_ou_id

        if not item:
            return False, "Item inválido ou não encontrado."

        if quantidade <= 0:
            return False, "Quantidade deve ser positiva."

        qtd_restante = quantidade

        # 1. Se o item for acumulável, tenta empilhar em slots existentes
        if item.acumulavel:
            for slot in self.slots:
                if slot.item.id == item.id:
                    espaco_livre = slot.item.quantidade_maxima - slot.quantidade
                    if espaco_livre > 0:
                        adicionar_aqui = min(qtd_restante, espaco_livre)
                        slot.quantidade += adicionar_aqui
                        qtd_restante -= adicionar_aqui
                        if qtd_restante <= 0:
                            return True, f"{quantidade}x {item.nome} adicionado(s) à bolsa."

        # 2. Se ainda sobrou quantidade, adiciona em novos slots
        while qtd_restante > 0:
            if self.esta_cheio:
                adicionados = quantidade - qtd_restante
                if adicionados > 0:
                    return True, f"Bolsa cheia! Apenas {adicionados}x {item.nome} foram guardados."
                return False, "Bolsa cheia! Não há mais espaço disponível."

            novo_item = ItemFactory.criar(item.id, nivel_upgrade=getattr(item, 'nivel_upgrade', 0))
            if item.acumulavel:
                qtd_slot = min(qtd_restante, novo_item.quantidade_maxima)
            else:
                qtd_slot = 1

            self.slots.append(ItemSlot(novo_item, qtd_slot))
            qtd_restante -= qtd_slot

        return True, f"{quantidade}x {item.nome} adicionado(s) à bolsa."

    def remover_item(self, item_id, quantidade=1):
        """
        Remove quantidade especificada de um item do inventário.
        Retorna True se removeu com sucesso, False se insuficiente.
        """
        if not self.tem_item(item_id, quantidade):
            return False

        qtd_para_remover = quantidade
        indices_para_remover = []

        for i in range(len(self.slots) - 1, -1, -1):
            slot = self.slots[i]
            if slot.item.id == item_id:
                if slot.quantidade <= qtd_para_remover:
                    qtd_para_remover -= slot.quantidade
                    indices_para_remover.append(i)
                else:
                    slot.quantidade -= qtd_para_remover
                    qtd_para_remover = 0
                    break

            if qtd_para_remover <= 0:
                break

        for i in indices_para_remover:
            self.slots.pop(i)

        return True

    def obter_quantidade(self, item_id):
        """Retorna o total acumulado de um item em todos os slots."""
        total = 0
        for slot in self.slots:
            if slot.item.id == item_id:
                total += slot.quantidade
        return total

    def tem_item(self, item_id, quantidade=1):
        """Verifica se há quantidade suficiente do item na bolsa."""
        return self.obter_quantidade(item_id) >= quantidade

    def obter_slot_por_indice(self, indice):
        """Retorna o ItemSlot pelo índice na lista, ou None."""
        if 0 <= indice < len(self.slots):
            return self.slots[indice]
        return None

    def obter_itens_por_categoria(self, categoria):
        """Retorna uma lista de (indice_original, ItemSlot) filtrados pela categoria."""
        categoria_upper = categoria.upper()
        resultado = []
        for i, slot in enumerate(self.slots):
            if categoria_upper in ["TODOS", "BOLSA"]:
                resultado.append((i, slot))
            elif categoria_upper in ["OUTROS", "CHAVE", "CHAVES"]:
                if slot.item.categoria in ["CHAVE", "OUTROS", "CHAVES"]:
                    resultado.append((i, slot))
            elif slot.item.categoria == categoria_upper:
                resultado.append((i, slot))
        return resultado

    # =========================================================================
    # EQUIPAMENTO E DESEQUIPAMENTO
    # =========================================================================

    def equipar(self, slot_alvo, indice_ou_item):
        """
        Equipa um equipamento ou grimório no slot correspondente.
        Se já houver outro item equipado no slot, ele retorna para o inventário.
        """
        slot_alvo = slot_alvo.upper()
        
        # Mapeamento de conveniência
        if slot_alvo == "GRIMORIO":
            # Procura o primeiro slot livre de grimório
            slot_livre = None
            for g_slot in ["GRIMORIO_1", "GRIMORIO_2", "GRIMORIO_3", "GRIMORIO_4"]:
                if self.equipados.get(g_slot) is None:
                    slot_livre = g_slot
                    break
            slot_alvo = slot_livre or "GRIMORIO_1"

        if slot_alvo not in self.equipados:
            return False, f"Slot de equipamento '{slot_alvo}' inválido."

        item = None
        indice_remocao = None

        if isinstance(indice_ou_item, int):
            if not (0 <= indice_ou_item < len(self.slots)):
                return False, "Índice de item inválido."
            item_slot = self.slots[indice_ou_item]
            item = item_slot.item
            indice_remocao = indice_ou_item
        else:
            item_candidato = indice_ou_item
            if isinstance(item_candidato, str):
                item_candidato = ItemFactory.criar(item_candidato)
            item = item_candidato
            for idx, s in enumerate(self.slots):
                if s.item == item or s.item.id == getattr(item, 'id', None):
                    indice_remocao = idx
                    item = s.item
                    break

        if not item:
            return False, "Item inválido."

        # Validação do tipo de slot
        if slot_alvo in ["ROUPA", "CAJADO", "ACESSORIO_1", "ACESSORIO_2"]:
            if not isinstance(item, EquipamentoItem):
                return False, f"{item.nome} não é um equipamento vestível."
            
            # Compatibilidade de slot
            if slot_alvo == "ROUPA" and item.slot != "ROUPA":
                return False, f"{item.nome} deve ser equipado no slot de Roupa."
            elif slot_alvo == "CAJADO" and item.slot != "CAJADO":
                return False, f"{item.nome} deve ser equipado no slot de Cajado."
            elif slot_alvo in ["ACESSORIO_1", "ACESSORIO_2"] and "ACESSORIO" not in item.slot:
                return False, f"{item.nome} não é um acessório."

        elif "GRIMORIO" in slot_alvo:
            if not isinstance(item, GrimorioItem) and getattr(item, 'categoria', '') != "GRIMORIO":
                return False, f"{item.nome} não é um Grimório."

        # Item atualmente equipado que será substituído
        item_antigo = self.equipados[slot_alvo]

        # Remove o item novo do inventário com segurança de quantidade
        if indice_remocao is not None and 0 <= indice_remocao < len(self.slots):
            if self.slots[indice_remocao].quantidade > 1:
                self.slots[indice_remocao].quantidade -= 1
            else:
                self.slots.pop(indice_remocao)

        # Devolve o item antigo para a bolsa (se houver)
        if item_antigo:
            self.adicionar_item(item_antigo, 1)

        # Equipa o novo
        self.equipados[slot_alvo] = item
        return True, f"{item.nome_formatado if hasattr(item, 'nome_formatado') else item.nome} equipado com sucesso!"

    def desequipar(self, slot_alvo):
        """Desequipa o item do slot e o coloca de volta na bolsa."""
        slot_alvo = slot_alvo.upper()
        if slot_alvo == "GRIMORIO":
            slot_alvo = "GRIMORIO_1"

        if slot_alvo not in self.equipados or self.equipados[slot_alvo] is None:
            return False, "Nenhum item equipado neste slot."

        if self.esta_cheio:
            return False, "Bolsa cheia! Esvazie espaço para desequipar."

        item = self.equipados[slot_alvo]
        self.equipados[slot_alvo] = None
        self.adicionar_item(item, 1)
        return True, f"{item.nome} desequipado e guardado na bolsa."

    def equipar_item(self, item_ou_id, slot_preferido=None):
        """
        Método de conveniência que recebe um item ou ID, identifica seu slot natural
        e equipa diretamente no inventário.
        """
        if isinstance(item_ou_id, str):
            item = ItemFactory.criar(item_ou_id)
        else:
            item = item_ou_id

        if not item:
            return False, "Item inválido."

        if isinstance(item, EquipamentoItem):
            slot = slot_preferido or item.slot
            if "ACESSORIO" in slot:
                if self.equipados.get("ACESSORIO_1") is None:
                    slot = "ACESSORIO_1"
                else:
                    slot = "ACESSORIO_2"
            return self.equipar(slot, item)
        elif isinstance(item, GrimorioItem) or getattr(item, 'categoria', '') == "GRIMORIO":
            return self.equipar("GRIMORIO", item)

        return False, f"O item {item.nome} não é equipável."

    # =========================================================================
    # CÁLCULO DE BÔNUS TOTAIS DE EQUIPAMENTOS
    # =========================================================================

    def obter_bonus_totais_equipamentos(self):
        """
        Calcula e consolida todos os bônus de atributos primários e derivados
        concedidos pelos equipamentos e grimórios equipados no momento.
        """
        bonus_attrs = {
            "forca": 0,
            "destreza": 0,
            "constituicao": 0,
            "intelecto": 0,
            "sabedoria": 0,
            "presenca": 0
        }
        bonus_stats = {
            "poder_magico": 0,
            "defesa_fisica": 0,
            "defesa_magica": 0,
            "vida_maxima_bonus": 0,
            "mana_maxima_bonus": 0,
            "dano_fogo_bonus": 0,
            "dano_gelo_bonus": 0,
            "cura_bonus": 0
        }

        for item in self.equipados.values():
            if not item:
                continue

            # Bônus de atributos primários
            if hasattr(item, 'obter_bonus_atributos_efetivos'):
                for attr, val in item.obter_bonus_atributos_efetivos().items():
                    if attr in bonus_attrs:
                        bonus_attrs[attr] += val

            # Bônus de stats derivados
            if hasattr(item, 'obter_bonus_stats_efetivos'):
                for stat, val in item.obter_bonus_stats_efetivos().items():
                    bonus_stats[stat] = bonus_stats.get(stat, 0) + val
            elif hasattr(item, 'bonus_stats') and item.bonus_stats:
                for stat, val in item.bonus_stats.items():
                    bonus_stats[stat] = bonus_stats.get(stat, 0) + val

        return {"atributos": bonus_attrs, "stats": bonus_stats}

    # =========================================================================
    # SERIALIZAÇÃO & PERSISTÊNCIA
    # =========================================================================

    def to_dict(self):
        """Serializa o inventário completo para persistência no SaveManager."""
        slots_dados = [s.to_dict() for s in self.slots]
        equipados_dados = {}
        for slot_nome, item in self.equipados.items():
            if item:
                equipados_dados[slot_nome] = {
                    "item_id": item.id,
                    "nivel_upgrade": getattr(item, 'nivel_upgrade', 0)
                }
            else:
                equipados_dados[slot_nome] = None

        return {
            "capacidade": self.capacidade,
            "slots": slots_dados,
            "equipados": equipados_dados
        }

    @classmethod
    def from_dict(cls, dados):
        """Restaura o inventário a partir dos dados do save."""
        if not dados:
            return cls()

        inv = cls(capacidade=dados.get("capacidade", cls.SLOTS_INICIAIS))
        
        # Restaura slots
        slots_salvos = dados.get("slots", [])
        inv.slots = []
        for s_dict in slots_salvos:
            slot_obj = ItemSlot.from_dict(s_dict)
            if slot_obj:
                inv.slots.append(slot_obj)

        # Restaura equipados
        equipados_salvos = dados.get("equipados", {})
        for slot_nome in inv.equipados.keys():
            info_eq = equipados_salvos.get(slot_nome)
            if info_eq and isinstance(info_eq, dict):
                item_id = info_eq.get("item_id")
                up = info_eq.get("nivel_upgrade", 0)
                item = ItemFactory.criar(item_id, nivel_upgrade=up)
                inv.equipados[slot_nome] = item
            else:
                inv.equipados[slot_nome] = None

        return inv
