# src/entities/Entity.py
import pygame
import math
import os
import sys

# Garante que a pasta raiz do projeto ('Oblivium') esteja no sys.path
_raiz_projeto = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _raiz_projeto not in sys.path:
    sys.path.insert(0, _raiz_projeto)

from src.utils.resource_manager import Animacao
from src.mechanics.attributes import Atributos

class Entidade:
    def __init__(self, nome, vida_maxima, x, y, velocidade, atributos=None, mana_maxima=None):
        self.nome = nome
        self.atributos = atributos if atributos is not None else Atributos()
        self.vida_maxima = vida_maxima
        self.vida_atual = vida_maxima
        
        # Sistema de Mana baseada em Atributos ou valor explícito
        if mana_maxima is not None:
            self.mana_maxima = mana_maxima
        else:
            self.mana_maxima = self.atributos.calcular_mana_maxima(mana_base=20)
        self.mana_atual = self.mana_maxima

        self.x = float(x)
        self.y = float(y)
        self.velocidade = velocidade
        self.vivo = True
        
        # Estado de combate e efeitos
        self.defendendo = False
        self.vulneravel = False
        self.focado = False
        self.condicoes = [] # Lista de instâncias de Condicao ativas
        
        self.largura = 40
        self.altura = 40
        
        # ==========================================
        # SISTEMA DE ANIMAÇÃO E SPRITES
        # ==========================================
        # Dicionário que guarda objetos da classe Animacao por estado
        self.animacoes = {
            "idle": Animacao([]),
            "andar": Animacao([]),
            "atacar": Animacao([], loop=False),
            "morrer": Animacao([], loop=False)
        }
        
        self.estado_atual = "idle"
        self.virado_direita = True       # Controla o flip horizontal da imagem
        
        # Imagem atual a ser renderizada
        self.imagem_atual = None

    def definir_animacao(self, estado, animacao):
        """
        Define ou sobrescreve a animação de um estado específico da Entidade.
        Ideal para injetar as artes após a criação da instância.
        """
        self.animacoes[estado] = animacao

    def aplicar_pacote_animacoes(self, pacote):
        """
        Recebe um dicionário onde a chave é o estado ("idle", "andar")
        e o valor é o objeto Animacao.
        """
        for estado, animacao in pacote.items():
            self.animacoes[estado] = animacao

    def atualizar_animacao(self):
        """Atualiza o frame atual da animação baseada no estado da entidade."""
        if not self.vivo and self.estado_atual != "morrer":
            self.mudar_estado("morrer")
            
        animacao = self.animacoes.get(self.estado_atual)
        
        if animacao and animacao.frames:
            animacao.atualizar()
            imagem_base = animacao.get_imagem()
            
            if imagem_base:
                # Espelha a imagem se estiver virado para a esquerda
                if not self.virado_direita:
                    self.imagem_atual = pygame.transform.flip(imagem_base, True, False)
                else:
                    self.imagem_atual = imagem_base
            else:
                self.imagem_atual = None
        else:
            self.imagem_atual = None

    def mudar_estado(self, novo_estado):
        """Altera o estado da animação e reseta o frame se o estado for novo."""
        if self.estado_atual != novo_estado:
            self.estado_atual = novo_estado
            if novo_estado in self.animacoes:
                self.animacoes[novo_estado].resetar()

    def mover(self, dx, dy, hitboxes_mapa=None):
        if hitboxes_mapa is None:
            hitboxes_mapa = []
            
        if not self.vivo or (dx == 0 and dy == 0):
            self.mudar_estado("idle")
            return
            
        self.mudar_estado("andar")
        
        # Define para onde a entidade está a olhar
        if dx > 0:
            self.virado_direita = True
        elif dx < 0:
            self.virado_direita = False
            
        tamanho = math.hypot(dx, dy)
        dx = dx / tamanho
        dy = dy / tamanho
        
        self.x += dx * self.velocidade
        rect_teste_x = pygame.Rect(int(self.x), int(self.y), self.largura, self.altura)
        
        for parede in hitboxes_mapa:
            if rect_teste_x.colliderect(parede):
                if dx > 0: self.x = parede.left - self.largura
                elif dx < 0: self.x = parede.right

        self.y += dy * self.velocidade
        rect_teste_y = pygame.Rect(int(self.x), int(self.y), self.largura, self.altura)
        
        for parede in hitboxes_mapa:
            if rect_teste_y.colliderect(parede):
                if dy > 0: self.y = parede.top - self.altura
                elif dy < 0: self.y = parede.bottom

    def desenhar(self, tela):
        # Atualiza o frame antes de desenhar
        self.atualizar_animacao()
        
        if self.imagem_atual:
            largura_img = self.imagem_atual.get_width()
            altura_img = self.imagem_atual.get_height()
            
            # Centraliza horizontalmente e alinha a base da imagem com a base da hitbox
            offset_x = (largura_img - self.largura) / 2
            offset_y = altura_img - self.altura
            
            tela.blit(self.imagem_atual, (int(self.x - offset_x), int(self.y - offset_y)))
        else:
            # Fallback limpo (Apenas o quadrado colorido)
            cor = (34, 139, 34) if self.vivo else (100, 100, 100)
            pygame.draw.rect(tela, cor, (int(self.x), int(self.y), self.largura, self.altura))

    # (Mantenha os métodos receber_dano, curar e mostrar_status iguais)
    def receber_dano(self, dano):
        if not self.vivo: return
        self.vida_atual = max(0, round(self.vida_atual - dano, 1))
        if self.vida_atual <= 0:
            self.vida_atual = 0
            self.vivo = False
            self.morrer()
            
    def esta_vivo(self):
        """Retorna se a entidade está viva e com pontos de vida."""
        return self.vivo and self.vida_atual > 0

    def curar(self, cura):
        if not self.vivo: return
        self.vida_atual = min(self.vida_maxima, round(self.vida_atual + cura, 1))

    def recuperar_mana(self, quantidade):
        """Recupera mana sem ultrapassar o limite máximo."""
        if not self.vivo: return
        self.mana_atual = min(self.mana_maxima, round(self.mana_atual + quantidade, 1))

    def gastar_mana(self, custo):
        """Deduz mana se houver o suficiente. Retorna True se sucesso, False se insuficiente."""
        if self.mana_atual >= custo:
            self.mana_atual = round(self.mana_atual - custo, 1)
            return True
        return False

    def restaurar_total(self):
        """Restaura completamente a vida, a mana e remove todas as condições ativas."""
        self.vida_atual = self.vida_maxima
        self.mana_atual = self.mana_maxima
        self.vivo = True
        self.defendendo = False
        self.vulneravel = False
        self.focado = False
        self.condicoes.clear()
        
    def aplicar_dano(self, dano_bruto, tipo="fisico"):
        """
        Aplica dano considerando a defesa da entidade, postura defensiva e estado vulnerável.
        Retorna o valor do dano final efetivamente sofrido.
        """
        if not self.vivo:
            return 0
            
        defesa = self.atributos.calcular_defesa_fisica() if tipo == "fisico" else self.atributos.calcular_defesa_magica()
        
        # Se estiver em postura defensiva, defesa amplificada e reduz dano recebido pela metade
        if self.defendendo:
            defesa = int(defesa * 2.2) + 4
            dano_calculado = max(1, dano_bruto - defesa)
            dano_final = max(1, int(dano_calculado * 0.55))
        else:
            dano_calculado = max(1, dano_bruto - defesa)
            dano_final = dano_calculado
            
        # Se estiver vulnerável (após Concentrar), sofre +35% de dano amplificado
        if getattr(self, 'vulneravel', False):
            dano_final = int(dano_final * 1.35) + 2
            
        self.receber_dano(dano_final)
        return dano_final

    def calcular_iniciativa(self):
        """Retorna a iniciativa para definir ordem de turnos."""
        return self.atributos.calcular_iniciativa()

    def adicionar_condicao(self, condicao):
        """Aplica ou renova uma condição de estado na entidade."""
        for c in self.condicoes:
            if c.id_condicao == condicao.id_condicao:
                c.duracao = max(c.duracao, condicao.duracao)
                c.intensidade = max(c.intensidade, condicao.intensidade)
                return
        self.condicoes.append(condicao)

    def remover_condicao(self, id_condicao):
        """Remove uma condição específica da entidade."""
        self.condicoes = [c for c in self.condicoes if c.id_condicao != id_condicao]

    def processar_condicoes_inicio_turno(self):
        """
        Processa todas as condições ativas no início do turno da entidade.
        Retorna lista de relatórios de efeitos ocorridos e flag se a ação foi impedida.
        """
        relatorios = []
        impede_acao = False

        for cond in self.condicoes[:]:
            if not self.vivo:
                break
            res = cond.processar_inicio_turno(self)
            if res:
                relatorios.append(res)
                if res.get("impede_acao", False):
                    impede_acao = True
            
            if cond.expirou() and cond in self.condicoes:
                self.condicoes.remove(cond)

        return relatorios, impede_acao

    @property
    def esta_atordoado(self):
        """Retorna se a entidade está sob algum efeito incapacitante."""
        return any(c.tipo == "CC" for c in self.condicoes)

    def resetar_turno_combate(self):
        """Reseta posturas temporárias do turno anterior."""
        self.defendendo = False
        self.vulneravel = False
        self.focado = False

    def restaurar_total(self):
        """Restaura vida e mana para os valores máximos, limpa estados e reanima a entidade."""
        self.vida_atual = self.vida_maxima
        self.mana_atual = self.mana_maxima
        self.vivo = True
        self.condicoes.clear()
        self.defendendo = False
        self.vulneravel = False
        self.focado = False
        self.mudar_estado("idle")

    def morrer(self):
        self.vivo = False
        self.condicoes.clear()
        self.mudar_estado("morrer")