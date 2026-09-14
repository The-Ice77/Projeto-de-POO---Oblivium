# src/entities/Enemy.py
import pygame
import random
import os
import sys

# Garante que a pasta raiz do projeto ('Oblivium') esteja no sys.path
_raiz_projeto = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _raiz_projeto not in sys.path:
    sys.path.insert(0, _raiz_projeto)

from src.entities.Entity import Entidade 
from src.mechanics.attributes import Atributos

class Enemy(Entidade):
    def __init__(self, nome, vida_maxima, velocidade, x, y, sprite=None, dano=10, agressivo=True, atributos=None, recompensas=None, mana_maxima=None):
        if atributos is None:
            atributos = Atributos(
                forca=10,
                destreza=10,
                constituicao=10,
                intelecto=8,
                sabedoria=8,
                presenca=8
            )
            
        super().__init__(nome, vida_maxima, x, y, velocidade, atributos=atributos, mana_maxima=mana_maxima)

        # Atributos exclusivos do inimigo
        self.dano = dano
        self.agressivo = agressivo
        self.alvo_detectado = False
        
        # Habilidades disponíveis para o inimigo
        self.habilidades = ["ataque_basico"]
        
        # Recompensas ao ser derrotado
        recompensas_padrao = {"moedas": 10, "memorias": 0, "xp": 15}
        self.recompensas = recompensas if recompensas is not None else recompensas_padrao

        # --- ATRIBUTOS DE RENDERIZAÇÃO (FALLBACK) ---
        if "Anomalia" in self.nome:
            self.largura = 55
            self.altura = 75
            self.cor = (150, 0, 200) 
        else:
            self.largura = 35
            self.altura = 45
            self.cor = (150, 30, 50) 

    # --- SISTEMA DE MOVIMENTO NO MAPA (Pré-Combate) ---
    def atualizar_movimento_mapa(self, alvo_x, alvo_y, lista_inimigos=None):
        if not getattr(self, 'vivo', True) or not getattr(self, 'agressivo', True):
            return

        dx_alvo = alvo_x - self.x
        dy_alvo = alvo_y - self.y
        distancia_alvo = (dx_alvo**2 + dy_alvo**2) ** 0.5
        
        if distancia_alvo < 500: 
            self.alvo_detectado = True
        
        vetor_x, vetor_y = 0, 0
        if getattr(self, 'alvo_detectado', False) and distancia_alvo > 0:
            vetor_x = (dx_alvo / distancia_alvo) * self.velocidade
            vetor_y = (dy_alvo / distancia_alvo) * self.velocidade

        if lista_inimigos:
            distancia_minima = 70 
            for outro in lista_inimigos:
                if outro is not self: 
                    dx_outro = self.x - outro.x
                    dy_outro = self.y - outro.y
                    dist_outro = (dx_outro**2 + dy_outro**2) ** 0.5
                    
                    if dist_outro < distancia_minima and dist_outro > 0:
                        fator_repulsao = (distancia_minima - dist_outro) / distancia_minima
                        vetor_x += (dx_outro / dist_outro) * (self.velocidade * fator_repulsao * 2)
                        vetor_y += (dy_outro / dist_outro) * (self.velocidade * fator_repulsao * 2)

        tamanho_vetor = (vetor_x**2 + vetor_y**2) ** 0.5
        if tamanho_vetor > 0:
            vetor_x = (vetor_x / tamanho_vetor) * self.velocidade
            vetor_y = (vetor_y / tamanho_vetor) * self.velocidade

        if hasattr(self, 'mover'):
            self.mover(vetor_x, vetor_y, [])
        else:
            self.x += vetor_x
            self.y += vetor_y

    # --- SISTEMA DE RENDERIZAÇÃO ROBUSTO ---
    def desenhar(self, tela):
        if not getattr(self, 'vivo', True):
            return
            
        if hasattr(self, 'atualizar_animacao'):
            self.atualizar_animacao()
            
        imagem = getattr(self, 'imagem_atual', None)
            
        if imagem:
            tela.blit(imagem, (int(self.x), int(self.y)))
        else:
            # Fallback limpo
            largura_segura = getattr(self, 'largura', 40)
            altura_segura = getattr(self, 'altura', 40)
            cor_segura = getattr(self, 'cor', (150, 30, 50))
            
            retangulo = pygame.Rect(int(self.x), int(self.y), largura_segura, altura_segura)
            pygame.draw.rect(tela, cor_segura, retangulo)
            pygame.draw.rect(tela, (50, 0, 0), retangulo, 2)

    # --- SISTEMA DE COMBATE LÓGICO ---
    def calcular_dano_base(self):
        """Calcula o dano bruto baseado no dano base + modificador de força/destreza."""
        variacao = random.randint(-1, 2)
        mod = max(0, self.atributos.mod_for)
        return max(1, self.dano + mod + variacao)

    def atacar(self, alvo):
        """Ataca o alvo aplicando dano mitigado pela defesa do alvo."""
        if not getattr(self, 'vivo', True):
            return 0
        dano_bruto = self.calcular_dano_base()
        dano_sofrido = alvo.aplicar_dano(dano_bruto, tipo="fisico")
        return dano_sofrido

    def mostrar_status(self):
        print("<-- ENEMY -->")
        print(f"Nome: {getattr(self, 'nome', 'Desconhecido')}")
        print(f"Vida: {self.vida_atual}/{self.vida_maxima}")
        print(f"Dano: {getattr(self, 'dano', 0)}")
        print(f"Atributos: {self.atributos}")
        print(f"Posição: ({self.x}, {self.y})")