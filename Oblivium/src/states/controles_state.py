# src/states/controles_state.py
import pygame
from src.states.states import State
from src.utils.colors import PRETO, BRANCO, UI_FUNDO_PADRAO, CINZA_CLARO, UI_TEXTO_DESTAQUE, UI_TEXTO_APAGADO, TXT_SISTEMA_NARRADOR

class ControlesState(State):
    def __init__(self, game):
        super().__init__(game)
        self.acoes = list(self.game.controles.keys())
        self.selecionada = 0
        self.fonte_titulo = pygame.font.Font(None, 50)
        self.fonte_opcao = pygame.font.Font(None, 30)
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

                if evento.key == pygame.K_UP:
                    self.selecionada = (self.selecionada - 1) % (len(self.acoes) + 1)
                elif evento.key == pygame.K_DOWN:
                    self.selecionada = (self.selecionada + 1) % (len(self.acoes) + 1)
                elif evento.key == pygame.K_RETURN:
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
        tela.fill(PRETO)
        
        largura_bloco = 700
        altura_bloco = 520
        x = (self.game.LARGURA - largura_bloco) // 2
        y = (self.game.ALTURA - altura_bloco) // 2

        pygame.draw.rect(tela, UI_FUNDO_PADRAO, (x, y, largura_bloco, altura_bloco))
        pygame.draw.rect(tela, CINZA_CLARO, (x, y, largura_bloco, altura_bloco), 2)

        titulo = self.fonte_titulo.render("Configurar Teclas", True, UI_TEXTO_DESTAQUE)
        tela.blit(titulo, (x + 40, y + 25))

        self.rects_opcoes.clear()
        
        # Renderiza cada ação e a sua respetiva tecla
        for i, acao in enumerate(self.acoes):
            tecla_nome = pygame.key.name(self.game.controles[acao]).upper()
            texto_str = f"{acao}: [ {tecla_nome} ]"
            
            if self.selecionada == i and self.redefinindo:
                texto_str = f"{acao}: < Pressione nova tecla... >"
                cor = (255, 100, 100)
            elif self.selecionada == i:
                cor = TXT_SISTEMA_NARRADOR
                texto_str = f"> {texto_str}"
            else:
                cor = BRANCO
                texto_str = f"  {texto_str}"

            render = self.fonte_opcao.render(texto_str, True, cor)
            pos_x = x + 50
            pos_y = y + 90 + (i * 45)
            tela.blit(render, (pos_x, pos_y))
            
            
            rect = pygame.Rect(pos_x, pos_y, largura_bloco - 100, 35)
            self.rects_opcoes.append(rect)

        
        i_voltar = len(self.acoes)
        cor_voltar = TXT_SISTEMA_NARRADOR if self.selecionada == i_voltar else BRANCO
        texto_voltar = "> Voltar" if self.selecionada == i_voltar else "  Voltar"
        render_voltar = self.fonte_opcao.render(texto_voltar, True, cor_voltar)
        pos_x_v = x + 50
        pos_y_v = y + 90 + (i_voltar * 45) + 10
        tela.blit(render_voltar, (pos_x_v, pos_y_v))
        
        rect_v = pygame.Rect(pos_x_v, pos_y_v, largura_bloco - 100, 35)
        self.rects_opcoes.append(rect_v)