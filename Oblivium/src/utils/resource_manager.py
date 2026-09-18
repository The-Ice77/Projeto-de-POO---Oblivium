# src/utils/resource_manager.py
import pygame
import os
import unicodedata

# Configuração de caminhos para localizar a pasta assets a partir da raiz do projeto
DIRETORIO_ATUAL = os.path.dirname(os.path.abspath(__file__))
DIRETORIO_SRC = os.path.dirname(DIRETORIO_ATUAL)
DIRETORIO_RAIZ = os.path.dirname(DIRETORIO_SRC)
PASTA_ASSETS = os.path.join(DIRETORIO_RAIZ, "assets")


def _normalizar_nome(texto):
    """Normaliza texto para comparação insensível a maiúsculas e sem acentos."""
    return "".join(
        c for c in unicodedata.normalize("NFD", texto.lower())
        if unicodedata.category(c) != "Mn"
    )


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
        
        caminho_direto = os.path.join(PASTA_ASSETS, caminho_limpo)
        if os.path.exists(caminho_direto):
            return caminho_direto
            
        # Fallback para resolver variações de codificação e acentuação no sistema de arquivos
        partes = caminho_limpo.replace("\\", "/").split("/")
        pasta_atual = PASTA_ASSETS
        for parte in partes:
            if not os.path.exists(pasta_atual):
                return caminho_direto
            itens = os.listdir(pasta_atual)
            correspondente = None
            parte_lower = parte.lower()
            
            # 1. Correspondência direta sem case
            for item in itens:
                if item.lower() == parte_lower:
                    correspondente = item
                    break
                    
            # 2. Correspondência sem acentos
            if not correspondente:
                parte_norm = _normalizar_nome(parte)
                for item in itens:
                    if _normalizar_nome(item) == parte_norm:
                        correspondente = item
                        break
                        
            if correspondente:
                pasta_atual = os.path.join(pasta_atual, correspondente)
            else:
                return caminho_direto
                
        return pasta_atual

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
        except Exception:
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
        except Exception:
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
    def carregar_imagem_com_transparencia(cls, caminho, tamanho=None, escala_fator=None, manter_proporcao=False, auto_crop=True, threshold_corte=4):
        """
        Carrega uma imagem em 32-bit RGBA de alta fidelidade visual, removendo o fundo preto/escuro
        com suavização anti-aliasing perfeita nas bordas em alta performance (C-accelerated).
        """
        chave = f"transp_hd_{caminho}_{tamanho}_{escala_fator}_{manter_proporcao}_{auto_crop}_{threshold_corte}"
        if chave in cls._cache_imagens:
            return cls._cache_imagens[chave]

        caminho_absoluto = cls._obter_caminho_absoluto(caminho)
        if not os.path.exists(caminho_absoluto):
            if caminho_absoluto not in cls._arquivos_ausentes_notificados:
                cls._arquivos_ausentes_notificados.add(caminho_absoluto)
            cls._cache_imagens[chave] = None
            return None

        try:
            img = pygame.image.load(caminho_absoluto)
            w, h = img.get_size()

            if auto_crop:
                # Recorte instantâneo via máscara binária em C do Pygame
                target_mid = (255 + threshold_corte) // 2
                spread = 255 - target_mid
                mask = pygame.mask.from_threshold(img, (target_mid, target_mid, target_mid, 255), (spread, spread, spread, 255))
                rects = mask.get_bounding_rects()
                if rects:
                    bbox = rects[0]
                    if len(rects) > 1:
                        bbox = bbox.unionall(rects[1:])
                    img = img.subsurface(bbox).copy()
                    w, h = img.get_size()

            # Determinar dimensões finais redimensionadas
            if escala_fator:
                nw = max(1, int(w * escala_fator))
                nh = max(1, int(h * escala_fator))
            elif tamanho:
                largura_alvo, altura_alvo = tamanho
                if manter_proporcao:
                    escala = min(largura_alvo / w, altura_alvo / h)
                    nw = max(1, int(w * escala))
                    nh = max(1, int(h * escala))
                else:
                    nw, nh = largura_alvo, altura_alvo
            else:
                nw, nh = w, h

            # Redimensionamento suave com preservação de detalhes
            if (nw, nh) != (w, h):
                img_scaled = pygame.transform.smoothscale(img, (nw, nh))
            else:
                img_scaled = img.copy()

            # Extração de canal alfa suave na superfície downscaled (instantâneo)
            rgba = cls.criar_superficie_32bit(nw, nh)
            for y in range(nh):
                for x in range(nw):
                    r, g, b = img_scaled.get_at((x, y))[:3]
                    lum = max(r, g, b)
                    if lum <= 2:
                        rgba.set_at((x, y), (0, 0, 0, 0))
                    elif lum < 24:
                        alpha = int((lum / 24.0) * 255)
                        rgba.set_at((x, y), (r, g, b, alpha))
                    else:
                        rgba.set_at((x, y), (r, g, b, 255))

            cls._cache_imagens[chave] = rgba
            return rgba
        except Exception:
            cls._cache_imagens[chave] = None
            return None

    @classmethod
    def carregar_spritesheet_grid(cls, caminho, colunas, linhas, tamanho_frame=None, remover_fundo_preto=True, threshold_fundo=16):
        """
        Carrega uma spritesheet fatiada em grade regular (colunas x linhas) com extração de canal alfa de alta performance.
        """
        chave = f"grid_{caminho}_{colunas}x{linhas}_{tamanho_frame}_{remover_fundo_preto}_{threshold_fundo}"
        if chave in cls._cache_animacoes:
            return cls._cache_animacoes[chave]

        caminho_absoluto = cls._obter_caminho_absoluto(caminho)
        if not os.path.exists(caminho_absoluto):
            cls._cache_animacoes[chave] = []
            return []

        try:
            sheet = pygame.image.load(caminho_absoluto)
            largura_total = sheet.get_width()
            altura_total = sheet.get_height()
            
            fw = largura_total // colunas
            fh = altura_total // linhas
            
            frames = []
            for r in range(linhas):
                for c in range(colunas):
                    rect = pygame.Rect(c * fw, r * fh, fw, fh)
                    sub = sheet.subsurface(rect).copy()
                    
                    if tamanho_frame:
                        sub = pygame.transform.smoothscale(sub, tamanho_frame)
                        
                    sw, sh = sub.get_size()
                    if remover_fundo_preto:
                        frame_rgba = cls.criar_superficie_32bit(sw, sh)
                        for y in range(sh):
                            for x in range(sw):
                                red, green, blue = sub.get_at((x, y))[:3]
                                lum = max(red, green, blue)
                                if lum <= threshold_fundo:
                                    frame_rgba.set_at((x, y), (0, 0, 0, 0))
                                elif lum < (threshold_fundo + 20):
                                    alpha = int(((lum - threshold_fundo) / 20.0) * 255)
                                    frame_rgba.set_at((x, y), (red, green, blue, alpha))
                                else:
                                    frame_rgba.set_at((x, y), (red, green, blue, 255))
                        sub = frame_rgba
                    else:
                        sub = sub.convert_alpha()

                    frames.append(sub)

            cls._cache_animacoes[chave] = frames
            return frames
        except Exception:
            cls._cache_animacoes[chave] = []
            return []

    @classmethod
    def extrair_sprites_individuais(cls, caminho, threshold_fundo=18, min_pixels=15, padding=2):
        """
        Método genérico de visão e extração de sprites desconexos contidos em uma imagem/spritesheet.
        Utiliza algoritmos nativos em C do Pygame para recortar instantaneamente partículas, folhas,
        estilhaços, faíscas, etc., gerando superfícies 32-bit com canal alfa limpo e sem delay.
        """
        chave = f"sprites_individuais_{caminho}_{threshold_fundo}_{min_pixels}_{padding}"
        if chave in cls._cache_animacoes:
            return cls._cache_animacoes[chave]

        caminho_absoluto = cls._obter_caminho_absoluto(caminho)
        if not os.path.exists(caminho_absoluto):
            cls._cache_animacoes[chave] = []
            return []

        try:
            sheet = pygame.image.load(caminho_absoluto)
            w, h = sheet.get_size()
            
            # Detecção ultrarrápida via máscara nativa em C
            target_mid = (255 + threshold_fundo) // 2
            spread = 255 - target_mid
            mask = pygame.mask.from_threshold(sheet, (target_mid, target_mid, target_mid, 255), (spread, spread, spread, 255))
            rects = mask.get_bounding_rects()
            
            sprites_extraidos = []
            for r in rects:
                if r.width >= 8 and r.height >= 8 and (r.width * r.height) >= min_pixels:
                    px = max(0, r.x - padding)
                    py = max(0, r.y - padding)
                    pw = min(w - px, r.width + (padding * 2))
                    ph = min(h - py, r.height + (padding * 2))
                    
                    sub = sheet.subsurface((px, py, pw, ph)).copy()
                    rgba = cls.criar_superficie_32bit(pw, ph)
                    
                    for py_i in range(ph):
                        for px_i in range(pw):
                            red, green, blue = sub.get_at((px_i, py_i))[:3]
                            lum = max(red, green, blue)
                            if lum <= threshold_fundo:
                                rgba.set_at((px_i, py_i), (0, 0, 0, 0))
                            elif lum < (threshold_fundo + 18):
                                alpha = int(((lum - threshold_fundo) / 18.0) * 255)
                                rgba.set_at((px_i, py_i), (red, green, blue, alpha))
                            else:
                                rgba.set_at((px_i, py_i), (red, green, blue, 255))
                                
                    sprites_extraidos.append(rgba)

            cls._cache_animacoes[chave] = sprites_extraidos
            return sprites_extraidos
        except Exception:
            cls._cache_animacoes[chave] = []
            return []

    @classmethod
    def extrair_petalas_individuais(cls, caminho, threshold_fundo=18, min_pixels=15):
        """Alias para compatibilidade reversa com extrair_sprites_individuais."""
        return cls.extrair_sprites_individuais(caminho, threshold_fundo=threshold_fundo, min_pixels=min_pixels)

    @classmethod
    def limpar_cache(cls):
        """Libera a memória das texturas em cache."""
        cls._cache_imagens.clear()
        cls._cache_animacoes.clear()
        cls._arquivos_ausentes_notificados.clear()