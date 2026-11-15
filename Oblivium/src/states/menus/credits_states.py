# src/states/menus/credits_states.py
import pygame
from src.states.states import State
from src.utils.colors import (
    PRETO, CARVAO_PROFUNDO, CINZA_ARDOSIA, CINZA_LINHO,
    MARFIM_OFFWHITE, DOURADO_ENVELHECIDO, UI_TEXTO_APAGADO,
    AZUL_HOVER_MENU, AZUL_HOVER_BG
)
from src.utils.resource_manager import ResourceManager
from src.ui.ui_utils import desenhar_painel_padrao, quebrar_texto_em_linhas


class CreditsState(State):
    """
    Tela de Créditos de Oblivium com dois modos de apresentação:
    - "MENU": painel clássico estático acessível pelo Menu Principal;
    - "DEMO": sequência cinemática de encerramento da Demo (agradecimento solene,
      rolagem contínua sem pétalas sobre o texto e retorno limpo ao Menu Principal).
    """

    VELOCIDADE_ROLAGEM = 38.0
    VELOCIDADE_ACELERADA = 115.0

    def __init__(self, game, modo="MENU"):
        super().__init__(game)
        self.fonte_titulo = ResourceManager.carregar_fonte("sunday", 34)
        self.fonte_demo_destaque = ResourceManager.carregar_fonte("sunday", 32)
        self.fonte_secao = ResourceManager.carregar_fonte("sunday", 21)
        self.fonte_texto = ResourceManager.carregar_fonte("contrail", 18)
        self.fonte_texto_demo = ResourceManager.carregar_fonte("contrail", 21)
        self.fonte_agradecimento = ResourceManager.carregar_fonte("just_breathe", 22)
        self.fonte_aviso = ResourceManager.carregar_fonte("contrail", 16)

        self.rect_voltar = pygame.Rect(0, 0, 0, 0)
        self.modo = modo if modo in ("MENU", "DEMO") else "MENU"
        self.fase_demo = "INATIVO"
        self.tempo_total = 0.0
        self.tempo_fase = 0.0
        self.scroll_y = 560.0
        self._altura_conteudo_demo = 680.0
        self._demo_finalizado = False
        self._on_demo_concluido = None

        self.mensagem_agradecimento = "obrigado por jogar a demo"
        self.submensagem_demo = "Sua jornada continuará além das colinas de Oakhaven..."

        self.linhas_creditos = [
            {"texto": "— DESENVOLVIMENTO PRINCIPAL —", "tipo": "secao", "centralizado": True, "cor": AZUL_HOVER_MENU},
            {"texto": "João Victor Sales de Azevedo Silva — Arquitetura, Programação, UI e Roteiro", "tipo": "normal", "centralizado": False, "cor": CINZA_LINHO},
            {"texto": "Davi Gomes Suassuna — Colaboração em Sistemas e Gameplay", "tipo": "normal", "centralizado": False, "cor": CINZA_LINHO},

            {"texto": "— ARTE, CENÁRIOS E VISUAL —", "tipo": "secao", "centralizado": True, "cor": AZUL_HOVER_MENU},
            {"texto": "Pixel Art Original de Halia, Cenários e Interfaces — Equipe Oblivium", "tipo": "normal", "centralizado": False, "cor": CINZA_LINHO},
            {"texto": "Tilesets Complementares — Craftpix Free Assets", "tipo": "normal", "centralizado": False, "cor": CINZA_LINHO},

            {"texto": "— ÁUDIO E TRILHA SONORA —", "tipo": "secao", "centralizado": True, "cor": AZUL_HOVER_MENU},
            {"texto": "Composição Musical: Kevin Penkin, Evan Call, Shiro SAGISU, Yasunori Nishiki e Toshio Masuda / MUSASHI PROJECT", "tipo": "normal", "centralizado": False, "cor": CINZA_LINHO},
            {"texto": "Fantasy UI SFX Free by heyheythere - https://heyheythere.itch.io/fantasy-ui-sfx-free - CC BY 4.0", "tipo": "normal", "centralizado": False, "cor": CINZA_LINHO},
            {"texto": "Efeitos Sonoros de Combate, Magia e Ambiente: FantasySFX Sampler por AHTu20 (https://ahtu20.itch.io) e Ambient Loops Free Lite 3 por yetiancai", "tipo": "normal", "centralizado": False, "cor": CINZA_LINHO},

            {"texto": "— AGRADECIMENTOS —", "tipo": "secao", "centralizado": True, "cor": AZUL_HOVER_MENU},
            {"texto": "Agradecimento especial ao professor Max Miller e a todos que apoiaram este projeto de Programação Orientada a Objetos.", "tipo": "normal", "centralizado": True, "cor": CINZA_LINHO},
        ]

    def on_enter(self):
        if self.modo == "DEMO":
            self.iniciar_modo_demo(on_concluido=self._on_demo_concluido)

    def obter_textos_demo(self):
        return [self.mensagem_agradecimento, self.submensagem_demo]

    def iniciar_modo_menu(self):
        """Configura o estado para visualização estática a partir do Menu Principal."""
        self.modo = "MENU"
        self.fase_demo = "INATIVO"
        self._demo_finalizado = False
        self._on_demo_concluido = None

    def iniciar_modo_demo(self, on_concluido=None):
        """Prepara os créditos cinemáticos de encerramento da Demo."""
        self.modo = "DEMO"
        self.game.origem_creditos = "DEMO"
        self.fase_demo = "AGRADECIMENTO"
        self.tempo_total = 0.0
        self.tempo_fase = 0.0
        self._demo_finalizado = False
        self._on_demo_concluido = on_concluido
        alt = getattr(self.game, "ALTURA", 720)
        self.scroll_y = float(alt - 130)
        self._altura_conteudo_demo = self._calcular_altura_conteudo_demo()

        if hasattr(self.game, "audio") and self.game.audio:
            if hasattr(self.game.audio, "limpar_contexto_combate"):
                self.game.audio.limpar_contexto_combate()
            elif hasattr(self.game.audio, "musica_anterior"):
                self.game.audio.musica_anterior = None
            try:
                self.game.audio.tocar_musica(
                    "creditos_demo", loop=-1, fade_ms=1000, salvar_anterior=False, contexto="cutscene"
                )
            except TypeError:
                self.game.audio.tocar_musica("creditos_demo", loop=-1, fade_ms=1000)

    def _calcular_altura_conteudo_demo(self):
        larg_util = min(840, getattr(self.game, "LARGURA", 1280) - 180)
        total = 20.0
        for idx, item in enumerate(self.linhas_creditos):
            fonte = self.fonte_secao if item["tipo"] == "secao" else self.fonte_texto_demo
            if item["tipo"] == "secao" and idx > 0:
                total += 22.0
            linhas = self._quebrar_texto(item["texto"], fonte, larg_util)
            total += len(linhas) * (30.0 if item["tipo"] == "secao" else 28.0)
            total += 8.0
        return total

    def _finalizar_demo(self):
        if self._demo_finalizado:
            return
        self._demo_finalizado = True
        self.fase_demo = "FINALIZADO"
        self.modo = "MENU"
        if hasattr(self.game, "audio") and self.game.audio:
            if hasattr(self.game.audio, "limpar_contexto_combate"):
                self.game.audio.limpar_contexto_combate()
            elif hasattr(self.game.audio, "musica_anterior"):
                self.game.audio.musica_anterior = None
            self.game.audio.parar_ambiente(fade_ms=400)
        cb = self._on_demo_concluido
        self._on_demo_concluido = None
        if callable(cb):
            cb()
        self.game.mudar_estado("MENU")

    def handle_events(self, eventos, teclas):
        if self.modo == "DEMO":
            for evento in eventos:
                if evento.type == pygame.KEYDOWN:
                    if evento.key == pygame.K_ESCAPE:
                        if self.tempo_total >= 0.35:
                            self._finalizar_demo()
                            return
                    elif evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                        if self.fase_demo == "AGRADECIMENTO" and self.tempo_total >= 0.45:
                            self.fase_demo = "ROLAGEM"
                            self.tempo_fase = 0.0
                        elif self.fase_demo == "POS_ROLAGEM" and self.tempo_fase >= 0.25:
                            self._finalizar_demo()
                            return
                elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                    if self.fase_demo == "AGRADECIMENTO" and self.tempo_total >= 0.45:
                        self.fase_demo = "ROLAGEM"
                        self.tempo_fase = 0.0
            return

        for evento in eventos:
            if evento.type == pygame.KEYDOWN:
                if evento.key in [pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE]:
                    self.game.mudar_estado("MENU")
            elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                if self.rect_voltar.collidepoint(evento.pos):
                    self.game.mudar_estado("MENU")

    def _obter_dt(self, dt=None):
        if isinstance(dt, (int, float)) and dt > 0:
            return min(float(dt), 0.1)
        dt_game = getattr(self.game, "dt", 0.0)
        if isinstance(dt_game, (int, float)) and dt_game > 0:
            return min(float(dt_game), 0.1)
        if hasattr(self.game, "clock"):
            dt_clk = self.game.clock.get_time() / 1000.0
            if dt_clk > 0:
                return min(dt_clk, 0.1)
        return 0.016

    def update(self, dt=None):
        dt_real = self._obter_dt(dt)
        if self.modo == "DEMO":
            self.tempo_total += dt_real
            self.tempo_fase += dt_real

            if self.fase_demo == "AGRADECIMENTO":
                if self.tempo_fase >= 2.8:
                    self.fase_demo = "ROLAGEM"
                    self.tempo_fase = 0.0
            elif self.fase_demo == "ROLAGEM":
                teclas = pygame.key.get_pressed()
                acelerar = bool(
                    teclas[pygame.K_SPACE] or teclas[pygame.K_RETURN] or teclas[pygame.K_KP_ENTER]
                )
                vel = self.VELOCIDADE_ACELERADA if acelerar else self.VELOCIDADE_ROLAGEM
                self.scroll_y -= vel * dt_real
                if self.scroll_y + self._altura_conteudo_demo < 95.0:
                    self.fase_demo = "POS_ROLAGEM"
                    self.tempo_fase = 0.0
            elif self.fase_demo == "POS_ROLAGEM":
                if self.tempo_fase >= 1.4:
                    self._finalizar_demo()
            return

        if getattr(self.game, "origem_creditos", "MENU") == "MENU":
            if hasattr(self.game, "menu") and hasattr(self.game.menu, "efeito_petalas"):
                self.game.menu.efeito_petalas.atualizar(dt_real)

    def _quebrar_texto(self, texto, fonte, largura_maxima):
        """Quebra textos longos mantendo a legibilidade na largura configurada."""
        if not fonte or not texto:
            return [texto] if texto else []
        return quebrar_texto_em_linhas(texto, fonte, largura_maxima)

    def _draw_demo(self, tela):
        larg = tela.get_width()
        alt = tela.get_height()
        tela.fill(CARVAO_PROFUNDO)

        # Borda sutil em torno da tela inteira sem pétalas cruzando o texto
        pygame.draw.rect(tela, (36, 34, 44), pygame.Rect(18, 18, larg - 36, alt - 36), 1)
        cx = larg // 2

        if self.fase_demo == "AGRADECIMENTO":
            alpha_in = min(1.0, self.tempo_fase / 0.6)
            alpha_out = 1.0 if self.tempo_fase < 2.2 else max(0.0, (2.8 - self.tempo_fase) / 0.6)
            alpha = int(255 * min(alpha_in, alpha_out))

            s_msg = self.fonte_demo_destaque.render(self.mensagem_agradecimento, True, MARFIM_OFFWHITE)
            s_sub = self.fonte_agradecimento.render(self.submensagem_demo, True, DOURADO_ENVELHECIDO)
            s_msg.set_alpha(alpha)
            s_sub.set_alpha(alpha)
            tela.blit(s_msg, s_msg.get_rect(center=(cx, alt // 2 - 22)))
            tela.blit(s_sub, s_sub.get_rect(center=(cx, alt // 2 + 24)))

            s_hint = self.fonte_aviso.render("[ESPAÇO] Avançar   •   [ESC] Pular", True, UI_TEXTO_APAGADO)
            tela.blit(s_hint, s_hint.get_rect(center=(cx, alt - 42)))
            return

        if self.fase_demo == "ROLAGEM":
            s_cab = self.fonte_secao.render("OBLIVIUM — CRÉDITOS DA DEMO", True, DOURADO_ENVELHECIDO)
            tela.blit(s_cab, s_cab.get_rect(center=(cx, 48)))
            pygame.draw.line(tela, CINZA_ARDOSIA, (140, 74), (larg - 140, 74), 1)

            clip_rect = pygame.Rect(0, 86, larg, alt - 166)
            clip_anterior = tela.get_clip()
            tela.set_clip(clip_rect)

            larg_util = min(840, larg - 180)
            y_cursor = self.scroll_y
            for idx, item in enumerate(self.linhas_creditos):
                fonte = self.fonte_secao if item["tipo"] == "secao" else self.fonte_texto_demo
                cor = DOURADO_ENVELHECIDO if item["tipo"] == "secao" else item["cor"]
                if item["tipo"] == "secao" and idx > 0:
                    y_cursor += 22.0
                for linha in self._quebrar_texto(item["texto"], fonte, larg_util):
                    surf_l = fonte.render(linha.strip(), True, cor)
                    if clip_rect.top - 40 <= y_cursor <= clip_rect.bottom + 10:
                        tela.blit(surf_l, surf_l.get_rect(center=(cx, int(y_cursor))))
                    y_cursor += 30.0 if item["tipo"] == "secao" else 28.0
                y_cursor += 8.0

            tela.set_clip(clip_anterior)

            # Máscaras suaves de transição na entrada/saída do clip
            for i in range(28):
                alpha_f = int(255 * (1.0 - i / 28.0))
                faixa_sup = pygame.Surface((larg - 40, 1), pygame.SRCALPHA)
                faixa_sup.fill((*CARVAO_PROFUNDO[:3], alpha_f))
                tela.blit(faixa_sup, (20, clip_rect.top + i))
                tela.blit(faixa_sup, (20, clip_rect.bottom - 1 - i))

            s_hint = self.fonte_aviso.render(
                "[ESPAÇO] Acelerar   •   [ESC] Voltar ao Menu Principal",
                True,
                UI_TEXTO_APAGADO,
            )
            tela.blit(s_hint, s_hint.get_rect(center=(cx, alt - 42)))
            return

        # POS_ROLAGEM
        s_fim = self.fonte_agradecimento.render("Até o próximo horizonte...", True, DOURADO_ENVELHECIDO)
        tela.blit(s_fim, s_fim.get_rect(center=(cx, alt // 2)))

    def draw(self, tela):
        if self.modo == "DEMO":
            self._draw_demo(tela)
            return

        if getattr(self.game, "origem_creditos", "MENU") == "MENU":
            tela.fill(PRETO)
            if hasattr(self.game, "menu") and hasattr(self.game.menu, "efeito_petalas"):
                self.game.menu.efeito_petalas.desenhar(tela)
        else:
            tela.fill(CARVAO_PROFUNDO)

        largura_bloco = 860
        altura_bloco = 580
        x = (self.game.LARGURA - largura_bloco) // 2
        y = (self.game.ALTURA - altura_bloco) // 2

        rect_painel = pygame.Rect(x, y, largura_bloco, altura_bloco)
        desenhar_painel_padrao(tela, rect_painel, cor_fundo=CARVAO_PROFUNDO, cor_borda=CINZA_LINHO, alpha=245)

        rect_interno = rect_painel.inflate(-10, -10)
        pygame.draw.rect(tela, (28, 28, 34), rect_interno, 1, border_radius=2)

        titulo = self.fonte_titulo.render("Créditos — Oblivium", True, MARFIM_OFFWHITE)
        tela.blit(titulo, (x + (largura_bloco - titulo.get_width()) // 2, y + 22))
        pygame.draw.line(tela, CINZA_ARDOSIA, (x + 50, y + 64), (x + largura_bloco - 50, y + 64), 1)

        pos_y_atual = y + 76
        largura_util = largura_bloco - 110

        for i, item in enumerate(self.linhas_creditos):
            tipo = item["tipo"]
            fonte_utilizada = self.fonte_secao if tipo == "secao" else self.fonte_texto
            if tipo == "secao" and i > 0:
                pos_y_atual += 10
            linhas_quebradas = self._quebrar_texto(item["texto"], fonte_utilizada, largura_util)
            for linha in linhas_quebradas:
                render = fonte_utilizada.render(linha.strip(), True, item["cor"])
                pos_x = (
                    x + (largura_bloco - render.get_width()) // 2
                    if item["centralizado"]
                    else x + 55
                )
                tela.blit(render, (pos_x, pos_y_atual))
                pos_y_atual += 23
            pos_y_atual += 4 if tipo == "secao" else 2

        pos_mouse = pygame.mouse.get_pos()
        hover_voltar = self.rect_voltar.collidepoint(pos_mouse)
        cor_aviso = AZUL_HOVER_MENU if hover_voltar else UI_TEXTO_APAGADO
        aviso = self.fonte_aviso.render("[ Pressione ESC ou clique aqui para voltar ]", True, cor_aviso)
        self.rect_voltar = pygame.Rect(
            x + (largura_bloco - aviso.get_width()) // 2 - 10,
            y + altura_bloco - 36,
            aviso.get_width() + 20,
            aviso.get_height() + 8,
        )
        if hover_voltar:
            pygame.draw.rect(tela, AZUL_HOVER_BG, self.rect_voltar, border_radius=3)
            pygame.draw.rect(tela, AZUL_HOVER_MENU, self.rect_voltar, 1, border_radius=3)
        tela.blit(aviso, (x + (largura_bloco - aviso.get_width()) // 2, y + altura_bloco - 32))
