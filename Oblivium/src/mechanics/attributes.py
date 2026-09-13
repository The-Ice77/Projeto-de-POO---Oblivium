# src/mechanics/attributes.py
import random

class Atributos:
    """
    Componente modular de atributos para entidades (Halia, Inimigos, Chefes, NPCs).
    Gerencia os 6 atributos principais, cálculos derivados (HP/MP, Defesa, Modificadores)
    e testes de perícia.
    """
    def __init__(self, forca=10, destreza=10, constituicao=10, intelecto=10, sabedoria=10, presenca=10):
        self.forca = int(forca)              # Dano físico, força bruta
        self.destreza = int(destreza)        # Iniciativa, esquiva, acertos críticos
        self.constituicao = int(constituicao)# Bônus de vida máxima, resistência física
        self.intelecto = int(intelecto)      # Dano mágico elemental, arcanismo
        self.sabedoria = int(sabedoria)      # Bônus de mana máxima, curas, resistência mental
        self.presenca = int(presenca)        # Foco em combate, regeneração tática, moral

    # ==========================================
    # CÁLCULO DE MODIFICADORES
    # ==========================================
    @staticmethod
    def calcular_modificador(valor):
        """Calcula o modificador padrão (ex: 10 -> 0, 12 -> +1, 14 -> +2, 8 -> -1)."""
        return (valor - 10) // 2

    @property
    def mod_for(self):
        return self.calcular_modificador(self.forca)

    @property
    def mod_des(self):
        return self.calcular_modificador(self.destreza)

    @property
    def mod_con(self):
        return self.calcular_modificador(self.constituicao)

    @property
    def mod_int(self):
        return self.calcular_modificador(self.intelecto)

    @property
    def mod_sab(self):
        return self.calcular_modificador(self.sabedoria)

    @property
    def mod_pre(self):
        return self.calcular_modificador(self.presenca)

    # ==========================================
    # ESTATÍSTICAS DERIVADAS PARA COMBATE
    # ==========================================
    def calcular_vida_maxima(self, vida_base=50):
        """Vida Máxima = Vida Base + (Constituição * 5)."""
        return max(10, vida_base + (self.constituicao * 5))

    def calcular_mana_maxima(self, mana_base=20):
        """Mana Máxima = Mana Base + (Sabedoria * 3)."""
        return max(0, mana_base + (self.sabedoria * 3))

    def calcular_iniciativa(self):
        """Iniciativa para ordenar turnos = Destreza + variação d6."""
        return self.destreza + random.randint(1, 6)

    def calcular_defesa_fisica(self):
        """Defesa física passiva reduz dano direto."""
        return max(0, self.mod_con + (self.forca // 4))

    def calcular_defesa_magica(self):
        """Defesa mágica passiva reduz dano elemental/arcano."""
        return max(0, self.mod_sab + (self.intelecto // 4))

    def calcular_chance_critico(self):
        """Retorna chance de acerto crítico em % (ex: 5% a 30%)."""
        base_crit = 5.0
        bonus_des = max(0, self.mod_des) * 2.5
        bonus_pre = max(0, self.mod_pre) * 1.5
        return min(35.0, base_crit + bonus_des + bonus_pre)

    def calcular_recuperacao_foco(self):
        """Calcula recuperação de mana durante a ação de Concentrar."""
        return max(5, 5 + self.mod_pre * 2 + self.mod_sab)

    # ==========================================
    # TESTES DE PERÍCIA / DESAFIOS
    # ==========================================
    def testar(self, nome_atributo, dificuldade=12):
        """
        Executa um teste de atributo estilo d20 + modificador contra uma dificuldade.
        Retorna: (sucesso: bool, total_rolado: int, detalhe: str)
        """
        mapa_mods = {
            "forca": self.mod_for,
            "destreza": self.mod_des,
            "constituicao": self.mod_con,
            "intelecto": self.mod_int,
            "sabedoria": self.mod_sab,
            "presenca": self.mod_pre
        }
        mod = mapa_mods.get(nome_atributo.lower(), 0)
        rolagem = random.randint(1, 20)
        total = rolagem + mod
        sucesso = total >= dificuldade
        return sucesso, total, f"Rolagem ({rolagem}) + Mod ({mod:+d}) = {total} vs Dif ({dificuldade})"

    # ==========================================
    # SERIALIZAÇÃO PARA SAVES
    # ==========================================
    def to_dict(self):
        return {
            "forca": self.forca,
            "destreza": self.destreza,
            "constituicao": self.constituicao,
            "intelecto": self.intelecto,
            "sabedoria": self.sabedoria,
            "presenca": self.presenca
        }

    @classmethod
    def from_dict(cls, data):
        if not data or not isinstance(data, dict):
            return cls()
        return cls(
            forca=data.get("forca", 10),
            destreza=data.get("destreza", 10),
            constituicao=data.get("constituicao", 10),
            intelecto=data.get("intelecto", 10),
            sabedoria=data.get("sabedoria", 10),
            presenca=data.get("presenca", 10)
        )

    def __repr__(self):
        return (f"Atributos(FOR={self.forca}, DES={self.destreza}, CON={self.constituicao}, "
                f"INT={self.intelecto}, SAB={self.sabedoria}, PRE={self.presenca})")
