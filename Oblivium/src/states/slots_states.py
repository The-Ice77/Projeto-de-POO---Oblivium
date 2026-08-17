# src/states/slots_states.py
import pygame
from src.states.states import State
from src.utils.colors import PRETO, BRANCO, UI_FUNDO_PADRAO, CINZA_CLARO, UI_TEXTO_DESTAQUE, UI_TEXTO_APAGADO, TXT_SISTEMA_NARRADOR
from src.utils import save_manager

class SlotsState(State):
    def __init__(self, game):
        super().__init__(game)
        self.opcoes = ["Slot 1", "Slot 2", "Slot 3", "Voltar"]
        self.selecionada = 0
        
        self.slot_confirmacao = None 
        self.opcao_confirmacao = 1 # 0: Sim, 1: Não
        
        self.fonte_titulo = pygame.font.Font(None, 60)
        self.fonte_opcao = pygame.font.Font(None, 40)
        self.fonte_status = pygame.font.Font(None, 24)
        
        self.rects_opcoes = []
        self.rects_deletar = [] 
        self.rects_confirma = []
        
        self.overlay = pygame.Surface((self.game.LARGURA, self.game.ALTURA))
        self.overlay.fill(PRETO)
        self.overlay.set_alpha(180)

    def handle_events(self, eventos, teclas):
        for evento in eventos:
            if self.slot_confirmacao is not None:
                if evento.type == pygame.KEYDOWN:
                    if evento.key == pygame.K_LEFT:
                        self.opcao_confirmacao = 0
                    elif evento.key == pygame.K_RIGHT:
                        self.opcao_confirmacao = 1
                    elif evento.key == pygame.K_RETURN:
                        if self.opcao_confirmacao == 0: 
                            save_manager.apagar_dados(self.slot_confirmacao)
                            if hasattr(self.game, 'menu'):
                                self.game.menu.atualizar_opcoes()
                        self.slot_confirmacao = None
                    elif evento.key == pygame.K_ESCAPE:
                        self.slot_confirmacao = None
                elif evento.type == pygame.MOUSEMOTION:
                    for i, rect in enumerate(self.rects_confirma):
                        if rect.collidepoint(evento.pos):
                            self.opcao_confirmacao = i
                elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                    for i, rect in enumerate(self.rects_confirma):
                        if rect.collidepoint(evento.pos):
                            if i == 0:
                                save_manager.apagar_dados(self.slot_confirmacao)
                                if hasattr(self.game, 'menu'):
                                    self.game.menu.atualizar_opcoes()
                            self.slot_confirmacao = None
                return 
                
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_UP:
                    self.selecionada = (self.selecionada - 1) % len(self.opcoes)
                elif evento.key == pygame.K_DOWN:
                    self.selecionada = (self.selecionada + 1) % len(self.opcoes)
                elif evento.key == pygame.K_RETURN:
                    self.executar_opcao()
                elif evento.key == pygame.K_ESCAPE:
                    self.voltar_origem()
                    
            elif evento.type == pygame.MOUSEMOTION:
                for i, rect in enumerate(self.rects_opcoes):
                    if rect and rect.collidepoint(evento.pos):
                        self.selecionada = i
                        
            elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                for i, rect_del in enumerate(self.rects_deletar):
                    if rect_del and rect_del.collidepoint(evento.pos):
                        self.slot_confirmacao = i + 1
                        self.opcao_confirmacao = 1 
                        return 
                
                for i, rect in enumerate(self.rects_opcoes):
                    if rect and rect.collidepoint(evento.pos):
                        self.selecionada = i
                        self.executar_opcao()

    def _mostrar_feedback_sincrono(self, texto):
        """Desenha a tela congelada com o jogo ao fundo e exibe o aviso de loading."""
        # Se veio do Pause, desenha o PlayingState limpo por baixo para manter a imersão
        if self.game.origem_slots == "PAUSE" and "JOGANDO" in self.game.estados:
            self.game.estados["JOGANDO"].draw(self.game.tela)
        else:
            self.game.tela.fill(PRETO)
            
        # Película escura cobrindo a tela
        overlay_fb = pygame.Surface((self.game.LARGURA, self.game.ALTURA))
        overlay_fb.fill(PRETO)
        overlay_fb.set_alpha(220)
        self.game.tela.blit(overlay_fb, (0, 0))
        
        # Texto centralizado
        render_fb = self.fonte_titulo.render(texto, True, BRANCO)
        pos_x = (self.game.LARGURA - render_fb.get_width()) // 2
        pos_y = (self.game.ALTURA - render_fb.get_height()) // 2
        self.game.tela.blit(render_fb, (pos_x, pos_y))
        
        # Atualiza a janela imediatamente
        pygame.display.flip()
        
        # Pausa fluida de 1 segundo sem congelar o sistema operativo
        tempo_inicio = pygame.time.get_ticks()
        while pygame.time.get_ticks() - tempo_inicio < 1000:
            pygame.event.pump()

    def executar_opcao(self):
        if self.selecionada == 3: 
            self.voltar_origem()
            return
            
        slot_escolhido = self.selecionada + 1 
        
        if self.game.acao_slots == "SALVAR":
            self._mostrar_feedback_sincrono("Salvando Jogo...") 
            self.game.salvar_estado(slot_escolhido)
            if hasattr(self.game, 'menu'):
                self.game.menu.atualizar_opcoes()
            self.game.mudar_estado("JOGANDO") 
            
        elif self.game.acao_slots == "CARREGAR":
            if save_manager.save_existe(slot_escolhido):
                self._mostrar_feedback_sincrono("Carregando Jogo...") 
                self.game.carregar_estado(slot_escolhido)
                self.game.mudar_estado("JOGANDO") 
                    
        elif self.game.acao_slots == "NOVO_JOGO":
            self.game.slot_atual = slot_escolhido
            self.game.tempo_jogado = 0.0
            self.game.itens_coletados.clear() 
            
            self.game.mapa_casa.carregar_cenario("CASA")
            self.game.filtrar_itens_coletados()
            self.game.investigou_pedras = False
            self.game.flashback_magia_concluido = False
            
            self.game.intro.iniciar()
            self.game.mudar_estado("INTRO")

    def voltar_origem(self):
        if self.game.origem_slots == "PAUSE":
            self.game.mudar_estado("PAUSE")
        else:
            self.game.mudar_estado("MENU")

    def update(self):
        pass

    def draw(self, tela):
        if self.game.origem_slots == "PAUSE":
            self.game.estados["JOGANDO"].draw(tela)
            tela.blit(self.overlay, (0, 0))
        else:
            tela.fill(PRETO)
        
        largura_bloco = 700 
        altura_bloco = 500
        x = (self.game.LARGURA - largura_bloco) // 2
        y = (self.game.ALTURA - altura_bloco) // 2

        pygame.draw.rect(tela, UI_FUNDO_PADRAO, (x, y, largura_bloco, altura_bloco))
        pygame.draw.rect(tela, CINZA_CLARO, (x, y, largura_bloco, altura_bloco), 2)

        if self.game.acao_slots == "NOVO_JOGO":
            texto_titulo = "Escolha onde Salvar"
        elif self.game.acao_slots == "CARREGAR":
            texto_titulo = "Carregar Jogo"
        else:
            texto_titulo = "Salvar Jogo"
            
        titulo = self.fonte_titulo.render(texto_titulo, True, UI_TEXTO_DESTAQUE)
        tela.blit(titulo, (x + (largura_bloco - titulo.get_width()) // 2, y + 40))

        self.rects_opcoes.clear()
        self.rects_deletar.clear()
        
        for i in range(3):
            tem_save = save_manager.save_existe(i + 1)
            
            if tem_save:
                dados = save_manager.carregar_dados(i + 1)
                fase = dados.get("cenario_atual", "Desconhecido").replace("_", " ")
                segundos = dados.get("tempo_jogado", 0.0)
                
                m, s = divmod(int(segundos), 60)
                h, m = divmod(m, 60)
                tempo_formatado = f"{h:02d}:{m:02d}:{s:02d}"
                status_texto = f"[{fase.capitalize()} | {tempo_formatado}]"
            else:
                status_texto = "[ Vazio ]"
            
            cor_opcao = TXT_SISTEMA_NARRADOR if i == self.selecionada else (BRANCO if tem_save or self.game.acao_slots in ["SALVAR", "NOVO_JOGO"] else UI_TEXTO_APAGADO)
            prefixo = "> " if i == self.selecionada else "  "
            
            render_slot = self.fonte_opcao.render(f"{prefixo}Slot {i+1}", True, cor_opcao)
            render_status = self.fonte_status.render(status_texto, True, cor_opcao)
            
            pos_x = x + 60
            pos_y = y + 140 + (i * 80)
            
            tela.blit(render_slot, (pos_x, pos_y))
            tela.blit(render_status, (pos_x + 130, pos_y + 8)) 
            
            if tem_save and self.game.acao_slots != "NOVO_JOGO":
                render_x = self.fonte_status.render("Apagar", True, (255, 100, 100))
                pos_x_del = pos_x + 500
                pos_y_del = pos_y + 8
                tela.blit(render_x, (pos_x_del, pos_y_del))
                self.rects_deletar.append(pygame.Rect(pos_x_del, pos_y_del, render_x.get_width(), 30))
            else:
                self.rects_deletar.append(None)
            
            rect = pygame.Rect(pos_x, pos_y, 480, 40)
            self.rects_opcoes.append(rect)

        cor_voltar = TXT_SISTEMA_NARRADOR if self.selecionada == 3 else BRANCO
        prefixo_v = "> " if self.selecionada == 3 else "  "
        render_voltar = self.fonte_opcao.render(f"{prefixo_v}Voltar", True, cor_voltar)
        
        pos_y_v = y + 140 + (3 * 80) + 20
        tela.blit(render_voltar, (x + 60, pos_y_v))
        self.rects_opcoes.append(pygame.Rect(x + 60, pos_y_v, 200, 40))

        if self.slot_confirmacao is not None:
            self._draw_confirmacao(tela)

    def _draw_confirmacao(self, tela):
        larg_conf = 450
        alt_conf = 200
        cx = (self.game.LARGURA - larg_conf) // 2
        cy = (self.game.ALTURA - alt_conf) // 2

        pygame.draw.rect(tela, UI_FUNDO_PADRAO, (cx, cy, larg_conf, alt_conf))
        pygame.draw.rect(tela, (255, 100, 100), (cx, cy, larg_conf, alt_conf), 2)
        
        txt_aviso = self.fonte_opcao.render(f"Apagar dados do Slot {self.slot_confirmacao}?", True, BRANCO)
        tela.blit(txt_aviso, (cx + (larg_conf - txt_aviso.get_width()) // 2, cy + 50))
        
        self.rects_confirma.clear()
        
        cor_sim = TXT_SISTEMA_NARRADOR if self.opcao_confirmacao == 0 else BRANCO
        txt_sim = self.fonte_opcao.render("> Sim <" if self.opcao_confirmacao == 0 else "  Sim  ", True, cor_sim)
        tela.blit(txt_sim, (cx + 100, cy + 120))
        self.rects_confirma.append(pygame.Rect(cx + 100, cy + 120, txt_sim.get_width(), 40))
        
        cor_nao = TXT_SISTEMA_NARRADOR if self.opcao_confirmacao == 1 else BRANCO
        txt_nao = self.fonte_opcao.render("> Não <" if self.opcao_confirmacao == 1 else "  Não  ", True, cor_nao)
        tela.blit(txt_nao, (cx + 250, cy + 120))
        self.rects_confirma.append(pygame.Rect(cx + 250, cy + 120, txt_nao.get_width(), 40))