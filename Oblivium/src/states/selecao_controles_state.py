# src/states/selecao_controles_state.py
import pygame
from src.states.states import State
from src.utils.colors import (
    PRETO, CARVAO_PROFUNDO, CINZA_LINHO,
    MARFIM_OFFWHITE, UI_TEXTO_APAGADO, DOURADO_ENVELHECIDO,
    AZUL_HOVER_MENU, AZUL_HOVER_BG, AZUL_HOVER_BORDA
)
from src.utils.resource_manager import ResourceManager
from src.utils.animations import EfeitoPetalas
from src.ui.ui_utils import desenhar_painel_padrao

class SelecaoControlesState(State):
    """
    Tela de Seleção de Esquema de Controles apresentada antes de iniciar um novo jogo:
    - Oferece escolha clara entre o 'Padrão WASD' (recomendado) e o 'Padrão Setinhas'.
    - Apresenta diagrama visual das teclas, comandos de interação, corrida e inventário [TAB].
    - Suporta navegação fluida por Teclado (Setas/A-D/Enter) e Mouse (hover/clique).
    """
    def __init__(self, game):
        super().__init__(game)
        self.selecionada = 0  # 0: WASD, 1: SETINHAS
        self.hover_mouse = -1
        self.modo_teclado = False
        
        # Tipografia temática
        self.fonte_titulo = ResourceManager.carregar_fonte("sunday", 38)
        self.fonte_sub = ResourceManager.carregar_fonte("contrail", 18)
        self.fonte_card_titulo = ResourceManager.carregar_fonte("sunday", 24)
        self.fonte_tecla = ResourceManager.carregar_fonte("contrail", 18)
        self.fonte_desc = ResourceManager.carregar_fonte("contrail", 15)
        self.fonte_rodape = ResourceManager.carregar_fonte("contrail", 14)

        # Sistema de partículas de pétalas caindo ao fundo (mesmo estilo do Menu)
        self.efeito_petalas = EfeitoPetalas(self.game.LARGURA, self.game.ALTURA, quantidade_petalas=22)

        # Retângulos interativos dos dois cartões
        self.largura_card = 420
        self.altura_card = 410
        self.espacamento_x = 50

        total_largura = (self.largura_card * 2) + self.espacamento_x
        self.inicio_x = (self.game.LARGURA - total_largura) // 2
        self.pos_y = 175

        self.rect_card_wasd = pygame.Rect(self.inicio_x, self.pos_y, self.largura_card, self.altura_card)
        self.rect_card_setas = pygame.Rect(self.inicio_x + self.largura_card + self.espacamento_x, self.pos_y, self.largura_card, self.altura_card)
        
        # Botões de confirmação dentro dos cards
        self.rect_btn_wasd = pygame.Rect(self.rect_card_wasd.x + 40, self.rect_card_wasd.bottom - 60, self.largura_card - 80, 42)
        self.rect_btn_setas = pygame.Rect(self.rect_card_setas.x + 40, self.rect_card_setas.bottom - 60, self.largura_card - 80, 42)

    def handle_events(self, eventos, teclas):
        for evento in eventos:
            if evento.type == pygame.KEYDOWN:
                if evento.key in [pygame.K_LEFT, pygame.K_a, pygame.K_1]:
                    self.selecionada = 0
                    self.hover_mouse = -1
                    self.modo_teclado = True
                elif evento.key in [pygame.K_RIGHT, pygame.K_d, pygame.K_2]:
                    self.selecionada = 1
                    self.hover_mouse = -1
                    self.modo_teclado = True
                elif evento.key in [pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE]:
                    self.confirmar_escolha()
                elif evento.key == pygame.K_ESCAPE:
                    self.voltar_menu()

            elif evento.type == pygame.MOUSEMOTION:
                pos = evento.pos
                self.modo_teclado = False
                if self.rect_card_wasd.collidepoint(pos):
                    self.selecionada = 0
                    self.hover_mouse = 0
                elif self.rect_card_setas.collidepoint(pos):
                    self.selecionada = 1
                    self.hover_mouse = 1
                else:
                    self.hover_mouse = -1

            elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                pos = evento.pos
                if self.rect_card_wasd.collidepoint(pos):
                    self.selecionada = 0
                    self.confirmar_escolha()
                elif self.rect_card_setas.collidepoint(pos):
                    self.selecionada = 1
                    self.confirmar_escolha()

    def confirmar_escolha(self):
        """Aplica o preset de controles escolhido e avança para a seleção de saves."""
        tipo_preset = "WASD" if self.selecionada == 0 else "SETINHAS"
        self.game.aplicar_preset_controles(tipo_preset)

        # Prossegue para a criação de novo jogo nos slots
        self.game.acao_slots = "NOVO_JOGO"
        self.game.origem_slots = "MENU"
        self.game.mudar_estado("SLOTS")

    def voltar_menu(self):
        """Retorna ao Menu Inicial."""
        self.game.mudar_estado("MENU")

    def update(self):
        dt = self.game.clock.get_time() / 1000.0 if hasattr(self.game, 'clock') else 0.016
        dt = min(dt, 0.05) if dt > 0 else 0.016
        self.efeito_petalas.atualizar(dt)

    def _desenhar_tecla(self, tela, texto, x, y, largura=36, altura=36, ativo=False):
        """Desenha uma tecla estilizada estilo botão mecânico/painel dark fantasy."""
        rect_tecla = pygame.Rect(x, y, largura, altura)
        cor_fundo = (32, 44, 62) if ativo else (20, 22, 28)
        cor_borda = AZUL_HOVER_MENU if ativo else CINZA_LINHO
        cor_txt = MARFIM_OFFWHITE if ativo else (210, 205, 198)

        pygame.draw.rect(tela, cor_fundo, rect_tecla, border_radius=4)
        pygame.draw.rect(tela, cor_borda, rect_tecla, 1, border_radius=4)

        txt_surf = self.fonte_tecla.render(texto, True, cor_txt)
        tela.blit(txt_surf, txt_surf.get_rect(center=rect_tecla.center))
        return rect_tecla

    def draw(self, tela):
        # 1. Fundo Preto com Pétalas Etéreas
        tela.fill(PRETO)
        self.efeito_petalas.desenhar(tela)

        # 2. Cabeçalho Principal
        txt_titulo = self.fonte_titulo.render("Como Deseja Jogar?", True, MARFIM_OFFWHITE)
        tela.blit(txt_titulo, txt_titulo.get_rect(center=(self.game.LARGURA // 2, 70)))

        txt_sub = self.fonte_sub.render("Escolha o esquema de controles ideal para sua experiência no Oblivium", True, DOURADO_ENVELHECIDO)
        tela.blit(txt_sub, txt_sub.get_rect(center=(self.game.LARGURA // 2, 115)))

        # 3. Card 1: PADRÃO WASD
        ativo_wasd = (self.hover_mouse == 0) or (self.modo_teclado and self.selecionada == 0)
        cor_borda_wasd = AZUL_HOVER_BORDA if ativo_wasd else CINZA_LINHO
        cor_fundo_wasd = (16, 24, 36) if ativo_wasd else CARVAO_PROFUNDO
        desenhar_painel_padrao(tela, self.rect_card_wasd, cor_fundo=cor_fundo_wasd, cor_borda=cor_borda_wasd, largura_borda=2 if ativo_wasd else 1, alpha=245)

        # Título do Card WASD
        cor_tit_wasd = AZUL_HOVER_MENU if ativo_wasd else MARFIM_OFFWHITE
        txt_c1 = self.fonte_card_titulo.render("Padrão WASD", True, cor_tit_wasd)
        tela.blit(txt_c1, txt_c1.get_rect(center=(self.rect_card_wasd.centerx, self.rect_card_wasd.y + 35)))

        badge_w = self.fonte_rodape.render("RECOMENDADO (TECLADO + MOUSE)", True, DOURADO_ENVELHECIDO if ativo_wasd else UI_TEXTO_APAGADO)
        tela.blit(badge_w, badge_w.get_rect(center=(self.rect_card_wasd.centerx, self.rect_card_wasd.y + 65)))

        # Diagrama de Teclas WASD
        cx_w = self.rect_card_wasd.centerx
        cy_teclas_w = self.rect_card_wasd.y + 95
        self._desenhar_tecla(tela, "W", cx_w - 18, cy_teclas_w, 36, 36, ativo=ativo_wasd)
        self._desenhar_tecla(tela, "A", cx_w - 60, cy_teclas_w + 42, 36, 36, ativo=ativo_wasd)
        self._desenhar_tecla(tela, "S", cx_w - 18, cy_teclas_w + 42, 36, 36, ativo=ativo_wasd)
        self._desenhar_tecla(tela, "D", cx_w + 24, cy_teclas_w + 42, 36, 36, ativo=ativo_wasd)

        # Comandos WASD
        y_linha = self.rect_card_wasd.y + 195
        comandos_wasd = [
            ("Movimentação:", "W, A, S, D"),
            ("Correr:", "Shift Esquerdo"),
            ("Interagir:", "Tecla E"),
            ("Inventário / Bolsa:", "Tecla TAB"),
            ("Menu Pause:", "Tecla ESC")
        ]
        for rotulo, tecla in comandos_wasd:
            lbl = self.fonte_desc.render(rotulo, True, UI_TEXTO_APAGADO if not ativo_wasd else (195, 205, 215))
            val = self.fonte_desc.render(tecla, True, MARFIM_OFFWHITE if not ativo_wasd else AZUL_HOVER_MENU)
            tela.blit(lbl, (self.rect_card_wasd.x + 35, y_linha))
            tela.blit(val, (self.rect_card_wasd.right - val.get_width() - 35, y_linha))
            y_linha += 27

        # Botão de Seleção WASD
        fundo_btn_w = AZUL_HOVER_BG if ativo_wasd else (22, 24, 30)
        borda_btn_w = AZUL_HOVER_MENU if ativo_wasd else CINZA_LINHO
        pygame.draw.rect(tela, fundo_btn_w, self.rect_btn_wasd, border_radius=4)
        pygame.draw.rect(tela, borda_btn_w, self.rect_btn_wasd, 1, border_radius=4)
        txt_btn_w = self.fonte_tecla.render("✦ Jogar com WASD" if ativo_wasd else "Selecionar WASD", True, MARFIM_OFFWHITE if ativo_wasd else CINZA_LINHO)
        tela.blit(txt_btn_w, txt_btn_w.get_rect(center=self.rect_btn_wasd.center))

        # 4. Card 2: PADRÃO SETINHAS
        ativo_setas = (self.hover_mouse == 1) or (self.modo_teclado and self.selecionada == 1)
        cor_borda_setas = AZUL_HOVER_BORDA if ativo_setas else CINZA_LINHO
        cor_fundo_setas = (16, 24, 36) if ativo_setas else CARVAO_PROFUNDO
        desenhar_painel_padrao(tela, self.rect_card_setas, cor_fundo=cor_fundo_setas, cor_borda=cor_borda_setas, largura_borda=2 if ativo_setas else 1, alpha=245)

        # Título do Card Setinhas
        cor_tit_setas = AZUL_HOVER_MENU if ativo_setas else MARFIM_OFFWHITE
        txt_c2 = self.fonte_card_titulo.render("Padrão Setinhas", True, cor_tit_setas)
        tela.blit(txt_c2, txt_c2.get_rect(center=(self.rect_card_setas.centerx, self.rect_card_setas.y + 35)))

        badge_s = self.fonte_rodape.render("FOCO NAS SETAS DIRECIONAIS", True, DOURADO_ENVELHECIDO if ativo_setas else UI_TEXTO_APAGADO)
        tela.blit(badge_s, badge_s.get_rect(center=(self.rect_card_setas.centerx, self.rect_card_setas.y + 65)))

        # Diagrama de Teclas Setinhas
        cx_s = self.rect_card_setas.centerx
        cy_teclas_s = self.rect_card_setas.y + 95
        self._desenhar_tecla(tela, "^", cx_s - 18, cy_teclas_s, 36, 36, ativo=ativo_setas)
        self._desenhar_tecla(tela, "<", cx_s - 60, cy_teclas_s + 42, 36, 36, ativo=ativo_setas)
        self._desenhar_tecla(tela, "v", cx_s - 18, cy_teclas_s + 42, 36, 36, ativo=ativo_setas)
        self._desenhar_tecla(tela, ">", cx_s + 24, cy_teclas_s + 42, 36, 36, ativo=ativo_setas)

        # Comandos Setinhas
        y_linha_s = self.rect_card_setas.y + 195
        comandos_setas = [
            ("Movimentação:", "Setas Direcionais"),
            ("Correr:", "Shift (Dir. / Esq.)"),
            ("Interagir:", "Tecla Espaço / E"),
            ("Inventário / Bolsa:", "Tecla TAB"),
            ("Menu Pause:", "Tecla ESC")
        ]
        for rotulo, tecla in comandos_setas:
            lbl = self.fonte_desc.render(rotulo, True, UI_TEXTO_APAGADO if not ativo_setas else (195, 205, 215))
            val = self.fonte_desc.render(tecla, True, MARFIM_OFFWHITE if not ativo_setas else AZUL_HOVER_MENU)
            tela.blit(lbl, (self.rect_card_setas.x + 35, y_linha_s))
            tela.blit(val, (self.rect_card_setas.right - val.get_width() - 35, y_linha_s))
            y_linha_s += 27

        # Botão de Seleção Setinhas
        fundo_btn_s = AZUL_HOVER_BG if ativo_setas else (22, 24, 30)
        borda_btn_s = AZUL_HOVER_MENU if ativo_setas else CINZA_LINHO
        pygame.draw.rect(tela, fundo_btn_s, self.rect_btn_setas, border_radius=4)
        pygame.draw.rect(tela, borda_btn_s, self.rect_btn_setas, 1, border_radius=4)
        txt_btn_s = self.fonte_tecla.render("✦ Jogar com Setinhas" if ativo_setas else "Selecionar Setinhas", True, MARFIM_OFFWHITE if ativo_setas else CINZA_LINHO)
        tela.blit(txt_btn_s, txt_btn_s.get_rect(center=self.rect_btn_setas.center))

        # 5. Rodapé Informativo
        txt_rodape1 = self.fonte_rodape.render("Pressione [<- / ->] ou [1 / 2] para alternar  •  [ENTER] ou [Clique] para confirmar", True, MARFIM_OFFWHITE)
        tela.blit(txt_rodape1, txt_rodape1.get_rect(center=(self.game.LARGURA // 2, self.game.ALTURA - 68)))

        txt_rodape2 = self.fonte_rodape.render("Você também pode remapear ou alterar qualquer tecla a qualquer momento nas Configurações.", True, UI_TEXTO_APAGADO)
        tela.blit(txt_rodape2, txt_rodape2.get_rect(center=(self.game.LARGURA // 2, self.game.ALTURA - 42)))
