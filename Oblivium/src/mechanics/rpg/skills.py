# src/mechanics/rpg/skills.py
import copy
import random
import json
import os

from abc import ABC, abstractmethod
from src.mechanics.rpg.conditions import Condicao
from src.utils.constants import PASTA_DATA


def _obter_atributos_efetivos(entidade):
    """Retorna os atributos efetivos da entidade (com equipamentos quando aplicável)."""
    if entidade is None:
        return None
    if hasattr(entidade, "obter_atributos_efetivos"):
        attrs = entidade.obter_atributos_efetivos()
        if attrs is not None:
            return attrs
    if hasattr(entidade, "obter_atributos_totais"):
        attrs = entidade.obter_atributos_totais()
        if attrs is not None:
            return attrs
    return getattr(entidade, "atributos", None)

class AcaoCombate(ABC):
    """

    Classe base abstrata para todas as ações executáveis em combate (Ataques, Magias, Foco, Suporte).

    Implementa o padrão Strategy / Command para execução desacoplada.

    """

    def __init__(self, id_acao, nome, descricao, tipo, elemento="FISICO", custo_mana=0, alvo_tipo="INIMIGO_UNICO", poder_base=10, condicao_aplicada=None):
        self.id_acao = id_acao
        self.nome = nome
        self.descricao = descricao
        self.tipo = tipo            # "FISICO", "MAGICO", "CURA", "FOCO", "BUFF", "DEBUFF"
        self.elemento = elemento    # "FISICO", "FOGO", "ARCANO", "SAGRADO", "SOMBRA", "NEUTRO"
        self.custo_mana = custo_mana
        self.alvo_tipo = alvo_tipo  # "INIMIGO_UNICO", "TODOS_INIMIGOS", "PROPRIO", "ALIADO"
        self.poder_base = poder_base
        self.condicao_aplicada = condicao_aplicada # Dict com {"id_condicao": ..., "chance": ...}

    @property
    def tipo_alvo(self):
        """Retorna o tipo de alvo em formato minúsculo padronizado."""
        return str(self.alvo_tipo).lower()

    @tipo_alvo.setter
    def tipo_alvo(self, valor):
        self.alvo_tipo = valor

    def obter_custo_mana(self, conjurador=None):
        """Retorna o custo de mana efetivo considerando bônus de maestria e grimórios equipados."""
        custo = self.custo_mana
        if conjurador:
            # 1. Bônus de maestria permanente do conjurador
            if hasattr(conjurador, 'maestria_feiticos'):
                maestria = conjurador.maestria_feiticos.get(self.id_acao, {})
                reducao = maestria.get('reducao_custo', 0)
                custo -= reducao
            # 2. Bônus de tomos arcanos equipados nos 4 slots de grimório
            if hasattr(conjurador, 'inventario') and conjurador.inventario:
                equipados = getattr(conjurador.inventario, 'equipados', {})
                for g_slot in ['GRIMORIO_1', 'GRIMORIO_2', 'GRIMORIO_3', 'GRIMORIO_4']:
                    tomo = equipados.get(g_slot)
                    if tomo and getattr(tomo, 'magia_id', None) == self.id_acao:
                        custo -= getattr(tomo, 'reducao_custo', 0)
        return max(1 if self.custo_mana > 0 else 0, custo)
    def pode_usar(self, conjurador):
        """Verifica se o conjurador tem recursos (mana/vida) para executar a ação."""
        if not getattr(conjurador, 'vivo', True):
            return False
        custo_efetivo = self.obter_custo_mana(conjurador)
        if custo_efetivo > 0:
            mana_atual = getattr(conjurador, 'mana_atual', 0)
            return mana_atual >= custo_efetivo
        return True

    def deduzir_custos(self, conjurador):
        """Deduz o custo de mana do conjurador aplicando redução de maestria."""
        custo_efetivo = self.obter_custo_mana(conjurador)
        if custo_efetivo > 0 and hasattr(conjurador, 'gastar_mana'):
            return conjurador.gastar_mana(custo_efetivo)
        elif custo_efetivo > 0 and hasattr(conjurador, 'mana_atual'):
            conjurador.mana_atual -= custo_efetivo
            return True
        return True

    def calcular_critico(self, conjurador):
        """Determina se a ação gerou um acerto crítico baseado em Destreza e Presença."""
        attrs = _obter_atributos_efetivos(conjurador)
        if attrs is None:
            return False, 1.0
        chance = attrs.calcular_chance_critico()
        rolagem = random.uniform(0, 100)
        if rolagem <= chance:
            return True, 1.5
        return False, 1.0

    def tentar_aplicar_condicao(self, alvo):
        """Aplica condição de estado caso configurada e a rolagem de chance tenha sucesso."""
        alvo._ultima_resistencia_cc = None
        if not self.condicao_aplicada or not hasattr(alvo, 'adicionar_condicao'):
            return None

        chance = self.condicao_aplicada.get("chance", 30)
        id_cond = self.condicao_aplicada.get("id_condicao", "queimadura")
        duracao = self.condicao_aplicada.get("duracao", None)
        intensidade = self.condicao_aplicada.get("intensidade", None)

        if random.uniform(0, 100) <= chance:
            nova_cond = Condicao.criar(id_cond, duracao=duracao, intensidade=intensidade)
            aplicada = alvo.adicionar_condicao(nova_cond)
            if aplicada is False:
                if getattr(nova_cond, 'tipo', '') == 'CC':
                    alvo._ultima_resistencia_cc = nova_cond.nome
                return None
            return nova_cond
        return None

    def verificar_acerto(self, conjurador, alvo):
        """

        Calcula se o ataque/magia acertou o alvo com base em Destreza, atributos e postura defensiva.

        Retorna (acertou: bool, motivo: str) onde motivo pode ser 'acerto', 'esquiva' ou 'erro'.

        """

        attrs_conjurador = _obter_atributos_efetivos(conjurador)
        attrs_alvo = _obter_atributos_efetivos(alvo)
        if attrs_alvo is None or attrs_conjurador is None:
            return True, "acerto"

        # Se o alvo estiver atordoado ou incapacitado, acerto garantido (100%)
        if getattr(alvo, 'esta_atordoado', False):
            return True, "acerto"

        # Precisão do atacante
        if self.tipo == "FISICO":
            precisao_base = 86.0
            bonus_conjurador = (attrs_conjurador.mod_des * 2.0) + (attrs_conjurador.mod_for * 0.5)
        else: # MAGICO
            precisao_base = 88.0
            bonus_conjurador = (attrs_conjurador.mod_int * 2.0) + (attrs_conjurador.mod_sab * 1.0)

        # Evasão do defensor (base de agilidade + modificador de Destreza)
        evasao_base = 8.0
        evasao_alvo = evasao_base + max(0.0, attrs_alvo.mod_des * 3.0)
        
        # Postura defensiva (Defender) concede enorme bônus de esquiva (+45%)
        if getattr(alvo, 'defendendo', False):
            evasao_alvo += 45.0
            
        # Estado vulnerável (Foco Espiritual) reduz drasticamente a esquiva (-15%)
        if getattr(alvo, 'vulneravel', False):
            evasao_alvo = max(0.0, evasao_alvo - 15.0)

        # Chance final de acerto
        chance_acerto = max(25.0, min(95.0, precisao_base + bonus_conjurador - evasao_alvo))
        rolagem = random.uniform(0, 100)

        if rolagem <= chance_acerto:
            return True, "acerto"
        else:
            # Se o alvo estava defendendo ou tem evasão relevante, conta como esquiva ágil
            if getattr(alvo, 'defendendo', False) or evasao_alvo >= 10.0 or random.random() < 0.75:
                return False, "esquiva"
            return False, "erro"

    @abstractmethod
    def executar(self, conjurador, alvos):
        """

        Executa a ação sobre uma lista de alvos.

        Retorna um dicionário com o relatório detalhado da execução para a UI / Combat Log.

        """

        pass


