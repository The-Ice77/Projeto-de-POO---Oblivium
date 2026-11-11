import sys
import os
import json
import pygame

# Inicialização headless do pygame
os.environ["SDL_VIDEODRIVER"] = "dummy"
pygame.init()
pygame.display.set_mode((1, 1))

# Adicionar diretório raiz ao path
RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, RAIZ)

from Oblivium.src.mechanics.quest_manager import QuestManager
from Oblivium.src.entities.player import Player
from Oblivium.src.mechanics.inventory import Inventario
from Oblivium.src.entities.NPC import NPC
from Oblivium.src.maps.mapa_oakhaven import MapaOakhaven

class MockGame:
    def __init__(self):
        self.largura = 1280
        self.altura = 720
        self.tela = pygame.Surface((self.largura, self.altura))
        self.halia = Player(100, 100)
        self.halia.inventario = Inventario()
        self.missoes = QuestManager(self)
        self.lojas_dados = {}
        caminho_lojas = os.path.join(RAIZ, "Oblivium", "src", "data", "lojas.json")
        with open(caminho_lojas, "r", encoding="utf-8") as f:
            self.lojas_dados = json.load(f)

    def abrir_loja(self, loja_id):
        if loja_id in self.lojas_dados:
            return True
        return False

def test_elara_npc_loja_id():
    """Elara no MapaOakhaven deve ter loja_id 'botanica_elara' e existir em lojas.json."""
    game = MockGame()
    mapa = MapaOakhaven(game, 1280, 720)
    elara = None
    for npc in mapa.npcs:
        if npc.npc_id == "curandeira_elara":
            elara = npc
            break
    assert elara is not None, "Elara não encontrada no MapaOakhaven"
    assert elara.loja_id == "botanica_elara", f"loja_id de Elara é '{elara.loja_id}', esperado 'botanica_elara'"
    assert game.abrir_loja(elara.loja_id) is True, f"Loja '{elara.loja_id}' não existe no catálogo lojas.json"

def test_coleta_previa_e_conclusao_com_consumo():
    """Halia coleta 3 ervas antes de aceitar a missão. Ao aceitar e entregar, 3 ervas devem ser consumidas e loja liberada."""
    game = MockGame()
    qm = game.missoes
    halia = game.halia

    # 1. Halia coleta 3 ervas antes de aceitar a missão
    halia.inventario.adicionar_item("erva_lunar", 3)
    assert halia.inventario.obter_quantidade("erva_lunar") == 3

    # 2. Aceita a missão da Elara
    qm.aceitar_missao("missao_ervas_medicinais")
    missao = qm.missoes["missao_ervas_medicinais"]
    assert missao["status"] == "ATIVA"

    # Objetivo coletar_ervas deve estar concluído (3/3)
    obj_coleta = next(o for o in missao["objetivos"] if o["id"] == "coletar_ervas")
    assert obj_coleta["atual"] == 3, f"Esperado 3 ervas no objetivo, obtido {obj_coleta['atual']}"
    assert obj_coleta["concluido"] is True

    # 3. Deve estar pronta para entregar
    assert qm.pronta_para_entregar("missao_ervas_medicinais") is True

    # 4. Processa entrega e conclusão
    res = qm.processar_interacao_npc("curandeira_elara")
    assert res["estado"] == "CONCLUIDA"
    assert missao["status"] == "CONCLUIDA"

    # 5. Exatamente 3 ervas devem ter sido consumidas do inventário
    assert halia.inventario.obter_quantidade("erva_lunar") == 0, (
        f"Esperado 0 ervas no inventário, obtido {halia.inventario.obter_quantidade('erva_lunar')}"
    )

    # 6. NPC Elara agora deve permitir abrir a loja
    elara = NPC(nome="Curandeira Elara", x=0, y=0, npc_id="curandeira_elara", tem_loja=True, loja_id="botanica_elara", arquetipo="curandeira")
    assert elara.pode_abrir_loja(qm) is True

if __name__ == "__main__":
    print("Executando test_elara_npc_loja_id...")
    test_elara_npc_loja_id()
    print("test_elara_npc_loja_id PASS")

    print("Executando test_coleta_previa_e_conclusao_com_consumo...")
    test_coleta_previa_e_conclusao_com_consumo()
    print("test_coleta_previa_e_conclusao_com_consumo PASS")
    print("TODOS OS TESTES DE ELARA PASSARAM!")
