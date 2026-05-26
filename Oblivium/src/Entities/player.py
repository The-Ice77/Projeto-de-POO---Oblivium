# player.py

from Entity import Entidade


class Player(Entidade):

    def __init__(self, nome, vida_maxima, velocidade, x, y, sprite, mana_maxima, dinheiro=0 ):

        # Herda atributos da classe pai
        super().__init__( nome, vida_maxima, velocidade, x, y, sprite )

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
            print(f"Mana restante: " f"{self.mana_atual}/{self.mana_maxima}")
        else:
            print("Mana insuficiente!")

    # Sistema de Memória

    def recuperar_memoria(self, quantidade):
        self.fragmentos_memoria += quantidade

        print(f"{self.nome} recuperou "f"{quantidade} fragmento(s) de memória!")
        print( f"Total de memórias: " f"{self.fragmentos_memoria}" )

    # Sistema de Dinheiro

    def ganhar_dinheiro(self, quantidade):
        self.dinheiro += quantidade
        print(f"{self.nome} recebeu "f"{quantidade} moedas.")

    def gastar_dinheiro(self, quantidade):
        if self.dinheiro >= quantidade:
            self.dinheiro -= quantidade
            print(f"{self.nome} gastou "f"{quantidade} moedas.")
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
        print(f"{self.nome} desmaiou e retornará "f"ao último checkpoint.")

    # Status

    def mostrar_status(self):

        print("< --- PLAYER --- >")

        print(f"Nome: {self.nome}")
        print(f"Vida: "f"{self.vida_atual}/{self.vida_maxima}")
        print(f"Mana: "f"{self.mana_atual}/{self.mana_maxima}")
        print(f"Fragmentos de Memórias: {self.fragmentos_memoria}")
        print(f"Dinheiro: {self.dinheiro}")
        print(f"Posição: ({self.x}, {self.y})")