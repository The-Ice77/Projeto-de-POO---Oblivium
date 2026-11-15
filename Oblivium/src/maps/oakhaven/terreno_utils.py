# src/maps/oakhaven/terreno_utils.py
import pygame
from src.utils.resource_manager import ResourceManager


def _carregar_tiles_terreno():
    """
    Carrega e escala (32x32) os tiles sólidos e bordas de Grama, Terra, Tijolo de Pedra
    e Calçamento a partir de Floors_Tiles.png e 02_Pisos_Externos.
    """
    tiles = {
        "grama_centro": [],
        "grama_borda": {},
        "terra_centro": [],
        "pedra_centro": [],
        "pedra_borda": {},
        "calca_centro": [],
        "calca_borda": {},
    }

    sheet_floors = ResourceManager.carregar_imagem("assets/cenario/pisos_externos/pedra/Floors_Tiles.png")
    if sheet_floors:
        def _sub32(col, lin):
            sub = sheet_floors.subsurface(pygame.Rect(col * 16, lin * 16, 16, 16)).copy()
            return pygame.transform.scale(sub, (32, 32))

        # 1. Grama Sólida (linha 11, colunas 1..3) + Bordas de Grama sobre Terra/Pedra (linhas 0..4, colunas 0..4)
        tiles["grama_centro"] = [_sub32(1, 11), _sub32(2, 11), _sub32(3, 11)]
        tiles["grama_borda"] = {
            "N": [_sub32(1, 0), _sub32(2, 0), _sub32(3, 0)],
            "S": [_sub32(1, 4), _sub32(2, 4), _sub32(3, 4)],
            "W": [_sub32(0, 1), _sub32(0, 2), _sub32(0, 3)],
            "E": [_sub32(4, 1), _sub32(4, 2), _sub32(4, 3)],
            "NW": _sub32(1, 1),
            "NE": _sub32(3, 1),
            "SW": _sub32(1, 3),
            "SE": _sub32(3, 3),
        }

        # 2. Terra Sólida (linha 11, colunas 11..13)
        tiles["terra_centro"] = [_sub32(11, 11), _sub32(12, 11), _sub32(13, 11)]

        # 3. Tijolos de Pedra Cinza Sólidos (linhas 1..3, colunas 16..18) + Bordas (colunas 15..19)
        tiles["pedra_centro"] = [
            _sub32(16, 1), _sub32(17, 1), _sub32(18, 1),
            _sub32(16, 2), _sub32(17, 2), _sub32(18, 2),
            _sub32(16, 3), _sub32(17, 3), _sub32(18, 3),
        ]
        tiles["pedra_borda"] = {
            "N": [_sub32(16, 0), _sub32(17, 0), _sub32(18, 0)],
            "S": [_sub32(16, 4), _sub32(17, 4), _sub32(18, 4)],
            "W": [_sub32(15, 1), _sub32(15, 2), _sub32(15, 3)],
            "E": [_sub32(19, 1), _sub32(19, 2), _sub32(19, 3)],
            "NW": _sub32(16, 1),
            "NE": _sub32(18, 1),
            "SW": _sub32(16, 3),
            "SE": _sub32(18, 3),
        }

        # 4. Calçamento de Pedra Sólido (linha 11, colunas 6..8) + Bordas (linhas 0..4, colunas 5..9)
        tiles["calca_centro"] = [_sub32(6, 11), _sub32(7, 11), _sub32(8, 11)]
        tiles["calca_borda"] = {
            "N": [_sub32(6, 0), _sub32(7, 0), _sub32(8, 0)],
            "S": [_sub32(6, 4), _sub32(7, 4), _sub32(8, 4)],
            "W": [_sub32(5, 1), _sub32(5, 2), _sub32(5, 3)],
            "E": [_sub32(9, 1), _sub32(9, 2), _sub32(9, 3)],
            "NW": _sub32(6, 1),
            "NE": _sub32(8, 1),
            "SW": _sub32(6, 3),
            "SE": _sub32(8, 3),
        }

    return tiles


