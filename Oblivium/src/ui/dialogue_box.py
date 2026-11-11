# src/ui/dialogue_box.py
import pygame
from src.ui.ui_utils import quebrar_texto_em_linhas, desenhar_painel_padrao
from src.utils.colors import (
    BRANCO, CINZA_LINHO, CINZA_ARDOSIA,
    UI_TEXTO_APAGADO, TXT_SISTEMA_NARRADOR, TXT_PENSAMENTO_INTERNO, 
    NOME_HALIA, NOME_MALDICAO,
    BOTAO_FECHAR_HOVER,
    CARVAO_PROFUNDO, MARFIM_OFFWHITE,
    AZUL_HOVER_MENU, AZUL_HOVER_BG
)
from src.utils.resource_manager import ResourceManager
from src.mechanics.dialogue_manager import DialogueManager
from src.core.audio_manager import AudioManager

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

        # -- POP-UP DE LEITURA INTEGRAL DE OPÇÃO LONGA --
        self.pop_up_aberto = False
        self.pop_up_opcao = None
        self.pop_up_indice = 0
        self.rect_popup = None
        self.rect_popup_confirmar = None
        self.rect_popup_cancelar = None
        self.rect_popup_fechar = None
        self.hover_popup_confirmar = False
        self.hover_popup_cancelar = False
        self.hover_popup_fechar = False

        # -- RETRATOS EM CACHE --
        self.retratos = {
            "Halia": None,  # Temporariamente desativado a pedido do usuário (aguardando novas artes)
            "Torvin": ResourceManager.carregar_imagem("elementos/torvin_portrait.png", (96, 124)),
            "Carroceiro": ResourceManager.carregar_imagem("elementos/carroceiro_portrait.png", (96, 124))
        }
        self._inicializar_retratos_companheiros()

    def _inicializar_retratos_companheiros(self):
        """Inicializa retratos pixel-art canônicos dos heróis da companhia e NPCs."""
        w_ret, h_ret = 96, 124

        # Carrega os retratos oficiais em alta definição gerados a partir das novas sprites
        mapa_retratos_oficiais = {
            "Halia": "elementos/retratos/retrato_halia.png",
            "Sylvan": "elementos/retratos/retrato_sylvan.png",
            "Roland": "elementos/retratos/retrato_roland.png",
            "Caelen": "elementos/retratos/retrato_caelen.png",
            "Aldous": "elementos/retratos/retrato_aldous.png",
            "Elara": "elementos/retratos/retrato_elara.png",
            "Torvald": "elementos/retratos/retrato_torvald.png"
        }
        for chave, rel_path in mapa_retratos_oficiais.items():
            img_ret = ResourceManager.carregar_imagem(rel_path, (w_ret, h_ret))
            if img_ret:
                self.retratos[chave] = img_ret
        
        # Sylvan (Ferreiro e Guerreiro Anão)
        surf_sylvan = pygame.Surface((w_ret, h_ret), pygame.SRCALPHA)
        surf_sylvan.fill((22, 18, 20))
        for r in range(50, 0, -10):
            pygame.draw.circle(surf_sylvan, (80, 40, 20, 25), (48, 62), r)
        pygame.draw.rect(surf_sylvan, (80, 50, 35), (14, 85, 68, 38), border_radius=4)
        pygame.draw.rect(surf_sylvan, (140, 150, 160), (22, 82, 52, 22))
        pygame.draw.rect(surf_sylvan, (220, 175, 45), (18, 100, 60, 6))
        pygame.draw.rect(surf_sylvan, (225, 185, 155), (28, 28, 40, 42), border_radius=4)
        pygame.draw.rect(surf_sylvan, (195, 75, 30), (24, 18, 48, 16), border_radius=4)
        pygame.draw.rect(surf_sylvan, (155, 55, 20), (20, 26, 10, 28))
        pygame.draw.rect(surf_sylvan, (155, 55, 20), (66, 26, 10, 28))
        pygame.draw.rect(surf_sylvan, (20, 16, 22), (34, 40, 6, 5))
        pygame.draw.rect(surf_sylvan, (20, 16, 22), (56, 40, 6, 5))
        pygame.draw.rect(surf_sylvan, (200, 150, 125), (44, 42, 8, 8))
        pygame.draw.rect(surf_sylvan, (195, 75, 30), (24, 48, 48, 56), border_radius=6)
        pygame.draw.rect(surf_sylvan, (155, 55, 20), (30, 68, 36, 32))
        pygame.draw.rect(surf_sylvan, (225, 185, 50), (28, 84, 12, 6))
        pygame.draw.rect(surf_sylvan, (225, 185, 50), (56, 84, 12, 6))
        if not self.retratos.get("Sylvan"):
            self.retratos["Sylvan"] = surf_sylvan

        # Roland (Paladino Sentinela)
        surf_roland = pygame.Surface((w_ret, h_ret), pygame.SRCALPHA)
        surf_roland.fill((18, 22, 28))
        for r in range(50, 0, -10):
            pygame.draw.circle(surf_roland, (40, 50, 75, 25), (48, 62), r)
        pygame.draw.rect(surf_roland, (36, 58, 110), (12, 85, 72, 38), border_radius=4)
        pygame.draw.rect(surf_roland, (190, 200, 215), (18, 78, 60, 26), border_radius=2)
        pygame.draw.rect(surf_roland, (220, 180, 50), (22, 98, 52, 4))
        pygame.draw.rect(surf_roland, (230, 195, 170), (30, 26, 36, 42), border_radius=4)
        pygame.draw.rect(surf_roland, (95, 70, 50), (26, 16, 44, 18), border_radius=4)
        pygame.draw.rect(surf_roland, (75, 50, 35), (24, 24, 8, 22))
        pygame.draw.rect(surf_roland, (75, 50, 35), (64, 24, 8, 22))
        pygame.draw.rect(surf_roland, (18, 20, 26), (36, 38, 5, 5))
        pygame.draw.rect(surf_roland, (18, 20, 26), (55, 38, 5, 5))
        pygame.draw.rect(surf_roland, (205, 165, 140), (45, 42, 6, 8))
        pygame.draw.rect(surf_roland, (215, 175, 150), (34, 56, 28, 8))
        if not self.retratos.get("Roland"):
            self.retratos["Roland"] = surf_roland

        # Caelen (Clérigo das Ervas)
        surf_caelen = pygame.Surface((w_ret, h_ret), pygame.SRCALPHA)
        surf_caelen.fill((20, 22, 24))
        for r in range(50, 0, -10):
            pygame.draw.circle(surf_caelen, (50, 70, 90, 25), (48, 62), r)
        pygame.draw.rect(surf_caelen, (242, 244, 248), (14, 82, 68, 42), border_radius=4)
        pygame.draw.rect(surf_caelen, (85, 160, 225), (28, 82, 12, 42))
        pygame.draw.rect(surf_caelen, (85, 160, 225), (56, 82, 12, 42))
        pygame.draw.rect(surf_caelen, (180, 115, 75), (42, 94, 12, 14))
        pygame.draw.rect(surf_caelen, (235, 205, 185), (31, 26, 34, 42), border_radius=4)
        pygame.draw.rect(surf_caelen, (175, 140, 95), (27, 16, 42, 18), border_radius=4)
        pygame.draw.rect(surf_caelen, (145, 115, 75), (26, 26, 6, 26))
        pygame.draw.rect(surf_caelen, (145, 115, 75), (64, 26, 6, 26))
        pygame.draw.rect(surf_caelen, (22, 24, 28), (36, 40, 5, 4))
        pygame.draw.rect(surf_caelen, (22, 24, 28), (55, 40, 5, 4))
        pygame.draw.rect(surf_caelen, (215, 180, 160), (45, 44, 6, 6))
        if not self.retratos.get("Caelen"):
            self.retratos["Caelen"] = surf_caelen

    @property
    def historico_escolhas(self):
        """Compartilha o histórico de escolhas diretamente com o DialogueManager."""
        return self.manager.historico_escolhas

    @historico_escolhas.setter
    def historico_escolhas(self, novo_historico):
        """Permite que o save_manager restaure o histórico de escolhas perfeitamente."""
        self.manager.historico_escolhas = set(novo_historico)

    def iniciar_dialogo(self, origem_dialogo, no_inicial=None):
        """
        Inicia uma conversa:
        - `origem_dialogo` pode ser o ID do diálogo no JSON ("hub_carroceiro")
        - ou uma lista de dicionários [{"autor": "...", "texto": "..."}] (modo legado)
        """
        if isinstance(origem_dialogo, str):
            sucesso = self.manager.iniciar_conversa(origem_dialogo, no_inicial=no_inicial)
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
        self.pop_up_aberto = False
        self.pop_up_opcao = None
        self.rect_popup = None
        self.rect_popup_confirmar = None
        self.rect_popup_cancelar = None
        self.rect_popup_fechar = None

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
                no_esgotado = no.get("no_esgotado")
                nos_conv = self.manager.banco_dialogos.get(self.manager.conversa_id, {}).get("nos", {})
                if no_esgotado and no_esgotado in nos_conv and no_esgotado != self.manager.no_id_atual:
                    self.manager.no_id_atual = no_esgotado
                    self.manager.no_atual = nos_conv[no_esgotado]
                    self._sincronizar_com_manager()
                elif self.pode_fechar:
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

    def _tocar_sfx(self, alias, volume_extra=1.0):
        audio = AudioManager.get_instance()
        if audio:
            audio.tocar_sfx(alias, volume_extra=volume_extra)

    def proximo_texto(self):
        """Avança o texto (máquina de escrever -> próximo nó da narrativa)."""
        if not self.ativo: return

        tempo_atual = pygame.time.get_ticks()
        if self.tempo_ultimo_input > 0 and (tempo_atual - self.tempo_ultimo_input < 250):
            return 
        self.tempo_ultimo_input = tempo_atual

        if self.em_escolha:
            if not self.opcoes_disponiveis:
                self._tocar_sfx("ui_cursor")
                self.manager.avancar()
                self._sincronizar_com_manager()
                return
            self.confirmar_escolha()
            return

        if self.caractere_atual < self.tamanho_total:
            self.caractere_atual = self.tamanho_total
        else:
            self._tocar_sfx("ui_cursor")
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

        self._tocar_sfx("ui_confirmar")
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

    def opcao_eh_longa(self, opcao, idx_global=0):
        """Verifica se uma opção de escolha é longa demais para a coluna padrão de 2 colunas."""
        if not opcao or not isinstance(opcao, dict):
            return False
        texto = opcao.get("texto", "")
        if not texto:
            return False
        largura_max_coluna = (min(960, getattr(self, "largura_tela", 1280) - 80) - 56) // 2 - 28
        prefixo = f"►  {idx_global + 1}. "
        largura_texto = self.fonte_opcao.size(f"{prefixo}{texto}")[0]
        return largura_texto > largura_max_coluna or len(texto) >= 44

    def abrir_pop_up(self, opcao, indice=0):
        """Abre o pop-up modal para leitura completa e confirmação de uma resposta extensa."""
        self.pop_up_aberto = True
        self.pop_up_opcao = opcao
        self.pop_up_indice = indice
        self.opcao_selecionada = indice
        self.hover_popup_confirmar = False
        self.hover_popup_cancelar = False
        self.hover_popup_fechar = False
        self._tocar_sfx("ui_cursor")

    def fechar_pop_up(self):
        """Fecha o pop-up de resposta extensa, retornando à lista de opções intacta."""
        self.pop_up_aberto = False
        self.pop_up_opcao = None
        self.rect_popup = None
        self.rect_popup_confirmar = None
        self.rect_popup_cancelar = None
        self.rect_popup_fechar = None
        self.tempo_ultimo_input = 0
        self._tocar_sfx("ui_voltar")

    def controlar_menu_escolhas(self, tecla):
        if not self.ativo or not self.em_escolha or not self.opcoes_disponiveis: return False
        
        if self.pop_up_aberto:
            if tecla == pygame.K_ESCAPE:
                self.fechar_pop_up()
                return True
            elif tecla in [pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE]:
                self.fechar_pop_up()
                self.confirmar_escolha()
                return True
            return False
        
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
            if self.pop_up_aberto:
                self.hover_popup_confirmar = self.rect_popup_confirmar.collidepoint(posicao_mouse) if self.rect_popup_confirmar else False
                self.hover_popup_cancelar = self.rect_popup_cancelar.collidepoint(posicao_mouse) if self.rect_popup_cancelar else False
                self.hover_popup_fechar = self.rect_popup_fechar.collidepoint(posicao_mouse) if self.rect_popup_fechar else False
                return

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
            if self.pop_up_aberto:
                if self.rect_popup_confirmar and self.rect_popup_confirmar.collidepoint(posicao_mouse):
                    self.fechar_pop_up()
                    self.confirmar_escolha()
                    return
                elif (self.rect_popup_cancelar and self.rect_popup_cancelar.collidepoint(posicao_mouse)) or \
                     (self.rect_popup_fechar and self.rect_popup_fechar.collidepoint(posicao_mouse)):
                    self.fechar_pop_up()
                    return
                elif self.rect_popup and not self.rect_popup.collidepoint(posicao_mouse):
                    self.fechar_pop_up()
                    return
                return

            if self.pode_fechar and self.rect_botao_x.collidepoint(posicao_mouse):
                self._tocar_sfx("ui_voltar")
                self.opcao_cancelada_id = self.id_cancelamento_no
                self.manager.cancelar_escolha()
                self._sincronizar_com_manager()
                return
                
            total_paginas = (len(self.opcoes_disponiveis) - 1) // self.opcoes_por_pagina + 1
            if total_paginas > 1:
                if self.rect_seta_esq.collidepoint(posicao_mouse) and self.pagina_atual > 0:
                    self._tocar_sfx("ui_cursor")
                    self.pagina_atual -= 1
                    return
                if self.rect_seta_dir.collidepoint(posicao_mouse) and self.pagina_atual < total_paginas - 1:
                    self._tocar_sfx("ui_cursor")
                    self.pagina_atual += 1
                    return
                    
            for i, rect in enumerate(self.rects_opcoes):
                if rect.collidepoint(posicao_mouse):
                    idx_global = (self.pagina_atual * self.opcoes_por_pagina) + i
                    self.opcao_selecionada = idx_global
                    if idx_global < len(self.opcoes_disponiveis):
                        opt = self.opcoes_disponiveis[idx_global]
                        if self.opcao_eh_longa(opt, idx_global):
                            self.abrir_pop_up(opt, idx_global)
                            return
                    self.confirmar_escolha()
                    break
        else:
            self.proximo_texto()

    def atualizar(self):
        if not self.ativo or self.em_escolha: return
        if self.caractere_atual < self.tamanho_total:
            caractere_ant = int(self.caractere_atual)
            self.caractere_atual += self.velocidade_texto
            if self.caractere_atual > self.tamanho_total:
                self.caractere_atual = self.tamanho_total
            
            # Feedback sonoro rítmico suave de máquina de escrever a cada 3 caracteres
            if int(self.caractere_atual) // 3 > caractere_ant // 3:
                self._tocar_sfx("ui_dialogo", volume_extra=0.3)

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
        autor_limpo = autor.lower() if autor else ""
        if "halia" in autor_limpo:
            return NOME_HALIA
        elif "sylvan" in autor_limpo or "grave" in autor_limpo:
            return (245, 140, 65)  # Laranja forja / calor
        elif "roland" in autor_limpo or "paladino" in autor_limpo:
            return (235, 195, 80)  # Ouro nobre / paladino
        elif "caelen" in autor_limpo or "clérigo" in autor_limpo or "clerigo" in autor_limpo:
            return (165, 210, 255) # Azul celeste / clérigo
        elif "aldous" in autor_limpo or "ancião" in autor_limpo or "anciao" in autor_limpo or "líder" in autor_limpo:
            return (220, 195, 130) # Ouro rústico / líder sábio
        elif "elara" in autor_limpo or "curandeira" in autor_limpo or "botânica" in autor_limpo:
            return (130, 215, 160) # Verde menta / curandeira
        elif "torvald" in autor_limpo or "ferreiro" in autor_limpo:
            return (235, 120, 50)  # Laranja brasas / forja
        elif "doran" in autor_limpo or "guarda" in autor_limpo or "cavaleiro" in autor_limpo:
            return (200, 215, 230) # Aço polido / guarda nobre
        elif "maldição" in autor_limpo or "maldicao" in autor_limpo:
            return NOME_MALDICAO
        elif autor in ["Sistema", "Narrador"]:
            return TXT_SISTEMA_NARRADOR
        elif autor in ["Pensamento", "Pensamento Interno"]:
            return TXT_PENSAMENTO_INTERNO
        return MARFIM_OFFWHITE

    def _obter_retrato_autor(self, autor):
        """Retorna o retrato canônico do interlocutor ou None."""
        if not autor:
            return None
        if autor in self.retratos and self.retratos[autor] is not None:
            return self.retratos[autor]
        autor_low = autor.lower()
        if "halia" in autor_low:
            return self.retratos.get("Halia")
        if "sylvan" in autor_low or "grave" in autor_low:
            return self.retratos.get("Sylvan")
        if "roland" in autor_low or "paladino" in autor_low:
            return self.retratos.get("Roland")
        if "caelen" in autor_low or "clérigo" in autor_low or "clerigo" in autor_low:
            return self.retratos.get("Caelen")
        if "aldous" in autor_low or "ancião" in autor_low or "anciao" in autor_low or "líder" in autor_low:
            return self.retratos.get("Aldous")
        if "elara" in autor_low or "curandeira" in autor_low:
            return self.retratos.get("Elara")
        if "torvald" in autor_low or "ferreiro" in autor_low:
            return self.retratos.get("Torvald")
        if "doran" in autor_low or "guarda" in autor_low:
            return self.retratos.get("Roland")
        if "torvin" in autor_low:
            return self.retratos.get("Torvin")
        if "carroceiro" in autor_low:
            return self.retratos.get("Carroceiro")
        return None

    def _desenhar_texto_corrido(self, tela):
        dados = self.dados_atuais or {}
        autor = dados.get("autor", "Narrador")
        tem_retrato = bool(autor and autor not in ["Sistema", "Narrador"])

        largura_tela = tela.get_width()
        altura_tela = tela.get_height()

        largura_caixa = min(960, largura_tela - 80)
        
        num_linhas = max(1, len(self.linhas_completas))
        if num_linhas <= 3:
            altura_caixa = 175
        elif num_linhas == 4:
            altura_caixa = 195
        else:
            altura_caixa = min(225, 195 + (num_linhas - 4) * 24)

        x_caixa = (largura_tela - largura_caixa) // 2
        y_caixa = altura_tela - altura_caixa - 22

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
            
            sprite_retrato = self._obter_retrato_autor(autor)
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
            tela.blit(r_nome, (pos_x_texto, y_caixa + 16))
            y_linha = y_caixa + 50
        else:
            y_linha = y_caixa + 24

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
            y_linha += 24

        # 5. Indicador de Avanço Estático e Limpo (com margem de respiro garantida)
        if self.caractere_atual >= self.tamanho_total:
            txt_avanco = self.fonte_rodape.render("[ ENTER ou Clique para avançar ]", True, UI_TEXTO_APAGADO)
            pos_x_av = x_caixa + largura_caixa - txt_avanco.get_width() - 24
            pos_y_av = y_caixa + altura_caixa - 22
            tela.blit(txt_avanco, (pos_x_av, pos_y_av))

    def _desenhar_escolhas(self, tela):
        largura_tela = tela.get_width()
        altura_tela = tela.get_height()

        largura_card = min(960, largura_tela - 80)
        x_card = (largura_tela - largura_card) // 2

        # 1. Cabeçalho Superior da Escolha Dinâmico com quebra de linha anti-overflow
        texto_cabecalho = getattr(self, "cabecalho_escolha", "Sobre o que deseja conversar?")
        largura_disp_cab = largura_card - (80 if self.pode_fechar else 48)
        linhas_cabecalho = quebrar_texto_em_linhas(texto_cabecalho, self.fonte_titulo_escolha, largura_disp_cab)
        if not linhas_cabecalho:
            linhas_cabecalho = [texto_cabecalho]

        extra_h_cab = max(0, (len(linhas_cabecalho) - 1) * 22)
        altura_card = 215 + extra_h_cab
        y_card = altura_tela - altura_card - 25

        rect_card = pygame.Rect(x_card, y_card, largura_card, altura_card)
        desenhar_painel_padrao(tela, rect_card, cor_fundo=CARVAO_PROFUNDO, cor_borda=CINZA_LINHO, alpha=250)

        # Moldura interna decorativa
        rect_interno = rect_card.inflate(-8, -8)
        pygame.draw.rect(tela, (24, 24, 30), rect_interno, 1, border_radius=2)

        # Renderizar cada linha do cabeçalho sem vazar
        y_linha_cab = y_card + 12
        for l_cab in linhas_cabecalho:
            r_cabecalho = self.fonte_titulo_escolha.render(l_cab, True, MARFIM_OFFWHITE)
            tela.blit(r_cabecalho, (x_card + 22, y_linha_cab))
            y_linha_cab += 22

        # Divisória do Cabeçalho
        y_divisoria = y_linha_cab + 4
        pygame.draw.line(tela, CINZA_ARDOSIA, (x_card + 20, y_divisoria), (x_card + largura_card - 20, y_divisoria), 1)

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
        y_opcoes_inicio = y_divisoria + 10

        for i, opcao in enumerate(opcoes_pagina):
            idx_global = inicio + i
            esta_sel = (idx_global == self.opcao_selecionada)
            
            col = i % 2
            row = i // 2
            
            x_opt = x_card + 20 + col * (w_coluna + 16)
            y_opt = y_opcoes_inicio + row * (h_opcao + 8)
            rect_opt = pygame.Rect(x_opt, y_opt, w_coluna, h_opcao)
            novos_rects.append(rect_opt)
            
            if esta_sel:
                pygame.draw.rect(tela, AZUL_HOVER_BG, rect_opt, border_radius=2)
                pygame.draw.rect(tela, AZUL_HOVER_MENU, rect_opt, 1, border_radius=2)
                cor_txt = AZUL_HOVER_MENU
                prefixo = f"> {idx_global + 1}. "
            else:
                pygame.draw.rect(tela, (18, 18, 22), rect_opt, border_radius=2)
                pygame.draw.rect(tela, CINZA_ARDOSIA, rect_opt, 1, border_radius=2)
                cor_txt = CINZA_LINHO
                prefixo = f"  {idx_global + 1}. "

            texto_bruto = opcao.get('texto', '')
            texto_opcao = f"{prefixo}{texto_bruto}"
            eh_longa = self.opcao_eh_longa(opcao, idx_global)
            
            # Garante que o texto caiba na coluna sem overflow
            largura_disponivel = w_coluna - (42 if eh_longa else 20)
            if self.fonte_opcao.size(texto_opcao)[0] > largura_disponivel:
                while len(texto_bruto) > 3 and self.fonte_opcao.size(f"{prefixo}{texto_bruto}...")[0] > largura_disponivel:
                    texto_bruto = texto_bruto[:-1]
                texto_opcao = f"{prefixo}{texto_bruto}..."

            r_opt = self.fonte_opcao.render(texto_opcao, True, cor_txt)
            tela.blit(r_opt, (rect_opt.x + 10, rect_opt.centery - r_opt.get_height() // 2))

            if eh_longa:
                cor_ico = AZUL_HOVER_MENU if esta_sel else CINZA_LINHO
                r_ico = self.fonte_rodape.render("[+]", True, cor_ico)
                tela.blit(r_ico, (rect_opt.right - 26, rect_opt.centery - r_ico.get_height() // 2))

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
            y_pag = y_card + altura_card - 36
            
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

        # 5. Pop-up Modal de Leitura Integral de Opções Longas
        if self.pop_up_aberto and self.pop_up_opcao:
            self._desenhar_pop_up(tela)

    def _desenhar_pop_up(self, tela):
        """Renderiza o modal de leitura integral com texto completo e botões de decisão deliberada."""
        largura_tela = tela.get_width()
        altura_tela = tela.get_height()

        # Dim sutil de fundo para focar a atenção do jogador
        overlay = pygame.Surface((largura_tela, altura_tela), pygame.SRCALPHA)
        overlay.fill((8, 8, 12, 175))
        tela.blit(overlay, (0, 0))

        largura_popup = min(840, largura_tela - 80)
        altura_popup = 225
        x_popup = (largura_tela - largura_popup) // 2
        y_popup = altura_tela - altura_popup - 30

        rect_popup = pygame.Rect(x_popup, y_popup, largura_popup, altura_popup)
        self.rect_popup = rect_popup

        # Moldura estética dark fantasy editorial
        desenhar_painel_padrao(tela, rect_popup, cor_fundo=CARVAO_PROFUNDO, cor_borda=AZUL_HOVER_MENU, alpha=252)
        rect_interno = rect_popup.inflate(-8, -8)
        pygame.draw.rect(tela, (28, 28, 36), rect_interno, 1, border_radius=2)

        # Cabeçalho do Pop-up
        titulo_popup = "RESPOSTA COMPLETA DE HALIA"
        r_titulo = self.fonte_titulo_escolha.render(titulo_popup, True, AZUL_HOVER_MENU)
        tela.blit(r_titulo, (x_popup + 22, y_popup + 14))

        # Divisória fina de cabeçalho
        pygame.draw.line(tela, CINZA_ARDOSIA, (x_popup + 20, y_popup + 40), (x_popup + largura_popup - 20, y_popup + 40), 1)

        # Botão Fechar [X] no topo direito
        self.rect_popup_fechar = pygame.Rect(x_popup + largura_popup - 36, y_popup + 10, 24, 24)
        cor_fechar = BOTAO_FECHAR_HOVER if self.hover_popup_fechar else (32, 32, 40)
        borda_fechar = AZUL_HOVER_MENU if self.hover_popup_fechar else CINZA_LINHO
        pygame.draw.rect(tela, cor_fechar, self.rect_popup_fechar, border_radius=2)
        pygame.draw.rect(tela, borda_fechar, self.rect_popup_fechar, 1, border_radius=2)
        txt_x = self.fonte_rodape.render("X", True, BRANCO)
        tela.blit(txt_x, txt_x.get_rect(center=self.rect_popup_fechar.center))

        # Texto integral quebrado em linhas legíveis
        texto_completo = self.pop_up_opcao.get("texto", "") if self.pop_up_opcao else ""
        largura_texto_disponivel = largura_popup - 48
        linhas_texto = quebrar_texto_em_linhas(texto_completo, self.fonte_texto, largura_texto_disponivel)

        y_texto = y_popup + 52
        for linha in linhas_texto[:4]:
            r_linha = self.fonte_texto.render(linha, True, MARFIM_OFFWHITE)
            tela.blit(r_linha, (x_popup + 24, y_texto))
            y_texto += 26

        # Botões de Ação na base do Pop-up
        h_btn = 34
        y_botoes = y_popup + altura_popup - h_btn - 14

        # 1. Botão Confirmar [ ✦ Dizer Resposta  (ENTER) ]
        w_btn_conf = 240
        x_btn_conf = x_popup + largura_popup - w_btn_conf - 22
        self.rect_popup_confirmar = pygame.Rect(x_btn_conf, y_botoes, w_btn_conf, h_btn)
        
        cor_bg_conf = AZUL_HOVER_BG if self.hover_popup_confirmar else (24, 30, 42)
        cor_borda_conf = AZUL_HOVER_MENU if self.hover_popup_confirmar else CINZA_LINHO
        cor_txt_conf = AZUL_HOVER_MENU if self.hover_popup_confirmar else MARFIM_OFFWHITE
        
        pygame.draw.rect(tela, cor_bg_conf, self.rect_popup_confirmar, border_radius=2)
        pygame.draw.rect(tela, cor_borda_conf, self.rect_popup_confirmar, 1, border_radius=2)
        r_conf = self.fonte_opcao.render("Dizer Resposta  [ENTER]", True, cor_txt_conf)
        tela.blit(r_conf, r_conf.get_rect(center=self.rect_popup_confirmar.center))

        # 2. Botão Cancelar [ Voltar às Opções  (ESC) ]
        w_btn_canc = 200
        x_btn_canc = x_btn_conf - w_btn_canc - 14
        self.rect_popup_cancelar = pygame.Rect(x_btn_canc, y_botoes, w_btn_canc, h_btn)

        cor_bg_canc = (35, 35, 45) if self.hover_popup_cancelar else (20, 20, 26)
        cor_borda_canc = AZUL_HOVER_MENU if self.hover_popup_cancelar else CINZA_ARDOSIA
        cor_txt_canc = AZUL_HOVER_MENU if self.hover_popup_cancelar else CINZA_LINHO

        pygame.draw.rect(tela, cor_bg_canc, self.rect_popup_cancelar, border_radius=2)
        pygame.draw.rect(tela, cor_borda_canc, self.rect_popup_cancelar, 1, border_radius=2)
        r_canc = self.fonte_opcao.render("Voltar às Opções  [ESC]", True, cor_txt_canc)
        tela.blit(r_canc, r_canc.get_rect(center=self.rect_popup_cancelar.center))