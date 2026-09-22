# src/states/credits_states.py
import pygame
from src.states.states import State
from src.utils.colors import (
    PRETO, BRANCO, CARVAO_PROFUNDO, CINZA_ARDOSIA, CINZA_LINHO, CINZA_CLARO,
    MARFIM_OFFWHITE, UI_TEXTO_DESTAQUE, UI_TEXTO_APAGADO, TXT_SISTEMA_NARRADOR,
    BORDA_PADRAO, BORDA_DESTAQUE, AZUL_HOVER_MENU, AZUL_HOVER_BG
)
from src.utils.resource_manager import ResourceManager
from src.ui.ui_utils import desenhar_painel_padrao

class CreditsState(State):
    """
    Tela de Créditos de Oblivium alinhada à estética Dark Fantasy / Metroidvania:
    - Moldura elegante em Carvão Profundo com contornos em Cinza Linho
    - Tipografia consolidada (Sunday para seções, Contrail One para cargos e Just Breathe para agradecimentos)
    """
    def __init__(self, game):
        super().__init__(game)
        self.fonte_titulo = ResourceManager.carregar_fonte("sunday", 36)
        self.fonte_secao = ResourceManager.carregar_fonte("sunday", 22)
        self.fonte_texto = ResourceManager.carregar_fonte("contrail", 19)
        self.fonte_agradecimento = ResourceManager.carregar_fonte("just_breathe", 20)
        self.fonte_aviso = ResourceManager.carregar_fonte("contrail", 16)
        
        self.rect_voltar = pygame.Rect(0, 0, 0, 0)
        
        # --- ESTRUTURA DE CRÉDITOS ---
        self.linhas_creditos = [
            # Secção 1
            {"texto": "— DESENVOLVIMENTO PRINCIPAL —", "tipo": "secao", "centralizado": True, "cor": AZUL_HOVER_MENU},
            {"texto": "Programação e Arquitetura: João Victor", "tipo": "normal", "centralizado": False, "cor": CINZA_LINHO},
            {"texto": "Design de UI e Sistemas: João Victor", "tipo": "normal", "centralizado": False, "cor": CINZA_LINHO},
            
            # Secção 2
            {"texto": "— ARTE E VISUAL —", "tipo": "secao", "centralizado": True, "cor": AZUL_HOVER_MENU},
            {"texto": "Pixel Art e Cenários: João Victor", "tipo": "normal", "centralizado": False, "cor": CINZA_LINHO},
            
            # Secção 3
            {"texto": "— ROTEIRO E ÁUDIO —", "tipo": "secao", "centralizado": True, "cor": AZUL_HOVER_MENU},
            {"texto": "História e Diálogos: João Victor", "tipo": "normal", "centralizado": False, "cor": CINZA_LINHO},
            
            # Secção 4
            {"texto": "— AGRADECIMENTOS —", "tipo": "secao", "centralizado": True, "cor": AZUL_HOVER_MENU},
            {"texto": "Um agradecimento especial ao professor Max Miller e a todos os colegas que apoiaram este projeto de Programação Orientada a Objetos.", "tipo": "normal", "centralizado": True, "cor": CINZA_LINHO}
        ]

    def handle_events(self, eventos, teclas):
        for evento in eventos:
            if evento.type == pygame.KEYDOWN:
                if evento.key in [pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE]:
                    self.game.mudar_estado("MENU")
            elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                if self.rect_voltar.collidepoint(evento.pos):
                    self.game.mudar_estado("MENU")

    def update(self):
        pass

    def _quebrar_texto(self, texto, fonte, largura_maxima):
        """Função auxiliar para quebrar textos longos automaticamente sem cortar na borda"""
        palavras = texto.split(' ')
        linhas = []
        linha_atual = ""
        for palavra in palavras:
            teste_linha = f"{linha_atual} {palavra}".strip()
            if fonte.size(teste_linha)[0] <= largura_maxima:
                linha_atual = teste_linha
            else:
                if linha_atual: 
                    linhas.append(linha_atual)
                linha_atual = palavra
        if linha_atual: 
            linhas.append(linha_atual)
        return linhas

    def draw(self, tela):
        tela.fill(CARVAO_PROFUNDO)
        
        largura_bloco = 840
        altura_bloco = 580
        x = (self.game.LARGURA - largura_bloco) // 2
        y = (self.game.ALTURA - altura_bloco) // 2

        rect_painel = pygame.Rect(x, y, largura_bloco, altura_bloco)
        desenhar_painel_padrao(tela, rect_painel, cor_fundo=CARVAO_PROFUNDO, cor_borda=CINZA_LINHO, alpha=245)

        # Moldura interna decorativa
        rect_interno = rect_painel.inflate(-10, -10)
        pygame.draw.rect(tela, (28, 28, 34), rect_interno, 1, border_radius=2)

        # Título Principal
        titulo = self.fonte_titulo.render("Créditos — Oblivium", True, MARFIM_OFFWHITE)
        tela.blit(titulo, (x + (largura_bloco - titulo.get_width()) // 2, y + 24))

        # Divisória
        pygame.draw.line(tela, CINZA_ARDOSIA, (x + 50, y + 68), (x + largura_bloco - 50, y + 68), 1)

        # Renderização das Linhas de Créditos
        pos_y_atual = y + 82
        largura_util = largura_bloco - 120

        for i, item in enumerate(self.linhas_creditos):
            texto = item["texto"]
            centralizado = item["centralizado"]
            cor = item["cor"]
            tipo = item["tipo"]
            
            if tipo == "secao":
                fonte_utilizada = self.fonte_secao
                # Espaçamento generoso antes de títulos de seção
                if i > 0:
                    pos_y_atual += 14
                else:
                    pos_y_atual += 4
            else:
                fonte_utilizada = self.fonte_texto
            
            linhas_quebradas = self._quebrar_texto(texto, fonte_utilizada, largura_util)
            
            for linha in linhas_quebradas:
                render = fonte_utilizada.render(linha.strip(), True, cor)
                
                if centralizado:
                    pos_x = x + (largura_bloco - render.get_width()) // 2
                else:
                    pos_x = x + 60
                
                tela.blit(render, (pos_x, pos_y_atual))
                pos_y_atual += 26
            
            # Espaçamento após o título da seção ou após o item
            if tipo == "secao":
                pos_y_atual += 6
            else:
                pos_y_atual += 3

        # Aviso de retorno no rodapé
        pos_mouse = pygame.mouse.get_pos()
        hover_voltar = self.rect_voltar.collidepoint(pos_mouse)
        cor_aviso = AZUL_HOVER_MENU if hover_voltar else UI_TEXTO_APAGADO
        aviso = self.fonte_aviso.render("[ Pressione ESC ou clique aqui para voltar ]", True, cor_aviso)
        self.rect_voltar = pygame.Rect(
            x + (largura_bloco - aviso.get_width()) // 2 - 10, 
            y + altura_bloco - 36, 
            aviso.get_width() + 20, 
            aviso.get_height() + 8
        )
        if hover_voltar:
            pygame.draw.rect(tela, AZUL_HOVER_BG, self.rect_voltar, border_radius=3)
            pygame.draw.rect(tela, AZUL_HOVER_MENU, self.rect_voltar, 1, border_radius=3)
        tela.blit(aviso, (x + (largura_bloco - aviso.get_width()) // 2, y + altura_bloco - 32))