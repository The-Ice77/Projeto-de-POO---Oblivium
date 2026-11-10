# src/core/save_manager.py
import logging
import datetime
from src.utils import save_manager as save_io
from src.mechanics.attributes import Atributos
from src.mechanics.inventory import Inventario

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
        slot_alvo = slot or self.game.slot_atual
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
            "flags": {
                "porta_aberta": getattr(mapa, 'porta_aberta', False),
                "investigou_pedras": self.game.investigou_pedras,
                "flashback_magia_concluido": self.game.flashback_magia_concluido,
                "magia_ativa": self.game.magia_ativa,
                "magia_usada_no_puzzle": self.game.magia_usada_no_puzzle,
                "puzzle_concluido": (self.game.magia_ativa == "CONCLUIDO"),
                "combate_concluido": getattr(self.game, 'combate_estrada_concluido', False),
                "pedra_torvald_quebrada": getattr(self.game, 'pedra_torvald_quebrada', False),
                "oakhaven_noite": getattr(self.game, 'oakhaven_noite', False),
                "oakhaven_destruida": getattr(self.game, 'oakhaven_destruida', False),
                "itens_coletados": self.game.itens_coletados,
                "historico_dialogos": list(self.game.caixa_dialogo.historico_escolhas)
            },
            "missoes": self.game.missoes.to_dict() if hasattr(self.game, 'missoes') else {}
        }

        save_io.salvar_dados(slot_alvo, dados_save, tipo=tipo)

        if not silenciar_notificacao and hasattr(self.game, 'notificacoes') and self.game.notificacoes:
            slot_num = str(slot_alvo).replace("slot_", "")
            slot_str = f"Slot {slot_num}"
            if tipo == "autosave":
                self.game.notificacoes.notificar("notificacao_autosave", slot=slot_str)
            else:
                self.game.notificacoes.notificar("notificacao_salvo", slot=slot_str)

        return True

    def carregar_estado(self, slot, tipo="manual"):
        """Carrega e desserializa os dados do save, restaurando entidades, flags e cenários."""
        dados = save_io.carregar_dados(slot, tipo=tipo)
        if not dados:
            outro_tipo = "autosave" if tipo == "manual" else "manual"
            dados = save_io.carregar_dados(slot, tipo=outro_tipo)

        if not dados:
            return False

        self.game.slot_atual = slot
        self.game.tempo_jogado = dados.get("tempo_jogado", 0.0)
        self.game.origem_pause = "JOGANDO"
        self.game.caixa_dialogo.historico_escolhas = set(dados.get("flags", {}).get("historico_dialogos", []))

        # 1. Recupera as flags e o progresso
        flags = dados.get("flags", {})
        self.game.mapa_casa.porta_aberta = flags.get("porta_aberta", False)
        self.game.investigou_pedras = flags.get("investigou_pedras", False)
        self.game.flashback_magia_concluido = flags.get("flashback_magia_concluido", False)
        self.game.magia_ativa = flags.get("magia_ativa", None)
        self.game.magia_usada_no_puzzle = flags.get("magia_usada_no_puzzle", None)
        self.game.combate_estrada_concluido = flags.get("combate_concluido", False)
        self.game.pedra_torvald_quebrada = flags.get("pedra_torvald_quebrada", False)
        self.game.oakhaven_noite = flags.get("oakhaven_noite", False)
        self.game.oakhaven_destruida = flags.get("oakhaven_destruida", False)
        self.game.itens_coletados = flags.get("itens_coletados", [])
        self.game.conversa_carroceiro_terminou = dados.get("carroceiro", {}).get("conversa_terminou", False)
        self.game.progresso_npcs = dados.get("progresso_npcs", {"carroceiro": 0})

        # Restaura progresso das missões
        if hasattr(self.game, 'missoes') and "missoes" in dados:
            self.game.missoes.from_dict(dados.get("missoes", {}))

        # Reseta flags temporárias de transição e batalha em andamento
        self.game.inimigos_em_cena = []
        self.game.cena_inimigos_andando = False
        self.game.iniciando_combate = False
        self.game.conversa_combate_ativa = False
        self.game.transicao.estado = "INATIVO"

        # 2. Carrega o cenário com validação e desobstrui caminhos se já resolvidos
        cenario_salvo = dados.get("cenario_atual", "CASA")
        if cenario_salvo not in self.CENARIOS_VALIDOS:
            logger.warning(f"[SaveManager] Cenário inválido '{cenario_salvo}', revertendo para 'CASA'.")
            cenario_salvo = "CASA"

        self.game.mapa_casa.restaurar_bloqueio_estrada2()
        self.game.mapa_casa.carregar_cenario(cenario_salvo)

        if cenario_salvo == "ESTRADA_2":
            if self.game.magia_ativa == "CONCLUIDO" or self.game.combate_estrada_concluido or flags.get("puzzle_concluido", False):
                self.game.magia_ativa = "CONCLUIDO"
                self.game.mapa_casa.desobstruir_estrada(self.game.magia_usada_no_puzzle or "FOGO")

        # 3. Restaura atributos, Grimório e inventário de Halia
        halia_dados = dados.get("halia", {})
        halia = self.game.halia

        halia.nivel = max(1, int(halia_dados.get("nivel", 1)))
        halia.xp = max(0, int(halia_dados.get("xp", 0)))
        halia.xp_proximo_nivel = halia.calcular_xp_proximo(halia.nivel)
        halia.feiticos_aprendidos = set(halia_dados.get("feiticos_aprendidos", []))
        halia.maestria_feiticos = halia_dados.get("maestria_feiticos", {})

        halia.fragmentos_memoria = max(0, min(7, int(halia_dados.get("fragmentos_memoria", 0))))
        halia.nivel_sincronia = halia_dados.get("nivel_sincronia", 1 + halia.fragmentos_memoria)
        halia.dinheiro = max(0, int(halia_dados.get("dinheiro", 0)))
        halia.direcao = halia_dados.get("direcao", "baixo")
        halia.virado_direita = halia_dados.get("virado_direita", True)

        # Saneamento e verificação de limites do mundo para coordenadas (x, y)
        larg_mundo = self.game.mapa_casa.largura_mundo
        alt_mundo = self.game.mapa_casa.altura_mundo
        raw_x = halia_dados.get("x", 210)
        raw_y = halia_dados.get("y", 280)
        if isinstance(raw_x, (int, float)) and isinstance(raw_y, (int, float)) and (0 <= raw_x <= larg_mundo - 20) and (0 <= raw_y <= alt_mundo - 20):
            halia.x = raw_x
            halia.y = raw_y
        else:
            spawn_def = self.SPAWNS_SEGUROS.get(cenario_salvo, (100, 100))
            halia.x, halia.y = spawn_def

        if "atributos" in halia_dados:
            halia.atributos = Atributos.from_dict(halia_dados["atributos"])

        if "inventario" in halia_dados and halia_dados["inventario"]:
            halia.inventario = Inventario.from_dict(halia_dados["inventario"])
        else:
            halia.inventario = Inventario()
            halia.inicializar_inventario_padrao()

        halia.recalcular_status_derivados(manter_porcentagem=False)

        # Saneamento de vida e mana: nunca permite que Halia carregue morta/com 0 de vida
        raw_vida = halia_dados.get("vida_atual", halia.vida_maxima)
        if raw_vida <= 0:
            halia.vida_atual = halia.vida_maxima
            halia.vivo = True
        else:
            halia.vida_atual = min(raw_vida, halia.vida_maxima)
            halia.vivo = halia_dados.get("vivo", True)

        halia.mana_atual = max(0, min(halia_dados.get("mana_atual", halia.mana_maxima), halia.mana_maxima))

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
        padrao_ataques = ["ataque_basico", "golpe_concentrado", "varredura_de_cajado", "estocada_perfurante"]
        salvos_ataques = halia_dados.get("ataques_fisicos", [])
        halia.ataques_fisicos = list(dict.fromkeys(salvos_ataques + padrao_ataques))

        # Restaura Carroceiro
        carroceiro_dados = dados.get("carroceiro", {})
        conversa_terminou = carroceiro_dados.get("conversa_terminou", flags.get("conversa_carroceiro_terminou", False))
        self.game.conversa_carroceiro_terminou = conversa_terminou

        if cenario_salvo == "CASA":
            self.game.carroceiro.x = carroceiro_dados.get("x", 1350)
            self.game.carroceiro.y = carroceiro_dados.get("y", 330)
            self.game.carroceiro_visivel = carroceiro_dados.get("visivel", False)
            self.game.carroceiro_andando = False
            self.game.carroceiro.velocidade = 2
        elif cenario_salvo == "ESTRADA":
            padrao_x = 900 if conversa_terminou else 1350
            self.game.carroceiro.x = carroceiro_dados.get("x", padrao_x)
            self.game.carroceiro.y = carroceiro_dados.get("y", 330)
            self.game.carroceiro_visivel = carroceiro_dados.get("visivel", conversa_terminou)
            self.game.carroceiro_andando = carroceiro_dados.get("andando", False)
            self.game.carroceiro.velocidade = 2 if not conversa_terminou else 0
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
                b1 = EnemyFactory.criar("demonio_inferior", x=565, y=285, nome_custom="Batedor Demoníaco 1")
                b2 = EnemyFactory.criar("demonio_inferior", x=665, y=305, nome_custom="Batedor Demoníaco 2")
                for b in (b1, b2):
                    b.velocidade = 0
                    b.virado_direita = False
                    b.direcao = "esquerda"
                    b.recompensas = {"moedas": 25, "memorias": 0, "xp": 45}
                self.game.inimigos_em_cena = [b1, b2]
        elif cenario_salvo == "NINHO_DRAGAO":
            if halia.fragmentos_memoria < 2:
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

        # 6. Blindagem de Autosave: ao carregar um Save Manual, sincroniza o autosave do slot
        # com o checkpoint restaurado, garantindo consistência cronológica
        if tipo == "manual" and slot:
            self.salvar_estado(slot, tipo="autosave", silenciar_notificacao=True)

        # Dispara notificação push de confirmação ao carregar
        if hasattr(self.game, 'notificacoes') and self.game.notificacoes:
            slot_num = str(slot).replace("slot_", "")
            slot_str = f"Slot {slot_num}"
            self.game.notificacoes.notificar("notificacao_carregar", slot=slot_str)

        return True

    def resetar_progresso(self, slot_novo):
        """Limpa as variáveis globais para iniciar um Novo Jogo limpo no slot."""
        self.game.slot_atual = slot_novo
        self.game.tempo_jogado = 0.0
        self.game.itens_coletados = []
        self.game.caixa_dialogo.historico_escolhas.clear()
        save_io.apagar_dados(slot_novo, tipo="autosave")

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
        self.game.fechando_porta = False
        self.game.aguardando_fim_viagem = False
        self.game.investigou_pedras = False
        self.game.flashback_magia_concluido = False
        self.game.mapa_casa.porta_aberta = False
        self.game.magia_ativa = None
        self.game.magia_usada_no_puzzle = None
        self.game.magia_selecionada_temporaria = None
        self.game.combate_estrada_concluido = False
        self.game.pedra_torvald_quebrada = False
        self.game.oakhaven_noite = False
        self.game.oakhaven_destruida = False
        self.game.iniciando_combate = False
        self.game.cena_inimigos_andando = False
        self.game.conversa_combate_ativa = False
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

    def verificar_integridade_slot(self, slot, tipo="manual"):
        """
        Verifica a integridade estrutural, consistência de esquema e limites do save no slot.
        Retorna (True, 'Save íntegro') se válido, ou (False, 'Motivo') se ausente ou corrompido.
        """
        if not save_io.save_existe(slot, tipo=tipo):
            return False, f"Nenhum arquivo de save ({tipo}) encontrado para o slot {slot}."

        dados = save_io.carregar_dados(slot, tipo=tipo)
        if not dados or not isinstance(dados, dict):
            return False, f"Dados do slot {slot} ({tipo}) corrompidos ou formato JSON inválido."

        chaves_obrigatorias = ["cenario_atual", "halia", "flags"]
        for chave in chaves_obrigatorias:
            if chave not in dados:
                return False, f"Slot {slot} ({tipo}) com estrutura corrompida: chave '{chave}' ausente."

        # Validação do cenário
        cenario = dados.get("cenario_atual")
        if cenario not in self.CENARIOS_VALIDOS:
            return False, f"Cenário '{cenario}' não reconhecido no slot {slot} ({tipo})."

        # Validação da entidade Halia
        halia_dados = dados.get("halia", {})
        if not isinstance(halia_dados, dict) or "atributos" not in halia_dados:
            return False, f"Slot {slot} ({tipo}) com dados de Halia corrompidos ou ausentes."

        # Validação da integridade dos atributos
        atributos = halia_dados.get("atributos", {})
        chaves_attr = ["forca", "destreza", "constituicao", "intelecto", "sabedoria", "presenca"]
        for attr in chaves_attr:
            if attr not in atributos or not isinstance(atributos[attr], (int, float)):
                return False, f"Atributo '{attr}' corrompido no slot {slot} ({tipo})."

        # Validação dos fragmentos de memória (0 a 7)
        mems = halia_dados.get("fragmentos_memoria", 0)
        if not isinstance(mems, int) or mems < 0 or mems > 7:
            return False, f"Valor de fragmentos de memória inválido ({mems}) no slot {slot}."

        return True, "Save íntegro"

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
