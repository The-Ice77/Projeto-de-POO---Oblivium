# src/entities/player.py
from src.entities.Entity import Entidade

class Player(Entidade):
    def __init__(self, nome, vida_maxima, x, y, velocidade, mana_maxima, dinheiro=0):
        
        # Herda atributos da classe pai (sem o sprite obsoleto)
        super().__init__(nome, vida_maxima, x, y, velocidade)

        # Atributos exclusivos do jogador
        self.mana_maxima = mana_maxima
        self.mana_atual = mana_maxima
        self.fragmentos_memoria = 0
        self.dinheiro = dinheiro

        # Estado do jogador
        self.em_combate = False

    # Sistema de Magia
    def usar_magia(self, custo_mana):
        if not self.vivo:
            print(f"{self.nome} não pode usar magia.")
            return

        if self.mana_atual >= custo_mana:
            self.mana_atual -= custo_mana
            print(f"{self.nome} usou magia!")
            print(f"Mana restante: {self.mana_atual}/{self.mana_maxima}")
        else:
            print("Mana insuficiente!")

    # Sistema de Memória
    def recuperar_memoria(self, quantidade):
        self.fragmentos_memoria += quantidade
        print(f"{self.nome} recuperou {quantidade} fragmento(s) de memória!")
        print(f"Total de memórias: {self.fragmentos_memoria}")

    # Sistema de Dinheiro
    def ganhar_dinheiro(self, quantidade):
        self.dinheiro += quantidade
        print(f"{self.nome} recebeu {quantidade} moedas.")

    def gastar_dinheiro(self, quantidade):
        if self.dinheiro >= quantidade:
            self.dinheiro -= quantidade
            print(f"{self.nome} gastou {quantidade} moedas.")
        else:
            print("Dinheiro insuficiente!")

    # Combate
    def entrar_combate(self):
        self.em_combate = True
        print(f"{self.nome} entrou em combate!")

    def sair_combate(self):
        self.em_combate = False
        print(f"{self.nome} saiu do combate!")

    # Sobrescrita
    def morrer(self):
        self.vivo = False
        print(f"{self.nome} desmaiou e retornará ao último checkpoint.")

    # Status
    def mostrar_status(self):
        print("< --- PLAYER --- >")
        print(f"Nome: {self.nome}")
        print(f"Vida: {self.vida_atual}/{self.vida_maxima}")
        print(f"Mana: {self.mana_atual}/{self.mana_maxima}")
        print(f"Fragmentos de Memórias: {self.fragmentos_memoria}")
        print(f"Dinheiro: {self.dinheiro}")
        print(f"Posição: ({int(self.x)}, {int(self.y)})")