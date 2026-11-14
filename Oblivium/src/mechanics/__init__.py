# src/mechanics/__init__.py
"""Pacote de mecânicas com aliases de retrocompatibilidade para módulos reorganizados."""

import importlib
import importlib.abc
import importlib.util
import sys

_ALIASES_LEGAIS = {
    f"{__name__}.minigame_base": f"{__name__}.minigames.minigame_base",
    f"{__name__}.minigame_ferraria": f"{__name__}.minigames.minigame_ferraria",
    f"{__name__}.minigame_curandeira": f"{__name__}.minigames.minigame_curandeira",
    f"{__name__}.combat_effects": f"{__name__}.combat.combat_effects",
    f"{__name__}.combat_input": f"{__name__}.combat.combat_input",
    f"{__name__}.combat_narrator": f"{__name__}.combat.combat_narrator",
    f"{__name__}.combat_renderer": f"{__name__}.combat.combat_renderer",
    f"{__name__}.cena_base": f"{__name__}.cutscenes.cena_base",
    f"{__name__}.cinematica_dragao": f"{__name__}.cutscenes.cinematica_dragao",
    f"{__name__}.cutscene_manager": f"{__name__}.cutscenes.cutscene_manager",
    f"{__name__}.cutscene_reconstrucao_visual": f"{__name__}.cutscenes.cutscene_reconstrucao_visual",
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


class _MechanicsAliasFinder(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        destino = _ALIASES_LEGAIS.get(fullname)
        if destino:
            return importlib.util.spec_from_loader(fullname, _AliasLoader(destino))
        return None


if not any(isinstance(f, _MechanicsAliasFinder) for f in sys.meta_path):
    sys.meta_path.insert(0, _MechanicsAliasFinder())


def __getattr__(name):
    fullname = f"{__name__}.{name}"
    if fullname in _ALIASES_LEGAIS:
        modulo = importlib.import_module(_ALIASES_LEGAIS[fullname])
        sys.modules[fullname] = modulo
        globals()[name] = modulo
        return modulo
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
