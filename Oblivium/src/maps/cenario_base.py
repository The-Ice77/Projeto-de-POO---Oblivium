# src/maps/cenario_base.py
from abc import ABC, abstractmethod


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

    def __init__(self, game, largura_tela, altura_tela, nome, largura_mundo=None, altura_mundo=None):
        self.game = game
        self.largura_tela = largura_tela
        self.altura_tela = altura_tela
        self.largura_mundo = int(largura_mundo) if largura_mundo else int(largura_tela)
        self.altura_mundo = int(altura_mundo) if altura_mundo else int(altura_tela)
        self.nome = nome
        self.hitboxes = []
        self.itens_no_chao = []
        self.npcs = []
        self.animais = []
        self.pontos_interacao = []
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
    def desenhar_camada_inferior(self, tela, area_visivel=None):
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

    def obter_superficie_passo(self, x, y):
        """Identifica a superfície sob o personagem ('grama' ou 'pedra') para passos."""
        grade = getattr(self, "grade", None)
        if grade:
            col = int(x // 32)
            lin = int(y // 32)
            if 0 <= lin < len(grade) and 0 <= col < len(grade[0]):
                if grade[lin][col] in (2, 3):
                    return "pedra"
        area_casa = getattr(self, "area_chao_casa", None)
        if area_casa and area_casa.collidepoint(int(x), int(y)):
            return "pedra"
        if str(getattr(self, "nome", "") or "").upper() == "NINHO_DRAGAO":
            return "pedra"
        return "grama"

    def obter_ambiente_cenario(self):
        """Retorna o alias do loop de ambiente contínuo apropriado ao cenário ativo."""
        nome_cen = str(getattr(self, "nome", "") or "").upper()
        if nome_cen in ("ESTRADA", "ESTRADA_2", "ORLA_NORTE"):
            return "floresta_dia"
        if nome_cen == "OAKHAVEN":
            return "vento_suave"
        if nome_cen == "OAKHAVEN_DESTRUIDA":
            if self.game and getattr(self.game, "oakhaven_reconstruida", False):
                return "vento_suave"
            return "fogueira"
        if nome_cen == "NINHO_DRAGAO":
            vencido = bool(
                getattr(self, "dragao_derrotado", False)
                or getattr(self, "ninho_amanhecer", False)
                or (self.game and getattr(self.game, "dragao_derrotado", False))
            )
            return "vento_suave" if vencido else "caverna_lava"
        if nome_cen == "FLASHBACK_ACAMPAMENTO":
            return "fogueira"
        if nome_cen == "CASA" and getattr(self, "noite_ativa", False):
            return "fogueira"
        return None
