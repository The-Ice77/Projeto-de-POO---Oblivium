# enemy.py

from Entity import Entidade


class Enemy(Entidade):

    def __init__(self, nome, vida_maxima, velocidade, x, y, sprite, dano, agressivo ):

       # Herda atributos da classe pai
       super().__init__( nome, vida_maxima, velocidade, x, y, sprite )

       # Atributos exclusivos do inimigo
       self.dano = dano
       self.agressivo = agressivo

       # Estado do inimigo
       self.alvo_detectado = False

    # Sistema de Combate

    def atacar(self, alvo):
        if not self.vivo:
            print(f"{self.nome} não pode atacar.")
            return
        print(f"{self.nome} atacou " f"{alvo.nome}!")
        alvo.receber_dano(self.dano)

    # Sistema de Patrulha

    def patrulhar(self):
        print(f"{self.nome} está patrulhando a área.")
    def detectar_alvo(self, alvo):
        self.alvo_detectado = True
        print(f"{self.nome} detectou "f"{alvo.nome}!")

    def perseguir(self, alvo):
        if not self.alvo_detectado:
            print(f"{self.nome} ainda não encontrou "f"nenhum alvo.")
            return
        print(f"{self.nome} está perseguindo "f"{alvo.nome}!")

    # IA Simples

    def agir(self, alvo):
        if not self.vivo:
            return
        if self.agressivo:
            self.detectar_alvo(alvo)
            self.perseguir(alvo)
            self.atacar(alvo)
        else:
            self.patrulhar()

    # Sobrescrita

    def morrer(self):
        self.vivo = False
        print(f"{self.nome} foi derrotado!")

    # Status

    def mostrar_status(self):

        print("<-- ENEMY -->")
        print(f"Nome: {self.nome}")
        print(f"Vida: "f"{self.vida_atual}/{self.vida_maxima}")
        print(f"Dano: {self.dano}")
        print(f"Agressivo: {self.agressivo}")
        print(f"Posição: ({self.x}, {self.y})")