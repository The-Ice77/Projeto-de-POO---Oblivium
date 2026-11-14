# src/core/save_manager.py
import logging
import datetime
from src.utils import save_storage as save_io
from src.mechanics.attributes import Atributos
from src.mechanics.inventory import Inventario
from src.mechanics.shop import Loja

logger = logging.getLogger(__name__)


class SaveManager:
    """
    Gerenciador Central de Persistência, Integridade e Ciclo de Vida dos Saves de Oblivium.

    Responsabilidades:
    - Serialização completa do estado de jogo (Halia, Carroceiro, Cenários, Flags, Missões e Inventário).
    - Desserialização robusta com retrocompatibilidade, saneamento de dados e recuperação de integridade.
    - Sincronização e restauração inteligente de inimigos de combate e Câmera 2D ao carregar.
    - Sincronização de integridade entre Saves Manuais e Autosaves (Blindagem de Autosave).
    - Diagnóstico e verificação de integridade estrutural contra corrupção em disco.
    - Reinicialização segura de progresso para criação de Novo Jogo.
    """

    CENARIOS_VALIDOS = {
        "CASA",
        "ESTRADA",
        "ESTRADA_2",
        "OAKHAVEN",
        "ORLA_NORTE",
        "OAKHAVEN_DESTRUIDA",
        "NINHO_DRAGAO"
    }

    SPAWNS_SEGUROS = {
        "CASA": (210, 280),
        "ESTRADA": (40, 330),
        "ESTRADA_2": (60, 330),
        "OAKHAVEN": (1102, 1320),
        "ORLA_NORTE": (610, 520),
        "OAKHAVEN_DESTRUIDA": (1102, 660),
        "NINHO_DRAGAO": (610, 520),
    }

    # (atributo em self.game, chave no bloco 'flags' do JSON, valor padrão)
    FLAGS_PERSISTENTES = (
        ("investigou_pedras", "investigou_pedras", False),
        ("flashback_magia_concluido", "flashback_magia_concluido", False),
        ("magia_ativa", "magia_ativa", None),
        ("magia_usada_no_puzzle", "magia_usada_no_puzzle", None),
        ("combate_estrada_concluido", "combate_concluido", False),
        ("pedra_torvald_quebrada", "pedra_torvald_quebrada", False),
        ("oakhaven_noite", "oakhaven_noite", False),
        ("oakhaven_destruida", "oakhaven_destruida", False),
        ("dragao_derrotado", "dragao_derrotado", False),
        ("desespero_superado", "desespero_superado", False),
        ("patusco_pos_oakhaven", "patusco_pos_oakhaven", None),
    )

    # (atributo transitório em self.game, valor padrão no reset/load)
    FLAGS_TRANSITORIAS = (
        ("fechando_porta", False),
        ("aguardando_fim_viagem", False),
        ("magia_selecionada_temporaria", None),
        ("iniciando_combate", False),
        ("cena_inimigos_andando", False),
        ("conversa_combate_ativa", False),
        ("combate_climax_dragao", False),
        ("aguardando_dialogo_pos_dragao", False),
        ("flashback_monumento_ativo", False),
        ("flashback_sylvan_ativo", False),
        ("partindo_estrada2", False),
    )

    def __init__(self, game):
        self.game = game

    def _obter_resumo_missao_ativa(self):
        """Retorna título e categoria da missão principal (ou secundária) ativa para metadados do save."""
        if hasattr(self.game, 'missoes') and self.game.missoes:
            m_princ = self.game.missoes.obter_missao_principal_ativa()
            if m_princ:
                return {
                    "id": m_princ.get("id"),
                    "titulo": m_princ.get("titulo", "Missão Principal"),
                    "categoria": "PRINCIPAL"
                }
            m_sec = self.game.missoes.obter_missao_secundaria_ativa()
            if m_sec:
                return {
                    "id": m_sec.get("id"),
                    "titulo": m_sec.get("titulo", "Missão Secundária"),
                    "categoria": "SECUNDARIA"
                }
        return {"id": None, "titulo": "Sem Missão Ativa", "categoria": "NENHUMA"}

    def salvar_estado(self, slot=None, tipo="manual", silenciar_notificacao=False):
        """Serializa todo o estado atual da sessão e persiste no slot indicado em disco."""
        slot_alvo = save_io.normalizar_slot(slot or self.game.slot_atual)
        if not slot_alvo:
            return False

        halia = self.game.halia
        carroceiro = self.game.carroceiro
        mapa = self.game.mapa_casa

        # Garante que as magias e técnicas estejam atualizadas antes de gravar
        if hasattr(halia, 'atualizar_grimorio'):
            halia.atualizar_grimorio()

        ataques_padrao = ["ataque_basico", "golpe_concentrado", "varredura_de_cajado", "estocada_perfurante"]
        ataques_salvar = getattr(halia, 'ataques_fisicos', ataques_padrao)

        flags_dict = {
            "porta_aberta": getattr(mapa, 'porta_aberta', False),
            "puzzle_concluido": (self.game.magia_ativa == "CONCLUIDO"),
            "itens_coletados": self.game.itens_coletados,
            "historico_dialogos": list(self.game.caixa_dialogo.historico_escolhas),
        }
        for attr_game, chave_save, padrao in self.FLAGS_PERSISTENTES:
            valor = getattr(self.game, attr_game, padrao)
            if attr_game == "patusco_pos_oakhaven" and isinstance(valor, (tuple, list)) and len(valor) == 2:
                valor = [int(valor[0]), int(valor[1])]
            flags_dict[chave_save] = valor

        dados_save = {
            "cenario_atual": mapa.cenario_atual,
            "tempo_jogado": self.game.tempo_jogado,
            "data_hora": datetime.datetime.now().strftime("%d/%m/%Y %H:%M"),
            "timestamp_epoch": datetime.datetime.now().timestamp(),
            "slot": slot_alvo,
            "tipo_save": tipo,
            "missao_ativa": self._obter_resumo_missao_ativa(),
            "progresso_npcs": getattr(self.game, 'progresso_npcs', {"carroceiro": 0}),
            "halia": {
                "nome": halia.nome,
                "x": halia.x,
                "y": halia.y,
                "direcao": getattr(halia, 'direcao', "baixo"),
                "virado_direita": getattr(halia, 'virado_direita', True),
                "vivo": getattr(halia, 'vivo', True),
                "estado_animacao": "idle",
                "vida_atual": getattr(halia, 'vida_atual', 100),
                "vida_maxima": getattr(halia, 'vida_maxima', 100),
                "mana_atual": getattr(halia, 'mana_atual', 50),
                "mana_maxima": getattr(halia, 'mana_maxima', 50),
                "nivel": getattr(halia, 'nivel', 1),
                "xp": getattr(halia, 'xp', 0),
                "feiticos_aprendidos": list(getattr(halia, 'feiticos_aprendidos', set())),
                "maestria_feiticos": getattr(halia, 'maestria_feiticos', {}),
                "fragmentos_memoria": getattr(halia, 'fragmentos_memoria', 0),
                "nivel_sincronia": getattr(halia, 'nivel_sincronia', 1),
                "dinheiro": getattr(halia, 'dinheiro', 0),
                "atributos": halia.atributos.to_dict(),
                "inventario": halia.inventario.to_dict() if hasattr(halia, 'inventario') else {},
                "magias_desbloqueadas": getattr(halia, 'magias_desbloqueadas', []),
                "ataques_fisicos": ataques_salvar
            },
            "carroceiro": {
                "x": carroceiro.x,
                "y": carroceiro.y,
                "visivel": self.game.carroceiro_visivel,
                "andando": self.game.carroceiro_andando,
                "conversa_terminou": getattr(self.game, 'conversa_carroceiro_terminou', False)
            },
            "flags": flags_dict,
            "missoes": self.game.missoes.to_dict() if hasattr(self.game, 'missoes') else {},
            "lojas": Loja.salvar_estado_lojas()
        }

        sucesso = save_io.salvar_dados(slot_alvo, dados_save, tipo=tipo)
        slot_num = str(slot_alvo).replace("slot_", "")
        slot_str = f"Slot {slot_num}"

        if not sucesso:
            logger.error(f"[SaveManager] Falha ao salvar progresso ({tipo}) no {slot_str}.")
            if hasattr(self.game, 'notificacoes') and self.game.notificacoes:
                self.game.notificacoes.notificar(
                    "notificacao_alerta",
                    titulo="Falha ao Salvar",
                    mensagem=f"Não foi possível gravar o progresso no {slot_str}.",
                    tipo="ALERTA"
                )
            return False

        if not silenciar_notificacao and hasattr(self.game, 'notificacoes') and self.game.notificacoes:
            if tipo == "autosave":
                self.game.notificacoes.notificar("notificacao_autosave", slot=slot_str)
            else:
                self.game.notificacoes.notificar("notificacao_salvo", slot=slot_str)

        return True

    def carregar_estado(self, slot, tipo="manual"):
        """
        Carrega e desserializa os dados do save em duas fases:
        1. Preparar/Validar: valida estrutura, tipos e constrói objetos em variáveis locais sem mutar a sessão.
        2. Aplicar: transfere o estado validado para `self.game` e `self.game.halia`.
        """
        slot = save_io.normalizar_slot(slot)
        tipo_pedido = tipo
        tipo_efetivo = tipo
        usou_fallback_tipo = False

        dados = save_io.carregar_dados(slot, tipo=tipo)
        if not dados:
            outro_tipo = "autosave" if tipo == "manual" else "manual"
            dados = save_io.carregar_dados(slot, tipo=outro_tipo)
            if dados:
                tipo_efetivo = outro_tipo
                usou_fallback_tipo = True

        if not dados:
            return False

        slot_num = str(slot).replace("slot_", "")
        slot_str = f"Slot {slot_num}"

        def _notificar_falha_load(motivo):
            logger.error(f"[SaveManager] Falha ao carregar {slot_str} ({tipo_efetivo}): {motivo}")
            if hasattr(self.game, 'notificacoes') and self.game.notificacoes:
                self.game.notificacoes.notificar(
                    "notificacao_alerta",
                    titulo="Falha ao Carregar",
                    mensagem=f"Os dados do {slot_str} estão corrompidos ou inválidos.",
                    tipo="ALERTA"
                )

        # --- FASE 1: PREPARAR E VALIDAR (nenhuma mutação na sessão até validar tudo) ---
        valido, motivo = self._validar_dados_save(
            dados, slot=slot, tipo=tipo_efetivo, verificar_limites_estritos=False
        )
        if not valido:
            _notificar_falha_load(motivo)
            return False

        try:
            flags = dados.get("flags", {})
            carroceiro_dados = dados.get("carroceiro") or {}
            halia_dados = dados.get("halia", {})

            tempo_jogado_novo = float(dados.get("tempo_jogado") or 0.0)

            raw_hist = flags.get("historico_dialogos", [])
            if raw_hist is None:
                historico_escolhas_novo = set()
            elif isinstance(raw_hist, (list, tuple, set)):
                historico_escolhas_novo = set(raw_hist)
            else:
                raise TypeError("historico_dialogos inválido.")

            raw_itens = flags.get("itens_coletados", [])
            if raw_itens is None:
                itens_coletados_novos = []
            elif isinstance(raw_itens, list):
                itens_coletados_novos = list(raw_itens)
            else:
                raise TypeError("itens_coletados inválido.")

            conversa_terminou_nova = bool(
                carroceiro_dados.get("conversa_terminou", flags.get("conversa_carroceiro_terminou", False))
            )
            progresso_npcs_novo = dict(dados.get("progresso_npcs") or {"carroceiro": 0})
            missoes_dados = dados.get("missoes") if "missoes" in dados else None
            lojas_dados = dados.get("lojas") or {}
            for id_loja, estoques in lojas_dados.items():
                if not isinstance(estoques, dict):
                    raise TypeError(f"Estoque da loja '{id_loja}' inválido.")
                for item_id, qtd in estoques.items():
                    if not self._eh_numero(qtd):
                        raise TypeError(f"Quantidade inválida para '{item_id}' na loja '{id_loja}'.")

            cenario_salvo = dados.get("cenario_atual", "CASA")
            if cenario_salvo not in self.CENARIOS_VALIDOS:
                logger.warning(f"[SaveManager] Cenário inválido '{cenario_salvo}', revertendo para 'CASA'.")
                cenario_salvo = "CASA"

            nivel_raw = halia_dados.get("nivel", 1)
            nivel_novo = max(1, int(1 if nivel_raw is None else nivel_raw))
            xp_raw = halia_dados.get("xp", 0)
            xp_novo = max(0, int(0 if xp_raw is None else xp_raw))

            raw_feiticos = halia_dados.get("feiticos_aprendidos", [])
            if raw_feiticos is None:
                feiticos_aprendidos_novos = set()
            elif isinstance(raw_feiticos, (list, tuple, set)):
                feiticos_aprendidos_novos = set(raw_feiticos)
            else:
                raise TypeError("feiticos_aprendidos inválido.")

            raw_maestria = halia_dados.get("maestria_feiticos", {})
            if raw_maestria is None:
                maestria_feiticos_nova = {}
            elif isinstance(raw_maestria, dict):
                maestria_feiticos_nova = dict(raw_maestria)
            else:
                raise TypeError("maestria_feiticos inválido.")

            mems_raw = halia_dados.get("fragmentos_memoria", 0)
            fragmentos_memoria_novos = max(0, min(7, int(0 if mems_raw is None else mems_raw)))
            sinc_raw = halia_dados.get("nivel_sincronia")
            nivel_sincronia_novo = int(sinc_raw) if sinc_raw is not None else (1 + fragmentos_memoria_novos)
            dinheiro_raw = halia_dados.get("dinheiro", 0)
            dinheiro_novo = max(0, int(0 if dinheiro_raw is None else dinheiro_raw))

            direcao_nova = halia_dados.get("direcao", "baixo")
            if not isinstance(direcao_nova, str):
                direcao_nova = "baixo"
            virado_direita_novo = bool(halia_dados.get("virado_direita", True))

            raw_x = halia_dados.get("x", 210)
            raw_y = halia_dados.get("y", 280)

            atributos_novos = Atributos.from_dict(halia_dados["atributos"])

            usar_inventario_padrao = False
            if "inventario" in halia_dados and halia_dados["inventario"]:
                inventario_novo = Inventario.from_dict(halia_dados["inventario"])
            else:
                inventario_novo = Inventario()
                usar_inventario_padrao = True

            raw_vida = halia_dados.get("vida_atual")
            if raw_vida is not None:
                raw_vida = float(raw_vida)
            vivo_salvo = bool(halia_dados.get("vivo", True))

            raw_mana = halia_dados.get("mana_atual")
            if raw_mana is not None:
                raw_mana = float(raw_mana)

            padrao_ataques = ["ataque_basico", "golpe_concentrado", "varredura_de_cajado", "estocada_perfurante"]
            raw_ataques = halia_dados.get("ataques_fisicos", [])
            if raw_ataques is None:
                salvos_ataques = []
            elif isinstance(raw_ataques, list):
                salvos_ataques = raw_ataques
            else:
                raise TypeError("ataques_fisicos inválido.")
            ataques_fisicos_novos = list(dict.fromkeys(salvos_ataques + padrao_ataques))

            flags_persistentes_novas = {}
            for attr_game, chave_save, padrao in self.FLAGS_PERSISTENTES:
                if attr_game == "patusco_pos_oakhaven":
                    raw_pos = flags.get(chave_save, None)
                    if (
                        isinstance(raw_pos, (list, tuple))
                        and len(raw_pos) == 2
                        and self._eh_numero(raw_pos[0])
                        and self._eh_numero(raw_pos[1])
                    ):
                        flags_persistentes_novas[attr_game] = (int(raw_pos[0]), int(raw_pos[1]))
                    else:
                        flags_persistentes_novas[attr_game] = None
                elif isinstance(padrao, bool):
                    flags_persistentes_novas[attr_game] = bool(flags.get(chave_save, padrao))
                else:
                    flags_persistentes_novas[attr_game] = flags.get(chave_save, padrao)
        except (TypeError, ValueError, KeyError, AttributeError) as e:
            _notificar_falha_load(str(e))
            return False

        # --- FASE 2: APLICAR ESTADO VALIDADO NA SESSÃO ---
        self.game.slot_atual = slot
        self.game.tempo_jogado = tempo_jogado_novo
        self.game.origem_pause = "JOGANDO"
        self.game.caixa_dialogo.historico_escolhas = historico_escolhas_novo

        # 1. Recupera as flags permanentes e o progresso
        self.game.mapa_casa.porta_aberta = bool(flags.get("porta_aberta", False))
        for attr_game, valor in flags_persistentes_novas.items():
            setattr(self.game, attr_game, valor)
        self.game.itens_coletados = itens_coletados_novos
        self.game.conversa_carroceiro_terminou = conversa_terminou_nova
        self.game.progresso_npcs = progresso_npcs_novo

        # Restaura progresso das missões
        if hasattr(self.game, 'missoes') and self.game.missoes:
            if missoes_dados is not None:
                self.game.missoes.from_dict(missoes_dados)
            else:
                self.game.missoes.resetar()

        # Reseta flags temporárias de transição, cutscenes e batalha em andamento
        for attr_game, padrao in self.FLAGS_TRANSITORIAS:
            setattr(self.game, attr_game, padrao)
        self.game.inimigos_em_cena = []
        self.game.transicao.estado = "INATIVO"

        # 2. Carrega o cenário com validação e desobstrui caminhos se já resolvidos
        self.game.mapa_casa.restaurar_bloqueio_estrada2()
        self.game.mapa_casa.carregar_cenario(cenario_salvo)

        if cenario_salvo == "ESTRADA_2":
            if self.game.magia_ativa == "CONCLUIDO" or self.game.combate_estrada_concluido or flags.get("puzzle_concluido", False):
                self.game.magia_ativa = "CONCLUIDO"
                self.game.mapa_casa.desobstruir_estrada(self.game.magia_usada_no_puzzle or "FOGO")

        # 3. Restaura atributos, Grimório e inventário de Halia
        halia = self.game.halia

        halia.nivel = nivel_novo
        halia.xp = xp_novo
        halia.xp_proximo_nivel = halia.calcular_xp_proximo(halia.nivel)
        halia.feiticos_aprendidos = feiticos_aprendidos_novos
        halia.maestria_feiticos = maestria_feiticos_nova

        halia.fragmentos_memoria = fragmentos_memoria_novos
        halia.nivel_sincronia = nivel_sincronia_novo
        halia.dinheiro = dinheiro_novo
        halia.direcao = direcao_nova
        halia.virado_direita = virado_direita_novo

        # Saneamento e verificação de limites do mundo para coordenadas (x, y)
        larg_mundo = self.game.mapa_casa.largura_mundo
        alt_mundo = self.game.mapa_casa.altura_mundo
        if self._eh_numero(raw_x) and self._eh_numero(raw_y) and (0 <= raw_x <= larg_mundo - 20) and (0 <= raw_y <= alt_mundo - 20):
            halia.x = raw_x
            halia.y = raw_y
        else:
            spawn_def = self.SPAWNS_SEGUROS.get(cenario_salvo, (100, 100))
            halia.x, halia.y = spawn_def

        halia.atributos = atributos_novos
        halia.inventario = inventario_novo
        if usar_inventario_padrao:
            halia.inicializar_inventario_padrao()

        halia.recalcular_status_derivados(manter_porcentagem=False)

        # Saneamento de vida e mana: nunca permite que Halia carregue morta/com 0 de vida
        vida_alvo = halia.vida_maxima if raw_vida is None else raw_vida
        if vida_alvo <= 0:
            halia.vida_atual = halia.vida_maxima
            halia.vivo = True
        else:
            halia.vida_atual = min(vida_alvo, halia.vida_maxima)
            halia.vivo = vivo_salvo

        mana_alvo = halia.mana_maxima if raw_mana is None else raw_mana
        halia.mana_atual = max(0, min(mana_alvo, halia.mana_maxima))

        # Limpa resíduos de combate
        halia.condicoes.clear()
        halia.defendendo = False
        halia.vulneravel = False
        halia.focado = False

        if halia.vivo:
            direcao = getattr(halia, 'direcao', 'baixo')
            estado_idle = f"idle_{direcao}" if f"idle_{direcao}" in halia.animacoes else "idle_baixo"
            halia.mudar_estado(estado_idle)
        else:
            halia.mudar_estado("morrer")

        if hasattr(halia, 'atualizar_animacao'):
            halia.atualizar_animacao()

        # Sincroniza o Grimório para garantir todos os feitiços do nível atual de Memória
        halia.atualizar_grimorio()

        # Sincroniza técnicas de ataque físico de cajado
        halia.ataques_fisicos = ataques_fisicos_novos

        # Restaura Carroceiro
        self.game.conversa_carroceiro_terminou = conversa_terminou_nova

        if cenario_salvo == "CASA":
            self.game.carroceiro.x = carroceiro_dados.get("x", 1350)
            self.game.carroceiro.y = carroceiro_dados.get("y", 330)
            self.game.carroceiro_visivel = carroceiro_dados.get("visivel", False)
            self.game.carroceiro_andando = False
            self.game.carroceiro.velocidade = 2
        elif cenario_salvo == "ESTRADA":
            padrao_x = 900 if conversa_terminou_nova else 1350
            self.game.carroceiro.x = carroceiro_dados.get("x", padrao_x)
            self.game.carroceiro.y = carroceiro_dados.get("y", 330)
            self.game.carroceiro_visivel = carroceiro_dados.get("visivel", conversa_terminou_nova)
            self.game.carroceiro_andando = carroceiro_dados.get("andando", False)
            self.game.carroceiro.velocidade = 2 if not conversa_terminou_nova else 0
        else:  # ESTRADA_2 ou cenários posteriores
            self.game.carroceiro.x = carroceiro_dados.get("x", 200)
            self.game.carroceiro.y = carroceiro_dados.get("y", 330)
            self.game.carroceiro_visivel = carroceiro_dados.get("visivel", (cenario_salvo == "ESTRADA_2"))
            self.game.carroceiro_andando = False
            self.game.carroceiro.velocidade = 0

        # 4. Respawn Inteligente de Inimigos em Cenários de Missão/Combate Ativos
        if cenario_salvo == "ORLA_NORTE":
            missao_ronda = (self.game.missoes.obter_missao("missao_ronda_fronteiras") if hasattr(self.game, "missoes") else None)
            if missao_ronda and missao_ronda.get("status") == "ATIVA" and not self.game.missoes.pronta_para_entregar("missao_ronda_fronteiras"):
                from src.entities.enemy_factory import EnemyFactory
                b1 = EnemyFactory.criar("mimico", x=565, y=285, nome_custom="Mímico Batedor 1")
                b2 = EnemyFactory.criar("mimico", x=665, y=305, nome_custom="Mímico Batedor 2")
                for b in (b1, b2):
                    b.velocidade = 0
                    b.virado_direita = False
                    b.direcao = "esquerda"
                    b.recompensas = {"moedas": 25, "memorias": 0, "xp": 45}
                    b.disfarcado = True
                    b.revelado = False
                    b.revelando = False
                    b.mudar_estado("corpo")
                self.game.inimigos_em_cena = [b1, b2]
        elif cenario_salvo == "NINHO_DRAGAO":
            if self.game.dragao_derrotado or halia.fragmentos_memoria >= 2:
                self.game.dragao_derrotado = True
                ninho = getattr(self.game.mapa_casa, "cenario_objeto", None)
                if ninho is not None:
                    ninho.ninho_amanhecer = True
                    ninho.dragao_derrotado = True
                    if hasattr(ninho, "inicializar_cenario"):
                        ninho.inicializar_cenario()
            else:
                from src.entities.enemy_factory import EnemyFactory
                dragao = EnemyFactory.criar_boss("dragao_vermelho", x=575, y=210, nome_custom="Ignis'Vahr, o Dragão Vermelho")
                dragao.velocidade = 0
                dragao.virado_direita = False
                dragao.direcao = "esquerda"
                self.game.inimigos_em_cena = [dragao]
                if hasattr(self.game, "audio") and self.game.audio:
                    self.game.audio.tocar_musica("combate_dragao", loop=-1, fade_ms=800)

        # 5. Sincroniza Câmera 2D, Filtro de Memória, HUD e telas visuais
        if hasattr(self.game, 'estados') and "JOGANDO" in self.game.estados:
            self.game.estados["JOGANDO"].atualizar_camera(instantaneo=True)
            self.game.estados["JOGANDO"].memoria_anterior_registrada = halia.fragmentos_memoria

        if hasattr(self.game, 'filtro_memoria') and self.game.filtro_memoria:
            self.game.filtro_memoria.definir_estagio(halia.fragmentos_memoria, com_transicao_suave=False)
        if hasattr(self.game, 'tela_despertar') and self.game.tela_despertar:
            self.game.tela_despertar.reiniciar()
        if hasattr(self.game, 'hud') and self.game.hud:
            self.game.hud.memorias_coletadas = halia.fragmentos_memoria

        # 6. Restaura estado dos estoques de lojas isolado por slot
        Loja.carregar_estado_lojas(lojas_dados)

        # 7. Blindagem de Autosave (Decisão D3): ao carregar um Save Manual, sincroniza o autosave
        # do slot somente após o carregamento ter sido aplicado com sucesso
        if tipo_efetivo == "manual" and slot:
            self.salvar_estado(slot, tipo="autosave", silenciar_notificacao=True)

        # Dispara notificação push de confirmação ao carregar (com aviso de fallback pela Decisão D4)
        if hasattr(self.game, 'notificacoes') and self.game.notificacoes:
            if usou_fallback_tipo:
                lbl_pedido = "Save manual" if tipo_pedido == "manual" else "Autosave"
                lbl_carregado = "autosave" if tipo_efetivo == "autosave" else "save manual"
                self.game.notificacoes.notificar(
                    "notificacao_carregar_fallback",
                    tipo_pedido=lbl_pedido,
                    tipo_carregado=lbl_carregado,
                    slot=slot_str
                )
            else:
                self.game.notificacoes.notificar("notificacao_carregar", slot=slot_str)

        return True

    def resetar_progresso(self, slot_novo):
        """Limpa as variáveis globais para iniciar um Novo Jogo limpo no slot."""
        slot_novo = save_io.normalizar_slot(slot_novo)
        self.game.slot_atual = slot_novo
        self.game.tempo_jogado = 0.0
        self.game.itens_coletados = []
        self.game.caixa_dialogo.historico_escolhas.clear()
        save_io.apagar_dados(slot_novo, tipo="autosave")
        Loja.resetar_lojas()

        # Reset da Halia
        halia = self.game.halia
        halia.x, halia.y = 210, 280
        halia.fragmentos_memoria = 0
        halia.nivel_sincronia = 1
        halia.dinheiro = 0
        halia.atributos = Atributos(forca=7, destreza=10, constituicao=10, intelecto=13, sabedoria=11, presenca=12)
        halia.inventario = Inventario()
        halia.inicializar_inventario_padrao()
        halia.recalcular_status_derivados(manter_porcentagem=False)
        halia.atualizar_grimorio()
        halia.ataques_fisicos = ["ataque_basico", "golpe_concentrado", "varredura_de_cajado", "estocada_perfurante"]
        halia.vida_atual = halia.vida_maxima
        halia.mana_atual = halia.mana_maxima
        halia.vivo = True
        halia.mudar_estado("idle")

        # Reset do Carroceiro
        carroceiro = self.game.carroceiro
        carroceiro.x, carroceiro.y = 1350, 330
        carroceiro.velocidade = 2
        self.game.carroceiro_visivel = False
        self.game.carroceiro_andando = False
        self.game.conversa_carroceiro_terminou = False
        self.game.progresso_npcs = {"carroceiro": 0}

        # Reset de Flags do Mapa e Progresso
        self.game.mapa_casa.porta_aberta = False
        for attr_game, _chave_save, padrao in self.FLAGS_PERSISTENTES:
            setattr(self.game, attr_game, padrao)
        for attr_game, padrao in self.FLAGS_TRANSITORIAS:
            setattr(self.game, attr_game, padrao)
        self.game.inimigos_em_cena = []
        self.game.transicao.estado = "INATIVO"
        self.game.mapa_casa.restaurar_bloqueio_estrada2()
        self.game.mapa_casa.carregar_cenario("CASA")

        if hasattr(self.game, 'filtro_memoria') and self.game.filtro_memoria:
            self.game.filtro_memoria.reiniciar(0)
        if hasattr(self.game, 'tela_despertar') and self.game.tela_despertar:
            self.game.tela_despertar.reiniciar()
        if hasattr(self.game, 'estados') and "JOGANDO" in self.game.estados:
            self.game.estados["JOGANDO"].memoria_anterior_registrada = 0
            self.game.estados["JOGANDO"].atualizar_camera(instantaneo=True)
        if hasattr(self.game, 'hud') and self.game.hud:
            self.game.hud.memorias_coletadas = 0

        # Reinicia o progresso das missões
        if hasattr(self.game, 'missoes'):
            self.game.missoes.resetar()

        self.game.mapa_casa.carregar_cenario("CASA")

    @staticmethod
    def _eh_numero(valor):
        """Retorna True para int ou float, rejeitando booleanos."""
        return isinstance(valor, (int, float)) and not isinstance(valor, bool)

    @staticmethod
    def _eh_inteiro(valor):
        """Retorna True para int, rejeitando booleanos."""
        return isinstance(valor, int) and not isinstance(valor, bool)

    def _validar_dados_save(self, dados, slot=None, tipo="manual", verificar_limites_estritos=False):
        """
        Valida a estrutura e os tipos de um dicionário de save já carregado.
        Retorna (True, 'Save íntegro') se válido, ou (False, 'Motivo') caso contrário.
        """
        rotulo_slot = f"slot {slot} ({tipo})" if slot is not None else f"save ({tipo})"
        if not dados or not isinstance(dados, dict):
            return False, f"Dados do {rotulo_slot} corrompidos ou formato JSON inválido."

        chaves_obrigatorias = ["cenario_atual", "halia", "flags"]
        for chave in chaves_obrigatorias:
            if chave not in dados:
                return False, f"{rotulo_slot.capitalize()} com estrutura corrompida: chave '{chave}' ausente."

        # Validação do cenário
        cenario = dados.get("cenario_atual")
        if not isinstance(cenario, str) or (verificar_limites_estritos and cenario not in self.CENARIOS_VALIDOS):
            return False, f"Cenário '{cenario}' não reconhecido no {rotulo_slot}."

        if not isinstance(dados.get("flags"), dict):
            return False, f"Bloco 'flags' inválido no {rotulo_slot}."

        if "tempo_jogado" in dados and dados["tempo_jogado"] is not None:
            if not self._eh_numero(dados["tempo_jogado"]):
                return False, f"Campo 'tempo_jogado' inválido no {rotulo_slot}."

        for chave_dict in ("carroceiro", "progresso_npcs", "lojas"):
            if chave_dict in dados and dados[chave_dict] is not None and not isinstance(dados[chave_dict], dict):
                return False, f"Bloco '{chave_dict}' inválido no {rotulo_slot}."

        if "missoes" in dados and dados["missoes"] is not None:
            missoes_dados = dados["missoes"]
            if not isinstance(missoes_dados, dict):
                return False, f"Bloco 'missoes' inválido no {rotulo_slot}."
            for subchave in ("missoes", "progresso"):
                if subchave in missoes_dados and missoes_dados[subchave] is not None:
                    sub = missoes_dados[subchave]
                    if not isinstance(sub, dict) or any(not isinstance(v, dict) for v in sub.values()):
                        return False, f"Subbloco 'missoes.{subchave}' inválido no {rotulo_slot}."

        # Validação da entidade Halia
        halia_dados = dados.get("halia", {})
        if not isinstance(halia_dados, dict) or not isinstance(halia_dados.get("atributos"), dict):
            return False, f"{rotulo_slot.capitalize()} com dados de Halia corrompidos ou ausentes."

        # Validação da integridade dos atributos
        atributos = halia_dados.get("atributos", {})
        chaves_attr = ["forca", "destreza", "constituicao", "intelecto", "sabedoria", "presenca"]
        for attr in chaves_attr:
            if attr not in atributos or not self._eh_numero(atributos[attr]):
                return False, f"Atributo '{attr}' corrompido no {rotulo_slot}."

        campos_numericos_halia = (
            "nivel", "xp", "dinheiro", "vida_atual", "vida_maxima",
            "mana_atual", "mana_maxima", "nivel_sincronia", "x", "y",
        )
        for campo in campos_numericos_halia:
            if campo in halia_dados and halia_dados[campo] is not None and not self._eh_numero(halia_dados[campo]):
                return False, f"Campo '{campo}' de Halia inválido no {rotulo_slot}."

        # Validação dos fragmentos de memória (0 a 7 quando estrito)
        if "fragmentos_memoria" in halia_dados and halia_dados["fragmentos_memoria"] is not None:
            mems = halia_dados["fragmentos_memoria"]
            if not self._eh_inteiro(mems) or (verificar_limites_estritos and (mems < 0 or mems > 7)):
                return False, f"Valor de fragmentos de memória inválido ({mems}) no {rotulo_slot}."

        # Validação do inventário
        if "inventario" in halia_dados and halia_dados["inventario"] is not None:
            inv_dados = halia_dados["inventario"]
            if not isinstance(inv_dados, dict):
                return False, f"Bloco 'inventario' inválido no {rotulo_slot}."
            if "capacidade" in inv_dados and inv_dados["capacidade"] is not None and not self._eh_inteiro(inv_dados["capacidade"]):
                return False, f"Capacidade de inventário inválida no {rotulo_slot}."
            if "slots" in inv_dados and inv_dados["slots"] is not None:
                if not isinstance(inv_dados["slots"], list) or any(not isinstance(s, dict) for s in inv_dados["slots"]):
                    return False, f"Lista de slots do inventário inválida no {rotulo_slot}."
            if "equipados" in inv_dados and inv_dados["equipados"] is not None and not isinstance(inv_dados["equipados"], dict):
                return False, f"Equipamentos do inventário inválidos no {rotulo_slot}."

        return True, "Save íntegro"

    def verificar_integridade_slot(self, slot, tipo="manual"):
        """
        Verifica a integridade estrutural, consistência de esquema e limites do save no slot.
        Retorna (True, 'Save íntegro') se válido, ou (False, 'Motivo') se ausente ou corrompido.
        """
        if not save_io.save_existe(slot, tipo=tipo):
            return False, f"Nenhum arquivo de save ({tipo}) encontrado para o slot {slot}."

        dados = save_io.carregar_dados(slot, tipo=tipo)
        return self._validar_dados_save(dados, slot=slot, tipo=tipo, verificar_limites_estritos=True)

    def diagnosticar_saves(self):
        """
        Executa um diagnóstico detalhado em todos os slots (manuais e autosaves),
        reportando o status de integridade e metadados de cada arquivo em disco.
        """
        diagnostico = {}
        for s in range(1, save_io.MAX_SLOTS + 1):
            diag_slot = {"slot": s}
            for tipo in ["manual", "autosave"]:
                existe = save_io.save_existe(s, tipo=tipo)
                if existe:
                    valido, motivo = self.verificar_integridade_slot(s, tipo=tipo)
                    diag_slot[tipo] = {
                        "existe": True,
                        "integro": valido,
                        "status": motivo
                    }
                else:
                    diag_slot[tipo] = {"existe": False, "integro": False, "status": "Vazio"}
            diagnostico[s] = diag_slot
        return diagnostico

    def save_existe(self, slot, tipo=None):
        """Verifica se existe save no slot especificado."""
        return save_io.save_existe(slot, tipo)

    def apagar_dados(self, slot, tipo="ambos"):
        """Deleta os arquivos de save do slot especificado."""
        return save_io.apagar_dados(slot, tipo)

    def obter_resumo_slots(self):
        """Retorna resumo com status e metadados dos 4 slots."""
        return save_io.obter_resumo_slots()

    def verificar_saves_globais(self):
        """Verifica se há qualquer save em qualquer um dos slots."""
        return save_io.verificar_saves_globais()
