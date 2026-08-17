# src/ui/dialogue_box.py
import pygame
from src.utils.colors import (
    UI_FUNDO_PADRAO, BRANCO, CINZA_CLARO, UI_TEXTO_APAGADO, 
    TXT_SISTEMA_NARRADOR, TXT_PENSAMENTO_INTERNO, 
    NOME_HALIA, NOME_MALDICAO, UI_TEXTO_DESTAQUE,
    BOTAO_FECHAR_NORMAL, BOTAO_FECHAR_HOVER
)

class DialogueBox:
    def __init__(self, largura_tela):
        self.fonte_texto = pygame.font.Font(None, 32)
        self.fonte_nome = pygame.font.Font(None, 36) 
        
        self.largura_maxima = largura_tela - 120 
        self.ativo = False
        self.dialogos = [] 
        self.indice_atual = 0
        
        # --- MÁQUINA DE ESCREVER ---
        self.texto_completo = ""
        self.linhas_completas = []
        self.tamanho_total = 0
        self.caractere_atual = 0
        self.velocidade_texto = 1.0 
        self.tempo_ultimo_input = 0

        # --- SISTEMA DE ESCOLHAS ---
        self.em_escolha = False
        self.opcoes_disponiveis = []
        self.opcao_selecionada = 0
        self.historico_escolhas = set() 
        self.rects_opcoes = []
        self.pagina_escolha = 0
        self.itens_por_pagina = 4

        # -- BOTÃO DE FECHAR --
        self.rect_botao_x = pygame.Rect(0, 0, 30, 30) 
        self.botao_x_hover = False    
        
        # -- PAGINAÇÃO --
        self.pagina_atual = 0
        self.opcoes_por_pagina = 4
        self.rect_seta_esq = pygame.Rect(-100, -100, 30, 30)
        self.rect_seta_dir = pygame.Rect(-100, -100, 30, 30)
        self.hover_esq = False
        self.hover_dir = False
        
        # -- CONTROLE DE CANCELAMENTO --
        self.pode_fechar = False
        self.resultado_fechar = []
        self.id_cancelamento_no = None
        self.opcao_cancelada_id = None  

    def iniciar_dialogo(self, lista_dialogos):
        self.dialogos = lista_dialogos
        self.indice_atual = 0
        self.ativo = True
        
        # RESET COMPLETO DE SEGURANÇA
        self.em_escolha = False
        self.texto_completo = ""
        self.linhas_completas = []
        self.tamanho_total = 0
        self.caractere_atual = 0
        self.tempo_ultimo_input = pygame.time.get_ticks() 
        
        self._configurar_texto_atual()

    def _configurar_texto_atual(self):
        if self.indice_atual < len(self.dialogos):
            dados_atuais = self.dialogos[self.indice_atual]
            
            if "escolhas" in dados_atuais:
                self.em_escolha = True
                
                # Lê as regras de fechamento e cancelamento
                self.pode_fechar = dados_atuais.get("pode_fechar", False)
                self.resultado_fechar = dados_atuais.get("resultado_fechar", [])
                self.id_cancelamento_no = dados_atuais.get("id_cancelamento", None)
                self.opcao_cancelada_id = None 
                self.pagina_atual = 0
                self.pagina_escolha = 0
                
                self.opcoes_disponiveis = [
                    opt for opt in dados_atuais["escolhas"] 
                    if opt.get("id") not in self.historico_escolhas
                ]
                self.opcao_selecionada = 0
                self.texto_completo = ""
                self.linhas_completas = []
                self.tamanho_total = 0
                self.caractere_atual = 0
                self.rects_opcoes = [] 
            else:
                self.em_escolha = False
                self.pode_fechar = False 
                self.texto_completo = dados_atuais.get("texto", "")
                self.linhas_completas = self._quebrar_texto(self.texto_completo, self.fonte_texto, self.largura_maxima)
                self.tamanho_total = len(self.texto_completo)
                self.caractere_atual = 0

    def _quebrar_texto(self, texto, fonte, largura_maxima):
        palavras = texto.split(' ')
        linhas = []
        linha_atual = ""
        for palavra in palavras:
            teste_linha = linha_atual + palavra + " "
            if fonte.size(teste_linha)[0] <= largura_maxima:
                linha_atual = teste_linha
            else:
                if linha_atual: linhas.append(linha_atual)
                linha_atual = palavra + " "
        if linha_atual: linhas.append(linha_atual)
        return linhas

    def proximo_texto(self):
        if not self.ativo: return

        tempo_atual = pygame.time.get_ticks()
        if tempo_atual - self.tempo_ultimo_input < 300: return 
        self.tempo_ultimo_input = tempo_atual

        if self.em_escolha:
            self.confirmar_escolha()
            return

        if self.caractere_atual < self.tamanho_total:
            self.caractere_atual = self.tamanho_total
        else:
            self.indice_atual += 1
            if self.indice_atual >= len(self.dialogos):
                self.ativo = False 
            else:
                self._configurar_texto_atual()

    def confirmar_escolha(self):
        if self.opcoes_disponiveis:
            escolha = self.opcoes_disponiveis[self.opcao_selecionada]
            
            if "id" in escolha and escolha["id"] != "prosseguir" and not escolha.get("repetivel", False):
                self.historico_escolhas.add(escolha["id"])
            
            self.em_escolha = False 
            self.iniciar_dialogo(escolha["resultado"])

    def controlar_menu_escolhas(self, tecla):
        if not self.ativo or not self.em_escolha or not self.opcoes_disponiveis: return
        
        total_opcoes = len(self.opcoes_disponiveis)
        total_paginas = (total_opcoes - 1) // self.opcoes_por_pagina

        if tecla == pygame.K_UP:
            if self.opcao_selecionada > 0:
                self.opcao_selecionada -= 1
                # Se subir e sair da página atual, volta uma página
                if self.opcao_selecionada < self.pagina_atual * self.opcoes_por_pagina:
                    if self.pagina_atual > 0:
                        self.pagina_atual -= 1
            else:
                # Volta para o final de tudo se estiver no topo absoluto
                self.opcao_selecionada = total_opcoes - 1
                self.pagina_atual = total_paginas

        elif tecla == pygame.K_DOWN:
            if self.opcao_selecionada < total_opcoes - 1:
                self.opcao_selecionada += 1
                # Se descer e passar da página atual, avança uma página
                if self.opcao_selecionada >= (self.pagina_atual + 1) * self.opcoes_por_pagina:
                    if self.pagina_atual < total_paginas:
                        self.pagina_atual += 1
            else:
                # Volta para o topo absoluto
                self.opcao_selecionada = 0
                self.pagina_atual = 0

    def atualizar_mouse(self, posicao_mouse):
        if not self.ativo or not self.em_escolha: return
        
        # Verifica o [X]
        if self.pode_fechar:
            self.botao_x_hover = self.rect_botao_x.collidepoint(posicao_mouse)
            
        # Verifica Paginação (as rects estão posicionadas no desenhar, se não existirem ficam fora da tela)
        self.hover_esq = self.rect_seta_esq.collidepoint(posicao_mouse)
        self.hover_dir = self.rect_seta_dir.collidepoint(posicao_mouse)
            
        for i, rect in enumerate(self.rects_opcoes):
            if rect.collidepoint(posicao_mouse):
                self.opcao_selecionada = (self.pagina_atual * self.opcoes_por_pagina) + i
                break

    def clicar_mouse(self, posicao_mouse):
        if not self.ativo or not self.em_escolha: return
        
        # Saída limpa ou de cancelamento pelo [X]
        if self.pode_fechar and self.rect_botao_x.collidepoint(posicao_mouse):
            self.em_escolha = False
            self.opcao_cancelada_id = self.id_cancelamento_no # Avisa o loop principal
            if self.resultado_fechar:
                self.iniciar_dialogo(self.resultado_fechar)
            else:
                self.ativo = False
                self.opcoes_disponiveis = []
            return
            
        # Clique na Paginação
        total_paginas = (len(self.opcoes_disponiveis) - 1) // self.opcoes_por_pagina + 1
        if total_paginas > 1:
            if self.rect_seta_esq.collidepoint(posicao_mouse) and self.pagina_atual > 0:
                self.pagina_atual -= 1
                return
            if self.rect_seta_dir.collidepoint(posicao_mouse) and self.pagina_atual < total_paginas - 1:
                self.pagina_atual += 1
                return
                
        # Clique na Opção de Texto
        for i, rect in enumerate(self.rects_opcoes):
            if rect.collidepoint(posicao_mouse):
                self.opcao_selecionada = (self.pagina_atual * self.opcoes_por_pagina) + i
                self.confirmar_escolha()
                break

    def atualizar(self):
        if not self.ativo or self.em_escolha: return
        if self.caractere_atual < self.tamanho_total:
            self.caractere_atual += self.velocidade_texto
            if self.caractere_atual > self.tamanho_total:
                self.caractere_atual = self.tamanho_total

    def desenhar(self, tela):
        if not self.ativo or self.indice_atual >= len(self.dialogos) or self.indice_atual < 0:
            self.ativo = False 
            return

        largura = tela.get_width() - 80
        altura = 160 
        x = 40
        y = tela.get_height() - altura - 30

        pygame.draw.rect(tela, UI_FUNDO_PADRAO, (x, y, largura, altura))
        pygame.draw.rect(tela, CINZA_CLARO, (x, y, largura, altura), 2)

        if self.em_escolha:
            self._desenhar_escolhas(tela, x, y, largura, altura)
        else:
            self._desenhar_texto_corrido(tela, x, y, largura, altura)

    def _desenhar_escolhas(self, tela, x, y, largura, altura):
        render_instrucao = self.fonte_nome.render("Respostas disponíveis:", True, UI_TEXTO_APAGADO)
        tela.blit(render_instrucao, (x + 20, y + 15))

        if self.pode_fechar:
            self.rect_botao_x.x = x + largura - 40
            self.rect_botao_x.y = y + 10
            
            cor_atual = BOTAO_FECHAR_HOVER if self.botao_x_hover else BOTAO_FECHAR_NORMAL
            pygame.draw.rect(tela, cor_atual, self.rect_botao_x)
            pygame.draw.rect(tela, BRANCO, self.rect_botao_x, 2)
            
            texto_x = self.fonte_texto.render("X", True, BRANCO)
            pos_texto_x = texto_x.get_rect(center=self.rect_botao_x.center)
            tela.blit(texto_x, pos_texto_x)
        
        novos_rects = []
        
        # --- PAGINAÇÃO (Fatiamento das opções) ---
        inicio = self.pagina_atual * self.opcoes_por_pagina
        fim = min(inicio + self.opcoes_por_pagina, len(self.opcoes_disponiveis))
        opcoes_pagina = self.opcoes_disponiveis[inicio:fim]
        
        for i, opcao in enumerate(opcoes_pagina):
            texto_menu = opcao["texto"]
            indice_global = inicio + i
            
            if indice_global == self.opcao_selecionada:
                cor_opt = TXT_SISTEMA_NARRADOR 
                texto_completo_opt = f"> {texto_menu}"
            else:
                cor_opt = CINZA_CLARO 
                texto_completo_opt = f"  {texto_menu}"
            
            coluna = i % 2 
            linha_idx = i // 2
            
            x_coluna = x + 20 if coluna == 0 else x + (largura // 2) + 10
            y_linha_pos = y + 55 + (linha_idx * 45) 
            
            linhas_opcao = self._quebrar_texto(texto_completo_opt, self.fonte_texto, (largura // 2) - 40)
            
            y_bloco_atual = y_linha_pos
            for linha in linhas_opcao:
                render_opt = self.fonte_texto.render(linha, True, cor_opt)
                tela.blit(render_opt, (x_coluna, y_bloco_atual))
                y_bloco_atual += 22 
            
            altura_bloco = max(35, y_bloco_atual - y_linha_pos)
            hitbox_opcao = pygame.Rect(x_coluna, y_linha_pos, (largura // 2) - 20, altura_bloco)
            novos_rects.append(hitbox_opcao)
            
        self.rects_opcoes = novos_rects

        # --- DESENHO DAS SETAS DE PAGINAÇÃO DISCRETAS (< >) ---
        total_paginas = (len(self.opcoes_disponiveis) - 1) // self.opcoes_por_pagina + 1
        
        # Esconde as áreas de clique por padrão (tira da tela)
        self.rect_seta_esq.topleft = (-100, -100)
        self.rect_seta_dir.topleft = (-100, -100)

        if total_paginas > 1:
            pos_y_setas = y + altura - 40 # Canto inferior direito

            # Seta Voltar (Aparece só se houver páginas anteriores)
            if self.pagina_atual > 0:
                self.rect_seta_esq.topleft = (x + largura - 75, pos_y_setas) # Puxei 5px para a esquerda
                cor_esq = BRANCO if self.hover_esq else UI_TEXTO_APAGADO
                # Usando fonte_nome (tamanho 36) em vez de fonte_texto (32) para ficar ligeiramente maior
                seta_esq_txt = self.fonte_nome.render("<", True, cor_esq) 
                tela.blit(seta_esq_txt, (self.rect_seta_esq.x + 8, self.rect_seta_esq.y)) # Subi 5px para centralizar

            # Seta Avançar (Aparece só se houver páginas seguintes)
            if self.pagina_atual < total_paginas - 1:
                self.rect_seta_dir.topleft = (x + largura - 35, pos_y_setas)
                cor_dir = BRANCO if self.hover_dir else UI_TEXTO_APAGADO
                seta_dir_txt = self.fonte_nome.render(">", True, cor_dir)
                tela.blit(seta_dir_txt, (self.rect_seta_dir.x + 8, self.rect_seta_dir.y))

    def _desenhar_texto_corrido(self, tela, x, y, largura, altura):
        autor = self.dialogos[self.indice_atual].get("autor", "")
        cor_nome, cor_texto, mostrar_nome = BRANCO, UI_TEXTO_DESTAQUE, True

        if autor in ["Sistema", "Narrador"]:
            cor_texto, mostrar_nome = TXT_SISTEMA_NARRADOR, False      
        elif autor == "Pensamento":
            cor_texto, mostrar_nome = TXT_PENSAMENTO_INTERNO, False        
        elif autor == "Halia":
            cor_nome = NOME_HALIA
        elif autor == "Maldição":
            cor_nome = NOME_MALDICAO

        if mostrar_nome and autor:
            render_nome = self.fonte_nome.render(autor, True, cor_nome)
            tela.blit(render_nome, (x + 20, y + 10))
            pos_y_texto = y + 50 
        else:
            pos_y_texto = y + 25 

        caracteres_permitidos = int(self.caractere_atual)
        y_linha = pos_y_texto
        for linha in self.linhas_completas:
            if caracteres_permitidos <= 0: break
            tamanho_linha = len(linha)
            if caracteres_permitidos >= tamanho_linha:
                texto_render = linha
                caracteres_permitidos -= tamanho_linha
            else:
                texto_render = linha[:caracteres_permitidos]
                caracteres_permitidos = 0
            render_texto = self.fonte_texto.render(texto_render, True, cor_texto)
            tela.blit(render_texto, (x + 20, y_linha))
            y_linha += 30
        
        if self.caractere_atual >= self.tamanho_total:
            avancar = pygame.font.Font(None, 24).render("Pressione [ENTER]", True, UI_TEXTO_APAGADO)
            tela.blit(avancar, (x + largura - 180, y + altura - 30))