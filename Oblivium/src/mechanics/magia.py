# src/mechanics/magia.py

class Magia:
    def __init__(self, id_magia, nome, elemento, custo_mana, dano, tipo_efeito, descricao):
        self.id_magia = id_magia
        self.nome = nome
        self.elemento = elemento
        self.custo_mana = custo_mana
        self.dano = dano
        self.tipo_efeito = tipo_efeito  # Ex: "PROJETIL", "BUFF", "UTILIDADE"
        self.descricao = descricao

    def pode_usar(self, player):
        """Verifica se o jogador tem mana suficiente para lançar a magia."""
        return player.mana_atual >= self.custo_mana

    def executar_custo(self, player):
        """Deduz o custo de mana do jogador se ele puder usar."""
        if self.pode_usar(player):
            player.mana_atual -= self.custo_mana
            return True
        return False