# src/utils/dev_commands.py
import pygame
import os
import sys

_raiz_projeto = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _raiz_projeto not in sys.path:
    sys.path.insert(0, _raiz_projeto)

from src.utils.colors import (
    CARVAO_PROFUNDO, CINZA_LINHO, CINZA_ARDOSIA, MARFIM_OFFWHITE,
    DOURADO_ENVELHECIDO, AZUL_HOVER_MENU, AZUL_HOVER_BG, UI_TEXTO_APAGADO,
    BOTAO_FECHAR_HOVER, BRANCO
)
from src.utils.resource_manager import ResourceManager
from src.ui.ui_utils import desenhar_painel_padrao


class ComandosDev:
    """
    Console de Comandos de Desenvolvedor (Dev Commands) de Oblivium.
    Alinhado estritamente à identidade visual Dark Fantasy / Metroidvania do jogo:
    - Painel modal centralizado com moldura em Carvão Profundo e bordas em Cinza Linho
    - Tipografia consolidada (Sunday para títulos e teclas, Contrail One para comandos e dados)
    - Caixas de opções amplas e proporcionais com badges de atalho e chips de status em tempo real
    - Suporte híbrido completo: Teclado (1-8, Numpad, ESC, aspas/crase) e Mouse (hover/cliques)
    
    Ativação: Tecla de Aspas simples ou Crase (' / ` / ~)
    """

    def __init__(self, game):
        self.game = game
        self.ativo = False
        self.hover_indice = None
        self.hover_fechar = False
        self.rects_botoes = []
        self.rect_fechar = pygame.Rect(0, 0, 0, 0)

        # Tipografia consolidada oficial do jogo
        self.fonte_titulo = ResourceManager.carregar_fonte("sunday", 26)
        self.fonte_subtitulo = ResourceManager.carregar_fonte("contrail", 14)
        self.fonte_tecla = ResourceManager.carregar_fonte("sunday", 20)
        self.fonte_nome = ResourceManager.carregar_fonte("contrail", 18)
        self.fonte_detalhe = ResourceManager.carregar_fonte("contrail", 13)
        self.fonte_chip = ResourceManager.carregar_fonte("contrail", 12)
        self.fonte_rodape = ResourceManager.carregar_fonte("contrail", 14)

        # Película escura de fundo para focar a atenção no painel
        self.overlay = pygame.Surface((self.game.LARGURA, self.game.ALTURA))
        self.overlay.fill((10, 10, 14))
        self.overlay.set_alpha(175)

    def alternar_ativacao(self):
        """Alterna a visibilidade do painel de desenvolvedor."""
        self.ativo = not self.ativo
        status = "ATIVADO" if self.ativo else "DESATIVADO"
        self._notificar("Modo Desenvolvedor", f"Painel de testes {status}", icone="◈")

    def processar_evento(self, evento):
        """Processa a tecla de ativação, atalhos de teclado e interações do mouse."""
        # 1. Ativação via teclado (aspas simples ou crase)
        if evento.type == pygame.KEYDOWN and evento.key in [pygame.K_BACKQUOTE, pygame.K_QUOTE]:
            self.alternar_ativacao()
            return True

        if not self.ativo:
            return False

        # 2. Interação com o Mouse
        if evento.type == pygame.MOUSEMOTION:
            pos = evento.pos
            self.hover_fechar = self.rect_fechar.collidepoint(pos)
            self.hover_indice = None
            for i, rect in enumerate(self.rects_botoes):
                if rect.collidepoint(pos):
                    self.hover_indice = i
                    break
            return True

        elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            pos = evento.pos
            if self.rect_fechar.collidepoint(pos):
                self.alternar_ativacao()
                return True
            for i, rect in enumerate(self.rects_botoes):
                if rect.collidepoint(pos):
                    self._executar_por_indice(i + 1)
                    return True
            return True

        # 3. Comandos via Teclado Numérico ou Fileira Superior de Números
        if evento.type == pygame.KEYDOWN:
            mapeamento = {
                pygame.K_1: 1, pygame.K_KP1: 1,
                pygame.K_2: 2, pygame.K_KP2: 2,
                pygame.K_3: 3, pygame.K_KP3: 3,
                pygame.K_4: 4, pygame.K_KP4: 4,
                pygame.K_5: 5, pygame.K_KP5: 5,
                pygame.K_6: 6, pygame.K_KP6: 6,
                pygame.K_7: 7, pygame.K_KP7: 7,
                pygame.K_8: 8, pygame.K_KP8: 8,
            }
            if evento.key in mapeamento:
                self._executar_por_indice(mapeamento[evento.key])
                return True
            elif evento.key == pygame.K_ESCAPE:
                self.alternar_ativacao()
                return True

        return False

    def _executar_por_indice(self, indice):
        """Executa a ação correspondente ao índice selecionado."""
        acoes = {
            1: self.cmd_alternar_filtro_cor,
            2: self.cmd_pular_cutscenes,
            3: self.cmd_mudar_mapa,
            4: self.cmd_curar_total,
            5: self.cmd_adicionar_moedas,
            6: self.cmd_desbloquear_grimorio,
            7: self.cmd_desobstruir_estrada,
            8: self.cmd_iniciar_combate
        }
        if indice in acoes:
            acoes[indice]()

    # =========================================================================
    # AÇÕES DO DEV (TESTADAS E BLINDADAS)
    # =========================================================================
    def cmd_alternar_filtro_cor(self):
        """Liga ou desliga o filtro de escala de cinza para ver as artes 100% coloridas."""
        if hasattr(self.game, 'filtro_memoria') and self.game.filtro_memoria:
            atual = getattr(self.game.filtro_memoria, 'desativado', False)
            self.game.filtro_memoria.desativado = not atual
            msg = "Filtro P&B desativado (Cores 100%)" if not atual else "Filtro P&B reativado"
            self._notificar("Filtro de Memória", msg, icone="✦")

    def cmd_pular_cutscenes(self):
        """Pula diálogos, cutscenes de transição, tela de despertar e animações ativas."""
        if hasattr(self.game, 'caixa_dialogo'):
            self.game.caixa_dialogo.ativo = False
            self.game.caixa_dialogo.texto_completo = ""

        if hasattr(self.game, 'tela_despertar'):
            self.game.tela_despertar.reiniciar()

        if hasattr(self.game, 'transicao'):
            self.game.transicao.estado = "INATIVO"

        self.game.fechando_porta = False
        self.game.aguardando_fim_viagem = False
        self.game.investigou_pedras = True
        self.game.cena_inimigos_andando = False
        self.game.conversa_combate_ativa = False
        self.game.distanciando_halia = False
        self.game.bola_fogo_ativa = False
        self.game.iniciando_combate = False
        self.game.magia_ativa = None
        self.game.mg_timing.ativo = False
        self.game.mg_mash.ativo = False

        if hasattr(self.game, 'halia'):
            self.game.halia.mudar_estado("idle")

        self._notificar("Cutscenes", "Diálogos e bloqueios pulados com sucesso!", icone="✦")

    def cmd_mudar_mapa(self):
        """Alterna ciclicamente entre CASA, ESTRADA e ESTRADA_2."""
        mapas_ciclo = ["CASA", "ESTRADA", "ESTRADA_2"]
        cenario_atual = getattr(getattr(self.game, 'mapa_casa', None), 'cenario_atual', "CASA")
        idx = (mapas_ciclo.index(cenario_atual) + 1) % len(mapas_ciclo) if cenario_atual in mapas_ciclo else 0
        novo_mapa = mapas_ciclo[idx]

        self.game.mudar_estado("JOGANDO")
        self.game.mapa_casa.carregar_cenario(novo_mapa)

        if novo_mapa == "CASA":
            self.game.halia.x, self.game.halia.y = 210, 280
        elif novo_mapa == "ESTRADA":
            self.game.halia.x, self.game.halia.y = 100, 350
            self.game.carroceiro_visivel = True
            self.game.carroceiro.x, self.game.carroceiro.y = 900, 330
        elif novo_mapa == "ESTRADA_2":
            self.game.halia.x, self.game.halia.y = 100, 350
            self.game.carroceiro_visivel = True
            self.game.carroceiro.x, self.game.carroceiro.y = 200, 330

        self.game.inimigos_em_cena.clear()
        self.game.cena_inimigos_andando = False
        self.game.iniciando_combate = False
        self.game.conversa_combate_ativa = False
        self.game.halia.mudar_estado("idle")
        self._notificar("Teleporte de Mapa", f"Cenário alterado para {novo_mapa}", icone="◈")

    def cmd_curar_total(self):
        """Restaura Vida e Mana totais da Halia."""
        if hasattr(self.game, 'halia'):
            self.game.halia.vida_atual = self.game.halia.vida_maxima
            self.game.halia.mana_atual = self.game.halia.mana_maxima
            self.game.halia.vivo = True
            self.game.halia.condicoes.clear()
            self.game.halia.defendendo = False
            self.game.halia.vulneravel = False
            self.game.halia.focado = False
        self._notificar("Restauração", "Vida e Mana restauradas ao máximo!", icone="✦")

    def cmd_adicionar_moedas(self):
        """Adiciona 1000 moedas ao inventário."""
        if hasattr(self.game, 'halia'):
            self.game.halia.dinheiro += 1000
        self._notificar("Tesouro Dev", "+1000 Moedas adicionadas à bolsa!", icone="✦")

    def cmd_desbloquear_grimorio(self):
        """Alterna entre 7 memórias (pleno despertar) e 0 memórias (estado inicial)."""
        if hasattr(self.game, 'halia'):
            if self.game.halia.fragmentos_memoria < 7:
                self.game.halia.fragmentos_memoria = 7
                msg = "7 Memórias e Grimório completo desbloqueados!"
            else:
                self.game.halia.fragmentos_memoria = 0
                msg = "Memórias resetadas para o estado inicial (0/7)."

            self.game.halia.atualizar_grimorio()
            if hasattr(self.game, 'filtro_memoria'):
                self.game.filtro_memoria.definir_estagio(self.game.halia.fragmentos_memoria, com_transicao_suave=True)
            self._notificar("Despertar de Memórias", msg, icone="◈")

    def cmd_desobstruir_estrada(self):
        """Alterna entre desobstruir e restaurar o bloqueio na Estrada 2."""
        mapa2 = self.game.mapa_casa.cenarios.get("ESTRADA_2")
        bloqueado = getattr(mapa2, 'bloqueio_ativo', True)
        if bloqueado:
            self.game.mapa_casa.desobstruir_estrada("FOGO")
            self.game.magia_ativa = "CONCLUIDO"
            self._notificar("Estrada 2", "Deslizamento de pedras removido do caminho!", icone="✦")
        else:
            self.game.mapa_casa.restaurar_bloqueio_estrada2()
            self.game.magia_ativa = None
            self.game.investigou_pedras = False
            self._notificar("Estrada 2", "Rochas de bloqueio restauradas!", icone="✦")

    def cmd_iniciar_combate(self):
        """Dispara a transição para a tela de combate com um inimigo de teste."""
        from src.entities.enemy_factory import EnemyFactory
        inimigo_teste = EnemyFactory.criar("demonio_inferior", x=900, y=360, nome_custom="Demônio de Treino")

        def on_vitoria():
            self.game.mudar_estado("JOGANDO")
            self._notificar("Vitória Dev", "Combate de teste vencido!", icone="✦")

        def on_derrota():
            self.game.halia.restaurar_total()
            self.game.mudar_estado("JOGANDO")
            self._notificar("Fim de Combate", "Halia restaurada após teste.", icone="✦")

        def on_fuga():
            self.game.mudar_estado("JOGANDO")
            self._notificar("Fuga Dev", "Combate encerrado.", icone="✦")

        self.ativo = False  # Fecha o painel dev para abrir a arena limpa
        self.game.iniciar_combate([inimigo_teste], on_vitoria=on_vitoria, on_derrota=on_derrota, on_fuga=on_fuga)
        self._notificar("Arena de Batalha", "Iniciando combate de teste com Demônio Inferior...", icone="⚔")

    def _notificar(self, titulo, mensagem, icone="◈"):
        if hasattr(self.game, 'notificacoes') and self.game.notificacoes:
            try:
                self.game.notificacoes.notificar(titulo, mensagem, tipo="SISTEMA", icone=icone)
            except Exception:
                pass

    # =========================================================================
    # RENDERIZAÇÃO DO PAINEL (Identidade Visual Dark Fantasy / Metroidvania)
    # =========================================================================
    def _obter_dados_comandos(self):
        """Retorna as informações dinâmicas atualizadas de cada botão."""
        filtro_desat = getattr(getattr(self.game, 'filtro_memoria', None), 'desativado', False)
        status_cor = "100% Cores" if filtro_desat else "Escala Cinza"
        cenario = getattr(getattr(self.game, 'mapa_casa', None), 'cenario_atual', 'CASA')
        mems = getattr(getattr(self.game, 'halia', None), 'fragmentos_memoria', 0)
        hp_atual = int(getattr(getattr(self.game, 'halia', None), 'vida_atual', 100))
        ouro = getattr(getattr(self.game, 'halia', None), 'dinheiro', 0)

        mapa2 = getattr(getattr(self.game, 'mapa_casa', None), 'cenarios', {}).get("ESTRADA_2", None)
        bloqueado = getattr(mapa2, 'bloqueio_ativo', True)
        status_estrada = "Bloqueado" if bloqueado else "Livre"

        return [
            ("1", "Filtro de Memória", "Alternar cores e P&B", status_cor),
            ("2", "Pular Cutscenes", "Avançar diálogos e transições", "Avanço Rápido"),
            ("3", "Teleporte de Mapa", "Alternar entre Casa, Estrada 1 e 2", cenario),
            ("4", "Curar Halia Total", "Restaurar HP e Mana ao máximo", f"HP {hp_atual}"),
            ("5", "Tesouro Dev (+1000)", "Adicionar ouro à bolsa de Halia", f"{ouro} Ouro"),
            ("6", "Despertar Memórias", "Desbloquear ou resetar Grimório", f"{mems}/7 Mems"),
            ("7", "Bloqueio Estrada 2", "Remover ou repor rochas de obstrução", status_estrada),
            ("8", "Forçar Batalha", "Iniciar arena contra Demônio", "Arena Demo")
        ]

    def desenhar(self, tela):
        """Renderiza o console com o mesmo padrão estético e sofisticado de todo o jogo."""
        if not self.ativo:
            return

        # 1. Película escura translúcida de fundo
        tela.blit(self.overlay, (0, 0))

        largura_painel = 880
        altura_painel = 490
        x = (self.game.LARGURA - largura_painel) // 2
        y = (self.game.ALTURA - altura_painel) // 2

        rect_painel = pygame.Rect(x, y, largura_painel, altura_painel)

        # 2. Painel Principal com o padrão visual do jogo (Carvão Profundo + Cinza Linho)
        desenhar_painel_padrao(tela, rect_painel, cor_fundo=CARVAO_PROFUNDO, cor_borda=CINZA_LINHO, alpha=248)

        # Moldura interna decorativa
        rect_interno = rect_painel.inflate(-10, -10)
        pygame.draw.rect(tela, (28, 28, 34), rect_interno, 1, border_radius=2)

        # 3. Cabeçalho do Painel
        txt_titulo = self.fonte_titulo.render("Comandos de Desenvolvedor", True, MARFIM_OFFWHITE)
        tela.blit(txt_titulo, (x + 36, y + 22))

        txt_sub = self.fonte_subtitulo.render("Atalhos rápidos para testes, depuração e inspeção", True, UI_TEXTO_APAGADO)
        tela.blit(txt_sub, (x + 38 + txt_titulo.get_width() + 18, y + 30))

        # Botão Fechar [ X ] no topo direito
        self.rect_fechar = pygame.Rect(x + largura_painel - 44, y + 20, 24, 24)
        cor_bg_fechar = BOTAO_FECHAR_HOVER if self.hover_fechar else (26, 26, 32)
        cor_bd_fechar = AZUL_HOVER_MENU if self.hover_fechar else CINZA_ARDOSIA
        pygame.draw.rect(tela, cor_bg_fechar, self.rect_fechar, border_radius=2)
        pygame.draw.rect(tela, cor_bd_fechar, self.rect_fechar, 1, border_radius=2)
        txt_x = self.fonte_subtitulo.render("✕", True, BRANCO if self.hover_fechar else CINZA_LINHO)
        tela.blit(txt_x, txt_x.get_rect(center=self.rect_fechar.center))

        # Divisória elegante sob o cabeçalho
        pygame.draw.line(tela, CINZA_ARDOSIA, (x + 34, y + 64), (x + largura_painel - 34, y + 64), 1)

        # 4. Grade de Caixas de Comando (2 Colunas x 4 Linhas)
        self.rects_botoes.clear()
        dados_comandos = self._obter_dados_comandos()

        cols = 2
        espaco_x = 18
        espaco_y = 12
        larg_card = (largura_painel - 72 - espaco_x) // cols
        alt_card = 72
        y_grade_inicio = y + 78

        for i, (tecla, nome, detalhe, status_chip) in enumerate(dados_comandos):
            c = i % cols
            r = i // cols
            card_x = x + 36 + c * (larg_card + espaco_x)
            card_y = y_grade_inicio + r * (alt_card + espaco_y)

            card_rect = pygame.Rect(card_x, card_y, larg_card, alt_card)
            self.rects_botoes.append(card_rect)

            esta_hover = (self.hover_indice == i)
            cor_bg = AZUL_HOVER_BG if esta_hover else (20, 20, 26)
            cor_bd = AZUL_HOVER_MENU if esta_hover else CINZA_ARDOSIA

            # Fundo e contorno do card
            pygame.draw.rect(tela, cor_bg, card_rect, border_radius=2)
            pygame.draw.rect(tela, cor_bd, card_rect, 1, border_radius=2)

            # Badge da Tecla Numérica à esquerda
            badge_dim = 42
            badge_rect = pygame.Rect(card_x + 14, card_y + (alt_card - badge_dim) // 2, badge_dim, badge_dim)
            cor_bg_badge = (34, 38, 52) if esta_hover else (14, 14, 18)
            cor_bd_badge = DOURADO_ENVELHECIDO if esta_hover else (45, 45, 55)
            pygame.draw.rect(tela, cor_bg_badge, badge_rect, border_radius=2)
            pygame.draw.rect(tela, cor_bd_badge, badge_rect, 1, border_radius=2)

            txt_tecla = self.fonte_tecla.render(tecla, True, DOURADO_ENVELHECIDO if esta_hover else MARFIM_OFFWHITE)
            tela.blit(txt_tecla, txt_tecla.get_rect(center=badge_rect.center))

            # Nome e Descrição da Ação
            x_conteudo = badge_rect.right + 14
            cor_nome = MARFIM_OFFWHITE if esta_hover else CINZA_LINHO
            txt_nome = self.fonte_nome.render(nome, True, cor_nome)
            tela.blit(txt_nome, (x_conteudo, card_y + 14))

            cor_detalhe = (165, 205, 245) if esta_hover else UI_TEXTO_APAGADO
            txt_detalhe = self.fonte_detalhe.render(detalhe, True, cor_detalhe)
            tela.blit(txt_detalhe, (x_conteudo, card_y + 40))

            # Chip de Status em tempo real no canto direito da caixa
            render_chip = self.fonte_chip.render(status_chip, True, DOURADO_ENVELHECIDO if esta_hover else CINZA_LINHO)
            w_chip = render_chip.get_width() + 14
            h_chip = 22
            rect_chip = pygame.Rect(card_rect.right - w_chip - 12, card_y + 14, w_chip, h_chip)
            cor_bg_chip = (28, 38, 55) if esta_hover else (14, 14, 18)
            cor_bd_chip = AZUL_HOVER_MENU if esta_hover else (40, 40, 50)
            pygame.draw.rect(tela, cor_bg_chip, rect_chip, border_radius=2)
            pygame.draw.rect(tela, cor_bd_chip, rect_chip, 1, border_radius=2)
            tela.blit(render_chip, render_chip.get_rect(center=rect_chip.center))

        # 5. Rodapé com instruções de navegação
        y_rodape = y + altura_painel - 36
        pygame.draw.line(tela, CINZA_ARDOSIA, (x + 34, y_rodape - 10), (x + largura_painel - 34, y_rodape - 10), 1)

        txt_rodape = self.fonte_rodape.render("[ ' ] Fechar Console   •   [ 1 - 8 ] Executar Atalho   •   [ Mouse ] Clicar na Opção", True, UI_TEXTO_APAGADO)
        tela.blit(txt_rodape, (x + (largura_painel - txt_rodape.get_width()) // 2, y_rodape))
