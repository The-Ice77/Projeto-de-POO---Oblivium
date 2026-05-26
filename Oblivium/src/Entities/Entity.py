class Entidade:
    # Atributos mais simples
    def __init__(self, nome, vida_maxima, x, y, velocidade, sprite):
        self.nome = nome
        self.vida_maxima = vida_maxima
        self.vida_atual = vida_maxima
        self.x = x
        self.y = y
        self.velocidade = velocidade
        self.sprite = sprite
        self.vivo = True
    
    # movimentação
    def mover(self, dx, dy):
        self.x += dx*self.velocidade
        self.y += dy*self.velocidade
    
    # sistema de dano
    def receber_dano(self, dano):
        if not self.vivo:
            print(f"{self.nome} já está morto")
            return
        
        self.vida_atual -= dano

        if self.vida < 0:
            self.vida = 0
            self.vivo = False
            self.morrer()
    
    # sistema de cura
    def curar(self, cura):
        if not self.vivo:
            print(f'{self.nome} não pode receber cura')
            return
        if self.vida_atual > self.vida_maxima:
            self.vida_atual = self.vida_maxima

            print(f'{self.nome} recuperou {cura} de vida')
    
    # sistema de morte

    def morrer(self):
        print(f'{self.nome} foi derrotado!')

    def mostrar_status(self):
        print("<-- Status -->")
        print(f"Nome: {self.nome}")
        print(f"Vida: {self.vida_atual}/{self.vida_maxima}")
        print(f"Posição: ({self.x},{self.y})")
        print(f"Velocidade: {self.velocidade}")
        print(f'Estado: {self.vivo} ')

        
