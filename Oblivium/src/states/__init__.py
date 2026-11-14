# src/states/__init__.py
"""Pacote de estados com aliases de retrocompatibilidade para módulos reorganizados."""

import importlib
import importlib.abc
import importlib.util
import sys

_ALIASES_LEGAIS = {
    f"{__name__}.playing_states": f"{__name__}.playing.playing_states",
    f"{__name__}.prologo_controller": f"{__name__}.playing.prologo_controller",
    f"{__name__}.oakhaven_controller": f"{__name__}.playing.oakhaven_controller",
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


class _StatesAliasFinder(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        destino = _ALIASES_LEGAIS.get(fullname)
        if destino:
            return importlib.util.spec_from_loader(fullname, _AliasLoader(destino))
        return None


if not any(isinstance(f, _StatesAliasFinder) for f in sys.meta_path):
    sys.meta_path.insert(0, _StatesAliasFinder())


def __getattr__(name):
    fullname = f"{__name__}.{name}"
    if fullname in _ALIASES_LEGAIS:
        modulo = importlib.import_module(_ALIASES_LEGAIS[fullname])
        sys.modules[fullname] = modulo
        globals()[name] = modulo
        return modulo
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
