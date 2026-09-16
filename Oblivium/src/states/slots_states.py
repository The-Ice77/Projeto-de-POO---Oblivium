# src/states/slots_states.py
import pygame
from src.states.states import State
from src.utils.colors import (
    PRETO, BRANCO, UI_FUNDO_PADRAO, CINZA_CLARO, CINZA_ESCURO,
    UI_TEXTO_DESTAQUE, UI_TEXTO_APAGADO, TXT_SISTEMA_NARRADOR,
    BARRA_VIDA_JOGADOR, BARRA_MANA
)
from src.utils import save_manager

def formatar_tempo(segundos):
    m, s = divmod(int(segundos), 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

class SlotsState(State):
    def __init__(self, game):
        super().__init__(game)
        self.max_slots = 4
        self.opcoes = ["Slot 1", "Slot 2", "Slot 3", "Slot 4", "Voltar"]
        self.selecionada = 0
        
        # Modal de confirmação de exclusão
        self.slot_confirmacao = None 
        self.opcao_confirmacao = 1 # 0: Sim, 1: Não
        
        # Modal de escolha entre Save Manual e Autosave ao carregar
        self.slot_modal_versao = None
        self.versao_selecionada = 0 # 0: Manual, 1: Autosave, 2: Voltar
        self.opcoes_modal_versao = [] # guardará lista de dicts com as opções disponíveis
        
        self.fonte_titulo = pygame.font.Font(None, 52)
        self.fonte_subtitulo = pygame.font.Font(None, 28)
        self.fonte_opcao = pygame.font.Font(None, 34)
        self.fonte_status = pygame.font.Font(None, 22)
        self.fonte_badge = pygame.font.Font(None, 20)
        
        self.rects_opcoes = []
        self.rects_deletar = [] 
        self.rects_confirma = []
        self.rects_modal_versao = []
        
        self.overlay = pygame.Surface((self.game.LARGURA, self.game.ALTURA))
        self.overlay.fill(PRETO)
        self.overlay.set_alpha(180)

    def handle_events(self, eventos, teclas):
        for evento in eventos:
            # 1. Tratamento do Modal de Confirmação de Exclusão
            if self.slot_confirmacao is not None:
                self._handle_eventos_confirmacao(evento)
                return

            # 2. Tratamento do Modal de Escolha de Versão (Manual vs Autosave)
            if self.slot_modal_versao is not None:
                self._handle_eventos_modal_versao(evento)
                return

            # 3. Tratamento da Lista Principal de Slots
            if evento.type == pygame.KEYDOWN:
                if evento.key in [pygame.K_UP, pygame.K_w]:
                    self.selecionada = (self.selecionada - 1) % len(self.opcoes)
                elif evento.key in [pygame.K_DOWN, pygame.K_s]:
                    self.selecionada = (self.selecionada + 1) % len(self.opcoes)
                elif evento.key in [pygame.K_RETURN, pygame.K_SPACE]:
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

    def _handle_eventos_confirmacao(self, evento):
        if evento.type == pygame.KEYDOWN:
            if evento.key in [pygame.K_LEFT, pygame.K_a]:
                self.opcao_confirmacao = 0
            elif evento.key in [pygame.K_RIGHT, pygame.K_d]:
                self.opcao_confirmacao = 1
            elif evento.key in [pygame.K_RETURN, pygame.K_SPACE]:
                if self.opcao_confirmacao == 0: 
                    save_manager.apagar_dados(self.slot_confirmacao, tipo="ambos")
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
                        save_manager.apagar_dados(self.slot_confirmacao, tipo="ambos")
                        if hasattr(self.game, 'menu'):
                            self.game.menu.atualizar_opcoes()
                    self.slot_confirmacao = None

    def _handle_eventos_modal_versao(self, evento):
        num_opcoes = len(self.opcoes_modal_versao)
        if num_opcoes == 0:
            self.slot_modal_versao = None
            return

        if evento.type == pygame.KEYDOWN:
            if evento.key in [pygame.K_UP, pygame.K_w]:
                self.versao_selecionada = (self.versao_selecionada - 1) % num_opcoes
            elif evento.key in [pygame.K_DOWN, pygame.K_s]:
                self.versao_selecionada = (self.versao_selecionada + 1) % num_opcoes
            elif evento.key in [pygame.K_RETURN, pygame.K_SPACE]:
                self._executar_opcao_versao()
            elif evento.key == pygame.K_ESCAPE:
                self.slot_modal_versao = None
        elif evento.type == pygame.MOUSEMOTION:
            for i, rect in enumerate(self.rects_modal_versao):
                if rect and rect.collidepoint(evento.pos):
                    self.versao_selecionada = i
        elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            for i, rect in enumerate(self.rects_modal_versao):
                if rect and rect.collidepoint(evento.pos):
                    self.versao_selecionada = i
                    self._executar_opcao_versao()

    def _executar_opcao_versao(self):
        if not (0 <= self.versao_selecionada < len(self.opcoes_modal_versao)):
            self.slot_modal_versao = None
            return

        item = self.opcoes_modal_versao[self.versao_selecionada]
        tipo = item.get("tipo")
        slot = self.slot_modal_versao

        if tipo == "voltar":
            self.slot_modal_versao = None
            return

        if tipo in ["manual", "autosave"]:
            texto_loading = "Carregando Save Manual..." if tipo == "manual" else "Carregando Autosave..."
            self._mostrar_feedback_sincrono(texto_loading)
            self.game.carregar_estado(slot, tipo=tipo)
            self.slot_modal_versao = None
            self.game.mudar_estado("JOGANDO")

    def _mostrar_feedback_sincrono(self, texto):
        """Desenha a tela congelada com o jogo ao fundo e exibe o aviso de loading."""
        if self.game.origem_slots == "PAUSE" and "JOGANDO" in self.game.estados:
            self.game.estados["JOGANDO"].draw(self.game.tela)
        else:
            self.game.tela.fill(PRETO)
            
        overlay_fb = pygame.Surface((self.game.LARGURA, self.game.ALTURA))
        overlay_fb.fill(PRETO)
        overlay_fb.set_alpha(220)
        self.game.tela.blit(overlay_fb, (0, 0))
        
        render_fb = self.fonte_titulo.render(texto, True, BRANCO)
        pos_x = (self.game.LARGURA - render_fb.get_width()) // 2
        pos_y = (self.game.ALTURA - render_fb.get_height()) // 2
        self.game.tela.blit(render_fb, (pos_x, pos_y))
        
        pygame.display.flip()
        
        tempo_inicio = pygame.time.get_ticks()
        while pygame.time.get_ticks() - tempo_inicio < 700:
            pygame.event.pump()

    def executar_opcao(self):
        if self.selecionada == self.max_slots: # Botão "Voltar"
            self.voltar_origem()
            return
            
        slot_escolhido = self.selecionada + 1 
        
        if self.game.acao_slots == "SALVAR":
            self._mostrar_feedback_sincrono("Salvando Jogo...") 
            self.game.salvar_estado(slot_escolhido, tipo="manual")
            if hasattr(self.game, 'menu'):
                self.game.menu.atualizar_opcoes()
            self.game.mudar_estado("JOGANDO") 
            
        elif self.game.acao_slots == "CARREGAR":
            tem_manual = save_manager.save_existe(slot_escolhido, tipo="manual")
            tem_auto = save_manager.save_existe(slot_escolhido, tipo="autosave")
            
            if tem_manual or tem_auto:
                # Abre o modal de seleção comparativa (Save Manual vs Autosave)
                self.slot_modal_versao = slot_escolhido
                self.versao_selecionada = 0
                self._montar_opcoes_modal_versao(slot_escolhido)
                    
        elif self.game.acao_slots == "NOVO_JOGO":
            # Reseta estado e inicializa no slot escolhido
            self.game.resetar_progresso(slot_escolhido)
            self.game.salvar_estado(slot_escolhido, tipo="manual")
            if hasattr(self.game, 'menu'):
                self.game.menu.atualizar_opcoes()
            self.game.intro.iniciar()
            self.game.mudar_estado("INTRO")

    def _montar_opcoes_modal_versao(self, slot):
        self.opcoes_modal_versao.clear()
        resumos = save_manager.obter_resumo_slots()
        info_slot = resumos.get(slot, {})
        
        man = info_slot.get("manual", {})
        auto = info_slot.get("autosave", {})

        if man.get("existe"):
            self.opcoes_modal_versao.append({
                "tipo": "manual",
                "titulo": "✦ Carregar Save Manual",
                "dados": man
            })
        if auto.get("existe"):
            self.opcoes_modal_versao.append({
                "tipo": "autosave",
                "titulo": "⚡ Carregar Autosave (Checkpoint)",
                "dados": auto
            })
            
        self.opcoes_modal_versao.append({
            "tipo": "voltar",
            "titulo": "⮜ Voltar",
            "dados": None
        })

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
        
        largura_bloco = 860 
        altura_bloco = 580
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
        tela.blit(titulo, (x + (largura_bloco - titulo.get_width()) // 2, y + 25))

        self.rects_opcoes.clear()
        self.rects_deletar.clear()
        
        resumos = save_manager.obter_resumo_slots()
        
        for i in range(self.max_slots):
            slot_num = i + 1
            info = resumos.get(slot_num, {})
            man = info.get("manual", {})
            auto = info.get("autosave", {})
            tem_save = info.get("tem_qualquer", False)
            
            cor_slot = TXT_SISTEMA_NARRADOR if i == self.selecionada else (BRANCO if tem_save or self.game.acao_slots in ["SALVAR", "NOVO_JOGO"] else UI_TEXTO_APAGADO)
            prefixo = "> " if i == self.selecionada else "  "
            
            pos_x = x + 40
            pos_y = y + 85 + (i * 92)
            
            # Caixa do slot
            rect_slot_card = pygame.Rect(pos_x, pos_y, largura_bloco - 80, 80)
            cor_borda_slot = TXT_SISTEMA_NARRADOR if i == self.selecionada else CINZA_ESCURO
            pygame.draw.rect(tela, (24, 24, 28), rect_slot_card)
            pygame.draw.rect(tela, cor_borda_slot, rect_slot_card, 1)
            
            render_nome_slot = self.fonte_opcao.render(f"{prefixo}Slot {slot_num}", True, cor_slot)
            tela.blit(render_nome_slot, (pos_x + 15, pos_y + 12))
            
            # Renderização dos status: Manual e Autosave
            if tem_save:
                # Linha 1: Manual Save
                if man.get("existe"):
                    fase_m = man.get("cenario", "").replace("_", " ").capitalize()
                    tempo_m = formatar_tempo(man.get("tempo_jogado", 0.0))
                    txt_man = f"✦ Manual: {fase_m} | {tempo_m}"
                    cor_man = (200, 220, 200)
                else:
                    txt_man = "✦ Manual: Nenhum"
                    cor_man = UI_TEXTO_APAGADO
                    
                render_man = self.fonte_status.render(txt_man, True, cor_man)
                tela.blit(render_man, (pos_x + 170, pos_y + 14))
                
                # Linha 2: Autosave
                if auto.get("existe"):
                    fase_a = auto.get("cenario", "").replace("_", " ").capitalize()
                    tempo_a = formatar_tempo(auto.get("tempo_jogado", 0.0))
                    txt_auto = f"⚡ Autosave: {fase_a} | {tempo_a}"
                    cor_auto = (210, 210, 160)
                else:
                    txt_auto = "⚡ Autosave: Nenhum"
                    cor_auto = UI_TEXTO_APAGADO
                    
                render_auto = self.fonte_status.render(txt_auto, True, cor_auto)
                tela.blit(render_auto, (pos_x + 170, pos_y + 44))
            else:
                render_vazio = self.fonte_status.render("[ Slot Vazio ]", True, UI_TEXTO_APAGADO)
                tela.blit(render_vazio, (pos_x + 170, pos_y + 28))
            
            # Botão Apagar
            if tem_save and self.game.acao_slots != "NOVO_JOGO":
                render_del = self.fonte_status.render("Apagar", True, (255, 110, 110))
                pos_x_del = pos_x + rect_slot_card.width - 90
                pos_y_del = pos_y + 28
                tela.blit(render_del, (pos_x_del, pos_y_del))
                self.rects_deletar.append(pygame.Rect(pos_x_del - 5, pos_y_del - 4, render_del.get_width() + 10, 30))
            else:
                self.rects_deletar.append(None)
            
            self.rects_opcoes.append(rect_slot_card)

        # Opção Voltar
        idx_voltar = self.max_slots
        cor_voltar = TXT_SISTEMA_NARRADOR if self.selecionada == idx_voltar else BRANCO
        prefixo_v = "> " if self.selecionada == idx_voltar else "  "
        render_voltar = self.fonte_opcao.render(f"{prefixo_v}Voltar", True, cor_voltar)
        
        pos_y_v = y + 85 + (self.max_slots * 92) + 12
        pos_x_v = x + 40
        tela.blit(render_voltar, (pos_x_v, pos_y_v))
        self.rects_opcoes.append(pygame.Rect(pos_x_v, pos_y_v, 180, 40))

        # Modais
        if self.slot_modal_versao is not None:
            self._draw_modal_versao(tela)
        elif self.slot_confirmacao is not None:
            self._draw_confirmacao(tela)

    def _draw_modal_versao(self, tela):
        """Desenha o modal comparativo entre Save Manual e Autosave com layout dark fantasy."""
        larg_modal = 620
        alt_modal = 420
        cx = (self.game.LARGURA - larg_modal) // 2
        cy = (self.game.ALTURA - alt_modal) // 2

        # Película interna escura
        overlay_m = pygame.Surface((self.game.LARGURA, self.game.ALTURA))
        overlay_m.fill(PRETO)
        overlay_m.set_alpha(170)
        tela.blit(overlay_m, (0, 0))

        pygame.draw.rect(tela, UI_FUNDO_PADRAO, (cx, cy, larg_modal, alt_modal))
        pygame.draw.rect(tela, CINZA_CLARO, (cx, cy, larg_modal, alt_modal), 2)
        
        txt_titulo = self.fonte_titulo.render(f"Carregar Slot {self.slot_modal_versao}", True, UI_TEXTO_DESTAQUE)
        tela.blit(txt_titulo, (cx + (larg_modal - txt_titulo.get_width()) // 2, cy + 22))
        
        txt_sub = self.fonte_subtitulo.render("Escolha qual versão do progresso carregar:", True, UI_TEXTO_APAGADO)
        tela.blit(txt_sub, (cx + (larg_modal - txt_sub.get_width()) // 2, cy + 72))

        self.rects_modal_versao.clear()
        
        y_opcao = cy + 115
        for i, item in enumerate(self.opcoes_modal_versao):
            tipo = item["tipo"]
            selecionado = (i == self.versao_selecionada)
            prefixo = "> " if selecionado else "  "
            
            if tipo == "voltar":
                cor_v = TXT_SISTEMA_NARRADOR if selecionado else BRANCO
                render_v = self.fonte_opcao.render(f"{prefixo}{item['titulo']}", True, cor_v)
                pos_x_v = cx + 40
                pos_y_v = y_opcao + 15
                tela.blit(render_v, (pos_x_v, pos_y_v))
                self.rects_modal_versao.append(pygame.Rect(pos_x_v, pos_y_v, 200, 36))
            else:
                larg_card = larg_modal - 80
                alt_card = 95
                card_rect = pygame.Rect(cx + 40, y_opcao, larg_card, alt_card)
                
                cor_borda = TXT_SISTEMA_NARRADOR if selecionado else CINZA_ESCURO
                cor_fundo_card = (26, 26, 32) if selecionado else (20, 20, 24)
                
                pygame.draw.rect(tela, cor_fundo_card, card_rect)
                pygame.draw.rect(tela, cor_borda, card_rect, 1)
                
                cor_titulo = TXT_SISTEMA_NARRADOR if selecionado else BRANCO
                render_tit = self.fonte_opcao.render(f"{prefixo}{item['titulo']}", True, cor_titulo)
                tela.blit(render_tit, (card_rect.x + 15, card_rect.y + 12))
                
                dados = item.get("dados", {})
                fase = dados.get("cenario", "Desconhecido").replace("_", " ").capitalize()
                tempo = formatar_tempo(dados.get("tempo_jogado", 0.0))
                halia = dados.get("halia", {})
                hp_atual = halia.get("vida_atual", 100)
                hp_max = halia.get("vida_maxima", 100)
                mp_atual = halia.get("mana_atual", 50)
                mp_max = halia.get("mana_maxima", 50)
                mems = halia.get("fragmentos_memoria", 0)
                
                linha1 = f"Cenário: {fase}   |   Tempo Jogado: {tempo}"
                linha2 = f"HP: {hp_atual}/{hp_max}   |   MP: {mp_atual}/{mp_max}   |   Memórias: {mems}"
                
                render_l1 = self.fonte_status.render(linha1, True, (210, 210, 210))
                render_l2 = self.fonte_status.render(linha2, True, (170, 190, 180))
                
                tela.blit(render_l1, (card_rect.x + 35, card_rect.y + 44))
                tela.blit(render_l2, (card_rect.x + 35, card_rect.y + 68))
                
                self.rects_modal_versao.append(card_rect)
                y_opcao += alt_card + 14

    def _draw_confirmacao(self, tela):
        larg_conf = 480
        alt_conf = 210
        cx = (self.game.LARGURA - larg_conf) // 2
        cy = (self.game.ALTURA - alt_conf) // 2

        pygame.draw.rect(tela, UI_FUNDO_PADRAO, (cx, cy, larg_conf, alt_conf))
        pygame.draw.rect(tela, (255, 100, 100), (cx, cy, larg_conf, alt_conf), 2)
        
        txt_aviso = self.fonte_opcao.render(f"Apagar todos os dados do Slot {self.slot_confirmacao}?", True, BRANCO)
        txt_sub = self.fonte_status.render("(Remove tanto o Save Manual quanto o Autosave)", True, UI_TEXTO_APAGADO)
        
        tela.blit(txt_aviso, (cx + (larg_conf - txt_aviso.get_width()) // 2, cy + 40))
        tela.blit(txt_sub, (cx + (larg_conf - txt_sub.get_width()) // 2, cy + 80))
        
        self.rects_confirma.clear()
        
        cor_sim = TXT_SISTEMA_NARRADOR if self.opcao_confirmacao == 0 else BRANCO
        txt_sim = self.fonte_opcao.render("> Sim <" if self.opcao_confirmacao == 0 else "  Sim  ", True, cor_sim)
        tela.blit(txt_sim, (cx + 110, cy + 135))
        self.rects_confirma.append(pygame.Rect(cx + 110, cy + 135, txt_sim.get_width(), 40))
        
        cor_nao = TXT_SISTEMA_NARRADOR if self.opcao_confirmacao == 1 else BRANCO
        txt_nao = self.fonte_opcao.render("> Não <" if self.opcao_confirmacao == 1 else "  Não  ", True, cor_nao)
        tela.blit(txt_nao, (cx + 280, cy + 135))
        self.rects_confirma.append(pygame.Rect(cx + 280, cy + 135, txt_nao.get_width(), 40))