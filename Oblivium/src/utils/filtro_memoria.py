# src/utils/filtro_memoria.py
import pygame
import math

class FiltroMemoria:
    """
    Gerenciador de Pós-Processamento Fotográfico em Escala de Cinza
    baseado nos 7 Estágios de Memória da Halia (0 a 7 fragmentos).
    
    Utiliza dessaturação fotográfica real (Luminância precisa) sem escurecer
    a imagem, preservando 100% do brilho e contraste originais do cenário e entidades.
    """

    # Configuração dos 7 estágios:
    # Formato: {"alpha_cinza": 0-255, "saturacao_pct": 0-100, "nome": str}
    ESTAGIOS = {
        0: {"alpha_cinza": 255, "saturacao": 0,   "nome": "Vazio Absoluto (100% P&B)"},
        1: {"alpha_cinza": 215, "saturacao": 15,  "nome": "Lampejo Inicial (15% Cor)"},
        2: {"alpha_cinza": 175, "saturacao": 30,  "nome": "Contornos Desbotados (30% Cor)"},
        3: {"alpha_cinza": 130, "saturacao": 50,  "nome": "Equilíbrio Suave (50% Cor)"},
        4: {"alpha_cinza": 85,  "saturacao": 67,  "nome": "Despertar Mágico (67% Cor)"},
        5: {"alpha_cinza": 45,  "saturacao": 82,  "nome": "Quase Plena (82% Cor)"},
        6: {"alpha_cinza": 15,  "saturacao": 94,  "nome": "Limiar da Consciência (94% Cor)"},
        7: {"alpha_cinza": 0,   "saturacao": 100, "nome": "Totalmente Desperta (100% Cor)"},
    }

    def __init__(self, largura=1280, altura=720):
        self.largura = largura
        self.altura = altura
        
        self.estagio_atual = 0
        self.alpha_visual = float(self.ESTAGIOS[0]["alpha_cinza"])
        
        # Superfície de Flash / Onda de Expansão de Cor ao absorver memória
        self.overlay_flash = pygame.Surface((self.largura, self.altura), pygame.SRCALPHA)
        self.flash_alpha = 0.0
        self.raio_onda_expansao = 0.0
        self.onda_ativa = False
        self.pos_origem_onda = (self.largura // 2, self.altura // 2)

    def reiniciar(self, estagio=0):
        """Reinicia instantaneamente o filtro para um estágio específico (padrão 0 = 100% P&B)."""
        self.definir_estagio(estagio, com_transicao_suave=False)

    def definir_estagio(self, fragmentos_memoria, com_transicao_suave=True, pos_origem=None):
        """Atualiza o estágio do filtro de acordo com a quantidade de fragmentos coletados (0 a 7)."""
        novo_estagio = max(0, min(7, int(fragmentos_memoria)))
        
        if com_transicao_suave and novo_estagio > self.estagio_atual:
            # Ativa animação de expansão e flash de despertar de cores
            self.flash_alpha = 160.0
            self.onda_ativa = True
            self.raio_onda_expansao = 0.0
            if pos_origem:
                self.pos_origem_onda = pos_origem
        elif not com_transicao_suave:
            self.flash_alpha = 0.0
            self.onda_ativa = False
            self.raio_onda_expansao = 0.0

        self.estagio_atual = novo_estagio
        
        if not com_transicao_suave:
            config = self.ESTAGIOS[self.estagio_atual]
            self.alpha_visual = float(config["alpha_cinza"])

    def atualizar(self):
        """Atualiza a interpolação suave entre os níveis de saturação a cada frame."""
        config_alvo = self.ESTAGIOS[self.estagio_atual]
        alvo_alpha = float(config_alvo["alpha_cinza"])

        # Interpolação suave (Lerp) de 6% por frame
        self.alpha_visual += (alvo_alpha - self.alpha_visual) * 0.06

        # Atualiza flash de transição
        if self.flash_alpha > 0:
            self.flash_alpha = max(0.0, self.flash_alpha - 5.0)

        # Atualiza onda de choque de cor
        if self.onda_ativa:
            self.raio_onda_expansao += 34.0
            if self.raio_onda_expansao > math.hypot(self.largura, self.altura):
                self.onda_ativa = False

    def aplicar_filtro(self, tela, pos_jogador=None):
        """
        Aplica a dessaturação fotográfica sobre a tela.
        Gera uma cópia em escala de cinza real (Luminância) e a mescla com a tela original
        de acordo com o estágio de sincronia de memórias atual.
        """
        # Se estiver no estágio final (100% de cor) e sem transição, não precisa processar
        if self.alpha_visual < 1.0 and self.flash_alpha <= 0 and not self.onda_ativa:
            return

        alpha_int = int(max(0, min(255, self.alpha_visual)))
        
        if alpha_int > 0:
            # 1. Converte a tela colorida em escala de cinza fotográfica real
            camada_cinza = pygame.transform.grayscale(tela)
            
            # 2. Se estiver 100% preto e branco (Estágio 0), desenha direto para máximo desempenho
            if alpha_int >= 254:
                tela.blit(camada_cinza, (0, 0))
            else:
                # 3. Se for estágio intermediário, mescla proporcionalmente para dar efeito de saturação parcial
                camada_cinza.set_alpha(alpha_int)
                tela.blit(camada_cinza, (0, 0))

        # 4. Onda de Expansão de Cor ao Despertar
        if self.onda_ativa:
            ox, oy = self.pos_origem_onda
            raio = int(self.raio_onda_expansao)
            pygame.draw.circle(tela, (240, 245, 255), (ox, oy), raio, width=6)
            pygame.draw.circle(tela, (190, 220, 255), (ox, oy), max(1, raio - 4), width=3)

        # 5. Flash Suave de Despertar de Memória
        if self.flash_alpha > 0:
            self.overlay_flash.fill((255, 255, 255, int(self.flash_alpha)))
            tela.blit(self.overlay_flash, (0, 0))
