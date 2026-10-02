# src/maps/map_loader.py
import pygame
from src.maps.mapa_casa import MapaCasa
from src.maps.mapa_estrada import MapaEstrada
from src.maps.mapa_estrada_2 import MapaEstrada2


class Mapa:
    """
    Gerenciador e Carregador Central de Mapas (MapLoader / MapManager).
    Atua como Fachada (Facade) e Orquestrador dos cenários de Oblivium,
    delegando operações polimorficamente para as instâncias de CenarioBase.
    
    Mantém compatibilidade integral com o Game Loop, salvamento de slots
    e máquinas de estado (PlayingState).
    """

    def __init__(self, game, largura_tela, altura_tela):
        self.game = game
        self.largura_tela = largura_tela
        self.altura_tela = altura_tela

        # Catálogo de instâncias dos cenários modulares
        self.cenarios = {
            "CASA": MapaCasa(game, largura_tela, altura_tela),
            "ESTRADA": MapaEstrada(game, largura_tela, altura_tela),
            "ESTRADA_2": MapaEstrada2(game, largura_tela, altura_tela)
        }

        self.cenario_atual = "CASA"
        self.cenario_objeto = self.cenarios["CASA"]
        self.carregar_cenario("CASA")

    def carregar_cenario(self, nome_cenario):
        """
        Alterna o cenário ativo e reinicializa suas hitboxes e itens de acordo
        com o progresso salvo e itens já coletados.
        """
        if nome_cenario in self.cenarios:
            self.cenario_atual = nome_cenario
            self.cenario_objeto = self.cenarios[nome_cenario]
            self.cenario_objeto.inicializar_cenario()
        else:
            print(f"[MapLoader] Aviso: Cenário '{nome_cenario}' não reconhecido.")

    # =========================================================================
    # DELEGAÇÃO E PROPRIEDADES POLIMÓRFICAS (COMPATIBILIDADE TOTAL)
    # =========================================================================
    @property
    def hitboxes(self):
        """Retorna a lista viva de hitboxes do cenário ativo."""
        return self.cenario_objeto.hitboxes

    @hitboxes.setter
    def hitboxes(self, nova_lista):
        self.cenario_objeto.hitboxes = nova_lista

    @property
    def itens_no_chao(self):
        """Retorna a lista de itens coletáveis no chão do cenário ativo."""
        return self.cenario_objeto.itens_no_chao

    @itens_no_chao.setter
    def itens_no_chao(self, nova_lista):
        self.cenario_objeto.itens_no_chao = nova_lista

    @property
    def porta(self):
        """Gatilho da porta da casa."""
        return getattr(self.cenarios.get("CASA"), "porta", None)

    @property
    def porta_aberta(self):
        """Status de abertura da porta da casa."""
        return getattr(self.cenarios.get("CASA"), "porta_aberta", False)

    @porta_aberta.setter
    def porta_aberta(self, valor):
        mapa_casa = self.cenarios.get("CASA")
        if mapa_casa:
            mapa_casa.porta_aberta = valor
            if valor and mapa_casa.porta in mapa_casa.hitboxes:
                mapa_casa.hitboxes.remove(mapa_casa.porta)

    @property
    def pedras_deslizamento(self):
        """Retângulos das pedras de bloqueio na Estrada 2."""
        return getattr(self.cenarios.get("ESTRADA_2"), "pedras_deslizamento", [])

    @pedras_deslizamento.setter
    def pedras_deslizamento(self, lista):
        mapa_estrada2 = self.cenarios.get("ESTRADA_2")
        if mapa_estrada2:
            mapa_estrada2.pedras_deslizamento = lista

    def abrir_porta(self):
        """Dispara a abertura da porta na casa."""
        mapa_casa = self.cenarios.get("CASA")
        if mapa_casa:
            mapa_casa.abrir_porta()

    def desobstruir_estrada(self, tipo_magia="FOGO"):
        """Desobstrui o deslizamento de rochas na Estrada 2."""
        mapa_estrada2 = self.cenarios.get("ESTRADA_2")
        if mapa_estrada2:
            mapa_estrada2.desobstruir_estrada(tipo_magia)

    # =========================================================================
    # CICLO DE RENDERIZAÇÃO
    # =========================================================================
    def atualizar(self, dt=0.016):
        """Atualiza a lógica interna do cenário corrente."""
        self.cenario_objeto.atualizar(dt)

    def desenhar(self, tela):
        """Delega a renderização para o cenário concreto ativo."""
        self.cenario_objeto.desenhar(tela)

    def desenhar_camada_superior(self, tela):
        """Delega a renderização de elementos que ficam acima do jogador (copas/telhados)."""
        self.cenario_objeto.desenhar_camada_superior(tela)


# Alias semântico para arquitetura limpa
MapLoader = Mapa
MapManager = Mapa