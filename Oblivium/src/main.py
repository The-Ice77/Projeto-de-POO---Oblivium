"""Ponto de entrada do jogo."""


def main():
    from src.core.application import Aplicacao
    return Aplicacao().executar()


if __name__ == "__main__":
    # Permite também executar diretamente: python src/main.py.
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    raise SystemExit(main())