# ==============================================================================
# SUBCLASSES ESPECÍFICAS DE AÇÕES
# ==============================================================================

class AtaqueFisico(AcaoCombate):
    """Ataque físico direto escalado com Força e Destreza."""
    def __init__(self, id_acao, nome, descricao, poder_base=12, custo_mana=0, alvo_tipo="INIMIGO_UNICO", elemento="FISICO", condicao_aplicada=None):
        super().__init__(id_acao, nome, descricao, tipo="FISICO", elemento=elemento, custo_mana=custo_mana, alvo_tipo=alvo_tipo, poder_base=poder_base, condicao_aplicada=condicao_aplicada)

    def executar(self, conjurador, alvos):
        if not self.pode_usar(conjurador):
            return {"sucesso": False, "mensagem": f"{conjurador.nome} não tem mana suficiente!"}

        self.deduzir_custos(conjurador)
        resultados = []

        if not isinstance(alvos, list):
            alvos = [alvos]

        for alvo in alvos:
            if not getattr(alvo, 'vivo', True):
                continue

            # 1. Verifica se o ataque acertou ou errou/esquivou
            acertou, motivo = self.verificar_acerto(conjurador, alvo)
            if not acertou:
                if motivo == "esquiva":
                    msg = f"{conjurador.nome} usou {self.nome}, mas {alvo.nome} se esquivou agilmente!"
                else:
                    msg = f"{conjurador.nome} usou {self.nome}, mas errou o ataque contra {alvo.nome}!"
                
                resultados.append({
                    "alvo": alvo,
                    "dano": 0,
                    "cura": 0,
                    "errou": True,
                    "motivo": motivo,
                    "critico": False,
                    "tipo_dano": "FISICO",
                    "mensagem": msg
                })
                continue

            # 2. Executa cálculo de dano e crítico em caso de acerto
            critico, mult_crit = self.calcular_critico(conjurador)
            attrs_conj = _obter_atributos_efetivos(conjurador)
            mod_for = getattr(attrs_conj, 'mod_for', 0) if attrs_conj else 0
            mod_des = getattr(attrs_conj, 'mod_des', 0) if attrs_conj else 0
            variacao = random.randint(-2, 2)

            dano_bruto = int((self.poder_base + (mod_for * 1.5) + (mod_des * 0.8) + variacao) * mult_crit)
            mult_fase = float(getattr(conjurador, 'multiplicador_fase', 1.15 if getattr(conjurador, 'enfurecido', False) else 1.0))
            dano_bruto = max(1, int(round(dano_bruto * mult_fase)))

            dano_sofrido = alvo.aplicar_dano(dano_bruto, tipo="fisico")
            
            cond_aplicada = self.tentar_aplicar_condicao(alvo)
            texto_crit = " (CRÍTICO!)" if critico else ""
            res_cc = getattr(alvo, '_ultima_resistencia_cc', None)
            texto_cond = f" [{cond_aplicada.nome} {cond_aplicada.icone}]" if cond_aplicada else (f" [{res_cc} Resistido - Imunidade Temporária!]" if res_cc else "")
            msg = f"{conjurador.nome} usou {self.nome} em {alvo.nome} causando {dano_sofrido} de dano{texto_crit}{texto_cond}."
            
            resultados.append({
                "alvo": alvo,
                "dano": dano_sofrido,
                "cura": 0,
                "errou": False,
                "motivo": "acerto",
                "critico": critico,
                "condicao": cond_aplicada,
                "tipo_dano": "FISICO",
                "mensagem": msg
            })

        return {
            "sucesso": True,
            "acao": self,
            "conjurador": conjurador,
            "resultados": resultados
        }


