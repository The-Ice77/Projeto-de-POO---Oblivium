# src/mechanics/items.py
from abc import ABC, abstractmethod

class ItemBase(ABC):
    """
    Classe base abstrata para todos os itens do ecossistema de Oblivium.
    Fornece atributos fundamentais, serialização e métodos polimórficos de uso e inspeção.
    """
    def __init__(self, id_item, nome, descricao, categoria, raridade="COMUM", preco_compra=0, preco_venda=0, acumulavel=True, quantidade_maxima=99, icone_sprite=None):
        self.id = id_item
        self.nome = nome
        self.descricao = descricao
        self.categoria = categoria.upper() # CONSUMIVEL, EQUIPAMENTO, GRIMORIO, MATERIAL, CHAVE
        self.raridade = raridade.upper()   # COMUM, INCOMUM, RARO, EPICO, LENDARIO
        self.preco_compra = preco_compra
        self.preco_venda = preco_venda
        self.acumulavel = acumulavel
        self.quantidade_maxima = quantidade_maxima
        self.icone_sprite = icone_sprite

    def to_dict(self):
        """Serializa o item para formato dicionário para persistência em JSON."""
        return {
            "id": self.id,
            "nome": self.nome,
            "descricao": self.descricao,
            "categoria": self.categoria,
            "raridade": self.raridade,
            "preco_compra": self.preco_compra,
            "preco_venda": self.preco_venda,
            "acumulavel": self.acumulavel,
            "quantidade_maxima": self.quantidade_maxima,
            "icone_sprite": self.icone_sprite
        }

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.nome} (ID: {self.id})>"


class ConsumivelItem(ItemBase):
    """
    Item de uso único ou limitado que provoca efeitos imediatos no usuário ou alvo:
    - CURA_HP: Restaura pontos de vida.
    - RESTAURA_MP: Restaura pontos de mana.
    - DANO_OFENSIVO: Causa dano imediato e pode aplicar condição de status.
    - CURA_CONDICAO: Remove aflições ativas (veneno, queimadura, sangramento, etc.).
    - BUFF_TEMPORARIO: Aplica condição benéfica (escudo arcano, foco, etc.).
    """
    def __init__(self, id_item, nome, descricao, tipo_consumivel="CURA_HP", valor_efeito=0, usavel_combate=True, usavel_fora=True, condicao_aplicada=None, raridade="COMUM", preco_compra=0, preco_venda=0, acumulavel=True, quantidade_maxima=20, icone_sprite=None):
        super().__init__(id_item, nome, descricao, "CONSUMIVEL", raridade, preco_compra, preco_venda, acumulavel, quantidade_maxima, icone_sprite)
        self.tipo_consumivel = tipo_consumivel.upper()
        self.valor_efeito = valor_efeito
        self.usavel_combate = usavel_combate
        self.usavel_fora = usavel_fora
        self.condicao_aplicada = condicao_aplicada

    def pode_usar(self, usuario, em_combate=False):
        """Verifica se o item é elegível para uso no contexto atual."""
        if em_combate and not self.usavel_combate:
            return False, "Este item não pode ser utilizado em combate."
        if not em_combate and not self.usavel_fora:
            return False, "Este item só pode ser utilizado durante o combate."
        
        if self.tipo_consumivel == "CURA_HP" and usuario.vida_atual >= usuario.vida_maxima:
            return False, f"A vida de {usuario.nome} já está no máximo."
            
        if self.tipo_consumivel == "RESTAURA_MP" and usuario.mana_atual >= usuario.mana_maxima:
            return False, f"A mana de {usuario.nome} já está no máximo."
            
        return True, "Pronto para uso."

    def usar(self, usuario, alvo=None, em_combate=False):
        """
        Executa o efeito polimórfico do consumível no usuário ou alvo.
        Retorna um dicionário com os detalhes do resultado:
        {'sucesso': bool, 'mensagem': str, 'tipo': str, 'valor': int, 'condicao': str|None}
        """
        pode, msg = self.pode_usar(usuario, em_combate)
        if not pode:
            return {"sucesso": False, "mensagem": msg, "tipo": self.tipo_consumivel, "valor": 0}

        alvo_final = alvo if alvo is not None else usuario

        if self.tipo_consumivel == "CURA_HP":
            vida_antes = usuario.vida_atual
            usuario.curar(self.valor_efeito)
            curado = usuario.vida_atual - vida_antes
            return {
                "sucesso": True,
                "mensagem": f"{usuario.nome} usou {self.nome} e regenerou {curado} PV!",
                "tipo": "CURA_HP",
                "valor": curado
            }

        elif self.tipo_consumivel == "RESTAURA_MP":
            mana_antes = usuario.mana_atual
            usuario.recuperar_mana(self.valor_efeito)
            restaurado = usuario.mana_atual - mana_antes
            return {
                "sucesso": True,
                "mensagem": f"{usuario.nome} bebeu {self.nome} e restaurou {restaurado} PM!",
                "tipo": "RESTAURA_MP",
                "valor": restaurado
            }

        elif self.tipo_consumivel == "DANO_OFENSIVO":
            if alvo_final is None or alvo_final == usuario:
                return {"sucesso": False, "mensagem": "Selecione um inimigo como alvo!", "tipo": "ERRO", "valor": 0}
            
            dano_causado = alvo_final.receber_dano(self.valor_efeito)
            msg = f"{usuario.nome} arremessou {self.nome} em {alvo_final.nome}, causando {dano_causado} de dano!"
            
            cond_aplicada = None
            if self.condicao_aplicada and hasattr(alvo_final, 'aplicar_condicao'):
                alvo_final.aplicar_condicao(self.condicao_aplicada, duracao=3)
                cond_aplicada = self.condicao_aplicada
                msg += f" {alvo_final.nome} sofreu {self.condicao_aplicada.capitalize()}!"
                
            return {
                "sucesso": True,
                "mensagem": msg,
                "tipo": "DANO_OFENSIVO",
                "valor": dano_causado,
                "condicao": cond_aplicada
            }

        elif self.tipo_consumivel == "CURA_CONDICAO":
            if hasattr(usuario, 'condicoes'):
                usuario.condicoes.clear()
            return {
                "sucesso": True,
                "mensagem": f"{usuario.nome} aplicou {self.nome} e purificou todas as suas aflições!",
                "tipo": "CURA_CONDICAO",
                "valor": 0
            }

        return {"sucesso": True, "mensagem": f"{usuario.nome} utilizou {self.nome}.", "tipo": "OUTRO", "valor": 0}

    def to_dict(self):
        d = super().to_dict()
        d.update({
            "tipo_consumivel": self.tipo_consumivel,
            "valor_efeito": self.valor_efeito,
            "usavel_combate": self.usavel_combate,
            "usavel_fora": self.usavel_fora,
            "condicao_aplicada": self.condicao_aplicada
        })
        return d


