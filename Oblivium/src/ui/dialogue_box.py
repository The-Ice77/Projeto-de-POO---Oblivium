# src/ui/dialogue_box.py
import pygame
import math
from src.ui.ui_utils import quebrar_texto_em_linhas, desenhar_painel_padrao
from src.utils.colors import (
    UI_FUNDO_PADRAO, BRANCO, CINZA_CLARO, CINZA_LINHO, CINZA_ARDOSIA,
    UI_TEXTO_APAGADO, TXT_SISTEMA_NARRADOR, TXT_PENSAMENTO_INTERNO, 
    NOME_HALIA, NOME_MALDICAO, UI_TEXTO_DESTAQUE,
    BOTAO_FECHAR_NORMAL, BOTAO_FECHAR_HOVER,
    CARVAO_PROFUNDO, MARFIM_OFFWHITE, BORDA_PADRAO, BORDA_DESTAQUE,
    AZUL_HOVER_MENU, AZUL_HOVER_BG, AZUL_HOVER_BORDA
)
from src.utils.resource_manager import ResourceManager
from src.mechanics.dialogue_manager import DialogueManager

class DialogueBox:
    """
    Caixa de Diálogo e Sistema de Escolhas de Oblivium (Visual + POO):
    - Conectada ao DialogueManager (leitura de JSON estruturado em nós)
    - Fundo escuro em Carvão Profundo com contorno sutil de 1px
    - Suporte universal a Retrato (Portrait) para NPCs e Halia
    - Sistema de Escolhas lado a lado (grade 2 colunas) com cabeçalho dinâmico
    - Destaques visuais e hover no padrão azul clarinho do menu inicial
    - Totalmente retrocompatível com chamadas legadas de listas de falas
    """
    def __init__(self, largura_tela, manager=None):
        self.fonte_texto = ResourceManager.carregar_fonte("contrail", 20)
        self.fonte_nome = ResourceManager.carregar_fonte("sunday", 24)
        self.fonte_titulo_escolha = ResourceManager.carregar_fonte("sunday", 20)
        self.fonte_opcao = ResourceManager.carregar_fonte("contrail", 18)
        self.fonte_rodape = ResourceManager.carregar_fonte("contrail", 15)
        
        self.largura_tela = largura_tela
        self.largura_maxima = largura_tela - 220 
        self.ativo = False
        
        # Gerenciador de Diálogos por Nós
        self.manager = manager or DialogueManager()
        self.dados_atuais = None
        
        # --- MÁQUINA DE ESCREVER ---
        self.texto_completo = ""
        self.linhas_completas = []
        self.tamanho_total = 0
        self.caractere_atual = 0
        self.velocidade_texto = 1.0 
        self.tempo_ultimo_input = 0

        # --- SISTEMA DE ESCOLHAS LADO A LADO ---
        self.em_escolha = False
        self.cabecalho_escolha = "Sobre o que deseja conversar?"
        self.opcoes_disponiveis = []
        self.opcao_selecionada = 0
        self.rects_opcoes = []
        self.opcoes_por_pagina = 4

        # -- BOTÃO DE FECHAR --
        self.rect_botao_x = pygame.Rect(0, 0, 26, 26) 
        self.botao_x_hover = False    
        
        # -- PAGINAÇÃO --
        self.pagina_atual = 0
        self.rect_seta_esq = pygame.Rect(-100, -100, 24, 24)
        self.rect_seta_dir = pygame.Rect(-100, -100, 24, 24)
        self.hover_esq = False
        self.hover_dir = False
        
        # -- CONTROLE DE CANCELAMENTO --
        self.pode_fechar = False
        self.id_cancelamento_no = None
        self.opcao_cancelada_id = None

        # -- RETRATOS EM CACHE --
        self.retratos = {
            "Halia": None,  # Temporariamente desativado a pedido do usuário (aguardando novas artes)
            "Torvin": ResourceManager.carregar_imagem("elementos/torvin_portrait.png", (96, 124)),
            "Carroceiro": ResourceManager.carregar_imagem("elementos/carroceiro_portrait.png", (96, 124))
        }

    @property
    def historico_escolhas(self):
        """Compartilha o histórico de escolhas diretamente com o DialogueManager."""
        return self.manager.historico_escolhas

    @historico_escolhas.setter
    def historico_escolhas(self, novo_historico):
        """Permite que o save_manager restaure o histórico de escolhas perfeitamente."""
        self.manager.historico_escolhas = set(novo_historico)

    def iniciar_dialogo(self, origem_dialogo):
        """
        Inicia uma conversa:
        - `origem_dialogo` pode ser o ID do diálogo no JSON ("hub_carroceiro")
        - ou uma lista de dicionários [{"autor": "...", "texto": "..."}] (modo legado)
        """
        if isinstance(origem_dialogo, str):
            sucesso = self.manager.iniciar_conversa(origem_dialogo)
        elif isinstance(origem_dialogo, list):
            sucesso = self.manager.iniciar_lista_direta(origem_dialogo)
        elif isinstance(origem_dialogo, dict):
            sucesso = self.manager.iniciar_lista_direta([origem_dialogo])
        else:
            sucesso = False

        if not sucesso:
            self.ativo = False
            return

        self.ativo = True
        self.opcao_cancelada_id = None
        self.tempo_ultimo_input = pygame.time.get_ticks()
        self._sincronizar_com_manager()

    def _sincronizar_com_manager(self):
        """Lê o nó ativo do DialogueManager e ajusta o estado da UI correspondente."""
        no = self.manager.obter_no_atual()
        if not self.manager.ativo or not no:
            self.ativo = False
            self.em_escolha = False
            self.dados_atuais = None
            return

        self.ativo = True
        self.dados_atuais = no

        tipo_no = no.get("tipo", "fala")
        if tipo_no == "escolha" or "escolhas" in no:
            self.em_escolha = True
            self.pode_fechar = no.get("pode_fechar", False)
            self.id_cancelamento_no = no.get("id_cancelamento", None)
            self.cabecalho_escolha = no.get("cabecalho", no.get("titulo", "Sobre o que deseja conversar?"))
            self.pagina_atual = 0
            self.opcao_selecionada = 0
            self.rects_opcoes = []
            self.texto_completo = ""
            self.linhas_completas = []
            self.tamanho_total = 0
            self.caractere_atual = 0

            if "opcoes" in no:
                self.opcoes_disponiveis = self.manager.obter_opcoes_filtradas()
            else:
                # Suporte a listas legadas com 'escolhas'
                self.opcoes_disponiveis = [
                    opt for opt in no.get("escolhas", [])
                    if opt.get("id") not in self.manager.historico_escolhas
                ]

            # Caso todas as opções já tenham sido consumidas
            if not self.opcoes_disponiveis:
                if self.pode_fechar:
                    self.manager.cancelar_escolha()
                    self._sincronizar_com_manager()
                else:
                    self.manager.avancar()
                    self._sincronizar_com_manager()
        else:
            self.em_escolha = False
            self.pode_fechar = False
            self.texto_completo = no.get("texto", "")

            autor = no.get("autor", "Narrador")
            tem_retrato = bool(autor and autor not in ["Sistema", "Narrador"])
            largura_caixa = min(960, self.largura_tela - 80)
            largura_util = largura_caixa - (180 if tem_retrato else 70)

            self.linhas_completas = quebrar_texto_em_linhas(self.texto_completo, self.fonte_texto, largura_util)
            self.tamanho_total = sum(len(l) for l in self.linhas_completas)
            self.caractere_atual = 0

    def proximo_texto(self):
        """Avança o texto (máquina de escrever -> próximo nó da narrativa)."""
        if not self.ativo: return

        tempo_atual = pygame.time.get_ticks()
        if tempo_atual - self.tempo_ultimo_input < 250: return 
        self.tempo_ultimo_input = tempo_atual

        if self.em_escolha:
            if not self.opcoes_disponiveis:
                self.manager.avancar()
                self._sincronizar_com_manager()
                return
            self.confirmar_escolha()
            return

        if self.caractere_atual < self.tamanho_total:
            self.caractere_atual = self.tamanho_total
        else:
            continua = self.manager.avancar()
            if continua:
                self._sincronizar_com_manager()
            else:
                self.ativo = False

    def confirmar_escolha(self):
        """Confirma a opção atualmente selecionada no menu de escolhas."""
        if not self.opcoes_disponiveis:
            self.ativo = False
            self.em_escolha = False
            return

        if 0 <= self.opcao_selecionada < len(self.opcoes_disponiveis):
            escolha = self.opcoes_disponiveis[self.opcao_selecionada]
            
            # Se for legado (contém chave "resultado" em dict/list)
            if "resultado" in escolha:
                opt_id = escolha.get("id")
                if opt_id and opt_id != "prosseguir" and not escolha.get("repetivel", False):
                    self.manager.historico_escolhas.add(opt_id)
                self.iniciar_dialogo(escolha["resultado"])
            else:
                self.manager.escolher_opcao(escolha)
                self._sincronizar_com_manager()
        else:
            self.ativo = False
            self.em_escolha = False

    def controlar_menu_escolhas(self, tecla):
        if not self.ativo or not self.em_escolha or not self.opcoes_disponiveis: return False
        
        total_opcoes = len(self.opcoes_disponiveis)
        total_paginas = max(1, (total_opcoes - 1) // self.opcoes_por_pagina + 1)

        inicio = self.pagina_atual * self.opcoes_por_pagina
        fim = min(inicio + self.opcoes_por_pagina, total_opcoes)
        num_opcoes_pagina = fim - inicio

        if num_opcoes_pagina <= 0: return False

        # Índice local na página atual (0 a num_opcoes_pagina - 1)
        idx_local = self.opcao_selecionada - inicio
        if idx_local < 0 or idx_local >= num_opcoes_pagina:
            idx_local = 0

        col = idx_local % 2
        row = idx_local // 2

        # 1. Atalhos Numéricos Diretos (1 a 4)
        teclas_num = {
            pygame.K_1: 0, pygame.K_KP1: 0,
            pygame.K_2: 1, pygame.K_KP2: 1,
            pygame.K_3: 2, pygame.K_KP3: 2,
            pygame.K_4: 3, pygame.K_KP4: 3
        }
        if tecla in teclas_num:
            offset = teclas_num[tecla]
            if offset < num_opcoes_pagina:
                self.opcao_selecionada = inicio + offset
                return True

        # 2. Tecla TAB (Avanço Cíclico) e Shift+TAB (Retrocesso Cíclico)
        if tecla == pygame.K_TAB:
            mods = pygame.key.get_mods()
            if mods & pygame.KMOD_SHIFT:
                self.opcao_selecionada = (self.opcao_selecionada - 1) % total_opcoes
            else:
                self.opcao_selecionada = (self.opcao_selecionada + 1) % total_opcoes
            self.pagina_atual = self.opcao_selecionada // self.opcoes_por_pagina
            return True

        # 3. Navegação Vertical (CIMA / BAIXO ou W / S)
        if tecla in [pygame.K_UP, pygame.K_w]:
            if row > 0:
                self.opcao_selecionada = inicio + col
            else:
                if self.pagina_atual > 0:
                    self.pagina_atual -= 1
                    prev_inicio = self.pagina_atual * self.opcoes_por_pagina
                    prev_fim = min(prev_inicio + self.opcoes_por_pagina, total_opcoes)
                    prev_count = prev_fim - prev_inicio
                    target = 2 + col if (2 + col) < prev_count else (prev_count - 1)
                    self.opcao_selecionada = prev_inicio + target
                else:
                    target = 2 + col if (2 + col) < num_opcoes_pagina else (num_opcoes_pagina - 1)
                    self.opcao_selecionada = inicio + target
            return True

        elif tecla in [pygame.K_DOWN, pygame.K_s]:
            if row == 0 and (2 + col) < num_opcoes_pagina:
                self.opcao_selecionada = inicio + 2 + col
            elif row == 0 and 2 < num_opcoes_pagina:
                self.opcao_selecionada = inicio + 2
            else:
                if self.pagina_atual < total_paginas - 1:
                    self.pagina_atual += 1
                    next_inicio = self.pagina_atual * self.opcoes_por_pagina
                    next_fim = min(next_inicio + self.opcoes_por_pagina, total_opcoes)
                    next_count = next_fim - next_inicio
                    target = col if col < next_count else 0
                    self.opcao_selecionada = next_inicio + target
                else:
                    self.opcao_selecionada = inicio + col
            return True

        # 4. Navegação Horizontal (ESQUERDA / DIREITA ou A / D)
        elif tecla in [pygame.K_LEFT, pygame.K_a]:
            if col > 0:
                self.opcao_selecionada = inicio + (row * 2)
            else:
                if self.pagina_atual > 0:
                    self.pagina_atual -= 1
                    prev_inicio = self.pagina_atual * self.opcoes_por_pagina
                    prev_fim = min(prev_inicio + self.opcoes_por_pagina, total_opcoes)
                    prev_count = prev_fim - prev_inicio
                    target = min(prev_count - 1, row * 2 + 1)
                    self.opcao_selecionada = prev_inicio + target
                else:
                    target = row * 2 + 1
                    if target < num_opcoes_pagina:
                        self.opcao_selecionada = inicio + target
                    elif num_opcoes_pagina > 1:
                        self.opcao_selecionada = inicio + (num_opcoes_pagina - 1)
            return True

        elif tecla in [pygame.K_RIGHT, pygame.K_d]:
            if col == 0 and (row * 2 + 1) < num_opcoes_pagina:
                self.opcao_selecionada = inicio + (row * 2 + 1)
            else:
                if self.pagina_atual < total_paginas - 1:
                    self.pagina_atual += 1
                    next_inicio = self.pagina_atual * self.opcoes_por_pagina
                    next_fim = min(next_inicio + self.opcoes_por_pagina, total_opcoes)
                    next_count = next_fim - next_inicio
                    target = min(next_count - 1, row * 2)
                    self.opcao_selecionada = next_inicio + target
                else:
                    self.opcao_selecionada = inicio + (row * 2)
            return True

        return False

    def rolar_pagina(self, delta_y):
        """Suporte à roda do mouse (scroll) para mudar páginas de escolhas."""
        if not self.ativo or not self.em_escolha or not self.opcoes_disponiveis: return
        total_paginas = max(1, (len(self.opcoes_disponiveis) - 1) // self.opcoes_por_pagina + 1)
        if total_paginas <= 1: return

        if delta_y > 0 and self.pagina_atual > 0:
            self.pagina_atual -= 1
            self.opcao_selecionada = self.pagina_atual * self.opcoes_por_pagina
        elif delta_y < 0 and self.pagina_atual < total_paginas - 1:
            self.pagina_atual += 1
            self.opcao_selecionada = self.pagina_atual * self.opcoes_por_pagina

    def atualizar_mouse(self, posicao_mouse):
        if not self.ativo: return
        
        if self.em_escolha:
            if self.pode_fechar:
                self.botao_x_hover = self.rect_botao_x.collidepoint(posicao_mouse)
                
            self.hover_esq = self.rect_seta_esq.collidepoint(posicao_mouse)
            self.hover_dir = self.rect_seta_dir.collidepoint(posicao_mouse)
                
            for i, rect in enumerate(self.rects_opcoes):
                if rect.collidepoint(posicao_mouse):
                    self.opcao_selecionada = (self.pagina_atual * self.opcoes_por_pagina) + i
                    break

    def clicar_mouse(self, posicao_mouse):
        if not self.ativo: return
        
        if self.em_escolha:
            if self.pode_fechar and self.rect_botao_x.collidepoint(posicao_mouse):
                self.opcao_cancelada_id = self.id_cancelamento_no
                self.manager.cancelar_escolha()
                self._sincronizar_com_manager()
                return
                
            total_paginas = (len(self.opcoes_disponiveis) - 1) // self.opcoes_por_pagina + 1
            if total_paginas > 1:
                if self.rect_seta_esq.collidepoint(posicao_mouse) and self.pagina_atual > 0:
                    self.pagina_atual -= 1
                    return
                if self.rect_seta_dir.collidepoint(posicao_mouse) and self.pagina_atual < total_paginas - 1:
                    self.pagina_atual += 1
                    return
                    
            for i, rect in enumerate(self.rects_opcoes):
                if rect.collidepoint(posicao_mouse):
                    self.opcao_selecionada = (self.pagina_atual * self.opcoes_por_pagina) + i
                    self.confirmar_escolha()
                    break
        else:
            self.proximo_texto()

    def atualizar(self):
        if not self.ativo or self.em_escolha: return
        if self.caractere_atual < self.tamanho_total:
            self.caractere_atual += self.velocidade_texto
            if self.caractere_atual > self.tamanho_total:
                self.caractere_atual = self.tamanho_total

    def desenhar(self, tela):
        if not self.ativo or not self.dados_atuais:
            self.ativo = False 
            return

        if self.em_escolha:
            if not self.opcoes_disponiveis:
                self.em_escolha = False
                self.ativo = False
                return
            self._desenhar_escolhas(tela)
        else:
            self._desenhar_texto_corrido(tela)

    def _obter_cor_autor(self, autor):
        if autor == "Halia":
            return NOME_HALIA
        elif autor == "Maldição":
            return NOME_MALDICAO
        elif autor in ["Sistema", "Narrador"]:
            return TXT_SISTEMA_NARRADOR
        elif autor in ["Pensamento", "Pensamento Interno"]:
            return TXT_PENSAMENTO_INTERNO
        return MARFIM_OFFWHITE

    def _desenhar_texto_corrido(self, tela):
        dados = self.dados_atuais or {}
        autor = dados.get("autor", "Narrador")
        tem_retrato = bool(autor and autor not in ["Sistema", "Narrador"])

        largura_tela = tela.get_width()
        altura_tela = tela.get_height()

        largura_caixa = min(960, largura_tela - 80)
        altura_caixa = 175
        x_caixa = (largura_tela - largura_caixa) // 2
        y_caixa = altura_tela - altura_caixa - 25

        rect_caixa = pygame.Rect(x_caixa, y_caixa, largura_caixa, altura_caixa)
        
        # 1. Caixa Principal em Carvão Profundo
        desenhar_painel_padrao(tela, rect_caixa, cor_fundo=CARVAO_PROFUNDO, cor_borda=CINZA_LINHO, alpha=245)
        
        # Moldura interna decorativa
        rect_interno = rect_caixa.inflate(-8, -8)
        pygame.draw.rect(tela, (24, 24, 30), rect_interno, 1, border_radius=2)

        # 2. Retrato do Interlocutor (NPC / Halia)
        pos_x_texto = x_caixa + 24
        if tem_retrato:
            w_ret = 96
            h_ret = 124
            x_ret = x_caixa + 18
            y_ret = y_caixa + (altura_caixa - h_ret) // 2
            rect_ret = pygame.Rect(x_ret, y_ret, w_ret, h_ret)
            
            pygame.draw.rect(tela, (14, 14, 18), rect_ret, border_radius=2)
            pygame.draw.rect(tela, CINZA_ARDOSIA, rect_ret, 1, border_radius=2)
            
            sprite_retrato = self.retratos.get(autor)
            if sprite_retrato:
                sprite_redim = pygame.transform.smoothscale(sprite_retrato, (w_ret - 2, h_ret - 2))
                tela.blit(sprite_redim, (x_ret + 1, y_ret + 1))
            else:
                f_ini = ResourceManager.carregar_fonte("sunday", 36)
                txt_ini = f_ini.render(autor[0].upper() if autor else "?", True, MARFIM_OFFWHITE)
                tela.blit(txt_ini, txt_ini.get_rect(center=rect_ret.center))
                
            pos_x_texto = x_ret + w_ret + 24

        # 3. Nome do Autor
        cor_autor = self._obter_cor_autor(autor)
        if autor and autor not in ["Narrador", "Sistema"]:
            r_nome = self.fonte_nome.render(autor, True, cor_autor)
            tela.blit(r_nome, (pos_x_texto, y_caixa + 18))
            y_linha = y_caixa + 54
        else:
            y_linha = y_caixa + 28

        # 4. Texto corrido com Máquina de Escrever
        caracteres_permitidos = int(self.caractere_atual)
        for linha in self.linhas_completas:
            if caracteres_permitidos <= 0: break
            tamanho_linha = len(linha)
            if caracteres_permitidos >= tamanho_linha:
                texto_render = linha
                caracteres_permitidos -= tamanho_linha
            else:
                texto_render = linha[:caracteres_permitidos]
                caracteres_permitidos = 0
                
            if texto_render:
                render_texto = self.fonte_texto.render(texto_render, True, MARFIM_OFFWHITE)
                tela.blit(render_texto, (pos_x_texto, y_linha))
            y_linha += 26

        # 5. Indicador de Avanço Estático e Limpo
        if self.caractere_atual >= self.tamanho_total:
            txt_avanco = self.fonte_rodape.render("▼  [ ENTER ou Clique para avançar ]", True, UI_TEXTO_APAGADO)
            pos_x_av = x_caixa + largura_caixa - txt_avanco.get_width() - 24
            pos_y_av = y_caixa + altura_caixa - 24
            tela.blit(txt_avanco, (pos_x_av, pos_y_av))

    def _desenhar_escolhas(self, tela):
        largura_tela = tela.get_width()
        altura_tela = tela.get_height()

        largura_card = min(960, largura_tela - 80)
        altura_card = 215
        x_card = (largura_tela - largura_card) // 2
        y_card = altura_tela - altura_card - 25

        rect_card = pygame.Rect(x_card, y_card, largura_card, altura_card)
        desenhar_painel_padrao(tela, rect_card, cor_fundo=CARVAO_PROFUNDO, cor_borda=CINZA_LINHO, alpha=250)

        # Moldura interna decorativa
        rect_interno = rect_card.inflate(-8, -8)
        pygame.draw.rect(tela, (24, 24, 30), rect_interno, 1, border_radius=2)

        # 1. Cabeçalho Superior da Escolha Dinâmico
        texto_cabecalho = getattr(self, "cabecalho_escolha", "Sobre o que deseja conversar?")
        r_cabecalho = self.fonte_titulo_escolha.render(texto_cabecalho, True, MARFIM_OFFWHITE)
        tela.blit(r_cabecalho, (x_card + 22, y_card + 14))

        # Divisória do Cabeçalho
        pygame.draw.line(tela, CINZA_ARDOSIA, (x_card + 20, y_card + 42), (x_card + largura_card - 20, y_card + 42), 1)

        # 2. Botão de Fechar [X] no topo direito sem sobreposição
        if self.pode_fechar:
            self.rect_botao_x.x = x_card + largura_card - 38
            self.rect_botao_x.y = y_card + 10
            
            cor_fechar = BOTAO_FECHAR_HOVER if self.botao_x_hover else (35, 35, 42)
            borda_fechar = AZUL_HOVER_MENU if self.botao_x_hover else CINZA_LINHO
            pygame.draw.rect(tela, cor_fechar, self.rect_botao_x, border_radius=2)
            pygame.draw.rect(tela, borda_fechar, self.rect_botao_x, 1, border_radius=2)
            
            txt_x = self.fonte_rodape.render("X", True, BRANCO)
            tela.blit(txt_x, txt_x.get_rect(center=self.rect_botao_x.center))

        # 3. Lista de Opções Lado a Lado (2 Colunas x 2 Linhas)
        inicio = self.pagina_atual * self.opcoes_por_pagina
        fim = min(inicio + self.opcoes_por_pagina, len(self.opcoes_disponiveis))
        opcoes_pagina = self.opcoes_disponiveis[inicio:fim]

        novos_rects = []
        w_coluna = (largura_card - 56) // 2
        h_opcao = 42

        for i, opcao in enumerate(opcoes_pagina):
            idx_global = inicio + i
            esta_sel = (idx_global == self.opcao_selecionada)
            
            col = i % 2
            row = i // 2
            
            x_opt = x_card + 20 + col * (w_coluna + 16)
            y_opt = y_card + 54 + row * (h_opcao + 8)
            rect_opt = pygame.Rect(x_opt, y_opt, w_coluna, h_opcao)
            novos_rects.append(rect_opt)
            
            if esta_sel:
                pygame.draw.rect(tela, AZUL_HOVER_BG, rect_opt, border_radius=2)
                pygame.draw.rect(tela, AZUL_HOVER_MENU, rect_opt, 1, border_radius=2)
                cor_txt = AZUL_HOVER_MENU
                prefixo = f"►  {idx_global + 1}. "
            else:
                pygame.draw.rect(tela, (18, 18, 22), rect_opt, border_radius=2)
                pygame.draw.rect(tela, CINZA_ARDOSIA, rect_opt, 1, border_radius=2)
                cor_txt = CINZA_LINHO
                prefixo = f"    {idx_global + 1}. "

            texto_bruto = opcao.get('texto', '')
            texto_opcao = f"{prefixo}{texto_bruto}"
            
            # Garante que o texto caiba na coluna sem overflow
            largura_disponivel = w_coluna - 20
            if self.fonte_opcao.size(texto_opcao)[0] > largura_disponivel:
                while len(texto_bruto) > 3 and self.fonte_opcao.size(f"{prefixo}{texto_bruto}...")[0] > largura_disponivel:
                    texto_bruto = texto_bruto[:-1]
                texto_opcao = f"{prefixo}{texto_bruto}..."

            r_opt = self.fonte_opcao.render(texto_opcao, True, cor_txt)
            tela.blit(r_opt, (rect_opt.x + 10, rect_opt.centery - r_opt.get_height() // 2))

        self.rects_opcoes = novos_rects

        # 4. Barra de Paginação Visível e Espaçosa ( [ ◄ ]  Página 1 de 2  [ ► ] )
        total_paginas = (len(self.opcoes_disponiveis) - 1) // self.opcoes_por_pagina + 1
        self.rect_seta_esq.topleft = (-100, -100)
        self.rect_seta_dir.topleft = (-100, -100)

        if total_paginas > 1:
            txt_pag = f"Página {self.pagina_atual + 1} de {total_paginas}"
            r_pag = self.fonte_rodape.render(txt_pag, True, CINZA_LINHO)
            
            largura_paginacao = 38 + 16 + r_pag.get_width() + 16 + 38
            x_pag = x_card + (largura_card - largura_paginacao) // 2
            y_pag = y_card + altura_card - 38
            
            # Botão Anterior [ ◄ ]
            self.rect_seta_esq = pygame.Rect(x_pag, y_pag, 38, 26)
            pode_voltar = self.pagina_atual > 0
            cor_bg_esq = AZUL_HOVER_BG if (self.hover_esq and pode_voltar) else (20, 20, 26)
            cor_borda_esq = AZUL_HOVER_MENU if (self.hover_esq and pode_voltar) else (CINZA_LINHO if pode_voltar else CINZA_ARDOSIA)
            cor_txt_esq = AZUL_HOVER_MENU if (self.hover_esq and pode_voltar) else (MARFIM_OFFWHITE if pode_voltar else UI_TEXTO_APAGADO)
            
            pygame.draw.rect(tela, cor_bg_esq, self.rect_seta_esq, border_radius=2)
            pygame.draw.rect(tela, cor_borda_esq, self.rect_seta_esq, 1, border_radius=2)
            r_esq = self.fonte_rodape.render("◄", True, cor_txt_esq)
            tela.blit(r_esq, r_esq.get_rect(center=self.rect_seta_esq.center))
            
            # Texto central da página
            tela.blit(r_pag, (x_pag + 38 + 16, y_pag + 4))
            
            # Botão Próximo [ ► ]
            self.rect_seta_dir = pygame.Rect(x_pag + 38 + 16 + r_pag.get_width() + 16, y_pag, 38, 26)
            pode_avancar = self.pagina_atual < total_paginas - 1
            cor_bg_dir = AZUL_HOVER_BG if (self.hover_dir and pode_avancar) else (20, 20, 26)
            cor_borda_dir = AZUL_HOVER_MENU if (self.hover_dir and pode_avancar) else (CINZA_LINHO if pode_avancar else CINZA_ARDOSIA)
            cor_txt_dir = AZUL_HOVER_MENU if (self.hover_dir and pode_avancar) else (MARFIM_OFFWHITE if pode_avancar else UI_TEXTO_APAGADO)
            
            pygame.draw.rect(tela, cor_bg_dir, self.rect_seta_dir, border_radius=2)
            pygame.draw.rect(tela, cor_borda_dir, self.rect_seta_dir, 1, border_radius=2)
            r_dir = self.fonte_rodape.render("►", True, cor_txt_dir)
            tela.blit(r_dir, r_dir.get_rect(center=self.rect_seta_dir.center))