class MagiaOfensiva(AcaoCombate):
    """Magia de dano elemental / arcano escalada com Intelecto e Sabedoria."""
    def __init__(self, id_acao, nome, descricao, elemento, custo_mana, poder_base=20, alvo_tipo="INIMIGO_UNICO", condicao_aplicada=None):
        super().__init__(id_acao, nome, descricao, tipo="MAGICO", elemento=elemento, custo_mana=custo_mana, alvo_tipo=alvo_tipo, poder_base=poder_base, condicao_aplicada=condicao_aplicada)

    def executar(self, conjurador, alvos):
        if not self.pode_usar(conjurador):
            return {"sucesso": False, "mensagem": f"{conjurador.nome} não tem mana suficiente para {self.nome}!"}

        self.deduzir_custos(conjurador)
        resultados = []

        if not isinstance(alvos, list):
            alvos = [alvos]

        for alvo in alvos:
            if not getattr(alvo, 'vivo', True):
                continue

            # 1. Verifica se a magia acertou ou errou/esquivou
            acertou, motivo = self.verificar_acerto(conjurador, alvo)
            if not acertou:
                if motivo == "esquiva":
                    msg = f"{conjurador.nome} conjurou {self.nome}, mas {alvo.nome} esquivou-se da magia!"
                else:
                    msg = f"{conjurador.nome} conjurou {self.nome}, mas a magia errou o alvo {alvo.nome}!"
                
                resultados.append({
                    "alvo": alvo,
                    "dano": 0,
                    "cura": 0,
                    "errou": True,
                    "motivo": motivo,
                    "critico": False,
                    "tipo_dano": "MAGICO",
                    "elemento": self.elemento,
                    "mensagem": msg
                })
                continue

            # 2. Executa cálculo de dano e crítico em caso de acerto
            critico, mult_crit = self.calcular_critico(conjurador)
            attrs_conj = _obter_atributos_efetivos(conjurador)
            mod_int = getattr(attrs_conj, 'mod_int', 0) if attrs_conj else 0
            mod_sab = getattr(attrs_conj, 'mod_sab', 0) if attrs_conj else 0
            variacao = random.randint(-2, 3)

            bonus_maestria = 0
            if hasattr(conjurador, 'maestria_feiticos'):
                bonus_maestria = conjurador.maestria_feiticos.get(self.id_acao, {}).get('bonus_poder', 0)
            # Bônus de tomos equipados e equipamentos arcanos (cajados, vestimentas, acessórios)
            bonus_grimorio = 0
            poder_magico_equip = 0
            bonus_elemental_pct = 0
            if hasattr(conjurador, 'inventario') and conjurador.inventario:
                equipados = getattr(conjurador.inventario, 'equipados', {})
                for g_slot in ['GRIMORIO_1', 'GRIMORIO_2', 'GRIMORIO_3', 'GRIMORIO_4']:
                    tomo = equipados.get(g_slot)
                    if tomo and getattr(tomo, 'magia_id', None) == self.id_acao:
                        bonus_grimorio += getattr(tomo, 'bonus_poder', 0)
                totais = conjurador.inventario.obter_bonus_totais_equipamentos()
                stats_eq = totais.get('stats', {})
                poder_magico_equip = stats_eq.get('poder_magico', 0) + stats_eq.get('dano_magico', 0)
                if self.elemento == 'FOGO':
                    bonus_elemental_pct = stats_eq.get('dano_fogo_bonus', 0)
                elif self.elemento in ['GELO', 'FRIO']:
                    bonus_elemental_pct = stats_eq.get('dano_gelo_bonus', 0)
            poder_calculado = (self.poder_base + bonus_maestria + bonus_grimorio + poder_magico_equip + (mod_int * 2.2) + (mod_sab * 0.8) + variacao)
            if bonus_elemental_pct > 0:
                poder_calculado = poder_calculado * (1.0 + (bonus_elemental_pct / 100.0))
            dano_bruto = int(poder_calculado * mult_crit)
            mult_fase = float(getattr(conjurador, 'multiplicador_fase', 1.15 if getattr(conjurador, 'enfurecido', False) else 1.0))
            dano_bruto = max(2, int(round(dano_bruto * mult_fase)))
            dano_sofrido = alvo.aplicar_dano(dano_bruto, tipo="magico")
            
            cond_aplicada = self.tentar_aplicar_condicao(alvo)
            texto_crit = " (CRÍTICO MÁGICO!)" if critico else ""
            res_cc = getattr(alvo, '_ultima_resistencia_cc', None)
            texto_cond = f" [{cond_aplicada.nome} {cond_aplicada.icone}]" if cond_aplicada else (f" [{res_cc} Resistido - Imunidade Temporária!]" if res_cc else "")
            msg = f"{conjurador.nome} conjurou {self.nome} em {alvo.nome} causando {dano_sofrido} de dano [{self.elemento}]{texto_crit}{texto_cond}."
            
            resultados.append({
                "alvo": alvo,
                "dano": dano_sofrido,
                "cura": 0,
                "errou": False,
                "motivo": "acerto",
                "critico": critico,
                "condicao": cond_aplicada,
                "tipo_dano": "MAGICO",
                "elemento": self.elemento,
                "mensagem": msg
            })

        return {
            "sucesso": True,
            "acao": self,
            "conjurador": conjurador,
            "resultados": resultados
        }


