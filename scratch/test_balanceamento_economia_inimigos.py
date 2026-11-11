import sys
import os
import json
import pygame

os.environ["SDL_VIDEODRIVER"] = "dummy"
pygame.init()
pygame.display.set_mode((1, 1))

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, RAIZ)

from Oblivium.src.entities.enemy_factory import EnemyFactory
from Oblivium.src.entities.player import Player

def test_bestiario_balanceamento():
    """Valida calibração dos status do Demônio Olho e do Dragão Vermelho."""
    caminho = os.path.join(RAIZ, "Oblivium", "src", "data", "bestiario.json")
    with open(caminho, "r", encoding="utf-8") as f:
        bestiario = json.load(f)

    olho = bestiario["demonio_olho"]
    assert olho["dano_base"] <= 9, f"Dano base de demonio_olho ({olho['dano_base']}) deve ser <= 9"
    assert olho["vida_base"] <= 45, f"Vida base de demonio_olho ({olho['vida_base']}) deve ser <= 45"

    dragao = bestiario["dragao_vermelho"]
    assert dragao["vida_base"] >= 160, f"Vida base do Dragão ({dragao['vida_base']}) deve ser >= 160"
    assert dragao["dano_base"] >= 16, f"Dano base do Dragão ({dragao['dano_base']}) deve ser >= 16"

def test_inimigos_estrada_e_patrulha_sao_inferiores():
    """Verifica que playing_states e enemy_factory usam demonio_inferior na estrada e orla norte."""
    caminho_ps = os.path.join(RAIZ, "Oblivium", "src", "states", "playing_states.py")
    with open(caminho_ps, "r", encoding="utf-8") as f:
        conteudo = f.read()

    # Na estrada (cutscene de encontro) e na patrulha da orla norte com Doran
    assert 'EnemyFactory.criar("demonio_olho", x=1180' not in conteudo, (
        "Estrada não deve instanciar demonio_olho, deve ser demonio_inferior"
    )
    assert 'EnemyFactory.criar("demonio_olho", x=565' not in conteudo, (
        "Patrulha do Doran na orla norte não deve instanciar demonio_olho, deve ser demonio_inferior"
    )

def test_bolsa_moedas_valor():
    """A Bolsa de Moedas deve conceder exatamente 50 moedas (5 de ouro), impedindo inflação."""
    caminho_ps = os.path.join(RAIZ, "Oblivium", "src", "states", "playing_states.py")
    with open(caminho_ps, "r", encoding="utf-8") as f:
        conteudo = f.read()

    assert "self.game.halia.ganhar_dinheiro(1000)" not in conteudo, (
        "Bolsa de moedas ainda está concedendo 1000 moedas em vez de 50!"
    )
    assert "self.game.halia.ganhar_dinheiro(50)" in conteudo, (
        "Esperado self.game.halia.ganhar_dinheiro(50) ao coletar item_moedas"
    )

if __name__ == "__main__":
    print("Executando test_bestiario_balanceamento...")
    test_bestiario_balanceamento()
    print("test_bestiario_balanceamento PASS")

    print("Executando test_inimigos_estrada_e_patrulha_sao_inferiores...")
    test_inimigos_estrada_e_patrulha_sao_inferiores()
    print("test_inimigos_estrada_e_patrulha_sao_inferiores PASS")

    print("Executando test_bolsa_moedas_valor...")
    test_bolsa_moedas_valor()
    print("test_bolsa_moedas_valor PASS")

    print("TODOS OS TESTES DE BALANCEAMENTO E ECONOMIA PASSARAM!")
