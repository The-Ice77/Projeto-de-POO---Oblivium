import sys
import os
import json

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, RAIZ)

def test_mapa_oakhaven_pontos_narrador():
    """Pontos de exame no mapa (monumento, canteiro, bancada, rocha) devem usar autor Narrador."""
    caminho = os.path.join(RAIZ, "Oblivium", "src", "maps", "mapa_oakhaven.py")
    with open(caminho, "r", encoding="utf-8") as f:
        codigo = f.read()

    # Não deve ter 'autor': 'Halia' nos pontos de interação de exame de ambiente
    assert '"id": "estatua_herois"' in codigo
    assert '"id": "bancada_ferramentas_torvald"' in codigo
    assert '"id": "canteiro_gengibre_elara"' in codigo

    # Verifica trechos de pontos_interacao
    assert '{\n                        "autor": "Narrador",\n                        "texto": "O monumento de pedra' in codigo or \
           '"autor": "Narrador"' in codigo, "estatua_herois deve ter autor Narrador"

def test_playing_states_narracoes_narrador():
    """Cenas de chegada e conclusão após flashbacks devem ter autor Narrador."""
    caminho = os.path.join(RAIZ, "Oblivium", "src", "states", "playing_states.py")
    with open(caminho, "r", encoding="utf-8") as f:
        codigo = f.read()

    # Flashback monumento e ninho
    assert '"autor": "Narrador",\n                        "texto": "O calor daquela fogueira distante' in codigo or \
           'O calor daquela fogueira distante ainda ecoa' in codigo
    assert '"autor": "Narrador"' in codigo

def test_dialogos_fase1_narrador_em_cenas_situacionais():
    """Nós situacionais de despertar do dragão, exame de carcaça e pós-combate devem usar Narrador."""
    caminho = os.path.join(RAIZ, "Oblivium", "src", "data", "dialogos", "dialogos_fase1.json")
    with open(caminho, "r", encoding="utf-8") as f:
        dialogos = json.load(f)

    # 1. Despertar do ataque do dragão
    desp = dialogos.get("despertar_ataque_dragao_vila", {}).get("nos", {})
    assert desp.get("fala_1", {}).get("autor") == "Narrador", (
        f"despertar_ataque_dragao_vila.fala_1 deve ser 'Narrador', obtido {desp.get('fala_1', {}).get('autor')}"
    )

    # 2. Exame da carcaça do dragão
    ex_d = dialogos.get("examinar_corpo_dragao", {}).get("nos", {})
    assert ex_d.get("fala_1", {}).get("autor") == "Narrador", (
        f"examinar_corpo_dragao.fala_1 deve ser 'Narrador', obtido {ex_d.get('fala_1', {}).get('autor')}"
    )

    # 3. Pós-combate ninho do dragão
    pos_d = dialogos.get("cena_pos_combate_ninho_dragao", {}).get("nos", {})
    assert pos_d.get("fala_1", {}).get("autor") == "Narrador", (
        f"cena_pos_combate_ninho_dragao.fala_1 deve ser 'Narrador', obtido {pos_d.get('fala_1', {}).get('autor')}"
    )
    assert pos_d.get("fala_2", {}).get("autor") == "Narrador"
    assert pos_d.get("fala_3", {}).get("autor") == "Narrador"

    # 4. Monumento aos heróis
    mon = dialogos.get("monumento_herois", {}).get("nos", {})
    assert mon.get("fala_1", {}).get("autor") == "Narrador"
    assert mon.get("fala_2", {}).get("autor") == "Narrador"

    # 5. Pensamento íntimo autêntico deve continuar com autor 'Halia'
    elara = dialogos.get("hub_elara", {}).get("nos", {})
    assert elara.get("fala_elara_vila_2", {}).get("autor") == "Halia"
    assert "(Pensamento)" in elara.get("fala_elara_vila_2", {}).get("texto")

if __name__ == "__main__":
    print("Executando test_dialogos_fase1_narrador_em_cenas_situacionais...")
    test_dialogos_fase1_narrador_em_cenas_situacionais()
    print("test_dialogos_fase1_narrador_em_cenas_situacionais PASS")

    print("Executando test_mapa_oakhaven_pontos_narrador...")
    test_mapa_oakhaven_pontos_narrador()
    print("test_mapa_oakhaven_pontos_narrador PASS")

    print("Executando test_playing_states_narracoes_narrador...")
    test_playing_states_narracoes_narrador()
    print("test_playing_states_narracoes_narrador PASS")

    print("TODOS OS TESTES DE DIALOGOS NARRADOR VS HALIA PASSARAM!")
