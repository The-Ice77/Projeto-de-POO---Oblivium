"""Valores monetários da demo, sempre em cobres.

Os encontros roteirizados preservam seus próprios XP e memórias. A recompensa
é final: não recebe outro multiplicador de nível depois da criação do inimigo.
Missões e o dragão continuam definidos em seus catálogos JSON.
"""

VERSAO_ECONOMIA = 1
BOLSA_INICIAL_COBRES = 100

_RECOMPENSAS_ENCONTROS = {
    "estrada_fogo": {"moedas": 10, "memorias": 0, "xp": 40},
    "estrada_levitacao": {"moedas": 20, "memorias": 0, "xp": 80},
    "patrulha": {"moedas": 15, "memorias": 0, "xp": 45},
}


def recompensas_encontro(id_encontro):
    """Entrega uma cópia independente do perfil do encontro roteirizado."""
    return dict(_RECOMPENSAS_ENCONTROS[id_encontro])
