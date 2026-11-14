# src/states/prologo_controller.py
import pygame
from src.entities.enemy_factory import EnemyFactory
from src.mechanics.item_factory import ItemFactory


class PrologoController:
    """
    Controlador modular da sequência do Prólogo (Casa de Halia, Estrada 1,
    Estrada 2, Carroceiro, puzzle das rochas e primeiro combate).
    Extraído de PlayingState mantendo 100% do comportamento original.
    """

    def __init__(self, game, playing_state):
        self.game = game
        self.playing_state = playing_state

    def checar_sucesso_timing(self):
        """Valida a tentativa do minigame de Bola de Fogo e dispara a cutscene correspondente."""
        res = self.game.mg_timing.checar_sucesso()
        if res == "VENCEU" or res is True:
            self.game.magia_ativa = "FOGO"
            self.game.distanciando_halia = True
            self.game.timer_magia = 0
            if hasattr(self.game, "conquistas") and self.game.conquistas:
                self.game.conquistas.desbloquear("chama_primordial")
        elif res == "AVANCOU_ETAPA":
            pass
        else:
            self.game.caixa_dialogo.iniciar_dialogo("falha_timing")

    def finalizar_minigame_levitacao(self, res):
        """Finaliza a levitação, assenta as rochas e abre o diálogo pos_levitar."""
        if res == "VENCEU":
            if hasattr(self.game.mapa_casa, "desobstruir_estrada"):
                self.game.mapa_casa.desobstruir_estrada("LEVITAR")
            self.game.magia_usada_no_puzzle = "LEVITAR"
            self.game.magia_ativa = "CONCLUIDO"
            self.game.distanciando_halia = False
            self.game.timer_magia = 0
            if hasattr(self.game, "conquistas") and self.game.conquistas:
                self.game.conquistas.desbloquear("dominio_gravidade")
            self.game.caixa_dialogo.iniciar_dialogo("pos_levitar")
            self.game.conversa_combate_ativa = True
        elif res == "PERDEU":
            if hasattr(self.game.mapa_casa, "atualizar_levitacao_minigame"):
                self.game.mapa_casa.atualizar_levitacao_minigame(0.0)
            self.game.caixa_dialogo.iniciar_dialogo("falha_mash")

    def atualizar_minigames(self, dt):
        """Atualiza os minigames de timing/mash e inicia o puzzle da Estrada 2 quando liberado."""
        if self.game.mg_timing.ativo:
            self.game.mg_timing.atualizar(dt)
        elif self.game.mg_mash.ativo:
            res = self.game.mg_mash.atualizar(dt)

            pct = self.game.mg_mash.get_progresso_pct()
            if hasattr(self.game.mapa_casa, "atualizar_levitacao_minigame"):
                self.game.mapa_casa.atualizar_levitacao_minigame(pct)

            if res in ["VENCEU", "PERDEU"]:
                self.finalizar_minigame_levitacao(res)

        if (
            self.game.mapa_casa.cenario_atual == "ESTRADA_2"
            and self.game.investigou_pedras
            and self.game.magia_ativa is None
            and not self.playing_state._bloqueio_ativo(
                incluir_transicao=False, incluir_inimigos_andando=False
            )
        ):
            if self.game.magia_selecionada_temporaria == "FOGO":
                self.game.magia_selecionada_temporaria = None
                self.game.mg_timing.iniciar()
            elif self.game.magia_selecionada_temporaria == "LEVITAR":
                self.game.magia_selecionada_temporaria = None
                self.game.mg_mash.iniciar()

    def mover_carroceiro_autonomo(self):
        """Move o Carroceiro automaticamente até encontrar Halia na Estrada 1."""
        next_h = pygame.Rect(
            int(self.game.carroceiro.x - 2),
            int(self.game.carroceiro.y),
            self.game.carroceiro.largura,
            self.game.carroceiro.altura,
        )
        h_halia = pygame.Rect(
            int(self.game.halia.x),
            int(self.game.halia.y),
            self.game.halia.largura,
            self.game.halia.altura,
        )
        if not next_h.colliderect(h_halia):
            self.game.carroceiro.mover(-1, 0, [])
        if self.game.carroceiro.x <= 900 or next_h.colliderect(h_halia):
            if self.game.carroceiro.x <= 900:
                self.game.carroceiro.x = 900
            self.game.carroceiro_andando = False
            self.game.carroceiro.velocidade = 0
            self.game.carroceiro.mudar_estado("idle")
            self.game.carroceiro.virado_direita = (self.game.halia.x > self.game.carroceiro.x)
            h_npc = pygame.Rect(
                int(self.game.carroceiro.x),
                int(self.game.carroceiro.y),
                self.game.carroceiro.largura,
                self.game.carroceiro.altura,
            )
            if h_npc not in self.game.mapa_casa.hitboxes:
                self.game.mapa_casa.hitboxes.append(h_npc)

    def atualizar_inimigos_e_combate(self):
        """Gerencia o surgimento e caminhada dos demônios após o puzzle na Estrada 2."""
        # 1. GATILHO DA CUTSCENE (Nascer dos inimigos)
        if self.game.conversa_combate_ativa and not self.game.caixa_dialogo.ativo:
            self.game.conversa_combate_ativa = False
            self.game.cena_inimigos_andando = True

            if self.game.halia.x > 1000:
                self.game.halia.x = 1000
            self.game.halia.virado_direita = True
            self.game.halia.direcao = "direita"
            self.game.halia.mudar_estado("idle")

            if self.game.magia_usada_no_puzzle == "FOGO":
                sombra1 = EnemyFactory.criar(
                    "demonio_inferior", x=1180, y=290, nome_custom="Demônio Inferior Voraz"
                )
                sombra2 = EnemyFactory.criar(
                    "demonio_inferior", x=1180, y=420, nome_custom="Demônio Inferior Vigia"
                )
                sombra1.velocidade = 3.5
                sombra2.velocidade = 3.5
                sombra1.recompensas = {"moedas": 20, "memorias": 0, "xp": 40}
                sombra2.recompensas = {"moedas": 20, "memorias": 0, "xp": 40}
                sombra1.virado_direita = False
                sombra2.virado_direita = False
                sombra1.direcao = "esquerda"
                sombra2.direcao = "esquerda"
                self.game.inimigos_em_cena.extend([sombra1, sombra2])
            elif self.game.magia_usada_no_puzzle == "LEVITAR":
                boss = EnemyFactory.criar_boss(
                    "demonio_superior", x=1180, y=310, nome_custom="Demônio Superior (Chefe)"
                )
                boss.velocidade = 3.5
                boss.recompensas = {"moedas": 45, "memorias": 0, "xp": 80}
                boss.virado_direita = False
                boss.direcao = "esquerda"
                self.game.inimigos_em_cena.append(boss)

        # 2. MOVIMENTO DA CUTSCENE (Roteirizado)
        if self.game.cena_inimigos_andando:
            x_parada = max(self.game.halia.x + self.game.halia.largura + 100, 850)
            alguem_chegou = False

            for inimigo in self.game.inimigos_em_cena:
                if not self.game.iniciando_combate:
                    inimigo.virado_direita = False
                    inimigo.direcao = "esquerda"
                    if inimigo.x > x_parada:
                        inimigo.mover(-inimigo.velocidade, 0)
                    else:
                        inimigo.mover(0, 0)
                        alguem_chegou = True

            if alguem_chegou and not self.game.iniciando_combate:
                self.game.iniciando_combate = True
                self.game.transicao.iniciar()

    def verificar_gatilhos_zona(self):
        """Processa os gatilhos espaciais e narrativos de CASA, ESTRADA e ESTRADA_2."""
        if (
            self.game.mapa_casa.cenario_atual == "CASA"
            and self.game.mapa_casa.porta_aberta
            and self.game.halia.y > 545
        ):
            self.game.mapa_casa.fechar_porta()
            self.game.caixa_dialogo.iniciar_dialogo("fechar_porta")

        if (
            self.game.mapa_casa.cenario_atual == "CASA"
            and not self.game.mapa_casa.porta_aberta
            and self.game.halia.x > 1220
        ):
            self.game.transicao.iniciar("Seguindo viagem...")

        if (
            self.game.mapa_casa.cenario_atual == "ESTRADA"
            and not self.game.carroceiro_visivel
            and self.game.halia.x > 640
        ):
            self.game.carroceiro_visivel = True
            self.game.carroceiro_andando = True
            self.game.carroceiro.velocidade = 2
            self.game.carroceiro.mudar_estado("andar")
            self.game.caixa_dialogo.iniciar_dialogo("avistar_carroceiro")

        if (
            self.game.mapa_casa.cenario_atual == "ESTRADA_2"
            and not self.game.investigou_pedras
            and self.game.halia.x > 1000
        ):
            self.game.investigou_pedras = True
            self.game.halia.x = 980
            self.game.caixa_dialogo.iniciar_dialogo(
                "escolha_magias" if self.game.flashback_magia_concluido else "investigar_pedras"
            )

        if self.game.carroceiro_andando:
            self.mover_carroceiro_autonomo()

        if (
            self.game.mapa_casa.cenario_atual == "ESTRADA"
            and self.game.aguardando_fim_viagem
            and not self.game.caixa_dialogo.ativo
        ):
            self.game.aguardando_fim_viagem = False
            self.game.conversa_carroceiro_terminou = True
            self.game.transicao.iniciar("Algumas horas depois...")

        # Partida com o carroceiro em Estrada 2 -> Desperta a Memória e Cores (Padrão original do Prólogo)
        if (
            self.game.mapa_casa.cenario_atual == "ESTRADA_2"
            and getattr(self.game, "partindo_estrada2", False)
            and not self.game.caixa_dialogo.ativo
        ):
            self.game.partindo_estrada2 = False
            self.game.conversa_carroceiro_terminou = True
            if hasattr(self.game, "conquistas") and self.game.conquistas:
                self.game.conquistas.desbloquear("rumo_a_vila")
            if self.game.halia.fragmentos_memoria < 1:
                self.game.halia.recuperar_memoria(1)
            if self.game.slot_atual:
                self.game.salvar_estado(self.game.slot_atual, tipo="autosave")

    def processar_escolha_dialogo(self, opt_id):
        """Trata opções de diálogo específicas do Prólogo; retorna True se interromper avanço."""
        if opt_id == "analisar_pedras":
            self.game.caixa_dialogo.ativo = False
            self.game.caixa_dialogo.em_escolha = False
            seq_flashback = self.game.caixa_dialogo.manager.obter_sequencia_linear("flashback_magia")
            self.game.flashback_sistema.iniciar(seq_flashback, game=self.game)
            return True
        elif opt_id == "escolha_fogo":
            self.game.magia_selecionada_temporaria = "FOGO"
        elif opt_id == "escolha_levitar":
            self.game.magia_selecionada_temporaria = "LEVITAR"
        elif opt_id in ["voltar_magia", "desistir_puzzle"]:
            self.game.investigou_pedras = False
        elif opt_id == "prosseguir":
            self.game.aguardando_fim_viagem = True
        elif opt_id == "seguir_capital":
            self.game.partindo_estrada2 = True
        return False

    def processar_interacao_item_inicial(self, item, id_do_item):
        """Aplica as recompensas e equipamentos dos itens iniciais coletados na Casa."""
        if id_do_item == "item_moedas":
            self.game.halia.ganhar_dinheiro(50 * self.game.halia.COBRES_POR_OURO)  # 50 Moedas de Ouro = 10.000 Cobres
            self.game.caixa_dialogo.iniciar_dialogo(
                [{"autor": "Sistema", "texto": "Você encontrou a Bolsa de Moedas com 50 moedas de ouro."}]
            )
        elif id_do_item == "item_cajado":
            cajado = ItemFactory.criar("cajado_espinheiro")
            if cajado:
                self.game.halia.inventario.equipados["CAJADO"] = cajado
            self.game.halia.recalcular_status_derivados()
            self.game.caixa_dialogo.iniciar_dialogo(
                [{"autor": "Sistema", "texto": "Você empunhou o Cajado de Espinheiro."}]
            )
        elif id_do_item == "item_livro":
            tomo = ItemFactory.criar("tomo_chama_ancestral")
            if tomo:
                self.game.halia.inventario.equipados["GRIMORIO_1"] = tomo
            self.game.caixa_dialogo.iniciar_dialogo(
                [{"autor": "Sistema", "texto": "Você recolheu o Livro Antigo contendo encantamentos arcanos esquecidos."}]
            )
        else:
            self.game.caixa_dialogo.iniciar_dialogo(
                [{"autor": "Sistema", "texto": f"Você guardou: {item.nome}."}]
            )

    def processar_interacao_cenario(self, area_interacao):
        """Processa interações na Casa, Carroceiro e pedras da Estrada 2; retorna True se consumiu."""
        if (
            self.game.mapa_casa.cenario_atual == "CASA"
            and area_interacao.colliderect(self.game.mapa_casa.porta)
            and not self.game.mapa_casa.porta_aberta
        ):
            if len(self.game.mapa_casa.itens_no_chao) == 0:
                self.game.mapa_casa.abrir_porta()
                self.game.caixa_dialogo.iniciar_dialogo("porta_abriu")
            else:
                self.game.caixa_dialogo.iniciar_dialogo("porta_trancada")
            return True

        if (
            self.game.mapa_casa.cenario_atual in ["ESTRADA", "ESTRADA_2"]
            and self.game.carroceiro_visivel
        ):
            if area_interacao.colliderect(
                pygame.Rect(
                    self.game.carroceiro.x,
                    self.game.carroceiro.y,
                    self.game.carroceiro.largura,
                    self.game.carroceiro.altura,
                )
            ):
                self.game.carroceiro.virado_direita = (self.game.halia.x > self.game.carroceiro.x)
                self.game.halia.virado_direita = (self.game.carroceiro.x > self.game.halia.x)
                if self.game.mapa_casa.cenario_atual == "ESTRADA":
                    self.game.caixa_dialogo.iniciar_dialogo("hub_carroceiro")
                elif self.game.mapa_casa.cenario_atual == "ESTRADA_2":
                    if getattr(self.game, "combate_estrada_concluido", False):
                        self.game.caixa_dialogo.iniciar_dialogo("carroceiro_pos_combate")
                    elif self.game.magia_ativa == "CONCLUIDO":
                        self.game.caixa_dialogo.iniciar_dialogo("carroceiro_pos_puzzle")
                    else:
                        self.game.caixa_dialogo.iniciar_dialogo("carroceiro_impedimento")
                return True

        if (
            self.game.mapa_casa.cenario_atual == "ESTRADA_2"
            and self.game.magia_ativa != "CONCLUIDO"
            and not getattr(self.game, "combate_estrada_concluido", False)
        ):
            if self.game.halia.x >= 950:
                self.game.investigou_pedras = True
                if self.game.flashback_magia_concluido:
                    self.game.caixa_dialogo.iniciar_dialogo("escolha_magias")
                else:
                    self.game.caixa_dialogo.iniciar_dialogo("investigar_pedras")
                return True

        return False

    def entrar_na_estrada_1(self):
        """Transiciona Halia da Casa para a Estrada 1."""
        self.game.mapa_casa.carregar_cenario("ESTRADA")
        self.game.halia.x, self.game.halia.y = 40, 330
        self.playing_state.atualizar_camera(instantaneo=True)
        if not getattr(self.game, "conversa_carroceiro_terminou", False):
            self.game.carroceiro_visivel = False
            self.game.carroceiro_andando = False
            self.game.carroceiro.x, self.game.carroceiro.y = 1350, 330
            self.game.carroceiro.velocidade = 2
            self.game.carroceiro.mudar_estado("idle")
        if self.game.slot_atual:
            self.game.salvar_estado(self.game.slot_atual, tipo="autosave")
        pygame.event.clear()
        self.game.caixa_dialogo.iniciar_dialogo("entrada_estrada1")
        self.game.transicao.estado = "CLAREANDO"

    def entrar_na_estrada_2(self):
        """Transiciona Halia da Estrada 1 para a Estrada 2 (bloqueio de pedras)."""
        if not (self.game.magia_ativa == "CONCLUIDO" or self.game.combate_estrada_concluido):
            self.game.mapa_casa.restaurar_bloqueio_estrada2()
        self.game.mapa_casa.carregar_cenario("ESTRADA_2")
        self.game.conversa_carroceiro_terminou = False
        self.game.aguardando_fim_viagem = False
        self.game.magia_ativa = None
        self.game.bola_fogo_ativa = False
        self.game.cena_inimigos_andando = False
        self.game.inimigos_em_cena.clear()

        self.game.halia.x, self.game.halia.y = 60, 330
        self.playing_state.atualizar_camera(instantaneo=True)
        self.game.carroceiro_visivel, self.game.carroceiro_andando = True, False
        self.game.carroceiro.velocidade, self.game.carroceiro.x, self.game.carroceiro.y = 0, 200, 330
        self.game.carroceiro.mudar_estado("idle")
        self.game.carroceiro.virado_direita = (self.game.halia.x > self.game.carroceiro.x)

        h_npc = pygame.Rect(
            int(self.game.carroceiro.x),
            int(self.game.carroceiro.y),
            self.game.carroceiro.largura,
            self.game.carroceiro.altura,
        )
        if h_npc not in self.game.mapa_casa.hitboxes:
            self.game.mapa_casa.hitboxes.append(h_npc)

        if self.game.slot_atual:
            self.game.salvar_estado(self.game.slot_atual, tipo="autosave")

        pygame.event.clear()
        self.game.caixa_dialogo.iniciar_dialogo("entrada_estrada2")
        self.game.transicao.estado = "CLAREANDO"

    def on_vitoria_combate_estrada(self):
        """Aplica as recompensas e progresso após vencer o combate na Estrada 2."""
        self.game.combate_estrada_concluido = True
        self.game.magia_ativa = "CONCLUIDO"
        self.game.mapa_casa.desobstruir_estrada(self.game.magia_usada_no_puzzle or "FOGO")
        teve_chefe = any(
            getattr(i, "eh_chefe", False) or "superior" in getattr(i, "nome", "").lower()
            for i in self.game.inimigos_em_cena
        )
        self.game.inimigos_em_cena.clear()
        self.game.cena_inimigos_andando = False
        if hasattr(self.game, "conquistas") and self.game.conquistas:
            self.game.conquistas.desbloquear("primeiro_sangue")
            if teve_chefe:
                self.game.conquistas.desbloquear("cacadora_abissal")
        self.game.mudar_estado("JOGANDO")
        self.game.caixa_dialogo.iniciar_dialogo("pos_combate_vitoria")

    def on_fuga_combate_estrada(self):
        """Recua Halia ao fugir do combate da Estrada 2."""
        self.game.halia.x = max(60, self.game.halia.x - 120)
        self.game.inimigos_em_cena.clear()

    def resetar_derrota_estrada_2(self):
        """Restaura o estado da Estrada 2 após derrota em combate."""
        self.game.combate_estrada_concluido = False
        self.game.inimigos_em_cena.clear()
        self.game.cena_inimigos_andando = False
        self.game.iniciando_combate = False
        self.game.halia.restaurar_total()
        self.game.magia_ativa = None
        self.game.investigou_pedras = False
        self.game.bola_fogo_ativa = False
        self.game.mapa_casa.restaurar_bloqueio_estrada2()

    def desenhar_prompts(self, tela, area_interacao, tecla_interacao_str, bloqueado_geral, desenhar_fn):
        """Desenha os indicadores de tecla para porta da Casa, Carroceiro e bloqueio da Estrada 2."""
        if not self.game.caixa_dialogo.ativo:
            if (
                self.game.mapa_casa.cenario_atual == "CASA"
                and area_interacao.colliderect(self.game.mapa_casa.porta)
                and not self.game.mapa_casa.porta_aberta
            ):
                desenhar_fn(
                    tela,
                    self.game.mapa_casa.porta.x + (self.game.mapa_casa.porta.width // 2),
                    self.game.mapa_casa.porta.y - 34,
                    tecla=tecla_interacao_str,
                    acao="para Abrir",
                )

        if (
            self.game.mapa_casa.cenario_atual in ["ESTRADA", "ESTRADA_2"]
            and self.game.carroceiro_visivel
        ):
            r_c = pygame.Rect(
                self.game.carroceiro.x,
                self.game.carroceiro.y,
                self.game.carroceiro.largura,
                self.game.carroceiro.altura,
            )
            if area_interacao.colliderect(r_c) and not bloqueado_geral:
                desenhar_fn(
                    tela,
                    self.game.carroceiro.x + (self.game.carroceiro.largura // 2),
                    self.game.carroceiro.y - 38,
                    tecla=tecla_interacao_str,
                    acao="para Conversar",
                )

        if (
            self.game.mapa_casa.cenario_atual == "ESTRADA_2"
            and self.game.magia_ativa != "CONCLUIDO"
            and not getattr(self.game, "combate_estrada_concluido", False)
        ):
            if self.game.halia.x >= 950 and not bloqueado_geral:
                txt_acao = "para Usar Magia" if self.game.flashback_magia_concluido else "para Investigar"
                desenhar_fn(tela, 1070, 200, tecla=tecla_interacao_str, acao=txt_acao)
