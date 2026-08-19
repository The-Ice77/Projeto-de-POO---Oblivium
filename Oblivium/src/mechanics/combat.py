# src/mechanics/combat.py
import pygame

class CombatScreen:
    def __init__(self, largura, altura):
        self.largura = largura
        self.altura = altura
        
        self.fonte_nomes = pygame.font.Font(None, 36)
        self.fonte_status = pygame.font.Font(None, 24)
        self.fonte_menu = pygame.font.Font(None, 32)
        
        self.opcoes_menu = ["Atacar", "Magia", "Item", "Fugir"]
        self.opcao_selecionada = 0
        
        self.jogador = None
        self.inimigos = []
        
        self.estado_combate = "SELECIONANDO_ACAO" 
        
    def iniciar_combate(self, jogador, inimigos):
        self.jogador = jogador
        self.inimigos = inimigos
        self.opcao_selecionada = 0
        self.estado_combate = "SELECIONANDO_ACAO"
        print("Batalha iniciada!")

    def processar_eventos(self, evento):
        if self.estado_combate == "SELECIONANDO_ACAO":
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_UP:
                    self.opcao_selecionada = (self.opcao_selecionada - 1) % len(self.opcoes_menu)
                elif evento.key == pygame.K_DOWN:
                    self.opcao_selecionada = (self.opcao_selecionada + 1) % len(self.opcoes_menu)
                elif evento.key == pygame.K_RETURN:
                    acao = self.opcoes_menu[self.opcao_selecionada]
                    self.executar_acao_jogador(acao)

    def executar_acao_jogador(self, acao):
        if acao == "Atacar":
            print("Halia usou Atacar!")
        elif acao == "Fugir":
            print("Halia fugiu da batalha!")
            self.estado_combate = "FUGIU"

    def atualizar(self):
        inimigos_vivos = [i for i in self.inimigos if getattr(i, 'vivo', True)]
        if not inimigos_vivos:
            self.estado_combate = "VITORIA"
            
        return self.estado_combate

    def desenhar_barra(self, tela, x, y, valor_atual, valor_maximo, cor_barra, cor_fundo=(50, 50, 50), largura=150, altura=15):
        razao = max(0, valor_atual / valor_maximo) if valor_maximo > 0 else 0
        largura_atual = int(largura * razao)
        
        pygame.draw.rect(tela, cor_fundo, (x, y, largura, altura))
        pygame.draw.rect(tela, cor_barra, (x, y, largura_atual, altura))
        pygame.draw.rect(tela, (255, 255, 255), (x, y, largura, altura), 1) 

    def desenhar(self, tela):
        tela.fill((20, 25, 35))
        
        # --- DESENHAR INIMIGOS ---
        for idx, inimigo in enumerate(self.inimigos):
            if not getattr(inimigo, 'vivo', True): continue
            
            pos_x = self.largura - 300
            pos_y = 150 + (idx * 150)
            
            # Busca a imagem de forma robusta
            imagem_inimigo = getattr(inimigo, 'imagem_atual', None)
            
            if imagem_inimigo:
                # Opcional: Escalonar a imagem para o combate se ela for muito pequena
                img_combate = pygame.transform.scale(imagem_inimigo, (inimigo.largura * 2, inimigo.altura * 2))
                tela.blit(img_combate, (pos_x, pos_y))
            else:
                rect_inimigo = pygame.Rect(pos_x, pos_y, getattr(inimigo, 'largura', 40) * 2, getattr(inimigo, 'altura', 40) * 2) 
                pygame.draw.rect(tela, getattr(inimigo, 'cor', (150, 30, 50)), rect_inimigo)
                pygame.draw.rect(tela, (255, 255, 255), rect_inimigo, 2)
            
            texto_nome = self.fonte_nomes.render(inimigo.nome, True, (255, 100, 100))
            tela.blit(texto_nome, (pos_x, pos_y - 30))
            
            vida = getattr(inimigo, 'vida_atual', 30) 
            vida_max = getattr(inimigo, 'vida_maxima', 30)
            self.desenhar_barra(tela, pos_x, pos_y + getattr(inimigo, 'altura', 40) * 2 + 10, vida, vida_max, (200, 50, 50))

        # --- DESENHAR HALIA ---
        halia_x = 150
        halia_y = 300
        
        imagem_halia = getattr(self.jogador, 'imagem_atual', None)
        if imagem_halia:
            img_combate_halia = pygame.transform.scale(imagem_halia, (self.jogador.largura * 2, self.jogador.altura * 2))
            tela.blit(img_combate_halia, (halia_x, halia_y))
        else:
            rect_halia = pygame.Rect(halia_x, halia_y, 80, 100)
            pygame.draw.rect(tela, (34, 139, 34), rect_halia)
        
        texto_halia = self.fonte_nomes.render(self.jogador.nome, True, (100, 255, 100))
        tela.blit(texto_halia, (halia_x, halia_y - 40))
        
        self.desenhar_barra(tela, halia_x, halia_y + 110, self.jogador.vida_atual, self.jogador.vida_maxima, (50, 200, 50))
        texto_hp = self.fonte_status.render(f"HP: {self.jogador.vida_atual}/{self.jogador.vida_maxima}", True, (255,255,255))
        tela.blit(texto_hp, (halia_x + 160, halia_y + 110))
        
        self.desenhar_barra(tela, halia_x, halia_y + 130, getattr(self.jogador, 'mana_atual', self.jogador.mana_maxima), self.jogador.mana_maxima, (50, 50, 255))
        texto_mp = self.fonte_status.render(f"MP: {getattr(self.jogador, 'mana_atual', self.jogador.mana_maxima)}/{self.jogador.mana_maxima}", True, (255,255,255))
        tela.blit(texto_mp, (halia_x + 160, halia_y + 130))

        # --- CAIXA DE MENU ---
        caixa_menu = pygame.Rect(0, self.altura - 200, self.largura, 200)
        pygame.draw.rect(tela, (10, 10, 15), caixa_menu)
        pygame.draw.rect(tela, (200, 200, 200), caixa_menu, 3) 

        for i, opcao in enumerate(self.opcoes_menu):
            cor = (255, 255, 100) if i == self.opcao_selecionada else (200, 200, 200)
            marcador = "> " if i == self.opcao_selecionada else "  "
            
            texto = self.fonte_menu.render(f"{marcador}{opcao}", True, cor)
            tela.blit(texto, (50, self.altura - 170 + (i * 40)))