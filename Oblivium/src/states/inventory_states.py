# src/states/inventory_states.py
import pygame
from src.states.states import State
from src.utils.colors import (
    PRETO, BRANCO, CARVAO_PROFUNDO, CINZA_ARDOSIA, CINZA_LINHO, CINZA_CLARO,
    MARFIM_OFFWHITE, UI_TEXTO_DESTAQUE, UI_TEXTO_APAGADO, BORDA_PADRAO, BORDA_DESTAQUE,
    PERGAMINHO_BG, PERGAMINHO_BORDA, PERGAMINHO_TINTA
)
from src.utils.resource_manager import ResourceManager
from src.ui.ui_utils import desenhar_painel_padrao, desenhar_tooltip_formatado, desenhar_flor_botanica

class InventoryState(State):
    """
    Interface de Inventário e Grimórios alinhada à estética Editorial Botânica:
    - Fundo em Carvão Profundo com bordas duplas em Cinza Linho / Marfim
    - Abas de Categorias: Bolsa, Grimórios, Chaves, Acessórios
    - Painel de Equipamentos à esquerda (Roupa, Cajado, Grimórios Ativos)
    - Grelha de Itens à direita com slots refinados e destaque em hover
    - Tooltips dinâmicos em estilo pergaminho
    """
    def __init__(self, game):
        super().__init__(game)
        self.overlay = pygame.Surface((self.game.LARGURA, self.game.ALTURA))
        self.overlay.fill((10, 10, 12))
        self.overlay.set_alpha(195)
        
        # Tipografia Editorial
        self.fonte_titulo = ResourceManager.carregar_fonte("sunday", 32)
        self.fonte_sub = ResourceManager.carregar_fonte("sunday", 20)
        self.fonte_abas = ResourceManager.carregar_fonte("contrail", 18)
        self.fonte_texto = ResourceManager.carregar_fonte("contrail", 15)
        self.fonte_poetica = ResourceManager.carregar_fonte("just_breathe", 18)
        
        # Abas de Navegação
        self.abas = ["Bolsa", "Grimórios", "Chaves", "Acessórios"]
        self.aba_ativa = 0
        self.rects_abas = []
        
        # Dimensões do Painel Central
        self.largura_inv = min(980, self.game.LARGURA - 80)
        self.altura_inv = min(600, self.game.ALTURA - 80)
        self.x_inv = (self.game.LARGURA - self.largura_inv) // 2
        self.y_inv = (self.game.ALTURA - self.altura_inv) // 2
        
        # Slots de Equipamento (Esquerda)
        self.slot_roupa = pygame.Rect(self.x_inv + 45, self.y_inv + 120, 85, 105)
        self.slot_cajado = pygame.Rect(self.x_inv + 145, self.y_inv + 120, 85, 105)
        
        # Slots Grimórios (4)
        self.slots_grimorios = [
            pygame.Rect(self.x_inv + 45 + (i * 92), self.y_inv + 275, 80, 80)
            for i in range(4)
        ]
        
        # Grelha de Itens (Direita)
        self.slots_gerais = []
        linhas, colunas = 4, 4
        inicio_x_grid = self.x_inv + 460
        inicio_y_grid = self.y_inv + 120
        tamanho_celula = 90
        
        for l in range(linhas):
            for c in range(colunas):
                r = pygame.Rect(inicio_x_grid + (c * tamanho_celula), inicio_y_grid + (l * tamanho_celula), 80, 80)
                self.slots_gerais.append(r)
                
        # Estado do Mouse
        self.pos_mouse = (0, 0)
        self.slot_hover = None
        self.tooltip_ativo = None

    def handle_events(self, eventos, teclas):
        self.pos_mouse = pygame.mouse.get_pos()
        self.slot_hover = None
        self.tooltip_ativo = None

        # Detecta hover nas abas
        for i, rect_aba in enumerate(self.rects_abas):
            if rect_aba.collidepoint(self.pos_mouse):
                break

        # Detecta hover nos equipamentos
        if self.slot_roupa.collidepoint(self.pos_mouse):
            self.slot_hover = "roupa"
            self.tooltip_ativo = ("Manto Arcanista", "Tecido impregnado com ressonância mágica ancestral.")
        elif self.slot_cajado.collidepoint(self.pos_mouse):
            self.slot_hover = "cajado"
            self.tooltip_ativo = ("Cajado de Espinheiro", "Foco arcano talhado em madeira sagrada de Oblivium.")

        # Detecta hover nos grimórios
        halia = getattr(self.game, 'halia', None)
        magias = getattr(halia, 'magias_desbloqueadas', []) if halia else []
        for i, rect_g in enumerate(self.slots_grimorios):
            if rect_g.collidepoint(self.pos_mouse):
                self.slot_hover = f"grimorio_{i}"
                if i < len(magias):
                    m = magias[i]
                    nome_m = m.get("nome", "Magia Desconhecida") if isinstance(m, dict) else getattr(m, 'nome', str(m))
                    desc_m = m.get("descricao", "Feitiço despertado dos fragmentos de memória.") if isinstance(m, dict) else getattr(m, 'descricao', "")
                    self.tooltip_ativo = (nome_m, desc_m)
                else:
                    self.tooltip_ativo = (f"Grimório {i+1}", "Espaço selado. Reúna mais memórias para despertar novos feitiços.")
                break

        for evento in eventos:
            if evento.type == pygame.KEYDOWN:
                # Fechar com ESC ou apertando a tecla de inventário
                tecla_inv = self.game.controles.get("Inventário", pygame.K_i)
                if evento.key in [pygame.K_ESCAPE, tecla_inv]:
                    self.game.mudar_estado("JOGANDO")
                    return
                    
            elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                # Clique nas Abas
                for i, rect_aba in enumerate(self.rects_abas):
                    if rect_aba.collidepoint(evento.pos):
                        self.aba_ativa = i
                        break

    def update(self):
        pass

    def draw(self, tela):
        # 1. Renderiza o jogo de fundo
        if "JOGANDO" in self.game.estados:
            self.game.estados["JOGANDO"].draw(tela)
        
        # 2. Película escura
        tela.blit(self.overlay, (0, 0))
 
        # 3. Painel Principal em Carvão Profundo com bordas e filigranas
        rect_painel = pygame.Rect(self.x_inv, self.y_inv, self.largura_inv, self.altura_inv)
        desenhar_painel_padrao(tela, rect_painel, cor_fundo=CARVAO_PROFUNDO, cor_borda=CINZA_LINHO, alpha=245)

        # Moldura interna decorativa
        rect_interno = rect_painel.inflate(-10, -10)
        pygame.draw.rect(tela, (30, 30, 36), rect_interno, 1, border_radius=2)

        # 4. Título Superior e Ornamentação Botânica
        txt_titulo = self.fonte_titulo.render("Inventário & Grimórios", True, MARFIM_OFFWHITE)
        tela.blit(txt_titulo, (self.x_inv + 35, self.y_inv + 24))

        desenhar_flor_botanica(tela, self.x_inv + self.largura_inv - 50, self.y_inv + 40, cor=CINZA_LINHO, escala=0.8)

        # 5. Abas de Categoria (Bolsa, Grimórios, Chaves, Acessórios)
        self.rects_abas.clear()
        x_aba = self.x_inv + 420
        y_aba = self.y_inv + 28
        
        for i, nome_aba in enumerate(self.abas):
            esta_ativa = (i == self.aba_ativa)
            r_aba_txt = self.fonte_abas.render(nome_aba, True, MARFIM_OFFWHITE if esta_ativa else CINZA_LINHO)
            w_aba = r_aba_txt.get_width() + 20
            h_aba = 28
            rect_aba = pygame.Rect(x_aba, y_aba, w_aba, h_aba)
            self.rects_abas.append(rect_aba)

            if esta_ativa:
                pygame.draw.rect(tela, (36, 36, 44), rect_aba, border_radius=2)
                pygame.draw.rect(tela, CINZA_LINHO, rect_aba, 1, border_radius=2)
                # Linha de destaque dourada/marfim na base da aba
                pygame.draw.line(tela, MARFIM_OFFWHITE, (rect_aba.left + 4, rect_aba.bottom - 2), (rect_aba.right - 4, rect_aba.bottom - 2), 2)
            
            tela.blit(r_aba_txt, (rect_aba.centerx - r_aba_txt.get_width() // 2, rect_aba.centery - r_aba_txt.get_height() // 2))
            x_aba += w_aba + 8

        # Linha separadora do cabeçalho
        pygame.draw.line(tela, CINZA_ARDOSIA, (self.x_inv + 30, self.y_inv + 68), (self.x_inv + self.largura_inv - 30, self.y_inv + 68), 1)

        # 6. SEÇÃO ESQUERDA: EQUIPAMENTOS DE HALIA
        halia = getattr(self.game, 'halia', None)
        nivel_sinc = getattr(halia, 'nivel_sincronia', 1) if halia else 1
        mems = getattr(halia, 'fragmentos_memoria', 0) if halia else 0

        txt_eq = self.fonte_sub.render(f"Halia — Nível de Sincronia {nivel_sinc}", True, MARFIM_OFFWHITE)
        tela.blit(txt_eq, (self.x_inv + 45, self.y_inv + 84))

        # 6.1 Slot Roupa
        hover_r = (self.slot_hover == "roupa")
        pygame.draw.rect(tela, (28, 28, 34) if hover_r else (20, 20, 24), self.slot_roupa, border_radius=2)
        pygame.draw.rect(tela, BORDA_DESTAQUE if hover_r else CINZA_LINHO, self.slot_roupa, 1, border_radius=2)
        lbl_r = self.fonte_texto.render("Roupa", True, MARFIM_OFFWHITE if hover_r else CINZA_LINHO)
        tela.blit(lbl_r, (self.slot_roupa.centerx - lbl_r.get_width() // 2, self.slot_roupa.centery - 8))

        # 6.2 Slot Cajado
        hover_c = (self.slot_hover == "cajado")
        pygame.draw.rect(tela, (28, 28, 34) if hover_c else (20, 20, 24), self.slot_cajado, border_radius=2)
        pygame.draw.rect(tela, BORDA_DESTAQUE if hover_c else CINZA_LINHO, self.slot_cajado, 1, border_radius=2)
        lbl_c = self.fonte_texto.render("Cajado", True, MARFIM_OFFWHITE if hover_c else CINZA_LINHO)
        tela.blit(lbl_c, (self.slot_cajado.centerx - lbl_c.get_width() // 2, self.slot_cajado.centery - 8))

        # 6.3 Slots de Grimórios Ativos (4)
        magias = getattr(halia, 'magias_desbloqueadas', []) if halia else []
        txt_gr = self.fonte_sub.render(f"Grimórios Despertados ({len(magias)}/4)", True, MARFIM_OFFWHITE)
        tela.blit(txt_gr, (self.x_inv + 45, self.y_inv + 245))
        
        for i, rect_g in enumerate(self.slots_grimorios):
            hover_g = (self.slot_hover == f"grimorio_{i}")
            pygame.draw.rect(tela, (28, 28, 34) if hover_g else (20, 20, 24), rect_g, border_radius=2)
            pygame.draw.rect(tela, BORDA_DESTAQUE if hover_g else CINZA_LINHO, rect_g, 1, border_radius=2)
            
            # Número do slot
            lbl_num = self.fonte_texto.render(f"[{i+1}]", True, CINZA_LINHO)
            tela.blit(lbl_num, (rect_g.x + 6, rect_g.y + 4))

            if i < len(magias):
                m = magias[i]
                nome_m = m.get("nome", "?") if isinstance(m, dict) else getattr(m, 'nome', str(m))
                r_m = self.fonte_texto.render(nome_m[:3].upper(), True, MARFIM_OFFWHITE)
                tela.blit(r_m, (rect_g.centerx - r_m.get_width() // 2, rect_g.centery - r_m.get_height() // 2 + 6))
            else:
                r_selo = self.fonte_texto.render("✦", True, (60, 60, 70))
                tela.blit(r_selo, (rect_g.centerx - r_selo.get_width() // 2, rect_g.centery - r_selo.get_height() // 2 + 6))

        # Linha vertical divisória entre equipamentos e bolsa
        pygame.draw.line(tela, CINZA_ARDOSIA, (self.x_inv + 430, self.y_inv + 84), (self.x_inv + 430, self.y_inv + self.altura_inv - 50), 1)

        # 7. SEÇÃO DIREITA: GRELHA DE ITENS / BOLSA
        nome_aba_atual = self.abas[self.aba_ativa]
        txt_geral = self.fonte_sub.render(f"{nome_aba_atual} — Espaço de Armazenamento", True, MARFIM_OFFWHITE)
        tela.blit(txt_geral, (self.x_inv + 460, self.y_inv + 84))
        
        for rect_geral in self.slots_gerais:
            esta_hover = rect_geral.collidepoint(self.pos_mouse)
            fundo_slot = (30, 30, 38) if esta_hover else (18, 18, 22)
            borda_slot = BORDA_DESTAQUE if esta_hover else CINZA_ARDOSIA
            
            pygame.draw.rect(tela, fundo_slot, rect_geral, border_radius=2)
            pygame.draw.rect(tela, borda_slot, rect_geral, 1, border_radius=2)

        # 8. RODAPÉ INFORMATIVO
        txt_mem = self.fonte_poetica.render(f"Fragmentos de Memória Selados: {mems} / 7", True, CINZA_LINHO)
        tela.blit(txt_mem, (self.x_inv + 45, self.y_inv + self.altura_inv - 34))

        txt_rodape = self.fonte_texto.render("[ESC], [I] ou [B] para retornar", True, CINZA_LINHO)
        tela.blit(txt_rodape, (self.x_inv + self.largura_inv - txt_rodape.get_width() - 40, self.y_inv + self.altura_inv - 34))

        # 9. RENDERIZAÇÃO DO TOOLTIP EM PERGAMINHO (Se houver item em hover)
        if self.tooltip_ativo:
            titulo_t, desc_t = self.tooltip_ativo
            desenhar_tooltip_formatado(tela, self.pos_mouse[0] + 18, self.pos_mouse[1] + 18, titulo_t, desc_t)