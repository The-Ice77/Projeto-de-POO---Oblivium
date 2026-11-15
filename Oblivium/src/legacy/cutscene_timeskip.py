# LEGADO: substituído por src.mechanics.cutscene_reconstrucao_visual (CutsceneReconstrucaoVisual). Mantido por histórico (REGRAS §3).
# src/mechanics/cutscene_timeskip.py
import pygame
import math
import random
import os
import sys

# Garante path raiz de Oblivium
_raiz = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _raiz not in sys.path:
    sys.path.insert(0, _raiz)

from src.utils.resource_manager import ResourceManager
from src.utils.colors import (
    CARVAO_PROFUNDO, CINZA_ARDOSIA, CINZA_ESCURO, CINZA_LINHO,
    MARFIM_OFFWHITE, DOURADO_ENVELHECIDO, AZUL_HOVER_MENU,
    TXT_ECO_PASSADO, UI_TEXTO_APAGADO
)


class ParticulaLuzDourada:
    """Partícula suave de pólen e luz dourada flutuando durante o timeskip."""
    __slots__ = ("x", "y", "vx", "vy", "vida", "vida_max", "raio", "fase_seno", "cor")

    def __init__(self, largura, altura):
        self.x = random.uniform(20, largura - 20)
        self.y = random.uniform(20, altura - 20)
        self.vx = random.uniform(-0.4, 0.4)
        self.vy = random.uniform(-0.8, -0.2)
        self.vida = random.uniform(80, 160)
        self.vida_max = float(self.vida)
        self.raio = random.uniform(1.5, 3.5)
        self.fase_seno = random.uniform(0, math.pi * 2)
        self.cor = random.choice([
            (255, 230, 140),
            (255, 245, 190),
            (220, 255, 230),
            (180, 230, 255)
        ])

    def atualizar(self, dt=1.0):
        self.vida -= dt
        self.fase_seno += 0.05 * dt
        self.x += (self.vx + math.sin(self.fase_seno) * 0.4) * dt
        self.y += self.vy * dt
        return self.vida > 0

    def desenhar(self, tela):
        ratio = max(0.0, min(1.0, self.vida / self.vida_max))
        alpha = int(180 * math.sin(ratio * math.pi))
        if alpha <= 0:
            return
        surf = pygame.Surface((int(self.raio * 4), int(self.raio * 4)), pygame.SRCALPHA)
        cx = int(self.raio * 2)
        pygame.draw.circle(surf, (*self.cor[:3], alpha), (cx, cx), int(self.raio))
        tela.blit(surf, (int(self.x) - cx, int(self.y) - cx))


