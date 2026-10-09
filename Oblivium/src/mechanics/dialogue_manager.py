# src/mechanics/dialogue_manager.py
import os
import json

class DialogueManager:
    """
    Gerenciador Central de Diálogos e Árvores de Decisão Narrativa (POO).
    
    Responsabilidades:
    - Carregar e validar diálogos estruturados a partir do arquivo JSON externo.
    - Controlar o estado do fluxo de nós (falas sequenciais, escolhas, links entre diálogos).
    - Manter histórico de escolhas já selecionadas para evitar repetições desnecessárias.
    - Disparar eventos narrativos para o motor do jogo (combates, transições, puzzles).
    - Fornecer retrocompatibilidade com sequências manuais de falas (listas de dicionários).
    """

    _CAMINHO_PADRAO_JSON = os.path.join(os.path.dirname(__file__), "..", "data", "dialogos.json")

    def __init__(self, caminho_json=None):
        self.caminho_json = caminho_json or self._CAMINHO_PADRAO_JSON
        self.banco_dialogos = {}
        
        # Estado atual da conversa
        self.ativo = False
        self.conversa_id = None
        self.no_id_atual = None
        self.no_atual = None
        
        # Histórico de escolhas (IDs de opções selecionadas) e flags de narrativa
        self.historico_escolhas = set()
        self.flags = {}
        
        # Eventos pendentes a serem consumidos pelo jogo
        self.evento_pendente = None
        
        # Modo de lista direta (retrocompatibilidade com diálogos gerados em tempo de execução)
        self.modo_lista = False
        self.lista_dialogos = []
        self.indice_lista = 0

        self.carregar_dados()

    def carregar_dados(self):
        """Carrega e valida o arquivo JSON contendo as conversas."""
        try:
            if os.path.exists(self.caminho_json):
                with open(self.caminho_json, "r", encoding="utf-8") as arquivo:
                    self.banco_dialogos = json.load(arquivo)
            else:
                print(f"[DialogueManager] Aviso: Arquivo de diálogos não encontrado em {self.caminho_json}")
                self.banco_dialogos = {}
        except Exception as erro:
            print(f"[DialogueManager] Erro ao carregar dialogos.json: {erro}")
            self.banco_dialogos = {}

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
        return True

    def _processar_no_atual(self):
        """Processa o nó atual, verificando se há links diretos ou eventos imediatos."""
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
        Recebe o dicionário da opção selecionada.
        """
        if not self.ativo or not self.no_atual:
            return False

        # Marca no histórico se a opção não for repetível
        opt_id = opcao.get("id")
        if opt_id and not opcao.get("repetivel", False):
            self.historico_escolhas.add(opt_id)

        # Registra evento caso a opção possua
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

    def obter_opcoes_filtradas(self):
        """Retorna as opções válidas do nó atual, excluindo as já utilizadas não-repetíveis."""
        if not self.ativo or not self.no_atual or self.no_atual.get("tipo") != "escolha":
            return []
        
        opcoes = self.no_atual.get("opcoes", [])
        return [opt for opt in opcoes if opt.get("id") not in self.historico_escolhas]

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

    def finalizar(self):
        """Encerra a conversa ativa."""
        self.ativo = False
        self.no_atual = None
        self.no_id_atual = None
        self.conversa_id = None
        self.modo_lista = False
        self.lista_dialogos = []
