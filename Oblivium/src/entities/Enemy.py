# src/entities/Enemy.py
import pygame
import random

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

        # Suporte a inimigos Mímicos (disfarce de corpo de soldado no overworld e revelação em combate)
        self.eh_mimico = "mimico" in str(self.pasta_sprites or "").lower()
        self.disfarcado = self.eh_mimico
        self.revelado = not self.eh_mimico
        self.revelando = False
        self.tempo_reveal = 0.0

        # Inferencia inteligente de sprites se não fornecido
        if not self.pasta_sprites:
            nome_low = self.nome.lower()
            if "mimico" in nome_low:
                self.pasta_sprites = "mimico"
                self.eh_mimico = True
                self.disfarcado = True
                self.revelado = False
            elif any(k in nome_low for k in ["superior", "demonio_superior", "gulosao", "gulosão", "anomalia", "boss", "guardiao", "guardião"]):
                self.pasta_sprites = "demonio_superior"
            elif any(k in nome_low for k in ["demonio_olho", "olho", "observador"]):
                self.pasta_sprites = "demonio_olho"
            elif any(k in nome_low for k in ["pequeno", "demonio_pequeno"]):
                self.pasta_sprites = "demonio_pequeno"
            elif any(k in nome_low for k in ["banco", "espectro"]):
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
        tabela_arquetipos = [
            (("dragao",), 2.0, (220, 130), False, 1.03, 186, (195, 42, 36), False),
            (("superior", "gulosao", "grande"), 0.70, (55, 50), False, 1.63, 140, (150, 0, 200), False),
            (("olho",), 0.65, (42, 42), True, 1.27, 80, (140, 30, 90), False),
            (("pequeno",), 0.60, (38, 38), False, 1.42, 94, (110, 25, 70), False),
            (("banco",), 0.55, (36, 36), True, 1.70, 92, (50, 80, 140), False),
            (("mimico",), 0.70, (46, 40), False, 1.57, 118, (145, 45, 55), True),
            (("orc",), 0.60, (44, 42), False, 1.50, 126, (90, 130, 70), False),
        ]
        escala, dims, flutuante, escala_combate, alt_combate, cor, eh_mimico = (
            0.55, (36, 36), False, 1.57, 94, (80, 30, 110), False
        )
        for chaves, esc, dm, flut, esc_c, alt_c, cor_arq, mim_flag in tabela_arquetipos:
            if any(k in pasta_low for k in chaves):
                escala, dims, flutuante, escala_combate, alt_combate, cor, eh_mimico = (
                    esc, dm, flut, esc_c, alt_c, cor_arq, mim_flag
                )
                break

        self.largura, self.altura = dims
        self.flutuante = flutuante
        self.escala_combate = escala_combate
        self.altura_combate_alvo = alt_combate
        self.cor = cor
        if eh_mimico:
            self.eh_mimico = True

        self.animacoes = ResourceManager.carregar_animacoes_inimigo(pasta_sprites, escala_fator=escala)
        if self.eh_mimico and getattr(self, "disfarcado", False) and "corpo" in self.animacoes:
            self.estado_atual = "corpo"
            self.imagem_atual = self.animacoes["corpo"].get_imagem()
        elif "idle" in self.animacoes:
            self.estado_atual = "idle"
            self.imagem_atual = self.animacoes["idle"].get_imagem()

    def iniciar_revelacao(self):
        """Inicia a sequência de revelação do Mímico, saindo da forma de cadáver e erguendo-se como monstro feroz."""
        if not getattr(self, 'eh_mimico', False) or getattr(self, 'revelado', False) or getattr(self, 'revelando', False):
            return
        self.disfarcado = False
        self.revelando = True
        self.mudar_estado("reveal")

    def finalizar_revelacao(self):
        """Conclui a revelação tornando o Mímico totalmente erguido na sua forma feroz (para combate)."""
        self.disfarcado = False
        self.revelando = False
        self.revelado = True
        self.mudar_estado("idle")

    def atualizar_animacao(self, dt=None):
        """Atualiza a animação corrente respeitando a transição de revelação do Mímico e morte."""
        if not getattr(self, 'vivo', True):
            if self.estado_atual not in ("dead", "morte", "morrer"):
                self.mudar_estado("dead")
            anim_m = self.animacoes.get(self.estado_atual)
            if anim_m and anim_m.frames:
                anim_m.atualizar(dt)
            self._sincronizar_imagem_atual()
            return

        if getattr(self, 'eh_mimico', False) and getattr(self, 'revelando', False):
            anim = self.animacoes.get("reveal")
            if anim and anim.frames:
                anim.atualizar(dt)
                self._sincronizar_imagem_atual()
                if getattr(anim, "concluida", False):
                    self.finalizar_revelacao()
            else:
                self.finalizar_revelacao()
            return

        super().atualizar_animacao(dt)

    def mudar_estado(self, novo_estado):
        # Se for um mímico já revelado (ex: em combate), impede regressão para forma de corpo de soldado
        if getattr(self, "eh_mimico", False) and getattr(self, "revelado", False) and novo_estado in ("corpo", "soldado"):
            novo_estado = "idle"
        super().mudar_estado(novo_estado)

    def mover(self, dx, dy, hitboxes_mapa=None):
        """Move o inimigo atualizando a animação de caminhar e a orientação do olhar."""
        super().mover(dx, dy, hitboxes_mapa)

    # --- SISTEMA DE MOVIMENTO NO MAPA (Pré-Combate) ---
    def atualizar_movimento_mapa(self, alvo_x, alvo_y, lista_inimigos=None):
        if not getattr(self, 'vivo', True) or not getattr(self, 'agressivo', True):
            return
        if getattr(self, 'eh_mimico', False) and (getattr(self, 'disfarcado', False) or getattr(self, 'revelando', False)):
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

        if hasattr(self, '_sincronizar_imagem_atual'):
            self._sincronizar_imagem_atual()
            
        imagem = getattr(self, 'imagem_atual', None)
            
        if imagem:
            largura_img = imagem.get_width()
            altura_img = imagem.get_height()
            
            # Ancoragem bottom-center na base física dos pés
            offset_x = (largura_img - getattr(self, 'largura', 40)) / 2
            offset_y = altura_img - getattr(self, 'altura', 40)
            offset_flutuante = -12 if getattr(self, 'flutuante', False) else 0

            # Sombra e calor residual imponente sob o corpo colossal do dragão
            if "dragao" in getattr(self, 'pasta_sprites', '').lower():
                sombra_dragao = pygame.Surface((250, 42), pygame.SRCALPHA)
                pygame.draw.ellipse(sombra_dragao, (12, 6, 6, 120), (0, 0, 250, 42))
                pygame.draw.ellipse(sombra_dragao, (215, 45, 15, 45), (20, 6, 210, 30))
                tela.blit(sombra_dragao, (int(self.x + getattr(self, 'largura', 180) // 2 - 125), int(self.y + getattr(self, 'altura', 110) - 16)))

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
        attrs = self.obter_atributos_efetivos() if hasattr(self, "obter_atributos_efetivos") else self.atributos
        mod = max(0, attrs.mod_for)
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