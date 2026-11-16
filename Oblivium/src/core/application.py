"""Ciclo de inicialização: perfil, dependência gráfica e execução do jogo."""
import importlib
from importlib import metadata
import os
from pathlib import Path
import subprocess
import sys
from uuid import uuid4

from src.utils.constants import PASTA_OBLIVIUM
from src.utils import save_storage as save_io


class Aplicacao:
    VERSAO_PYGAME = "2.6.1"

    def __init__(self, pasta=None):
        self.pasta = Path(pasta or PASTA_OBLIVIUM)

    def criar_atalho_windows(self):
        """Cria um atalho local com a logo; sua ausência não impede o jogo.

        O Windows mantém um ícone comum para arquivos .bat. O .lnk referencia
        o iniciador e o ícone nesta instalação, sem alterar associações globais.
        """
        if os.name != "nt":
            return False
        raiz = self.pasta.resolve()
        icone = raiz / "assets" / "oblivium.ico"
        iniciador = raiz / "Iniciar Oblivium.bat"
        atalho = raiz / "Oblivium.lnk"
        if not icone.is_file() or not iniciador.is_file():
            return False
        if atalho.exists():
            return atalho.is_file()
        comando = """+$ErrorActionPreference = 'Stop'
$raiz = $env:OBLIVIUM_ATALHO_RAIZ
$shell = New-Object -ComObject WScript.Shell
$atalho = $shell.CreateShortcut((Join-Path $raiz 'Oblivium.lnk'))
$atalho.TargetPath = Join-Path $raiz 'Iniciar Oblivium.bat'
$atalho.WorkingDirectory = $raiz
$atalho.IconLocation = (Join-Path $raiz 'assets\oblivium.ico') + ',0'
$atalho.Description = 'Iniciar Oblivium'
$atalho.Save()
"""
        ambiente = os.environ.copy()
        ambiente["OBLIVIUM_ATALHO_RAIZ"] = str(raiz)
        powershell = (Path(os.environ.get("SystemRoot", r"C:\Windows"))
                      / "System32" / "WindowsPowerShell" / "v1.0" / "powershell.exe")
        try:
            resultado = subprocess.run(
                [str(powershell), "-NoProfile", "-NonInteractive", "-Command", comando],
                env=ambiente, capture_output=True, check=False, timeout=15,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        except (OSError, subprocess.TimeoutExpired):
            return False
        return resultado.returncode == 0 and atalho.is_file()

    @classmethod
    def pygame_compativel(cls):
        """Confere a versão e executa a conversão usada pelo filtro, sem janela."""
        try:
            if metadata.version("pygame") != cls.VERSAO_PYGAME:
                return False
            pygame = importlib.import_module("pygame")
            if pygame.version.ver != cls.VERSAO_PYGAME:
                return False
            origem = pygame.Surface((1, 1), depth=32)
            destino = pygame.Surface((1, 1), depth=32)
            origem.fill((180, 70, 20))
            pygame.transform.grayscale(origem, destino)
            r, g, b, _ = destino.get_at((0, 0))
            return r == g == b and 0 < r < 255
        except (metadata.PackageNotFoundError, ImportError, AttributeError, TypeError, RuntimeError):
            return False

    def _python_local(self):
        pasta_bin = "Scripts" if os.name == "nt" else "bin"
        nome = "python.exe" if os.name == "nt" else "python"
        return self.pasta / ".venv" / pasta_bin / nome

    def _ambiente_local_compativel(self, interpretador):
        # Extensões nativas são verificadas num processo novo antes da execução.
        codigo = (
            "from src.core.application import Aplicacao; "
            "raise SystemExit(0 if Aplicacao.pygame_compativel() else 1)"
        )
        resultado = subprocess.run(
            [str(interpretador), "-c", codigo], cwd=self.pasta,
            capture_output=True, check=False,
        )
        return resultado.returncode == 0

    def _interpretador_local_valido(self, interpretador):
        """Uma .venv copiada ou cujo Python foi removido precisa ser refeita."""
        codigo = (
            "import sys; from pathlib import Path; "
            "valido = (3, 10) <= sys.version_info[:2] <= (3, 13) "
            "and Path(sys.prefix).resolve() == Path(sys.argv[1]).resolve(); "
            "raise SystemExit(0 if valido else 1)"
        )
        try:
            resultado = subprocess.run(
                [str(interpretador), "-c", codigo, str(self.pasta.resolve() / ".venv")],
                capture_output=True, check=False,
            )
            return resultado.returncode == 0
        except OSError:
            return False

    def _preparar_interpretador_local(self):
        raiz = self.pasta.resolve()
        pasta_venv = raiz / ".venv"
        # Nunca mover uma ligação/junção que aponta para outro diretório.
        if pasta_venv.is_symlink() or pasta_venv.resolve() != pasta_venv:
            raise OSError("A pasta .venv é uma ligação para outro diretório; use uma pasta local do jogo.")
        interpretador = self._python_local()
        if interpretador.is_file() and self._interpretador_local_valido(interpretador):
            return interpretador
        if pasta_venv.exists():
            backup = raiz / (".venv_backup_" + uuid4().hex[:12])
            if backup.parent != raiz or backup.exists():
                raise OSError("Não foi possível reservar um backup para o ambiente anterior.")
            pasta_venv.rename(backup)
            print(f"Ambiente anterior preservado em {backup.name}.", flush=True)
        print("Preparando o ambiente local de Oblivium...", flush=True)
        subprocess.run([sys.executable, "-m", "venv", str(pasta_venv)], check=True)
        return interpretador

    @staticmethod
    def _garantir_pip(interpretador):
        resultado = subprocess.run(
            [str(interpretador), "-m", "pip", "--version"], capture_output=True, check=False,
        )
        if resultado.returncode != 0:
            print("Preparando o pip no ambiente local...", flush=True)
            subprocess.run([str(interpretador), "-m", "ensurepip", "--upgrade"], check=True)

    def _executar_ambiente_local(self, argumentos):
        if os.environ.get("OBLIVIUM_AMBIENTE_PREPARADO") == "1":
            print("O pygame instalado não passou na verificação do filtro. "
                  "Recrie a pasta .venv do jogo e tente iniciar novamente.", file=sys.stderr)
            return 1
        try:
            interpretador = self._preparar_interpretador_local()
            if not self._ambiente_local_compativel(interpretador):
                self._garantir_pip(interpretador)
                print(f"Instalando pygame {self.VERSAO_PYGAME} para o filtro de memória...", flush=True)
                subprocess.run([
                    str(interpretador), "-m", "pip", "install", "--disable-pip-version-check",
                    "--only-binary=:all:", "--upgrade", "--force-reinstall",
                    "-r", str(self.pasta / "requirements.txt"),
                ], check=True)
            ambiente = os.environ.copy()
            ambiente["OBLIVIUM_AMBIENTE_PREPARADO"] = "1"
            return subprocess.run(
                [str(interpretador), str(self.pasta / "iniciar.py"), *argumentos],
                cwd=self.pasta, env=ambiente, check=False,
            ).returncode
        except (OSError, subprocess.CalledProcessError) as erro:
            print("Não foi possível preparar o ambiente do jogo. "
                  f"Confira a mensagem acima e o acesso à pasta. Detalhe: {erro}", file=sys.stderr)
            return 1

    def executar(self, argv=None):
        argumentos = list(sys.argv[1:] if argv is None else argv)
        # --help e opções inválidas são tratados antes de qualquer instalação.
        perfil = save_io.configurar_perfil(argumentos)
        if not (3, 10) <= sys.version_info[:2] <= (3, 13):
            print("Oblivium requer Python 3.10 a 3.13 para instalar o pygame 2.6.1. "
                  f"Versão selecionada: {sys.version_info.major}.{sys.version_info.minor}.", file=sys.stderr)
            return 1
        if not self.pygame_compativel():
            # Mantém o mesmo participante ao trocar de interpretador.
            reentrada = ["--perfil", perfil] if perfil else argumentos
            return self._executar_ambiente_local(reentrada)

        self.criar_atalho_windows()
        import pygame
        from src.core.game import Game

        pygame.init()
        try:
            Game().run()
        finally:
            pygame.quit()
        return 0
