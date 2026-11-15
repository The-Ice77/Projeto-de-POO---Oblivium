# src/ui/dialogue_portraits.py
"""Resolução de cores tipográficas e formatação de marcadores de controles para diálogos."""
import pygame

from src.utils.colors import (
    MARFIM_OFFWHITE,
    NOME_HALIA,
    NOME_MALDICAO,
    TXT_PENSAMENTO_INTERNO,
    TXT_SISTEMA_NARRADOR,
)

NOMES_TECLAS_PT = {
    pygame.K_SPACE: "ESPAÇO",
    pygame.K_RETURN: "ENTER",
    pygame.K_KP_ENTER: "ENTER",
    pygame.K_ESCAPE: "ESC",
    pygame.K_TAB: "TAB",
    pygame.K_UP: "SETA CIMA",
    pygame.K_DOWN: "SETA BAIXO",
    pygame.K_LEFT: "SETA ESQUERDA",
    pygame.K_RIGHT: "SETA DIREITA",
}


def obter_nome_tecla_legivel(codigo_tecla, game=None):
    """Converte um keycode Pygame em rótulo legível em português."""
    if game is not None and hasattr(game, "obter_nome_tecla"):
        return game.obter_nome_tecla(codigo_tecla)
    if codigo_tecla in NOMES_TECLAS_PT:
        return NOMES_TECLAS_PT[codigo_tecla]
    return pygame.key.name(codigo_tecla).upper()


def formatar_marcadores_controles(texto, controles=None, game=None):
    """Substitui {TECLAS_MOVER} e {TECLA_INTERAGIR} pelas teclas configuradas no momento da exibição."""
    if not isinstance(texto, str) or (
        "{TECLAS_MOVER}" not in texto and "{TECLA_INTERAGIR}" not in texto
    ):
        return texto

    mapa = controles if isinstance(controles, dict) else getattr(game, "controles", None)
    if not isinstance(mapa, dict):
        mapa = {}

    if "{TECLAS_MOVER}" in texto:
        teclas_mov = (
            mapa.get("Cima", pygame.K_w),
            mapa.get("Esquerda", pygame.K_a),
            mapa.get("Baixo", pygame.K_s),
            mapa.get("Direita", pygame.K_d),
        )
        if set(teclas_mov) == {pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT}:
            rotulo_mover = "as setas do teclado"
        else:
            rotulo_mover = ", ".join(obter_nome_tecla_legivel(k, game=game) for k in teclas_mov)
        texto = texto.replace("{TECLAS_MOVER}", rotulo_mover)

    if "{TECLA_INTERAGIR}" in texto:
        tecla_interagir = mapa.get("Interagir", pygame.K_e)
        rotulo_interagir = obter_nome_tecla_legivel(tecla_interagir, game=game)
        texto = texto.replace("{TECLA_INTERAGIR}", rotulo_interagir)

    return texto


class DialoguePortraitCatalog:
    """Centraliza as cores dos personagens no diálogo; retratos removidos por R02."""

    @classmethod
    def criar_retratos_base(cls):
        """Retorna mapa vazio (diálogos de Oblivium não exibem retratos/imagens)."""
        return {}

    @classmethod
    def inicializar_retratos_companheiros(cls, retratos):
        """Mantido por compatibilidade de assinatura; não carrega nem cria imagens."""
        return retratos

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
        elif any(k in autor_limpo for k in ("alvorecer", "forja renascida", "herbário", "herbario", "renovação", "renovacao")):
            return (220, 195, 130)  # Ouro narrativo de capítulo/reconstrução
        elif "maldição" in autor_limpo or "maldicao" in autor_limpo:
            return NOME_MALDICAO
        elif autor in ["Sistema", "Narrador"]:
            return TXT_SISTEMA_NARRADOR
        elif autor in ["Pensamento", "Pensamento Interno"]:
            return TXT_PENSAMENTO_INTERNO
        return MARFIM_OFFWHITE

    @staticmethod
    def obter_retrato_autor(retratos, autor):
        """Mantido por compatibilidade; diálogos não retornam nem exibem retratos."""
        return None
