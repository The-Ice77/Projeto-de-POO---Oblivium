# src/ui/dialogue_box.py
import pygame
from src.ui.ui_utils import quebrar_texto_em_linhas, desenhar_painel_padrao
from src.utils.colors import (
    BRANCO, CINZA_LINHO, CINZA_ARDOSIA,
    UI_TEXTO_APAGADO,
    BOTAO_FECHAR_HOVER,
    CARVAO_PROFUNDO, MARFIM_OFFWHITE,
    AZUL_HOVER_MENU, AZUL_HOVER_BG
)
from src.utils.resource_manager import ResourceManager
from src.mechanics.dialogue_manager import DialogueManager
from src.core.audio_manager import AudioManager
from src.ui.dialogue_portraits import (
    DialoguePortraitCatalog,
    NOMES_TECLAS_PT,
    formatar_marcadores_controles,
    obter_nome_tecla_legivel,
)


class DialogueBox:
    """
    Caixa de Diálogo e Sistema de Escolhas de Oblivium (Visual + POO):
    - Conectada ao DialogueManager (leitura de JSON estruturado em nós)
    - Fundo escuro em Carvão Profundo com contorno sutil de 1px
    - Layout tipográfico uniforme sem retratos laterais, preservando nome e cor do autor
    - Sistema de Escolhas lado a lado (grade 2 colunas) com cabeçalho dinâmico
    - Destaques visuais e hover no padrão azul clarinho do menu inicial
    - Totalmente retrocompatível com chamadas legadas de listas de falas
    """
    def __init__(self, largura_tela, manager=None, game=None):
        self.game = game
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
        self.MAX_LINHAS_POR_PAGINA = 6
        self.texto_completo = ""
        self.linhas_completas = []
        self.paginas_texto = [[]]
        self.indice_pagina_texto = 0
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

        # Retratos removidos por R02: diálogos exibem apenas nome/cor do autor e texto uniforme
        self.retratos = {}

    def _inicializar_retratos_companheiros(self):
        """Mantido por compatibilidade; retratos foram desativados em R02."""
        return

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
            self.manager.finalizar(limpar_eventos=True)
            self._sincronizar_com_manager()
            return

        self.ativo = True
        self.opcao_cancelada_id = None
        self.tempo_ultimo_input = pygame.time.get_ticks()
        self._sincronizar_com_manager()

    def formatar_texto_controles(self, texto):
        """Substitui marcadores dinâmicos de controles no texto com base em self.game."""
        return formatar_marcadores_controles(texto, game=self.game)

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
        self.dados_atuais = dict(no)

        tipo_no = no.get("tipo", "fala")
        if tipo_no == "escolha" or "escolhas" in no:
            self.em_escolha = True
            self.pode_fechar = no.get("pode_fechar", False)
            self.id_cancelamento_no = no.get("id_cancelamento", None)
            cabecalho_bruto = no.get("cabecalho", no.get("titulo", "Sobre o que deseja conversar?"))
            self.cabecalho_escolha = self.formatar_texto_controles(cabecalho_bruto)
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
            self.texto_completo = self.formatar_texto_controles(no.get("texto", ""))
            self.dados_atuais["texto"] = self.texto_completo

            autor = no.get("autor", "Narrador")
            layout = self._calcular_layout_texto(self.largura_tela, autor=autor, num_linhas=1)
            self.linhas_completas = quebrar_texto_em_linhas(
                self.texto_completo, self.fonte_texto, layout["largura_util"]
            )
            max_linhas = max(1, int(getattr(self, "MAX_LINHAS_POR_PAGINA", 6)))
            if self.linhas_completas:
                self.paginas_texto = [
                    self.linhas_completas[i : i + max_linhas]
                    for i in range(0, len(self.linhas_completas), max_linhas)
                ]
            else:
                self.paginas_texto = [[]]
            self.indice_pagina_texto = 0
            self.tamanho_total = sum(len(l) for l in self.linhas_pagina_atual)
            self.caractere_atual = 0

    @property
    def total_paginas_texto(self):
        return max(1, len(getattr(self, "paginas_texto", [[]])))

    @property
    def linhas_pagina_atual(self):
        paginas = getattr(self, "paginas_texto", [[]])
        if not paginas:
            return []
        idx = max(0, min(getattr(self, "indice_pagina_texto", 0), len(paginas) - 1))
        return paginas[idx]

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
        elif self.indice_pagina_texto + 1 < self.total_paginas_texto:
            self._tocar_sfx("ui_cursor")
            self.indice_pagina_texto += 1
            self.tamanho_total = sum(len(l) for l in self.linhas_pagina_atual)
            self.caractere_atual = 0
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

    def _largura_disponivel_opcao(self, largura_tela=None, com_icone=False):
        w_tela = largura_tela or getattr(self, "largura_tela", 1280)
        w_coluna = (min(960, w_tela - 80) - 56) // 2
        return max(120, w_coluna - (42 if com_icone else 20))

    def opcao_eh_longa(self, opcao, idx_global=0):
        """Verifica se uma opção excede a largura real útil da coluna de escolhas."""
        if not opcao or not isinstance(opcao, dict):
            return False
        texto = opcao.get("texto", "")
        if not texto:
            return False
        largura_disponivel = self._largura_disponivel_opcao(com_icone=False)
        largura_sel = self.fonte_opcao.size(f"> {idx_global + 1}. {texto}")[0]
        largura_nor = self.fonte_opcao.size(f"  {idx_global + 1}. {texto}")[0]
        return max(largura_sel, largura_nor) > largura_disponivel

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

    def atualizar(self, dt=None):
        if not self.ativo or self.em_escolha:
            return
        if dt is None:
            dt = getattr(self.game, "dt", 1.0 / 60.0) if self.game is not None else (1.0 / 60.0)
        if not isinstance(dt, (int, float)) or dt <= 0:
            dt = 1.0 / 60.0
        fator_quadro = float(dt) * 60.0
        if self.caractere_atual < self.tamanho_total:
            caractere_ant = int(self.caractere_atual)
            self.caractere_atual += self.velocidade_texto * fator_quadro
            if self.caractere_atual > self.tamanho_total:
                self.caractere_atual = self.tamanho_total
            
            # Feedback sonoro rítmico suave de máquina de escrever a cada 3 caracteres
            if int(self.caractere_atual) // 3 > caractere_ant // 3:
                self._tocar_sfx("ui_dialogo", volume_extra=0.45)

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
        return DialoguePortraitCatalog.obter_cor_autor(autor)

    def _obter_retrato_autor(self, autor):
        """Retratos desativados em R02; sempre retorna None."""
        return None

    def _calcular_layout_texto(self, largura_tela=None, altura_tela=None, autor=None, num_linhas=None):
        """Calcula dimensões únicas para quebra de texto, renderização e proteção de partículas."""
        w_tela = largura_tela or getattr(self, "largura_tela", 1280)
        h_tela = altura_tela or getattr(getattr(self, "game", None), "ALTURA", 720)
        largura_caixa = min(960, w_tela - 80)
        margem_x = 28
        largura_util = max(200, largura_caixa - (margem_x * 2))

        tem_nome_autor = bool(autor and autor not in ["Narrador", "Sistema"])
        y_inicio_rel = 50 if tem_nome_autor else 24
        altura_linha = 24
        qtd_linhas = max(1, len(self.linhas_pagina_atual) if num_linhas is None else int(num_linhas))
        altura_min = 165 if qtd_linhas <= 3 else 185
        altura_necessaria = y_inicio_rel + (qtd_linhas * altura_linha) + 42
        altura_caixa = min(max(altura_min, altura_necessaria), max(altura_min, h_tela - 80))

        x_caixa = (w_tela - largura_caixa) // 2
        y_caixa = h_tela - altura_caixa - 22
        return {
            "rect_caixa": pygame.Rect(x_caixa, y_caixa, largura_caixa, altura_caixa),
            "largura_caixa": largura_caixa,
            "altura_caixa": altura_caixa,
            "largura_util": largura_util,
            "x_caixa": x_caixa,
            "y_caixa": y_caixa,
            "pos_x_texto": x_caixa + margem_x,
            "y_inicio_texto": y_caixa + y_inicio_rel,
            "altura_linha": altura_linha,
        }

    def _calcular_layout_escolhas(self, largura_tela=None, altura_tela=None):
        """Calcula o card de escolhas e linhas do cabeçalho em fonte única."""
        w_tela = largura_tela or getattr(self, "largura_tela", 1280)
        h_tela = altura_tela or getattr(getattr(self, "game", None), "ALTURA", 720)
        largura_card = min(960, w_tela - 80)
        x_card = (w_tela - largura_card) // 2
        texto_cabecalho = getattr(self, "cabecalho_escolha", "Sobre o que deseja conversar?")
        largura_disp_cab = largura_card - (80 if self.pode_fechar else 48)
        linhas_cabecalho = quebrar_texto_em_linhas(texto_cabecalho, self.fonte_titulo_escolha, largura_disp_cab) or [texto_cabecalho]
        altura_card = 215 + max(0, (len(linhas_cabecalho) - 1) * 22)
        return pygame.Rect(x_card, h_tela - altura_card - 25, largura_card, altura_card), linhas_cabecalho

    def _obter_linhas_popup(self, largura_popup):
        texto_c = self.pop_up_opcao.get("texto", "") if self.pop_up_opcao else ""
        return quebrar_texto_em_linhas(texto_c, self.fonte_texto, max(120, largura_popup - 48))

    def _calcular_layout_popup(self, largura_tela=None, altura_tela=None):
        """Calcula o retângulo do modal de leitura completa expandindo para comportar todas as linhas."""
        w_tela = largura_tela or getattr(self, "largura_tela", 1280)
        h_tela = altura_tela or getattr(getattr(self, "game", None), "ALTURA", 720)
        largura_popup = min(840, w_tela - 80)
        linhas = self._obter_linhas_popup(largura_popup)
        altura_popup = min(h_tela - 60, max(225, 112 + len(linhas) * 26))
        return pygame.Rect((w_tela - largura_popup) // 2, max(30, h_tela - altura_popup - 30), largura_popup, altura_popup)

    def obter_areas_protegidas(self, largura_tela=None, altura_tela=None, margem=24):
        """Retorna os retângulos reais ocupados pela caixa, escolhas e popup com margem de segurança."""
        if not self.ativo:
            return []
        margem_px = max(0, int(margem))
        areas = []
        if self.em_escolha:
            rect_card, _ = self._calcular_layout_escolhas(largura_tela, altura_tela)
            areas.append(rect_card.inflate(margem_px * 2, margem_px * 2))
            if self.pop_up_aberto:
                rect_popup = self._calcular_layout_popup(largura_tela, altura_tela)
                areas.append(rect_popup.inflate(margem_px * 2, margem_px * 2))
        else:
            autor = (self.dados_atuais or {}).get("autor", "Narrador")
            layout = self._calcular_layout_texto(largura_tela, altura_tela, autor=autor)
            areas.append(layout["rect_caixa"].inflate(margem_px * 2, margem_px * 2))
        return areas

    def _desenhar_texto_corrido(self, tela):
        dados = self.dados_atuais or {}
        autor = dados.get("autor", "Narrador")
        linhas_visiveis = self.linhas_pagina_atual
        layout = self._calcular_layout_texto(
            tela.get_width(), tela.get_height(), autor=autor, num_linhas=len(linhas_visiveis)
        )
        rect_caixa = layout["rect_caixa"]
        x_caixa = layout["x_caixa"]
        y_caixa = layout["y_caixa"]
        largura_caixa = layout["largura_caixa"]
        altura_caixa = layout["altura_caixa"]
        pos_x_texto = layout["pos_x_texto"]
        y_linha = layout["y_inicio_texto"]
        altura_linha = layout["altura_linha"]

        # 1. Caixa Principal em Carvão Profundo
        desenhar_painel_padrao(tela, rect_caixa, cor_fundo=CARVAO_PROFUNDO, cor_borda=CINZA_LINHO, alpha=245)

        # Moldura interna decorativa
        rect_interno = rect_caixa.inflate(-8, -8)
        pygame.draw.rect(tela, (24, 24, 30), rect_interno, 1, border_radius=2)

        # 2. Nome do Autor (sem retratos ou iniciais laterais)
        cor_autor = self._obter_cor_autor(autor)
        if autor and autor not in ["Narrador", "Sistema"]:
            r_nome = self.fonte_nome.render(autor, True, cor_autor)
            tela.blit(r_nome, (pos_x_texto, y_caixa + 16))

        # 3. Texto corrido com Máquina de Escrever
        caracteres_permitidos = int(self.caractere_atual)
        for linha in linhas_visiveis:
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
            y_linha += altura_linha

        # 4. Indicador de Avanço Estático e Limpo (com margem de respiro garantida)
        if self.caractere_atual >= self.tamanho_total:
            if self.total_paginas_texto > 1:
                av_str = f"Página {self.indice_pagina_texto + 1}/{self.total_paginas_texto}  •  [ ENTER ou Clique para avançar ]"
            else:
                av_str = "[ ENTER ou Clique para avançar ]"
            txt_avanco = self.fonte_rodape.render(av_str, True, UI_TEXTO_APAGADO)
            pos_x_av = x_caixa + largura_caixa - txt_avanco.get_width() - 28
            pos_y_av = y_caixa + altura_caixa - 24
            tela.blit(txt_avanco, (pos_x_av, pos_y_av))

    def _desenhar_escolhas(self, tela):
        largura_tela = tela.get_width()
        altura_tela = tela.get_height()
        rect_card, linhas_cabecalho = self._calcular_layout_escolhas(largura_tela, altura_tela)
        x_card, y_card, largura_card, altura_card = rect_card.x, rect_card.y, rect_card.width, rect_card.height
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
            largura_disponivel = self._largura_disponivel_opcao(largura_tela, com_icone=eh_longa)
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

        rect_popup = self._calcular_layout_popup(largura_tela, altura_tela)
        x_popup, y_popup, largura_popup, altura_popup = (
            rect_popup.x,
            rect_popup.y,
            rect_popup.width,
            rect_popup.height,
        )
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

        # Texto integral quebrado em linhas legíveis sem corte artificial
        linhas_texto = self._obter_linhas_popup(largura_popup)
        y_texto, y_limite = y_popup + 52, y_popup + altura_popup - 54
        for linha in linhas_texto:
            if y_texto + 24 > y_limite:
                break
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