class MagiaCura(AcaoCombate):
    """Magia de restauração de pontos de vida escalada com Sabedoria e Presença."""
    def __init__(self, id_acao, nome, descricao, custo_mana=15, poder_base=25, alvo_tipo="PROPRIO", condicao_aplicada=None, elemento="SAGRADO"):
        super().__init__(id_acao, nome, descricao, tipo="CURA", elemento=elemento, custo_mana=custo_mana, alvo_tipo=alvo_tipo, poder_base=poder_base, condicao_aplicada=condicao_aplicada)

    def executar(self, conjurador, alvos):
        if not self.pode_usar(conjurador):
            return {"sucesso": False, "mensagem": f"{conjurador.nome} não tem mana suficiente para {self.nome}!"}

        self.deduzir_custos(conjurador)
        resultados = []

        if not isinstance(alvos, list):
            alvos = [alvos]

        for alvo in alvos:
            if not getattr(alvo, 'vivo', True):
                continue

            attrs_conj = _obter_atributos_efetivos(conjurador)
            mod_sab = getattr(attrs_conj, 'mod_sab', 0) if attrs_conj else 0
            mod_pre = getattr(attrs_conj, 'mod_pre', 0) if attrs_conj else 0
            variacao = random.randint(-1, 3)

            bonus_maestria = 0
            if hasattr(conjurador, 'maestria_feiticos'):
                bonus_maestria = conjurador.maestria_feiticos.get(self.id_acao, {}).get('bonus_poder', 0)
            bonus_grimorio = 0
            bonus_cura_pct = 0
            poder_magico_equip = 0
            if hasattr(conjurador, 'inventario') and conjurador.inventario:
                equipados = getattr(conjurador.inventario, 'equipados', {})
                for g_slot in ['GRIMORIO_1', 'GRIMORIO_2', 'GRIMORIO_3', 'GRIMORIO_4']:
                    tomo = equipados.get(g_slot)
                    if tomo and getattr(tomo, 'magia_id', None) == self.id_acao:
                        bonus_grimorio += getattr(tomo, 'bonus_poder', 0)
                totais = conjurador.inventario.obter_bonus_totais_equipamentos()
                stats_eq = totais.get('stats', {})
                bonus_cura_pct = stats_eq.get('cura_bonus', 0)
                poder_magico_equip = stats_eq.get('poder_magico', 0) // 2
            cura_base = (self.poder_base + bonus_maestria + bonus_grimorio + poder_magico_equip + (mod_sab * 2.5) + (mod_pre * 1.2) + variacao)
            if bonus_cura_pct > 0:
                cura_base = cura_base * (1.0 + (bonus_cura_pct / 100.0))
            cura_calculada = max(5.0, cura_base)
            cura_bruta = round(cura_calculada, 1)
            from src.entities.Entity import Entidade
            vida_antes = float(alvo.vida_atual)
            delta = alvo.curar(cura_bruta)
            cura_efetiva = Entidade.normalizar_recurso(max(0.0, float(alvo.vida_atual) - vida_antes) if delta is None else delta)
            cond_aplicada = self.tentar_aplicar_condicao(alvo)

            # Formatação limpa de dígitos (ex: 33 se inteiro, 33.3 se decimal)
            cura_fmt = str(cura_efetiva)
            vida_atual_fmt = str(Entidade.normalizar_recurso(alvo.vida_atual))
            vida_max_fmt = str(Entidade.normalizar_recurso(alvo.vida_maxima))

            texto_cond = f" [{cond_aplicada.nome} {cond_aplicada.icone}]" if cond_aplicada else ""
            msg = f"{conjurador.nome} usou {self.nome} e recuperou {cura_fmt} de vida ({vida_atual_fmt}/{vida_max_fmt}){texto_cond}."
            
            resultados.append({
                "alvo": alvo,
                "dano": 0,
                "cura": cura_efetiva,
                "critico": False,
                "condicao": cond_aplicada,
                "tipo_dano": "CURA",
                "mensagem": msg
            })

        return {
            "sucesso": True,
            "acao": self,
            "conjurador": conjurador,
            "resultados": resultados
        }


