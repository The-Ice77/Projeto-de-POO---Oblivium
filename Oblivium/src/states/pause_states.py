# src/states/pause_states.py
import pygame
from src.states.states import State
from src.utils.colors import PRETO, BRANCO, UI_FUNDO_PADRAO, CINZA_CLARO, UI_TEXTO_DESTAQUE, UI_TEXTO_APAGADO, TXT_SISTEMA_NARRADOR
from src.utils import save_manager

class PauseState(State):
    def __init__(self, game):
        super().__init__(game)
        self.opcoes = ["Retomar", "Salvar Jogo", "Carregar Jogo", "Configurações", "Sair para o Menu"]
        self.selecionada = 0
        self.fonte_titulo = pygame.font.Font(None, 50)
        self.fonte_menu = pygame.font.Font(None, 36)
        
        # Lista para guardar as hitboxes das opções para detetar o rato
        self.rects_opcoes = []
        
        # Película escura de fundo
        self.overlay = pygame.Surface((self.game.LARGURA, self.game.ALTURA))
        self.overlay.fill(PRETO)
        self.overlay.set_alpha(150)

    def handle_events(self, eventos, teclas):
        for evento in eventos:
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_UP:
                    self.selecionada = (self.selecionada - 1) % len(self.opcoes)
                elif evento.key == pygame.K_DOWN:
                    self.selecionada = (self.selecionada + 1) % len(self.opcoes)
                elif evento.key == pygame.K_RETURN:
                    self.executar_opcao()
                elif evento.key == pygame.K_ESCAPE:
                    self.game.mudar_estado("JOGANDO")
                    
            elif evento.type == pygame.MOUSEMOTION:
                for i, rect in enumerate(self.rects_opcoes):
                    if rect.collidepoint(evento.pos):
                        self.selecionada = i
                        
            elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                for i, rect in enumerate(self.rects_opcoes):
                    if rect.collidepoint(evento.pos):
                        self.selecionada = i
                        self.executar_opcao()

    def executar_opcao(self):
        opcao = self.opcoes[self.selecionada]
        
        if opcao == "Retomar":
            self.game.mudar_estado("JOGANDO")
            
        elif opcao == "Salvar Jogo":
            if self.game.slot_atual:
                # Dispara a telinha de "Salvando..." por cima do jogo e executa
                self.game.executar_com_feedback("Salvando Jogo...", lambda: self.game.salvar_estado(self.game.slot_atual))
                self.game.mudar_estado("JOGANDO")
            else:
                # Caso por algum motivo não tenha slot vinculado, abre os slots
                self.game.acao_slots = "SALVAR"
                self.game.origem_slots = "PAUSE"
                self.game.mudar_estado("SLOTS")
                
        elif opcao == "Carregar Jogo":
            if self.game.slot_atual and save_manager.save_existe(self.game.slot_atual):
                # Dispara a telinha de "Carregando..." por cima do jogo e executa
                self.game.executar_com_feedback("Carregando Jogo...", lambda: self.game.carregar_estado(self.game.slot_atual))
                self.game.mudar_estado("JOGANDO")
            else:
                self.game.acao_slots = "CARREGAR"
                self.game.origem_slots = "PAUSE"
                self.game.mudar_estado("SLOTS")
                
        elif opcao == "Configurações":
            self.game.origem_configuracoes = "PAUSE"
            self.game.mudar_estado("CONFIGURACOES")
            
        elif opcao == "Sair para o Menu":
            if hasattr(self.game, 'menu'):
                self.game.menu.atualizar_opcoes()
            self.game.mudar_estado("MENU")
    def update(self):
        pass

    def draw(self, tela):
        self.game.estados["JOGANDO"].draw(tela)
        tela.blit(self.overlay, (0, 0))
        
        largura_bloco = 500
        altura_bloco = 420
        x = (self.game.LARGURA - largura_bloco) // 2
        y = (self.game.ALTURA - altura_bloco) // 2

        pygame.draw.rect(tela, UI_FUNDO_PADRAO, (x, y, largura_bloco, altura_bloco))
        pygame.draw.rect(tela, CINZA_CLARO, (x, y, largura_bloco, altura_bloco), 2)

        titulo = self.fonte_titulo.render("Menu de Pause", True, UI_TEXTO_DESTAQUE)
        tela.blit(titulo, (x + (largura_bloco - titulo.get_width()) // 2, y + 30))

        self.rects_opcoes.clear()
        for i, opcao in enumerate(self.opcoes):
            cor = TXT_SISTEMA_NARRADOR if i == self.selecionada else BRANCO
            texto = f"> {opcao}" if i == self.selecionada else f"  {opcao}"
            render = self.fonte_menu.render(texto, True, cor)
            
            pos_x = x + 60
            pos_y = y + 110 + (i * 50)
            tela.blit(render, (pos_x, pos_y))
            
            rect = pygame.Rect(pos_x, pos_y, render.get_width(), render.get_height())
            self.rects_opcoes.append(rect)