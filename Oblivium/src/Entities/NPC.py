class NPC():
    def __init__(self, nome, x, y, sprite, vivo):
        self.nome = nome
        self.x = x
        self.y = y
        self.vivo = True

    def mover(self, dx, dy):
        self.x += dx*self.velocidade
        self.y += dy*self.velocidade
