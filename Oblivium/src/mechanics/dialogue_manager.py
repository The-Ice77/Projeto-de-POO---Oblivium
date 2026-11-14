# src/mechanics/dialogue_manager.py
import json
import logging
import os

logger = logging.getLogger(__name__)


class DialogueManager:
    """
    Gerenciador Central de Diálogos e Árvores de Decisão Narrativa (POO).
    
    Responsabilidades:
    - Carregar e mesclar diálogos estruturados a partir da pasta modular `src/data/dialogos/`
      (`dialogos_prologo.json`, `dialogos_fase1.json`, etc.) e `src/data/dialogos.json`.
    - Controlar o estado do fluxo de nós (falas sequenciais, escolhas, links entre diálogos).
    - Manter histórico de escolhas já selecionadas para que os assuntos de conversa
      se esgotem naturalmente, enquanto opções funcionais (como Lojas e Saídas) permanecem.
    - Integrar-se ao `QuestManager` para filtrar opções de missão e disparar aceitação/conclusão.
    - Disparar eventos narrativos para o motor do jogo (combates, transições, puzzles, lojas).
    - Fornecer retrocompatibilidade com sequências manuais de falas (listas de dicionários).
    """

    _DIRETORIO_DATA = os.path.join(os.path.dirname(__file__), "..", "data")
    _PASTA_DIALOGOS_MODULAR = os.path.join(_DIRETORIO_DATA, "dialogos")
    _CAMINHO_PADRAO_JSON = os.path.join(_DIRETORIO_DATA, "dialogos.json")

    def __init__(self, caminho_json=None, quest_manager=None):
        self.caminho_json = caminho_json or self._CAMINHO_PADRAO_JSON
        self.quest_manager = quest_manager
        self.banco_dialogos = {}
        self._origens_dialogos = {}
        
        # Estado atual da conversa
        self.ativo = False
        self.conversa_id = None
        self.no_id_atual = None
        self.no_atual = None
        
        # Histórico de escolhas (IDs de opções selecionadas) e flags de narrativa
        self.historico_escolhas = set()
        self.flags = {}
        
        # Eventos e lojas pendentes a serem consumidos pelo jogo
        self.evento_pendente = None
        self.loja_pendente = None
        
        # Modo de lista direta (retrocompatibilidade com diálogos gerados em tempo de execução)
        self.modo_lista = False
        self.lista_dialogos = []
        self.indice_lista = 0

        self.carregar_dados()

    def _mesclar_dialogos(self, dados_novos, caminho_origem):
        """Mescla um dicionário de diálogos no banco registrando warning em caso de colisão de ID."""
        if not isinstance(dados_novos, dict):
            return
        nome_origem = os.path.basename(caminho_origem) if caminho_origem else "<desconhecido>"
        for conv_id, conteudo in dados_novos.items():
            if conv_id in self.banco_dialogos:
                origem_anterior = self._origens_dialogos.get(conv_id, "<desconhecido>")
                logger.warning(
                    "[DialogueManager] ID de diálogo duplicado '%s': '%s' sobrescreveu '%s'.",
                    conv_id,
                    nome_origem,
                    origem_anterior,
                )
            self.banco_dialogos[conv_id] = conteudo
            self._origens_dialogos[conv_id] = nome_origem

    def carregar_dados(self):
        """
        Carrega e mescla os arquivos JSON de diálogos:
        1. Carrega o arquivo base (`dialogos.json` ou `caminho_json` informado).
        2. Carrega todos os arquivos `*.json` na pasta modular `src/data/dialogos/` em ordem alfabética.
        """
        self.banco_dialogos = {}
        self._origens_dialogos = {}
        try:
            # Se caminho_json for um diretório, carrega todos os JSONs dele
            if self.caminho_json and os.path.isdir(self.caminho_json):
                self._carregar_pasta_modular(self.caminho_json)
                return

            # 1. Carrega o arquivo base se existir
            if self.caminho_json and os.path.isfile(self.caminho_json):
                with open(self.caminho_json, "r", encoding="utf-8") as arquivo:
                    dados_base = json.load(arquivo)
                    self._mesclar_dialogos(dados_base, self.caminho_json)

            # 2. Carrega e mescla os módulos por fase de src/data/dialogos/
            if os.path.isdir(self._PASTA_DIALOGOS_MODULAR):
                self._carregar_pasta_modular(self._PASTA_DIALOGOS_MODULAR)

            if not self.banco_dialogos:
                print(f"[DialogueManager] Aviso: Nenhum diálogo encontrado em {self.caminho_json}")
        except Exception as erro:
            print(f"[DialogueManager] Erro ao carregar diálogos: {erro}")

    def _carregar_pasta_modular(self, pasta):
        """Lê todos os arquivos .json de uma pasta em ordem alfabética e mescla no banco."""
        for nome_arq in sorted(os.listdir(pasta)):
            if nome_arq.lower().endswith(".json"):
                caminho_mod = os.path.join(pasta, nome_arq)
                if os.path.isfile(caminho_mod):
                    try:
                        with open(caminho_mod, "r", encoding="utf-8") as f:
                            dados_mod = json.load(f)
                            self._mesclar_dialogos(dados_mod, caminho_mod)
                    except Exception as e:
                        print(f"[DialogueManager] Erro ao ler módulo {nome_arq}: {e}")

    @staticmethod
    def _opcao_eh_permanente(opcao):
        """
        Define se uma opção de diálogo NUNCA deve desaparecer do menu:
        - Opções de acesso a loja ('acao': 'abrir_loja', 'evento': 'abrir_loja', 'loja_id')
        - Opções marcadas com 'repetivel': True ou 'persistente': True
        """
        if not isinstance(opcao, dict):
            return False
        if opcao.get("desaparecer") or opcao.get("unica_vez") or opcao.get("desaparecer_apos_uso"):
            return False
        if opcao.get("acao") == "abrir_loja" or opcao.get("evento") == "abrir_loja" or "loja_id" in opcao:
            return True
        return bool(opcao.get("repetivel", False) or opcao.get("persistente", False))

    def iniciar_conversa(self, conversa_id, no_inicial=None):
        """
        Inicia uma conversa baseada em grafo a partir de seu ID no JSON.
        Se `conversa_id` não existir no banco, tenta modo lista se for uma lista.
        """
        if isinstance(conversa_id, list):
            return self.iniciar_lista_direta(conversa_id)

        if conversa_id not in self.banco_dialogos:
            print(f"[DialogueManager] Erro: Diálogo '{conversa_id}' não encontrado no JSON.")
            self.ativo = False
            return False

        conversa = self.banco_dialogos[conversa_id]
        nos = conversa.get("nos", {})
        
        id_inicio = no_inicial or conversa.get("no_inicial")
        if not id_inicio or id_inicio not in nos:
            print(f"[DialogueManager] Erro: Nó inicial '{id_inicio}' não encontrado na conversa '{conversa_id}'.")
            self.ativo = False
            return False

        self.modo_lista = False
        self.conversa_id = conversa_id
        self.no_id_atual = id_inicio
        self.no_atual = nos[id_inicio]
        self.ativo = True
        self.evento_pendente = None
        self.loja_pendente = None

        self._processar_no_atual()
        return True

    def iniciar_lista_direta(self, lista_falas):
        """
        Inicia uma conversa a partir de uma lista em memória de dicionários:
        [{"autor": "...", "texto": "..."}]
        """
        if not lista_falas:
            self.finalizar()
            return False

        self.modo_lista = True
        self.lista_dialogos = lista_falas
        self.indice_lista = 0
        self.conversa_id = None
        self.no_id_atual = None
        self.no_atual = self.lista_dialogos[0]
        self.ativo = True
        self.evento_pendente = None
        self.loja_pendente = None
        return True

    def _processar_no_atual(self):
        """Processa o nó atual, verificando se há links diretos, missões ou eventos imediatos."""
        if not self.no_atual:
            self.finalizar()
            return

        # Verifica redirecionamento entre diálogos (link_dialogo)
        if self.no_atual.get("tipo") == "link_dialogo":
            dialogo_alvo = self.no_atual.get("dialogo_alvo")
            no_alvo = self.no_atual.get("no_alvo", None)
            if dialogo_alvo:
                self.iniciar_conversa(dialogo_alvo, no_alvo)
            else:
                self.finalizar()
            return

        # Gatilhos de missão em nós
        if "aceitar_missao" in self.no_atual and self.quest_manager:
            self.quest_manager.aceitar_missao(self.no_atual["aceitar_missao"])
        if "concluir_missao" in self.no_atual and self.quest_manager:
            self.quest_manager.concluir_missao(self.no_atual["concluir_missao"])

        # Se for um nó de escolha e todas as opções já tiverem acabado, cai para no_esgotado se existir
        if self.no_atual.get("tipo") == "escolha":
            opcoes_restantes = self.obter_opcoes_filtradas()
            if not opcoes_restantes:
                no_esgotado = self.no_atual.get("no_esgotado") or self.no_atual.get("resultado_fechar")
                nos = self.banco_dialogos.get(self.conversa_id, {}).get("nos", {})
                if no_esgotado and no_esgotado in nos and no_esgotado != self.no_id_atual:
                    self.no_id_atual = no_esgotado
                    self.no_atual = nos[no_esgotado]
                    self._processar_no_atual()
                    return

        # Registra evento se o nó possuir um
        if "evento" in self.no_atual:
            self.evento_pendente = self.no_atual["evento"]

    def avancar(self):
        """
        Avança o diálogo corrente:
        - No modo JSON: navega para o nó definido em 'proximo'.
        - No modo lista: vai para o próximo índice da lista.
        Retorna True se ainda houver diálogo ativo, ou False se a conversa terminou.
        """
        if not self.ativo:
            return False

        if self.modo_lista:
            self.indice_lista += 1
            if self.indice_lista < len(self.lista_dialogos):
                self.no_atual = self.lista_dialogos[self.indice_lista]
                return True
            else:
                self.finalizar()
                return False

        # Modo JSON por Nós
        if not self.no_atual:
            self.finalizar()
            return False

        proximo_id = self.no_atual.get("proximo")
        if not proximo_id:
            self.finalizar()
            return False

        nos = self.banco_dialogos.get(self.conversa_id, {}).get("nos", {})
        if proximo_id in nos:
            self.no_id_atual = proximo_id
            self.no_atual = nos[proximo_id]
            self._processar_no_atual()
            return self.ativo
        else:
            print(f"[DialogueManager] Nó '{proximo_id}' não encontrado em '{self.conversa_id}'. Finalizando.")
            self.finalizar()
            return False

    def escolher_opcao(self, opcao):
        """
        Processa uma escolha do jogador no menu de opções:
        - Assuntos comuns são adicionados a `historico_escolhas` e somem do menu.
        - Opções de loja ou marcadas com `repetivel: true` permanecem sempre disponíveis.
        - Aciona `aceitar_missao`, `concluir_missao` ou `abrir_loja` quando configurados.
        """
        if not self.ativo or not self.no_atual:
            return False

        opt_id = opcao.get("id")
        if opt_id and not self._opcao_eh_permanente(opcao):
            self.historico_escolhas.add(opt_id)

        # Integração direta com QuestManager
        if "aceitar_missao" in opcao:
            id_m = opcao["aceitar_missao"]
            if self.quest_manager:
                self.quest_manager.aceitar_missao(id_m)
            if "evento" not in opcao:
                self.evento_pendente = f"aceitar_missao:{id_m}"

        if "concluir_missao" in opcao:
            id_m = opcao["concluir_missao"]
            if self.quest_manager:
                self.quest_manager.concluir_missao(id_m)
            if "evento" not in opcao:
                self.evento_pendente = f"concluir_missao:{id_m}"

        # Integração direta com Loja
        if opcao.get("acao") == "abrir_loja" or opcao.get("evento") == "abrir_loja":
            self.evento_pendente = "abrir_loja"
            self.loja_pendente = opcao.get("loja_id")

        # Registra evento explícito caso a opção possua
        if "evento" in opcao:
            self.evento_pendente = opcao["evento"]

        # Navega para o próximo nó indicado pela escolha
        proximo_id = opcao.get("proximo")
        if proximo_id:
            nos = self.banco_dialogos.get(self.conversa_id, {}).get("nos", {})
            if proximo_id in nos:
                self.no_id_atual = proximo_id
                self.no_atual = nos[proximo_id]
                self._processar_no_atual()
                return True
            else:
                print(f"[DialogueManager] Destino da opção '{proximo_id}' não encontrado. Finalizando.")
                self.finalizar()
                return False
        else:
            # Opção sem próximo nó encerra o menu/conversa
            self.finalizar()
            return False

    def cancelar_escolha(self):
        """Trata o fechamento de um menu de escolhas pelo botão [X]."""
        if not self.ativo or not self.no_atual:
            return

        id_cancel = self.no_atual.get("id_cancelamento")
        if id_cancel:
            self.evento_pendente = id_cancel

        resultado_fechar = self.no_atual.get("resultado_fechar")
        if resultado_fechar:
            nos = self.banco_dialogos.get(self.conversa_id, {}).get("nos", {})
            if resultado_fechar in nos:
                self.no_id_atual = resultado_fechar
                self.no_atual = nos[resultado_fechar]
                self._processar_no_atual()
                return

        self.finalizar()

    def obter_no_atual(self):
        """Retorna o nó de diálogo ativo."""
        return self.no_atual if self.ativo else None

    def _opcao_atende_condicoes(self, opt):
        """Verifica se uma opção atende às condições de histórico, missão e flags."""
        opt_id = opt.get("id")
        if opt_id in self.historico_escolhas and not self._opcao_eh_permanente(opt):
            return False

        # Bloqueio de loja com pré-requisito ou missão ativa pendente
        if (opt.get("acao") == "abrir_loja" or opt.get("evento") == "abrir_loja" or "loja_id" in opt) and self.quest_manager:
            loja_ref = str(opt.get("loja_id") or "").lower()
            # Torvald / Forja: requer conclusão da missão da rocha
            if "forja" in loja_ref or "torvald" in loja_ref:
                m_t = self.quest_manager.missoes.get("missao_pedra_forja")
                if not m_t or m_t.get("status") != "CONCLUIDA":
                    return False
            # Elara / Botânica: requer conclusão da missão das ervas
            if "botanica" in loja_ref or "elara" in loja_ref:
                m_e = self.quest_manager.missoes.get("missao_ervas_medicinais")
                if not m_e or m_e.get("status") != "CONCLUIDA":
                    return False

            npc_ref = opt.get("npc_id")
            if not npc_ref and self.conversa_id in self.banco_dialogos:
                conv = self.banco_dialogos[self.conversa_id]
                npc_ref = conv.get("npc_id")
                if not npc_ref:
                    no_ini = conv.get("nos", {}).get(conv.get("no_inicial"), {})
                    npc_ref = no_ini.get("autor")
            if npc_ref and self.quest_manager.obter_missao_ativa_do_npc(npc_ref):
                return False

        # Condição de missão concluída (única ou lista de IDs)
        cond_conc = opt.get("condicao_missao_concluida")
        if cond_conc and self.quest_manager:
            lista_req = [cond_conc] if isinstance(cond_conc, str) else list(cond_conc)
            for mid in lista_req:
                m_obj = self.quest_manager.missoes.get(mid)
                if not m_obj or m_obj.get("status") != "CONCLUIDA":
                    return False

        # Condição de missão pendente / NÃO concluída (única ou lista de IDs)
        cond_nao_conc = opt.get("condicao_missao_nao_concluida")
        if cond_nao_conc and self.quest_manager:
            lista_pend = [cond_nao_conc] if isinstance(cond_nao_conc, str) else list(cond_nao_conc)
            # Se todas as missões especificadas já estiverem concluídas, esconde esta opção alternativa
            if all(self.quest_manager.missoes.get(mid, {}).get("status") == "CONCLUIDA" for mid in lista_pend):
                return False

        # Condição de missão disponível
        id_missao_disp = opt.get("condicao_missao_disponivel") or opt.get("aceitar_missao")
        if id_missao_disp and self.quest_manager:
            missao = self.quest_manager.missoes.get(id_missao_disp)
            if not missao or missao.get("status") != "DISPONIVEL":
                return False

        # Condição de flag narrativa
        flag_req = opt.get("condicao_flag")
        if flag_req and not self.flags.get(flag_req, False):
            return False

        return True

    def obter_opcoes_filtradas(self):
        """Retorna as opções válidas do nó atual, excluindo as já utilizadas não-repetíveis e missões indisponíveis."""
        if not self.ativo or not self.no_atual or self.no_atual.get("tipo") != "escolha":
            return []
        
        opcoes = self.no_atual.get("opcoes", [])
        return [opt for opt in opcoes if self._opcao_atende_condicoes(opt)]

    def consumir_evento(self):
        """Retorna e limpa o último evento gerado por nó ou escolha."""
        ev = self.evento_pendente
        self.evento_pendente = None
        return ev

    def definir_flag(self, chave, valor=True):
        """Define uma flag de narrativa no jogo."""
        self.flags[chave] = valor

    def obter_flag(self, chave, padrao=None):
        """Obtém o valor de uma flag de narrativa."""
        return self.flags.get(chave, padrao)

    def obter_sequencia_linear(self, conversa_id):
        """
        Retorna uma conversa puramente linear em formato de lista:
        [{"autor": ..., "texto": ...}]
        Útil para componentes como o sistema de Flashback.
        """
        if conversa_id not in self.banco_dialogos:
            return []
        conversa = self.banco_dialogos[conversa_id]
        nos = conversa.get("nos", {})
        resultado = []
        no_id = conversa.get("no_inicial")
        visitados = set()
        while no_id and no_id in nos and no_id not in visitados:
            visitados.add(no_id)
            no = nos[no_id]
            if "texto" in no:
                resultado.append({"autor": no.get("autor", "Narrador"), "texto": no["texto"]})
            no_id = no.get("proximo")
        return resultado

    def validar_integridade_nos(self, banco=None):
        """Valida no_inicial, proximo, resultado_fechar, no_esgotado e link_dialogo das conversas."""
        catalogo = self.banco_dialogos if banco is None else banco
        if not isinstance(catalogo, dict):
            return ["Catálogo de diálogos inválido (esperado dict)."]

        erros = []
        for conv_id, conv in sorted(catalogo.items()):
            if not isinstance(conv, dict):
                erros.append(f"[{conv_id}] Estrutura de conversa inválida (esperado dict).")
                continue

            nos = conv.get("nos")
            if not isinstance(nos, dict):
                erros.append(f"[{conv_id}] Bloco 'nos' ausente ou inválido.")
                continue

            no_inicial = conv.get("no_inicial")
            if not no_inicial or no_inicial not in nos:
                erros.append(f"[{conv_id}] 'no_inicial' aponta para nó inexistente: {no_inicial!r}")

            for no_id, no in nos.items():
                if not isinstance(no, dict):
                    erros.append(f"[{conv_id}.{no_id}] Nó inválido (esperado dict).")
                    continue

                for campo in ("proximo", "resultado_fechar", "no_esgotado"):
                    alvo = no.get(campo)
                    if alvo and alvo not in nos:
                        erros.append(f"[{conv_id}.{no_id}] '{campo}' aponta para nó inexistente: '{alvo}'")

                for opt in no.get("opcoes", []):
                    if not isinstance(opt, dict):
                        continue
                    op_id = opt.get("id", "<sem_id>")
                    op_prox = opt.get("proximo")
                    if op_prox and op_prox not in nos:
                        erros.append(
                            f"[{conv_id}.{no_id}.opcoes[{op_id}]] 'proximo' aponta para nó inexistente: '{op_prox}'"
                        )

                if no.get("tipo") == "link_dialogo":
                    dialogo_alvo = no.get("dialogo_alvo")
                    no_alvo = no.get("no_alvo")
                    if not dialogo_alvo or dialogo_alvo not in catalogo:
                        erros.append(
                            f"[{conv_id}.{no_id}] 'dialogo_alvo' aponta para conversa inexistente: {dialogo_alvo!r}"
                        )
                    elif no_alvo and no_alvo not in catalogo[dialogo_alvo].get("nos", {}):
                        erros.append(
                            f"[{conv_id}.{no_id}] 'no_alvo' '{no_alvo}' não existe na conversa alvo '{dialogo_alvo}'"
                        )

        return erros

    def finalizar(self):
        """Encerra a conversa ativa."""
        self.ativo = False
        self.no_atual = None
        self.no_id_atual = None
        self.conversa_id = None
        self.modo_lista = False
        self.lista_dialogos = []
