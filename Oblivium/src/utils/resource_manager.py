# src/utils/resource_manager.py
import pygame
import os

# Configuração de caminhos para localizar a pasta assets a partir da raiz do projeto
DIRETORIO_ATUAL = os.path.dirname(os.path.abspath(__file__))
DIRETORIO_SRC = os.path.dirname(DIRETORIO_ATUAL)
DIRETORIO_RAIZ = os.path.dirname(DIRETORIO_SRC)
PASTA_ASSETS = os.path.join(DIRETORIO_RAIZ, "assets")

class Animacao:
    """
    Classe utilitária para gerenciar o estado e os frames de uma animação.
    Garante compatibilidade total com superfícies 32-bit com canal alfa.
    """
    def __init__(self, frames, velocidade=0.15, loop=True):
        self.frames = frames if frames else []
        self.velocidade = velocidade
        self.loop = loop
        self.frame_atual = 0.0
        self.concluida = False

    def atualizar(self):
        if not self.frames:
            return

        if not self.concluida:
            self.frame_atual += self.velocidade
            if self.frame_atual >= len(self.frames):
                if self.loop:
                    self.frame_atual = 0.0
                else:
                    self.frame_atual = len(self.frames) - 1
                    self.concluida = True

    def get_imagem(self):
        if not self.frames:
            return None
        idx = int(self.frame_atual)
        if 0 <= idx < len(self.frames):
            return self.frames[idx]
        return self.frames[0]

    def resetar(self):
        self.frame_atual = 0.0
        self.concluida = False


class ResourceManager:
    """
    Gerenciador Central de Recursos e Sprites de Oblivium.
    Suporta formato nativo de 32-bit (RGBA com canal alfa), recepção flexível de imagens de
    diferentes resoluções (escalonamento seguro) e fallback procedural sem poluição de log.
    """
    _cache_imagens = {}
    _cache_animacoes = {}
    _arquivos_ausentes_notificados = set()

    @classmethod
    def _obter_caminho_absoluto(cls, caminho_relativo):
        caminho_limpo = caminho_relativo.lstrip("/\\")
        if caminho_limpo.startswith("assets/"):
            caminho_limpo = caminho_limpo[len("assets/"):]
        return os.path.join(PASTA_ASSETS, caminho_limpo)

    @classmethod
    def criar_superficie_32bit(cls, largura, altura, cor_preenchimento=(0, 0, 0, 0)):
        """Cria uma superfície transparente em formato nativo 32-bit com canal alfa."""
        surf = pygame.Surface((largura, altura), pygame.SRCALPHA, 32)
        surf.fill(cor_preenchimento)
        return surf

    @classmethod
    def carregar_imagem(cls, caminho, tamanho=None, manter_proporcao=False):
        """
        Carrega uma imagem em 32-bit RGBA com suporte flexível a dimensões maiores.
        Se já foi carregada, recupera da memória cache.
        """
        chave = f"{caminho}_{tamanho}_{manter_proporcao}"
        
        if chave in cls._cache_imagens:
            return cls._cache_imagens[chave]

        caminho_absoluto = cls._obter_caminho_absoluto(caminho)

        if not os.path.exists(caminho_absoluto):
            if caminho_absoluto not in cls._arquivos_ausentes_notificados:
                cls._arquivos_ausentes_notificados.add(caminho_absoluto)
            cls._cache_imagens[chave] = None
            return None

        try:
            imagem = pygame.image.load(caminho_absoluto).convert_alpha()
            
            if tamanho:
                largura_alvo, altura_alvo = tamanho
                if manter_proporcao:
                    # Redimensiona proporcionalmente dentro da caixa
                    w_orig, h_orig = imagem.get_width(), imagem.get_height()
                    escala = min(largura_alvo / w_orig, altura_alvo / h_orig)
                    novo_w = max(1, int(w_orig * escala))
                    novo_h = max(1, int(h_orig * escala))
                    imagem = pygame.transform.scale(imagem, (novo_w, novo_h))
                else:
                    imagem = pygame.transform.scale(imagem, (largura_alvo, altura_alvo))
                
            cls._cache_imagens[chave] = imagem
            return imagem
        except Exception as e:
            cls._cache_imagens[chave] = None
            return None

    @classmethod
    def carregar_spritesheet(cls, caminho, largura_frame, altura_frame, tamanho_final=None):
        """
        Carrega uma folha de sprites 32-bit e fatia em frames individuais com proteção de dimensões.
        """
        chave = f"{caminho}_{largura_frame}x{altura_frame}_{tamanho_final}"
        
        if chave in cls._cache_animacoes:
            return cls._cache_animacoes[chave]

        caminho_absoluto = cls._obter_caminho_absoluto(caminho)

        if not os.path.exists(caminho_absoluto):
            cls._cache_animacoes[chave] = []
            return []

        try:
            spritesheet = pygame.image.load(caminho_absoluto).convert_alpha()
            largura_total = spritesheet.get_width()
            altura_total = spritesheet.get_height()
            
            frames = []

            for y in range(0, altura_total, altura_frame):
                if y + altura_frame > altura_total:
                    break
                for x in range(0, largura_total, largura_frame):
                    if x + largura_frame > largura_total:
                        break

                    rect_corte = pygame.Rect(x, y, largura_frame, altura_frame)
                    frame = cls.criar_superficie_32bit(largura_frame, altura_frame)
                    frame.blit(spritesheet, (0, 0), rect_corte)

                    if tamanho_final:
                        frame = pygame.transform.scale(frame, tamanho_final)
                        
                    frames.append(frame)

            cls._cache_animacoes[chave] = frames
            return frames
        except Exception as e:
            cls._cache_animacoes[chave] = []
            return []

    @classmethod
    def extrair_linha_spritesheet(cls, caminho, largura_frame, altura_frame, linha, tamanho_final=None):
        """
        Extrai os frames de uma linha específica de uma spritesheet 32-bit.
        """
        chave = f"{caminho}_{largura_frame}x{altura_frame}_linha{linha}_{tamanho_final}"
        if chave in cls._cache_animacoes:
            return cls._cache_animacoes[chave]
            
        caminho_absoluto = cls._obter_caminho_absoluto(caminho)
        if not os.path.exists(caminho_absoluto):
            cls._cache_animacoes[chave] = []
            return []
            
        try:
            spritesheet = pygame.image.load(caminho_absoluto).convert_alpha()
            largura_total = spritesheet.get_width()
            altura_total = spritesheet.get_height()
            
            frames = []
            y = linha * altura_frame
            
            if y + altura_frame > altura_total:
                cls._cache_animacoes[chave] = []
                return []
                
            for x in range(0, largura_total, largura_frame):
                if x + largura_frame > largura_total:
                    break
                rect_corte = pygame.Rect(x, y, largura_frame, altura_frame)
                frame = cls.criar_superficie_32bit(largura_frame, altura_frame)
                frame.blit(spritesheet, (0, 0), rect_corte)
                
                if tamanho_final:
                    frame = pygame.transform.smoothscale(frame, tamanho_final)
                frames.append(frame)
                
            cls._cache_animacoes[chave] = frames
            return frames
        except Exception:
            cls._cache_animacoes[chave] = []
            return []

    @classmethod
    def limpar_cache(cls):
        """Libera a memória das texturas em cache."""
        cls._cache_imagens.clear()
        cls._cache_animacoes.clear()
        cls._arquivos_ausentes_notificados.clear()