# src/mechanics/combat_effects.py
import pygame
import math
import random
from src.utils.resource_manager import ResourceManager

# =============================================================================
# PALETAS VISUAIS TEMÁTICAS POR ELEMENTO (PROJÉTEIS, BRILHOS E EXPLOSÕES)
# =============================================================================

CORES_ELEMENTOS = {
    "FOGO": {
        "primaria": (255, 125, 25),
        "nucleo": (255, 240, 110),
        "rastro": (230, 45, 15),
        "aura": (255, 110, 20, 130),
        "tint_explosao": (255, 150, 40),
        "pasta_explosao": "efeitos/explosao/explosao_1",
        "raio_projetil": 7.0,
        "som_impacto": "dano_inimigo"
    },
    "GELO": {
        "primaria": (110, 220, 255),
        "nucleo": (245, 250, 255),
        "rastro": (60, 140, 240),
        "aura": (100, 210, 255, 130),
        "tint_explosao": (120, 225, 255),
        "pasta_explosao": "efeitos/explosao/explosao_2",
        "raio_projetil": 6.5,
        "som_impacto": "dano_inimigo"
    },
    "ELETRICO": {
        "primaria": (95, 225, 255),
        "nucleo": (255, 255, 160),
        "rastro": (245, 250, 130),
        "aura": (90, 215, 255, 130),
        "tint_explosao": (140, 240, 255),
        "pasta_explosao": "efeitos/explosao/explosao_3",
        "raio_projetil": 6.0,
        "som_impacto": "dano_inimigo"
    },
    "VENTO": {
        "primaria": (75, 225, 150),
        "nucleo": (225, 255, 235),
        "rastro": (35, 180, 135),
        "aura": (70, 220, 145, 130),
        "tint_explosao": (110, 240, 175),
        "pasta_explosao": "efeitos/explosao/explosao_2",
        "raio_projetil": 6.5,
        "som_impacto": "dano_inimigo"
    },
    "SOMBRA": {
        "primaria": (180, 65, 240),
        "nucleo": (90, 20, 120),
        "rastro": (130, 25, 190),
        "aura": (170, 50, 230, 130),
        "tint_explosao": (195, 90, 255),
        "pasta_explosao": "efeitos/explosao/explosao_3",
        "raio_projetil": 7.0,
        "som_impacto": "dano_inimigo"
    },
    "TERRA": {
        "primaria": (185, 145, 60),
        "nucleo": (150, 220, 75),
        "rastro": (95, 65, 30),
        "aura": (180, 140, 50, 130),
        "tint_explosao": (190, 170, 90),
        "pasta_explosao": "efeitos/explosao/explosao_2",
        "raio_projetil": 6.5,
        "som_impacto": "dano_inimigo"
    },
    "ARCANO": {
        "primaria": (245, 215, 80),
        "nucleo": (255, 255, 255),
        "rastro": (150, 105, 255),
        "aura": (240, 205, 75, 130),
        "tint_explosao": (250, 225, 120),
        "pasta_explosao": "efeitos/explosao/explosao_1",
        "raio_projetil": 7.5,
        "som_impacto": "dano_inimigo"
    },
    "SAGRADO": {
        "primaria": (255, 235, 130),
        "nucleo": (255, 255, 255),
        "rastro": (255, 210, 80),
        "aura": (255, 230, 120, 130),
        "tint_explosao": (255, 245, 160),
        "pasta_explosao": "efeitos/explosao/explosao_3",
        "raio_projetil": 6.5,
        "som_impacto": "dano_inimigo"
    },
    "FISICO": {
        "primaria": (225, 230, 240),
        "nucleo": (255, 255, 255),
        "rastro": (165, 175, 190),
        "aura": (215, 220, 230, 100),
        "tint_explosao": (230, 235, 245),
        "pasta_explosao": "efeitos/explosao/explosao_2",
        "raio_projetil": 6.0,
        "som_impacto": "dano_inimigo"
    },
    "NEUTRO": {
        "primaria": (210, 215, 225),
        "nucleo": (255, 255, 255),
        "rastro": (150, 160, 175),
        "aura": (200, 205, 215, 100),
        "tint_explosao": (220, 225, 235),
        "pasta_explosao": "efeitos/explosao/explosao_2",
        "raio_projetil": 6.0,
        "som_impacto": "dano_inimigo"
    }
}


