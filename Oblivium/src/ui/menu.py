# src/ui/menu.py
import pygame
from src.utils.colors import PRETO
from src.utils import save_manager
from src.utils.resource_manager import ResourceManager
from src.utils.animations import EfeitoPetalas
from src.ui.ui_utils import BotaoGrafico

class Menu:
    """
    Gerencia a tela inicial de Oblivium com artes em alta definição,
    fundo 100% preto puro, pétalas transparentes em segundo plano,
    botões com espaçamento refinado e hover fiel às proporções originais.
    """
    def __init__(self):
        self.largura = 1280
        self.altura = 720
        self.margem_x = 80
        
        self.opcoes = []
        self.selecionada = -1  # Desativo por padrão até o mouse/teclado interagir
        self.cor_fundo = PRETO  # Fundo totalmente preto puro (0, 0, 0)
        
        # Sistema de partículas de pétalas caindo ao fundo (sem fundo preto)
        self.efeito_petalas = EfeitoPetalas(self.largura, self.altura, quantidade_petalas=22)
        
        # Carregamento e dimensionamento dos elementos visuais
        self._carregar_artes()
        self._criar_botoes()
        self.atualizar_opcoes()

    def _carregar_artes(self):
        """Carrega e escala as ilustrações e textos gráficos da tela inicial em alta definição."""
        # 1. Título e Subtítulo
        self.img_titulo = ResourceManager.carregar_imagem_com_transparencia(
            "menu inicial/título e subtítulo.png",
            tamanho=(550, 225),
            manter_proporcao=True
        )
        self.pos_titulo = (self.margem_x, 30)

        # 2. Versão do Jogo (Canto inferior direito)
        self.img_versao = ResourceManager.carregar_imagem_com_transparencia(
            "menu inicial/versão do jogo.png",
            tamanho=(210, 44),
            manter_proporcao=True
        )
        if self.img_versao:
            v_w, v_h = self.img_versao.get_size()
            self.pos_versao = (self.largura - v_w - 40, self.altura - v_h - 26)
        else:
            self.pos_versao = (self.largura - 220, self.altura - 40)

        # 3. Texto Especial (Alinhado à esquerda na mesma linha de altura da versão)
        self.img_texto_especial = ResourceManager.carregar_imagem_com_transparencia(
            "menu inicial/texto especial.png",
            tamanho=(330, 44),
            manter_proporcao=True
        )
        if self.img_texto_especial:
            te_w, te_h = self.img_texto_especial.get_size()
            pos_y_especial = self.pos_versao[1] + ((self.img_versao.get_height() - te_h) // 2 if self.img_versao else 0)
            self.pos_texto_especial = (self.margem_x, pos_y_especial)
        else:
            self.pos_texto_especial = (self.margem_x, self.pos_versao[1])

    def _criar_botoes(self):
        """
        Prepara os botões com escala compacta proporcional (0.125),
        tornando os botões originais menores e harmonizados com o hover.
        """
        escala_uniforme_botoes = 0.125
        
        nomes_botoes = {
            "Novo Jogo": ("menu inicial/novo jogo.png", "menu inicial/novo jogo hover.png"),
            "Continuar": ("menu inicial/continuar.png", "menu inicial/continuar hover.png"),
            "Configurações": ("menu inicial/configurações.png", "menu inicial/configurações hover.png"),
            "Créditos": ("menu inicial/créditos.png", "menu inicial/créditos hover.png"),
            "Sair": ("menu inicial/sair.png", "menu inicial/sair hover.png")
        }

        self.botoes = {}
        for id_opcao, (path_norm, path_hov) in nomes_botoes.items():
            img_norm = ResourceManager.carregar_imagem_com_transparencia(
                path_norm, escala_fator=escala_uniforme_botoes
            )
            img_hov = ResourceManager.carregar_imagem_com_transparencia(
                path_hov, escala_fator=escala_uniforme_botoes
            )
            self.botoes[id_opcao] = BotaoGrafico(id_opcao, img_norm, img_hov)

    def atualizar_opcoes(self):
        """Atualiza a lista de opções com base na presença de saves e posiciona com espaçamento aprimorado."""
        if save_manager.verificar_saves_globais():
            self.opcoes = ["Novo Jogo", "Continuar", "Configurações", "Créditos", "Sair"]
        else:
            self.opcoes = ["Novo Jogo", "Configurações", "Créditos", "Sair"]

        if self.selecionada >= len(self.opcoes):
            self.selecionada = -1

        # Reposicionar botões verticalmente com espaçamento compacto (60px entre botões)
        y_inicial = 305
        espacamento_y = 60
        for i, opcao in enumerate(self.opcoes):
            if opcao in self.botoes:
                self.botoes[opcao].definir_posicao(self.margem_x, y_inicial + i * espacamento_y)

    def atualizar(self, dt=0.016):
        """Atualiza a simulação das pétalas e o estado de animação dos botões."""
        self.efeito_petalas.atualizar(dt)

        for i, opcao in enumerate(self.opcoes):
            if opcao in self.botoes:
                esta_ativo = (i == self.selecionada)
                self.botoes[opcao].atualizar(esta_ativo, dt)

    def atualizar_mouse(self, pos_mouse):
        """Atualiza a opção selecionada pelo mouse; se fora de todos os botões, desativa o hover."""
        hover_encontrado = False
        for i, opcao in enumerate(self.opcoes):
            if opcao in self.botoes and self.botoes[opcao].colide(pos_mouse):
                self.selecionada = i
                hover_encontrado = True
                break
        if not hover_encontrado:
            self.selecionada = -1

    def clicar_mouse(self, pos_mouse):
        """Retorna a opção clicada se o mouse colidir com algum botão."""
        for i, opcao in enumerate(self.opcoes):
            if opcao in self.botoes and self.botoes[opcao].colide(pos_mouse):
                return opcao
        return None

    def desenhar(self, tela):
        """Renderiza a composição visual da tela inicial com fundo 100% preto puro."""
        # 1. Fundo 100% preto puro
        tela.fill(self.cor_fundo)

        # 2. Pétalas caindo ao fundo com transparência alfa limpa
        self.efeito_petalas.desenhar(tela)

        # 3. Título e Subtítulo
        if self.img_titulo:
            tela.blit(self.img_titulo, self.pos_titulo)

        # 4. Botões do Menu (Hover substitui o normal no tamanho original centralizado)
        for i, opcao in enumerate(self.opcoes):
            if opcao in self.botoes:
                self.botoes[opcao].desenhar(tela, selecionado=(i == self.selecionada))

        # 5. Texto Especial (abaixo das opções)
        if self.img_texto_especial:
            tela.blit(self.img_texto_especial, self.pos_texto_especial)

        # 6. Versão do Jogo (canto inferior direito)
        if self.img_versao:
            tela.blit(self.img_versao, self.pos_versao)