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
    """
    def __init__(self, game):
        super().__init__(game)
        self.opcoes = [
            "Velocidade do Texto", 
            "Velocidade do Combate", 
            "Volume Geral (Master)", 
            "Volume da Música",
            "Volume dos Efeitos",
            "Volume do Ambiente",
            "Configurar Teclas...", 
            "Voltar"
        ]
        self.selecionada = 0
        
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

    def _tocar_sfx(self, alias):
        if hasattr(self.game, 'audio') and self.game.audio:
            self.game.audio.tocar_sfx(alias)

    def handle_events(self, eventos, teclas):
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
                elif evento.key in [pygame.K_RETURN, pygame.K_SPACE, pygame.K_e]:
                    self.executar_acao()
                elif evento.key == pygame.K_ESCAPE:
                    self._tocar_sfx("ui_voltar")
                    self.voltar_origem()
                    
            elif evento.type == pygame.MOUSEMOTION:
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
                        if i in [0, 1, 2, 3, 4, 5]:
                            # Clique no lado esquerdo do retângulo diminui; lado direito aumenta
                            if evento.pos[0] < rect.centerx:
                                self.alterar_valor(-1)
                            else:
                                self.alterar_valor(1)
                        else:
                            self.executar_acao()

    def alterar_valor(self, direcao):
        # 0: Velocidade do Texto
        if self.selecionada == 0:
            self.game.config_velocidade_indice = (self.game.config_velocidade_indice + direcao) % len(self.game.opcoes_velocidade)
            novo_valor = self.game.valores_velocidade[self.game.config_velocidade_indice]
            self.game.caixa_dialogo.velocidade_texto = novo_valor
            self._tocar_sfx("ui_cursor")

        # 1: Velocidade do Combate
        elif self.selecionada == 1:
            self.game.config_velocidade_combate_indice = (self.game.config_velocidade_combate_indice + direcao) % len(self.game.opcoes_velocidade_combate)
            novo_fator = self.game.valores_velocidade_combate[self.game.config_velocidade_combate_indice]
            self.game.tela_combate.definir_velocidade(novo_fator)
            self._tocar_sfx("ui_cursor")

        # 2: Volume Geral (Master)
        elif self.selecionada == 2:
            self.game.config_audio = max(0, min(100, getattr(self.game, 'config_audio', 100) + (direcao * 10)))
            if hasattr(self.game, 'audio') and self.game.audio:
                self.game.audio.definir_volume_master(self.game.config_audio)
                self.game.audio.tocar_sfx("ui_confirmar")

        # 3: Volume da Música (BGM)
        elif self.selecionada == 3:
            self.game.config_audio_musica = max(0, min(100, getattr(self.game, 'config_audio_musica', 80) + (direcao * 10)))
            if hasattr(self.game, 'audio') and self.game.audio:
                self.game.audio.definir_volume_musica(self.game.config_audio_musica)
                self.game.audio.tocar_sfx("ui_confirmar")

        # 4: Volume dos Efeitos Sonoros (SFX)
        elif self.selecionada == 4:
            self.game.config_audio_sfx = max(0, min(100, getattr(self.game, 'config_audio_sfx', 90) + (direcao * 10)))
            if hasattr(self.game, 'audio') and self.game.audio:
                self.game.audio.definir_volume_sfx(self.game.config_audio_sfx)
                self.game.audio.tocar_sfx("ui_confirmar")

        # 5: Volume dos Sons de Ambiente (BGS)
        elif self.selecionada == 5:
            self.game.config_audio_ambiente = max(0, min(100, getattr(self.game, 'config_audio_ambiente', 75) + (direcao * 10)))
            if hasattr(self.game, 'audio') and self.game.audio:
                self.game.audio.definir_volume_ambiente(self.game.config_audio_ambiente)
                self.game.audio.tocar_sfx("ui_confirmar")

    def executar_acao(self):
        opcao = self.opcoes[self.selecionada]
        if opcao == "Configurar Teclas...":
            self._tocar_sfx("ui_confirmar")
            self.game.mudar_estado("CONTROLES")
        elif opcao in ["Voltar", "Voltar ao Menu", "Voltar ao Jogo"]:
            self._tocar_sfx("ui_voltar")
            self.voltar_origem()
        else:
            # Pressionar ENTER em opções de valor avança o item
            self.alterar_valor(1)

    def voltar_origem(self):
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
        
        largura_bloco = 760
        altura_bloco = 560
        x = (self.game.LARGURA - largura_bloco) // 2
        y = (self.game.ALTURA - altura_bloco) // 2

        rect_painel = pygame.Rect(x, y, largura_bloco, altura_bloco)
        desenhar_painel_padrao(tela, rect_painel, cor_fundo=CARVAO_PROFUNDO, cor_borda=CINZA_LINHO, alpha=245)

        # Moldura interna decorativa
        rect_interno = rect_painel.inflate(-10, -10)
        pygame.draw.rect(tela, (28, 28, 34), rect_interno, 1, border_radius=2)

        # Título
        titulo = self.fonte_titulo.render("Configurações", True, MARFIM_OFFWHITE)
        tela.blit(titulo, (x + 45, y + 24))

        # Divisória elegante
        pygame.draw.line(tela, CINZA_ARDOSIA, (x + 40, y + 66), (x + largura_bloco - 40, y + 66), 1)

        vel_texto = self.game.opcoes_velocidade[self.game.config_velocidade_indice]
        vel_combate = self.game.opcoes_velocidade_combate[self.game.config_velocidade_combate_indice]
        audio_master = getattr(self.game, 'config_audio', 100)
        audio_musica = getattr(self.game, 'config_audio_musica', 80)
        audio_sfx = getattr(self.game, 'config_audio_sfx', 90)
        audio_ambiente = getattr(self.game, 'config_audio_ambiente', 75)
        
        texto_voltar = "Voltar ao Jogo" if getattr(self.game, 'origem_configuracoes', 'MENU') == "PAUSE" else "Voltar ao Menu"

        dados_opcoes = [
            ("Velocidade do Texto", f"< {vel_texto} >", None),
            ("Velocidade do Combate", f"< {vel_combate} >", None),
            ("Volume Geral (Master)", f"< {audio_master}% >", audio_master),
            ("Volume da Música", f"< {audio_musica}% >", audio_musica),
            ("Volume dos Efeitos", f"< {audio_sfx}% >", audio_sfx),
            ("Volume do Ambiente", f"< {audio_ambiente}% >", audio_ambiente),
            ("Configurar Teclas...", "", None),
            (texto_voltar, "", None)
        ]

        self.rects_opcoes.clear()
        for i, (nome_opcao, valor_texto, pct_volume) in enumerate(dados_opcoes):
            esta_sel = (i == self.selecionada)
            pos_x = x + 40
            pos_y = y + 76 + (i * 53)
            
            rect_opt = pygame.Rect(pos_x, pos_y, largura_bloco - 80, 40)
            self.rects_opcoes.append(rect_opt)
            
            if esta_sel:
                pygame.draw.rect(tela, AZUL_HOVER_BG, rect_opt, border_radius=3)
                pygame.draw.rect(tela, AZUL_HOVER_MENU, rect_opt, 1, border_radius=3)
                cor_texto = MARFIM_OFFWHITE
                texto_prefixo = "✦  "
            else:
                cor_texto = CINZA_LINHO
                texto_prefixo = "   "
                
            render_nome = self.fonte_opcao.render(f"{texto_prefixo}{nome_opcao}", True, cor_texto)
            tela.blit(render_nome, (pos_x + 16, rect_opt.centery - render_nome.get_height() // 2))

            # Exibe o valor à direita
            if valor_texto:
                cor_val = MARFIM_OFFWHITE if esta_sel else CINZA_LINHO
                render_val = self.fonte_opcao.render(valor_texto, True, cor_val)
                val_x = rect_opt.right - 18 - render_val.get_width()
                tela.blit(render_val, (val_x, rect_opt.centery - render_val.get_height() // 2))

                # Mini barra medidora animada/estilizada para opções de volume
                if pct_volume is not None:
                    gauge_w = 90
                    gauge_h = 8
                    gauge_x = val_x - gauge_w - 14
                    gauge_y = rect_opt.centery - gauge_h // 2
                    
                    # Trilho de fundo
                    rect_gauge_bg = pygame.Rect(gauge_x, gauge_y, gauge_w, gauge_h)
                    pygame.draw.rect(tela, (20, 22, 28), rect_gauge_bg, border_radius=2)
                    pygame.draw.rect(tela, (50, 54, 66), rect_gauge_bg, 1, border_radius=2)
                    
                    # Preenchimento ativo
                    if pct_volume > 0:
                        largura_preenchida = int((gauge_w - 2) * (pct_volume / 100.0))
                        cor_barra = AZUL_HOVER_MENU if esta_sel else (85, 120, 155)
                        rect_preenchido = pygame.Rect(gauge_x + 1, gauge_y + 1, largura_preenchida, gauge_h - 2)
                        pygame.draw.rect(tela, cor_barra, rect_preenchido, border_radius=1)

        # Rodapé elegante com atalhos
        txt_rodape = self.fonte_sub.render("[← / → / Clique] Ajustar   •   [ENTER] Confirmar   •   [ESC] Retornar", True, UI_TEXTO_APAGADO)
        tela.blit(txt_rodape, (x + (largura_bloco - txt_rodape.get_width()) // 2, y + altura_bloco - 26))