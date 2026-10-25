# src/utils/resource_manager.py
import pygame
import os
import unicodedata
import logging

logger = logging.getLogger(__name__)

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


class FonteEditorialWrapper:
    """
    Wrapper transparente para pygame.font.Font que intercepta glifos especiais
    ausentes nas fontes TTF/OTF customizadas ('✦', '✕', '✓', '✔', '▲', '▼', '◀', '▶')
    e os desenha proceduralmente com geometria vetorial nítida na mesma cor e linha base,
    eliminando retângulos vazios (.notdef) em qualquer texto do jogo.
    """
    GLIFOS_VETORIAIS = frozenset({"✦", "✕", "✓", "✔", "▲", "▼", "◀", "▶"})

    def __init__(self, fonte_pygame, tamanho=20):
        self._fonte = fonte_pygame
        self._tamanho = max(8, int(tamanho))
        self._largura_glifo = max(10, int(self._tamanho * 0.65))

    def _contem_glifo_especial(self, texto):
        if not texto:
            return False
        for ch in str(texto):
            if ch in self.GLIFOS_VETORIAIS:
                return True
        return False

    def size(self, texto):
        texto_str = str(texto) if texto is not None else ""
        if not self._contem_glifo_especial(texto_str):
            return self._fonte.size(texto_str)

        largura_total = 0
        altura_max = self._fonte.get_height()
        buffer_normal = []

        for ch in texto_str:
            if ch in self.GLIFOS_VETORIAIS:
                if buffer_normal:
                    seg = "".join(buffer_normal)
                    w_s, h_s = self._fonte.size(seg)
                    largura_total += w_s
                    altura_max = max(altura_max, h_s)
                    buffer_normal.clear()
                largura_total += self._largura_glifo
            else:
                buffer_normal.append(ch)

        if buffer_normal:
            seg = "".join(buffer_normal)
            w_s, h_s = self._fonte.size(seg)
            largura_total += w_s
            altura_max = max(altura_max, h_s)

        return (largura_total, altura_max)

    def render(self, texto, antialias, color, background=None):
        texto_str = str(texto) if texto is not None else ""
        if not self._contem_glifo_especial(texto_str):
            if background is not None:
                return self._fonte.render(texto_str, antialias, color, background)
            return self._fonte.render(texto_str, antialias, color)

        w_total, h_total = self.size(texto_str)
        w_total = max(1, w_total)
        h_total = max(1, h_total)

        surf = pygame.Surface((w_total, h_total), pygame.SRCALPHA, 32)
        if background is not None:
            surf.fill(background)

        cor_rgb = tuple(color[:3]) if isinstance(color, (tuple, list, pygame.Color)) else (240, 240, 240)
        cursor_x = 0
        buffer_normal = []

        def _flush_texto(cx):
            if not buffer_normal:
                return cx
            seg = "".join(buffer_normal)
            buffer_normal.clear()
            r_seg = self._fonte.render(seg, antialias, color)
            surf.blit(r_seg, (cx, (h_total - r_seg.get_height()) // 2))
            return cx + r_seg.get_width()

        for ch in texto_str:
            if ch in self.GLIFOS_VETORIAIS:
                cursor_x = _flush_texto(cursor_x)
                cx = cursor_x + self._largura_glifo // 2
                cy = h_total // 2
                r = max(3, int(self._tamanho * 0.26))
                ri = max(1, int(r * 0.35))

                if ch == "✦":
                    pts = [
                        (cx, cy - r), (cx + ri, cy - ri),
                        (cx + r, cy), (cx + ri, cy + ri),
                        (cx, cy + r), (cx - ri, cy + ri),
                        (cx - r, cy), (cx - ri, cy - ri)
                    ]
                    pygame.draw.polygon(surf, cor_rgb, pts)
                elif ch == "✕":
                    pygame.draw.line(surf, cor_rgb, (cx - r, cy - r), (cx + r, cy + r), 2)
                    pygame.draw.line(surf, cor_rgb, (cx - r, cy + r), (cx + r, cy - r), 2)
                elif ch in ("✓", "✔"):
                    pygame.draw.lines(surf, cor_rgb, False, [(cx - r, cy), (cx - ri, cy + r - 1), (cx + r, cy - r + 1)], 2)
                elif ch == "▲":
                    pygame.draw.polygon(surf, cor_rgb, [(cx, cy - r), (cx + r, cy + r - 1), (cx - r, cy + r - 1)])
                elif ch == "▼":
                    pygame.draw.polygon(surf, cor_rgb, [(cx - r, cy - r + 1), (cx + r, cy - r + 1), (cx, cy + r)])
                elif ch == "◀":
                    pygame.draw.polygon(surf, cor_rgb, [(cx + r - 1, cy - r), (cx + r - 1, cy + r), (cx - r, cy)])
                elif ch == "▶":
                    pygame.draw.polygon(surf, cor_rgb, [(cx - r + 1, cy - r), (cx - r + 1, cy + r), (cx + r, cy)])

                cursor_x += self._largura_glifo
            else:
                buffer_normal.append(ch)

        _flush_texto(cursor_x)
        return surf

    def __getattr__(self, nome):
        return getattr(self._fonte, nome)


class ResourceManager:
    """
    Gerenciador Central de Recursos e Sprites de Oblivium.
    Suporta formato nativo de 32-bit (RGBA com canal alfa), recepção flexível de imagens de
    diferentes resoluções (escalonamento seguro) e fallback procedural sem poluição de log.
    """
    _cache_imagens = {}
    _cache_animacoes = {}
    _cache_fontes = {}
    _arquivos_ausentes_notificados = set()

    @classmethod
    def carregar_fonte(cls, familia_ou_caminho="ui", tamanho=20):
        """
        Carrega uma fonte tipográfica com suporte a aliases editoriais de Oblivium,
        arquivos TTF/OTF locais e fallback seguro do Pygame.
        """
        chave = (str(familia_ou_caminho).lower(), int(tamanho))
        if chave in cls._cache_fontes:
            return cls._cache_fontes[chave]

        nome = str(familia_ou_caminho).lower()
        fonte_obj = None

        # 1. Se for caminho direto para arquivo existente
        if os.path.isfile(str(familia_ou_caminho)):
            try:
                fonte_obj = pygame.font.Font(familia_ou_caminho, tamanho)
            except Exception:
                fonte_obj = None

        # 2. Se for alias com arquivos locais em assets/fontes/ ou assets/fonts/
        if not fonte_obj:
            nomes_arquivos = {
                "sunday": ["Sunday.ttf", "sunday.ttf", "Sunday.otf"],
                "titulo": ["Sunday.ttf", "sunday.ttf"],
                "just_breathe": ["Just Breathe.ttf", "just_breathe.ttf", "JustBreathe.ttf"],
                "narrativa": ["Just Breathe.ttf", "just_breathe.ttf"],
                "poetica": ["Just Breathe.ttf", "just_breathe.ttf"],
                "contrail": ["ContrailOne.ttf", "Contrail One.ttf", "contrail.ttf"],
                "ui": ["ContrailOne.ttf", "Contrail One.ttf", "contrail.ttf"],
                "status": ["ContrailOne.ttf", "Contrail One.ttf", "contrail.ttf"]
            }
            arquivos_candidatos = nomes_arquivos.get(nome, [str(familia_ou_caminho)])
            for arq in arquivos_candidatos:
                for subpasta in ["fontes", "fonts", "menu inicial", ""]:
                    caminho_teste = cls._obter_caminho_absoluto(os.path.join(subpasta, arq))
                    if os.path.exists(caminho_teste) and os.path.isfile(caminho_teste):
                        try:
                            fonte_obj = pygame.font.Font(caminho_teste, tamanho)
                            break
                        except Exception:
                            pass
                if fonte_obj:
                    break

        # 3. Fallback inteligente para fontes instaladas no sistema operacional
        if not fonte_obj:
            fontes_sistema = {
                "sunday": ["georgia", "times new roman", "palatino linotype", "serif"],
                "titulo": ["georgia", "times new roman", "palatino linotype", "serif"],
                "just_breathe": ["gabriola", "segoe print", "segoe script", "monotype corsiva", "georgia"],
                "narrativa": ["gabriola", "segoe print", "segoe script", "georgia"],
                "poetica": ["gabriola", "segoe print", "segoe script", "georgia"],
                "contrail": ["trebuchet ms", "segoe ui", "candara", "arial", "sans-serif"],
                "ui": ["segoe ui", "trebuchet ms", "candara", "arial"],
                "status": ["segoe ui", "trebuchet ms", "candara", "arial"]
            }
            candidatos_sys = fontes_sistema.get(nome, [nome, "georgia", "segoe ui"])
            for sys_font in candidatos_sys:
                try:
                    fonte_obj = pygame.font.SysFont(sys_font, tamanho)
                    if fonte_obj:
                        break
                except Exception:
                    pass

        # 4. Fallback padrão do Pygame
        if not fonte_obj:
            fonte_obj = pygame.font.Font(None, tamanho)

        fonte_wrapped = FonteEditorialWrapper(fonte_obj, tamanho=tamanho)
        cls._cache_fontes[chave] = fonte_wrapped
        return fonte_wrapped


    @classmethod
    def _obter_caminho_absoluto(cls, caminho_relativo):
        caminho_limpo = caminho_relativo.lstrip("/\\")
        if caminho_limpo.startswith("assets/") or caminho_limpo.startswith("assets\\"):
            caminho_limpo = caminho_limpo[7:].lstrip("/\\")
        
        # 1. Prioriza caminho relativo direto se a pasta assets estiver no CWD
        caminho_rel = os.path.join("assets", caminho_limpo)
        if os.path.exists(caminho_rel):
            return caminho_rel

        caminho_direto = os.path.join(PASTA_ASSETS, caminho_limpo)
        if os.path.exists(caminho_direto):
            return caminho_direto
            
        # Fallback para resolver variações de codificação e acentuação no sistema de arquivos
        partes = caminho_limpo.replace("\\", "/").split("/")
        pasta_atual = "assets" if os.path.exists("assets") else PASTA_ASSETS
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
    def carregar_frames_pasta(cls, caminho_pasta, filtro=None, tamanho=None):
        """
        Carrega ordenadamente todos os arquivos PNG de uma pasta com filtro opcional.
        Útil para carregar animações quadro a quadro (passarinho, chamas de fogo, splashes, etc.).
        """
        chave = f"frames_pasta_{caminho_pasta}_{filtro}_{tamanho}"
        if chave in cls._cache_animacoes:
            return cls._cache_animacoes[chave]

        pasta_abs = cls._obter_caminho_absoluto(caminho_pasta)
        if not os.path.exists(pasta_abs) or not os.path.isdir(pasta_abs):
            pasta_direta = os.path.join(PASTA_ASSETS, caminho_pasta.lstrip("/\\"))
            if os.path.exists(pasta_direta) and os.path.isdir(pasta_direta):
                pasta_abs = pasta_direta
            else:
                cls._cache_animacoes[chave] = []
                return []

        try:
            import re
            def _chave_natural(nome):
                return [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', nome)]

            arquivos = sorted([
                f for f in os.listdir(pasta_abs)
                if f.lower().endswith(".png") and (filtro is None or filtro in f)
            ], key=_chave_natural)
            frames = []
            for arq in arquivos:
                caminho_completo = os.path.join(pasta_abs, arq)
                try:
                    img = pygame.image.load(caminho_completo).convert_alpha()
                except pygame.error:
                    img = pygame.image.load(caminho_completo)
                if tamanho:
                    img = pygame.transform.scale(img, tamanho)
                frames.append(img)
            cls._cache_animacoes[chave] = frames
            return frames
        except Exception:
            cls._cache_animacoes[chave] = []
            return []

    @classmethod
    def carregar_animacoes_inimigo(cls, pasta_inimigo, escala_fator=None, tamanho=None):
        """
        Carrega automaticamente todas as animações de um inimigo da pasta assets/inimigos/<pasta_inimigo>.
        Mapeia os arquivos PackX_Estado_YY.png para instâncias de Animacao nos estados:
        'idle', 'walk'/'andar', 'attack'/'ataque', 'hurt'/'dano', 'dead'/'morte', 'projectile'.
        """
        alias_pastas = {
            "gulosao": "demonio_superior",
            "gulosinho": "demonio_inferior"
        }
        pasta_inimigo = alias_pastas.get(str(pasta_inimigo).lower(), str(pasta_inimigo))

        chave = f"anim_inimigo_{pasta_inimigo}_{escala_fator}_{tamanho}"
        if chave in cls._cache_animacoes:
            return cls._cache_animacoes[chave]

        pasta_absoluta = cls._obter_caminho_absoluto(os.path.join("inimigos", pasta_inimigo))
        if not os.path.exists(pasta_absoluta) or not os.path.isdir(pasta_absoluta):
            pasta_direta = os.path.join(PASTA_ASSETS, "inimigos", pasta_inimigo)
            if os.path.exists(pasta_direta) and os.path.isdir(pasta_direta):
                pasta_absoluta = pasta_direta
            else:
                return {}

        arquivos = sorted([f for f in os.listdir(pasta_absoluta) if f.lower().endswith(".png")])
        grupos = {}
        for nome_arq in arquivos:
            partes = os.path.splitext(nome_arq)[0].split("_")
            if len(partes) >= 2:
                estado = partes[1].lower() if len(partes) >= 3 else partes[0].lower()
                grupos.setdefault(estado, []).append(nome_arq)

        # Configurações de velocidade e repetição por estado
        config_estados = {
            "idle": {"vel": 0.12, "loop": True},
            "walk": {"vel": 0.15, "loop": True},
            "attack": {"vel": 0.18, "loop": False},
            "hurt": {"vel": 0.20, "loop": False},
            "dead": {"vel": 0.15, "loop": False},
            "projectile": {"vel": 0.20, "loop": True}
        }

        dicionario_animacoes = {}
        for estado, lista_arqs in grupos.items():
            cfg = config_estados.get(estado, {"vel": 0.15, "loop": True})
            frames = []
            for nome_arq in lista_arqs:
                caminho_rel = os.path.join("inimigos", pasta_inimigo, nome_arq).replace("\\", "/")
                img = cls.carregar_imagem(caminho_rel)
                if img:
                    if escala_fator and escala_fator != 1.0:
                        nw = max(1, int(img.get_width() * escala_fator))
                        nh = max(1, int(img.get_height() * escala_fator))
                        img = pygame.transform.scale(img, (nw, nh))
                    elif tamanho:
                        img = pygame.transform.scale(img, tamanho)
                    frames.append(img)
            
            if frames:
                anim = Animacao(frames, velocidade=cfg["vel"], loop=cfg["loop"])
                dicionario_animacoes[estado] = anim

        # Aliases de compatibilidade em português
        if "walk" in dicionario_animacoes and "andar" not in dicionario_animacoes:
            dicionario_animacoes["andar"] = dicionario_animacoes["walk"]
        if "attack" in dicionario_animacoes and "ataque" not in dicionario_animacoes:
            dicionario_animacoes["ataque"] = dicionario_animacoes["attack"]
        if "hurt" in dicionario_animacoes and "dano" not in dicionario_animacoes:
            dicionario_animacoes["dano"] = dicionario_animacoes["hurt"]
        if "dead" in dicionario_animacoes:
            dicionario_animacoes.setdefault("morte", dicionario_animacoes["dead"])
            dicionario_animacoes.setdefault("morrer", dicionario_animacoes["dead"])

        cls._cache_animacoes[chave] = dicionario_animacoes
        return dicionario_animacoes

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
                    cor = img_scaled.get_at((x, y))
                    r, g, b = cor.r, cor.g, cor.b
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
                                cor = sub.get_at((x, y))
                                red, green, blue = cor.r, cor.g, cor.b
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
                            cor = sub.get_at((px_i, py_i))
                            red, green, blue = cor.r, cor.g, cor.b
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
    def obter_tile(cls, caminho_tileset, col, lin, tamanho_tile=16, escala=None):
        """Delega a extração de tile individual para o TilemapBuilder."""
        from src.maps.tilemap_builder import TilemapBuilder
        return TilemapBuilder.obter_tile(caminho_tileset, col, lin, tamanho_tile=tamanho_tile, escala=escala)

    @classmethod
    def criar_superficie_tiled(cls, caminho_tileset, largura_total, altura_total, col=0, lin=0, tamanho_tile=16, escala_tile=2):
        """Delega a criação de superfície contínua de tiles para o TilemapBuilder."""
        from src.maps.tilemap_builder import TilemapBuilder
        return TilemapBuilder.criar_superficie_tiled(
            caminho_tileset, largura_total, altura_total,
            col=col, lin=lin, tamanho_tile=tamanho_tile, escala_tile=escala_tile
        )

    @classmethod
    def gerar_chao_com_estrada_e_transicao(cls, largura_total, altura_total, y_estrada=240, h_estrada=240):
        """Delega a geração do terreno de estrada com transição para o TilemapBuilder."""
        from src.maps.tilemap_builder import TilemapBuilder
        return TilemapBuilder.gerar_chao_com_estrada_e_transicao(
            largura_total, altura_total, y_estrada=y_estrada, h_estrada=h_estrada
        )

    @classmethod
    def carregar_frames_de_pasta(cls, caminho_pasta, filtro_prefixo=None, tamanho=None, manter_proporcao=False):
        """
        Carrega ordenadamente todos os frames de imagem (.png/.jpg) de um diretório.
        Permite filtrar por prefixo de nome de arquivo e redimensionar.
        """
        chave = f"pasta_{caminho_pasta}_{filtro_prefixo}_{tamanho}_{manter_proporcao}"
        if chave in cls._cache_animacoes:
            return cls._cache_animacoes[chave]

        pasta_absoluta = cls._obter_caminho_absoluto(caminho_pasta)
        if not os.path.isdir(pasta_absoluta):
            cls._cache_animacoes[chave] = []
            return []

        arquivos = sorted([
            f for f in os.listdir(pasta_absoluta)
            if f.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".webp"))
            and (not filtro_prefixo or f.lower().startswith(filtro_prefixo.lower()))
        ])

        frames = []
        for arq in arquivos:
            caminho_arq = os.path.join(pasta_absoluta, arq)
            img = cls.carregar_imagem(caminho_arq, tamanho=tamanho, manter_proporcao=manter_proporcao)
            if img:
                frames.append(img)

        cls._cache_animacoes[chave] = frames
        return frames

    @classmethod
    def carregar_animacao_de_pasta(cls, caminho_pasta, filtro_prefixo=None, tamanho=None, velocidade=0.15, loop=True, manter_proporcao=False):
        """
        Gera uma instância de Animacao diretamente a partir de arquivos de imagem em uma pasta.
        """
        frames = cls.carregar_frames_de_pasta(caminho_pasta, filtro_prefixo=filtro_prefixo, tamanho=tamanho, manter_proporcao=manter_proporcao)
        return Animacao(frames=frames, velocidade=velocidade, loop=loop)

    _cache_sons = {}

    @classmethod
    def carregar_som(cls, caminho, volume=1.0):
        """
        Carrega um efeito sonoro (SFX) em formato WAV/OGG/MP3 com cache e controle de volume.
        """
        if caminho in cls._cache_sons:
            return cls._cache_sons[caminho]

        caminho_absoluto = cls._obter_caminho_absoluto(caminho)
        if not os.path.exists(caminho_absoluto):
            return None

        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            som = pygame.mixer.Sound(caminho_absoluto)
            som.set_volume(volume)
            cls._cache_sons[caminho] = som
            return som
        except (pygame.error, OSError) as e:
            logger.warning("Falha ao carregar som '%s': %s", caminho, e)
            return None

    @classmethod
    def tocar_musica(cls, caminho, loop=True, volume=0.5):
        """
        Inicia a reprodução de música de fundo em streaming.
        """
        caminho_absoluto = cls._obter_caminho_absoluto(caminho)
        if not os.path.exists(caminho_absoluto):
            return False

        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            pygame.mixer.music.load(caminho_absoluto)
            pygame.mixer.music.set_volume(volume)
            pygame.mixer.music.play(-1 if loop else 0)
            return True
        except (pygame.error, OSError) as e:
            logger.warning("Falha ao tocar música '%s': %s", caminho, e)
            return False

    @classmethod
    def parar_musica(cls):
        """Interrompe a música de fundo atual."""
        try:
            if pygame.mixer.get_init():
                pygame.mixer.music.stop()
        except (pygame.error, OSError) as e:
            logger.warning("Falha ao interromper a música de fundo: %s", e)

    @classmethod
    def limpar_cache(cls):
        """Libera a memória das texturas e sons em cache."""
        cls._cache_imagens.clear()
        cls._cache_animacoes.clear()
        cls._cache_fontes.clear()
        cls._cache_sons.clear()
        cls._arquivos_ausentes_notificados.clear()