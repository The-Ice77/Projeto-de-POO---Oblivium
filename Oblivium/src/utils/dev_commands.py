# src/utils/dev_commands.py
import pygame


class ComandosDev:
    """
    Console Secreto de Comandos de Desenvolvedor (Dev Commands).
    Permite ativar e desativar recursos em tempo real de execução para testes rápidos.
    
    Ativação:
    - Tecla de Aspas simples ou Crase (' / ` / ~)
    
    Ações Rápidas via Teclado Numérico:
    [1] - Desativar / Ativar Filtro Monocromático de Memória (Exibir 100% das Cores)
    [2] - Pular Cutscene / Encerrar Diálogos e Transições Imediatamente
    [3] - Teleporte de Mapas (CASA -> ESTRADA -> ESTRADA_2)
    [4] - Restaurar Vida e Mana ao Máximo
    [5] - Adicionar +1000 Moedas ao Inventário
    [6] - Despertar Pleno: 7 Memórias e todas as Magias do Grimório
    [7] - Desobstruir Estrada 2 (Remover pedras do caminho)
    [8] - Forçar Encontro de Combate Imediato
    """

    def __init__(self, game):
        self.game = game
        self.ativo = False
        self.fonte_titulo = pygame.font.Font(None, 24)
        self.fonte_opcoes = pygame.font.Font(None, 20)

    def alternar_ativacao(self):
        """Alterna a visibilidade e captura do modo desenvolvedor."""
        self.ativo = not self.ativo
        status = "ATIVADOS" if self.ativo else "DESATIVADOS"
        self._notificar(f"Modo Dev: {status}", icone="⚙️")

    def processar_evento(self, evento):
        """Escuta a tecla de ativação e os numerais quando o modo dev está ativo."""
        if evento.type != pygame.KEYDOWN:
            return False

        # Tecla de aspas simples (') ou crase (`)
        if evento.key in [pygame.K_BACKQUOTE, pygame.K_QUOTE]:
            self.alternar_ativacao()
            return True

        if not self.ativo:
            return False

        # Comandos via teclado numérico ou fileira superior de números
        if evento.key in [pygame.K_1, pygame.K_KP1]:
            self.cmd_alternar_filtro_cor()
            return True
        elif evento.key in [pygame.K_2, pygame.K_KP2]:
            self.cmd_pular_cutscenes()
            return True
        elif evento.key in [pygame.K_3, pygame.K_KP3]:
            self.cmd_mudar_mapa()
            return True
        elif evento.key in [pygame.K_4, pygame.K_KP4]:
            self.cmd_curar_total()
            return True
        elif evento.key in [pygame.K_5, pygame.K_KP5]:
            self.cmd_adicionar_moedas()
            return True
        elif evento.key in [pygame.K_6, pygame.K_KP6]:
            self.cmd_desbloquear_grimorio()
            return True
        elif evento.key in [pygame.K_7, pygame.K_KP7]:
            self.cmd_desobstruir_estrada()
            return True
        elif evento.key in [pygame.K_8, pygame.K_KP8]:
            self.cmd_iniciar_combate()
            return True

        return False

    # =========================================================================
    # AÇÕES DO DEV
    # =========================================================================
    def cmd_alternar_filtro_cor(self):
        """Liga ou desliga o filtro de escala de cinza para ver as artes 100% coloridas."""
        if hasattr(self.game, 'filtro_memoria') and self.game.filtro_memoria:
            atual = getattr(self.game.filtro_memoria, 'desativado', False)
            self.game.filtro_memoria.desativado = not atual
            msg = "Filtro P&B: DESATIVADO (Cores 100%)" if not atual else "Filtro P&B: ATIVADO"
            self._notificar(msg, icone="🎨")

    def cmd_pular_cutscenes(self):
        """Pula diálogos, cutscenes de transição, tela de despertar e animações ativas."""
        # 1. Fecha diálogos
        if hasattr(self.game, 'caixa_dialogo'):
            self.game.caixa_dialogo.ativo = False
            self.game.caixa_dialogo.texto_completo = ""

        # 2. Pula tela de despertar
        if hasattr(self.game, 'tela_despertar'):
            self.game.tela_despertar.reiniciar()

        # 3. Pula transições
        if hasattr(self.game, 'transicao'):
            self.game.transicao.estado = "INATIVO"

        # 4. Cancela flags de espera
        self.game.fechando_porta = False
        self.game.aguardando_fim_viagem = False
        self.game.investigou_pedras = True
        self.game.cena_inimigos_andando = False
        self.game.conversa_combate_ativa = False
        self.game.magia_ativa = None
        self.game.mg_timing.ativo = False
        self.game.mg_mash.ativo = False

        self._notificar("Cutscene e Diálogos Pulados!", icone="⏩")

    def cmd_mudar_mapa(self):
        """Alterna ciclicamente entre CASA, ESTRADA e ESTRADA_2."""
        mapas_ciclo = ["CASA", "ESTRADA", "ESTRADA_2"]
        cenario_atual = self.game.mapa_casa.cenario_atual
        idx = (mapas_ciclo.index(cenario_atual) + 1) % len(mapas_ciclo) if cenario_atual in mapas_ciclo else 0
        novo_mapa = mapas_ciclo[idx]

        self.game.mapa_casa.carregar_cenario(novo_mapa)

        # Reposiciona Halia com segurança
        if novo_mapa == "CASA":
            self.game.halia.x = 210
            self.game.halia.y = 280
        elif novo_mapa == "ESTRADA":
            self.game.halia.x = 100
            self.game.halia.y = 350
        elif novo_mapa == "ESTRADA_2":
            self.game.halia.x = 100
            self.game.halia.y = 350

        self._notificar(f"Teleporte para {novo_mapa}", icone="🗺️")

    def cmd_curar_total(self):
        """Restaura Vida e Mana totais da Halia."""
        self.game.halia.vida_atual = self.game.halia.vida_maxima
        self.game.halia.mana_atual = self.game.halia.mana_maxima
        self._notificar("Halia 100% Curada (HP & Mana Max)", icone="💖")

    def cmd_adicionar_moedas(self):
        """Adiciona 1000 moedas ao inventário."""
        self.game.halia.dinheiro += 1000
        self._notificar("+1000 Moedas Concedidas!", icone="🪙")

    def cmd_desbloquear_grimorio(self):
        """Desbloqueia as 7 memórias e todas as magias."""
        self.game.halia.fragmentos_memoria = 7
        self.game.halia.atualizar_grimorio()
        if hasattr(self.game, 'filtro_memoria'):
            self.game.filtro_memoria.definir_estagio(7, com_transicao_suave=True)
        self._notificar("7 Memórias & Grimório Supremo Desbloqueados!", icone="📖")

    def cmd_desobstruir_estrada(self):
        """Desobstrui o deslizamento na Estrada 2."""
        self.game.mapa_casa.desobstruir_estrada("FOGO")
        self._notificar("Deslizamento da Estrada 2 Desobstruído!", icone="💥")

    def cmd_iniciar_combate(self):
        """Dispara a transição para a tela de combate com um inimigo de teste."""
        if hasattr(self.game, 'iniciar_combate'):
            self.game.iniciar_combate()
            self._notificar("Combate Forçado!", icone="⚔️")

    def _notificar(self, texto, icone="⚙️"):
        if hasattr(self.game, 'notificacoes') and self.game.notificacoes:
            try:
                self.game.notificacoes.notificar("Comandos Dev", texto, tipo="SISTEMA", icone=icone)
            except Exception:
                pass

    # =========================================================================
    # RENDERIZAÇÃO DO OVERLAY
    # =========================================================================
    def desenhar(self, tela):
        """Renderiza a barra superior com os comandos do desenvolvedor."""
        if not self.ativo:
            return

        w, h = self.game.LARGURA, 60
        painel = pygame.Surface((w, h), pygame.SRCALPHA)
        painel.fill((16, 16, 20, 235))
        pygame.draw.line(painel, (220, 180, 60), (0, h - 2), (w, h - 2), 2)

        # Cabeçalho
        txt_header = self.fonte_titulo.render("⚙️ MODO DESENVOLVEDOR ATIVO (Pressione ' para fechar)", True, (240, 210, 100))
        painel.blit(txt_header, (16, 8))

        # Atalhos
        linha_comandos = (
            "[1] Cores On/Off   [2] Pular Cutscene   [3] Mudar Mapa   "
            "[4] Curar Full   [5] +1000$   [6] Desbloquear Grimório   "
            "[7] Desobstruir   [8] Combate"
        )
        txt_atalhos = self.fonte_opcoes.render(linha_comandos, True, (210, 215, 225))
        painel.blit(txt_atalhos, (16, 34))

        tela.blit(painel, (0, 0))
