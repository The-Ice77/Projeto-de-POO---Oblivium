import sys
import os
import pygame

os.environ["SDL_VIDEODRIVER"] = "dummy"
pygame.init()
pygame.display.set_mode((1, 1))

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "Oblivium"))

from Oblivium.src.maps.mapa_oakhaven import MapaOakhavenDestruida
from Oblivium.src.entities.player import Player

def test_npcs_escondidos_durante_ataque():
    """Durante o ataque do dragão, todos os NPCs devem estar escondidos fora do mapa."""
    class MockGame:
        def __init__(self):
            self.desespero_superado = False
            self.dragao_derrotado = False
            self.itens_coletados = []
            self.slot_atual = None
            self.halia = Player("Halia", 100, 210, 280, 3)

    game = MockGame()
    mapa = MapaOakhavenDestruida(game, 1280, 720)
    mapa.inicializar_cenario()

    assert len(mapa.npcs) == 0, (
        f"Durante o ataque do dragão, NPCs devem estar escondidos! Encontrados: {len(mapa.npcs)}"
    )

def test_npcs_reunidos_na_praca_pos_dragao():
    """Após vencer o dragão, Aldous, Elara e Guarda Doran devem estar reunidos na praça para acolher Halia."""
    class MockGame:
        def __init__(self):
            self.desespero_superado = True
            self.dragao_derrotado = True
            self.itens_coletados = []
            self.slot_atual = None
            self.halia = Player("Halia", 100, 210, 280, 3)

    game = MockGame()
    mapa = MapaOakhavenDestruida(game, 1280, 720)
    mapa.inicializar_cenario()

    assert len(mapa.npcs) == 3, f"Esperado 3 NPCs reunidos na praça pós-dragão, obtido {len(mapa.npcs)}"

    ids_npcs = {npc.npc_id for npc in mapa.npcs}
    assert "anciao_aldous" in ids_npcs, "Ancião Aldous deve estar na praça"
    assert "curandeira_elara" in ids_npcs, "Curandeira Elara deve estar na praça"
    assert "guarda_doran" in ids_npcs, "Guarda Doran deve estar na praça"

    # Devem estar próximos uns dos outros na praça central (em torno de x=1050-1180, y=620-650)
    for npc in mapa.npcs:
        assert 1000 <= npc.x <= 1250, f"NPC {npc.nome} fora da praça central no eixo X: {npc.x}"
        assert 600 <= npc.y <= 680, f"NPC {npc.nome} fora da praça central no eixo Y: {npc.y}"

def test_cutscene_reconstrucao_visual_cenas():
    """A cutscene visual de reconstrução deve existir e transicionar entre as áreas destruídas e reconstruídas."""
    from Oblivium.src.mechanics.cutscene_reconstrucao_visual import CutsceneReconstrucaoVisual

    class MockGameCutscene:
        def __init__(self):
            self.LARGURA = 1280
            self.ALTURA = 720
            self.tela = pygame.Surface((1280, 720))
            self.halia = Player("Halia", 100, 210, 280, 3)
            self.mapa_casa = None
            self.audio = None
            self.slot_atual = None

    game = MockGameCutscene()
    cutscene = CutsceneReconstrucaoVisual(game)
    assert len(cutscene.cenas) >= 3, "Cutscene deve conter pelo menos 3 quadros visuais de reconstrução"

    # Inicia cutscene
    cutscene.iniciar()
    assert cutscene.ativo is True
    assert cutscene.indice_cena == 0

    # Simula progresso da primeira cena
    for _ in range(60):
        cutscene.atualizar(0.016)

    # Verifica que progresso de reconstrução suave opera entre 0.0 e 1.0
    assert 0.0 <= cutscene.progresso_reconstrucao <= 1.0

    # Testa renderização em superfície limpa sem estourar erros
    tela = pygame.Surface((1280, 720))
    cutscene.desenhar(tela)

if __name__ == "__main__":
    print("Executando test_npcs_escondidos_durante_ataque...")
    test_npcs_escondidos_durante_ataque()
    print("test_npcs_escondidos_durante_ataque PASS")

    print("Executando test_npcs_reunidos_na_praca_pos_dragao...")
    test_npcs_reunidos_na_praca_pos_dragao()
    print("test_npcs_reunidos_na_praca_pos_dragao PASS")

    print("Executando test_cutscene_reconstrucao_visual_cenas...")
    test_cutscene_reconstrucao_visual_cenas()
    print("test_cutscene_reconstrucao_visual_cenas PASS")

    print("TODOS OS TESTES DE RECONSTRUCAO VISUAL PASSARAM!")