def _renderizar_grade_autotile(largura_mundo, altura_mundo, grade, tiles, seed=4201):
    """
    Renderiza uma grade 2D de tiles 32x32 com autotiling orgânico:
    0 = Grama Verde Sólida
    1 = Caminho de Terra Marrom (com bordas orgânicas de grama sobrepostas)
    2 = Praça/Calçada de Tijolos de Pedra Cinza (com bordas de grama quando adjacente à grama)
    3 = Pátio Interno de Calçamento de Pedra (Floors_Tiles cols 5..9)
    """
    surf = pygame.Surface((largura_mundo, altura_mundo))
    surf.fill((75, 128, 52))
    cols = len(grade[0])
    rows = len(grade)

    grama_c = tiles["grama_centro"]
    terra_c = tiles["terra_centro"]
    pedra_c = tiles["pedra_centro"]
    calca_c = tiles["calca_centro"] or pedra_c
    gb = tiles["grama_borda"]

    def _tipo(gx, gy):
        if 0 <= gx < cols and 0 <= gy < rows:
            return grade[gy][gx]
        return grade[max(0, min(rows - 1, gy))][max(0, min(cols - 1, gx))]

    def _sobrepor_borda_grama(px, py, gx, gy):
        n_grama = (_tipo(gx, gy - 1) == 0)
        s_grama = (_tipo(gx, gy + 1) == 0)
        w_grama = (_tipo(gx - 1, gy) == 0)
        e_grama = (_tipo(gx + 1, gy) == 0)

        if n_grama and w_grama and gb.get("NW"):
            surf.blit(gb["NW"], (px, py))
        elif n_grama and e_grama and gb.get("NE"):
            surf.blit(gb["NE"], (px, py))
        elif s_grama and w_grama and gb.get("SW"):
            surf.blit(gb["SW"], (px, py))
        elif s_grama and e_grama and gb.get("SE"):
            surf.blit(gb["SE"], (px, py))
        else:
            if n_grama and gb.get("N"):
                surf.blit(gb["N"][gx % len(gb["N"])], (px, py))
            if s_grama and gb.get("S"):
                surf.blit(gb["S"][gx % len(gb["S"])], (px, py))
            if w_grama and gb.get("W"):
                surf.blit(gb["W"][gy % len(gb["W"])], (px, py))
            if e_grama and gb.get("E"):
                surf.blit(gb["E"][gy % len(gb["E"])], (px, py))

    for gy in range(rows):
        for gx in range(cols):
            px, py = gx * 32, gy * 32
            t = grade[gy][gx]

            # 1. Base de grama sólida sempre desenhada por baixo
            if grama_c:
                sp_g = grama_c[(gx * 3 + gy * 5) % len(grama_c)]
                surf.blit(sp_g, (px, py))

            if t == 0:
                continue

            # 2. Caminho de Terra + Bordas Orgânicas de Grama
            if t == 1:
                if terra_c:
                    sp_t = terra_c[(gx * 7 + gy * 13) % len(terra_c)]
                    surf.blit(sp_t, (px, py))
                else:
                    pygame.draw.rect(surf, (176, 124, 82), (px, py, 32, 32))
                _sobrepor_borda_grama(px, py, gx, gy)

            # 3. Calçada / Praça de Tijolos de Pedra Cinza
            elif t == 2:
                if pedra_c:
                    sp_p = pedra_c[(gx * 3 + gy * 7) % len(pedra_c)]
                    surf.blit(sp_p, (px, py))
                _sobrepor_borda_grama(px, py, gx, gy)

            # 4. Pátio Nobre de Calçamento (Coração da Praça Central)
            elif t == 3:
                if pedra_c:
                    surf.blit(pedra_c[(gx + gy) % len(pedra_c)], (px, py))
                if calca_c:
                    sp_c = calca_c[(gx * 5 + gy * 3) % len(calca_c)]
                    surf.blit(sp_c, (px, py))
                # Moldura sutil nos limites entre o calçamento interno (3) e os tijolos externos (2)
                n_out = (_tipo(gx, gy - 1) != 3)
                s_out = (_tipo(gx, gy + 1) != 3)
                w_out = (_tipo(gx - 1, gy) != 3)
                e_out = (_tipo(gx + 1, gy) != 3)
                cor_friso = (96, 92, 88)
                if n_out:
                    pygame.draw.line(surf, cor_friso, (px, py), (px + 31, py), 2)
                if s_out:
                    pygame.draw.line(surf, cor_friso, (px, py + 31), (px + 31, py + 31), 2)
                if w_out:
                    pygame.draw.line(surf, cor_friso, (px, py), (px, py + 31), 2)
                if e_out:
                    pygame.draw.line(surf, cor_friso, (px + 31, py), (px + 31, py + 31), 2)

    return surf


