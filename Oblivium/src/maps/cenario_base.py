# src/maps/cenario_base.py
from abc import ABC, abstractmethod
import pygame


class CenarioBase(ABC):
    """
    Classe Abstrata de Referência para todos os cenários/mapas de Oblivium.
    Estabelece o contrato polimórfico de carregamento de recursos, atualização,
    colisões (hitboxes 2.5D), gerenciamento de itens no chão e renderização em camadas.
    
    Arquitetura de Renderização:
    - Camada Inferior: Pisos, caminhos, tapetes, sombras de construções.
    - Camada de Objetos e Paredes: Estruturas colidíveis, móveis e props com Y-Sort.
    - Camada Superior: Telhados, beirais e copas de árvores (passam por cima do jogador).
    """

    def __init__(self, game, largura_tela, altura_tela, nome):
        self.game = game
        self.largura_tela = largura_tela
        self.altura_tela = altura_tela
        self.nome = nome
        self.hitboxes = []
        self.itens_no_chao = []
        self.carregar_recursos()

    @abstractmethod
    def carregar_recursos(self):
        """Carrega e armazena em cache as texturas e sprites específicas do cenário."""
        pass

    @abstractmethod
    def inicializar_cenario(self):
        """Configura hitboxes iniciais, itens no chão e pontos de interação do mapa."""
        pass

    def atualizar(self, dt=0.016):
        """Atualiza animações de ambiente, partículas ou props dinâmicos."""
        pass

    @abstractmethod
    def desenhar_camada_inferior(self, tela):
        """Renderiza o chão, pisos, calçamento, terra e detalhes de relevo plano."""
        pass

    def desenhar_props(self, tela):
        """Renderiza móveis, paredes, construções e decorações fixas do cenário."""
        pass

    def desenhar_camada_superior(self, tela):
        """Renderiza telhados, beirais e copas de árvores que cobrem o jogador (Z-Index alto)."""
        pass

    def desenhar(self, tela):
        """
        Método template padrão de renderização do cenário.
        Executa a renderização do piso, dos props fixos e dos itens no chão.
        """
        self.desenhar_camada_inferior(tela)
        self.desenhar_props(tela)
        for item in self.itens_no_chao:
            item.desenhar(tela)

    def obter_hitboxes(self):
        """Retorna a lista de retângulos colidíveis ativos no mapa."""
        return self.hitboxes

    def obter_itens(self):
        """Retorna a lista de itens coletáveis atualmente no chão."""
        return self.itens_no_chao
