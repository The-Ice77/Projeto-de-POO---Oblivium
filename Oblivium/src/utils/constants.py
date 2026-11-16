import os

LARGURA = 1280
ALTURA = 720
FPS = 60

PASTA_SRC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA_OBLIVIUM = os.path.dirname(PASTA_SRC)
PASTA_DATA = os.path.join(PASTA_SRC, "data")


def modo_apresentacao():
    """O marcador existe somente na distribuição escolar preparada pelo projeto."""
    return os.path.isfile(os.path.join(PASTA_OBLIVIUM, "apresentacao.json"))


def desenvolvimento_habilitado():
    """A versão escolar nunca habilita o console, mesmo com a variável definida."""
    return not modo_apresentacao() and os.environ.get("OBLIVIUM_DEV") == "1"
