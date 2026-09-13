# src/entities/Boss.py
import pygame
from src.entities.Enemy import Enemy
from src.mechanics.attributes import Atributos

class Boss(Enemy):
    """
    Classe para Chefes e Mini-Chefes.
    Herda de Enemy com atributos aprimorados, múltiplas fases e habilidades de chefe.
    """
    def __init__(self, nome, vida_maxima, velocidade, x, y, sprite=None, dano=20, atributos=None, recompensas=None):
        if atributos is None:
            atributos = Atributos(
                forca=14,
                destreza=11,
                constituicao=16,
                intelecto=14,
                sabedoria=12,
                presenca=16
            )
            
        if recompensas is None:
            recompensas = {"moedas": 50, "memorias": 1, "xp": 100}

        super().__init__(nome, vida_maxima, velocidade, x, y, sprite=sprite, dano=dano, agressivo=True, atributos=atributos, recompensas=recompensas)
        
        self.largura = 65
        self.altura = 85
        self.cor = (120, 20, 180)
        self.fase = 1
        self.enfurecido = False

    def verificar_mudanca_fase(self):
        """Ativa modo enfurecido quando a vida cai abaixo de 40%."""
        if self.vida_atual <= (self.vida_maxima * 0.4) and not self.enfurecido:
            self.enfurecido = True
            self.fase = 2
            self.dano = int(self.dano * 1.3)
            print(f"[BOSS] {self.nome} entrou na Fase 2 (Enfurecido)!")
            return True
        return False