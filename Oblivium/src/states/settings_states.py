# src/states/settings_states.py
import pygame
from src.states.states import State
from src.utils.colors import (
    PRETO, BRANCO, CARVAO_PROFUNDO, CINZA_ARDOSIA, CINZA_LINHO, CINZA_CLARO,
    MARFIM_OFFWHITE, UI_TEXTO_DESTAQUE, UI_TEXTO_APAGADO, TXT_SISTEMA_NARRADOR,
    BORDA_PADRAO, BORDA_DESTAQUE, AZUL_HOVER_MENU, AZUL_HOVER_BG
)
from src.utils.resource_manager import ResourceManager
from src.ui.ui_utils import desenhar_painel_padrao

class SettingsState(State):
    """
    Tela de Configurações alinhada à estética Dark Fantasy / Metroidvania:
    - Moldura em Carvão Profundo com contornos delicados em Cinza Linho / Marfim
    - Tipografia consolidada (Sunday para títulos, Contrail One para opções)
    - Navegação com teclado e mouse com feedback visual
    """
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
        
        # Tipografia Consolidada
        self.fonte_titulo = ResourceManager.carregar_fonte("sunday", 36)
        self.fonte_opcao = ResourceManager.carregar_fonte("contrail", 22)
        self.fonte_sub = ResourceManager.carregar_fonte("contrail", 16)
        
        self.rects_opcoes = []

    def handle_events(self, eventos, teclas):
        for evento in eventos:
            if evento.type == pygame.KEYDOWN:
                if evento.key in [pygame.K_UP, pygame.K_w]:
                    self.selecionada = (self.selecionada - 1) % len(self.opcoes)
                elif evento.key in [pygame.K_DOWN, pygame.K_s]:
                    self.selecionada = (self.selecionada + 1) % len(self.opcoes)
                elif evento.key in [pygame.K_LEFT, pygame.K_a]:
                    self.alterar_valor(-1)
                elif evento.key in [pygame.K_RIGHT, pygame.K_d]:
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
        tela.fill(CARVAO_PROFUNDO)
        
        largura_bloco = 740
        altura_bloco = 470
        x = (self.game.LARGURA - largura_bloco) // 2
        y = (self.game.ALTURA - altura_bloco) // 2

        rect_painel = pygame.Rect(x, y, largura_bloco, altura_bloco)
        desenhar_painel_padrao(tela, rect_painel, cor_fundo=CARVAO_PROFUNDO, cor_borda=CINZA_LINHO, alpha=245)

        # Moldura interna decorativa
        rect_interno = rect_painel.inflate(-10, -10)
        pygame.draw.rect(tela, (28, 28, 34), rect_interno, 1, border_radius=2)

        # Título
        titulo = self.fonte_titulo.render("Configurações", True, MARFIM_OFFWHITE)
        tela.blit(titulo, (x + 45, y + 28))

        # Divisória
        pygame.draw.line(tela, CINZA_ARDOSIA, (x + 40, y + 74), (x + largura_bloco - 40, y + 74), 1)

        vel_texto = self.game.opcoes_velocidade[self.game.config_velocidade_indice]
        vel_combate = self.game.opcoes_velocidade_combate[self.game.config_velocidade_combate_indice]
        audio_texto = f"{self.game.config_audio}%"

        opcoes_render = [
            f"Velocidade do Texto: < {vel_texto} >",
            f"Velocidade do Combate: < {vel_combate} >",
            f"Volume do Áudio: < {audio_texto} >",
            "Configurar Teclas...",
            "Voltar ao Menu"
        ]

        self.rects_opcoes.clear()
        for i, texto_opcao in enumerate(opcoes_render):
            esta_sel = (i == self.selecionada)
            pos_x = x + 40
            pos_y = y + 95 + (i * 62)
            
            rect_opt = pygame.Rect(pos_x, pos_y, largura_bloco - 80, 42)
            self.rects_opcoes.append(rect_opt)
            
            if esta_sel:
                pygame.draw.rect(tela, AZUL_HOVER_BG, rect_opt, border_radius=3)
                pygame.draw.rect(tela, AZUL_HOVER_MENU, rect_opt, 1, border_radius=3)
                cor = MARFIM_OFFWHITE
                texto_final = f"✦  {texto_opcao}"
            else:
                cor = CINZA_LINHO
                texto_final = f"   {texto_opcao}"
                
            render = self.fonte_opcao.render(texto_final, True, cor)
            tela.blit(render, (pos_x + 16, rect_opt.centery - render.get_height() // 2))

        # Rodapé
        txt_rodape = self.fonte_sub.render("[← / →] Ajustar valor   •   [ENTER] Confirmar   •   [ESC] Retornar", True, UI_TEXTO_APAGADO)
        tela.blit(txt_rodape, (x + (largura_bloco - txt_rodape.get_width()) // 2, y + altura_bloco - 32))