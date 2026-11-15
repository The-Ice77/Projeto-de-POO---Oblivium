# src/maps/__init__.py
"""Pacote de mapas com aliases de retrocompatibilidade para cenários reorganizados."""

import importlib
import importlib.abc
import importlib.util
import sys

_ALIASES_LEGAIS = {
    f"{__name__}.mapa_casa": f"{__name__}.prologo.mapa_casa",
    f"{__name__}.mapa_estrada": f"{__name__}.prologo.mapa_estrada",
    f"{__name__}.mapa_estrada_2": f"{__name__}.prologo.mapa_estrada_2",
}


class _AliasLoader(importlib.abc.Loader):
    def __init__(self, destino):
        self.destino = destino

    def create_module(self, spec):
        modulo = importlib.import_module(self.destino)
        sys.modules[spec.name] = modulo
        return modulo

    def exec_module(self, module):
        pass


class _MapsAliasFinder(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        destino = _ALIASES_LEGAIS.get(fullname)
        if destino:
            return importlib.util.spec_from_loader(fullname, _AliasLoader(destino))
        return None


if not any(isinstance(f, _MapsAliasFinder) for f in sys.meta_path):
    sys.meta_path.insert(0, _MapsAliasFinder())


def __getattr__(name):
    fullname = f"{__name__}.{name}"
    if fullname in _ALIASES_LEGAIS:
        modulo = importlib.import_module(_ALIASES_LEGAIS[fullname])
        sys.modules[fullname] = modulo
        globals()[name] = modulo
        return modulo
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
