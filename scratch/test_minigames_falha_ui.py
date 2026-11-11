import sys
import os
import pygame

os.environ["SDL_VIDEODRIVER"] = "dummy"
pygame.init()
pygame.display.set_mode((1, 1))

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "Oblivium"))

from Oblivium.src.mechanics.minigame_curandeira import MinigameCurandeira
from Oblivium.src.mechanics.minigame_ferraria import MinigameFerraria
from Oblivium.src.mechanics.inventory import Inventario
from Oblivium.src.entities.player import Player
from Oblivium.src.entities.item import Item
from Oblivium.src.maps.mapa_oakhaven import MapaOakhaven
from Oblivium.src.states.playing_states import PlayingState

class MockHUD:
    def __init__(self):
        self.desenhado = False
    def desenhar(self, tela, game):
        self.desenhado = True

class MockQuestTracker:
    def __init__(self):
        self.desenhado = False
    def desenhar(self, tela, game):
        self.desenhado = True

class MockCaixaDialogo:
    def __init__(self):
        self.ativo = False
    def desenhar(self, tela):
        pass

class MockTransicao:
    def desenhar(self, tela):
        pass

class MockFlashback:
    def desenhar(self, tela):
        pass

class MockMg:
    def __init__(self):
        self.ativo = False
    def desenhar(self, tela):
        pass

class MockTelaDespertar:
    def __init__(self):
        self.estado = "INATIVO"

def test_hud_oculto_durante_minigames():
    """HUD e Quest Tracker não devem ser desenhados enquanto minigame_curandeira ou minigame_ferraria estiverem ativos."""
    class MockGame:
        def __init__(self):
            self.LARGURA = 1280
            self.ALTURA = 720
            self.tela = pygame.Surface((1280, 720))
            self.halia = Player("Halia", 100, 210, 280, 3)
            self.halia.inventario = Inventario()
            self.hud = MockHUD()
            self.quest_tracker = MockQuestTracker()
            self.caixa_dialogo = MockCaixaDialogo()
            self.transicao = MockTransicao()
            self.flashback_sistema = MockFlashback()
            self.mg_timing = MockMg()
            self.mg_mash = MockMg()
            self.tela_despertar = MockTelaDespertar()
            self.mapa_casa = None

    game = MockGame()
    ps = PlayingState(game)

    # 1. Sem minigames ativos: HUD e Tracker devem ser desenhados
    game.hud.desenhado = False
    game.quest_tracker.desenhado = False
    ps._draw_ui_overlays(game.tela)
    assert game.hud.desenhado is True, "HUD deveria ter sido desenhado sem minigame ativo"
    assert game.quest_tracker.desenhado is True, "Tracker deveria ter sido desenhado sem minigame ativo"

    # 2. Com minigame da curandeira ativo: HUD e Tracker devem ser suprimidos
    ps.minigame_curandeira.ativo = True
    game.hud.desenhado = False
    game.quest_tracker.desenhado = False
    ps._draw_ui_overlays(game.tela)
    assert game.hud.desenhado is False, "HUD NÃO deve ser desenhado durante minigame da curandeira!"
    assert game.quest_tracker.desenhado is False, "Tracker NÃO deve ser desenhado durante minigame da curandeira!"

    # 3. Com minigame da ferraria ativo: HUD e Tracker devem ser suprimidos
    ps.minigame_curandeira.ativo = False
    ps.minigame_ferraria.ativo = True
    game.hud.desenhado = False
    game.quest_tracker.desenhado = False
    ps._draw_ui_overlays(game.tela)
    assert game.hud.desenhado is False, "HUD NÃO deve ser desenhado durante minigame da ferraria!"
    assert game.quest_tracker.desenhado is False, "Tracker NÃO deve ser desenhado durante minigame da ferraria!"

def test_falha_colheita_murcha_e_respawn_alternativo():
    """Falhar no minigame da curandeira não concede o item, remove a erva murcha e spawna outra em local alternativo."""
    class MockGameCurandeira:
        def __init__(self):
            self.LARGURA = 1280
            self.ALTURA = 720
            self.tela = pygame.Surface((1280, 720))
            self.halia = Player("Halia", 100, 210, 280, 3)
            self.halia.inventario = Inventario()
            self.itens_coletados = []
            self.audio = None
            self.notificacoes = None
            self.missoes = None
            self.mapa_casa = MapaOakhaven(self, 1280, 720)

    game = MockGameCurandeira()
    mg = MinigameCurandeira(game)

    # Pega uma erva do mapa
    assert len(game.mapa_casa.ervas_coletaveis) > 0
    erva_original = game.mapa_casa.ervas_coletaveis[0]
    pos_original = (erva_original.x, erva_original.y)

    mg.iniciar(erva_original)
    assert mg.ativo is True
    assert hasattr(mg, "max_erros"), "MinigameCurandeira deve ter controle de erros máximos"

    # Força 2 erros propositais (fora da margem)
    mg.raio_atual = mg.raio_max # longe de raio_alvo
    mg._tentar_colheita() # 1 erro
    assert mg.erros == 1

    mg.raio_atual = mg.raio_max
    mg._tentar_colheita() # 2 erros -> Falha
    assert mg.estado == "FALHA_ANIMACAO", f"Esperado FALHA_ANIMACAO, obtido {mg.estado}"

    # Simula passagem dos frames de animação de falha
    for _ in range(70):
        mg.atualizar(0.016)

    assert mg.ativo is False, "Minigame deveria ter sido encerrado após a falha"
    assert game.halia.inventario.obter_quantidade("erva_lunar") == 0, "Halia não deve receber a erva se falhou!"
    assert erva_original not in game.mapa_casa.itens_no_chao, "A erva murcha deve ter sido removida do chão"

    # Verifica se uma nova erva alternativa foi gerada no mapa
    novas_ervas = [it for it in game.mapa_casa.itens_no_chao if "erva_lunar" in getattr(it, "id_unico", "")]
    assert len(novas_ervas) >= 3, "Uma nova erva de orvalho lunar alternativa deve ter sido gerada no mapa"
    nova_criada = next(it for it in novas_ervas if it != erva_original)
    assert (nova_criada.x, nova_criada.y) != pos_original, "A nova erva deve estar em local alternativo da vila"

if __name__ == "__main__":
    print("Executando test_hud_oculto_durante_minigames...")
    test_hud_oculto_durante_minigames()
    print("test_hud_oculto_durante_minigames PASS")

    print("Executando test_falha_colheita_murcha_e_respawn_alternativo...")
    test_falha_colheita_murcha_e_respawn_alternativo()
    print("test_falha_colheita_murcha_e_respawn_alternativo PASS")

    print("TODOS OS TESTES DE MINIGAMES PASSARAM!")
