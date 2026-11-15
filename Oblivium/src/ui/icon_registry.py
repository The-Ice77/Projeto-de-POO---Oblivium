# src/ui/icon_registry.py
import math
import pygame
from src.utils.colors import (
    CINZA_LINHO, CINZA_ARDOSIA, MARFIM_OFFWHITE, DOURADO_ENVELHECIDO
)
from src.utils.resource_manager import ResourceManager


class IconRegistry:
    """
    Registro Central e Fábrica de Ícones e Artes Procedurais de Oblivium (Padrão Flyweight / Factory).

    Responsabilidades:
    - Resolver sprites oficiais de itens que existem em disco (ex.: Cajado.png, Grimório.png),
      retornando None caso o item não possua sprite própria (mantendo o modelo de apenas texto).
    - Gerar uma única vez e armazenar em cache (pygame.Surface com canal Alpha) os ícones
      procedurais de slots de equipamento, conquistas, notificações, moedas e controles de janela,
      evitando recálculos geométricos a cada frame (60 FPS).
    """

    _cache_surfaces = {}

    # Apenas as sprites de itens que realmente existem na pasta assets/props/ do projeto
    _SPRITES_OFICIAIS_ITENS = {
        "cajado_espinheiro": "props/Cajado.png",
        "cajado_orvalho_estelar": "props/Cajado.png",
        "tomo_chama_ancestral": "props/Grimório.png",
        "tomo_geada_eterna": "props/Grimório.png",
        "tomo_brisa_restauradora": "props/Grimório.png",
    }

    @classmethod
    def limpar_cache(cls):
        """Limpa o cache de superfícies procedurais geradas."""
        cls._cache_surfaces.clear()

    # =========================================================================
    # 1. SPRITES OFICIAIS DE ITENS (APENAS OS QUE EXISTEM EM ASSETS)
    # =========================================================================
    @classmethod
    def resolver_caminho_sprite_item(cls, item):
        """
        Retorna o caminho relativo da sprite oficial de um item APENAS se ela existir
        para aquele item específico. Não improvisa sprites de cenário para outros itens.
        """
        if item is None or isinstance(item, str):
            return None

        icone_item = getattr(item, "icone_sprite", None)
        if icone_item:
            return icone_item

        id_it = getattr(item, "id", "").lower()
        return cls._SPRITES_OFICIAIS_ITENS.get(id_it)

    @classmethod
    def obter_sprite_item(cls, item, tamanho=(40, 40)):
        """
        Retorna a pygame.Surface da sprite oficial do item redimensionada,
        ou None caso o item não possua sprite própria no jogo.
        """
        caminho = cls.resolver_caminho_sprite_item(item)
        if not caminho:
            return None
        return ResourceManager.carregar_imagem(caminho, tamanho)

    # =========================================================================
    # 2. ÍCONES PROCEDURAIS DOS SLOTS DE EQUIPAMENTO / GRIMÓRIO / BOLSA
    # =========================================================================
    @classmethod
    def obter_icone_slot(cls, tipo_ou_item, tamanho=(48, 44), equipado=False, **kwargs):
        """
        Retorna uma pygame.Surface cacheada para o slot de inventário:
        - Se for um item equipado que possui sprite oficial (ex.: Cajado ou Grimório), usa a sprite.
        - Caso contrário, retorna o ícone vetorial antigo do slot (ROUPA, CAJADO, ACESSORIO, GRIMORIO, VAZIO_BOLSA).
        """
        largura = max(16, int(tamanho[0]))
        altura = max(16, int(tamanho[1]))

        if not isinstance(tipo_ou_item, str) and tipo_ou_item is not None:
            sprite_oficial = cls.obter_sprite_item(tipo_ou_item, (min(largura, altura) - 2, min(largura, altura) - 2))
            if sprite_oficial:
                return sprite_oficial

            slot_eq = getattr(tipo_ou_item, "slot", "")
            cat = getattr(tipo_ou_item, "categoria", "")
            chave_slot = slot_eq if slot_eq else cat
        else:
            chave_slot = str(tipo_ou_item or "VAZIO")

        chave_slot = chave_slot.upper()
        chave_cache = ("slot", chave_slot, largura, altura, bool(equipado))
        if chave_cache in cls._cache_surfaces:
            return cls._cache_surfaces[chave_cache]

        surf = pygame.Surface((largura, altura), pygame.SRCALPHA)
        cx, cy = largura // 2, altura // 2

        cor_base = (195, 180, 130) if equipado else (64, 66, 78)
        cor_detalhe = (240, 225, 175) if equipado else (85, 88, 102)

        if "ROUPA" in chave_slot:
            pts_tunica = [
                (cx - 6, cy - 13), (cx + 6, cy - 13),
                (cx + 15, cy - 5), (cx + 11, cy + 1), (cx + 7, cy - 3),
                (cx + 9, cy + 13), (cx - 9, cy + 13),
                (cx - 7, cy - 3), (cx - 11, cy + 1), (cx - 15, cy - 5)
            ]
            pygame.draw.polygon(surf, cor_base, pts_tunica, 2)
            pygame.draw.line(surf, cor_detalhe, (cx, cy - 10), (cx, cy + 12), 1)

        elif "CAJADO" in chave_slot:
            pygame.draw.line(surf, cor_base, (cx - 10, cy + 12), (cx + 8, cy - 6), 2)
            pygame.draw.circle(surf, cor_detalhe, (cx + 9, cy - 8), 5, 2)
            pygame.draw.circle(surf, cor_base, (cx + 9, cy - 8), 2)

        elif "ACESSORIO_1" in chave_slot:
            pygame.draw.circle(surf, cor_base, (cx, cy + 2), 9, 2)
            pts_gema = [(cx, cy - 12), (cx + 5, cy - 7), (cx, cy - 4), (cx - 5, cy - 7)]
            pygame.draw.polygon(surf, cor_detalhe, pts_gema)

        elif "ACESSORIO" in chave_slot:
            pygame.draw.lines(surf, cor_base, False, [(cx - 8, cy - 11), (cx, cy + 1), (cx + 8, cy - 11)], 1)
            pts_pend = [(cx, cy - 2), (cx + 7, cy + 5), (cx, cy + 13), (cx - 7, cy + 5)]
            pygame.draw.polygon(surf, cor_detalhe, pts_pend, 2)
            pygame.draw.circle(surf, cor_base, (cx, cy + 5), 2)

        elif "GRIMORIO" in chave_slot:
            r_livro = pygame.Rect(cx - 10, cy - 12, 20, 24)
            pygame.draw.rect(surf, cor_base, r_livro, 2, border_radius=2)
            pygame.draw.line(surf, cor_detalhe, (cx - 6, cy - 12), (cx - 6, cy + 11), 1)
            pts_runa = [(cx + 2, cy - 5), (cx + 6, cy), (cx + 2, cy + 5), (cx - 2, cy)]
            pygame.draw.polygon(surf, cor_detalhe, pts_runa, 1)

        else:
            # Filigrana sutil para slots vazios da bolsa (VAZIO_BOLSA)
            cor_vazio = (36, 38, 46)
            pts_los = [(cx, cy - 6), (cx + 6, cy), (cx, cy + 6), (cx - 6, cy)]
            pygame.draw.polygon(surf, cor_vazio, pts_los, 1)
            pygame.draw.circle(surf, cor_vazio, (cx, cy), 1)

        cls._cache_surfaces[chave_cache] = surf
        return surf

    # =========================================================================
    # 3. ÍCONES PROCEDURAIS DE CONQUISTAS (CACHEADOS EM SURFACE)
    # =========================================================================
    @classmethod
    def obter_icone_conquista(cls, id_conquista, categoria="", cor_principal=None, desbloqueada=True, tamanho=44, cor=None, secreta=False, **kwargs):
        """
        Gera uma única vez e retorna do cache a pygame.Surface com a arte vetorial
        exclusiva de cada conquista de Oblivium.
        """
        cor_alvo = cor if cor is not None else cor_principal
        cor_p = tuple(cor_alvo[:3]) if cor_alvo else ((230, 195, 95) if desbloqueada else (95, 95, 110))
        chave_cache = ("conquista", str(id_conquista), str(categoria), cor_p, bool(desbloqueada), bool(secreta), int(tamanho))
        if chave_cache in cls._cache_surfaces:
            return cls._cache_surfaces[chave_cache]

        surf = pygame.Surface((tamanho, tamanho), pygame.SRCALPHA)
        cx, cy = tamanho // 2, tamanho // 2

        if not desbloqueada and secreta:
            # Emblema arcano enigmático para conquistas secretas não reveladas
            pygame.draw.circle(surf, (22, 22, 28), (cx, cy), tamanho // 2 - 4)
            pygame.draw.circle(surf, (60, 64, 76), (cx, cy), tamanho // 2 - 4, 1)
            # Ponto de interrogação / Glifo de enigma
            pygame.draw.arc(surf, (120, 125, 140), (cx - 7, cy - 10, 14, 12), 0, math.pi, 2)
            pygame.draw.line(surf, (120, 125, 140), (cx + 7, cy - 4), (cx, cy + 2), 2)
            pygame.draw.line(surf, (120, 125, 140), (cx, cy + 2), (cx, cy + 5), 2)
            pygame.draw.circle(surf, (140, 145, 160), (cx, cy + 10), 2)
            cls._cache_surfaces[chave_cache] = surf
            return surf

        cor_sec = (
            min(255, cor_p[0] + 35),
            min(255, cor_p[1] + 35),
            min(255, cor_p[2] + 35)
        ) if desbloqueada else (65, 65, 78)
        cor_brilho = MARFIM_OFFWHITE if desbloqueada else (120, 120, 135)

        id_c = (id_conquista or "").lower()
        cat_c = (categoria or "").upper()

        if id_c == "despertar_oblivium":
            pygame.draw.ellipse(surf, (28, 36, 52) if desbloqueada else (22, 22, 28), (cx - 16, cy - 9, 32, 18))
            pygame.draw.ellipse(surf, cor_p, (cx - 16, cy - 9, 32, 18), 2)
            pygame.draw.circle(surf, cor_sec, (cx, cy), 6)
            pygame.draw.circle(surf, (15, 20, 30), (cx, cy), 3)
            pygame.draw.circle(surf, cor_brilho, (cx + 2, cy - 2), 1)
            for dx in (-10, -5, 0, 5, 10):
                pygame.draw.line(surf, cor_p, (cx + dx, cy - 11), (cx + int(dx * 1.2), cy - 15), 1)

        elif id_c == "chama_primordial":
            pts_ext = [(cx, cy - 16), (cx + 10, cy - 3), (cx + 12, cy + 7), (cx + 6, cy + 14),
                       (cx - 6, cy + 14), (cx - 12, cy + 7), (cx - 10, cy - 3)]
            pts_int = [(cx, cy - 8), (cx + 6, cy + 2), (cx + 4, cy + 11), (cx - 4, cy + 11), (cx - 6, cy + 2)]
            pygame.draw.polygon(surf, cor_p, pts_ext)
            pygame.draw.polygon(surf, (255, 220, 120) if desbloqueada else cor_sec, pts_int)
            pygame.draw.circle(surf, cor_brilho, (cx, cy + 7), 3)

        elif id_c == "dominio_gravidade":
            pts_rocha = [(cx, cy - 15), (cx + 11, cy - 6), (cx + 8, cy + 6), (cx, cy + 10), (cx - 8, cy + 6), (cx - 11, cy - 6)]
            pygame.draw.polygon(surf, (55, 45, 80) if desbloqueada else (35, 35, 42), pts_rocha)
            pygame.draw.polygon(surf, cor_p, pts_rocha, 2)
            pygame.draw.line(surf, cor_brilho, (cx, cy - 15), (cx, cy + 10), 1)
            pygame.draw.arc(surf, cor_sec, (cx - 16, cy + 4, 32, 12), math.pi, 2 * math.pi, 2)
            pygame.draw.circle(surf, cor_brilho, (cx - 13, cy - 10), 2)
            pygame.draw.circle(surf, cor_brilho, (cx + 13, cy - 4), 2)

        elif id_c == "primeiro_sangue" or cat_c == "COMBATE" and "cacadora" not in id_c and "intocavel" not in id_c:
            pygame.draw.line(surf, cor_p, (cx - 12, cy + 12), (cx + 12, cy - 12), 3)
            pygame.draw.line(surf, cor_brilho, (cx - 11, cy + 11), (cx + 11, cy - 11), 1)
            pygame.draw.line(surf, cor_p, (cx + 12, cy + 12), (cx - 12, cy - 12), 3)
            pygame.draw.line(surf, cor_brilho, (cx + 11, cy + 11), (cx - 11, cy - 11), 1)
            pygame.draw.line(surf, cor_sec, (cx - 11, cy + 4), (cx - 4, cy + 11), 2)
            pygame.draw.line(surf, cor_sec, (cx + 4, cy + 11), (cx + 11, cy + 4), 2)
            pygame.draw.circle(surf, cor_brilho, (cx, cy), 3)

        elif id_c == "cacadora_abissal":
            pygame.draw.circle(surf, (55, 22, 28) if desbloqueada else (30, 30, 38), (cx, cy + 2), 10)
            pygame.draw.circle(surf, cor_p, (cx, cy + 2), 10, 2)
            pts_chifre_esq = [(cx - 7, cy - 5), (cx - 15, cy - 15), (cx - 3, cy - 8)]
            pts_chifre_dir = [(cx + 7, cy - 5), (cx + 15, cy - 15), (cx + 3, cy - 8)]
            pygame.draw.polygon(surf, cor_p, pts_chifre_esq)
            pygame.draw.polygon(surf, cor_p, pts_chifre_dir)
            pygame.draw.circle(surf, cor_brilho, (cx - 4, cy + 1), 2)
            pygame.draw.circle(surf, cor_brilho, (cx + 4, cy + 1), 2)
            pygame.draw.line(surf, cor_p, (cx - 4, cy + 7), (cx + 4, cy + 7), 2)

        elif id_c == "intocavel":
            pts_escudo = [
                (cx, cy - 14), (cx + 13, cy - 9), (cx + 11, cy + 4),
                (cx, cy + 15), (cx - 11, cy + 4), (cx - 13, cy - 9)
            ]
            pygame.draw.polygon(surf, (25, 48, 56) if desbloqueada else (30, 30, 36), pts_escudo)
            pygame.draw.polygon(surf, cor_p, pts_escudo, 2)
            pts_estrela = [
                (cx, cy - 8), (cx + 3, cy - 2), (cx + 9, cy),
                (cx + 3, cy + 2), (cx, cy + 8), (cx - 3, cy + 2),
                (cx - 9, cy), (cx - 3, cy - 2)
            ]
            pygame.draw.polygon(surf, cor_brilho, pts_estrela)

        elif id_c == "erudita_grimorios":
            rect_livro = pygame.Rect(cx - 14, cy - 9, 28, 20)
            pygame.draw.rect(surf, (45, 32, 62) if desbloqueada else (30, 30, 38), rect_livro, border_radius=3)
            pygame.draw.rect(surf, cor_p, rect_livro, 2, border_radius=3)
            pygame.draw.line(surf, cor_p, (cx, cy - 9), (cx, cy + 11), 2)
            pygame.draw.line(surf, cor_brilho, (cx - 10, cy - 3), (cx - 3, cy - 3), 1)
            pygame.draw.line(surf, cor_brilho, (cx - 10, cy + 2), (cx - 3, cy + 2), 1)
            pygame.draw.line(surf, cor_brilho, (cx + 3, cy - 3), (cx + 10, cy - 3), 1)
            pygame.draw.line(surf, cor_brilho, (cx + 3, cy + 2), (cx + 10, cy + 2), 1)
            pygame.draw.circle(surf, cor_brilho, (cx, cy - 14), 3)

        elif id_c == "cumpridor_promessas":
            rect_perg = pygame.Rect(cx - 10, cy - 13, 20, 26)
            pygame.draw.rect(surf, (58, 48, 32) if desbloqueada else (32, 32, 38), rect_perg, border_radius=2)
            pygame.draw.rect(surf, cor_p, rect_perg, 2, border_radius=2)
            pygame.draw.line(surf, cor_sec, (cx - 12, cy - 13), (cx + 12, cy - 13), 3)
            pygame.draw.line(surf, cor_sec, (cx - 12, cy + 13), (cx + 12, cy + 13), 3)
            pygame.draw.line(surf, cor_brilho, (cx - 6, cy - 6), (cx + 6, cy - 6), 1)
            pygame.draw.line(surf, cor_brilho, (cx - 6, cy - 1), (cx + 4, cy - 1), 1)
            pygame.draw.circle(surf, (215, 75, 75) if desbloqueada else cor_p, (cx + 4, cy + 7), 4)
            pygame.draw.circle(surf, cor_brilho, (cx + 4, cy + 7), 4, 1)

        elif id_c == "memoria_completa":
            pygame.draw.circle(surf, cor_p, (cx, cy), 14, 1)
            pygame.draw.circle(surf, (45, 38, 65) if desbloqueada else (28, 28, 35), (cx, cy), 9)
            for i in range(7):
                ang = math.radians(i * (360 / 7) - 90)
                px = cx + int(math.cos(ang) * 11)
                py = cy + int(math.sin(ang) * 11)
                pygame.draw.circle(surf, cor_brilho if desbloqueada else cor_p, (px, py), 2)
            pts_c = [(cx, cy - 6), (cx + 5, cy), (cx, cy + 6), (cx - 5, cy)]
            pygame.draw.polygon(surf, cor_brilho, pts_c)

        elif id_c == "mestre_platinador" or cat_c == "PLATINA":
            pts_coroa = [
                (cx - 13, cy + 10), (cx - 15, cy - 4), (cx - 7, cy + 2),
                (cx, cy - 12), (cx + 7, cy + 2), (cx + 15, cy - 4), (cx + 13, cy + 10)
            ]
            pygame.draw.polygon(surf, (68, 58, 28) if desbloqueada else (32, 32, 40), pts_coroa)
            pygame.draw.polygon(surf, cor_p, pts_coroa, 2)
            pygame.draw.line(surf, cor_brilho, (cx - 13, cy + 13), (cx + 13, cy + 13), 2)
            pygame.draw.circle(surf, cor_brilho, (cx, cy - 13), 2)
            pygame.draw.circle(surf, cor_brilho, (cx - 15, cy - 5), 2)
            pygame.draw.circle(surf, cor_brilho, (cx + 15, cy - 5), 2)
            pygame.draw.circle(surf, (140, 225, 255) if desbloqueada else cor_p, (cx, cy + 4), 3)

        else:
            for i in range(8):
                ang = math.radians(i * 45)
                r_ext = 13 if i % 2 == 0 else 6
                px = cx + int(math.cos(ang) * r_ext)
                py = cy + int(math.sin(ang) * r_ext)
                pygame.draw.line(surf, cor_p, (cx, cy), (px, py), 2)
            pygame.draw.circle(surf, cor_brilho, (cx, cy), 4)

        cls._cache_surfaces[chave_cache] = surf
        return surf

    # =========================================================================
    # 4. ÍCONES PROCEDURAIS DE NOTIFICAÇÕES E MOEDAS (CACHEADOS EM SURFACE)
    # =========================================================================
    @classmethod
    def obter_icone_notificacao(cls, categoria="SISTEMA", cor_destaque=None, raio=13, tipo=None, cor=None, **kwargs):
        """Gera uma única vez e retorna do cache a Surface do selo de notificação."""
        cat_final = str(tipo or categoria or "SISTEMA").upper()
        cor_alvo = cor if cor is not None else (cor_destaque or (200, 200, 210))
        cor_d = tuple(cor_alvo[:3])
        chave_cache = ("notif", cat_final, cor_d, int(raio))
        if chave_cache in cls._cache_surfaces:
            return cls._cache_surfaces[chave_cache]

        diametro = (raio + 2) * 2
        surf = pygame.Surface((diametro, diametro), pygame.SRCALPHA)
        cx, cy = diametro // 2, diametro // 2
        cat = cat_final

        pygame.draw.circle(surf, (16, 16, 22), (cx, cy), raio)
        pygame.draw.circle(surf, cor_d, (cx, cy), raio, 1)

        if cat == "CONQUISTA":
            pts_taca = [
                (cx - 6, cy - 6), (cx + 6, cy - 6),
                (cx + 4, cy + 1), (cx - 4, cy + 1)
            ]
            pygame.draw.polygon(surf, cor_d, pts_taca)
            pygame.draw.line(surf, cor_d, (cx, cy + 1), (cx, cy + 6), 2)
            pygame.draw.line(surf, cor_d, (cx - 5, cy + 6), (cx + 5, cy + 6), 2)
        elif cat == "MISSAO":
            pts_bussola = [
                (cx, cy - 7), (cx + 3, cy - 2), (cx + 7, cy),
                (cx + 3, cy + 2), (cx, cy + 7), (cx - 3, cy + 2),
                (cx - 7, cy), (cx - 3, cy - 2)
            ]
            pygame.draw.polygon(surf, cor_d, pts_bussola)
            pygame.draw.circle(surf, (16, 16, 22), (cx, cy), 2)
        elif cat == "MEMORIA":
            pts_cristal = [(cx, cy - 7), (cx + 5, cy), (cx, cy + 7), (cx - 5, cy)]
            pygame.draw.polygon(surf, cor_d, pts_cristal)
            pygame.draw.polygon(surf, MARFIM_OFFWHITE, pts_cristal, 1)
        elif cat == "ITEM":
            pygame.draw.rect(surf, cor_d, (cx - 6, cy - 4, 12, 9), border_radius=2)
            pygame.draw.line(surf, (16, 16, 22), (cx - 6, cy), (cx + 6, cy), 1)
            pygame.draw.rect(surf, MARFIM_OFFWHITE, (cx - 2, cy - 2, 4, 4))
        elif cat == "ALERTA":
            pts_tri = [(cx, cy - 7), (cx - 7, cy + 6), (cx + 7, cy + 6)]
            pygame.draw.polygon(surf, cor_d, pts_tri, 2)
            pygame.draw.line(surf, cor_d, (cx, cy - 2), (cx, cy + 2), 2)
            pygame.draw.circle(surf, cor_d, (cx, cy + 4), 1)
        else:
            pygame.draw.circle(surf, cor_d, (cx, cy), 6, 1)
            pygame.draw.line(surf, cor_d, (cx, cy - 8), (cx, cy + 8), 1)
            pygame.draw.line(surf, cor_d, (cx - 8, cy), (cx + 8, cy), 1)

        cls._cache_surfaces[chave_cache] = surf
        return surf

    @classmethod
    def obter_icone_moeda(cls, tipo="OURO", raio=8, **kwargs):
        """Gera uma única vez e retorna do cache a Surface de moeda (OURO, PRATA, COBRE)."""
        t = (tipo or "OURO").upper()
        chave_cache = ("moeda", t, int(raio))
        if chave_cache in cls._cache_surfaces:
            return cls._cache_surfaces[chave_cache]

        diametro = (raio + 2) * 2
        surf = pygame.Surface((diametro, diametro), pygame.SRCALPHA)
        cx, cy = diametro // 2, diametro // 2

        if t == "OURO":
            cor_ext, cor_int, cor_borda = (215, 175, 65), (245, 215, 110), (255, 240, 175)
        elif t == "PRATA":
            cor_ext, cor_int, cor_borda = (160, 170, 185), (210, 218, 230), (240, 245, 255)
        else:
            cor_ext, cor_int, cor_borda = (175, 105, 68), (215, 140, 98), (240, 180, 145)

        pygame.draw.circle(surf, cor_ext, (cx, cy), raio)
        pygame.draw.circle(surf, cor_int, (cx, cy), max(2, raio - 2))
        pygame.draw.circle(surf, cor_borda, (cx, cy), raio, 1)
        pts = [(cx, cy - 3), (cx + 3, cy), (cx, cy + 3), (cx - 3, cy)]
        pygame.draw.polygon(surf, cor_ext, pts)

        cls._cache_surfaces[chave_cache] = surf
        return surf

    @classmethod
    def obter_icone_objetivo(cls, concluido=False, cor_ativo=(130, 225, 150), cor_pendente=(185, 190, 200), **kwargs):
        """Gera uma única vez e retorna do cache a Surface do marcador de objetivo de missão."""
        ca = tuple(cor_ativo[:3])
        cp = tuple(cor_pendente[:3])
        chave_cache = ("objetivo", bool(concluido), ca, cp)
        if chave_cache in cls._cache_surfaces:
            return cls._cache_surfaces[chave_cache]

        surf = pygame.Surface((16, 16), pygame.SRCALPHA)
        cx, cy = 8, 8
        if concluido:
            pts = [(cx, cy - 6), (cx + 6, cy), (cx, cy + 6), (cx - 6, cy)]
            pygame.draw.polygon(surf, (24, 52, 34), pts)
            pygame.draw.polygon(surf, ca, pts, 1)
            pygame.draw.lines(surf, ca, False, [(cx - 3, cy), (cx - 1, cy + 3), (cx + 4, cy - 3)], 2)
        else:
            pts = [(cx, cy - 5), (cx + 5, cy), (cx, cy + 5), (cx - 5, cy)]
            pygame.draw.polygon(surf, (20, 22, 28), pts)
            pygame.draw.polygon(surf, cp, pts, 1)
            pygame.draw.circle(surf, cp, (cx, cy), 1)

        cls._cache_surfaces[chave_cache] = surf
        return surf

    @classmethod
    def obter_icone_missao_badge(cls, categoria="PRINCIPAL", cor=(235, 205, 115), **kwargs):
        """Gera uma única vez e retorna do cache a Surface do emblema de Missão Principal/Secundária."""
        cat = (categoria or "PRINCIPAL").upper()
        c_rgb = tuple(cor[:3])
        chave_cache = ("missao_badge", cat, c_rgb)
        if chave_cache in cls._cache_surfaces:
            return cls._cache_surfaces[chave_cache]

        surf = pygame.Surface((18, 18), pygame.SRCALPHA)
        cx, cy = 9, 9
        if cat == "PRINCIPAL":
            pts_v = [(cx, cy - 7), (cx + 2, cy - 2), (cx + 7, cy), (cx + 2, cy + 2),
                     (cx, cy + 7), (cx - 2, cy + 2), (cx - 7, cy), (cx - 2, cy - 2)]
            pygame.draw.polygon(surf, c_rgb, pts_v)
            pygame.draw.circle(surf, (255, 245, 210), (cx, cy), 2)
        else:
            pts_ext = [(cx, cy - 6), (cx + 6, cy), (cx, cy + 6), (cx - 6, cy)]
            pygame.draw.polygon(surf, (24, 36, 52), pts_ext)
            pygame.draw.polygon(surf, c_rgb, pts_ext, 1)
            pygame.draw.circle(surf, c_rgb, (cx, cy), 2)

        cls._cache_surfaces[chave_cache] = surf
        return surf


# =============================================================================
# FUNÇÕES FACHADA DE COMPATIBILIDADE (DELEGAM AO ICONREGISTRY COM CACHE)
# =============================================================================
def desenhar_icone_fechar(superficie, rect, cor=MARFIM_OFFWHITE, espessura=2, **kwargs):
    """Desenha um ícone 'X' vetorial perfeitamente centralizado dentro de rect."""
    cx, cy = rect.centerx, rect.centery
    raio = max(4, min(rect.width, rect.height) // 2 - 6)
    pygame.draw.line(superficie, cor, (cx - raio, cy - raio), (cx + raio, cy + raio), espessura)
    pygame.draw.line(superficie, cor, (cx - raio, cy + raio), (cx + raio, cy - raio), espessura)
    pygame.draw.circle(superficie, cor, (cx, cy), 1)


def desenhar_icone_minimizar_expandir(superficie, rect, expandido=True, cor=MARFIM_OFFWHITE, espessura=2, **kwargs):
    """Desenha o ícone '-' (minimizar) ou '+' (expandir) centralizado dentro de rect."""
    cx, cy = rect.centerx, rect.centery
    r = max(4, min(rect.width, rect.height) // 2 - 6)
    pygame.draw.line(superficie, cor, (cx - r, cy), (cx + r, cy), espessura)
    if not expandido:
        pygame.draw.line(superficie, cor, (cx, cy - r), (cx, cy + r), espessura)


def desenhar_icone_minimizar(superficie, rect, expandido=True, cor=MARFIM_OFFWHITE, espessura=2, **kwargs):
    """Alias para desenhar_icone_minimizar_expandir."""
    desenhar_icone_minimizar_expandir(superficie, rect, expandido=expandido, cor=cor, espessura=espessura, **kwargs)


def desenhar_icone_objetivo(superficie, cx, cy, concluido=False, cor_ativo=(130, 225, 150), cor_pendente=(185, 190, 200), **kwargs):
    """Renderiza na tela a Surface cacheada do marcador de status de objetivo de missão."""
    surf = IconRegistry.obter_icone_objetivo(concluido=concluido, cor_ativo=cor_ativo, cor_pendente=cor_pendente, **kwargs)
    superficie.blit(surf, surf.get_rect(center=(cx, cy)))


def desenhar_icone_missao_badge(superficie, cx, cy, categoria="PRINCIPAL", cor=(235, 205, 115), **kwargs):
    """Renderiza na tela a Surface cacheada do emblema de Missão Principal vs Secundária."""
    surf = IconRegistry.obter_icone_missao_badge(categoria=categoria, cor=cor, **kwargs)
    superficie.blit(surf, surf.get_rect(center=(cx, cy)))


def desenhar_estrela_quatro_pontas(superficie, cx, cy, raio_externo=6, raio_interno=2, cor=MARFIM_OFFWHITE, **kwargs):
    """Desenha uma estrela arcana de 4 pontas (✦) vetorialmente nítida."""
    pts = [
        (cx, cy - raio_externo),
        (cx + raio_interno, cy - raio_interno),
        (cx + raio_externo, cy),
        (cx + raio_interno, cy + raio_interno),
        (cx, cy + raio_externo),
        (cx - raio_interno, cy + raio_interno),
        (cx - raio_externo, cy),
        (cx - raio_interno, cy - raio_interno),
    ]
    pygame.draw.polygon(superficie, cor, pts)


def desenhar_icone_moeda(superficie, cx, cy, tipo="OURO", raio=8, cor=None, **kwargs):
    """Renderiza na tela a Surface cacheada da moeda (Ouro, Prata ou Cobre)."""
    surf = IconRegistry.obter_icone_moeda(tipo=tipo, raio=raio, **kwargs)
    superficie.blit(surf, surf.get_rect(center=(cx, cy)))


def desenhar_icone_notificacao(superficie, cx, cy, categoria="SISTEMA", cor_destaque=None, raio=13, tipo=None, cor=None, **kwargs):
    """Renderiza na tela a Surface cacheada do emblema de notificação."""
    surf = IconRegistry.obter_icone_notificacao(
        categoria=categoria,
        cor_destaque=cor_destaque,
        raio=raio,
        tipo=tipo,
        cor=cor,
        **kwargs
    )
    superficie.blit(surf, surf.get_rect(center=(cx, cy)))


def desenhar_icone_conquista(superficie, rect_icone, id_conquista, categoria="", cor_principal=None, desbloqueada=True, cor=None, secreta=False, **kwargs):
    """Renderiza na tela a Surface cacheada da conquista centralizada em rect_icone."""
    lado = min(rect_icone.width, rect_icone.height)
    surf = IconRegistry.obter_icone_conquista(
        id_conquista=id_conquista,
        categoria=categoria,
        cor_principal=cor_principal,
        desbloqueada=desbloqueada,
        tamanho=lado,
        cor=cor,
        secreta=secreta,
        **kwargs
    )
    superficie.blit(surf, surf.get_rect(center=rect_icone.center))


def desenhar_icone_slot_inventario(superficie, rect, tipo_ou_item=None, equipado=False, **kwargs):
    """
    Renderiza o ícone de um slot de Equipamento ou Grimório:
    - Mantém os ícones vetoriais antigos para os slots (ROUPA, CAJADO, ACESSORIO_1, ACESSORIO_2, GRIMORIO).
    - Se o item equipado tiver sprite oficial existente no jogo (Cajado.png / Grimório.png), usa a sprite.
    """
    surf = IconRegistry.obter_icone_slot(tipo_ou_item, (rect.width, rect.height), equipado=equipado, **kwargs)
    if surf:
        superficie.blit(surf, surf.get_rect(center=rect.center))