def criar_sombra_contato_estrutura(sprite, cor=(14, 18, 16, 75), offset_x_sol=2):
    """
    Gera superfície e offset (dx, dy) relativo a (ox, oy) de sombra de contato 2.5D
    ancorada na base opaca real do sprite (evitando sombras flutuantes em padding
    transparente ou ovais exageradamente largos sob pilares e vãos).
    """
    if sprite is None:
        return None, (0, 0)

    bb = sprite.get_bounding_rect()
    if bb.width <= 0 or bb.height <= 0:
        return None, (0, 0)

    mascara = pygame.mask.from_surface(sprite, 35)
    faixa_h = max(3, min(14, int(bb.height * 0.14)))
    y_ini = max(bb.top, bb.bottom - faixa_h)

    colunas_base = []
    for x in range(bb.left, bb.right):
        maior_y = -1
        for y in range(bb.bottom - 1, y_ini - 1, -1):
            if mascara.get_at((x, y)):
                maior_y = y
                break
        if maior_y >= 0:
            colunas_base.append((x, maior_y + 1))

    segmentos = []
    if colunas_base:
        seg_x0, seg_bot = colunas_base[0]
        seg_x1 = seg_x0
        for cx, cbot in colunas_base[1:]:
            if cx - seg_x1 <= 6:
                seg_x1 = cx
                if cbot > seg_bot:
                    seg_bot = cbot
            else:
                if seg_x1 - seg_x0 + 1 >= 4:
                    segmentos.append((seg_x0, seg_x1, seg_bot))
                seg_x0, seg_x1, seg_bot = cx, cx, cbot
        if seg_x1 - seg_x0 + 1 >= 4:
            segmentos.append((seg_x0, seg_x1, seg_bot))

    if not segmentos:
        segmentos = [(bb.left, bb.right - 1, bb.bottom)]

    elipses = []
    for x0, x1, y_bot in segmentos:
        seg_w = max(6, x1 - x0 + 1)
        larg_e = min(bb.width + 4, seg_w + min(4, max(0, seg_w // 10)))
        alt_e = max(6, min(14, int(min(seg_w * 0.26, bb.height * 0.14))))
        if bb.height < 28:
            alt_e = max(5, min(9, int(bb.height * 0.28)))
        ext_baixo = max(2, min(5, alt_e // 3 + 1))
        top_e = y_bot + ext_baixo - alt_e
        desloc_x = min(int(offset_x_sol), max(0, bb.right - x1 + 2))
        left_e = x0 + (seg_w - larg_e) // 2 + desloc_x
        elipses.append((left_e, top_e, larg_e, alt_e))

    min_x = min(e[0] for e in elipses)
    min_y = min(e[1] for e in elipses)
    max_x = max(e[0] + e[2] for e in elipses)
    max_y = max(e[1] + e[3] for e in elipses)

    sombra_surf = pygame.Surface((max(1, max_x - min_x), max(1, max_y - min_y)), pygame.SRCALPHA)
    r, g, b = cor[0], cor[1], cor[2]
    alpha_base = cor[3] if len(cor) >= 4 else 80
    alpha_penumbra = max(20, int(alpha_base * 0.55))
    alpha_nucleo = max(30, int(alpha_base * 0.90))

    for lx, ty, lw, lh in elipses:
        rx, ry = lx - min_x, ty - min_y
        pygame.draw.ellipse(sombra_surf, (r, g, b, alpha_penumbra), (rx, ry, lw, lh))
        nw = max(4, int(lw * 0.78))
        nh = max(4, int(lh * 0.68))
        nx = rx + (lw - nw) // 2
        ny = ry + (lh - nh) // 2
        pygame.draw.ellipse(sombra_surf, (r, g, b, alpha_nucleo), (nx, ny, nw, nh))

    return sombra_surf, (int(min_x), int(min_y))


def criar_sombra_silhueta_achatada(sprite, cor=(14, 10, 14, 95), escala_y=0.28, desloc_x=4, desloc_y=3):
    """Gera sombra contornada e achatada pela silhueta real para corpos horizontais deitados."""
    if sprite is None:
        return None, (0, 0)
    bb = sprite.get_bounding_rect()
    if bb.width <= 0 or bb.height <= 0:
        return None, (0, 0)

    recorte = sprite.subsurface(bb)
    mascara = pygame.mask.from_surface(recorte, 40)
    r, g, b = cor[0], cor[1], cor[2]
    alpha_base = cor[3] if len(cor) >= 4 else 95

    sil_ext = mascara.to_surface(
        setcolor=(r, g, b, max(20, int(alpha_base * 0.55))), unsetcolor=(0, 0, 0, 0)
    ).convert_alpha()
    sil_int = mascara.to_surface(
        setcolor=(r, g, b, max(30, int(alpha_base * 0.85))), unsetcolor=(0, 0, 0, 0)
    ).convert_alpha()

    w_ext = bb.width + 6
    h_ext = max(10, int(round(bb.height * escala_y)))
    w_int = max(4, int(round(bb.width * 0.96)))
    h_int = max(6, int(round(h_ext * 0.68)))

    surf_ext = pygame.transform.smoothscale(sil_ext, (w_ext, h_ext))
    surf_int = pygame.transform.smoothscale(sil_int, (w_int, h_int))

    final = pygame.Surface((w_ext, h_ext), pygame.SRCALPHA)
    final.blit(surf_ext, (0, 0))
    final.blit(surf_int, ((w_ext - w_int) // 2, (h_ext - h_int) // 2))

    dx = bb.left - 3 + int(desloc_x)
    dy = bb.bottom - h_ext + int(desloc_y)
    return final, (dx, dy)
