class Boss(entity, enemy):
    def __init__(self, nome, vida_maxima, x, y, velocidade, sprite):
        self.nome = nome
        self.vida_maxima = vida_maxima
        self.vida_atual = vida_maxima
        self.x = x
        self.y = y
        self.velocidade = velocidade
        self.sprite = sprite
        self.vivo = True