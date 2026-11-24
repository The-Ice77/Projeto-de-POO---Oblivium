"""Pequenas marcas no cenário, independentes de missões e da fauna."""

import pygame
from src.utils import constants


def _tracos(sprite, posicao, quantidade):
    x, y = posicao
    for i in range(quantidade):
        pygame.draw.line(sprite, (75, 62, 47), (x + i * 3, y + 5), (x + 2 + i * 3, y), 1)
        pygame.draw.line(sprite, (167, 145, 109), (x + i * 3 + 1, y + 5), (x + 3 + i * 3, y), 1)


def preparar_detalhes(mapa):
    """Monta as marcas, suas faixas de inspeção e a madeira da taverna."""
    mapa.indicios_assinatura = []
    mapa.assinatura_alvo = None
    if not constants.easter_egg_oakhaven_habilitado():
        return
    por_id = {e.get("id"): e for e in mapa.estruturas_ysort if e.get("id")}
    for identificador, estrutura, local, ponto, direcao, quantidade in (
        ("quadro", "quadro_vila", (78, 44), (1345, 878), "esquerda", 1),
        ("canteiro", "canteiro_elara", (1, 29), (310, 615), "direita", 2),
        ("bancada", "bancada_torvald", (57, 25), (1826, 618), "esquerda", 3),
    ):
        est = por_id.get(estrutura)
        if est is None:
            continue
        est["sprite"] = est["sprite"].copy()
        _tracos(est["sprite"], local, quantidade)
        hitbox = est["hitbox_ref"]
        # A face acompanha o objeto físico. O centro do corpo pode ocupar toda
        # a lateral, inclusive o canto inferior onde Halia para ao caminhar.
        inicio_x = hitbox.left - 56 if direcao == "direita" else hitbox.right - 4
        face = pygame.Rect(inicio_x, hitbox.top - 32, 60, hitbox.height + 64)
        mapa.indicios_assinatura.append({
            # Referência para validar o percurso; a ação usa face_interacao.
            "id": identificador, "ponto": ponto, "direcao": direcao,
            "marca": (est["x"] + local[0], est["y"] + local[1]),
            "face_interacao": face,
        })

    taverna = por_id.get("loja_taverna")
    if taverna is not None:
        # Peça sobre o poste de madeira do canto esquerdo, visível desde o chão.
        madeira = pygame.Surface((14, 28), pygame.SRCALPHA)
        pygame.draw.rect(madeira, (104, 77, 51), (0, 0, 14, 28))
        pygame.draw.rect(madeira, (133, 102, 66), (1, 1, 12, 26))
        for y in (5, 17, 24):
            pygame.draw.line(madeira, (108, 82, 54), (2, y), (11, y - 2))
        _tracos(madeira, (2, 10), 3)
        x, y = taverna["x"] + 64, taverna["y"] + 130
        est = mapa._add_estrutura_fn(
            madeira, x, y, hitbox_rel=(0, 0, 0, 0), sombra=False,
            y_sort_custom=taverna["y_sort"] + 1, id_estrutura="tabua_assinatura",
        )
        mapa.assinatura_alvo = {
            "ponto": (taverna["x"] + 42, taverna["y"] + 205),
            "direcao": "cima", "estrutura": est,
        }
        # Uma caneca pequena identifica o estabelecimento citado na primeira pista.
        taverna["sprite"] = taverna["sprite"].copy()
        placa = pygame.Rect(123, 126, 23, 17)
        pygame.draw.rect(taverna["sprite"], (91, 65, 44), placa, border_radius=2)
        pygame.draw.rect(taverna["sprite"], (216, 193, 139), (129, 130, 8, 10), border_radius=1)
        pygame.draw.rect(taverna["sprite"], (216, 193, 139), (136, 132, 5, 6), width=1)


def sprite_bancada():
    """Materializa a bancada que já possuía descrição e área de interação."""
    surf = pygame.Surface((68, 38), pygame.SRCALPHA)
    pygame.draw.rect(surf, (67, 48, 33), (6, 13, 7, 25))
    pygame.draw.rect(surf, (67, 48, 33), (54, 13, 7, 25))
    pygame.draw.rect(surf, (112, 80, 48), (2, 8, 64, 20))
    pygame.draw.rect(surf, (158, 121, 73), (0, 5, 68, 10))
    pygame.draw.line(surf, (89, 64, 40), (2, 11), (65, 11))
    pygame.draw.rect(surf, (106, 113, 116), (13, 1, 16, 5), border_radius=2)
    pygame.draw.line(surf, (94, 73, 45), (37, 2), (48, 9), 3)
    pygame.draw.rect(surf, (111, 117, 119), (44, 0, 8, 5))
    return surf


def desenhar_revelacao(mapa, tela):
    if not constants.easter_egg_oakhaven_habilitado():
        return
    segredo = getattr(mapa.game, "segredo_oakhaven", None)
    alvo = getattr(mapa, "assinatura_alvo", None)
    if segredo is None or alvo is None or mapa.nome != "OAKHAVEN":
        return
    est = alvo["estrutura"]
    x, y = est["x"], est["y"]
    if segredo.concluida:
        pygame.draw.rect(tela, (59, 44, 32), (x + 1, y + 2, 12, 24))
        pygame.draw.rect(tela, (191, 158, 95), (x + 2, y + 5, 10, 16))
        pygame.draw.line(tela, (78, 61, 43), (x + 4, y + 11), (x + 9, y + 11))
        pygame.draw.line(tela, (78, 61, 43), (x + 4, y + 15), (x + 9, y + 15))
    elif segredo.progresso > 0:
        pygame.draw.line(tela, (220, 203, 161), (x + 2, y + 22),
                         (x + 2 + int(9 * segredo.progresso), y + 10), 2)
