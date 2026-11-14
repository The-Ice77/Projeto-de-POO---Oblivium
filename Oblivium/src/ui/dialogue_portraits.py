# src/ui/dialogue_portraits.py
"""Catálogo, cache procedural e resolução de retratos e cores de interlocutores de diálogo."""

import pygame

from src.utils.colors import (
    MARFIM_OFFWHITE,
    NOME_HALIA,
    NOME_MALDICAO,
    TXT_PENSAMENTO_INTERNO,
    TXT_SISTEMA_NARRADOR,
)
from src.utils.resource_manager import ResourceManager


class DialoguePortraitCatalog:
    """Centraliza o carregamento oficial, fallback pixel-art, resolução de retratos e cores dos personagens."""

    TAMANHO_RETRATO = (96, 124)

    @classmethod
    def criar_retratos_base(cls):
        """Inicializa o dicionário completo de retratos em cache para uso em caixas de diálogo."""
        retratos = {
            "Halia": None,  # Temporariamente desativado a pedido do usuário (aguardando novas artes)
            "Torvin": ResourceManager.carregar_imagem("elementos/torvin_portrait.png", cls.TAMANHO_RETRATO),
            "Carroceiro": ResourceManager.carregar_imagem("elementos/carroceiro_portrait.png", cls.TAMANHO_RETRATO),
        }
        cls.inicializar_retratos_companheiros(retratos)
        return retratos

    @classmethod
    def inicializar_retratos_companheiros(cls, retratos):
        """Inicializa retratos pixel-art canônicos dos heróis da companhia e NPCs no dicionário informado."""
        w_ret, h_ret = cls.TAMANHO_RETRATO

        # Carrega os retratos oficiais em alta definição gerados a partir das novas sprites
        mapa_retratos_oficiais = {
            "Halia": "elementos/retratos/retrato_halia.png",
            "Sylvan": "elementos/retratos/retrato_sylvan.png",
            "Roland": "elementos/retratos/retrato_roland.png",
            "Caelen": "elementos/retratos/retrato_caelen.png",
            "Aldous": "elementos/retratos/retrato_aldous.png",
            "Elara": "elementos/retratos/retrato_elara.png",
            "Torvald": "elementos/retratos/retrato_torvald.png",
        }
        for chave, rel_path in mapa_retratos_oficiais.items():
            img_ret = ResourceManager.carregar_imagem(rel_path, (w_ret, h_ret))
            if img_ret:
                retratos[chave] = img_ret

        # Sylvan (Ferreiro e Guerreiro Anão)
        surf_sylvan = pygame.Surface((w_ret, h_ret), pygame.SRCALPHA)
        surf_sylvan.fill((22, 18, 20))
        for r in range(50, 0, -10):
            pygame.draw.circle(surf_sylvan, (80, 40, 20, 25), (48, 62), r)
        pygame.draw.rect(surf_sylvan, (80, 50, 35), (14, 85, 68, 38), border_radius=4)
        pygame.draw.rect(surf_sylvan, (140, 150, 160), (22, 82, 52, 22))
        pygame.draw.rect(surf_sylvan, (220, 175, 45), (18, 100, 60, 6))
        pygame.draw.rect(surf_sylvan, (225, 185, 155), (28, 28, 40, 42), border_radius=4)
        pygame.draw.rect(surf_sylvan, (195, 75, 30), (24, 18, 48, 16), border_radius=4)
        pygame.draw.rect(surf_sylvan, (155, 55, 20), (20, 26, 10, 28))
        pygame.draw.rect(surf_sylvan, (155, 55, 20), (66, 26, 10, 28))
        pygame.draw.rect(surf_sylvan, (20, 16, 22), (34, 40, 6, 5))
        pygame.draw.rect(surf_sylvan, (20, 16, 22), (56, 40, 6, 5))
        pygame.draw.rect(surf_sylvan, (200, 150, 125), (44, 42, 8, 8))
        pygame.draw.rect(surf_sylvan, (195, 75, 30), (24, 48, 48, 56), border_radius=6)
        pygame.draw.rect(surf_sylvan, (155, 55, 20), (30, 68, 36, 32))
        pygame.draw.rect(surf_sylvan, (225, 185, 50), (28, 84, 12, 6))
        pygame.draw.rect(surf_sylvan, (225, 185, 50), (56, 84, 12, 6))
        if not retratos.get("Sylvan"):
            retratos["Sylvan"] = surf_sylvan

        # Roland (Paladino Sentinela)
        surf_roland = pygame.Surface((w_ret, h_ret), pygame.SRCALPHA)
        surf_roland.fill((18, 22, 28))
        for r in range(50, 0, -10):
            pygame.draw.circle(surf_roland, (40, 50, 75, 25), (48, 62), r)
        pygame.draw.rect(surf_roland, (36, 58, 110), (12, 85, 72, 38), border_radius=4)
        pygame.draw.rect(surf_roland, (190, 200, 215), (18, 78, 60, 26), border_radius=2)
        pygame.draw.rect(surf_roland, (220, 180, 50), (22, 98, 52, 4))
        pygame.draw.rect(surf_roland, (230, 195, 170), (30, 26, 36, 42), border_radius=4)
        pygame.draw.rect(surf_roland, (95, 70, 50), (26, 16, 44, 18), border_radius=4)
        pygame.draw.rect(surf_roland, (75, 50, 35), (24, 24, 8, 22))
        pygame.draw.rect(surf_roland, (75, 50, 35), (64, 24, 8, 22))
        pygame.draw.rect(surf_roland, (18, 20, 26), (36, 38, 5, 5))
        pygame.draw.rect(surf_roland, (18, 20, 26), (55, 38, 5, 5))
        pygame.draw.rect(surf_roland, (205, 165, 140), (45, 42, 6, 8))
        pygame.draw.rect(surf_roland, (215, 175, 150), (34, 56, 28, 8))
        if not retratos.get("Roland"):
            retratos["Roland"] = surf_roland

        # Caelen (Clérigo das Ervas)
        surf_caelen = pygame.Surface((w_ret, h_ret), pygame.SRCALPHA)
        surf_caelen.fill((20, 22, 24))
        for r in range(50, 0, -10):
            pygame.draw.circle(surf_caelen, (50, 70, 90, 25), (48, 62), r)
        pygame.draw.rect(surf_caelen, (242, 244, 248), (14, 82, 68, 42), border_radius=4)
        pygame.draw.rect(surf_caelen, (85, 160, 225), (28, 82, 12, 42))
        pygame.draw.rect(surf_caelen, (85, 160, 225), (56, 82, 12, 42))
        pygame.draw.rect(surf_caelen, (180, 115, 75), (42, 94, 12, 14))
        pygame.draw.rect(surf_caelen, (235, 205, 185), (31, 26, 34, 42), border_radius=4)
        pygame.draw.rect(surf_caelen, (175, 140, 95), (27, 16, 42, 18), border_radius=4)
        pygame.draw.rect(surf_caelen, (145, 115, 75), (26, 26, 6, 26))
        pygame.draw.rect(surf_caelen, (145, 115, 75), (64, 26, 6, 26))
        pygame.draw.rect(surf_caelen, (22, 24, 28), (36, 40, 5, 4))
        pygame.draw.rect(surf_caelen, (22, 24, 28), (55, 40, 5, 4))
        pygame.draw.rect(surf_caelen, (215, 180, 160), (45, 44, 6, 6))
        if not retratos.get("Caelen"):
            retratos["Caelen"] = surf_caelen

    @staticmethod
    def obter_cor_autor(autor):
        """Retorna a cor RGB canônica para o rótulo do interlocutor na caixa de diálogo."""
        autor_limpo = autor.lower() if autor else ""
        if "halia" in autor_limpo:
            return NOME_HALIA
        elif "sylvan" in autor_limpo or "grave" in autor_limpo:
            return (245, 140, 65)  # Laranja forja / calor
        elif "roland" in autor_limpo or "paladino" in autor_limpo:
            return (235, 195, 80)  # Ouro nobre / paladino
        elif "caelen" in autor_limpo or "clérigo" in autor_limpo or "clerigo" in autor_limpo:
            return (165, 210, 255)  # Azul celeste / clérigo
        elif "aldous" in autor_limpo or "ancião" in autor_limpo or "anciao" in autor_limpo or "líder" in autor_limpo:
            return (220, 195, 130)  # Ouro rústico / líder sábio
        elif "elara" in autor_limpo or "curandeira" in autor_limpo or "botânica" in autor_limpo:
            return (130, 215, 160)  # Verde menta / curandeira
        elif "torvald" in autor_limpo or "ferreiro" in autor_limpo:
            return (235, 120, 50)  # Laranja brasas / forja
        elif "doran" in autor_limpo or "guarda" in autor_limpo or "cavaleiro" in autor_limpo:
            return (200, 215, 230)  # Aço polido / guarda nobre
        elif "maldição" in autor_limpo or "maldicao" in autor_limpo:
            return NOME_MALDICAO
        elif autor in ["Sistema", "Narrador"]:
            return TXT_SISTEMA_NARRADOR
        elif autor in ["Pensamento", "Pensamento Interno"]:
            return TXT_PENSAMENTO_INTERNO
        return MARFIM_OFFWHITE

    @staticmethod
    def obter_retrato_autor(retratos, autor):
        """Retorna o retrato canônico do interlocutor ou None."""
        if not autor:
            return None
        if autor in retratos and retratos[autor] is not None:
            return retratos[autor]
        autor_low = autor.lower()
        if "halia" in autor_low:
            return retratos.get("Halia")
        if "sylvan" in autor_low or "grave" in autor_low:
            return retratos.get("Sylvan")
        if "roland" in autor_low or "paladino" in autor_low:
            return retratos.get("Roland")
        if "caelen" in autor_low or "clérigo" in autor_low or "clerigo" in autor_low:
            return retratos.get("Caelen")
        if "aldous" in autor_low or "ancião" in autor_low or "anciao" in autor_low or "líder" in autor_low:
            return retratos.get("Aldous")
        if "elara" in autor_low or "curandeira" in autor_low:
            return retratos.get("Elara")
        if "torvald" in autor_low or "ferreiro" in autor_low:
            return retratos.get("Torvald")
        if "doran" in autor_low or "guarda" in autor_low:
            return retratos.get("Roland")
        if "torvin" in autor_low:
            return retratos.get("Torvin")
        if "carroceiro" in autor_low:
            return retratos.get("Carroceiro")
        return None
