import sys
import os
import pygame

os.environ["SDL_VIDEODRIVER"] = "dummy"
pygame.init()
pygame.display.set_mode((1, 1))

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "Oblivium"))

from Oblivium.src.entities.NPC import NPC

def test_arquivos_sprites_guarda_doran():
    """Verifica que a pasta guarda_doran existe com os frames recortados de idle e walk."""
    pasta_idle = os.path.join(RAIZ, "Oblivium", "assets", "npc", "guarda_doran", "idle")
    pasta_walk = os.path.join(RAIZ, "Oblivium", "assets", "npc", "guarda_doran", "walk")

    assert os.path.isdir(pasta_idle), f"Pasta de idle do Guarda Doran não existe: {pasta_idle}"
    assert os.path.isdir(pasta_walk), f"Pasta de walk do Guarda Doran não existe: {pasta_walk}"

    frames_idle = [f for f in os.listdir(pasta_idle) if f.lower().endswith(".png")]
    frames_walk = [f for f in os.listdir(pasta_walk) if f.lower().endswith(".png")]

    assert len(frames_idle) >= 4, f"Esperado pelo menos 4 frames de idle, obtido {len(frames_idle)}"
    assert len(frames_walk) >= 4, f"Esperado pelo menos 4 frames de walk, obtido {len(frames_walk)}"

def test_npc_resolucao_pastas():
    """Guarda Doran deve usar pasta 'guarda_doran' e Carroceiro deve usar 'aventureiro'."""
    doran = NPC(nome="Guarda Doran", x=100, y=100, npc_id="guarda_doran", arquetipo="guarda")
    assert doran._resolver_pasta_sprites() == "guarda_doran", (
        f"Guarda Doran deve resolver para 'guarda_doran', obteve '{doran._resolver_pasta_sprites()}'"
    )

    carroceiro = NPC(nome="Carroceiro", x=1350, y=330)
    assert carroceiro._resolver_pasta_sprites() == "aventureiro", (
        f"Carroceiro deve resolver para 'aventureiro', obteve '{carroceiro._resolver_pasta_sprites()}'"
    )

if __name__ == "__main__":
    print("Executando test_arquivos_sprites_guarda_doran...")
    test_arquivos_sprites_guarda_doran()
    print("test_arquivos_sprites_guarda_doran PASS")

    print("Executando test_npc_resolucao_pastas...")
    test_npc_resolucao_pastas()
    print("test_npc_resolucao_pastas PASS")

    print("TODOS OS TESTES DE SPRITES DO GUARDA E CARROCEIRO PASSARAM!")
