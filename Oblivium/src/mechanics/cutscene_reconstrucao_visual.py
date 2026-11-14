# src/mechanics/cutscene_reconstrucao_visual.py
import pygame
import math
import random
import os
import sys

_raiz = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _raiz not in sys.path:
    sys.path.insert(0, _raiz)

from src.utils.resource_manager import ResourceManager
from src.utils.colors import (
    CARVAO_PROFUNDO, CINZA_ARDOSIA, CINZA_ESCURO, CINZA_LINHO,
    MARFIM_OFFWHITE, DOURADO_ENVELHECIDO, AZUL_HOVER_MENU,
    TXT_ECO_PASSADO, UI_TEXTO_APAGADO
)
from src.ui.ui_utils import quebrar_texto_em_linhas
from src.mechanics.cena_base import CenaBase


class ParticulaReconstrucao:
    """Partícula mágica de restauração (fagulhas douradas, orvalho lunar ou pólen solar)."""
    __slots__ = ("x", "y", "vx", "vy", "vida", "vida_max", "raio", "fase_seno", "cor")

    def __init__(self, x_min, x_max, y_min, y_max, tipo="luz_dourada"):
        self.x = random.uniform(x_min, x_max)
        self.y = random.uniform(y_min, y_max)
        self.vx = random.uniform(-0.5, 0.5)
        self.vy = random.uniform(-1.2, -0.3)
        self.vida = random.uniform(40, 90)
        self.vida_max = float(self.vida)
        self.raio = random.uniform(1.5, 3.5)
        self.fase_seno = random.uniform(0, math.pi * 2)

        if tipo == "fagulha_arcana":
            self.cor = random.choice([
                (255, 180, 70),
                (255, 220, 110),
                (120, 200, 255),
                (180, 240, 255),
            ])
        elif tipo == "orvalho_lunar":
            self.cor = random.choice([
                (150, 230, 255),
                (190, 255, 230),
                (220, 210, 255),
                (180, 255, 210),
            ])
        else:  # luz_dourada
            self.cor = random.choice([
                (255, 235, 150),
                (255, 215, 100),
                (255, 245, 190),
                (240, 220, 170),
            ])

    def atualizar(self, dt=1.0 / 60.0):
        self.vida -= dt * 60.0
        self.fase_seno += 0.08 * dt * 60.0
        self.x += (self.vx + math.sin(self.fase_seno) * 0.5) * dt * 60.0
        self.y += self.vy * dt * 60.0
        return self.vida > 0

    def desenhar(self, tela):
        ratio = max(0.0, min(1.0, self.vida / self.vida_max))
        alpha = int(220 * math.sin(ratio * math.pi))
        if alpha <= 0:
            return
        surf = pygame.Surface((int(self.raio * 4), int(self.raio * 4)), pygame.SRCALPHA)
        cx = int(self.raio * 2)
        pygame.draw.circle(surf, (*self.cor[:3], alpha), (cx, cx), int(self.raio))
        tela.blit(surf, (int(self.x) - cx, int(self.y) - cx))