class AcaoDefender(AcaoCombate):
    """Ação tática que assume postura de guarda para reduzir danos pela metade e esquivar de ataques."""
    def __init__(self, id_acao="defender", nome="Defender", descricao="Assume postura de guarda. Reduz danos recebidos pela metade e esquiva com facilidade.", custo_mana=0, poder_base=0, elemento="NEUTRO", alvo_tipo="PROPRIO", condicao_aplicada=None):
        super().__init__(id_acao, nome, descricao, tipo="DEFESA", elemento=elemento, custo_mana=custo_mana, alvo_tipo=alvo_tipo, poder_base=poder_base, condicao_aplicada=condicao_aplicada)

    def executar(self, conjurador, alvos=None):
        if not self.pode_usar(conjurador):
            return {"sucesso": False, "mensagem": f"{conjurador.nome} não tem mana suficiente para {self.nome}!"}

        self.deduzir_custos(conjurador)
        conjurador.defendendo = True
        conjurador.vulneravel = False
        conjurador.focado = False
        cond_aplicada = self.tentar_aplicar_condicao(conjurador)

        texto_cond = f" [{cond_aplicada.nome} {cond_aplicada.icone}]" if cond_aplicada else ""
        msg = f"{conjurador.nome} assumiu postura defensiva em guarda total, reduzindo danos e preparando esquiva!{texto_cond}"
        
        return {
            "sucesso": True,
            "acao": self,
            "conjurador": conjurador,
            "defendendo": True,
            "mensagem": msg,
            "resultados": [{
                "alvo": conjurador,
                "dano": 0,
                "cura": 0,
                "defendendo": True,
                "critico": False,
                "condicao": cond_aplicada,
                "mensagem": msg
            }]
        }