class CutsceneTimeskipOakhaven:
    """
    Cutscene Cinemática de Passagem de Tempo (Timeskip) e Encerramento da Fase 1 em Oakhaven:
    - Transição poética de semanas após a derrota do Dragão Ancestral Ignis'Vahr.
    - Apresentação de 3 quadros narrativos da reconstrução e acolhimento comunitário:
      1. Halia e Torvald na forja acelerando a têmpera e reconstruindo os telhados.
      2. Halia e Elara colhendo ervas lunares e cuidando dos feridos nos canteiros da vila.
      3. A consagração solene na praça pelo Ancião Aldous diante do Monumento dos Heróis.
    - Conclusão com a vila 100% restaurada sob a luz dourada do sol e Halia consagrada heroína.
    """
    def __init__(self, game, playing_state=None):
        self.game = game
        self.playing_state = playing_state
        self.largura = 1280
        self.altura = 720

        self.ativo = False
        self.fase = "INATIVO"  # 'INATIVO', 'FADE_ENTRADA', 'CENA', 'FADE_SAIDA', 'CONCLUIDO'
        self.alpha_fade = 0.0
        self.indice_cena = 0
        self.tempo_fase = 0.0

        # Fontes canônicas
        self.fonte_capitulo = ResourceManager.carregar_fonte("sunday", 28)
        self.fonte_titulo = ResourceManager.carregar_fonte("sunday", 24)
        self.fonte_texto = ResourceManager.carregar_fonte("just_breathe", 25)
        self.fonte_dica = ResourceManager.carregar_fonte("contrail", 16)

        # Controle de digitação (máquina de escrever suave)
        self.caractere_atual = 0.0
        self.velocidade_digitacao = 0.85
        self.texto_completo_exibido = False

        # Partículas de atmosfera
        self.particulas = []

        # Conteúdo narrativo dos 3 quadros de reconstrução
        self.cenas = [
            {
                "epoca": "TRÊS SEMANAS APÓS A QUEDA DE IGNIS'VAHR",
                "titulo": "A Forja e o Ferro Renascido",
                "icone": "forja",
                "linhas": [
                    "O martelo do Ferreiro Torvald bateu sem cessar desde que o fogo do dragão se apagou.",
                    "Ao lado da fornalha, Halia aprendeu a canalizar pulsos arcanos sutis para resfriar",
                    "e temperar as vigas metálicas das casas destruídas. O som rítmico do ferro na bigorna",
                    "já não soava como pânico de batalha, mas como o batimento cardíaco da vila que renascia."
                ]
            },
            {
                "epoca": "UM MÊS DEPOIS — O DESPERTAR DAS FLORES",
                "titulo": "O Herbário e o Cuidado dos Feridos",
                "icone": "botanica",
                "linhas": [
                    "Nos canteiros floridos a oeste, Halia e Elara colhiam folhas de orvalho lunar ao amanhecer.",
                    "Os aldeões que antes temiam a energia arcana agora se aproximavam com presentes simples:",
                    "pães frescos, fitas de linho e sorrisos de gratidão pelos ungüentos que curavam suas queimaduras.",
                    "Pela primeira vez em sua jornada, o peito de Halia não ardia com solidão: ali havia um lar."
                ]
            },
            {
                "epoca": "O DIA DA CONSAGRAÇÃO DE OAKHAVEN",
                "titulo": "A Protetora dos Carvalhos Antigos",
                "icone": "monumento",
                "linhas": [
                    "Sob a luz límpida da manhã, toda a vila reuniu-se ao redor do Monumento dos Heróis.",
                    "O Ancião Aldous prendeu à capa de Halia o broche de carvalho dourado, declarando-a guardiã oficial.",
                    "As sombras de suas memórias passadas ainda sussurravam promessas distantes no horizonte norte...",
                    "Mas agora ela sabia: onde quer que seus passos a levassem, Oakhaven sempre guardaria seu refúgio."
                ]
            }
        ]

    def iniciar(self):
        """Dispara a sequência de encerramento da Fase 1."""
        self.ativo = True
        self.fase = "FADE_ENTRADA"
        self.alpha_fade = 0.0
        self.indice_cena = 0
        self.tempo_fase = 0.0
        self.caractere_atual = 0.0
        self.texto_completo_exibido = False
        self.particulas = [ParticulaLuzDourada(self.largura, self.altura) for _ in range(35)]

        if hasattr(self.game, "audio") and self.game.audio:
            self.game.audio.tocar_musica("tema_vila", loop=-1, fade_ms=1200)

    def handle_event(self, evento):
        """Avança texto ou cenas via teclado/mouse."""
        if not self.ativo or self.fase not in ("CENA", "FADE_ENTRADA"):
            return False

        if (evento.type == pygame.KEYDOWN and evento.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_e)) or \
           (evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1):
            
            cena_atual = self.cenas[self.indice_cena]
            total_chars = sum(len(linha) for linha in cena_atual["linhas"])

            if not self.texto_completo_exibido:
                # Acelera e conclui a digitação da cena imediatamente
                self.caractere_atual = float(total_chars)
                self.texto_completo_exibido = True
                return True
            else:
                # Avança para a próxima cena ou encerra o timeskip
                if self.indice_cena + 1 < len(self.cenas):
                    self.indice_cena += 1
                    self.caractere_atual = 0.0
                    self.texto_completo_exibido = False
                    self.tempo_fase = 0.0
                else:
                    self.fase = "FADE_SAIDA"
                    self.tempo_fase = 0.0
                return True
        return False

    def atualizar(self, dt=0.016):
        """Atualiza fades, partículas e digitação."""
        if not self.ativo:
            return

        self.tempo_fase += dt

        # Atualiza partículas de luz dourada
        self.particulas = [p for p in self.particulas if p.atualizar(1.0)]
        while len(self.particulas) < 35:
            self.particulas.append(ParticulaLuzDourada(self.largura, self.altura))

        # 1. Fade de entrada
        if self.fase == "FADE_ENTRADA":
            self.alpha_fade = min(235.0, self.alpha_fade + dt * 240.0)
            if self.alpha_fade >= 235.0:
                self.fase = "CENA"
                self.tempo_fase = 0.0

        # 2. Exibição da cena ativa com digitação fluida
        elif self.fase == "CENA":
            cena_atual = self.cenas[self.indice_cena]
            total_chars = sum(len(linha) for linha in cena_atual["linhas"])
            if self.caractere_atual < total_chars:
                self.caractere_atual += self.velocidade_digitacao
                if self.caractere_atual >= total_chars:
                    self.caractere_atual = float(total_chars)
                    self.texto_completo_exibido = True

        # 3. Fade de saída para o mundo restaurado
        elif self.fase == "FADE_SAIDA":
            self.alpha_fade = max(0.0, self.alpha_fade - dt * 200.0)
            if self.alpha_fade <= 0.0:
                self._concluir()

    def _concluir(self):
        """Restaura a vila de Oakhaven para seu estado pacífico diurno definitivo."""
        self.ativo = False
        self.fase = "CONCLUIDO"

        # 1. Flags do estado de jogo da Fase 1 Concluída
        self.game.oakhaven_destruida = False
        self.game.oakhaven_noite = False
        self.game.dragao_derrotado = True
        self.game.desespero_superado = True
        self.game.fase1_concluida = True

        # 2. Recarrega o cenário com a vila 100% viva e ensolarada
        self.game.mapa_casa.carregar_cenario("OAKHAVEN")
        if hasattr(self.game.mapa_casa, "cenario_objeto") and self.game.mapa_casa.cenario_objeto:
            self.game.mapa_casa.cenario_objeto.inicializar_cenario()

        # 3. Posiciona Halia no coração da praça diante da estátua restaurada
        self.game.halia.x = 1102
        self.game.halia.y = 660
        self.game.halia.direcao = "baixo"
        self.game.halia.mudar_estado("idle")

        if self.playing_state:
            self.playing_state.atualizar_camera(instantaneo=True)

        # 4. Autosave silencioso
        if getattr(self.game, "slot_atual", None):
            self.game.salvar_estado(self.game.slot_atual, tipo="autosave", silenciar_notificacao=True)

        # 5. Notificação festiva de encerramento da Fase 1
        if hasattr(self.game, "notificacoes") and self.game.notificacoes:
            self.game.notificacoes.adicionar(
                titulo="OAKHAVEN EM PAZ",
                mensagem="Fase 1 Concluída com Honra! A vila floresce sob sua proteção.",
                tipo="conquista",
                duracao=420
            )

    def desenhar(self, tela):
        """Renderiza a vinheta cinematográfica de timeskip com estética Dark Fantasy solene."""
        if not self.ativo or self.fase == "INATIVO":
            return

        # 1. Backdrop escuro com profundidade suave
        overlay = pygame.Surface((self.largura, self.altura), pygame.SRCALPHA)
        overlay.fill((10, 12, 16, int(self.alpha_fade)))
        tela.blit(overlay, (0, 0))

        if self.fase in ("FADE_ENTRADA", "FADE_SAIDA") and self.alpha_fade < 100:
            return

        # 2. Partículas de luz dourada flutuando
        for p in self.particulas:
            p.desenhar(tela)

        # 3. Card Central Solene da Memória
        card_w, card_h = 860, 430
        cx = (self.largura - card_w) // 2
        cy = (self.altura - card_h) // 2

        # Superfície do Card com bordas nobres
        surf_card = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
        surf_card.fill((16, 20, 26, 225))
        pygame.draw.rect(surf_card, DOURADO_ENVELHECIDO, (0, 0, card_w, card_h), width=1, border_radius=10)
        pygame.draw.rect(surf_card, (45, 52, 65, 140), (8, 8, card_w - 16, card_h - 16), width=1, border_radius=8)
        tela.blit(surf_card, (cx, cy))

        cena = self.cenas[self.indice_cena]

        # 4. Época / Subtítulo Superior em Ouro Pálido
        txt_epoca = self.fonte_capitulo.render(cena["epoca"], True, DOURADO_ENVELHECIDO)
        rect_epoca = txt_epoca.get_rect(center=(self.largura // 2, cy + 38))
        tela.blit(txt_epoca, rect_epoca)

        # Linha divisória ornamental
        pygame.draw.line(tela, DOURADO_ENVELHECIDO, (self.largura // 2 - 180, cy + 62), (self.largura // 2 + 180, cy + 62), 1)

        # 5. Título da Cena
        txt_tit = self.fonte_titulo.render(cena["titulo"], True, MARFIM_OFFWHITE)
        rect_tit = txt_tit.get_rect(center=(self.largura // 2, cy + 92))
        tela.blit(txt_tit, rect_tit)

        # 6. Linhas de Texto Poético com digitação progressiva
        chars_visiveis = int(self.caractere_atual)
        chars_contados = 0
        y_texto = cy + 140

        for linha in cena["linhas"]:
            len_linha = len(linha)
            if chars_visiveis <= chars_contados:
                break
            elif chars_visiveis >= chars_contados + len_linha:
                txt_render = linha
            else:
                chars_nesta = chars_visiveis - chars_contados
                txt_render = linha[:chars_nesta]

            chars_contados += len_linha
            surf_l = self.fonte_texto.render(txt_render, True, (235, 235, 240))
            rect_l = surf_l.get_rect(center=(self.largura // 2, y_texto))
            tela.blit(surf_l, rect_l)
            y_texto += 38

        # 7. Marcador de Progresso (3 gemas)
        for i in range(len(self.cenas)):
            gx = self.largura // 2 + (i - 1) * 36
            gy = cy + card_h - 48
            ativa = (i == self.indice_cena)
            cor_gema = DOURADO_ENVELHECIDO if ativa else CINZA_ARDOSIA
            pygame.draw.circle(tela, cor_gema, (gx, gy), 5 if ativa else 3)
            if ativa:
                pygame.draw.circle(tela, MARFIM_OFFWHITE, (gx, gy), 6, 1)

        # 8. Rodapé de Interação
        if self.texto_completo_exibido:
            if self.indice_cena + 1 < len(self.cenas):
                msg_dica = "[ ENTER / ESPAÇO: Próxima Memória ]"
            else:
                msg_dica = "[ ENTER / ESPAÇO: Explorar Oakhaven em Paz ]"
        else:
            msg_dica = "[ ENTER / ESPAÇO: Acelerar Leitura ]"

        txt_dica = self.fonte_dica.render(msg_dica, True, UI_TEXTO_APAGADO)
        rect_dica = txt_dica.get_rect(center=(self.largura // 2, cy + card_h - 22))
        tela.blit(txt_dica, rect_dica)