class CutsceneReconstrucaoVisual(CenaBase):
    """
    Cutscene Cinemática Visual da Reconstrução de Oakhaven (Encerramento da Fase 1).
    Apresenta a transição visual das áreas destruídas da vila sendo reconstruídas
    pelas mãos de Halia e dos moradores (Torvald, Elara, Aldous e Guarda Doran):
    - Cross-fade suave e contínuo entre as ruínas e as estruturas restauradas.
    - Halia e NPCs em cena nas áreas correspondentes com animação de respiração sutil.
    - Partículas de restauração mágica (fagulhas arcanas, orvalho lunar e luz solar).
    - Caixa de narração com tipografia canônica sem sobreposição indesejada.
    """
    def __init__(self, game, playing_state=None):
        super().__init__(game=game, on_concluido=None)
        self.playing_state = playing_state
        self.largura = getattr(game, "LARGURA", 1280) if game is not None else 1280
        self.altura = getattr(game, "ALTURA", 720) if game is not None else 720

        self._consequencias_aplicadas = False
        self.indice_cena = 0
        self.tempo_cena = 0.0
        self.progresso_reconstrucao = 0.0
        self.duracao_crossfade = 4.0
        self.duracao_cena_total = 9.0

        self.caractere_atual = 0.0
        self.velocidade_digitacao = 38.0
        self.particulas = []

        # Fontes do jogo
        self.fonte_titulo = ResourceManager.carregar_fonte("sunday", 24)
        self.fonte_texto = ResourceManager.carregar_fonte("just_breathe", 24)
        self.fonte_dica = ResourceManager.carregar_fonte("contrail", 15)

        # Cache de superfícies carregadas
        self._sprite_cache = {}

        # Definição dos 3 quadros de reconstrução visual
        self.cenas = [
            {
                "id": "forja",
                "titulo": "A Forja e o Ferro Renascido",
                "epoca": "TRÊS SEMANAS APÓS A QUEDA DE IGNIS'VAHR",
                "texto": "Halia guia chamas arcanas para acelerar o fole enquanto Torvald ergue as vigas mestras da nova forja. O bater rítmico do martelo na bigorna já não soa como batalha, mas como a pulsação viva de Oakhaven renascendo.",
                "ruina_estrutura": "cenario/vila/Casas/Conjunto_2/Frente/casa_12_lateral_destruida.png",
                "restaurada_estrutura": "cenario/vila/Casas/Conjunto_2/Frente/casa_02_com_forja_chamine.png",
                "tamanho_estrutura": (440, 310),
                "pos_estrutura": (430, 140),
                "ruina_prop": "cenario/vila/Barracas/Frente/barraca_15_ruina_queimada.png",
                "restaurado_prop": "cenario/vila/Barracas/Frente/barraca_09_ferraria_ferramentas.png",
                "tamanho_prop": (230, 185),
                "pos_prop": (870, 260),
                "personagens": [
                    {"nome": "Halia", "path": "halia/frente/Halia_frente_parado.png", "pos": (280, 320), "tamanho": (90, 140)},
                    {"nome": "Torvald", "path": "npc/torvald_ferreiro/idle/torvald_idle_01.png", "pos": (370, 315), "tamanho": (90, 150)}
                ],
                "tipo_particula": "fagulha_arcana"
            },
            {
                "id": "botanica",
                "titulo": "O Herbário e o Despertar da Terra",
                "epoca": "UM MÊS DEPOIS — O DESPERTAR DAS FLORES",
                "texto": "Gotas de orvalho lunar revitalizam a terra crestada pelo dragão. Halia e Elara plantam brotos de cura e distribuem unguentos aos feridos, trazendo de volta o verde e o calor do acolhimento.",
                "ruina_estrutura": "cenario/vila/Lojas/Frente/loja_15_ruina_incendio_telhado.png",
                "restaurada_estrutura": "cenario/vila/Lojas/Frente/loja_09_floricultura.png",
                "tamanho_estrutura": (390, 320),
                "pos_estrutura": (450, 130),
                "ruina_prop": "cenario/vila/Barracas/Frente/barraca_14_ruina_saqueada.png",
                "restaurado_prop": "cenario/vila/Barracas/Frente/barraca_04_floricultura_vasos.png",
                "tamanho_prop": (230, 185),
                "pos_prop": (860, 260),
                "personagens": [
                    {"nome": "Halia", "path": "halia/frente/Halia_frente_parado.png", "pos": (270, 320), "tamanho": (90, 140)},
                    {"nome": "Elara", "path": "npc/elara_curandeira/idle/elara_idle_01.png", "pos": (360, 330), "tamanho": (75, 135)}
                ],
                "tipo_particula": "orvalho_lunar"
            },
            {
                "id": "praca",
                "titulo": "A Praça Central e a Consagração da Protetora",
                "epoca": "O DIA DA CONSAGRAÇÃO DE OAKHAVEN",
                "texto": "Sob a luz límpida da aurora, toda a vila reúne-se diante do Monumento dos Heróis. O Ancião Aldous e o Guarda Doran celebram a paz recuperada e consagram Halia como a eterna guardiã dos carvalhos antigos.",
                "ruina_estrutura": "cenario/vila/Props/Monumentos/monumento_herois_danificado.png",
                "restaurada_estrutura": "cenario/vila/Props/Monumentos/monumento_herois_intacto.png",
                "tamanho_estrutura": (440, 320),
                "pos_estrutura": (430, 130),
                "ruina_prop": "cenario/vila/Props/Cargas_e_Transporte/carroca_destruida.png",
                "restaurado_prop": "cenario/vila/Props/Monumentos/monumento_espada_fincada.png",
                "tamanho_prop": (170, 190),
                "pos_prop": (880, 260),
                "personagens": [
                    {"nome": "Aldous", "path": "npc/aldous_lider/idle/aldous_idle_01.png", "pos": (220, 325), "tamanho": (85, 140)},
                    {"nome": "Halia", "path": "halia/frente/Halia_frente_parado.png", "pos": (305, 320), "tamanho": (90, 140)},
                    {"nome": "Guarda Doran", "path": "npc/guarda_doran/idle/guarda_doran_idle_01.png", "pos": (880, 330), "tamanho": (85, 130)}
                ],
                "tipo_particula": "luz_dourada"
            }
        ]

    def _obter_sprite(self, caminho, tamanho):
        chave = (caminho, tamanho)
        if chave not in self._sprite_cache:
            img = ResourceManager.carregar_imagem(caminho, tamanho=tamanho)
            if img is None:
                # Superfície de fallback caso o arquivo não seja encontrado
                img = pygame.Surface(tamanho, pygame.SRCALPHA)
                img.fill((80, 70, 95, 200))
                pygame.draw.rect(img, (200, 180, 120), img.get_rect(), 2)
            self._sprite_cache[chave] = img
        return self._sprite_cache[chave]

    def iniciar(self, on_concluido=None):
        """Dispara a cutscene visual de reconstrução."""
        self._reiniciar_estado_execucao(on_concluido=on_concluido)
        self._consequencias_aplicadas = False
        self.largura = getattr(self.game, "LARGURA", self.largura) if self.game is not None else self.largura
        self.altura = getattr(self.game, "ALTURA", self.altura) if self.game is not None else self.altura
        self.ativo = True
        self.indice_cena = 0
        self.tempo_cena = 0.0
        self.progresso_reconstrucao = 0.0
        self.caractere_atual = 0.0
        self._spawn_particulas()

        if hasattr(self.game, "audio") and self.game.audio:
            self.game.audio.tocar_musica("tema_vila", loop=-1, fade_ms=1000)

    def _spawn_particulas(self):
        if self.indice_cena < len(self.cenas):
            tipo = self.cenas[self.indice_cena]["tipo_particula"]
            x_min = int(self.largura * 0.15)
            x_max = max(x_min + 50, int(self.largura * 0.85))
            y_min = 150
            y_max = max(y_min + 50, self.altura - 240)
            self.particulas = [
                ParticulaReconstrucao(x_min, x_max, y_min, y_max, tipo=tipo)
                for _ in range(40)
            ]

    def handle_event(self, evento):
        """Gerencia input do jogador para acelerar, avançar ou pular a reconstrução."""
        if not self.ativo:
            return False

        if evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_ESCAPE:
                self.pular()
                return True
            if evento.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_e):
                self._acao_avanco()
                return True
        elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            self._acao_avanco()
            return True

        return False

    def _acao_avanco(self):
        # Se a transição visual ainda estiver acontecendo, conclui o crossfade e o texto imediatamente
        if self.progresso_reconstrucao < 1.0:
            self.progresso_reconstrucao = 1.0
            self.caractere_atual = 9999.0
            self.tempo_cena = max(self.tempo_cena, self.duracao_crossfade)
        else:
            # Já reconstruído na cena atual: avança para a próxima cena
            self._avancar_cena()

    def _avancar_cena(self):
        self.indice_cena += 1
        self.tempo_cena = 0.0
        self.progresso_reconstrucao = 0.0
        self.caractere_atual = 0.0
        if self.indice_cena >= len(self.cenas):
            self.finalizar()
        else:
            self._spawn_particulas()

    def finalizar(self):
        """Conclui a cutscene, restaura Oakhaven e dispara o callback uma única vez."""
        if not self._consequencias_aplicadas:
            self._consequencias_aplicadas = True
            # Restaura Oakhaven para sua versão reconstruída plena
            if hasattr(self.game, "oakhaven_destruida"):
                self.game.oakhaven_destruida = False

            if hasattr(self.game, "mapa_casa") and self.game.mapa_casa:
                self.game.mapa_casa.carregar_cenario("OAKHAVEN")
                if hasattr(self.game, "halia") and self.game.halia:
                    self.game.halia.x, self.game.halia.y = 1102, 600
                    self.game.halia.direcao = "baixo"
                    self.game.halia.mudar_estado("idle")
                if self.playing_state:
                    self.playing_state.atualizar_camera(instantaneo=True)

            if getattr(self.game, "slot_atual", None):
                self.game.salvar_estado(self.game.slot_atual, tipo="autosave")

        return super().finalizar()

    def pular(self):
        """Pula a cutscene de reconstrução deixando Oakhaven restaurada."""
        return self.finalizar()

    def atualizar(self, dt=None):
        """Atualiza a física das partículas, o avanço suave do crossfade e o typewriter."""
        if not self.ativo or self.indice_cena >= len(self.cenas):
            return

        if dt is None:
            dt = getattr(self.game, "dt", 1.0 / 60.0) if self.game else (1.0 / 60.0)
        if not isinstance(dt, (int, float)) or dt <= 0:
            dt = 1.0 / 60.0

        self.tempo_cena += dt
        # Progresso de reconstrução de 0.0 a 1.0
        self.progresso_reconstrucao = min(1.0, self.tempo_cena / self.duracao_crossfade)

        # Atualização do texto gradual
        self.caractere_atual += self.velocidade_digitacao * dt

        # Atualização e reposição de partículas ativas
        particulas_vivas = []
        for p in self.particulas:
            if p.atualizar(dt):
                particulas_vivas.append(p)
            else:
                tipo = self.cenas[self.indice_cena]["tipo_particula"]
                x_min = int(self.largura * 0.15)
                x_max = max(x_min + 50, int(self.largura * 0.85))
                y_max = max(230, self.altura - 240)
                particulas_vivas.append(ParticulaReconstrucao(x_min, x_max, 180, y_max, tipo=tipo))
        self.particulas = particulas_vivas

        # Avanço automático se decorrido o tempo total da cena
        if self.tempo_cena >= self.duracao_cena_total:
            self._avancar_cena()

    def desenhar(self, tela):
        """Renderiza o cenário com transição visual suave entre ruína e restaurado."""
        if not self.ativo or self.indice_cena >= len(self.cenas):
            return

        cena = self.cenas[self.indice_cena]

        # 1. Fundo atmosférico em degradê (alvorecer / renascimento)
        tela.fill(CARVAO_PROFUNDO)
        for y_linha in range(0, 480, 4):
            fator_grad = y_linha / 480.0
            r = int(18 + (38 - 18) * fator_grad)
            g = int(22 + (30 - 22) * fator_grad)
            b = int(32 + (46 - 32) * fator_grad)
            pygame.draw.rect(tela, (r, g, b), (0, y_linha, self.largura, 4))

        # 2. Piso de calçamento e terra da vila na parte inferior da cena
        piso_rect = pygame.Rect(0, 440, self.largura, 60)
        pygame.draw.rect(tela, (42, 38, 36), piso_rect)
        pygame.draw.line(tela, (65, 58, 52), (0, 440), (self.largura, 440), 2)
        pygame.draw.line(tela, DOURADO_ENVELHECIDO, (0, 442), (self.largura, 442), 1)

        # 3. Renderização com cross-fade suave das estruturas
        alpha_restaurada = int(max(0, min(255, self.progresso_reconstrucao * 255)))
        alpha_ruina = int(max(0, min(255, (1.0 - self.progresso_reconstrucao) * 255)))

        # Estrutura principal
        pos_est = cena["pos_estrutura"]
        tam_est = cena["tamanho_estrutura"]
        if alpha_ruina > 0:
            surf_ruina = self._obter_sprite(cena["ruina_estrutura"], tam_est).copy()
            surf_ruina.set_alpha(alpha_ruina)
            tela.blit(surf_ruina, pos_est)

        if alpha_restaurada > 0:
            surf_rest = self._obter_sprite(cena["restaurada_estrutura"], tam_est).copy()
            surf_rest.set_alpha(alpha_restaurada)
            tela.blit(surf_rest, pos_est)

        # Prop secundário
        pos_prop = cena["pos_prop"]
        tam_prop = cena["tamanho_prop"]
        if alpha_ruina > 0:
            surf_p_ruina = self._obter_sprite(cena["ruina_prop"], tam_prop).copy()
            surf_p_ruina.set_alpha(alpha_ruina)
            tela.blit(surf_p_ruina, pos_prop)

        if alpha_restaurada > 0:
            surf_p_rest = self._obter_sprite(cena["restaurado_prop"], tam_prop).copy()
            surf_p_rest.set_alpha(alpha_restaurada)
            tela.blit(surf_p_rest, pos_prop)

        # 4. Desenha Halia e os NPCs em cena
        respiro = math.sin(self.tempo_cena * 3.5) * 2.0
        for pers in cena["personagens"]:
            s_pers = self._obter_sprite(pers["path"], pers["tamanho"])
            px, py = pers["pos"]
            # Sombra suave sob os pés
            sombra_rect = pygame.Rect(px + 10, py + pers["tamanho"][1] - 8, pers["tamanho"][0] - 20, 10)
            surf_sombra = pygame.Surface((sombra_rect.width, sombra_rect.height), pygame.SRCALPHA)
            pygame.draw.ellipse(surf_sombra, (12, 10, 14, 140), (0, 0, sombra_rect.width, sombra_rect.height))
            tela.blit(surf_sombra, (sombra_rect.x, sombra_rect.y))
            # Blit da entidade com leve respiração
            tela.blit(s_pers, (px, py + respiro))

        # 5. Partículas mágica de restauração
        for p in self.particulas:
            p.desenhar(tela)

        # 6. Caixa narrativa elegante inferior
        caixa_larg = min(1000, max(400, self.largura - 280))
        caixa_rect = pygame.Rect((self.largura - caixa_larg) // 2, self.altura - 215, caixa_larg, 175)
        surf_caixa = pygame.Surface((caixa_rect.width, caixa_rect.height), pygame.SRCALPHA)
        surf_caixa.fill((16, 17, 24, 235))
        pygame.draw.rect(surf_caixa, DOURADO_ENVELHECIDO, (0, 0, caixa_rect.width, caixa_rect.height), 2)
        pygame.draw.rect(surf_caixa, (50, 45, 60), (4, 4, caixa_rect.width - 8, caixa_rect.height - 8), 1)
        tela.blit(surf_caixa, caixa_rect.topleft)

        # Título e Época
        if self.fonte_titulo:
            surf_ep = self.fonte_dica.render(cena["epoca"], True, DOURADO_ENVELHECIDO)
            tela.blit(surf_ep, (caixa_rect.x + 25, caixa_rect.y + 16))

            surf_tit = self.fonte_titulo.render(cena["titulo"], True, MARFIM_OFFWHITE)
            tela.blit(surf_tit, (caixa_rect.x + 25, caixa_rect.y + 36))

        # Linha divisória sutil
        pygame.draw.line(
            tela,
            (70, 62, 52),
            (caixa_rect.x + 25, caixa_rect.y + 68),
            (caixa_rect.right - 25, caixa_rect.y + 68),
            1
        )

        # Texto datilografado
        texto_limpo = cena["texto"]
        caracteres_visiveis = int(min(len(texto_limpo), self.caractere_atual))
        texto_parcial = texto_limpo[:caracteres_visiveis]

        if self.fonte_texto:
            linhas = quebrar_texto_em_linhas(texto_parcial, self.fonte_texto, caixa_rect.width - 60)
            y_txt = caixa_rect.y + 78
            for linha in linhas:
                s_txt = self.fonte_texto.render(linha, True, CINZA_LINHO)
                tela.blit(s_txt, (caixa_rect.x + 25, y_txt))
                y_txt += 26

        # Indicador de avanço
        if self.fonte_dica:
            txt_hint = "[ESPAÇO] Avançar" if self.progresso_reconstrucao >= 1.0 else "[ESPAÇO] Pular"
            s_hint = self.fonte_dica.render(txt_hint, True, UI_TEXTO_APAGADO)
            tela.blit(s_hint, (caixa_rect.right - s_hint.get_width() - 25, caixa_rect.bottom - 26))

    def _quebrar_texto(self, texto, largura_max):
        """Quebra o texto em linhas reutilizando o utilitário canônico de ui_utils."""
        if not self.fonte_texto or not texto:
            return [texto] if texto else []
        return quebrar_texto_em_linhas(texto, self.fonte_texto, largura_max)
