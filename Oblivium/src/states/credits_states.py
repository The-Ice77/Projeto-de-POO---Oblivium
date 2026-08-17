# src/states/credits_states.py
import pygame
from src.states.states import State
from src.utils.colors import PRETO, BRANCO, UI_FUNDO_PADRAO, CINZA_CLARO, UI_TEXTO_DESTAQUE, UI_TEXTO_APAGADO, TXT_SISTEMA_NARRADOR

class CreditsState(State):
    def __init__(self, game):
        super().__init__(game)
        self.fonte_titulo = pygame.font.Font(None, 50)
        self.fonte_texto = pygame.font.Font(None, 26)
        self.fonte_secao = pygame.font.Font(None, 32)
        self.fonte_aviso = pygame.font.Font(None, 22)
        
        self.rect_voltar = pygame.Rect(0, 0, 0, 0)
        
        # --- ESTRUTURA DE CRÉDITOS ---
        # Cada item é um dicionário: {"texto": "...", "tipo": "secao/cargo/normal", "centralizado": True/False, "cor": (r,g,b)}
        self.linhas_creditos = [
            # Secção 1
            {"texto": "— DESENVOLVIMENTO PRINCIPAL —", "tipo": "secao", "centralizado": True, "cor": TXT_SISTEMA_NARRADOR},
            {"texto": "Programação e Arquitetura: João Victor", "tipo": "normal", "centralizado": False, "cor": BRANCO},
            {"texto": "Design de UI e Sistemas: Equipe Oblivium", "tipo": "normal", "centralizado": False, "cor": BRANCO},
            
            # Secção 2
            {"texto": "— ARTE E VISUAL —", "tipo": "secao", "centralizado": True, "cor": TXT_SISTEMA_NARRADOR},
            {"texto": "Pixel Art e Cenários: Davi Suassuna", "tipo": "normal", "centralizado": False, "cor": BRANCO},
            
            # Secção 3
            {"texto": "— ROTEIRO E ÁUDIO —", "tipo": "secao", "centralizado": True, "cor": TXT_SISTEMA_NARRADOR},
            {"texto": "História e Diálogos: Equipe Oblivium", "tipo": "normal", "centralizado": False, "cor": BRANCO},
            
            # Secção 4
            {"texto": "— AGRADECIMENTOS —", "tipo": "secao", "centralizado": True, "cor": TXT_SISTEMA_NARRADOR},
            {"texto": "Um agradecimento especial ao professor Max Miller e a todos os colegas que apoiaram este projeto de Programação Orientada a Objetos.", "tipo": "normal", "centralizado": True, "cor": UI_TEXTO_DESTAQUE}
        ]

    def handle_events(self, eventos, teclas):
        for evento in eventos:
            if evento.type == pygame.KEYDOWN:
                if evento.key in [pygame.K_ESCAPE, pygame.K_RETURN]:
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
            teste_linha = linha_atual + palavra + " "
            if fonte.size(teste_linha)[0] <= largura_maxima:
                linha_atual = teste_linha
            else:
                if linha_atual: 
                    linhas.append(linha_atual)
                linha_atual = palavra + " "
        if linha_atual: 
            linhas.append(linha_atual)
        return linhas

    def draw(self, tela):
        tela.fill(PRETO)
        
        largura_bloco = 820
        altura_bloco = 560
        x = (self.game.LARGURA - largura_bloco) // 2
        y = (self.game.ALTURA - altura_bloco) // 2

        # Caixa de fundo no estilo UI do jogo
        pygame.draw.rect(tela, UI_FUNDO_PADRAO, (x, y, largura_bloco, altura_bloco))
        pygame.draw.rect(tela, CINZA_CLARO, (x, y, largura_bloco, altura_bloco), 2)

        # Título Principal
        titulo = self.fonte_titulo.render("Créditos - Oblivium", True, UI_TEXTO_DESTAQUE)
        tela.blit(titulo, (x + (largura_bloco - titulo.get_width()) // 2, y + 25))

        # Renderização Inteligente das Linhas com Quebra de Texto
        pos_y_atual = y + 90
        largura_util = largura_bloco - 100 # Margem interna de 50px para cada lado

        for item in self.linhas_creditos:
            texto = item["texto"]
            centralizado = item["centralizado"]
            cor = item["cor"]
            tipo = item["tipo"]
            
            # Escolhe a fonte com base no tipo de linha
            fonte_utilizada = self.fonte_secao if tipo == "secao" else self.fonte_texto
            
            # Quebra o texto se ultrapassar a largura da caixa
            linhas_quebradas = self._quebrar_texto(texto, fonte_utilizada, largura_util)
            
            for linha in linhas_quebradas:
                render = fonte_utilizada.render(linha.strip(), True, cor)
                
                if centralizado:
                    pos_x = x + (largura_bloco - render.get_width()) // 2
                else:
                    pos_x = x + 50 # Alinhado à esquerda com margem
                
                tela.blit(render, (pos_x, pos_y_atual))
                pos_y_atual += 30 # Espaçamento vertical entre as linhas geradas
            
            # Pequeno espaçamento extra após cada secção/bloco
            pos_y_atual += 6

        # Aviso de retorno no rodapé
        aviso = self.fonte_aviso.render("Pressione [ESC] ou clique aqui para voltar", True, UI_TEXTO_APAGADO)
        self.rect_voltar = pygame.Rect(
            x + (largura_bloco - aviso.get_width()) // 2, 
            y + altura_bloco - 40, 
            aviso.get_width(), 
            aviso.get_height()
        )
        tela.blit(aviso, (self.rect_voltar.x, self.rect_voltar.y))