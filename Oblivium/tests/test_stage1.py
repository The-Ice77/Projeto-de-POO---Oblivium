# tests/test_stage1.py
import os
import sys

# Garante inclusão do diretório raiz do projeto no path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame
pygame.init()
pygame.display.set_mode((1, 1), pygame.NOFRAME)

from src.mechanics.attributes import Atributos
from src.entities.Entity import Entidade
from src.entities.player import Player
from src.entities.Enemy import Enemy
from src.entities.Boss import Boss

def test_atributos():
    print("=== Testando Atributos ===")
    att = Atributos(forca=14, destreza=16, constituicao=12, intelecto=18, sabedoria=10, presenca=8)
    
    assert att.mod_for == 2, f"Esperado 2, obtido {att.mod_for}"
    assert att.mod_des == 3, f"Esperado 3, obtido {att.mod_des}"
    assert att.mod_con == 1, f"Esperado 1, obtido {att.mod_con}"
    assert att.mod_int == 4, f"Esperado 4, obtido {att.mod_int}"
    assert att.mod_sab == 0, f"Esperado 0, obtido {att.mod_sab}"
    assert att.mod_pre == -1, f"Esperado -1, obtido {att.mod_pre}"
    
    hp_max = att.calcular_vida_maxima(vida_base=50)
    mp_max = att.calcular_mana_maxima(mana_base=20)
    assert hp_max == 50 + (12 * 5), f"HP incorreto: {hp_max}"
    assert mp_max == 20 + (10 * 3), f"MP incorreto: {mp_max}"
    
    # Teste de Serialização
    data = att.to_dict()
    att2 = Atributos.from_dict(data)
    assert att2.intelecto == 18
    assert att2.presenca == 8
    print("-> Atributos: OK!")

def test_player():
    print("=== Testando Player (Halia) ===")
    halia = Player("Halia", 100, 210, 280, 3, mana_maxima=50)
    assert halia.atributos.intelecto == 15
    assert halia.atributos.presenca == 14
    
    # Teste de dano e cura
    dano_sofrido = halia.aplicar_dano(25, tipo="fisico")
    assert halia.vida_atual < 100
    assert dano_sofrido > 0
    
    halia.curar(100)
    assert halia.vida_atual == halia.vida_maxima
    
    # Teste de mana
    assert halia.gastar_mana(20) is True
    assert halia.mana_atual == halia.mana_maxima - 20
    halia.recuperar_mana(10)
    assert halia.mana_atual == halia.mana_maxima - 10
    print("-> Player: OK!")

def test_enemy_e_boss():
    print("=== Testando Enemy e Boss ===")
    sombra = Enemy("Sombra 1", 30, 2.5, 100, 100, dano=12)
    assert sombra.atributos.forca == 10
    assert isinstance(sombra, Entidade)
    
    boss = Boss("Anomalia Maior", 80, 2.0, 100, 100, dano=25)
    assert boss.atributos.forca == 14
    assert boss.atributos.constituicao == 16
    assert isinstance(boss, Enemy)
    assert isinstance(boss, Entidade)
    
    # Teste de combate entre Boss e Halia
    halia = Player("Halia", 100, 210, 280, 3, mana_maxima=50)
    vida_antes = halia.vida_atual
    dano_causado = boss.atacar(halia)
    assert halia.vida_atual < vida_antes
    assert dano_causado > 0
    
    # Teste de fase do Boss
    boss.receber_dano(60) # Vida cai abaixo de 40% (80 * 0.4 = 32)
    assert boss.verificar_mudanca_fase() is True
    assert boss.enfurecido is True
    print("-> Enemy e Boss: OK!")

if __name__ == "__main__":
    test_atributos()
    test_player()
    test_enemy_e_boss()
    print("\nTODOS OS TESTES DA ETAPA 1 PASSARAM COM SUCESSO!")
