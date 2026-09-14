# src/entities/Boss.py
import pygame
import os
import sys

# Garante que a pasta raiz do projeto ('Oblivium') esteja no sys.path
_raiz_projeto = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _raiz_projeto not in sys.path:
    sys.path.insert(0, _raiz_projeto)

from src.entities.Enemy import Enemy
from src.mechanics.attributes import Atributos

class Boss(Enemy):
    """
    Classe para Chefes e Mini-Chefes.
    Herda de Enemy com atributos aprimorados, múltiplas fases e habilidades de chefe.
    """
    def __init__(self, nome, vida_maxima, velocidade, x, y, sprite=None, dano=20, atributos=None, recompensas=None, mana_maxima=None):
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

        super().__init__(nome, vida_maxima, velocidade, x, y, sprite=sprite, dano=dano, agressivo=True, atributos=atributos, recompensas=recompensas, mana_maxima=mana_maxima)
        
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