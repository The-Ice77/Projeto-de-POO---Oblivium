# src/mechanics/quest_manager.py
import json
import os
import logging
import copy

logger = logging.getLogger(__name__)

DIRETORIO_ATUAL = os.path.dirname(os.path.abspath(__file__))
DIRETORIO_SRC = os.path.dirname(DIRETORIO_ATUAL)
ARQUIVO_MISSOES_CATALOGO = os.path.join(DIRETORIO_SRC, "data", "missoes.json")


class QuestManager:
    """
    Gerenciador Central de Missões (Quests) de Oblivium.

    Responsabilidades:
    - Carregamento e instanciação de missões a partir do catálogo JSON.
    - Gestão de ciclo de vida das missões: DISPONIVEL -> ATIVA -> CONCLUIDA.
    - Regra de simultaneidade estrita: o jogador pode ter ativa no máximo
      1 missão PRINCIPAL e 1 missão SECUNDARIA por vez (exibidas juntas no HUD).
    - Acompanhamento detalhado de objetivos com contadores e conclusão automática de etapas.
    - Entrega de recompensas (ouro, itens e experiência) e conquista 'cumpridor_promessas' ao concluir.
    - Serialização/desserialização integrada com o SaveManager.
    """

    def __init__(self, game=None):
        self.game = game
        self.catalogo_base = []
        self.missoes = {}
        self.missao_rastreada_id = None
        self._carregar_catalogo()
        self.resetar()

    def _carregar_catalogo(self):
        """Carrega o catálogo original de missões do arquivo data/missoes.json."""
        if os.path.exists(ARQUIVO_MISSOES_CATALOGO):
            try:
                with open(ARQUIVO_MISSOES_CATALOGO, "r", encoding="utf-8") as f:
                    dados = json.load(f)
                    self.catalogo_base = dados.get("missoes", [])
            except Exception as e:
                logger.error(f"[QuestManager] Erro ao carregar catalogo de missoes: {e}")
                self.catalogo_base = []

    def resetar(self):
        """Reinicia todas as missões para o estado inicial definido no catálogo."""
        self.missoes = {}
        for m in self.catalogo_base:
            mid = m.get("id")
            if mid:
                self.missoes[mid] = copy.deepcopy(m)
        self.missao_rastreada_id = None

    def obter_missao_ativa_por_categoria(self, categoria):
        """Retorna a missão atualmente ATIVA da categoria informada ('PRINCIPAL' ou 'SECUNDARIA'), ou None."""
        cat_alvo = (categoria or "PRINCIPAL").upper()
        for m in self.missoes.values():
            if m.get("status") == "ATIVA" and m.get("categoria", "SECUNDARIA").upper() == cat_alvo:
                return m
        return None

    def obter_missao_principal_ativa(self):
        """Retorna a missão PRINCIPAL atualmente ativa, ou None."""
        return self.obter_missao_ativa_por_categoria("PRINCIPAL")

    def obter_missao_secundaria_ativa(self):
        """Retorna a missão SECUNDARIA atualmente ativa, ou None."""
        return self.obter_missao_ativa_por_categoria("SECUNDARIA")

    def aceitar_missao(self, id_missao, substituir_categoria=False):
        """
        Transiciona uma missão do estado DISPONIVEL para ATIVA, respeitando o limite
        de no máximo 1 missão PRINCIPAL e 1 missão SECUNDARIA ativas por vez.
        """
        if id_missao not in self.missoes:
            return False

        missao = self.missoes[id_missao]
        if missao["status"] == "ATIVA":
            return False  # Já está ativa
        if missao["status"] == "CONCLUIDA":
            return False  # Já foi concluída

        categoria = missao.get("categoria", "SECUNDARIA").upper()
        ativa_mesma_cat = self.obter_missao_ativa_por_categoria(categoria)

        if ativa_mesma_cat and ativa_mesma_cat["id"] != id_missao:
            if substituir_categoria:
                ativa_mesma_cat["status"] = "DISPONIVEL"
            else:
                # Limite atingido para esta categoria (1 Principal + 1 Secundária por vez)
                return False

        missao["status"] = "ATIVA"

        if not self.missao_rastreada_id:
            self.missao_rastreada_id = id_missao

        # Notificação Push no Centro Superior
        if self.game and hasattr(self.game, 'notificacoes') and self.game.notificacoes:
            tipo_lbl = "Principal" if categoria == "PRINCIPAL" else "Secundária"
            self.game.notificacoes.notificar(
                "notificacao_missao",
                missao=f"Missão {tipo_lbl}: {missao['titulo']}"
            )

        # Efeito Sonoro
        if self.game and hasattr(self.game, 'audio') and self.game.audio:
            self.game.audio.tocar_sfx("ui_confirmar")

        return True

    def progredir_objetivo(self, id_missao, id_ou_indice_obj, quantidade=1):
        """
        Incrementa o contador de um objetivo específico de uma missão ativa.
        Se todos os objetivos forem completados, conclui a missão automaticamente.
        """
        if id_missao not in self.missoes:
            return False

        missao = self.missoes[id_missao]
        if missao["status"] != "ATIVA":
            return False

        objetivo_alvo = None
        if isinstance(id_ou_indice_obj, int):
            if 0 <= id_ou_indice_obj < len(missao["objetivos"]):
                objetivo_alvo = missao["objetivos"][id_ou_indice_obj]
        else:
            for obj in missao["objetivos"]:
                if obj.get("id") == str(id_ou_indice_obj):
                    objetivo_alvo = obj
                    break

        if not objetivo_alvo or objetivo_alvo.get("concluido", False):
            return False

        atual = objetivo_alvo.get("atual", 0) + quantidade
        alvo = objetivo_alvo.get("alvo", 1)
        objetivo_alvo["atual"] = min(alvo, atual)

        if objetivo_alvo["atual"] >= alvo:
            objetivo_alvo["concluido"] = True
            if self.game and hasattr(self.game, 'notificacoes') and self.game.notificacoes:
                self.game.notificacoes.notificar(
                    "notificacao_missao",
                    missao=f"Objetivo: {objetivo_alvo['descricao']} (Concluído)"
                )

        # Verifica se todos os objetivos foram completados
        todos_concluidos = all(o.get("concluido", False) for o in missao["objetivos"])
        if todos_concluidos:
            self.concluir_missao(id_missao)

        return True

    def concluir_missao(self, id_missao):
        """Marca a missão como concluída, entrega recompensas e desbloqueia a conquista 'cumpridor_promessas'."""
        if id_missao not in self.missoes:
            return False

        missao = self.missoes[id_missao]
        if missao["status"] == "CONCLUIDA":
            return False

        missao["status"] = "CONCLUIDA"

        # Entrega recompensas
        recompensas = missao.get("recompensas", {})
        if self.game and hasattr(self.game, 'halia') and self.game.halia:
            moedas = recompensas.get("dinheiro", 0)
            if moedas > 0:
                self.game.halia.ganhar_dinheiro(moedas)

        # Desbloqueia a conquista especial de conclusão de missão
        if self.game and hasattr(self.game, 'conquistas') and self.game.conquistas:
            self.game.conquistas.desbloquear("cumpridor_promessas")

        # Notificação Push de Conclusão
        if self.game and hasattr(self.game, 'notificacoes') and self.game.notificacoes:
            self.game.notificacoes.notificar(
                "notificacao_missao",
                missao=f"Missão Concluída: {missao['titulo']}"
            )

        if self.game and hasattr(self.game, 'audio') and self.game.audio:
            self.game.audio.tocar_sfx("ui_confirmar")

        if self.missao_rastreada_id == id_missao:
            ativas = self.obter_missoes_ativas()
            self.missao_rastreada_id = ativas[0]["id"] if ativas else None

        return True

    def obter_missoes_ativas(self):
        """
        Retorna as missões atualmente ativas (no máximo 1 PRINCIPAL e 1 SECUNDARIA),
        sempre ordenadas com a PRINCIPAL primeiro e a SECUNDARIA em seguida.
        """
        principal = self.obter_missao_principal_ativa()
        secundaria = self.obter_missao_secundaria_ativa()
        ativas = []
        if principal:
            ativas.append(principal)
        if secundaria:
            ativas.append(secundaria)
        return ativas

    def obter_missoes_rastreadas(self):
        """Retorna a lista de missões exibidas juntas no HUD Tracker (1 Principal e 1 Secundária)."""
        return self.obter_missoes_ativas()

    def obter_missao_rastreada(self):
        """Retorna a missão principal ativa (ou a secundária ativa) por retrocompatibilidade."""
        ativas = self.obter_missoes_ativas()
        if ativas:
            self.missao_rastreada_id = ativas[0]["id"]
            return ativas[0]
        self.missao_rastreada_id = None
        return None

    def definir_missao_rastreada(self, id_missao):
        """Altera a missão prioritária se estiver ativa."""
        if id_missao in self.missoes and self.missoes[id_missao]["status"] == "ATIVA":
            self.missao_rastreada_id = id_missao
            return True
        return False

    def _sanitizar_limite_simultaneo(self):
        """Garante que no máximo 1 PRINCIPAL e 1 SECUNDARIA estejam com status ATIVA."""
        tem_principal = False
        tem_secundaria = False
        for m in self.missoes.values():
            if m.get("status") == "ATIVA":
                cat = m.get("categoria", "SECUNDARIA").upper()
                if cat == "PRINCIPAL":
                    if tem_principal:
                        m["status"] = "DISPONIVEL"
                    else:
                        tem_principal = True
                else:
                    if tem_secundaria:
                        m["status"] = "DISPONIVEL"
                    else:
                        tem_secundaria = True

    def to_dict(self):
        """Serializa todo o estado das missões para gravação no SaveManager."""
        return {
            "rastreada": self.missao_rastreada_id,
            "missoes": self.missoes
        }

    def from_dict(self, dados):
        """Restaura o estado completo das missões a partir de um save salvo."""
        if not dados or not isinstance(dados, dict):
            return

        self.missao_rastreada_id = dados.get("rastreada")
        missoes_salvas = dados.get("missoes", {})

        for mid, m_dados in missoes_salvas.items():
            self.missoes[mid] = copy.deepcopy(m_dados)

        self._sanitizar_limite_simultaneo()
