# src/states/pause_states.py
import pygame
from src.states.states import State
from src.utils.colors import PRETO, BRANCO, UI_FUNDO_PADRAO, CINZA_CLARO, UI_TEXTO_DESTAQUE, UI_TEXTO_APAGADO, TXT_SISTEMA_NARRADOR
from src.utils import save_manager

class PauseState(State):
    def __init__(self, game):
        super().__init__(game)
        self.opcoes_padrao = ["Retomar", "Salvar Jogo", "Carregar Jogo", "Configurações", "Sair para o Menu"]
        self.opcoes_combate = ["Retomar", "Carregar Jogo", "Configurações", "Sair para o Menu"]
        self.opcoes = list(self.opcoes_padrao)
        self.selecionada = 0
        self.fonte_titulo = pygame.font.Font(None, 50)
        self.fonte_menu = pygame.font.Font(None, 36)
        
        # Lista para guardar as hitboxes das opções para detetar o rato
        self.rects_opcoes = []
        
        # Película escura de fundo
        self.overlay = pygame.Surface((self.game.LARGURA, self.game.ALTURA))
        self.overlay.fill(PRETO)
        self.overlay.set_alpha(165)

    def _obter_opcoes_atuais(self):
        if getattr(self.game, 'origem_pause', '') == "COMBATE":
            return self.opcoes_combate
        return self.opcoes_padrao

    def handle_events(self, eventos, teclas):
        self.opcoes = self._obter_opcoes_atuais()
        if self.selecionada >= len(self.opcoes):
            self.selecionada = 0

        for evento in eventos:
            if evento.type == pygame.KEYDOWN:
                if evento.key in [pygame.K_UP, pygame.K_w]:
                    self.selecionada = (self.selecionada - 1) % len(self.opcoes)
                elif evento.key in [pygame.K_DOWN, pygame.K_s]:
                    self.selecionada = (self.selecionada + 1) % len(self.opcoes)
                elif evento.key in [pygame.K_RETURN, pygame.K_SPACE]:
                    self.executar_opcao()
                elif evento.key == pygame.K_ESCAPE:
                    origem = getattr(self.game, 'origem_pause', 'JOGANDO')
                    self.game.mudar_estado(origem)
                    
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
        self.opcoes = self._obter_opcoes_atuais()
        if self.selecionada >= len(self.opcoes):
            self.selecionada = 0
            
        opcao = self.opcoes[self.selecionada]
        origem = getattr(self.game, 'origem_pause', 'JOGANDO')
        
        if opcao == "Retomar":
            self.game.mudar_estado(origem)
            
        elif opcao == "Salvar Jogo":
            # Não permitido no meio do combate por design
            if origem == "COMBATE":
                return

            if self.game.slot_atual:
                self.game.executar_com_feedback("Salvando Jogo...", lambda: self.game.salvar_estado(self.game.slot_atual))
                self.game.mudar_estado("JOGANDO")
            else:
                self.game.acao_slots = "SALVAR"
                self.game.origem_slots = "PAUSE"
                self.game.mudar_estado("SLOTS")
                
        elif opcao == "Carregar Jogo":
            if self.game.slot_atual and save_manager.save_existe(self.game.slot_atual):
                self.game.executar_com_feedback("Carregando Jogo...", lambda: self.game.carregar_estado(self.game.slot_atual))
                self.game.origem_pause = "JOGANDO"
                self.game.mudar_estado("JOGANDO")
            else:
                self.game.acao_slots = "CARREGAR"
                self.game.origem_slots = "PAUSE"
                self.game.mudar_estado("SLOTS")
                
        elif opcao == "Configurações":
            self.game.origem_configuracoes = "PAUSE"
            self.game.mudar_estado("CONFIGURACOES")
            
        elif opcao == "Sair para o Menu":
            self.game.origem_pause = "JOGANDO"
            if hasattr(self.game, 'menu'):
                self.game.menu.atualizar_opcoes()
            self.game.mudar_estado("MENU")

    def update(self):
        self.opcoes = self._obter_opcoes_atuais()

    def draw(self, tela):
        origem = getattr(self.game, 'origem_pause', 'JOGANDO')
        if origem == "COMBATE" and hasattr(self.game, 'tela_combate'):
            self.game.tela_combate.desenhar(tela)
        elif "JOGANDO" in self.game.estados:
            self.game.estados["JOGANDO"].draw(tela)

        tela.blit(self.overlay, (0, 0))
        
        self.opcoes = self._obter_opcoes_atuais()
        largura_bloco = 520
        altura_bloco = 120 + (len(self.opcoes) * 52)
        x = (self.game.LARGURA - largura_bloco) // 2
        y = (self.game.ALTURA - altura_bloco) // 2

        pygame.draw.rect(tela, UI_FUNDO_PADRAO, (x, y, largura_bloco, altura_bloco))
        pygame.draw.rect(tela, CINZA_CLARO, (x, y, largura_bloco, altura_bloco), 2)

        titulo_texto = "Combate Pausado" if origem == "COMBATE" else "Menu de Pause"
        titulo = self.fonte_titulo.render(titulo_texto, True, UI_TEXTO_DESTAQUE)
        tela.blit(titulo, (x + (largura_bloco - titulo.get_width()) // 2, y + 25))

        self.rects_opcoes.clear()
        for i, opcao in enumerate(self.opcoes):
            cor = TXT_SISTEMA_NARRADOR if i == self.selecionada else BRANCO
            texto = f"> {opcao}" if i == self.selecionada else f"  {opcao}"
            render = self.fonte_menu.render(texto, True, cor)
            
            pos_x = x + 60
            pos_y = y + 95 + (i * 48)
            tela.blit(render, (pos_x, pos_y))
            
            rect = pygame.Rect(pos_x, pos_y, render.get_width(), render.get_height())
            self.rects_opcoes.append(rect)