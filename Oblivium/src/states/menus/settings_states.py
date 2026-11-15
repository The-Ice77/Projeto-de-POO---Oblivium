# src/states/settings_states.py
import pygame
from src.states.states import State
from src.utils.colors import (
    PRETO, CARVAO_PROFUNDO, CINZA_ARDOSIA, CINZA_LINHO,
    MARFIM_OFFWHITE, UI_TEXTO_APAGADO,
    AZUL_HOVER_MENU, AZUL_HOVER_BG
)
from src.utils.resource_manager import ResourceManager
from src.ui.ui_utils import desenhar_painel_padrao
from src.utils import save_storage as save_io

class SettingsState(State):
    """
    Tela de Configurações alinhada à estética Dark Fantasy / Metroidvania:
    - Moldura em Carvão Profundo com contornos delicados em Cinza Linho / Marfim
    - Tipografia consolidada (Sunday para títulos, Contrail One para opções)
    - Navegação intuitiva com teclado e mouse com feedback visual
    - Controle granular e individual de volumes para todas as áreas sonoras:
      * Volume Geral (Master)
      * Volume da Música (BGM)
      * Volume dos Efeitos Sonoros (SFX)
      * Volume do Ambiente (BGS / Clima)
    - Opção de Redefinir Dados com modal de confirmação defensivo (Reset Global de saves e conquistas)
    """
    _MAPA_SLIDERS_VOLUME = {
        2: ("config_audio", "definir_volume_master", 100),
        3: ("config_audio_musica", "definir_volume_musica", 55),
        4: ("config_audio_sfx", "definir_volume_sfx", 95),
        5: ("config_audio_ambiente", "definir_volume_ambiente", 70),
    }

    def __init__(self, game):
        super().__init__(game)
        self.opcoes = [
            "Velocidade do Texto",
            "Velocidade do Combate",
            "Volume Geral (Master)",
            "Volume da Música",
            "Volume dos Efeitos",
            "Volume do Ambiente",
            "Silenciar Tudo (Mute)",
            "Restaurar Padrões",
            "Configurar Teclas...",
            "Redefinir Dados...",
            "Voltar",
        ]
        self.selecionada = 0

        # Estado de interação fina dos sliders de volume
        self.slider_arrastando_idx = None
        self.slider_widgets = {}
        self._preview_ambiente_ativo = False
        
        # Modal de Confirmação de Reset Global
        self.modal_reset_aberto = False
        self.modal_opcao_idx = 1  # 0: Confirmar Reset, 1: Cancelar (default seguro)
        self.rect_btn_confirmar_reset = pygame.Rect(0, 0, 0, 0)
        self.rect_btn_cancelar_reset = pygame.Rect(0, 0, 0, 0)
        self.rect_painel_modal = pygame.Rect(0, 0, 0, 0)
        
        # Tipografia Consolidada
        self.fonte_titulo = ResourceManager.carregar_fonte("sunday", 36)
        self.fonte_opcao = ResourceManager.carregar_fonte("contrail", 22)
        self.fonte_sub = ResourceManager.carregar_fonte("contrail", 16)
        
        self.rects_opcoes = []
        
        # Película escura para sobreposição caso aberto pelo Pause
        self.overlay = pygame.Surface((self.game.LARGURA, self.game.ALTURA))
        self.overlay.fill((10, 10, 12))
        self.overlay.set_alpha(190)
        self.hover_anterior = -1

    def _tocar_sfx(self, alias, cooldown_s=0.0):
        audio = getattr(self.game, "audio", None)
        if not audio:
            return
        if cooldown_s > 0.0 and hasattr(audio, "tocar_sfx_com_cooldown"):
            audio.tocar_sfx_com_cooldown(alias, cooldown_s=cooldown_s)
        else:
            audio.tocar_sfx(alias)

    def _obter_passo_volume(self):
        """Retorna passo padrão de 5% ou ajuste fino de 1% enquanto Shift estiver pressionado."""
        try:
            mods = pygame.key.get_mods() if pygame.get_init() else 0
        except pygame.error:
            mods = 0
        return 1 if (mods & pygame.KMOD_SHIFT) else 5

    def _garantir_preview_ambiente(self):
        """Inicia prévia leve de ambiente ao ajustar BGS no Menu, sem interromper BGS real de cenários."""
        audio = getattr(self.game, "audio", None)
        if not audio:
            return
        canal = getattr(audio, "canal_ambiente", None)
        ja_tocando_algo = bool(getattr(audio, "ambiente_atual", None)) or bool(canal and canal.get_busy())
        if not ja_tocando_algo and hasattr(audio, "tocar_ambiente"):
            audio.tocar_ambiente("vento_suave", loop=-1, fade_ms=250)
            self._preview_ambiente_ativo = True

    def _encerrar_preview_ambiente(self):
        """Encerra apenas a prévia temporária iniciada pelo menu Configurações."""
        if self._preview_ambiente_ativo:
            audio = getattr(self.game, "audio", None)
            if audio and hasattr(audio, "parar_ambiente"):
                audio.parar_ambiente(fade_ms=200)
            self._preview_ambiente_ativo = False

    def _salvar_preferencias(self):
        if hasattr(self.game, "salvar_preferencias_usuario"):
            self.game.salvar_preferencias_usuario()

    def _definir_volume_por_idx(self, idx, novo_valor, salvar=True, tocar_feedback=True):
        """Atualiza atributo do jogo e AudioManager para o canal de índice 2..5."""
        if idx not in self._MAPA_SLIDERS_VOLUME:
            return
        attr, metodo, _padrao = self._MAPA_SLIDERS_VOLUME[idx]
        valor = max(0, min(100, int(round(novo_valor))))
        setattr(self.game, attr, valor)

        audio = getattr(self.game, "audio", None)
        if audio and hasattr(audio, metodo):
            getattr(audio, metodo)(valor)
            if idx == 5:
                self._garantir_preview_ambiente()
            if tocar_feedback:
                self._tocar_sfx("ui_slider", cooldown_s=0.06)

        if salvar:
            self._salvar_preferencias()

    @staticmethod
    def _valor_slider_por_x(rect_track, pos_x):
        largura = max(1, rect_track.width)
        fracao = max(0.0, min(1.0, (pos_x - rect_track.x) / float(largura)))
        return int(round(fracao * 100))

    def _alternar_mute(self):
        novo_mutado = not bool(getattr(self.game, "config_audio_mutado", False))
        self.game.config_audio_mutado = novo_mutado
        audio = getattr(self.game, "audio", None)
        if audio and hasattr(audio, "definir_mute"):
            audio.definir_mute(novo_mutado)
            if not novo_mutado:
                self._tocar_sfx("toggle_on")
        self._salvar_preferencias()

    def _restaurar_padroes(self):
        if hasattr(self.game, "restaurar_padroes_audio"):
            self.game.restaurar_padroes_audio(salvar=True)
        else:
            for attr, _metodo, padrao in self._MAPA_SLIDERS_VOLUME.values():
                setattr(self.game, attr, padrao)
            self.game.config_audio_mutado = False
            self._salvar_preferencias()
        self._tocar_sfx("ui_confirmar")

    def handle_events(self, eventos, teclas):
        # 1. Intercepta eventos se o modal de confirmação de reset estiver aberto
        if self.modal_reset_aberto:
            for evento in eventos:
                if evento.type == pygame.KEYDOWN:
                    if evento.key in [pygame.K_LEFT, pygame.K_a, pygame.K_RIGHT, pygame.K_d, pygame.K_TAB]:
                        self.modal_opcao_idx = 1 - self.modal_opcao_idx
                        self._tocar_sfx("ui_cursor")
                    elif evento.key in [pygame.K_RETURN, pygame.K_SPACE]:
                        self._processar_escolha_modal()
                    elif evento.key == pygame.K_ESCAPE:
                        self._tocar_sfx("ui_voltar")
                        self.modal_reset_aberto = False

                elif evento.type == pygame.MOUSEMOTION:
                    if self.rect_btn_confirmar_reset.collidepoint(evento.pos):
                        self.modal_opcao_idx = 0
                    elif self.rect_btn_cancelar_reset.collidepoint(evento.pos):
                        self.modal_opcao_idx = 1

                elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                    if self.rect_btn_confirmar_reset.collidepoint(evento.pos):
                        self.modal_opcao_idx = 0
                        self._processar_escolha_modal()
                    elif self.rect_btn_cancelar_reset.collidepoint(evento.pos):
                        self.modal_opcao_idx = 1
                        self._processar_escolha_modal()
                    elif not self.rect_painel_modal.collidepoint(evento.pos):
                        self._tocar_sfx("ui_voltar")
                        self.modal_reset_aberto = False
            return

        for evento in eventos:
            if evento.type == pygame.KEYDOWN:
                if evento.key in [pygame.K_UP, pygame.K_w]:
                    self.selecionada = (self.selecionada - 1) % len(self.opcoes)
                    self._tocar_sfx("ui_cursor")
                elif evento.key in [pygame.K_DOWN, pygame.K_s]:
                    self.selecionada = (self.selecionada + 1) % len(self.opcoes)
                    self._tocar_sfx("ui_cursor")
                elif evento.key in [pygame.K_LEFT, pygame.K_a]:
                    self.alterar_valor(-1)
                elif evento.key in [pygame.K_RIGHT, pygame.K_d]:
                    self.alterar_valor(1)
                elif evento.key == pygame.K_m:
                    self._alternar_mute()
                elif evento.key == pygame.K_r:
                    self._restaurar_padroes()
                elif evento.key in [pygame.K_RETURN, pygame.K_SPACE, pygame.K_e]:
                    self.executar_acao()
                elif evento.key == pygame.K_ESCAPE:
                    self._encerrar_preview_ambiente()
                    self._tocar_sfx("ui_voltar")
                    self.voltar_origem()

            elif evento.type == pygame.MOUSEWHEEL:
                if self.selecionada in self._MAPA_SLIDERS_VOLUME and evento.y != 0:
                    self.alterar_valor(1 if evento.y > 0 else -1)

            elif evento.type == pygame.MOUSEMOTION:
                if self.slider_arrastando_idx is not None:
                    widget = self.slider_widgets.get(self.slider_arrastando_idx)
                    if widget:
                        val = self._valor_slider_por_x(widget["track"], evento.pos[0])
                        self._definir_volume_por_idx(self.slider_arrastando_idx, val, salvar=False)
                else:
                    for i, rect in enumerate(self.rects_opcoes):
                        if rect.collidepoint(evento.pos):
                            if self.hover_anterior != i:
                                self.hover_anterior = i
                                self.selecionada = i
                                self._tocar_sfx("ui_cursor")
                            break

            elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                for i, rect in enumerate(self.rects_opcoes):
                    if rect.collidepoint(evento.pos):
                        self.selecionada = i
                        if i in self._MAPA_SLIDERS_VOLUME:
                            widget = self.slider_widgets.get(i)
                            if widget and widget["btn_menos"].collidepoint(evento.pos):
                                self.alterar_valor(-1)
                            elif widget and widget["btn_mais"].collidepoint(evento.pos):
                                self.alterar_valor(1)
                            elif widget and widget["track_hit"].collidepoint(evento.pos):
                                self.slider_arrastando_idx = i
                                val = self._valor_slider_por_x(widget["track"], evento.pos[0])
                                self._definir_volume_por_idx(i, val, salvar=True)
                            else:
                                self.alterar_valor(-1 if evento.pos[0] < rect.centerx else 1)
                        elif i in (0, 1):
                            self.alterar_valor(-1 if evento.pos[0] < rect.centerx else 1)
                        else:
                            self.executar_acao()
                        break

            elif evento.type == pygame.MOUSEBUTTONUP and evento.button == 1:
                if self.slider_arrastando_idx is not None:
                    self.slider_arrastando_idx = None
                    self._salvar_preferencias()

    def alterar_valor(self, direcao):
        # 0: Velocidade do Texto
        if self.selecionada == 0:
            self.game.config_velocidade_indice = (self.game.config_velocidade_indice + direcao) % len(self.game.opcoes_velocidade)
            novo_valor = self.game.valores_velocidade[self.game.config_velocidade_indice]
            self.game.caixa_dialogo.velocidade_texto = novo_valor
            self._tocar_sfx("ui_slider")
            self._salvar_preferencias()

        # 1: Velocidade do Combate
        elif self.selecionada == 1:
            self.game.config_velocidade_combate_indice = (self.game.config_velocidade_combate_indice + direcao) % len(self.game.opcoes_velocidade_combate)
            novo_fator = self.game.valores_velocidade_combate[self.game.config_velocidade_combate_indice]
            self.game.tela_combate.definir_velocidade(novo_fator)
            self._tocar_sfx("ui_slider")
            self._salvar_preferencias()

        # 2..5: Volumes por canal (passo de 5%, ou 1% com Shift)
        elif self.selecionada in self._MAPA_SLIDERS_VOLUME:
            attr, _metodo, padrao = self._MAPA_SLIDERS_VOLUME[self.selecionada]
            atual = getattr(self.game, attr, padrao)
            passo = self._obter_passo_volume()
            self._definir_volume_por_idx(self.selecionada, atual + (direcao * passo), salvar=True)

        # 6: Mute global
        elif self.selecionada == 6:
            self._alternar_mute()

    def executar_acao(self):
        opcao = self.opcoes[self.selecionada]
        if opcao == "Silenciar Tudo (Mute)":
            self._alternar_mute()
        elif opcao == "Restaurar Padrões":
            self._restaurar_padroes()
        elif opcao == "Configurar Teclas...":
            self._encerrar_preview_ambiente()
            self._tocar_sfx("ui_confirmar")
            self.game.mudar_estado("CONTROLES")
        elif opcao == "Redefinir Dados...":
            self._tocar_sfx("ui_cursor")
            self.modal_reset_aberto = True
            self.modal_opcao_idx = 1  # Inicia no Cancelar por segurança
        elif opcao in ["Voltar", "Voltar ao Menu", "Voltar ao Jogo"]:
            self._encerrar_preview_ambiente()
            self._tocar_sfx("ui_voltar")
            self.voltar_origem()
        else:
            # Pressionar ENTER em opções de valor avança o item
            self.alterar_valor(1)

    def _processar_escolha_modal(self):
        """Executa a decisão do jogador no modal de redefinição de dados."""
        if self.modal_opcao_idx == 0:
            # Confirmar Reset: Apaga todos os saves (1 a 4) e reseta conquistas
            for s in range(1, 5):
                save_io.apagar_dados(s, "ambos")

            if hasattr(self.game, 'conquistas') and self.game.conquistas:
                self.game.conquistas.resetar_todas_conquistas()

            if hasattr(self.game, 'menu') and hasattr(self.game.menu, 'atualizar_opcoes'):
                self.game.menu.atualizar_opcoes()

            self.game.slot_atual = None

            if hasattr(self.game, 'notificacoes') and self.game.notificacoes:
                self.game.notificacoes.notificar(
                    "notificacao_alerta",
                    titulo="Dados Redefinidos",
                    mensagem="Todos os saves e conquistas foram apagados com sucesso.",
                    tipo="SISTEMA"
                )

            self._tocar_sfx("ui_confirmar")
            self.modal_reset_aberto = False
        else:
            # Cancelar Reset
            self._tocar_sfx("ui_voltar")
            self.modal_reset_aberto = False

    def voltar_origem(self):
        self.slider_arrastando_idx = None
        self._encerrar_preview_ambiente()
        if getattr(self.game, 'origem_configuracoes', 'MENU') == "PAUSE":
            self.game.mudar_estado("PAUSE")
        else:
            self.game.mudar_estado("MENU")

    def update(self):
        if getattr(self.game, 'origem_configuracoes', 'MENU') == "MENU":
            if hasattr(self.game, 'menu') and hasattr(self.game.menu, 'efeito_petalas'):
                dt = self.game.clock.get_time() / 1000.0 if hasattr(self.game, 'clock') else 0.016
                dt = min(dt, 0.05) if dt > 0 else 0.016
                self.game.menu.efeito_petalas.atualizar(dt)

    def _desenhar_slider_volume(self, tela, indice, rect_opt, pct_volume, esta_sel, mutado):
        """Desenha botões [-]/[+], trilha clicável, knob arrastável e percentual de volume."""
        slot_pct_w = 54
        btn_w, btn_h = 24, 24
        track_w, track_h = 186, 8
        gap = 8

        slot_pct_x = rect_opt.right - 16 - slot_pct_w
        btn_mais_x = slot_pct_x - gap - btn_w
        track_x = btn_mais_x - gap - track_w
        btn_menos_x = track_x - gap - btn_w

        cy = rect_opt.centery
        rect_menos = pygame.Rect(btn_menos_x, cy - btn_h // 2, btn_w, btn_h)
        rect_track = pygame.Rect(track_x, cy - track_h // 2, track_w, track_h)
        rect_mais = pygame.Rect(btn_mais_x, cy - btn_h // 2, btn_w, btn_h)

        self.slider_widgets[indice] = {
            "track": rect_track,
            "track_hit": rect_track.inflate(8, 20),
            "btn_menos": rect_menos,
            "btn_mais": rect_mais,
        }

        cor_btn_bg = (30, 34, 44) if esta_sel else (22, 24, 30)
        cor_btn_borda = AZUL_HOVER_MENU if esta_sel else (58, 62, 74)
        cor_btn_txt = MARFIM_OFFWHITE if esta_sel else CINZA_LINHO

        for rect_b, simbolo in ((rect_menos, "-"), (rect_mais, "+")):
            pygame.draw.rect(tela, cor_btn_bg, rect_b, border_radius=3)
            pygame.draw.rect(tela, cor_btn_borda, rect_b, 1, border_radius=3)
            rend_s = self.fonte_sub.render(simbolo, True, cor_btn_txt)
            tela.blit(rend_s, (rect_b.centerx - rend_s.get_width() // 2, rect_b.centery - rend_s.get_height() // 2))

        pygame.draw.rect(tela, (18, 20, 26), rect_track, border_radius=4)
        pygame.draw.rect(tela, (55, 60, 72), rect_track, 1, border_radius=4)

        fracao = max(0.0, min(1.0, pct_volume / 100.0))
        largura_preenchida = int((track_w - 2) * fracao)
        if mutado:
            cor_barra = (95, 98, 108)
        elif esta_sel or self.slider_arrastando_idx == indice:
            cor_barra = AZUL_HOVER_MENU
        else:
            cor_barra = (85, 120, 155)

        if largura_preenchida > 0:
            rect_preenchido = pygame.Rect(rect_track.x + 1, rect_track.y + 1, largura_preenchida, track_h - 2)
            pygame.draw.rect(tela, cor_barra, rect_preenchido, border_radius=3)

        knob_x = rect_track.x + int((track_w - 2) * fracao)
        knob_r = 7 if (esta_sel or self.slider_arrastando_idx == indice) else 5
        pygame.draw.circle(tela, cor_barra, (knob_x, cy), knob_r)
        pygame.draw.circle(tela, MARFIM_OFFWHITE if not mutado else CINZA_LINHO, (knob_x, cy), knob_r, 1)

        cor_pct = (135, 138, 148) if mutado else (MARFIM_OFFWHITE if esta_sel else CINZA_LINHO)
        rend_pct = self.fonte_opcao.render(f"{pct_volume}%", True, cor_pct)
        tela.blit(rend_pct, (slot_pct_x + slot_pct_w - rend_pct.get_width(), cy - rend_pct.get_height() // 2))

    def draw(self, tela):
        if getattr(self.game, 'origem_configuracoes', 'MENU') == "PAUSE":
            origem = getattr(self.game, 'origem_pause', 'JOGANDO')
            if origem == "COMBATE" and "COMBATE" in self.game.estados:
                self.game.estados["COMBATE"].draw(tela)
            elif "JOGANDO" in self.game.estados:
                self.game.estados["JOGANDO"].draw(tela)
            tela.blit(self.overlay, (0, 0))
        else:
            tela.fill(PRETO)
            if hasattr(self.game, 'menu') and hasattr(self.game.menu, 'efeito_petalas'):
                self.game.menu.efeito_petalas.desenhar(tela)
        
        largura_bloco = 780
        altura_bloco = 604
        x = (self.game.LARGURA - largura_bloco) // 2
        y = (self.game.ALTURA - altura_bloco) // 2

        rect_painel = pygame.Rect(x, y, largura_bloco, altura_bloco)
        desenhar_painel_padrao(tela, rect_painel, cor_fundo=CARVAO_PROFUNDO, cor_borda=CINZA_LINHO, alpha=245)

        # Moldura interna decorativa
        rect_interno = rect_painel.inflate(-10, -10)
        pygame.draw.rect(tela, (28, 28, 34), rect_interno, 1, border_radius=2)

        # Título
        titulo = self.fonte_titulo.render("Configurações", True, MARFIM_OFFWHITE)
        tela.blit(titulo, (x + 45, y + 18))

        # Divisória elegante
        pygame.draw.line(tela, CINZA_ARDOSIA, (x + 40, y + 60), (x + largura_bloco - 40, y + 60), 1)

        vel_texto = self.game.opcoes_velocidade[self.game.config_velocidade_indice]
        vel_combate = self.game.opcoes_velocidade_combate[self.game.config_velocidade_combate_indice]
        audio_master = getattr(self.game, 'config_audio', 100)
        audio_musica = getattr(self.game, 'config_audio_musica', 55)
        audio_sfx = getattr(self.game, 'config_audio_sfx', 95)
        audio_ambiente = getattr(self.game, 'config_audio_ambiente', 70)
        mutado = bool(getattr(self.game, 'config_audio_mutado', False)) or bool(
            getattr(getattr(self.game, 'audio', None), 'mutado', False)
        )

        texto_voltar = "Voltar ao Jogo" if getattr(self.game, 'origem_configuracoes', 'MENU') == "PAUSE" else "Voltar ao Menu"
        texto_mute = "< Ativado [M] >" if mutado else "< Desativado [M] >"

        dados_opcoes = [
            ("Velocidade do Texto", f"< {vel_texto} >", None),
            ("Velocidade do Combate", f"< {vel_combate} >", None),
            ("Volume Geral (Master)", f"{audio_master}%", audio_master),
            ("Volume da Música", f"{audio_musica}%", audio_musica),
            ("Volume dos Efeitos", f"{audio_sfx}%", audio_sfx),
            ("Volume do Ambiente", f"{audio_ambiente}%", audio_ambiente),
            ("Silenciar Tudo (Mute)", texto_mute, None),
            ("Restaurar Padrões", "[R] Mix Padrão", None),
            ("Configurar Teclas...", "", None),
            ("Redefinir Dados...", "", None),
            (texto_voltar, "", None),
        ]

        self.rects_opcoes.clear()
        self.slider_widgets.clear()
        espacamento_opt = 44
        for i, (nome_opcao, valor_texto, pct_volume) in enumerate(dados_opcoes):
            esta_sel = (i == self.selecionada)
            pos_x = x + 36
            pos_y = y + 70 + (i * espacamento_opt)
            
            rect_opt = pygame.Rect(pos_x, pos_y, largura_bloco - 72, 36)
            self.rects_opcoes.append(rect_opt)
            
            if esta_sel:
                pygame.draw.rect(tela, AZUL_HOVER_BG, rect_opt, border_radius=3)
                pygame.draw.rect(tela, AZUL_HOVER_MENU, rect_opt, 1, border_radius=3)
                cor_texto = (245, 120, 120) if nome_opcao == "Redefinir Dados..." else MARFIM_OFFWHITE
                texto_prefixo = "✦  "
            else:
                cor_texto = (185, 115, 115) if nome_opcao == "Redefinir Dados..." else CINZA_LINHO
                texto_prefixo = "   "
                
            render_nome = self.fonte_opcao.render(f"{texto_prefixo}{nome_opcao}", True, cor_texto)
            tela.blit(render_nome, (pos_x + 14, rect_opt.centery - render_nome.get_height() // 2))

            # Exibe controle à direita
            if pct_volume is not None:
                self._desenhar_slider_volume(tela, i, rect_opt, pct_volume, esta_sel, mutado)
            elif valor_texto:
                if nome_opcao == "Silenciar Tudo (Mute)" and mutado:
                    cor_val = (235, 165, 95)
                elif nome_opcao == "Restaurar Padrões" and not esta_sel:
                    cor_val = UI_TEXTO_APAGADO
                else:
                    cor_val = MARFIM_OFFWHITE if esta_sel else CINZA_LINHO
                render_val = self.fonte_opcao.render(valor_texto, True, cor_val)
                val_x = rect_opt.right - 16 - render_val.get_width()
                tela.blit(render_val, (val_x, rect_opt.centery - render_val.get_height() // 2))

        # Rodapé elegante com atalhos
        txt_rodape = self.fonte_sub.render(
            "[← / → / Arraste / Roda] Ajustar   •   [M] Mute   •   [R] Padrões   •   [ESC] Voltar",
            True,
            UI_TEXTO_APAGADO,
        )
        tela.blit(txt_rodape, (x + (largura_bloco - txt_rodape.get_width()) // 2, y + altura_bloco - 24))

        # 2. Desenha o Modal de Confirmação Defensivo se estiver ativo
        if self.modal_reset_aberto:
            self._desenhar_modal_reset(tela)

    def _desenhar_modal_reset(self, tela):
        """Renderiza a janela modal de confirmação defensiva para redefinição de dados."""
        # 1. Película escura cobrindo a tela
        overlay_modal = pygame.Surface((self.game.LARGURA, self.game.ALTURA), pygame.SRCALPHA)
        overlay_modal.fill((0, 0, 0, 190))
        tela.blit(overlay_modal, (0, 0))

        # 2. Painel Central do Modal
        w_modal = 580
        h_modal = 250
        x_m = (self.game.LARGURA - w_modal) // 2
        y_m = (self.game.ALTURA - h_modal) // 2

        self.rect_painel_modal = pygame.Rect(x_m, y_m, w_modal, h_modal)
        desenhar_painel_padrao(tela, self.rect_painel_modal, cor_fundo=CARVAO_PROFUNDO, cor_borda=(190, 65, 65), alpha=252)

        # Moldura interna
        rect_int_modal = self.rect_painel_modal.inflate(-8, -8)
        pygame.draw.rect(tela, (45, 20, 24), rect_int_modal, 1, border_radius=2)

        # Título de Advertência
        tit_modal = self.fonte_opcao.render("⚠  REDEFINIR TODOS OS DADOS  ⚠", True, (240, 95, 95))
        tela.blit(tit_modal, (x_m + (w_modal - tit_modal.get_width()) // 2, y_m + 24))

        # Mensagens explicativas
        msg1 = "Deseja apagar todos os 4 slots de salvamento e restaurar"
        msg2 = "todas as conquistas desbloqueadas para o estado inicial?"
        msg3 = "Esta ação é definitiva e não poderá ser desfeita."

        r_msg1 = self.fonte_sub.render(msg1, True, MARFIM_OFFWHITE)
        r_msg2 = self.fonte_sub.render(msg2, True, MARFIM_OFFWHITE)
        r_msg3 = self.fonte_sub.render(msg3, True, (220, 145, 145))

        tela.blit(r_msg1, (x_m + (w_modal - r_msg1.get_width()) // 2, y_m + 68))
        tela.blit(r_msg2, (x_m + (w_modal - r_msg2.get_width()) // 2, y_m + 92))
        tela.blit(r_msg3, (x_m + (w_modal - r_msg3.get_width()) // 2, y_m + 124))

        # Botões do Modal
        btn_w = 175
        btn_h = 38
        gap_btn = 30
        y_btn = y_m + h_modal - 58

        x_confirmar = x_m + (w_modal - (2 * btn_w + gap_btn)) // 2
        x_cancelar = x_confirmar + btn_w + gap_btn

        self.rect_btn_confirmar_reset = pygame.Rect(x_confirmar, y_btn, btn_w, btn_h)
        self.rect_btn_cancelar_reset = pygame.Rect(x_cancelar, y_btn, btn_w, btn_h)

        # Botão 0: Confirmar Reset (Vermelho Alerta)
        sel_conf = (self.modal_opcao_idx == 0)
        if sel_conf:
            pygame.draw.rect(tela, (130, 30, 35), self.rect_btn_confirmar_reset, border_radius=3)
            pygame.draw.rect(tela, (230, 80, 80), self.rect_btn_confirmar_reset, 1, border_radius=3)
            cor_txt_conf = MARFIM_OFFWHITE
        else:
            pygame.draw.rect(tela, (40, 18, 22), self.rect_btn_confirmar_reset, border_radius=3)
            pygame.draw.rect(tela, (90, 35, 40), self.rect_btn_confirmar_reset, 1, border_radius=3)
            cor_txt_conf = (200, 150, 150)

        rend_conf = self.fonte_sub.render("Confirmar Reset", True, cor_txt_conf)
        tela.blit(rend_conf, (self.rect_btn_confirmar_reset.centerx - rend_conf.get_width() // 2, self.rect_btn_confirmar_reset.centery - rend_conf.get_height() // 2))

        # Botão 1: Cancelar (Neutro / Azul de Foco)
        sel_canc = (self.modal_opcao_idx == 1)
        if sel_canc:
            pygame.draw.rect(tela, AZUL_HOVER_BG, self.rect_btn_cancelar_reset, border_radius=3)
            pygame.draw.rect(tela, AZUL_HOVER_MENU, self.rect_btn_cancelar_reset, 1, border_radius=3)
            cor_txt_canc = MARFIM_OFFWHITE
        else:
            pygame.draw.rect(tela, (22, 24, 30), self.rect_btn_cancelar_reset, border_radius=3)
            pygame.draw.rect(tela, (50, 54, 66), self.rect_btn_cancelar_reset, 1, border_radius=3)
            cor_txt_canc = CINZA_LINHO

        rend_canc = self.fonte_sub.render("Cancelar", True, cor_txt_canc)
        tela.blit(rend_canc, (self.rect_btn_cancelar_reset.centerx - rend_canc.get_width() // 2, self.rect_btn_cancelar_reset.centery - rend_canc.get_height() // 2))