class EquipamentoItem(ItemBase):
    """
    Equipamento vestível que confere bônus de atributos primários e derivados:
    - Slots: ROUPA, CAJADO, ACESSORIO_1, ACESSORIO_2
    - Nível de Upgrade: de 0 a +5, escalonando atributos a cada refino.
    """
    def __init__(self, id_item, nome, descricao, slot="ROUPA", bonus_atributos=None, bonus_stats=None, nivel_upgrade=0, tier=1, raridade="COMUM", preco_compra=0, preco_venda=0, icone_sprite=None):
        super().__init__(id_item, nome, descricao, "EQUIPAMENTO", raridade, preco_compra, preco_venda, acumulavel=False, quantidade_maxima=1, icone_sprite=icone_sprite)
        self.slot = slot.upper() # ROUPA, CAJADO, ACESSORIO_1, ACESSORIO_2
        self.bonus_atributos = bonus_atributos or {} # ex: {"intelecto": 2, "constituicao": 1}
        self.bonus_stats = bonus_stats or {}         # ex: {"poder_magico": 5, "defesa_fisica": 2, "defesa_magica": 4}
        self.nivel_upgrade = max(0, min(5, nivel_upgrade))
        self.tier = tier

    @property
    def nome_formatado(self):
        """Retorna o nome acompanhado do nível de melhoria (ex: Cajado de Espinheiro +2)."""
        if self.nivel_upgrade > 0:
            return f"{self.nome} +{self.nivel_upgrade}"
        return self.nome

    def obter_bonus_atributos_efetivos(self):
        """Retorna os bônus de atributos considerando o multiplicador de upgrade (+20% por refino)."""
        fator = 1.0 + (self.nivel_upgrade * 0.25)
        efetivos = {}
        for attr, valor in self.bonus_atributos.items():
            efetivos[attr] = int(round(valor * fator))
        return efetivos

    def obter_bonus_stats_efetivos(self):
        """Retorna os bônus em estatísticas derivadas considerando o upgrade."""
        fator = 1.0 + (self.nivel_upgrade * 0.25)
        efetivos = {}
        for stat, valor in self.bonus_stats.items():
            efetivos[stat] = int(round(valor * fator))
        return efetivos

    def pode_aprimorar(self):
        """Retorna True se ainda não atingiu o nível máximo de upgrade (+5)."""
        return self.nivel_upgrade < 5

    def aprimorar(self):
        """Eleva o nível de upgrade do equipamento."""
        if self.pode_aprimorar():
            self.nivel_upgrade += 1
            return True
        return False

    def to_dict(self):
        d = super().to_dict()
        d.update({
            "slot": self.slot,
            "bonus_atributos": self.bonus_atributos,
            "bonus_stats": self.bonus_stats,
            "nivel_upgrade": self.nivel_upgrade,
            "tier": self.tier
        })
        return d


class GrimorioItem(ItemBase):
    """
    Tomo ou Escritura mística que ensina/aprimora feitiços e concede ressonâncias de poder mágico.
    """
    def __init__(self, id_item, nome, descricao, magia_id=None, bonus_stats=None, raridade="RARO", preco_compra=0, preco_venda=0, icone_sprite=None):
        super().__init__(id_item, nome, descricao, "GRIMORIO", raridade, preco_compra, preco_venda, acumulavel=False, quantidade_maxima=1, icone_sprite=icone_sprite)
        self.magia_id = magia_id
        self.bonus_stats = bonus_stats or {}

    def to_dict(self):
        d = super().to_dict()
        d.update({
            "magia_id": self.magia_id,
            "bonus_stats": self.bonus_stats
        })
        return d


class MaterialItem(ItemBase):
    """
    Matéria-prima de alquimia, forja e tecelagem utilizada em receitas e melhorias.
    """
    def __init__(self, id_item, nome, descricao, raridade="COMUM", preco_compra=0, preco_venda=0, acumulavel=True, quantidade_maxima=99, icone_sprite=None):
        super().__init__(id_item, nome, descricao, "MATERIAL", raridade, preco_compra, preco_venda, acumulavel, quantidade_maxima, icone_sprite)


class ItemChave(ItemBase):
    """
    Item de valor narrativo, relíquias, cartas cartográficas e chaves de progressão.
    Não podem ser descartados nem vendidos para mercadores.
    """
    def __init__(self, id_item, nome, descricao, raridade="INCOMUM", preco_compra=0, preco_venda=0, acumulavel=False, quantidade_maxima=1, icone_sprite=None):
        super().__init__(id_item, nome, descricao, "CHAVE", raridade, preco_compra, 0, acumulavel, quantidade_maxima, icone_sprite)
