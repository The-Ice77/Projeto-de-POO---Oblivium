# src/ui/menu_secret.py
import math
import random
import pygame
from src.utils import constants
from src.utils.colors import (
    AZUL_HOVER_BG,
    AZUL_HOVER_MENU,
    CARVAO_PROFUNDO,
    DOURADO_ENVELHECIDO,
    MARFIM_OFFWHITE,
)
from src.utils.resource_manager import ResourceManager


class SegredoMenuCheats:
    """
    Dinâmica oculta da tela inicial para liberação do console de cheats (ComandosDev):
    1. Clicar em 3 pétalas sutis caindo ao fundo (`FOLHAS`).
    2. Arrastar a insígnia de versão de Oblivium suavemente para cima (`VERSAO_LIBERADA`).
    3. Acionar o botão escondido revelado sob a versão (`BOTAO_REVELADO` -> `CHEATS_LIBERADOS`).
    """

    CONQUISTA_ID = "segredo_menu_cheats"
    TOTAL_FOLHAS = 3
    DESLOCAMENTO_MAX_VERSAO = 60
    LIMIAR_TRAVAR_VERSAO = 44

    def __init__(self, efeito_petalas, pos_versao, tamanho_versao):
        self.efeito_petalas = efeito_petalas
        self.pos_versao = (int(pos_versao[0]), int(pos_versao[1]))
        self.tamanho_versao = (max(120, int(tamanho_versao[0])), max(32, int(tamanho_versao[1])))
        self.disponivel = not constants.modo_apresentacao()

        self.etapa = "FOLHAS"
        self.folhas_coletadas = 0
        self.versao_offset_y = 0.0
        self.versao_offset_alvo = 0.0
        self.arrastando_versao = False
        self._drag_inicio_mouse_y = 0
        self._drag_inicio_offset_y = 0.0

        self.revelacao_progresso = 0.0
        self.alpha_dica_versao = 0.0

        self.hover_versao = False
        self.hover_botao = False
        self.tempo_anim = 0.0
        self.pulso_versao = 0.0
        self.faiscas = []
        self._cache_sprites_douradas = {}
        self.fonte_botao = ResourceManager.carregar_fonte("contrail", 14)

        self.sincronizar_petalas()

    def obter_rect_compartimento(self):
        return pygame.Rect(
            self.pos_versao[0],
            self.pos_versao[1],
            self.tamanho_versao[0],
            self.tamanho_versao[1],
        )

    def obter_rect_versao_atual(self):
        return pygame.Rect(
            self.pos_versao[0],
            int(round(self.pos_versao[1] + self.versao_offset_y)),
            self.tamanho_versao[0],
            self.tamanho_versao[1],
        )

    def obter_rect_botao_secreto(self):
        vx, vy = self.pos_versao
        vw, vh = self.tamanho_versao
        return pygame.Rect(vx + 4, vy + 4, max(120, vw - 8), max(28, vh - 8))

    def sincronizar_petalas(self):
        particulas = getattr(self.efeito_petalas, "particulas", None) or []
        if not self.disponivel or self.etapa != "FOLHAS":
            for p in particulas:
                p.folha_secreta = False
            return

        necessarias = max(0, self.TOTAL_FOLHAS - self.folhas_coletadas)
        marcadas = [p for p in particulas if getattr(p, "folha_secreta", False)]

        if len(marcadas) > necessarias:
            for extra in marcadas[necessarias:]:
                extra.folha_secreta = False
            marcadas = marcadas[:necessarias]

        faltam = necessarias - len(marcadas)
        if faltam > 0:
            candidatas = [p for p in particulas if not getattr(p, "folha_secreta", False)]
            grandes = [
                p for p in candidatas
                if getattr(p, "sprite_base", None) is not None and max(p.sprite_base.get_size()) >= 28
            ]
            pool = grandes if len(grandes) >= faltam else (grandes + [p for p in candidatas if p not in grandes])
            for p in pool[:faltam]:
                p.folha_secreta = True
                marcadas.append(p)

        for p in marcadas:
            p.vy = min(float(getattr(p, "vy", 48.0)), 48.0)

    def _emitir_faiscas(self, cx, cy, quantidade=6):
        for _ in range(quantidade):
            ang = random.uniform(0.0, math.tau)
            vel = random.uniform(18.0, 58.0)
            vida = random.uniform(0.24, 0.45)
            self.faiscas.append({
                "x": float(cx),
                "y": float(cy),
                "vx": math.cos(ang) * vel,
                "vy": math.sin(ang) * vel - 8.0,
                "vida": vida,
                "vida_max": vida,
                "raio": random.choice((1, 1, 2)),
            })

    def atualizar(self, dt=0.016):
        dt = float(dt) if isinstance(dt, (int, float)) and dt > 0 else (1.0 / 60.0)
        self.tempo_anim += dt
        if self.pulso_versao > 0.0:
            self.pulso_versao = max(0.0, self.pulso_versao - dt)

        restantes = []
        for f in self.faiscas:
            f["vida"] -= dt
            if f["vida"] > 0.0:
                f["x"] += f["vx"] * dt
                f["y"] += f["vy"] * dt
                f["vy"] += 26.0 * dt
                restantes.append(f)
        self.faiscas = restantes

        if self.disponivel:
            self.sincronizar_petalas()

        if self.arrastando_versao:
            taxa_pos = 12.0
        elif self.etapa in ("BOTAO_REVELADO", "CHEATS_LIBERADOS"):
            taxa_pos = 6.5
        else:
            taxa_pos = 7.5

        diff = self.versao_offset_alvo - self.versao_offset_y
        if abs(diff) <= 0.25:
            self.versao_offset_y = float(self.versao_offset_alvo)
        else:
            self.versao_offset_y += diff * (1.0 - math.exp(-dt * taxa_pos))

        if self.disponivel and (self.etapa in ("BOTAO_REVELADO", "CHEATS_LIBERADOS") or self.versao_offset_y < -4.0):
            if self.etapa in ("BOTAO_REVELADO", "CHEATS_LIBERADOS"):
                alvo_rev = 1.0
            else:
                alvo_rev = min(
                    1.0, max(0.0, (-self.versao_offset_y - 4.0) / float(self.DESLOCAMENTO_MAX_VERSAO - 4.0))
                )
        else:
            alvo_rev = 0.0

        diff_rev = alvo_rev - self.revelacao_progresso
        if abs(diff_rev) <= 0.005:
            self.revelacao_progresso = alvo_rev
        else:
            self.revelacao_progresso += diff_rev * (1.0 - math.exp(-dt * 9.0))

        dica_alvo = (
            1.0
            if (
                self.disponivel
                and self.etapa == "VERSAO_LIBERADA"
                and (self.pulso_versao > 0.0 or self.hover_versao or self.arrastando_versao)
            )
            else 0.0
        )
        diff_dica = dica_alvo - self.alpha_dica_versao
        if abs(diff_dica) <= 0.005:
            self.alpha_dica_versao = dica_alvo
        else:
            self.alpha_dica_versao += diff_dica * (1.0 - math.exp(-dt * 6.0))

    def processar_mouse_down(self, pos):
        if not self.disponivel:
            return None

        if self.etapa == "FOLHAS":
            particulas = getattr(self.efeito_petalas, "particulas", None) or []
            for p in particulas:
                if not getattr(p, "folha_secreta", False):
                    continue
                sw, sh = p.sprite_base.get_size() if getattr(p, "sprite_base", None) else (32, 32)
                raio_acerto = max(28.0, max(sw, sh) * float(getattr(p, "escala", 1.0)) * 0.65)
                if math.hypot(pos[0] - p.x, pos[1] - p.y) <= raio_acerto:
                    p.folha_secreta = False
                    self._emitir_faiscas(p.x, p.y, 6)
                    p.reset(inicializar_na_tela=False)
                    self.folhas_coletadas += 1
                    if self.folhas_coletadas >= self.TOTAL_FOLHAS:
                        self.etapa = "VERSAO_LIBERADA"
                        self.pulso_versao = 1.6
                        self.sincronizar_petalas()
                        return {"evento": "versao_liberada"}
                    self.sincronizar_petalas()
                    return {"evento": "folha_coletada", "coletadas": self.folhas_coletadas}
            return None

        if self.etapa == "VERSAO_LIBERADA":
            if self.obter_rect_versao_atual().inflate(12, 12).collidepoint(pos):
                self.arrastando_versao = True
                self._drag_inicio_mouse_y = pos[1]
                self._drag_inicio_offset_y = self.versao_offset_y
                return {"evento": "arrasto_iniciado"}
            return None

        if self.etapa == "BOTAO_REVELADO":
            if self.obter_rect_botao_secreto().collidepoint(pos):
                self.etapa = "CHEATS_LIBERADOS"
                rect_b = self.obter_rect_botao_secreto()
                self._emitir_faiscas(rect_b.centerx, rect_b.centery, 8)
                return {"evento": "ativar_cheats"}
            return None

        if self.etapa == "CHEATS_LIBERADOS":
            if self.obter_rect_botao_secreto().collidepoint(pos):
                return {"evento": "abrir_cheats"}

        return None

    def processar_mouse_motion(self, pos):
        if not self.disponivel:
            return None

        hover_botao_ant = self.hover_botao
        if self.arrastando_versao and self.etapa == "VERSAO_LIBERADA":
            delta_y = pos[1] - self._drag_inicio_mouse_y
            novo_offset = self._drag_inicio_offset_y + delta_y
            self.versao_offset_alvo = max(-float(self.DESLOCAMENTO_MAX_VERSAO), min(0.0, novo_offset))
            self.versao_offset_y += (self.versao_offset_alvo - self.versao_offset_y) * 0.35

        self.hover_versao = (
            self.etapa == "VERSAO_LIBERADA"
            and self.obter_rect_versao_atual().inflate(12, 12).collidepoint(pos)
        )
        self.hover_botao = (
            self.etapa in ("BOTAO_REVELADO", "CHEATS_LIBERADOS")
            and self.obter_rect_botao_secreto().collidepoint(pos)
        )
        return {
            "evento": "hover_mudou",
            "hover_versao": self.hover_versao,
            "hover_botao": self.hover_botao,
            "hover_botao_entrou": self.hover_botao and not hover_botao_ant,
            "arrastando": self.arrastando_versao,
        }

    def processar_mouse_up(self, pos):
        if not self.disponivel or not self.arrastando_versao:
            return None

        self.arrastando_versao = False
        deslocamento = min(self.versao_offset_y, self.versao_offset_alvo)
        if self.etapa == "VERSAO_LIBERADA" and deslocamento <= -self.LIMIAR_TRAVAR_VERSAO:
            self.etapa = "BOTAO_REVELADO"
            self.versao_offset_alvo = -float(self.DESLOCAMENTO_MAX_VERSAO)
            comp = self.obter_rect_compartimento()
            self._emitir_faiscas(comp.centerx, comp.centery, 8)
            return {"evento": "botao_revelado"}

        self.versao_offset_alvo = 0.0
        return {"evento": "arrasto_cancelado"}

    def _obter_sprite_dourada(self, sprite_base):
        chave = id(sprite_base)
        cached = self._cache_sprites_douradas.get(chave)
        if cached is not None:
            return cached
        tint = sprite_base.copy()
        tint.fill((255, 240, 212, 255), special_flags=pygame.BLEND_RGBA_MULT)
        self._cache_sprites_douradas[chave] = tint
        return tint

    def _desenhar_petala_sutil(self, tela, p, alpha_eff):
        if not getattr(p, "sprite_base", None) or alpha_eff <= 0.005:
            return
        sprite_orig = p.sprite_base
        p.sprite_base = self._obter_sprite_dourada(sprite_orig)
        try:
            rot_surf = pygame.transform.rotozoom(p.sprite_base, p.angulo, p.escala)
            alpha_final = max(0, min(255, int(round(getattr(p, "alpha", 220) * alpha_eff))))
            if alpha_final <= 1:
                return
            if alpha_final < 255:
                rot_surf.set_alpha(alpha_final)

            pos_x = int(p.x - rot_surf.get_width() // 2)
            pos_y = int(p.y - rot_surf.get_height() // 2)
            tela.blit(rot_surf, (pos_x, pos_y))

            pulso = 0.5 + 0.5 * math.sin(self.tempo_anim * 2.6 + p.sway_phase)
            brilho_alpha = int(round(pulso * 42 * alpha_eff))
            if brilho_alpha > 2:
                cint = pygame.Surface((8, 8), pygame.SRCALPHA)
                pygame.draw.circle(cint, (255, 244, 214, brilho_alpha), (4, 4), 2)
                tela.blit(cint, (int(p.x) - 4, int(p.y) - 4))
        finally:
            p.sprite_base = sprite_orig

    def desenhar_petalas(self, tela):
        particulas = getattr(self.efeito_petalas, "particulas", None) or []
        alpha_eff = self.efeito_petalas._resolver_alpha_desenho(None)
        sutis = []
        for p in particulas:
            if getattr(p, "folha_secreta", False):
                sutis.append(p)
            else:
                p.desenhar(tela, alpha_multiplicador=alpha_eff)

        for p in sutis:
            self._desenhar_petala_sutil(tela, p, alpha_eff)

        for f in self.faiscas:
            frac = max(0.0, min(1.0, f["vida"] / f["vida_max"]))
            cor = (242, int(230 + 18 * frac), int(196 + 44 * frac))
            pygame.draw.circle(tela, cor, (int(f["x"]), int(f["y"])), f["raio"])

    def desenhar_versao_e_botao(self, tela, img_versao):
        comp = self.obter_rect_compartimento()
        rect_atual = self.obter_rect_versao_atual()

        if self.disponivel and self.revelacao_progresso > 0.005:
            t = max(0.0, min(1.0, self.revelacao_progresso))
            suave = t * t * (3.0 - 2.0 * t)
            deslocamento_entrada = int(round((1.0 - suave) * 8))

            surf_comp = pygame.Surface((comp.w, comp.h), pygame.SRCALPHA)
            pygame.draw.rect(surf_comp, CARVAO_PROFUNDO, (0, 0, comp.w, comp.h), border_radius=4)

            btn_abs = self.obter_rect_botao_secreto()
            btn_rel = pygame.Rect(
                btn_abs.x - comp.x,
                btn_abs.y - comp.y + deslocamento_entrada,
                btn_abs.w,
                btn_abs.h,
            )
            ativos = self.etapa == "CHEATS_LIBERADOS"
            cor_bg = AZUL_HOVER_BG if (self.hover_botao or ativos) else (20, 22, 28)
            cor_borda = AZUL_HOVER_MENU if self.hover_botao else DOURADO_ENVELHECIDO
            pygame.draw.rect(surf_comp, cor_bg, btn_rel, border_radius=4)
            pygame.draw.rect(surf_comp, cor_borda, btn_rel, 1, border_radius=4)
            rotulo = "CHEATS ATIVOS" if ativos else "LIBERAR CHEATS"
            cor_txt = MARFIM_OFFWHITE if (self.hover_botao or ativos) else DOURADO_ENVELHECIDO
            surf_txt = self.fonte_botao.render(rotulo, True, cor_txt)
            surf_comp.blit(
                surf_txt,
                (btn_rel.centerx - surf_txt.get_width() // 2, btn_rel.centery - surf_txt.get_height() // 2),
            )
            surf_comp.set_alpha(int(round(255 * suave)))

            clip_ant = tela.get_clip()
            if self.etapa == "VERSAO_LIBERADA":
                topo_visivel = max(comp.top, min(comp.bottom, rect_atual.bottom - 2))
                area_clip = pygame.Rect(comp.left, topo_visivel, comp.w, max(0, comp.bottom - topo_visivel))
            else:
                area_clip = comp
            tela.set_clip(area_clip)
            tela.blit(surf_comp, comp.topleft)
            tela.set_clip(clip_ant)

        if img_versao:
            tela.blit(img_versao, rect_atual.topleft)

        if self.disponivel and self.etapa == "FOLHAS" and self.folhas_coletadas > 0:
            inicio_x = comp.centerx - ((self.TOTAL_FOLHAS - 1) * 9) // 2
            py = comp.bottom + 5
            for i in range(self.TOTAL_FOLHAS):
                cor = (128, 120, 104) if i < self.folhas_coletadas else (34, 34, 40)
                pygame.draw.circle(tela, cor, (inicio_x + i * 9, py), 2)

        if self.disponivel and self.alpha_dica_versao > 0.01:
            alpha_linha = max(0, min(95, int(round(self.alpha_dica_versao * 95))))
            larg = max(16, rect_atual.w - 16)
            faixa = pygame.Surface((larg, 2), pygame.SRCALPHA)
            pygame.draw.line(faixa, (215, 190, 135, alpha_linha), (0, 0), (larg, 0), 1)
            tela.blit(faixa, (rect_atual.left + 8, rect_atual.bottom - 2))