class AcaoFoco(AcaoCombate):
    """Ação que canaliza energia espiritual para recuperar Mana, abrindo a guarda e deixando o conjurador vulnerável."""
    def __init__(self, id_acao="foco_espiritual", nome="Foco Espiritual", descricao="Canaliza energia espiritual para recuperar grande quantidade de Mana, mas fica vulnerável (+35% dano).", custo_mana=0, poder_base=15, elemento="NEUTRO", alvo_tipo="PROPRIO", condicao_aplicada=None):
        super().__init__(id_acao, nome, descricao, tipo="FOCO", elemento=elemento, custo_mana=custo_mana, alvo_tipo=alvo_tipo, poder_base=poder_base, condicao_aplicada=condicao_aplicada)

    def executar(self, conjurador, alvos=None):
        if not self.pode_usar(conjurador):
            return {"sucesso": False, "mensagem": f"{conjurador.nome} não tem mana suficiente para {self.nome}!"}

        self.deduzir_custos(conjurador)
        attrs_conj = _obter_atributos_efetivos(conjurador)
        mod_pre = getattr(attrs_conj, 'mod_pre', 0) if attrs_conj else 0
        mod_sab = getattr(attrs_conj, 'mod_sab', 0) if attrs_conj else 0
        
        mana_recuperada = max(12, 12 + (mod_pre * 3) + (mod_sab * 2) + random.randint(2, 5))
        
        from src.entities.Entity import Entidade
        mana_antes = float(getattr(conjurador, 'mana_atual', 0))
        delta = None
        if hasattr(conjurador, 'recuperar_mana'):
            delta = conjurador.recuperar_mana(mana_recuperada)
        elif hasattr(conjurador, 'mana_atual'):
            conjurador.mana_atual = min(conjurador.mana_maxima, conjurador.mana_atual + mana_recuperada)
        mana_efetiva = Entidade.normalizar_recurso(
            max(0.0, float(getattr(conjurador, 'mana_atual', 0)) - mana_antes) if delta is None else delta
        )

        # Ao concentrar, abre a guarda ficando vulnerável
        conjurador.defendendo = False
        conjurador.vulneravel = True
        conjurador.focado = True

        msg = f"{conjurador.nome} concentrou sua energia recuperando {mana_efetiva} MP, mas ficou vulnerável a ataques (+35% dano)!"
        
        return {
            "sucesso": True,
            "acao": self,
            "conjurador": conjurador,
            "mana_recuperada": mana_efetiva,
            "vulneravel": True,
            "mensagem": msg,
            "resultados": [{
                "alvo": conjurador,
                "dano": 0,
                "cura": 0,
                "mana_recuperada": mana_efetiva,
                "vulneravel": True,
                "critico": False,
                "mensagem": msg
            }]
        }


