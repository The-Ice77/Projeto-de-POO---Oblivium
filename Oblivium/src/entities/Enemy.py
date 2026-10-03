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
from src.utils.resource_manager import ResourceManager

class Enemy(Entidade):
    def __init__(self, nome, vida_maxima, velocidade, x, y, sprite=None, dano=10, agressivo=True, atributos=None, recompensas=None, mana_maxima=None, pasta_sprites=None):
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

        # Configurações visuais e de animação
        self.pasta_sprites = pasta_sprites
        self.flutuante = False
        self.escala_combate = 0.85
        self.virado_direita = True

        # Inferencia inteligente de sprites se não fornecido
        if not self.pasta_sprites:
            nome_low = self.nome.lower()
            if any(k in nome_low for k in ["superior", "demonio_superior", "gulosao", "gulosão", "anomalia", "boss", "guardiao", "guardião"]):
                self.pasta_sprites = "demonio_superior"
            elif any(k in nome_low for k in ["banco", "espectro", "olho", "observador"]):
                self.pasta_sprites = "banco"
            else:
                self.pasta_sprites = "demonio_inferior"

        # Dimensões da Hitbox Física 2.5D e carregamento de artes
        if self.pasta_sprites:
            self.carregar_sprites(self.pasta_sprites)
        else:
            self.largura = 36
            self.altura = 36
            self.cor = (150, 30, 50)

    def carregar_sprites(self, pasta_sprites):
        """Carrega o pacote completo de animações do inimigo a partir do ResourceManager."""
        self.pasta_sprites = pasta_sprites
        pasta_low = pasta_sprites.lower()

        if "superior" in pasta_low or "gulosao" in pasta_low:
            escala = 0.70
            self.largura = 55
            self.altura = 50
            self.flutuante = False
            self.escala_combate = 1.05
            self.cor = (150, 0, 200)
        elif "banco" in pasta_low:
            escala = 0.55
            self.largura = 36
            self.altura = 36
            self.flutuante = True
            self.escala_combate = 0.85
            self.cor = (50, 80, 140)
        else: # demonio_inferior / padrão
            escala = 0.55
            self.largura = 36
            self.altura = 36
            self.flutuante = False
            self.escala_combate = 0.85
            self.cor = (80, 30, 110)

        self.animacoes = ResourceManager.carregar_animacoes_inimigo(pasta_sprites, escala_fator=escala)
        if "idle" in self.animacoes:
            self.estado_atual = "idle"
            self.imagem_atual = self.animacoes["idle"].get_imagem()

    def mover(self, dx, dy, hitboxes_mapa=None):
        """Move o inimigo atualizando a animação de caminhar e a orientação do olhar."""
        super().mover(dx, dy, hitboxes_mapa)

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

        self.mover(vetor_x, vetor_y, [])

    # --- SISTEMA DE RENDERIZAÇÃO ROBUSTO COM ANCORAGEM 2.5D ---
    def desenhar(self, tela):
        if not getattr(self, 'vivo', True):
            return
            
        if hasattr(self, 'atualizar_animacao'):
            self.atualizar_animacao()
            
        imagem = getattr(self, 'imagem_atual', None)
            
        if imagem:
            largura_img = imagem.get_width()
            altura_img = imagem.get_height()
            
            # Ancoragem bottom-center na base física dos pés
            offset_x = (largura_img - getattr(self, 'largura', 40)) / 2
            offset_y = altura_img - getattr(self, 'altura', 40)
            offset_flutuante = -12 if getattr(self, 'flutuante', False) else 0

            tela.blit(imagem, (int(self.x - offset_x), int(self.y - offset_y + offset_flutuante)))
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