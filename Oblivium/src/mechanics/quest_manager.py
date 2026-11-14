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
    - Acompanhamento detalhado de objetivos de campo vs. objetivo final de entrega no NPC:
      cumprir os requisitos de campo NÃO conclui a missão sozinho à distância; exige
      interagir novamente com o NPC doador para entregar e concluir a missão.
    - Trava do NPC doador (e bloqueio de sua loja) enquanto a missão estiver ATIVA.
    - Entrega de recompensas (ouro, itens e experiência) e conquista 'cumpridor_promessas' ao concluir.
    - Serialização/desserialização integrada com o SaveManager.
    """

    VERSAO_SCHEMA_SAVE = 2

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

    @staticmethod
    def _eh_objetivo_entrega_npc(obj):
        """Identifica se um objetivo é o passo final de entrega/retorno presencial ao NPC."""
        if not isinstance(obj, dict):
            return False
        if obj.get("tipo") == "entrega_npc":
            return True
        oid = str(obj.get("id", "")).lower()
        return oid.startswith(("entregar_", "relatar_", "retornar_", "falar_anciao"))

    def obter_missao(self, id_missao):
        """Retorna o dicionário de dados da missão pelo ID, ou None."""
        return self.missoes.get(id_missao)

    def ativar_missao(self, id_missao, substituir_categoria=False):
        """Alias para aceitar_missao."""
        return self.aceitar_missao(id_missao, substituir_categoria=substituir_categoria)

    def atualizar_progresso(self, id_objetivo, quantidade=1, via_interacao_npc=False):
        """
        Progride o objetivo `id_objetivo` em qualquer missão atualmente ATIVA que o contenha.
        """
        progrediu = False
        for mid, missao in self.missoes.items():
            if missao.get("status") == "ATIVA":
                if self.progredir_objetivo(mid, id_objetivo, quantidade=quantidade, via_interacao_npc=via_interacao_npc):
                    progrediu = True
        return progrediu

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

    def obter_missao_ativa_do_npc(self, npc_id_ou_nome):
        """
        Retorna a missão atualmente ATIVA pertencente ao NPC informado (por `npc_id` ou `doador`),
        ou None caso o NPC não tenha missão ativa em andamento.
        """
        if not npc_id_ou_nome:
            return None
        chave = str(npc_id_ou_nome).strip().lower()
        for m in self.missoes.values():
            if m.get("status") == "ATIVA":
                npc_id_m = str(m.get("npc_id", "")).strip().lower()
                doador_m = str(m.get("doador", "")).strip().lower()
                if chave in (npc_id_m, doador_m):
                    return m
        return None

    def _obter_inventario_jogador(self):
        """Retorna o inventário da jogadora quando disponível na sessão atual."""
        halia = getattr(self.game, "halia", None) if self.game else None
        return getattr(halia, "inventario", None) if halia else None

    def pronta_para_entregar(self, id_missao):
        """
        Verifica se uma missão ATIVA já teve todos os seus requisitos de campo cumpridos,
        restando apenas interagir novamente com o NPC doador para concluí-la.
        """
        if id_missao not in self.missoes:
            return False
        missao = self.missoes[id_missao]
        if missao.get("status") != "ATIVA":
            return False

        objetivos = missao.get("objetivos", [])
        requisitos_entrega = missao.get("requisitos_entrega", [])
        if not objetivos and not requisitos_entrega:
            return True

        # Validação e sincronização genérica dos itens declarados em 'requisitos_entrega'
        if requisitos_entrega:
            inventario = self._obter_inventario_jogador()
            if not inventario:
                return False
            objs_campo_padrao = [o for o in objetivos if not self._eh_objetivo_entrega_npc(o)]
            for req in requisitos_entrega:
                item_id = req.get("item_id")
                qtd_req = int(req.get("quantidade", 1))
                obj_id_req = req.get("objetivo_id")
                qtd_possuida = inventario.obter_quantidade(item_id) if item_id else 0
                if qtd_possuida >= qtd_req:
                    for obj in objetivos:
                        if (obj_id_req and obj.get("id") == obj_id_req) or (
                            not obj_id_req and objs_campo_padrao and obj is objs_campo_padrao[0]
                        ):
                            obj["atual"] = max(obj.get("atual", 0), qtd_req)
                            obj["concluido"] = True
                else:
                    return False

        objs_campo = [o for o in objetivos if not self._eh_objetivo_entrega_npc(o)]
        if objs_campo:
            if not all(o.get("concluido", False) for o in objs_campo):
                return False

        # Caso todos os objetivos sejam de entrega, verifica os anteriores ao último
        if len(objetivos) > 1:
            return all(o.get("concluido", False) for o in objetivos[:-1])
        return True

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

        # Sincroniza objetivos que dependem de missões já concluídas anteriormente ('progresso_ao_concluir')
        ids_obj_missao = {o.get("id") for o in missao.get("objetivos", []) if isinstance(o, dict) and o.get("id")}
        for m_outra in self.missoes.values():
            if m_outra.get("id") != id_missao and m_outra.get("status") == "CONCLUIDA":
                for prog in m_outra.get("progresso_ao_concluir", []):
                    obj_id_prog = prog.get("objetivo_id")
                    inc_prog = int(prog.get("incremento", 1))
                    if obj_id_prog in ids_obj_missao:
                        self.progredir_objetivo(id_missao, obj_id_prog, inc_prog)

        # Reconhece itens de 'requisitos_entrega' já coletados e armazenados no inventário
        requisitos_entrega = missao.get("requisitos_entrega", [])
        inventario = self._obter_inventario_jogador()
        if requisitos_entrega and inventario:
            objs_campo_padrao = [o for o in missao.get("objetivos", []) if not self._eh_objetivo_entrega_npc(o)]
            for req in requisitos_entrega:
                item_id = req.get("item_id")
                qtd_req = int(req.get("quantidade", 1))
                obj_id_req = req.get("objetivo_id") or (objs_campo_padrao[0].get("id") if objs_campo_padrao else None)
                qtd_inv = inventario.obter_quantidade(item_id) if item_id else 0
                if obj_id_req and qtd_inv > 0:
                    for _ in range(min(qtd_req, qtd_inv)):
                        self.progredir_objetivo(id_missao, obj_id_req, 1)

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

        # Checkpoint de Autosave ao aceitar nova missão
        if self.game and getattr(self.game, 'slot_atual', None) and hasattr(self.game, 'salvar_estado'):
            self.game.salvar_estado(self.game.slot_atual, tipo="autosave", silenciar_notificacao=True)

        return True

    def progredir_objetivo(self, id_missao, id_ou_indice_obj, quantidade=1, via_interacao_npc=False):
        """
        Incrementa o contador de um objetivo específico de uma missão ativa.
        - Se a missão possui objetivo de entrega presencial ao NPC (`tipo: 'entrega_npc'`),
          cumprir os objetivos de campo NÃO conclui a missão automaticamente; o jogador
          deve retornar e interagir com o NPC.
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

        # Verifica se todos os objetivos (incluindo entrega presencial) foram completados
        tem_entrega_npc = any(self._eh_objetivo_entrega_npc(o) for o in missao["objetivos"])
        todos_concluidos = all(o.get("concluido", False) for o in missao["objetivos"])

        if todos_concluidos and (via_interacao_npc or not tem_entrega_npc):
            self.concluir_missao(id_missao)

        return True

    def processar_interacao_npc(self, npc_id_ou_nome):
        """
        Resolve o estado de missão ao interagir com um NPC:
        - Se o NPC tem missão ATIVA e `pronta_para_entregar` for True:
          conclui o objetivo de entrega, finaliza a missão (`concluir_missao`) e retorna o diálogo de conclusão.
        - Se o NPC tem missão ATIVA mas com objetivos de campo pendentes:
          mantém o NPC travado no diálogo de missão em andamento.
        - Se o NPC não tem missão ativa:
          retorna estado 'LIVRE'.
        """
        missao = self.obter_missao_ativa_do_npc(npc_id_ou_nome)
        if not missao:
            return {"estado": "LIVRE", "dialogo_id": None, "missao": None}

        mid = missao["id"]
        if self.pronta_para_entregar(mid):
            for obj in missao.get("objetivos", []):
                if self._eh_objetivo_entrega_npc(obj) and not obj.get("concluido", False):
                    self.progredir_objetivo(mid, obj["id"], obj.get("alvo", 1), via_interacao_npc=True)
            if missao.get("status") != "CONCLUIDA":
                self.concluir_missao(mid)
            return {
                "estado": "CONCLUIDA",
                "dialogo_id": missao.get("dialogo_conclusao"),
                "missao": missao
            }

        return {
            "estado": "ANDAMENTO",
            "dialogo_id": missao.get("dialogo_andamento"),
            "missao": missao
        }

    def concluir_missao(self, id_missao, forcar=False):
        """Marca a missão como concluída, consome requisitos de entrega, entrega recompensas e desbloqueia 'cumpridor_promessas'."""
        if id_missao not in self.missoes:
            return False

        missao = self.missoes[id_missao]
        if missao.get("status") == "CONCLUIDA":
            return False

        if not forcar:
            if missao.get("status") != "ATIVA" or not self.pronta_para_entregar(id_missao):
                return False

        requisitos_entrega = missao.get("requisitos_entrega", [])
        halia = getattr(self.game, 'halia', None) if self.game else None
        inventario = self._obter_inventario_jogador()

        # 1. Validar posse dos itens declarados em 'requisitos_entrega'
        if requisitos_entrega and not forcar:
            if not inventario:
                return False
            for req in requisitos_entrega:
                item_id = req.get("item_id")
                qtd_req = int(req.get("quantidade", 1))
                if not item_id or inventario.obter_quantidade(item_id) < qtd_req:
                    return False

        # 2. Remover itens de entrega
        if requisitos_entrega and inventario:
            for req in requisitos_entrega:
                item_id = req.get("item_id")
                qtd_req = int(req.get("quantidade", 1))
                if item_id and qtd_req > 0:
                    qtd_disp = inventario.obter_quantidade(item_id)
                    qtd_remover = min(qtd_req, qtd_disp) if forcar else qtd_req
                    if qtd_remover > 0 and not inventario.remover_item(item_id, qtd_remover):
                        if not forcar:
                            return False

        # 3. Marcar objetivos e missão como concluídos
        for obj in missao.get("objetivos", []):
            obj["atual"] = obj.get("alvo", 1)
            obj["concluido"] = True

        missao["status"] = "CONCLUIDA"

        # 4. Entregar recompensas (Moedas, XP, Itens e restauração opcional)
        recompensas = missao.get("recompensas", {})
        if halia:
            moedas = recompensas.get("dinheiro", 0)
            if moedas > 0 and hasattr(halia, 'ganhar_dinheiro'):
                halia.ganhar_dinheiro(moedas)

            xp = recompensas.get("xp", 0)
            if xp > 0 and hasattr(halia, 'ganhar_xp'):
                halia.ganhar_xp(xp)

            itens_rec = recompensas.get("itens", [])
            if itens_rec and inventario:
                for item_id in itens_rec:
                    inventario.adicionar_item(item_id, 1)

            if recompensas.get("restaurar_total") and hasattr(halia, "restaurar_total"):
                halia.restaurar_total()

        # 5. Progredir objetivos encadeados declarados no JSON
        for prog in missao.get("progresso_ao_concluir", []):
            obj_id = prog.get("objetivo_id")
            incremento = int(prog.get("incremento", 1))
            if obj_id:
                self.atualizar_progresso(obj_id, incremento)

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

        # Checkpoint de Autosave ao concluir missão
        if self.game and getattr(self.game, 'slot_atual', None) and hasattr(self.game, 'salvar_estado'):
            self.game.salvar_estado(self.game.slot_atual, tipo="autosave", silenciar_notificacao=True)

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
        """Serializa apenas o progresso das missões por ID (schema v2) para gravação no SaveManager."""
        progresso = {}
        for mid, missao in self.missoes.items():
            objs_prog = {}
            for obj in missao.get("objetivos", []):
                if isinstance(obj, dict) and obj.get("id"):
                    objs_prog[obj["id"]] = {
                        "atual": int(obj.get("atual", 0)),
                        "concluido": bool(obj.get("concluido", False)),
                    }
            progresso[mid] = {
                "status": missao.get("status", "DISPONIVEL"),
                "objetivos": objs_prog,
            }
        return {
            "versao_schema": self.VERSAO_SCHEMA_SAVE,
            "rastreada": self.missao_rastreada_id,
            "progresso": progresso,
        }

    def _aplicar_progresso_missao(self, mid, status_salvo, objs_map, origem="v2"):
        """Aplica o progresso salvo sobre a definição atual de `mid` no catálogo."""
        if mid not in self.missoes:
            logger.warning(f"[QuestManager] Missão '{mid}' ({origem}) não existe mais no catálogo atual; ignorando.")
            return

        missao_atual = self.missoes[mid]
        if status_salvo in ("DISPONIVEL", "ATIVA", "CONCLUIDA"):
            missao_atual["status"] = status_salvo

        objs_catalogo = {
            o.get("id"): o
            for o in missao_atual.get("objetivos", [])
            if isinstance(o, dict) and o.get("id")
        }
        if isinstance(objs_map, dict):
            for obj_id, obj_prog in objs_map.items():
                obj_cat = objs_catalogo.get(obj_id)
                if obj_cat is None:
                    logger.warning(
                        f"[QuestManager] Objetivo '{obj_id}' da missão '{mid}' ({origem}) não existe mais no catálogo atual; ignorando."
                    )
                    continue
                if isinstance(obj_prog, dict):
                    alvo_cat = int(obj_cat.get("alvo", 1))
                    atual_raw = obj_prog.get("atual", 0)
                    try:
                        atual_salvo = int(0 if atual_raw is None else atual_raw)
                    except (TypeError, ValueError):
                        atual_salvo = 0
                    concluido_salvo = bool(obj_prog.get("concluido", False))
                    if concluido_salvo:
                        obj_cat["atual"] = alvo_cat
                        obj_cat["concluido"] = True
                    else:
                        obj_cat["atual"] = max(0, min(alvo_cat, atual_salvo))
                        obj_cat["concluido"] = (obj_cat["atual"] >= alvo_cat)

        if missao_atual.get("status") == "CONCLUIDA":
            for obj in missao_atual.get("objetivos", []):
                if isinstance(obj, dict):
                    obj["atual"] = int(obj.get("alvo", 1))
                    obj["concluido"] = True

    def from_dict(self, dados):
        """
        Restaura o estado das missões a partir do catálogo atual de `missoes.json`,
        suportando o schema v2 (`progresso`) e migrando saves legados em schema v1 (`missoes`).
        """
        if not dados or not isinstance(dados, dict):
            return

        self.resetar()

        if dados.get("versao_schema") == 2 or "progresso" in dados:
            progresso_salvo = dados.get("progresso") or {}
            if isinstance(progresso_salvo, dict):
                for mid, m_prog in progresso_salvo.items():
                    if isinstance(m_prog, dict):
                        self._aplicar_progresso_missao(
                            mid,
                            m_prog.get("status"),
                            m_prog.get("objetivos") or {},
                            origem="v2",
                        )
        else:
            missoes_v1 = dados.get("missoes") or {}
            if isinstance(missoes_v1, dict):
                for mid, m_dados in missoes_v1.items():
                    if isinstance(m_dados, dict):
                        objs_dict = {}
                        for obj in (m_dados.get("objetivos") or []):
                            if isinstance(obj, dict) and obj.get("id"):
                                objs_dict[obj["id"]] = {
                                    "atual": obj.get("atual", 0),
                                    "concluido": obj.get("concluido", False),
                                }
                        self._aplicar_progresso_missao(
                            mid,
                            m_dados.get("status"),
                            objs_dict,
                            origem="v1",
                        )

        rastreada = dados.get("rastreada")
        self.missao_rastreada_id = rastreada if rastreada in self.missoes else None
        self._sanitizar_limite_simultaneo()
