# src/states/slots_states.py
import pygame
from src.states.states import State
from src.utils.colors import (
    PRETO, BRANCO, CARVAO_PROFUNDO, CINZA_ARDOSIA, CINZA_LINHO, CINZA_CLARO, CINZA_ESCURO,
    MARFIM_OFFWHITE, UI_TEXTO_DESTAQUE, UI_TEXTO_APAGADO, TXT_SISTEMA_NARRADOR,
    BARRA_VIDA_JOGADOR, BARRA_MANA, BORDA_PADRAO, BORDA_DESTAQUE, AZUL_HOVER_MENU, AZUL_HOVER_BG
)
from src.utils.resource_manager import ResourceManager
from src.ui.ui_utils import desenhar_painel_padrao
from src.utils import save_manager

def formatar_tempo(segundos):
    m, s = divmod(int(segundos), 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

class SlotsState(State):
    """
    Interface de Gerenciamento de Slots e Saves de Oblivium:
    - Estética Dark Fantasy / Metroidvania com molduras elegantes e tipografia consolidada
    - Suporte a múltiplos slots, modais de confirmação e seleção de versão (Manual vs Autosave)
    """
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
        self.opcoes_modal_versao = []
        
        # Tipografia Consolidada
        self.fonte_titulo = ResourceManager.carregar_fonte("sunday", 36)
        self.fonte_subtitulo = ResourceManager.carregar_fonte("contrail", 16)
        self.fonte_opcao = ResourceManager.carregar_fonte("sunday", 22)
        self.fonte_status = ResourceManager.carregar_fonte("contrail", 15)
        self.fonte_badge = ResourceManager.carregar_fonte("contrail", 13)
        
        self.rects_opcoes = []
        self.rects_deletar = [] 
        self.rects_confirma = []
        self.rects_modal_versao = []
        
        self.overlay = pygame.Surface((self.game.LARGURA, self.game.ALTURA))
        self.overlay.fill((10, 10, 12))
        self.overlay.set_alpha(190)

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
        total_opcoes = len(self.opcoes_modal_versao)
        if total_opcoes == 0:
            self.slot_modal_versao = None
            return

        if evento.type == pygame.KEYDOWN:
            if evento.key in [pygame.K_UP, pygame.K_w]:
                self.versao_selecionada = (self.versao_selecionada - 1) % total_opcoes
            elif evento.key in [pygame.K_DOWN, pygame.K_s]:
                self.versao_selecionada = (self.versao_selecionada + 1) % total_opcoes
            elif evento.key in [pygame.K_RETURN, pygame.K_SPACE]:
                self._executar_versao_escolhida()
            elif evento.key == pygame.K_ESCAPE:
                self.slot_modal_versao = None
                
        elif evento.type == pygame.MOUSEMOTION:
            for i, rect in enumerate(self.rects_modal_versao):
                if rect.collidepoint(evento.pos):
                    self.versao_selecionada = i
                    
        elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            for i, rect in enumerate(self.rects_modal_versao):
                if rect.collidepoint(evento.pos):
                    self.versao_selecionada = i
                    self._executar_versao_escolhida()

    def _executar_versao_escolhida(self):
        if not self.opcoes_modal_versao or self.versao_selecionada >= len(self.opcoes_modal_versao):
            self.slot_modal_versao = None
            return
            
        escolha = self.opcoes_modal_versao[self.versao_selecionada]
        tipo = escolha["tipo"]
        
        if tipo == "voltar":
            self.slot_modal_versao = None
        else:
            slot = self.slot_modal_versao
            self.slot_modal_versao = None
            self._mostrar_feedback_sincrono("Carregando Jogo...")
            self.game.carregar_estado(slot, tipo=tipo)
            self.game.mudar_estado("JOGANDO")

    def _mostrar_feedback_sincrono(self, mensagem):
        """Pinta a tela preta com mensagem elegante."""
        tela = pygame.display.get_surface()
        if not tela: return
        tela.fill(CARVAO_PROFUNDO)
        render = self.fonte_opcao.render(mensagem, True, MARFIM_OFFWHITE)
        tela.blit(render, ((self.game.LARGURA - render.get_width()) // 2, (self.game.ALTURA - render.get_height()) // 2))
        pygame.display.flip()
        pygame.time.delay(120)

    def executar_opcao(self):
        if self.selecionada == self.max_slots:
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
                self.slot_modal_versao = slot_escolhido
                self.versao_selecionada = 0
                self._montar_opcoes_modal_versao(slot_escolhido)
                    
        elif self.game.acao_slots == "NOVO_JOGO":
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
            tela.fill(CARVAO_PROFUNDO)
        
        largura_bloco = 860 
        altura_bloco = 580
        x = (self.game.LARGURA - largura_bloco) // 2
        y = (self.game.ALTURA - altura_bloco) // 2

        rect_painel = pygame.Rect(x, y, largura_bloco, altura_bloco)
        desenhar_painel_padrao(tela, rect_painel, cor_fundo=CARVAO_PROFUNDO, cor_borda=CINZA_LINHO, alpha=245)

        # Moldura interna decorativa
        rect_interno = rect_painel.inflate(-10, -10)
        pygame.draw.rect(tela, (28, 28, 34), rect_interno, 1, border_radius=2)

        if self.game.acao_slots == "NOVO_JOGO":
            texto_titulo = "Escolha onde Salvar"
        elif self.game.acao_slots == "CARREGAR":
            texto_titulo = "Carregar Jogo"
        else:
            texto_titulo = "Salvar Jogo"
            
        titulo = self.fonte_titulo.render(texto_titulo, True, MARFIM_OFFWHITE)
        tela.blit(titulo, (x + (largura_bloco - titulo.get_width()) // 2, y + 24))

        # Divisória
        pygame.draw.line(tela, CINZA_ARDOSIA, (x + 40, y + 68), (x + largura_bloco - 40, y + 68), 1)

        self.rects_opcoes.clear()
        self.rects_deletar.clear()
        
        resumos = save_manager.obter_resumo_slots()
        
        for i in range(self.max_slots):
            slot_num = i + 1
            info = resumos.get(slot_num, {})
            man = info.get("manual", {})
            auto = info.get("autosave", {})
            tem_save = info.get("tem_qualquer", False)
            
            esta_sel = (i == self.selecionada)
            pos_x = x + 40
            pos_y = y + 82 + (i * 92)
            
            rect_slot_card = pygame.Rect(pos_x, pos_y, largura_bloco - 80, 80)
            
            if esta_sel:
                pygame.draw.rect(tela, AZUL_HOVER_BG, rect_slot_card, border_radius=2)
                pygame.draw.rect(tela, AZUL_HOVER_MENU, rect_slot_card, 1, border_radius=2)
                cor_slot = MARFIM_OFFWHITE
                prefixo = "✦  "
            else:
                pygame.draw.rect(tela, (20, 20, 24), rect_slot_card, border_radius=2)
                pygame.draw.rect(tela, CINZA_ARDOSIA, rect_slot_card, 1, border_radius=2)
                cor_slot = CINZA_LINHO if tem_save or self.game.acao_slots in ["SALVAR", "NOVO_JOGO"] else UI_TEXTO_APAGADO
                prefixo = "    "
            
            render_nome_slot = self.fonte_opcao.render(f"{prefixo}Slot {slot_num}", True, cor_slot)
            tela.blit(render_nome_slot, (pos_x + 12, pos_y + 10))
            
            # Status: Manual e Autosave
            if tem_save:
                if man.get("existe"):
                    fase_m = man.get("cenario", "").replace("_", " ").capitalize()
                    tempo_m = formatar_tempo(man.get("tempo_jogado", 0.0))
                    txt_man = f"✦ Manual: {fase_m} | {tempo_m}"
                    cor_man = MARFIM_OFFWHITE
                else:
                    txt_man = "✦ Manual: Nenhum"
                    cor_man = UI_TEXTO_APAGADO
                    
                render_man = self.fonte_status.render(txt_man, True, cor_man)
                tela.blit(render_man, (pos_x + 180, pos_y + 14))
                
                if auto.get("existe"):
                    fase_a = auto.get("cenario", "").replace("_", " ").capitalize()
                    tempo_a = formatar_tempo(auto.get("tempo_jogado", 0.0))
                    txt_auto = f"⚡ Autosave: {fase_a} | {tempo_a}"
                    cor_auto = CINZA_LINHO
                else:
                    txt_auto = "⚡ Autosave: Nenhum"
                    cor_auto = UI_TEXTO_APAGADO
                    
                render_auto = self.fonte_status.render(txt_auto, True, cor_auto)
                tela.blit(render_auto, (pos_x + 180, pos_y + 44))
            else:
                render_vazio = self.fonte_status.render("[ Slot Vazio ]", True, UI_TEXTO_APAGADO)
                tela.blit(render_vazio, (pos_x + 180, pos_y + 28))
            
            # Botão Apagar
            if tem_save and self.game.acao_slots != "NOVO_JOGO":
                render_del = self.fonte_status.render("Apagar", True, (230, 90, 90))
                pos_x_del = pos_x + rect_slot_card.width - 85
                pos_y_del = pos_y + 28
                tela.blit(render_del, (pos_x_del, pos_y_del))
                self.rects_deletar.append(pygame.Rect(pos_x_del - 5, pos_y_del - 4, render_del.get_width() + 10, 30))
            else:
                self.rects_deletar.append(None)
            
            self.rects_opcoes.append(rect_slot_card)

        # Opção Voltar
        idx_voltar = self.max_slots
        esta_sel_v = (self.selecionada == idx_voltar)
        pos_y_v = y + 82 + (self.max_slots * 92) + 10
        pos_x_v = x + 40
        rect_v = pygame.Rect(pos_x_v, pos_y_v, 180, 36)
        
        if esta_sel_v:
            pygame.draw.rect(tela, AZUL_HOVER_BG, rect_v, border_radius=2)
            pygame.draw.rect(tela, AZUL_HOVER_MENU, rect_v, 1, border_radius=2)
            cor_voltar = MARFIM_OFFWHITE
            prefixo_v = "✦  "
        else:
            cor_voltar = CINZA_LINHO
            prefixo_v = "    "
            
        render_voltar = self.fonte_opcao.render(f"{prefixo_v}Voltar", True, cor_voltar)
        tela.blit(render_voltar, (pos_x_v + 10, pos_y_v + 6))
        self.rects_opcoes.append(rect_v)

        # Modais
        if self.slot_modal_versao is not None:
            self._draw_modal_versao(tela)
        elif self.slot_confirmacao is not None:
            self._draw_confirmacao(tela)

    def _draw_modal_versao(self, tela):
        """Modal comparativo entre Save Manual e Autosave com layout Dark Souls / Metroidvania."""
        larg_modal = 640
        alt_modal = 420
        cx = (self.game.LARGURA - larg_modal) // 2
        cy = (self.game.ALTURA - alt_modal) // 2

        overlay_m = pygame.Surface((self.game.LARGURA, self.game.ALTURA))
        overlay_m.fill((10, 10, 12))
        overlay_m.set_alpha(180)
        tela.blit(overlay_m, (0, 0))

        rect_modal = pygame.Rect(cx, cy, larg_modal, alt_modal)
        desenhar_painel_padrao(tela, rect_modal, cor_fundo=CARVAO_PROFUNDO, cor_borda=CINZA_LINHO, alpha=250)
        
        txt_titulo = self.fonte_titulo.render(f"Carregar Slot {self.slot_modal_versao}", True, MARFIM_OFFWHITE)
        tela.blit(txt_titulo, (cx + (larg_modal - txt_titulo.get_width()) // 2, cy + 22))
        
        txt_sub = self.fonte_subtitulo.render("Escolha qual versão do progresso carregar:", True, CINZA_LINHO)
        tela.blit(txt_sub, (cx + (larg_modal - txt_sub.get_width()) // 2, cy + 68))

        self.rects_modal_versao.clear()
        
        y_opcao = cy + 105
        for i, item in enumerate(self.opcoes_modal_versao):
            tipo = item["tipo"]
            selecionado = (i == self.versao_selecionada)
            
            if tipo == "voltar":
                pos_x_v = cx + 40
                pos_y_v = y_opcao + 12
                rect_v = pygame.Rect(pos_x_v, pos_y_v, 180, 36)
                
                if selecionado:
                    pygame.draw.rect(tela, AZUL_HOVER_BG, rect_v, border_radius=2)
                    pygame.draw.rect(tela, AZUL_HOVER_MENU, rect_v, 1, border_radius=2)
                    cor_v = MARFIM_OFFWHITE
                    prefixo = "✦  "
                else:
                    cor_v = CINZA_LINHO
                    prefixo = "    "
                    
                render_v = self.fonte_opcao.render(f"{prefixo}{item['titulo']}", True, cor_v)
                tela.blit(render_v, (pos_x_v + 10, pos_y_v + 6))
                self.rects_modal_versao.append(rect_v)
            else:
                larg_card = larg_modal - 80
                alt_card = 95
                card_rect = pygame.Rect(cx + 40, y_opcao, larg_card, alt_card)
                
                if selecionado:
                    pygame.draw.rect(tela, AZUL_HOVER_BG, card_rect, border_radius=2)
                    pygame.draw.rect(tela, AZUL_HOVER_MENU, card_rect, 1, border_radius=2)
                    cor_titulo = MARFIM_OFFWHITE
                    prefixo = "✦  "
                else:
                    pygame.draw.rect(tela, (20, 20, 24), card_rect, border_radius=2)
                    pygame.draw.rect(tela, CINZA_ARDOSIA, card_rect, 1, border_radius=2)
                    cor_titulo = CINZA_LINHO
                    prefixo = "    "
                
                render_tit = self.fonte_opcao.render(f"{prefixo}{item['titulo']}", True, cor_titulo)
                tela.blit(render_tit, (card_rect.x + 12, card_rect.y + 10))
                
                dados = item.get("dados", {})
                fase = dados.get("cenario", "Desconhecido").replace("_", " ").capitalize()
                tempo = formatar_tempo(dados.get("tempo_jogado", 0.0))
                halia = dados.get("halia", {})
                hp_atual = halia.get("vida_atual", 100)
                hp_max = halia.get("vida_maxima", 100)
                mp_atual = halia.get("mana_atual", 50)
                mp_max = halia.get("mana_maxima", 50)
                mems = halia.get("fragmentos_memoria", 0)
                
                linha1 = f"Cenário: {fase}   •   Tempo Jogado: {tempo}"
                linha2 = f"HP: {hp_atual}/{hp_max}   •   MP: {mp_atual}/{mp_max}   •   Memórias: {mems}"
                
                render_l1 = self.fonte_status.render(linha1, True, MARFIM_OFFWHITE)
                render_l2 = self.fonte_status.render(linha2, True, CINZA_LINHO)
                
                tela.blit(render_l1, (card_rect.x + 35, card_rect.y + 42))
                tela.blit(render_l2, (card_rect.x + 35, card_rect.y + 66))
                
                self.rects_modal_versao.append(card_rect)
                y_opcao += alt_card + 12

    def _draw_confirmacao(self, tela):
        larg_conf = 500
        alt_conf = 210
        cx = (self.game.LARGURA - larg_conf) // 2
        cy = (self.game.ALTURA - alt_conf) // 2

        rect_conf = pygame.Rect(cx, cy, larg_conf, alt_conf)
        desenhar_painel_padrao(tela, rect_conf, cor_fundo=CARVAO_PROFUNDO, cor_borda=(220, 80, 80), alpha=250)
        
        txt_aviso = self.fonte_opcao.render(f"Apagar todos os dados do Slot {self.slot_confirmacao}?", True, MARFIM_OFFWHITE)
        txt_sub = self.fonte_status.render("(Remove tanto o Save Manual quanto o Autosave)", True, CINZA_LINHO)
        
        tela.blit(txt_aviso, (cx + (larg_conf - txt_aviso.get_width()) // 2, cy + 36))
        tela.blit(txt_sub, (cx + (larg_conf - txt_sub.get_width()) // 2, cy + 76))
        
        self.rects_confirma.clear()
        
        # Botão Sim
        rect_sim = pygame.Rect(cx + 90, cy + 130, 140, 38)
        if self.opcao_confirmacao == 0:
            pygame.draw.rect(tela, (45, 20, 20), rect_sim, border_radius=2)
            pygame.draw.rect(tela, (220, 80, 80), rect_sim, 1, border_radius=2)
            cor_sim = (255, 120, 120)
            txt_s = "✦ Sim ✦"
        else:
            pygame.draw.rect(tela, (20, 20, 24), rect_sim, border_radius=2)
            pygame.draw.rect(tela, CINZA_ARDOSIA, rect_sim, 1, border_radius=2)
            cor_sim = CINZA_LINHO
            txt_s = "Sim"
            
        render_sim = self.fonte_opcao.render(txt_s, True, cor_sim)
        tela.blit(render_sim, (rect_sim.centerx - render_sim.get_width() // 2, rect_sim.centery - render_sim.get_height() // 2))
        self.rects_confirma.append(rect_sim)
        
        # Botão Não
        rect_nao = pygame.Rect(cx + 270, cy + 130, 140, 38)
        if self.opcao_confirmacao == 1:
            pygame.draw.rect(tela, (34, 34, 42), rect_nao, border_radius=2)
            pygame.draw.rect(tela, CINZA_LINHO, rect_nao, 1, border_radius=2)
            cor_nao = MARFIM_OFFWHITE
            txt_n = "✦ Não ✦"
        else:
            pygame.draw.rect(tela, (20, 20, 24), rect_nao, border_radius=2)
            pygame.draw.rect(tela, CINZA_ARDOSIA, rect_nao, 1, border_radius=2)
            cor_nao = CINZA_LINHO
            txt_n = "Não"
            
        render_nao = self.fonte_opcao.render(txt_n, True, cor_nao)
        tela.blit(render_nao, (rect_nao.centerx - render_nao.get_width() // 2, rect_nao.centery - render_nao.get_height() // 2))
        self.rects_confirma.append(rect_nao)
