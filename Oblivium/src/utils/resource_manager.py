# src/utils/resource_manager.py
import pygame
import os

# Configuração de caminhos para localizar a pasta assets a partir da raiz do projeto
DIRETORIO_ATUAL = os.path.dirname(os.path.abspath(__file__))
DIRETORIO_SRC = os.path.dirname(DIRETORIO_ATUAL)
DIRETORIO_RAIZ = os.path.dirname(DIRETORIO_SRC)
PASTA_ASSETS = os.path.join(DIRETORIO_RAIZ, "assets")

class ResourceManager:
    # Dicionários de Cache (Memória do Jogo)
    _cache_imagens = {}
    _cache_animacoes = {}

    @classmethod
    def _obter_caminho_absoluto(cls, caminho_relativo):
        caminho_limpo = caminho_relativo.lstrip("/\\")
        if caminho_limpo.startswith("assets/"):
            caminho_limpo = caminho_limpo[len("assets/"):]
        return os.path.join(PASTA_ASSETS, caminho_limpo)

    @classmethod
    def carregar_imagem(cls, caminho, tamanho=None):
        """
        Carrega uma imagem simples. 
        Se já foi carregada antes, devolve a versão da memória.
        Pode redimensionar a imagem automaticamente se 'tamanho' (largura, altura) for passado.
        """

        chave = f"{caminho}_{tamanho}"
        
        if chave in cls._cache_imagens:
            return cls._cache_imagens[chave]

        caminho_absoluto = cls._obter_caminho_absoluto(caminho)

        if not os.path.exists(caminho_absoluto):
            print(f"[Aviso] Imagem não encontrada: {caminho_absoluto}")
            return None

        imagem = pygame.image.load(caminho_absoluto).convert_alpha()
        
        if tamanho:
            imagem = pygame.transform.scale(imagem, tamanho)
            
        cls._cache_imagens[chave] = imagem
        return imagem

    @classmethod
    def carregar_spritesheet(cls, caminho, largura_frame, altura_frame, tamanho_final=None):
        """
        Carrega uma folha de sprites (spritesheet) e corta-a numa lista de frames individuais.
        Excelente para animações (andar, atacar, etc).
        """
        chave = f"{caminho}_{largura_frame}x{altura_frame}_{tamanho_final}"
        
        if chave in cls._cache_animacoes:
            return cls._cache_animacoes[chave]

        caminho_absoluto = cls._obter_caminho_absoluto(caminho)

        if not os.path.exists(caminho_absoluto):
            print(f"[Aviso] Spritesheet não encontrada: {caminho_absoluto}")
            return []

        spritesheet = pygame.image.load(caminho_absoluto).convert_alpha()
        largura_total = spritesheet.get_width()
        altura_total = spritesheet.get_height()
        
        frames = []

        for y in range(0, altura_total, altura_frame):
            for x in range(0, largura_total, largura_frame):
                rect_corte = pygame.Rect(x, y, largura_frame, altura_frame)

                frame = pygame.Surface((largura_frame, altura_frame), pygame.SRCALPHA)

                frame.blit(spritesheet, (0, 0), rect_corte)

                if tamanho_final:
                    frame = pygame.transform.scale(frame, tamanho_final)
                    
                frames.append(frame)

        cls._cache_animacoes[chave] = frames
        return frames

    @classmethod
    def limpar_cache(cls):
        """
        Útil para limpar a memória ao mudar de cenários muito pesados.
        """
        cls._cache_imagens.clear()
        cls._cache_animacoes.clear()
        print("[Sistema] Cache de imagens limpo.")