import os

LARGURA = 1280
ALTURA = 720
FPS = 60

PASTA_SRC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA_OBLIVIUM = os.path.dirname(PASTA_SRC)
PASTA_DATA = os.path.join(PASTA_SRC, "data")
