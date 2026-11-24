# src/states/menu_states.py
import pygame
from src.states.states import State

class MenuState(State):
    def __init__(self, game):
        super().__init__(game)
        self.hover_anterior = -1

    def _tocar_sfx(self, alias):
        if hasattr(self.game, 'audio') and self.game.audio:
            self.game.audio.tocar_sfx(alias)
        
    def handle_events(self, eventos, teclas):
        for evento in eventos:
            if evento.type == pygame.KEYDOWN:
                if evento.key in [pygame.K_UP, pygame.K_w]:
                    if self.game.menu.selecionada <= 0:
                        self.game.menu.selecionada = len(self.game.menu.opcoes) - 1
                    else:
                        self.game.menu.selecionada -= 1
                    self._tocar_sfx("ui_cursor")
                elif evento.key in [pygame.K_DOWN, pygame.K_s]:
                    if self.game.menu.selecionada == -1 or self.game.menu.selecionada >= len(self.game.menu.opcoes) - 1:
                        self.game.menu.selecionada = 0
                    else:
                        self.game.menu.selecionada += 1
                    self._tocar_sfx("ui_cursor")
                elif evento.key in [pygame.K_RETURN, pygame.K_SPACE]:
                    if self.game.menu.selecionada != -1:
                        self.executar_opcao()
                    
            elif evento.type == pygame.MOUSEMOTION:
                segredo = getattr(self.game.menu, "segredo_cheats", None)
                res_mov = segredo.processar_mouse_motion(evento.pos) if segredo else None
                if res_mov and res_mov.get("arrastando"):
                    self.game.menu.selecionada = -1
                else:
                    sel_ant = self.game.menu.selecionada
                    self.game.menu.atualizar_mouse(evento.pos)
                    if self.game.menu.selecionada != -1 and self.game.menu.selecionada != sel_ant:
                        self._tocar_sfx("ui_cursor")
                    elif res_mov and res_mov.get("hover_botao_entrou"):
                        self._tocar_sfx("ui_cursor")

            elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                opcao = self.game.menu.clicar_mouse(evento.pos)
                if opcao:
                    self.executar_opcao(opcao)
                else:
                    segredo = getattr(self.game.menu, "segredo_cheats", None)
                    if segredo:
                        self._tratar_evento_segredo_menu(segredo.processar_mouse_down(evento.pos))

            elif evento.type == pygame.MOUSEBUTTONUP and evento.button == 1:
                segredo = getattr(self.game.menu, "segredo_cheats", None)
                if segredo:
                    self._tratar_evento_segredo_menu(segredo.processar_mouse_up(evento.pos))

    def _tratar_evento_segredo_menu(self, resultado):
        if not resultado:
            return
        evento = resultado.get("evento")
        audio = getattr(self.game, "audio", None)
        if evento == "folha_coletada":
            if audio:
                audio.tocar_sfx("ui_aceitar", volume_extra=0.55)
        elif evento == "versao_liberada":
            if audio:
                audio.tocar_sfx("memoria_despertar", volume_extra=0.50)
        elif evento == "botao_revelado":
            if audio:
                audio.tocar_sfx("ui_clique_pedra", volume_extra=0.75)
        elif evento == "ativar_cheats":
            if hasattr(self.game, "habilitar_comandos_dev") and self.game.habilitar_comandos_dev():
                if audio:
                    audio.tocar_sfx("memoria_despertar", volume_extra=0.65)
                conquistas = getattr(self.game, "conquistas", None)
                if conquistas:
                    conquistas.desbloquear("segredo_menu_cheats")
                notif = getattr(self.game, "notificacoes", None)
                if notif:
                    notif.notificar(
                        "notificacao_alerta",
                        titulo="Cheats Liberados",
                        mensagem="Console DEV ativado! Pressione ['] ou [`] a qualquer momento.",
                        tipo="INFO",
                    )
        elif evento == "abrir_cheats":
            if hasattr(self.game, "habilitar_comandos_dev") and self.game.habilitar_comandos_dev():
                if getattr(self.game, "dev_commands", None):
                    self.game.dev_commands.ativo = True
                    self._tocar_sfx("ui_confirmar")

    def executar_opcao(self, opcao_clicada=None):
        if opcao_clicada is not None:
            opcao = opcao_clicada
        elif 0 <= self.game.menu.selecionada < len(self.game.menu.opcoes):
            opcao = self.game.menu.opcoes[self.game.menu.selecionada]
        else:
            return
            
        self._tocar_sfx("ui_confirmar")
        
        if opcao == "Continuar":
            self.game.acao_slots = "CARREGAR"
            self.game.origem_slots = "MENU"
            self.game.mudar_estado("SLOTS")
            
        elif opcao == "Novo Jogo" or opcao == "Jogar":
            # Apresenta a seleção de esquema de controles (WASD ou Setinhas) antes de iniciar
            self.game.mudar_estado("SELECAO_CONTROLES")
            
        elif opcao == "Conquistas":
            self.game.origem_conquistas = "MENU"
            self.game.mudar_estado("CONQUISTAS")
            
        elif opcao == "Configurações":
            self.game.origem_configuracoes = "MENU"
            self.game.mudar_estado("CONFIGURACOES")
            
        elif opcao == "Créditos":
            self.game.origem_creditos = "MENU"
            cred = self.game.estados.get("CREDITOS") if hasattr(self.game, "estados") else None
            if cred and hasattr(cred, "iniciar_modo_menu"):
                cred.iniciar_modo_menu()
            self.game.mudar_estado("CREDITOS")
            
        elif opcao == "Sair":
            self.game.running = False

    def update(self):
        dt = self.game.clock.get_time() / 1000.0 if hasattr(self.game, 'clock') else 0.016
        # Limita dt para evitar saltos bruscos em pausas de sistema
        dt = min(dt, 0.05) if dt > 0 else 0.016
        self.game.menu.atualizar(dt)
            
    def draw(self, tela):
        self.game.menu.desenhar(tela)