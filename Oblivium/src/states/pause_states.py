# src/states/pause_states.py
import pygame
from src.states.states import State
from src.utils.colors import (
    PRETO, BRANCO, CARVAO_PROFUNDO, CINZA_ARDOSIA, CINZA_LINHO, CINZA_CLARO,
    MARFIM_OFFWHITE, UI_TEXTO_DESTAQUE, UI_TEXTO_APAGADO, BORDA_PADRAO, BORDA_DESTAQUE,
    AZUL_HOVER_MENU, AZUL_HOVER_BG
)
from src.utils.resource_manager import ResourceManager
from src.ui.ui_utils import desenhar_painel_padrao
from src.utils import save_manager

class PauseState(State):
    """
    Menu de Pause alinhado à estética Dark Fantasy / Metroidvania e ao padrão do Menu Inicial:
    - Fundo escurecido suave
    - Moldura em Carvão Profundo com contornos finos em Cinza Linho
    - Tipografia consolidada (Sunday para títulos, Contrail One para opções e rodapé)
    - Hover e seleções em azul suave
    """
    def __init__(self, game):
        super().__init__(game)
        self.opcoes_padrao = ["Retomar", "Salvar Jogo", "Carregar Jogo", "Configurações", "Sair para o Menu"]
        self.opcoes_combate = ["Retomar", "Carregar Jogo", "Configurações", "Sair para o Menu"]
        self.opcoes = list(self.opcoes_padrao)
        self.selecionada = 0
        
        # Tipografia Consolidada
        self.fonte_titulo = ResourceManager.carregar_fonte("sunday", 36)
        self.fonte_subtitulo = ResourceManager.carregar_fonte("just_breathe", 19)
        self.fonte_menu = ResourceManager.carregar_fonte("contrail", 22)
        self.fonte_rodape = ResourceManager.carregar_fonte("contrail", 15)
        
        # Lista para guardar as hitboxes das opções para detetar o rato
        self.rects_opcoes = []
        
        # Película escura de fundo
        self.overlay = pygame.Surface((self.game.LARGURA, self.game.ALTURA))
        self.overlay.fill((10, 10, 14))
        self.overlay.set_alpha(190)

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
                self.game.executar_com_feedback("Salvando Jogo...", lambda: self.game.salvar_estado(self.game.slot_atual, tipo="manual"))
                self.game.mudar_estado("JOGANDO")
            else:
                self.game.acao_slots = "SALVAR"
                self.game.origem_slots = "PAUSE"
                self.game.mudar_estado("SLOTS")
                
        elif opcao == "Carregar Jogo":
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
        largura_bloco = 540
        altura_bloco = 160 + (len(self.opcoes) * 52)
        x = (self.game.LARGURA - largura_bloco) // 2
        y = (self.game.ALTURA - altura_bloco) // 2

        # 1. Painel Central em Carvão Profundo
        rect_painel = pygame.Rect(x, y, largura_bloco, altura_bloco)
        desenhar_painel_padrao(tela, rect_painel, cor_fundo=CARVAO_PROFUNDO, cor_borda=CINZA_LINHO, alpha=245)

        # Moldura interna decorativa
        rect_interno = rect_painel.inflate(-10, -10)
        pygame.draw.rect(tela, (28, 28, 34), rect_interno, 1, border_radius=2)

        # 2. Título e Subtítulo Poético
        titulo_texto = "Pausa no Combate" if origem == "COMBATE" else "Pausa"
        titulo = self.fonte_titulo.render(titulo_texto, True, MARFIM_OFFWHITE)
        tela.blit(titulo, (x + (largura_bloco - titulo.get_width()) // 2, y + 26))

        subtitulo = self.fonte_subtitulo.render("Entre o que foi e o que ainda pode ser", True, CINZA_LINHO)
        tela.blit(subtitulo, (x + (largura_bloco - subtitulo.get_width()) // 2, y + 68))

        # Divisória
        y_div = y + 96
        pygame.draw.line(tela, CINZA_ARDOSIA, (x + 40, y_div), (x + largura_bloco - 40, y_div), 1)

        # 3. Opções do Menu com destaques '✦' e hover azul
        self.rects_opcoes.clear()
        y_opcao_inicial = y + 114

        for i, opcao in enumerate(self.opcoes):
            pos_y = y_opcao_inicial + (i * 52)
            rect_opcao = pygame.Rect(x + 40, pos_y, largura_bloco - 80, 42)
            self.rects_opcoes.append(rect_opcao)

            esta_selecionada = (i == self.selecionada)

            if esta_selecionada:
                pygame.draw.rect(tela, AZUL_HOVER_BG, rect_opcao, border_radius=3)
                pygame.draw.rect(tela, AZUL_HOVER_MENU, rect_opcao, 1, border_radius=3)
                texto = f"✦  {opcao}"
                cor_texto = MARFIM_OFFWHITE
            else:
                texto = f"    {opcao}"
                cor_texto = CINZA_LINHO

            render = self.fonte_menu.render(texto, True, cor_texto)
            tela.blit(render, (rect_opcao.x + 20, rect_opcao.centery - render.get_height() // 2))

        # 4. Rodapé Informativo
        txt_rodape = self.fonte_rodape.render("[↑ / ↓] Navegar   •   [ENTER] Confirmar   •   [ESC] Retomar", True, UI_TEXTO_APAGADO)
        tela.blit(txt_rodape, (x + (largura_bloco - txt_rodape.get_width()) // 2, y + altura_bloco - 30))