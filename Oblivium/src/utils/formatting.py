"""Utilitários puros de formatação numérica para combate, itens e HUD."""


def limpar_numero(valor, casas=1):
    """Remove ruído de ponto flutuante e retorna int quando exato."""
    try:
        num = round(float(valor or 0.0), casas)
    except (TypeError, ValueError):
        return 0
    if abs(num) < (10 ** (-(casas + 1))):
        return 0
    return int(round(num)) if float(num).is_integer() else num


def formatar_numero_curto(valor, casas=1):
    """Formata número sem caudas binárias IEEE-754 (ex: 35 ou 12.5)."""
    return str(limpar_numero(valor, casas=casas))
