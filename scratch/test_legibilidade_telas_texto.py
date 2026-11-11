import sys
import os
import pygame

os.environ["SDL_VIDEODRIVER"] = "dummy"
pygame.init()
pygame.display.set_mode((1, 1))

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "Oblivium"))

from Oblivium.src.ui.transition import Transition
from Oblivium.src.utils.animations import ParticulaFlutuante, EfeitoPetalas
from Oblivium.src.mechanics.cinematica_dragao import CinematicaAtaqueDragao

def test_particula_respeita_area_excluida():
    """Uma partícula cujo ponto ou rect intercepta a área excluída não deve ser desenhada."""
    tela = pygame.Surface((1280, 720))
    sprite_teste = pygame.Surface((20, 20), pygame.SRCALPHA)
    sprite_teste.fill((255, 200, 200, 255))
    
    # Cria partícula posicionada exatamente no centro (640, 360)
    p = ParticulaFlutuante([sprite_teste], 1280, 720)
    p.x = 640
    p.y = 360
    
    area_proibida = pygame.Rect(600, 320, 100, 80)
    
    # Desenha em superfície limpa
    tela_teste = pygame.Surface((1280, 720), pygame.SRCALPHA)
    tela_teste.fill((0, 0, 0, 0))
    
    p.desenhar(tela_teste, areas_excluidas=[area_proibida])
    
    # Nenhum pixel deve ter sido desenhado dentro de area_proibida
    sub = tela_teste.subsurface(area_proibida)
    assert not any(sub.get_at((x, y))[3] > 0 for x in range(sub.get_width()) for y in range(sub.get_height())), (
        "Partícula desenhou dentro da área excluída do texto!"
    )

def test_transicao_passa_area_excluida_do_texto():
    """Quando Transition tem texto ativo, deve passar o rect do texto para efeito_petalas.desenhar."""
    t = Transition(1280, 720)
    t.estado = "EXIBINDO_TEXTO"
    t.texto_atual = "O mundo de Halia perdeu sua cor..."
    t.caractere_atual = len(t.texto_atual)
    t.alpha = 255
    t.texto_alpha = 255

    chamadas_areas = []
    def mock_desenhar(superficie, areas_excluidas=None, alpha_multiplicador=1.0):
        chamadas_areas.append(areas_excluidas)

    t.efeito_petalas.desenhar = mock_desenhar
    tela = pygame.Surface((1280, 720))
    t.desenhar(tela)

    assert len(chamadas_areas) > 0, "efeito_petalas.desenhar não foi chamado"
    assert chamadas_areas[0] is not None and len(chamadas_areas[0]) > 0, (
        "Transition não passou areas_excluidas para proteger a legibilidade do texto!"
    )
    rect = chamadas_areas[0][0]
    assert rect.collidepoint(640, 360), "A área excluída deve cobrir o centro da tela onde o texto é renderizado"

def test_cinematica_dragao_estetica_noite_sem_card_e_com_exclusao():
    """Na fase DORMINDO, a cinematica do dragão deve usar a estética limpa de flashback sem card e com exclusão de pétalas."""
    caminho = os.path.join(RAIZ, "Oblivium", "src", "mechanics", "cinematica_dragao.py")
    with open(caminho, "r", encoding="utf-8") as f:
        codigo = f.read()

    assert "surf_card" not in codigo, "Cinemática da noite não deve mais usar container de card/caixa ('surf_card')"
    assert "areas_excluidas" in codigo, "Cinemática da noite deve passar areas_excluidas ao desenhar pétalas"

if __name__ == "__main__":
    print("Executando test_particula_respeita_area_excluida...")
    test_particula_respeita_area_excluida()
    print("test_particula_respeita_area_excluida PASS")

    print("Executando test_transicao_passa_area_excluida_do_texto...")
    test_transicao_passa_area_excluida_do_texto()
    print("test_transicao_passa_area_excluida_do_texto PASS")

    print("Executando test_cinematica_dragao_estetica_noite_sem_card_e_com_exclusao...")
    test_cinematica_dragao_estetica_noite_sem_card_e_com_exclusao()
    print("test_cinematica_dragao_estetica_noite_sem_card_e_com_exclusao PASS")

    print("TODOS OS TESTES DE LEGIBILIDADE E NOITE PASSARAM!")