# ==============================================================================
# REGISTRO CENTRAL DE HABILIDADES (REGISTRY PATTERN)
# ==============================================================================

class SkillsRegistry:
    """Catálogo centralizado de todas as habilidades, magias e ações de combate do jogo."""

    _catalogo = {}
    _dados_json = {}
    _MAPA_CLASSES_TIPO = {
        "FISICO": (AtaqueFisico, {"elemento": "FISICO", "custo_mana": 0, "poder_base": 12, "alvo_tipo": "INIMIGO_UNICO"}),
        "CURA": (MagiaCura, {"elemento": "SAGRADO", "custo_mana": 15, "poder_base": 25, "alvo_tipo": "PROPRIO"}),
        "DEFESA": (AcaoDefender, {"elemento": "NEUTRO", "custo_mana": 0, "poder_base": 0, "alvo_tipo": "PROPRIO"}),
        "BUFF": (AcaoDefender, {"elemento": "NEUTRO", "custo_mana": 0, "poder_base": 0, "alvo_tipo": "PROPRIO"}),
        "FOCO": (AcaoFoco, {"elemento": "NEUTRO", "custo_mana": 0, "poder_base": 15, "alvo_tipo": "PROPRIO"}),
    }

    @classmethod
    def registrar(cls, acao):
        """Registra uma ação ou magia no catálogo."""
        cls._catalogo[acao.id_acao] = acao

    @classmethod
    def get(cls, id_acao):
        """Retorna uma ação pelo ID ou None se não existir."""
        if not cls._catalogo:
            cls.inicializar_catalogo_padrao()

        aliases = {
            "defender": "defender",
            "defesa": "defender",
            "guarda": "defender",
            "foco": "foco_espiritual",
            "concentrar": "foco_espiritual",
            "ataque": "ataque_basico",
            "cajado": "ataque_basico",
            "fogo": "bola_de_fogo",
            "cura": "brisa_curativa"
        }
        id_str = str(id_acao).lower()
        chave = aliases.get(id_str, id_str)
        return cls._catalogo.get(chave) or cls._catalogo.get(id_acao)

    @classmethod
    def listar_todas(cls):
        """Retorna lista de todas as ações registradas."""
        return list(cls._catalogo.values())

    @classmethod
    def obter_magias_iniciais_player(cls):
        """Retorna as ações iniciais que Halia possui no início da jornada."""
        return [
            cls.get("ataque_basico"),
            cls.get("bola_de_fogo"),
            cls.get("levitar"),
        ]

    @classmethod
    def _instanciar_acao(cls, info):
        """Instancia uma subclasse concreta de AcaoCombate a partir de um dicionário canônico."""
        tipo = str(info.get("tipo", "MAGICO")).upper()
        classe_alvo, defaults = cls._MAPA_CLASSES_TIPO.get(
            tipo,
            (MagiaOfensiva, {"elemento": "ARCANO", "custo_mana": 10, "poder_base": 20, "alvo_tipo": "INIMIGO_UNICO"}),
        )
        return classe_alvo(
            id_acao=info["id_acao"],
            nome=info["nome"],
            descricao=info.get("descricao", ""),
            elemento=info.get("elemento", defaults["elemento"]),
            custo_mana=info.get("custo_mana", defaults["custo_mana"]),
            poder_base=info.get("poder_base", defaults["poder_base"]),
            alvo_tipo=info.get("alvo_tipo", defaults["alvo_tipo"]),
            condicao_aplicada=info.get("condicao_aplicada", None),
        )

    @classmethod
    def criar_instancia(cls, id_acao):
        """Retorna uma nova instância independente da ação a partir do JSON canônico."""
        if not cls._catalogo:
            cls.inicializar_catalogo_padrao()
        info = cls._dados_json.get(id_acao)
        if info:
            return cls._instanciar_acao(info)
        modelo = cls.get(id_acao)
        return copy.copy(modelo) if modelo is not None else None

    @classmethod
    def obter_dados_raw(cls, id_acao):
        """Retorna cópia dos metadados de combate de uma ação definida em skills.json."""
        if not cls._catalogo:
            cls.inicializar_catalogo_padrao()
        info = cls._dados_json.get(id_acao)
        if info:
            return copy.deepcopy(info)
        acao = cls.get(id_acao)
        if not acao:
            return None
        return {
            "id_acao": acao.id_acao,
            "nome": acao.nome,
            "descricao": acao.descricao,
            "tipo": acao.tipo,
            "elemento": acao.elemento,
            "custo_mana": acao.custo_mana,
            "poder_base": acao.poder_base,
            "alvo_tipo": acao.alvo_tipo,
            "condicao_aplicada": copy.deepcopy(acao.condicao_aplicada),
        }

    @classmethod
    def carregar_de_json(cls, caminho_json=None):
        """Carrega todas as habilidades e magias a partir do arquivo JSON."""
        if caminho_json is None:
            caminho_json = os.path.join(PASTA_DATA, "skills.json")
            
        if not os.path.exists(caminho_json):
            print(f"[SkillsRegistry] Aviso: Arquivo '{caminho_json}' não encontrado. Usando catálogo em memória.")
            return False

        try:
            with open(caminho_json, "r", encoding="utf-8") as f:
                dados = json.load(f)

            cls._catalogo.clear()
            cls._dados_json.clear()
            for id_acao, info in dados.items():
                cls._dados_json[id_acao] = copy.deepcopy(info)
                instancia = cls._instanciar_acao(info)
                cls.registrar(instancia)
            return True
        except Exception as e:
            print(f"[SkillsRegistry] Erro ao carregar skills.json: {e}")
            return False

    @classmethod
    def inicializar_catalogo_padrao(cls):
        """Inicializa o catálogo prioritariamente a partir do JSON."""
        sucesso = cls.carregar_de_json()
        if not sucesso:
            # Fallback seguro caso o JSON não esteja disponível
            cls.registrar(AtaqueFisico("ataque_basico", "Golpe com Cajado", "Ataque físico", 12))
            cls.registrar(AcaoDefender("defender", "Defender", "Assume postura defensiva"))
            cls.registrar(AcaoFoco("foco_espiritual", "Concentrar", "Recupera Mana"))
            cls.registrar(MagiaOfensiva("bola_de_fogo", "Bola de Fogo", "Fogo", "FOGO", 12, 22))
            cls.registrar(MagiaOfensiva("levitar", "Pulso de Gravidade", "Arcano", "ARCANO", 14, 24))
            cls.registrar(MagiaCura("brisa_curativa", "Brisa Curativa", "Cura", 15, 28))

# Inicializa o catálogo padrão automaticamente ao carregar o módulo
SkillsRegistry.inicializar_catalogo_padrao()

# Alias de compatibilidade
ActionCatalog = SkillsRegistry
