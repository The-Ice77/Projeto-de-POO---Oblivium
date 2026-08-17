# src/states/settings_states.py
import pygame
from src.states.states import State
from src.utils.colors import PRETO, BRANCO, UI_FUNDO_PADRAO, CINZA_CLARO, UI_TEXTO_DESTAQUE, UI_TEXTO_APAGADO, TXT_SISTEMA_NARRADOR

class SettingsState(State):
    def __init__(self, game):
        super().__init__(game)
        self.opcoes = ["Velocidade do Texto", "Volume do Áudio", "Configurar Teclas...", "Voltar"]
        self.selecionada = 0
        self.fonte_titulo = pygame.font.Font(None, 60)
        self.fonte_opcao = pygame.font.Font(None, 34)
        self.rects_opcoes = []

    def handle_events(self, eventos, teclas):
        for evento in eventos:
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_UP:
                    self.selecionada = (self.selecionada - 1) % len(self.opcoes)
                elif evento.key == pygame.K_DOWN:
                    self.selecionada = (self.selecionada + 1) % len(self.opcoes)
                elif evento.key == pygame.K_LEFT:
                    self.alterar_valor(-1)
                elif evento.key == pygame.K_RIGHT:
                    self.alterar_valor(1)
                elif evento.key == pygame.K_RETURN:
                    self.executar_acao()
                elif evento.key == pygame.K_ESCAPE:
                    self.voltar_origem()
                    
            elif evento.type == pygame.MOUSEMOTION:
                for i, rect in enumerate(self.rects_opcoes):
                    if rect.collidepoint(evento.pos):
                        self.selecionada = i
                            
            elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                for i, rect in enumerate(self.rects_opcoes):
                    if rect.collidepoint(evento.pos):
                        self.selecionada = i
                        self.executar_acao()

    def alterar_valor(self, direcao):
        if self.selecionada == 0:
            self.game.config_velocidade_indice = (self.game.config_velocidade_indice + direcao) % len(self.game.opcoes_velocidade)
            novo_valor = self.game.valores_velocidade[self.game.config_velocidade_indice]
            self.game.caixa_dialogo.velocidade_texto = novo_valor
        elif self.selecionada == 1:
            self.game.config_audio = max(0, min(100, self.game.config_audio + (direcao * 10)))

    def executar_acao(self):
        opcao = self.opcoes[self.selecionada]
        if opcao == "Configurar Teclas...":
            self.game.mudar_estado("CONTROLES")
        elif opcao == "Voltar":
            self.voltar_origem()

    def voltar_origem(self):
        if self.game.origem_configuracoes == "PAUSE":
            self.game.mudar_estado("PAUSE")
        else:
            self.game.mudar_estado("MENU")

    def update(self):
        pass

    def draw(self, tela):
        tela.fill(PRETO)
        
        largura_bloco = 750
        altura_bloco = 450
        x = (self.game.LARGURA - largura_bloco) // 2
        y = (self.game.ALTURA - altura_bloco) // 2

        pygame.draw.rect(tela, UI_FUNDO_PADRAO, (x, y, largura_bloco, altura_bloco))
        pygame.draw.rect(tela, CINZA_CLARO, (x, y, largura_bloco, altura_bloco), 2)

        titulo = self.fonte_titulo.render("Configurações", True, UI_TEXTO_DESTAQUE)
        tela.blit(titulo, (x + 50, y + 35))

        vel_texto = self.game.opcoes_velocidade[self.game.config_velocidade_indice]
        audio_texto = f"{self.game.config_audio}%"

        opcoes_render = [
            f"Velocidade do Texto: < {vel_texto} >",
            f"Volume do Áudio: < {audio_texto} >",
            "Configurar Teclas...",
            "Voltar"
        ]

        self.rects_opcoes.clear()
        for i, texto_opcao in enumerate(opcoes_render):
            cor = TXT_SISTEMA_NARRADOR if i == self.selecionada else BRANCO
            prefixo = "> " if i == self.selecionada else "  "
            render = self.fonte_opcao.render(f"{prefixo}{texto_opcao}", True, cor)
            
            pos_x = x + 50
            pos_y = y + 130 + (i * 65)
            tela.blit(render, (pos_x, pos_y))
            
            rect = pygame.Rect(pos_x, pos_y, render.get_width(), render.get_height())
            self.rects_opcoes.append(rect)