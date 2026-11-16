"""Prepara uma cópia jogável limpa; não inclui documentos internos ou progresso."""
import argparse
import json
from datetime import datetime
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

RAIZ = Path(__file__).resolve().parents[1]
EXTENSOES_ASSETS = {".png", ".ico", ".jpg", ".jpeg", ".bmp", ".gif", ".webp", ".wav", ".ogg", ".mp3", ".m4a", ".ttf", ".otf", ".json", ".txt"}
ARQUIVOS_INICIO = (
    "iniciar.py", "requirements.txt", "Iniciar Oblivium.bat",
    "Novo participante.bat", "COMO_JOGAR.txt",
)


def arquivos_distribuicao(raiz=RAIZ):
    """Lista positiva: apenas código/dados de execução e assets, nunca saves."""
    raiz = Path(raiz)
    for nome in ARQUIVOS_INICIO:
        caminho = raiz / nome
        if not caminho.is_file() or caminho.is_symlink():
            raise FileNotFoundError(f"Arquivo de inicialização ausente: {caminho}")
        yield caminho, Path(nome)
    for pasta, extensoes in (("src", {".py", ".json"}), ("assets", EXTENSOES_ASSETS)):
        for caminho in sorted((raiz / pasta).rglob("*")):
            if not caminho.is_file() or caminho.is_symlink():
                continue
            if caminho.suffix.lower() not in extensoes or "__pycache__" in caminho.parts:
                continue
            relativo = caminho.relative_to(raiz)
            if relativo.as_posix() == "src/utils/dev_commands.py":
                continue
            yield caminho, relativo


def preparar_demo(destino, raiz=RAIZ):
    # Valida todos os arquivos de entrada antes de criar um pacote incompleto.
    arquivos = list(arquivos_distribuicao(raiz))
    destino = Path(destino).resolve()
    destino.parent.mkdir(parents=True, exist_ok=True)
    # Modo exclusivo: nunca sobrescrever uma distribuição já entregue.
    with ZipFile(destino, "x", compression=ZIP_DEFLATED) as pacote:
        for caminho, relativo in arquivos:
            pacote.write(caminho, "Oblivium/" + relativo.as_posix())
        pacote.writestr("Oblivium/apresentacao.json", json.dumps({"modo": "avaliacao", "versao": 1}))
    return destino


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destino", type=Path)
    args = parser.parse_args()
    destino = args.destino or RAIZ.parent / "dist" / ("Oblivium-demo-" + datetime.now().strftime("%Y%m%d-%H%M%S") + ".zip")
    print(preparar_demo(destino))


if __name__ == "__main__":
    main()
