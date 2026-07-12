# src/ui/dialogue_box.py
import pygame
from src.utils.colors import (
    UI_FUNDO_PADRAO, BRANCO, CINZA_CLARO, UI_TEXTO_APAGADO, 
    TXT_SISTEMA_NARRADOR, TXT_PENSAMENTO_INTERNO, 
    NOME_HALIA, NOME_MALDICAO, UI_TEXTO_DESTAQUE
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
        
        # Guarda as áreas retangulares de cada opção para colidir com o rato
        self.rects_opcoes = [] 

    def iniciar_dialogo(self, lista_dialogos):
        self.dialogos = lista_dialogos
        self.indice_atual = 0
        self.ativo = True
        
        # RESET COMPLETO DE SEGURANÇA PARA EVITAR TRAVAMENTOS
        self.em_escolha = False
        self.texto_completo = ""
        self.linhas_completas = []
        self.tamanho_total = 0
        self.caractere_atual = 0
        
        # Força o cooldown do teclado para evitar cliques fantasmas
        self.tempo_ultimo_input = pygame.time.get_ticks() 
        
        # Configura o primeiro frame/nó do novo diálogo
        self._configurar_texto_atual()

    def _configurar_texto_atual(self):
        if self.indice_atual < len(self.dialogos):
            dados_atuais = self.dialogos[self.indice_atual]
            
            if "escolhas" in dados_atuais:
                self.em_escolha = True
                self.opcoes_disponiveis = [
                    opt for opt in dados_atuais["escolhas"] 
                    if opt.get("id") not in self.historico_escolhas
                ]
                self.opcao_selecionada = 0
                self.texto_completo = ""
                self.linhas_completas = []
                self.tamanho_total = 0
                self.caractere_atual = 0
                self.rects_opcoes = [] # Limpa os retângulos antigos
            else:
                self.em_escolha = False
                self.texto_completo = dados_atuais.get("texto", "")
                self.linhas_completas = self._quebrar_texto(self.texto_completo, self.fonte_texto, self.largura_maxima)
                self.tamanho_total = len(self.texto_completo)
                self.caractere_atual = 0

    def _quebrar_texto(self, texto, fonte, largura_maxima):
        palavras = texto.split(' ')
        linhas = []
        linha_atual = ""
        for palabra in palavras:
            teste_linha = linha_atual + palabra + " "
            if fonte.size(teste_linha)[0] <= largura_maxima:
                linha_atual = teste_linha
            else:
                if linha_atual: linhas.append(linha_atual)
                linha_atual = palabra + " "
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
        """Executa a opção que estiver atualmente selecionada (via teclado ou rato)."""
        if self.opcoes_disponiveis:
            escolha = self.opcoes_disponiveis[self.opcao_selecionada]
            
            # VERIFICAÇÃO NOVA: Só guarda no histórico se NÃO tiver a flag 'repetivel'
            if "id" in escolha and escolha["id"] != "prosseguir" and not escolha.get("repetivel", False):
                self.historico_escolhas.add(escolha["id"])
            
            # Desativa o modo escolha ANTES de carregar a resposta
            self.em_escolha = False 
            self.iniciar_dialogo(escolha["resultado"])

    def controlar_menu_escolhas(self, tecla):
        if not self.ativo or not self.em_escolha or not self.opcoes_disponiveis:
            return
        if tecla == pygame.K_UP:
            self.opcao_selecionada = (self.opcao_selecionada - 1) % len(self.opcoes_disponiveis)
        elif tecla == pygame.K_DOWN:
            self.opcao_selecionada = (self.opcao_selecionada + 1) % len(self.opcoes_disponiveis)

    def atualizar_mouse(self, posicao_mouse):
        """Muda o índice selecionado se o rato passar por cima de uma opção."""
        if not self.ativo or not self.em_escolha: return
        
        for i, rect in enumerate(self.rects_opcoes):
            if rect.collidepoint(posicao_mouse):
                self.opcao_selecionada = i
                break

    def clicar_mouse(self, posicao_mouse):
        """Confirma a escolha se o jogador clicar com o rato em cima dela."""
        if not self.ativo or not self.em_escolha: return
        
        for i, rect in enumerate(self.rects_opcoes):
            if rect.collidepoint(posicao_mouse):
                self.opcao_selecionada = i
                self.confirmar_escolha()
                break

    def atualizar(self):
        if not self.ativo or self.em_escolha: return
        if self.caractere_atual < self.tamanho_total:
            self.caractere_atual += self.velocidade_texto
            if self.caractere_atual > self.tamanho_total:
                self.caractere_atual = self.tamanho_total

    def desenhar(self, tela):
        # PROTEÇÃO DE SEGURANÇA: Se não estiver ativo ou o índice estourar a lista, aborta o desenho
        if not self.ativo or self.indice_atual >= len(self.dialogos) or self.indice_atual < 0:
            self.ativo = False # Garante que ela se desative se algo deu errado
            return

        largura = tela.get_width() - 80
        altura = 160 
        x = 40
        y = tela.get_height() - altura - 30

        # Fundo e moldura externa (Usando UI_FUNDO_PADRAO e CINZA_CLARO)
        pygame.draw.rect(tela, UI_FUNDO_PADRAO, (x, y, largura, altura))
        pygame.draw.rect(tela, CINZA_CLARO, (x, y, largura, altura), 2)

        # --- MODO DE ESCOLHA REESTRUTURADO EM COLUNAS ---
        if self.em_escolha:
            render_instrucao = self.fonte_nome.render("Respostas disponíveis:", True, UI_TEXTO_APAGADO)
            tela.blit(render_instrucao, (x + 20, y + 15))
            
            novos_rects = []
            
            # Divide as opções em duas colunas se houver mais de 2 opções
            for i, opcao in enumerate(self.opcoes_disponiveis):
                texto_menu = opcao["texto"]
                
                if i == self.opcao_selecionada:
                    cor_opt = TXT_SISTEMA_NARRADOR  # Amarelo Ouro Destaque
                    texto_completo_opt = f"> {texto_menu}"
                else:
                    cor_opt = CINZA_CLARO  # Cor neutra padrão
                    texto_completo_opt = f"  {texto_menu}"
                
                # Determina a coluna (0 para esquerda, 1 para direita) e a linha correspondente
                coluna = i // 2
                linha_idx = i % 2
                
                # Define o X e Y iniciais com base na coluna e linha
                x_coluna = x + 20 if coluna == 0 else x + (largura // 2) + 10
                y_linha_pos = y + 55 + (linha_idx * 45) # Dá bastante espaço vertical sem vazar
                
                # Quebra o texto limitando-o à metade da largura da caixa
                linhas_opcao = self._quebrar_texto(texto_completo_opt, self.fonte_texto, (largura // 2) - 40)
                
                y_bloco_atual = y_linha_pos
                for linha in linhas_opcao:
                    render_opt = self.fonte_texto.render(linha, True, cor_opt)
                    tela.blit(render_opt, (x_coluna, y_bloco_atual))
                    y_bloco_atual += 22 
                
                # Cria a hitbox de clique precisa para cada metade da tela
                altura_bloco = max(35, y_bloco_atual - y_linha_pos)
                hitbox_opcao = pygame.Rect(x_coluna, y_linha_pos, (largura // 2) - 20, altura_bloco)
                novos_rects.append(hitbox_opcao)
                
            self.rects_opcoes = novos_rects
            return

        # --- MODO TEXTO CORRIDO STANDARD ---
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