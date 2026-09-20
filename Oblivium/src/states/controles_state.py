# src/states/controles_state.py
import pygame
from src.states.states import State
from src.utils.colors import (
    PRETO, BRANCO, CARVAO_PROFUNDO, CINZA_ARDOSIA, CINZA_LINHO, CINZA_CLARO,
    MARFIM_OFFWHITE, UI_TEXTO_DESTAQUE, UI_TEXTO_APAGADO, TXT_SISTEMA_NARRADOR,
    BORDA_PADRAO, BORDA_DESTAQUE, AZUL_HOVER_MENU, AZUL_HOVER_BG
)
from src.utils.resource_manager import ResourceManager
from src.ui.ui_utils import desenhar_painel_padrao

class ControlesState(State):
    """
    Tela de Configuração de Teclas de Oblivium alinhada à estética Dark Fantasy / Metroidvania:
    - Moldura em Carvão Profundo com contornos em Cinza Linho
    - Tipografia consolidada (Sunday para títulos, Contrail One para comandos)
    """
    def __init__(self, game):
        super().__init__(game)
        self.acoes = list(self.game.controles.keys())
        self.selecionada = 0
        
        # Tipografia Consolidada
        self.fonte_titulo = ResourceManager.carregar_fonte("sunday", 36)
        self.fonte_opcao = ResourceManager.carregar_fonte("contrail", 20)
        self.fonte_sub = ResourceManager.carregar_fonte("contrail", 15)
        
        self.redefinindo = False
        self.rects_opcoes = []

    def handle_events(self, eventos, teclas):
        for evento in eventos:
            if evento.type == pygame.KEYDOWN:
                if self.redefinindo:
                    if evento.key == pygame.K_ESCAPE:
                        self.redefinindo = False
                        return
                    
                    acao_atual = self.acoes[self.selecionada]
                    self.game.controles[acao_atual] = evento.key
                    self.redefinindo = False
                    return

                if evento.key in [pygame.K_UP, pygame.K_w]:
                    self.selecionada = (self.selecionada - 1) % (len(self.acoes) + 1)
                elif evento.key in [pygame.K_DOWN, pygame.K_s]:
                    self.selecionada = (self.selecionada + 1) % (len(self.acoes) + 1)
                elif evento.key in [pygame.K_RETURN, pygame.K_SPACE]:
                    i_voltar = len(self.acoes)
                    if self.selecionada == i_voltar:
                        self.game.mudar_estado("CONFIGURACOES")
                    else:
                        self.redefinindo = True
                elif evento.key == pygame.K_ESCAPE:
                    self.game.mudar_estado("CONFIGURACOES")

            elif evento.type == pygame.MOUSEMOTION and not self.redefinindo:
                for i, rect in enumerate(self.rects_opcoes):
                    if rect.collidepoint(evento.pos):
                        self.selecionada = i

            elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1 and not self.redefinindo:
                for i, rect in enumerate(self.rects_opcoes):
                    if rect.collidepoint(evento.pos):
                        self.selecionada = i
                        i_voltar = len(self.acoes)
                        if self.selecionada == i_voltar:
                            self.game.mudar_estado("CONFIGURACOES")
                        else:
                            self.redefinindo = True

    def update(self):
        pass

    def draw(self, tela):
        tela.fill(CARVAO_PROFUNDO)
        
        largura_bloco = 720
        altura_bloco = 520
        x = (self.game.LARGURA - largura_bloco) // 2
        y = (self.game.ALTURA - altura_bloco) // 2

        rect_painel = pygame.Rect(x, y, largura_bloco, altura_bloco)
        desenhar_painel_padrao(tela, rect_painel, cor_fundo=CARVAO_PROFUNDO, cor_borda=CINZA_LINHO, alpha=245)

        # Moldura interna decorativa
        rect_interno = rect_painel.inflate(-10, -10)
        pygame.draw.rect(tela, (28, 28, 34), rect_interno, 1, border_radius=2)

        # Título
        titulo = self.fonte_titulo.render("Configurar Teclas", True, MARFIM_OFFWHITE)
        tela.blit(titulo, (x + 40, y + 25))

        # Divisória
        pygame.draw.line(tela, CINZA_ARDOSIA, (x + 40, y + 68), (x + largura_bloco - 40, y + 68), 1)

        self.rects_opcoes.clear()
        
        # Renderiza cada ação e a sua respetiva tecla
        for i, acao in enumerate(self.acoes):
            tecla_nome = pygame.key.name(self.game.controles[acao]).upper()
            pos_y = y + 80 + (i * 44)
            rect = pygame.Rect(x + 40, pos_y, largura_bloco - 80, 36)
            self.rects_opcoes.append(rect)

            esta_sel = (self.selecionada == i)

            if esta_sel and self.redefinindo:
                pygame.draw.rect(tela, (45, 20, 20), rect, border_radius=2)
                pygame.draw.rect(tela, (220, 70, 70), rect, 1, border_radius=2)
                texto_str = f"{acao}:  < Pressione a nova tecla... >"
                cor = (255, 120, 120)
            elif esta_sel:
                pygame.draw.rect(tela, AZUL_HOVER_BG, rect, border_radius=2)
                pygame.draw.rect(tela, AZUL_HOVER_MENU, rect, 1, border_radius=2)
                texto_str = f"✦  {acao}: [ {tecla_nome} ]"
                cor = MARFIM_OFFWHITE
            else:
                texto_str = f"    {acao}: [ {tecla_nome} ]"
                cor = CINZA_LINHO

            render = self.fonte_opcao.render(texto_str, True, cor)
            tela.blit(render, (x + 55, rect.centery - render.get_height() // 2))

        # Opção de Voltar
        i_voltar = len(self.acoes)
        pos_y_v = y + 80 + (i_voltar * 44) + 8
        rect_v = pygame.Rect(x + 40, pos_y_v, largura_bloco - 80, 36)
        self.rects_opcoes.append(rect_v)

        esta_sel_v = (self.selecionada == i_voltar)
        if esta_sel_v:
            pygame.draw.rect(tela, AZUL_HOVER_BG, rect_v, border_radius=2)
            pygame.draw.rect(tela, AZUL_HOVER_MENU, rect_v, 1, border_radius=2)
            texto_voltar = "✦  Voltar"
            cor_voltar = MARFIM_OFFWHITE
        else:
            texto_voltar = "    Voltar"
            cor_voltar = CINZA_LINHO

        render_voltar = self.fonte_opcao.render(texto_voltar, True, cor_voltar)
        tela.blit(render_voltar, (x + 55, rect_v.centery - render_voltar.get_height() // 2))

        # Rodapé
        txt_rodape = self.fonte_sub.render("[ENTER] Redefinir tecla   •   [ESC] Retornar", True, UI_TEXTO_APAGADO)
        tela.blit(txt_rodape, (x + (largura_bloco - txt_rodape.get_width()) // 2, y + altura_bloco - 28))