class ParticulaVisual:
    """Partícula leve e de alto desempenho para rastros, faíscas e estilhaços radiais."""
    __slots__ = ("x", "y", "vx", "vy", "vida", "vida_max", "cor", "raio", "desaceleracao", "gravidade")

    def __init__(self, x, y, vx, vy, vida, cor, raio, desaceleracao=0.93, gravidade=0.0):
        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)
        self.vy = float(vy)
        self.vida = float(vida)
        self.vida_max = float(vida)
        self.cor = cor
        self.raio = float(raio)
        self.desaceleracao = float(desaceleracao)
        self.gravidade = float(gravidade)

    def atualizar(self, dt=1.0):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vx *= self.desaceleracao
        self.vy *= self.desaceleracao
        self.vy += self.gravidade * dt
        self.vida -= dt
        return self.vida > 0

    def desenhar(self, superficie):
        if self.vida <= 0:
            return
        ratio = max(0.0, min(1.0, self.vida / self.vida_max))
        alpha = int(255 * ratio)
        raio_atual = max(1, int(self.raio * (0.4 + 0.6 * ratio)))
        diam = raio_atual * 2

        surf_p = pygame.Surface((diam, diam), pygame.SRCALPHA)
        pygame.draw.circle(surf_p, (*self.cor[:3], alpha), (raio_atual, raio_atual), raio_atual)
        superficie.blit(surf_p, (int(self.x - raio_atual), int(self.y - raio_atual)))


class ProjetilMagico:
    """
    Projétil mágico lançado em arco ou linha reta em direção a um alvo específico,
    emitindo rastros dinâmicos de luz e faíscas elementais.
    """
    def __init__(self, x_origem, y_origem, x_destino, y_destino, elemento="ARCANO",
                 velocidade=22.0, curva_offset=0.0, alvo=None, dados_dano=None,
                 on_impacto=None):
        self.origem_x = float(x_origem)
        self.origem_y = float(y_origem)
        self.destino_x = float(x_destino)
        self.destino_y = float(y_destino)
        self.x = self.origem_x
        self.y = self.origem_y
        
        self.elemento = elemento.upper() if elemento else "ARCANO"
        self.config = CORES_ELEMENTOS.get(self.elemento, CORES_ELEMENTOS["ARCANO"])
        self.alvo = alvo
        self.dados_dano = dados_dano or {}
        self.on_impacto = on_impacto

        self.dx = self.destino_x - self.origem_x
        self.dy = self.destino_y - self.origem_y
        self.distancia_total = math.hypot(self.dx, self.dy) or 1.0

        # Vetor normal perpendicular à trajetória para aplicação do arco de fanning
        self.nx = -self.dy / self.distancia_total
        self.ny = self.dx / self.distancia_total
        self.curva_amplitude = float(curva_offset)

        self.velocidade = float(velocidade)
        self.progresso = 0.0
        self.atingiu = False
        self.concluido = False

        self.rastro = []
        self.raio_base = self.config["raio_projetil"]

    def atualizar(self, dt=1.0):
        if self.concluido:
            # Continua atualizando as partículas restantes do rastro após o impacto
            self.rastro = [p for p in self.rastro if p.atualizar(dt)]
            return bool(self.rastro)

        # Avanço do progresso proporcional à velocidade
        passo = (self.velocidade * dt) / self.distancia_total
        self.progresso = min(1.0, self.progresso + passo)

        # Posição interpolada com curva senoidal suave fanning out
        base_x = self.origem_x + self.dx * self.progresso
        base_y = self.origem_y + self.dy * self.progresso
        arco = math.sin(self.progresso * math.pi) * self.curva_amplitude

        self.x = base_x + self.nx * arco
        self.y = base_y + self.ny * arco

        # Emissão de partículas de rastro brilhantes
        for _ in range(2):
            vx_p = random.uniform(-1.5, 1.5) - (self.dx / self.distancia_total) * 2.0
            vy_p = random.uniform(-1.5, 1.5) - (self.dy / self.distancia_total) * 2.0
            p = ParticulaVisual(
                x=self.x + random.uniform(-3, 3),
                y=self.y + random.uniform(-3, 3),
                vx=vx_p,
                vy=vy_p,
                vida=random.uniform(8.0, 15.0),
                cor=self.config["rastro"],
                raio=random.uniform(2.5, 5.0),
                desaceleracao=0.88
            )
            self.rastro.append(p)

        self.rastro = [p for p in self.rastro if p.atualizar(dt)]

        # Verificação de impacto no destino
        if self.progresso >= 1.0 or math.hypot(self.destino_x - self.x, self.destino_y - self.y) <= 16:
            self.atingiu = True
            self.concluido = True
            if self.on_impacto:
                self.on_impacto(self)

        return True

    def desenhar(self, tela):
        # 1. Rastro de cauda do projétil
        for p in self.rastro:
            p.desenhar(tela)

        if self.concluido:
            return

        cx = int(self.x)
        cy = int(self.y)

        # 2. Halo / Aura brilhante translúcida
        raio_aura = int(self.raio_base * 2.4)
        diam_aura = raio_aura * 2
        surf_aura = pygame.Surface((diam_aura, diam_aura), pygame.SRCALPHA)
        cor_aura = self.config["aura"]
        pygame.draw.circle(surf_aura, cor_aura, (raio_aura, raio_aura), raio_aura)
        tela.blit(surf_aura, (cx - raio_aura, cy - raio_aura))

        # 3. Corpo principal colorido
        raio_corpo = max(2, int(self.raio_base))
        pygame.draw.circle(tela, self.config["primaria"], (cx, cy), raio_corpo)

        # 4. Núcleo incandescente brilhante
        raio_nucleo = max(1, int(self.raio_base * 0.55))
        pygame.draw.circle(tela, self.config["nucleo"], (cx, cy), raio_nucleo)


