# src/core/save_manager.py
import logging
from src.utils import save_manager as save_io
from src.mechanics.attributes import Atributos
from src.mechanics.inventory import Inventario

logger = logging.getLogger(__name__)


class SaveManager:
    """
    Gerenciador Central de Persistência, Integridade e Ciclo de Vida dos Saves de Oblivium.

    Responsabilidades:
    - Serialização completa do estado de jogo (Halia, Carroceiro, Cenários, Flags e Inventário).
    - Desserialização e reconstrução de entidades e subsistemas ao restaurar saves.
    - Sincronização de integridade entre Saves Manuais e Autosaves (Blindagem de Autosave).
    - Verificação de integridade estrutural e de esquema de arquivos de save em disco.
    - Reinicialização segura de progresso para criação de Novo Jogo.
    """

    def __init__(self, game):
        self.game = game

    def salvar_estado(self, slot=None, tipo="manual", silenciar_notificacao=False):
        """Serializa todo o estado atual da sessão e persiste no slot indicado em disco."""
        slot_alvo = slot or self.game.slot_atual
        if not slot_alvo:
            return False

        halia = self.game.halia
        carroceiro = self.game.carroceiro
        mapa = self.game.mapa_casa

        dados_save = {
            "cenario_atual": mapa.cenario_atual,
            "tempo_jogado": self.game.tempo_jogado,
            "slot": slot_alvo,
            "tipo_save": tipo,
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
                "fragmentos_memoria": getattr(halia, 'fragmentos_memoria', 0),
                "nivel_sincronia": getattr(halia, 'nivel_sincronia', 1),
                "dinheiro": getattr(halia, 'dinheiro', 0),
                "atributos": halia.atributos.to_dict(),
                "inventario": halia.inventario.to_dict() if hasattr(halia, 'inventario') else {},
                "magias_desbloqueadas": getattr(halia, 'magias_desbloqueadas', []),
                "ataques_fisicos": getattr(halia, 'ataques_fisicos', ["ataque_basico", "golpe_concentrado"])
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
                "itens_coletados": self.game.itens_coletados,
                "historico_dialogos": list(self.game.caixa_dialogo.historico_escolhas)
            }
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
        self.game.itens_coletados = flags.get("itens_coletados", [])
        self.game.conversa_carroceiro_terminou = dados.get("carroceiro", {}).get("conversa_terminou", False)

        # Reseta flags temporárias de transição e batalha em andamento
        self.game.inimigos_em_cena = []
        self.game.cena_inimigos_andando = False
        self.game.iniciando_combate = False
        self.game.conversa_combate_ativa = False
        self.game.transicao.estado = "INATIVO"

        # 2. Carrega o cenário e desobstrui caminhos se já resolvidos
        cenario_salvo = dados.get("cenario_atual", "CASA")
        self.game.mapa_casa.restaurar_bloqueio_estrada2()
        self.game.mapa_casa.carregar_cenario(cenario_salvo)

        if cenario_salvo == "ESTRADA_2":
            if self.game.magia_ativa == "CONCLUIDO" or self.game.combate_estrada_concluido or flags.get("puzzle_concluido", False):
                self.game.magia_ativa = "CONCLUIDO"
                self.game.mapa_casa.desobstruir_estrada(self.game.magia_usada_no_puzzle or "FOGO")

        # 3. Restaura posições da Halia, atributos, Grimório e NPCs
        halia_dados = dados.get("halia", {})
        halia = self.game.halia
        halia.x = halia_dados.get("x", 210)
        halia.y = halia_dados.get("y", 280)
        halia.direcao = halia_dados.get("direcao", "baixo")
        halia.virado_direita = halia_dados.get("virado_direita", True)
        halia.fragmentos_memoria = halia_dados.get("fragmentos_memoria", 0)
        halia.nivel_sincronia = halia_dados.get("nivel_sincronia", 1 + halia.fragmentos_memoria)
        halia.dinheiro = halia_dados.get("dinheiro", 0)

        if "atributos" in halia_dados:
            halia.atributos = Atributos.from_dict(halia_dados["atributos"])

        if "inventario" in halia_dados and halia_dados["inventario"]:
            halia.inventario = Inventario.from_dict(halia_dados["inventario"])
        else:
            halia.inventario = Inventario()
            halia.inicializar_inventario_padrao()

        halia.recalcular_status_derivados(manter_porcentagem=False)

        halia.vida_atual = halia_dados.get("vida_atual", halia.vida_maxima)
        halia.mana_atual = halia_dados.get("mana_atual", halia.mana_maxima)

        # Herda a condição de vivo ou reanima Halia para poder movimentar
        esta_vivo = halia_dados.get("vivo", True)
        if halia.vida_atual > 0:
            halia.vivo = esta_vivo
        else:
            halia.restaurar_total()

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

        # Atualiza a animação imediatamente para desenhar o sprite correto de imediato
        if hasattr(halia, 'atualizar_animacao'):
            halia.atualizar_animacao()

        if "magias_desbloqueadas" in halia_dados and halia_dados["magias_desbloqueadas"]:
            halia.magias_desbloqueadas = list(halia_dados["magias_desbloqueadas"])
        else:
            halia.atualizar_grimorio()

        if "ataques_fisicos" in halia_dados:
            halia.ataques_fisicos = list(halia_dados["ataques_fisicos"])

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
        else:  # ESTRADA_2
            self.game.carroceiro.x = carroceiro_dados.get("x", 200)
            self.game.carroceiro.y = carroceiro_dados.get("y", 330)
            self.game.carroceiro_visivel = carroceiro_dados.get("visivel", True)
            self.game.carroceiro_andando = False
            self.game.carroceiro.velocidade = 0

        # 4. Sincroniza imediatamente o Filtro de Memória, HUD e telas visuais com o save carregado
        if hasattr(self.game, 'filtro_memoria') and self.game.filtro_memoria:
            self.game.filtro_memoria.definir_estagio(halia.fragmentos_memoria, com_transicao_suave=False)
        if hasattr(self.game, 'tela_despertar') and self.game.tela_despertar:
            self.game.tela_despertar.reiniciar()
        if hasattr(self.game, 'estados') and "JOGANDO" in self.game.estados:
            self.game.estados["JOGANDO"].memoria_anterior_registrada = halia.fragmentos_memoria
        if hasattr(self.game, 'hud') and self.game.hud:
            self.game.hud.memorias_coletadas = halia.fragmentos_memoria

        # 5. Blindagem de Autosave: ao carregar um Save Manual, sincroniza o autosave do slot
        # com o checkpoint restaurado, garantindo que o autosave não fique apontando para um "futuro" antigo
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
        halia.dinheiro = 0
        halia.atributos = Atributos(forca=7, destreza=10, constituicao=10, intelecto=13, sabedoria=11, presenca=12)
        halia.inventario = Inventario()
        halia.inicializar_inventario_padrao()
        halia.recalcular_status_derivados(manter_porcentagem=False)
        halia.atualizar_grimorio()
        # Inicia o jogo com vida e mana cheias
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
        self.game.progresso_npcs["carroceiro"] = 0

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
        self.game.iniciando_combate = False
        self.game.cena_inimigos_andando = False
        self.game.conversa_combate_ativa = False
        self.game.inimigos_em_cena = []
        self.game.transicao.estado = "INATIVO"
        self.game.mapa_casa.restaurar_bloqueio_estrada2()
        self.game.mapa_casa.carregar_cenario("CASA")

        # Sincroniza e reseta o Filtro de Memória (100% P&B / Estágio 0), HUD e Cutscenes
        if hasattr(self.game, 'filtro_memoria') and self.game.filtro_memoria:
            self.game.filtro_memoria.reiniciar(0)
        if hasattr(self.game, 'tela_despertar') and self.game.tela_despertar:
            self.game.tela_despertar.reiniciar()
        if hasattr(self.game, 'estados') and "JOGANDO" in self.game.estados:
            self.game.estados["JOGANDO"].memoria_anterior_registrada = 0
        if hasattr(self.game, 'hud') and self.game.hud:
            self.game.hud.memorias_coletadas = 0

        # Recarrega o cenário inicial limpo
        self.game.mapa_casa.carregar_cenario("CASA")

    def verificar_integridade_slot(self, slot, tipo="manual"):
        """
        Verifica a integridade estrutural e consistência de esquema do save no slot.
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

        halia_dados = dados.get("halia", {})
        if not isinstance(halia_dados, dict) or "atributos" not in halia_dados:
            return False, f"Slot {slot} ({tipo}) com dados de Halia corrompidos ou ausentes."

        return True, "Save íntegro"

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
