# src/entities/Entity.py
import pygame
import math

from abc import ABC
from src.utils.resource_manager import Animacao
from src.mechanics.attributes import Atributos

class Entidade(ABC):
    """
    Classe base abstrata para todas as entidades vivas e interativas do mundo de Oblivium
    (Player/Halia, Inimigos comuns, Chefes e NPCs).
    Centraliza atributos, cálculo de mana/vida, condições e manipulação de sprites.
    """
    _TURNOS_IMUNIDADE_CC = 1

    def __init__(self, nome, vida_maxima, x, y, velocidade, atributos=None, mana_maxima=None):
        self.nome = nome
        self.atributos = atributos if atributos is not None else Atributos()
        self.vida_maxima = vida_maxima
        self._vida_atual = float(vida_maxima)
        
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
        self.imunidade_cc_turnos = 0
        
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
        self.direcao = "baixo"           # Direção atual: "baixo", "cima", "direita", "esquerda"
        self.virado_direita = True       # Controla a direção em que a entidade está voltada
        self.sprite_base_olha_direita = True # True se o sprite original olha para a direita, False se olha para a esquerda
        
        # Imagem atual a ser renderizada
        self.imagem_atual = None

    @property
    def vida_atual(self):
        return self._vida_atual

    @vida_atual.setter
    def vida_atual(self, valor):
        try:
            val = round(float(valor), 1)
        except (ValueError, TypeError):
            val = 0.0
        if val <= 0.0:
            self._vida_atual = 0.0
            if getattr(self, 'vivo', True):
                self.vivo = False
                self.morrer()
        else:
            self._vida_atual = min(float(self.vida_maxima), val)

    def definir_animacao(self, estado, animacao):
        """
        Define ou sobrescreve a animação de um estado específico da Entidade.
        Ideal para injetar as artes após a criação da instância.
        """
        self.animacoes[estado] = animacao

    def aplicar_pacote_animacoes(self, pacote):
        """
        Recebe um dicionário onde a chave é o estado ("idle", "andar", etc.)
        e o valor é o objeto Animacao.
        """
        for estado, animacao in pacote.items():
            self.animacoes[estado] = animacao

    def _tem_animacao_valida(self, chave):
        anim = self.animacoes.get(chave)
        return bool(anim and getattr(anim, "frames", None))

    def _sincronizar_imagem_atual(self):
        """Sincroniza `imagem_atual` a partir do quadro corrente sem avançar o cursor."""
        animacao = self.animacoes.get(self.estado_atual)
        if animacao and animacao.frames:
            imagem_base = animacao.get_imagem()
            if imagem_base:
                tem_direcao_explicita = any(
                    self.estado_atual.endswith(suf)
                    for suf in ("_baixo", "_cima", "_direita", "_esquerda")
                )
                if not tem_direcao_explicita:
                    precisa_espelhar = (self.virado_direita != getattr(self, 'sprite_base_olha_direita', True))
                    if precisa_espelhar:
                        self.imagem_atual = pygame.transform.flip(imagem_base, True, False)
                    else:
                        self.imagem_atual = imagem_base
                else:
                    self.imagem_atual = imagem_base
                return
        self.imagem_atual = None

    def atualizar_animacao(self, dt=None):
        """Atualiza o frame atual da animação baseada no estado da entidade."""
        if not self.vivo and self.estado_atual not in ["morrer", "dead", "morte"]:
            self.mudar_estado("morrer")

        animacao = self.animacoes.get(self.estado_atual)
        if animacao and animacao.frames:
            animacao.atualizar(dt)
        self._sincronizar_imagem_atual()

    def mudar_estado(self, novo_estado):
        """Altera o estado da animação e reseta o frame se o estado for novo."""
        # Suporte inteligente a mapeamento quadridirecional se disponível
        if novo_estado == "idle" and self._tem_animacao_valida(f"idle_{self.direcao}"):
            novo_estado = f"idle_{self.direcao}"
        elif novo_estado in ["andar", "walk"] and self._tem_animacao_valida(f"andar_{self.direcao}"):
            novo_estado = f"andar_{self.direcao}"
        elif novo_estado in ["andar", "walk"] and self._tem_animacao_valida(f"walk_{self.direcao}"):
            novo_estado = f"walk_{self.direcao}"
        elif novo_estado.startswith("walk_") and not self._tem_animacao_valida(novo_estado):
            dir_sufixo = novo_estado[5:]
            for cand in (f"andar_{dir_sufixo}", "andar", "walk"):
                if self._tem_animacao_valida(cand):
                    novo_estado = cand
                    break
        elif novo_estado.startswith("andar_") and not self._tem_animacao_valida(novo_estado):
            dir_sufixo = novo_estado[6:]
            for cand in (f"walk_{dir_sufixo}", "andar", "walk"):
                if self._tem_animacao_valida(cand):
                    novo_estado = cand
                    break
        elif novo_estado == "walk" and self._tem_animacao_valida("andar") and not self._tem_animacao_valida("walk"):
            novo_estado = "andar"
        elif novo_estado == "andar" and not self._tem_animacao_valida("andar") and self._tem_animacao_valida("walk"):
            novo_estado = "walk"
        elif novo_estado in ["morrer", "dead", "morte"]:
            for cand in ["dead", "morte", "morrer"]:
                if self._tem_animacao_valida(cand):
                    novo_estado = cand
                    break

        if self.estado_atual != novo_estado:
            anim_atual = self.animacoes.get(self.estado_atual)
            anim_nova = self.animacoes.get(novo_estado)
            self.estado_atual = novo_estado
            # Se for a mesma animação subjacente (ex: alias andar/walk), preserva o frame
            if anim_nova and anim_nova is not anim_atual:
                anim_nova.resetar()
        self._sincronizar_imagem_atual()

    def definir_estado(self, novo_estado):
        """Alias para mudar_estado garantindo compatibilidade total em combate e animações."""
        self.mudar_estado(novo_estado)

    def mover(self, dx, dy, hitboxes_mapa=None):
        if hitboxes_mapa is None:
            hitboxes_mapa = []
            
        if not self.vivo or (dx == 0 and dy == 0):
            if self._tem_animacao_valida(f"idle_{self.direcao}"):
                self.mudar_estado(f"idle_{self.direcao}")
            else:
                self.mudar_estado("idle")
            return
            
        # Determina a direção predominante de movimento
        if abs(dx) >= abs(dy):
            self.direcao = "direita" if dx > 0 else "esquerda"
            self.virado_direita = (dx > 0)
        else:
            self.direcao = "baixo" if dy > 0 else "cima"

        if self._tem_animacao_valida(f"andar_{self.direcao}"):
            self.mudar_estado(f"andar_{self.direcao}")
        elif self._tem_animacao_valida("andar"):
            self.mudar_estado("andar")
        elif self._tem_animacao_valida("walk"):
            self.mudar_estado("walk")
        else:
            self.mudar_estado("andar")
            
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
        # Sincroniza o quadro atual sem avançar o cursor de animação
        self._sincronizar_imagem_atual()
        
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

    @staticmethod
    def normalizar_recurso(valor, casas=1):
        """Remove ruído binário de ponto flutuante e retorna int quando o valor é exato."""
        try:
            num = round(float(valor or 0.0), casas)
        except (TypeError, ValueError):
            return 0
        if abs(num) < (10 ** (-(casas + 1))):
            return 0
        return int(round(num)) if float(num).is_integer() else num

    def receber_dano(self, dano):
        if not self.vivo:
            return 0
        vida_antes = float(self._vida_atual)
        self.vida_atual = self._vida_atual - float(dano)
        return self.normalizar_recurso(max(0.0, vida_antes - float(self._vida_atual)))

    def esta_vivo(self):
        """Retorna se a entidade está viva e com pontos de vida."""
        return self.vivo and self._vida_atual > 0.0

    def curar(self, cura):
        if not self.vivo:
            return 0
        vida_antes = float(self._vida_atual)
        self.vida_atual = self._vida_atual + float(cura)
        return self.normalizar_recurso(max(0.0, float(self._vida_atual) - vida_antes))

    def recuperar_mana(self, quantidade):
        """Recupera mana sem ultrapassar o limite máximo e retorna o delta efetivo."""
        if not self.vivo:
            return 0
        mana_antes = float(self.mana_atual)
        nova_mana = min(float(self.mana_maxima), mana_antes + float(quantidade))
        self.mana_atual = self.normalizar_recurso(nova_mana)
        return self.normalizar_recurso(max(0.0, float(self.mana_atual) - mana_antes))

    def gastar_mana(self, custo):
        """Deduz mana se houver o suficiente. Retorna True se sucesso, False se insuficiente."""
        if self.mana_atual >= custo:
            self.mana_atual = self.normalizar_recurso(max(0.0, float(self.mana_atual) - float(custo)))
            return True
        return False

    def restaurar_total(self):
        """Restaura vida e mana para os valores máximos, limpa estados e reanima a entidade."""
        self.vivo = True
        self._vida_atual = float(self.vida_maxima)
        self.mana_atual = self.mana_maxima
        self.defendendo = False
        self.vulneravel = False
        self.focado = False
        self.condicoes.clear()
        self.imunidade_cc_turnos = 0
        self.mudar_estado("idle")
        
    def obter_atributos_efetivos(self):
        """Retorna os atributos efetivos da entidade para cálculos de combate e defesa."""
        return self.atributos

    def obter_defesa_equipamento(self, tipo="fisico"):
        """Retorna bônus fixo de defesa proveniente de equipamentos (0 para entidades sem inventário)."""
        return 0

    def aplicar_dano(self, dano_bruto, tipo="fisico"):
        """
        Aplica dano considerando a defesa da entidade, postura defensiva e estado vulnerável.
        Retorna o valor do dano final efetivamente sofrido.
        """
        if not self.vivo:
            return 0
            
        attrs = self.obter_atributos_efetivos() or self.atributos
        defesa_attr = attrs.calcular_defesa_fisica() if tipo == "fisico" else attrs.calcular_defesa_magica()
        defesa = defesa_attr + self.obter_defesa_equipamento(tipo)
        
        # Se estiver em postura defensiva, defesa amplificada e reduz dano recebido pela metade
        if self.defendendo:
            defesa = int(defesa * 2.2) + 4
            dano_calculado = max(1, dano_bruto - defesa)
            dano_final = max(1, int(dano_calculado * 0.55))
        else:
            dano_final = max(1, dano_bruto - defesa)
            
        # Se estiver vulnerável (após Concentrar), sofre +35% de dano amplificado
        if self.vulneravel:
            dano_final = int(dano_final * 1.35) + 2
            
        self.receber_dano(dano_final)
        return dano_final

    def calcular_iniciativa(self):
        """Retorna a iniciativa para definir ordem de turnos."""
        attrs = self.obter_atributos_efetivos() or self.atributos
        return attrs.calcular_iniciativa()

    def adicionar_condicao(self, condicao):
        """Aplica ou renova uma condição de estado na entidade (retorna False se bloqueada por anti-stunlock)."""
        if getattr(condicao, "tipo", "") == "CC":
            if getattr(self, "imunidade_cc_turnos", 0) > 0:
                return False
            if any(getattr(c, "tipo", "") == "CC" for c in self.condicoes):
                return False
        for c in self.condicoes:
            if c.id_condicao == condicao.id_condicao:
                c.duracao = max(c.duracao, condicao.duracao)
                c.intensidade = max(c.intensidade, condicao.intensidade)
                return True
        self.condicoes.append(condicao)
        return True

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

        if impede_acao:
            self.imunidade_cc_turnos = max(
                getattr(self, "imunidade_cc_turnos", 0),
                getattr(self, "_TURNOS_IMUNIDADE_CC", 1),
            )
        elif getattr(self, "imunidade_cc_turnos", 0) > 0:
            self.imunidade_cc_turnos -= 1

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

    def morrer(self):
        """Marca a entidade como morta, limpa condições ativas e transiciona para animação de morte."""
        self.vivo = False
        self.condicoes.clear()
        self.imunidade_cc_turnos = 0
        self.mudar_estado("morrer")