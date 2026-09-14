# src/mechanics/magia.py
from src.mechanics.skills import MagiaOfensiva, SkillsRegistry

class Magia(MagiaOfensiva):
    """
    Classe de compatibilidade para o sistema de Magias anterior.
    Herda da arquitetura modular de Skills e mantém métodos legados.
    """
    def __init__(self, id_magia, nome, elemento, custo_mana, dano, tipo_efeito="PROJETIL", descricao=""):
        super().__init__(
            id_acao=id_magia,
            nome=nome,
            descricao=descricao,
            elemento=elemento,
            custo_mana=custo_mana,
            poder_base=dano
        )
        self.id_magia = id_magia
        self.dano = dano
        self.tipo_efeito = tipo_efeito

    def pode_usar(self, player):
        """Verifica se o jogador tem mana suficiente para lançar a magia."""
        return super().pode_usar(player)

    def executar_custo(self, player):
        """Deduz o custo de mana do jogador se ele puder usar."""
        return self.deduzir_custos(player)