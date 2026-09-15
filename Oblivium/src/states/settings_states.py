# src/states/settings_states.py
import pygame
from src.states.states import State
from src.utils.colors import PRETO, BRANCO, UI_FUNDO_PADRAO, CINZA_CLARO, UI_TEXTO_DESTAQUE, UI_TEXTO_APAGADO, TXT_SISTEMA_NARRADOR

class SettingsState(State):
    def __init__(self, game):
        super().__init__(game)
        self.opcoes = [
            "Velocidade do Texto", 
            "Velocidade do Combate", 
            "Volume do Áudio", 
            "Configurar Teclas...", 
            "Voltar"
        ]
        self.selecionada = 0
        self.fonte_titulo = pygame.font.Font(None, 56)
        self.fonte_opcao = pygame.font.Font(None, 32)
        self.rects_opcoes = []

    def handle_events(self, eventos, teclas):
        for evento in eventos:
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_UP or evento.key == pygame.K_w:
                    self.selecionada = (self.selecionada - 1) % len(self.opcoes)
                elif evento.key == pygame.K_DOWN or evento.key == pygame.K_s:
                    self.selecionada = (self.selecionada + 1) % len(self.opcoes)
                elif evento.key == pygame.K_LEFT or evento.key == pygame.K_a:
                    self.alterar_valor(-1)
                elif evento.key == pygame.K_RIGHT or evento.key == pygame.K_d:
                    self.alterar_valor(1)
                elif evento.key in [pygame.K_RETURN, pygame.K_SPACE, pygame.K_e]:
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
                        if i in [0, 1, 2]:
                            self.alterar_valor(1)
                        else:
                            self.executar_acao()

    def alterar_valor(self, direcao):
        # 0: Velocidade do Texto
        if self.selecionada == 0:
            self.game.config_velocidade_indice = (self.game.config_velocidade_indice + direcao) % len(self.game.opcoes_velocidade)
            novo_valor = self.game.valores_velocidade[self.game.config_velocidade_indice]
            self.game.caixa_dialogo.velocidade_texto = novo_valor

        # 1: Velocidade do Combate
        elif self.selecionada == 1:
            self.game.config_velocidade_combate_indice = (self.game.config_velocidade_combate_indice + direcao) % len(self.game.opcoes_velocidade_combate)
            novo_fator = self.game.valores_velocidade_combate[self.game.config_velocidade_combate_indice]
            self.game.tela_combate.definir_velocidade(novo_fator)

        # 2: Volume do Áudio
        elif self.selecionada == 2:
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
        
        largura_bloco = 760
        altura_bloco = 480
        x = (self.game.LARGURA - largura_bloco) // 2
        y = (self.game.ALTURA - altura_bloco) // 2

        pygame.draw.rect(tela, UI_FUNDO_PADRAO, (x, y, largura_bloco, altura_bloco))
        pygame.draw.rect(tela, CINZA_CLARO, (x, y, largura_bloco, altura_bloco), 2)

        titulo = self.fonte_titulo.render("Configurações", True, UI_TEXTO_DESTAQUE)
        tela.blit(titulo, (x + 50, y + 30))

        vel_texto = self.game.opcoes_velocidade[self.game.config_velocidade_indice]
        vel_combate = self.game.opcoes_velocidade_combate[self.game.config_velocidade_combate_indice]
        audio_texto = f"{self.game.config_audio}%"

        opcoes_render = [
            f"Velocidade do Texto: < {vel_texto} >",
            f"Velocidade do Combate: < {vel_combate} >",
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
            pos_y = y + 110 + (i * 65)
            tela.blit(render, (pos_x, pos_y))
            
            rect = pygame.Rect(pos_x, pos_y, render.get_width(), render.get_height())
            self.rects_opcoes.append(rect)