class ExplosaoMagica:
    """
    Explosão elemental de impacto nos alvos atingidos:
    - Sequência animada de sprites de explosão de alta fidelidade
    - Tinting cromático de acordo com o elemento da magia
    - Onda de choque (shockwave) concêntrica em expansão rápida
    - Estilhaços e fagulhas radiais em 360 graus
    """
    def __init__(self, x, y, elemento="ARCANO", escala=1.15, frames=None):
        self.x = int(x)
        self.y = int(y)
        self.elemento = elemento.upper() if elemento else "ARCANO"
        self.config = CORES_ELEMENTOS.get(self.elemento, CORES_ELEMENTOS["ARCANO"])
        self.escala = escala
        
        self.frames = frames or []
        self.frame_atual = 0.0
        self.velocidade_anim = 1.25

        # Onda de Choque
        self.raio_choque = 6.0
        self.raio_choque_max = 62.0
        self.velocidade_choque = 4.2

        # Estilhaços / Centelhas Radiais em 360 graus
        self.particulas = []
        qtd_particulas = random.randint(18, 24)
        for _ in range(qtd_particulas):
            ang = random.uniform(0, math.pi * 2)
            spd = random.uniform(3.5, 9.5)
            cor = random.choice([self.config["primaria"], self.config["nucleo"], self.config["rastro"]])
            self.particulas.append(
                ParticulaVisual(
                    x=self.x,
                    y=self.y,
                    vx=math.cos(ang) * spd,
                    vy=math.sin(ang) * spd,
                    vida=random.uniform(14.0, 24.0),
                    cor=cor,
                    raio=random.uniform(2.5, 5.0),
                    desaceleracao=0.91,
                    gravidade=0.10
                )
            )

        self.concluida = False

    def atualizar(self, dt=1.0):
        self.frame_atual += self.velocidade_anim * dt
        self.raio_choque += self.velocidade_choque * dt
        self.particulas = [p for p in self.particulas if p.atualizar(dt)]

        anim_terminou = not self.frames or (int(self.frame_atual) >= len(self.frames))
        choque_terminou = self.raio_choque >= self.raio_choque_max
        particulas_terminaram = not self.particulas

        if anim_terminou and choque_terminou and particulas_terminaram:
            self.concluida = True
            return False
        return True

    def desenhar(self, tela):
        # 1. Onda de Choque (Shockwave ring)
        if self.raio_choque < self.raio_choque_max:
            ratio_c = max(0.0, min(1.0, 1.0 - (self.raio_choque / self.raio_choque_max)))
            alpha_c = int(220 * ratio_c)
            r_int = int(self.raio_choque)
            diam = r_int * 2
            surf_c = pygame.Surface((diam, diam), pygame.SRCALPHA)
            cor_choque = (*self.config["primaria"][:3], alpha_c)
            pygame.draw.circle(surf_c, cor_choque, (r_int, r_int), r_int, width=max(1, int(3 * ratio_c)))
            tela.blit(surf_c, (self.x - r_int, self.y - r_int))

        # 2. Frame Animado da Explosão
        if self.frames and int(self.frame_atual) < len(self.frames):
            frame = self.frames[int(self.frame_atual)]
            pos_x = self.x - (frame.get_width() // 2)
            pos_y = self.y - (frame.get_height() // 2)
            tela.blit(frame, (pos_x, pos_y))

        # 3. Estilhaços e Fagulhas Radiais
        for p in self.particulas:
            p.desenhar(tela)


class FlashConjuracao:
    """Flash luminoso e fagulhas emitidas na ponta do cajado de Halia no início do lançamento."""
    def __init__(self, x, y, elemento="ARCANO"):
        self.x = int(x)
        self.y = int(y)
        self.config = CORES_ELEMENTOS.get(elemento.upper(), CORES_ELEMENTOS["ARCANO"])
        self.vida = 14.0
        self.vida_max = 14.0
        self.particulas = []
        for _ in range(12):
            ang = random.uniform(-math.pi * 0.45, math.pi * 0.45) # voltado para a frente
            spd = random.uniform(2.0, 6.0)
            self.particulas.append(
                ParticulaVisual(
                    x=self.x,
                    y=self.y,
                    vx=math.cos(ang) * spd,
                    vy=math.sin(ang) * spd,
                    vida=random.uniform(8.0, 14.0),
                    cor=self.config["nucleo"],
                    raio=random.uniform(2.0, 3.8),
                    desaceleracao=0.88
                )
            )

    def atualizar(self, dt=1.0):
        self.vida -= dt
        self.particulas = [p for p in self.particulas if p.atualizar(dt)]
        return self.vida > 0 or bool(self.particulas)

    def desenhar(self, tela):
        if self.vida > 0:
            ratio = self.vida / self.vida_max
            raio = int(18 * ratio)
            if raio > 1:
                surf_f = pygame.Surface((raio * 2, raio * 2), pygame.SRCALPHA)
                cor_f = (*self.config["nucleo"][:3], int(200 * ratio))
                pygame.draw.circle(surf_f, cor_f, (raio, raio), raio)
                tela.blit(surf_f, (self.x - raio, self.y - raio))
        for p in self.particulas:
            p.desenhar(tela)


class CombatVisualEffects:
    """
    Gerenciador Central de Efeitos Mágicos de Combate:
    - Coordena projéteis direcionados individuais e em leque (AoE)
    - Coordena explosões elementais de impacto nos monstros
    - Caching inteligente e sob demanda de frames dimensionados e tintados
    """
    def __init__(self, combat_screen):
        self.cs = combat_screen
        self.projeteis = []
        self.explosoes = []
        self.flashes = []
        self._cache_frames_explosao = {}

    def _obter_frames_explosao(self, elemento, escala=1.15):
        """Retorna a sequência de frames de explosão escalada e tintada para o elemento especificado."""
        chave = (elemento, escala)
        if chave in self._cache_frames_explosao:
            return self._cache_frames_explosao[chave]

        config = CORES_ELEMENTOS.get(elemento, CORES_ELEMENTOS["ARCANO"])
        pasta = config.get("pasta_explosao", "efeitos/explosao/explosao_2")
        frames_orig = ResourceManager.carregar_frames_pasta(pasta)

        if not frames_orig:
            # Fallback procedural de explosão esférica pulsante
            frames_procedurais = []
            for r in range(12, 54, 4):
                surf_fb = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                pygame.draw.circle(surf_fb, (*config["primaria"], 200), (r, r), r)
                pygame.draw.circle(surf_fb, (*config["nucleo"], 255), (r, r), max(1, r // 2))
                frames_procedurais.append(surf_fb)
            self._cache_frames_explosao[chave] = frames_procedurais
            return frames_procedurais

        frames_processados = []
        tint = config.get("tint_explosao", None)
        eh_fogo = (elemento == "FOGO")

        for f in frames_orig:
            nw = max(1, int(f.get_width() * escala))
            nh = max(1, int(f.get_height() * escala))
            f_scale = pygame.transform.scale(f, (nw, nh))

            # Se for fogo, a explosão natural alaranjada já tem visual excelente;
            # Para outros elementos (gelo, elétrico, sombra, vento), aplica o filtro cromático
            if tint and not eh_fogo:
                f_final = f_scale.copy()
                tint_surf = pygame.Surface((nw, nh), pygame.SRCALPHA)
                tint_surf.fill((*tint[:3], 170))
                f_final.blit(tint_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                frames_processados.append(f_final)
            else:
                frames_processados.append(f_scale)

        self._cache_frames_explosao[chave] = frames_processados
        return frames_processados

    def disparar_magia_aoe(self, acao, conjurador, alvos_com_dados, on_impacto_alvo=None):
        """
        Dispara barragem de projéteis fanning out em direção a todos os alvos atingidos pela magia em área.
        Cada projétil viaja com rastro de luz e culmina em uma explosão no centro do seu monstro alvo.
        """
        if not alvos_com_dados:
            return

        elemento = getattr(acao, 'elemento', 'ARCANO').upper() if hasattr(acao, 'elemento') else 'ARCANO'
        
        # Ponto de origem: cajado/mão do conjurador
        eh_jogador = (conjurador is getattr(self.cs, "jogador", None))
        cx_c, cy_c = self.cs._obter_posicao_combate(conjurador)
        if eh_jogador:
            origem_x = cx_c + 68
            origem_y = cy_c + 42
        else:
            origem_x = cx_c + 15
            origem_y = cy_c + 45

        # Flash de conjuração no ponto de origem
        self.flashes.append(FlashConjuracao(origem_x, origem_y, elemento))

        total_alvos = len(alvos_com_dados)

        for i, info in enumerate(alvos_com_dados):
            alvo_entidade = info.get("alvo", getattr(self.cs, "jogador", None))
            ax, ay = self.cs._obter_posicao_combate(alvo_entidade)
            
            eh_alvo_jogador = (alvo_entidade is getattr(self.cs, "jogador", None))
            if eh_alvo_jogador:
                destino_x = ax + 32
                destino_y = ay + 48
            else:
                destino_x = ax + 40
                destino_y = ay + 45

            # Leque de arcos: projéteis superiores curvam para cima, inferiores para baixo
            if total_alvos > 1:
                curva = (i - (total_alvos - 1) / 2.0) * 36.0
                vel = 21.0 + (i % 2) * 2.0  # Leve assincronia para dinâmica visual orgânica
            else:
                curva = 0.0
                vel = 22.0

            def criar_callback(alvo_e, dados_d):
                def _callback(proj):
                    # Spawna explosão elemental centrada no inimigo
                    frames = self._obter_frames_explosao(elemento, escala=1.15)
                    self.explosoes.append(
                        ExplosaoMagica(proj.destino_x, proj.destino_y, elemento=elemento, frames=frames)
                    )
                    # Dispara reações visuais e numéricas no combate
                    if on_impacto_alvo:
                        on_impacto_alvo(alvo_e, dados_d)
                return _callback

            p = ProjetilMagico(
                x_origem=origem_x,
                y_origem=origem_y,
                x_destino=destino_x,
                y_destino=destino_y,
                elemento=elemento,
                velocidade=vel,
                curva_offset=curva,
                alvo=alvo_entidade,
                dados_dano=info,
                on_impacto=criar_callback(alvo_entidade, info)
            )
            self.projeteis.append(p)

    def disparar_magia_alvo(self, acao, conjurador, alvo, dados_dano, on_impacto_alvo=None):
        """Dispara um projétil direcionado e explosão para magias ofensivas direcionadas a alvo único."""
        self.disparar_magia_aoe(acao, conjurador, [{"alvo": alvo, "dados": dados_dano}], on_impacto_alvo)

    def adicionar_explosao_direta(self, x, y, elemento="ARCANO", escala=1.15):
        """Permite adicionar uma explosão imediata em coordenadas específicas."""
        frames = self._obter_frames_explosao(elemento, escala=escala)
        self.explosoes.append(ExplosaoMagica(x, y, elemento=elemento, frames=frames))

    def atualizar(self, dt=1.0):
        """Atualiza a física e ciclo de vida de todos os flashes, projéteis e explosões."""
        self.flashes = [f for f in self.flashes if f.atualizar(dt)]
        self.projeteis = [p for p in self.projeteis if p.atualizar(dt)]
        self.explosoes = [e for e in self.explosoes if e.atualizar(dt)]

    def desenhar(self, tela):
        """Renderiza flashes de conjuração, projéteis e explosões sobre a arena de combate."""
        for f in self.flashes:
            f.desenhar(tela)
        for p in self.projeteis:
            p.desenhar(tela)
        for e in self.explosoes:
            e.desenhar(tela)

    def tem_efeitos_ativos(self):
        """Indica se ainda existem projéteis em voo ou explosões em andamento na arena."""
        return bool(self.projeteis or self.explosoes)

    def limpar(self):
        """Limpa imediatamente todos os efeitos visuais (ao sair do combate)."""
        self.projeteis.clear()
        self.explosoes.clear()
        self.flashes.clear()
