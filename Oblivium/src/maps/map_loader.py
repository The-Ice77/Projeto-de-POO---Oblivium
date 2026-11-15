# src/maps/map_loader.py
from src.maps.prologo import MapaCasa, MapaEstrada, MapaEstrada2
from src.maps.oakhaven import (
    MapaOakhaven,
    MapaOrlaNorte,
    MapaOakhavenDestruida,
    MapaNinhoDragao,
)


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
            "ESTRADA_2": MapaEstrada2(game, largura_tela, altura_tela),
            "OAKHAVEN": MapaOakhaven(game, largura_tela, altura_tela),
            "ORLA_NORTE": MapaOrlaNorte(game, largura_tela, altura_tela),
            "OAKHAVEN_DESTRUIDA": MapaOakhavenDestruida(game, largura_tela, altura_tela),
            "NINHO_DRAGAO": MapaNinhoDragao(game, largura_tela, altura_tela),
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

            # Gerenciamento acústico contextual (somente em exploração ativa e sem cutscene sobreposta)
            if self._deve_sincronizar_trilha_cenario():
                trilha = self.obter_trilha_cenario(nome_cenario)
                if trilha:
                    self.game.audio.tocar_musica(trilha, loop=-1, fade_ms=1000, contexto="mundo")
                if hasattr(self.game, "sincronizar_ambiente_cenario"):
                    self.game.sincronizar_ambiente_cenario(fade_ms=900)
        else:
            print(f"[MapLoader] Aviso: Cenário '{nome_cenario}' não reconhecido.")

    def _deve_sincronizar_trilha_cenario(self):
        """Evita que cargas em Menu/Slots, Combate ou Cutscenes troquem a trilha ativa."""
        if not (self.game and getattr(self.game, "audio", None)):
            return False
        if getattr(self.game, "nome_estado_atual", "") != "JOGANDO":
            return False
        if getattr(getattr(self.game, "intro", None), "ativo", False):
            return False
        if getattr(getattr(self.game, "flashback_sistema", None), "estado", "INATIVO") != "INATIVO":
            return False
        if getattr(getattr(self.game, "tela_despertar", None), "estado", "INATIVO") != "INATIVO":
            return False
        if getattr(self.game, "flashback_sylvan_ativo", False):
            return False
        if getattr(self.game, "etapa_epilogo", None) == "DESPERTAR_PENDENTE":
            return False
        if getattr(getattr(self.game, "cinematica_dragao", None), "ativo", False):
            return False
        estados = getattr(self.game, "estados", {}) or {}
        estado_jogando = estados.get("JOGANDO")
        if estado_jogando and (
            getattr(getattr(estado_jogando, "cutscene_reconstrucao", None), "ativo", False)
            or getattr(getattr(estado_jogando, "cinematica_dragao", None), "ativo", False)
        ):
            return False
        return True

    def obter_trilha_cenario(self, nome_cenario=None):
        """Retorna o alias musical contextual correspondente ao cenário e marco narrativo."""
        cen = nome_cenario or self.cenario_atual
        if cen == "CASA":
            return "casa_halia"
        if cen in ("ESTRADA", "ESTRADA_2", "ORLA_NORTE"):
            return "estrada_floresta"
        if cen == "OAKHAVEN":
            return "vila_oakhaven"
        if cen in ("OAKHAVEN_DESTRUIDA", "NINHO_DRAGAO"):
            epilogo_pos = getattr(self.game, "etapa_epilogo", "NAO_INICIADO") in (
                "POS_DRAGAO",
                "DESPERTAR_PENDENTE",
                "RETORNO_VILA",
                "RECONSTRUCAO_PENDENTE",
                "DESPEDIDA_PENDENTE",
                "DEMO_CONCLUIDA",
            )
            cenario_obj = self.cenarios.get(cen, self.cenario_objeto)
            amanhecer_ninho = bool(
                cen == "NINHO_DRAGAO"
                and cenario_obj is not None
                and (getattr(cenario_obj, "ninho_amanhecer", False) or getattr(cenario_obj, "dragao_derrotado", False))
            )
            dragao_vencido = bool(getattr(self.game, "dragao_derrotado", False) or epilogo_pos or amanhecer_ninho)
            if dragao_vencido:
                return "tema_melancolico"
            if cen == "OAKHAVEN_DESTRUIDA":
                return "ataque_dragao"
            return "combate_dragao"
        return None

    # =========================================================================
    # DELEGAÇÃO E PROPRIEDADES POLIMÓRFICAS (COMPATIBILIDADE TOTAL)
    # =========================================================================
    @property
    def largura_mundo(self):
        return getattr(self.cenario_objeto, "largura_mundo", self.largura_tela)

    @property
    def altura_mundo(self):
        return getattr(self.cenario_objeto, "altura_mundo", self.altura_tela)

    @property
    def npcs(self):
        return getattr(self.cenario_objeto, "npcs", [])

    @property
    def animais(self):
        return getattr(self.cenario_objeto, "animais", [])

    @property
    def pontos_interacao(self):
        return getattr(self.cenario_objeto, "pontos_interacao", [])

    @property
    def ervas_coletaveis(self):
        """Retorna a lista de ervas lunares coletáveis do cenário ativo."""
        return getattr(self.cenario_objeto, "ervas_coletaveis", [])

    @ervas_coletaveis.setter
    def ervas_coletaveis(self, nova_lista):
        if hasattr(self.cenario_objeto, "ervas_coletaveis"):
            self.cenario_objeto.ervas_coletaveis = nova_lista

    def respawn_erva_alternativa(self, item_antigo=None):
        """Delega a geração de erva alternativa para o cenário ativo, se suportado."""
        if hasattr(self.cenario_objeto, "respawn_erva_alternativa"):
            return self.cenario_objeto.respawn_erva_alternativa(item_antigo)
        return None
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
            if hasattr(self.game, 'audio') and self.game.audio:
                self.game.audio.tocar_sfx("porta_abrir")

    def fechar_porta(self):
        """Dispara o fechamento e tranca da porta na casa."""
        mapa_casa = self.cenarios.get("CASA")
        if mapa_casa:
            mapa_casa.fechar_porta()
            if hasattr(self.game, 'audio') and self.game.audio:
                self.game.audio.tocar_sfx("porta_fechar")

    def desobstruir_estrada(self, tipo_magia="FOGO"):
        """Desobstrui o deslizamento de rochas na Estrada 2."""
        mapa_estrada2 = self.cenarios.get("ESTRADA_2")
        if mapa_estrada2:
            mapa_estrada2.desobstruir_estrada(tipo_magia)

    def restaurar_bloqueio_estrada2(self):
        """Restaura as rochas de bloqueio originais na Estrada 2."""
        mapa_estrada2 = self.cenarios.get("ESTRADA_2")
        if mapa_estrada2:
            mapa_estrada2.restaurar_bloqueio()

    def atualizar_levitacao_minigame(self, progresso_pct):
        """Atualiza a posição em tempo real e os efeitos visuais das rochas no minigame de levitação."""
        mapa_estrada2 = self.cenarios.get("ESTRADA_2")
        if mapa_estrada2 and hasattr(mapa_estrada2, "atualizar_levitacao_minigame"):
            mapa_estrada2.atualizar_levitacao_minigame(progresso_pct)

    def obter_hitboxes(self):
        """Retorna as hitboxes ativas do cenário atual."""
        return self.cenario_objeto.obter_hitboxes()

    def obter_itens(self):
        """Retorna os itens no chão do cenário atual."""
        return self.cenario_objeto.obter_itens()

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

    def obter_superficie_passo(self, x, y):
        """Delega a detecção da superfície de pisada ao cenário ativo."""
        if hasattr(self.cenario_objeto, "obter_superficie_passo"):
            return self.cenario_objeto.obter_superficie_passo(x, y)
        return "grama"

    def obter_ambiente_cenario(self):
        """Delega a seleção do loop de ambiente ao cenário ativo."""
        if hasattr(self.cenario_objeto, "obter_ambiente_cenario"):
            return self.cenario_objeto.obter_ambiente_cenario()
        return None


# Alias semântico para arquitetura limpa
MapLoader = Mapa
MapManager = Mapa