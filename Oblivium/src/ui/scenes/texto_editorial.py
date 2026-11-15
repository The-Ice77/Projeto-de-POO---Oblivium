# Oblivium/src/ui/scenes/texto_editorial.py
"""Apresentador editorial compartilhado para telas narrativas em fundo escuro com pétalas."""
import pygame

from src.ui.ui_utils import desenhar_flor_botanica, quebrar_texto_em_linhas
from src.utils.colors import (
    CARVAO_PROFUNDO,
    CINZA_LINHO,
    DOURADO_ENVELHECIDO,
    MARFIM_OFFWHITE,
    UI_TEXTO_APAGADO,
)
from src.utils.resource_manager import ResourceManager


def obter_multiplicador_velocidade_texto(game=None):
    """Lê a velocidade configurada nas opções de diálogo/jogo (0.5 Lento, 1.0 Normal, 2.5 Rápido)."""
    if game is not None:
        caixa = getattr(game, "caixa_dialogo", None)
        if caixa is not None and isinstance(getattr(caixa, "velocidade_texto", None), (int, float)):
            return max(0.25, min(4.0, float(caixa.velocidade_texto)))
        valores = getattr(game, "valores_velocidade", None)
        idx = getattr(game, "config_velocidade_indice", None)
        if isinstance(valores, (list, tuple)) and isinstance(idx, int) and 0 <= idx < len(valores):
            return max(0.25, min(4.0, float(valores[idx])))
    return 1.0


class ApresentacaoTextoEditorial:
    """Renderiza blocos editoriais centralizados com typewriter, quebra automática e proteção de pétalas."""

    def __init__(
        self,
        game=None,
        largura=1280,
        altura=720,
        paragrafos=None,
        titulo=None,
        cor_titulo=DOURADO_ENVELHECIDO,
        cor_fundo=CARVAO_PROFUNDO,
        fonte_texto=None,
        fonte_titulo=None,
        fonte_dica=None,
        margem_horizontal=240,
        altura_linha=36,
        espaco_paragrafo=10,
        deslocamento_y=0,
        velocidade_base=0.45,
        usar_velocidade_configurada=True,
        mostrar_flor=False,
        pos_y_dica_offset=45,
        dicas=(
            "[ Pressione ENTER / ESPAÇO ou Clique para acelerar ]",
            "[ Pressione ENTER / ESPAÇO ou Clique para prosseguir ]",
        ),
    ):
        self.game = game
        self.largura = int(largura or 1280)
        self.altura = int(altura or 720)
        self.titulo = titulo
        self.cor_titulo = cor_titulo
        self.cor_fundo = cor_fundo
        self.fonte_texto = fonte_texto or ResourceManager.carregar_fonte("just_breathe", 28)
        self.fonte_titulo = fonte_titulo or ResourceManager.carregar_fonte("sunday", 26)
        self.fonte_dica = fonte_dica or ResourceManager.carregar_fonte("contrail", 16)
        self.margem_horizontal = int(margem_horizontal)
        self.altura_linha = int(altura_linha)
        self.espaco_paragrafo = int(espaco_paragrafo)
        self.deslocamento_y = int(deslocamento_y)
        self.velocidade_base = float(velocidade_base)
        self.usar_velocidade_configurada = bool(usar_velocidade_configurada)
        self.mostrar_flor = bool(mostrar_flor)
        self.pos_y_dica_offset = int(pos_y_dica_offset)
        self.dicas = dicas

        self.paragrafos = []
        self.linhas_renderizaveis = []
        self.total_caracteres = 0
        self.caractere_atual = 0.0
        self.estado = "DIGITANDO"
        self.tempo_ultimo_input = 0
        self.definir_conteudo(paragrafos or [], titulo=titulo, revelar_tudo=False)

    def _normalizar_paragrafos(self, paragrafos):
        normalizados = []
        for item in paragrafos or []:
            if isinstance(item, str):
                normalizados.append((item, MARFIM_OFFWHITE))
            elif isinstance(item, dict):
                normalizados.append((item.get("texto", ""), item.get("cor", MARFIM_OFFWHITE)))
            elif isinstance(item, (tuple, list)) and len(item) >= 2:
                normalizados.append((str(item[0]), item[1]))
        return normalizados

    def definir_conteudo(self, paragrafos, titulo=None, revelar_tudo=False):
        if titulo is not None:
            self.titulo = titulo
        self.paragrafos = self._normalizar_paragrafos(paragrafos)
        self.linhas_renderizaveis = []
        self._recalcular_linhas(self.largura)
        self.total_caracteres = sum(len(linha) for linha, _, _ in self.linhas_renderizaveis)
        if revelar_tudo:
            self.caractere_atual = float(self.total_caracteres)
            self.estado = "AGUARDANDO"
        else:
            self.caractere_atual = 0.0
            self.estado = "DIGITANDO" if self.total_caracteres > 0 else "AGUARDANDO"

    def _recalcular_linhas(self, largura_tela):
        largura_max = max(280, int(largura_tela) - self.margem_horizontal)
        linhas_out = []
        for idx_p, (texto, cor) in enumerate(self.paragrafos):
            quebradas = quebrar_texto_em_linhas(texto, self.fonte_texto, largura_max) or [""]
            for idx_l, linha in enumerate(quebradas):
                extra_y = self.espaco_paragrafo if (idx_p > 0 and idx_l == 0) else 0
                linhas_out.append((linha, cor, extra_y))
        self.linhas_renderizaveis = linhas_out

    def reiniciar(self, revelar_tudo=False):
        if revelar_tudo:
            self.caractere_atual = float(self.total_caracteres)
            self.estado = "AGUARDANDO"
        else:
            self.caractere_atual = 0.0
            self.estado = "DIGITANDO" if self.total_caracteres > 0 else "AGUARDANDO"
        self.tempo_ultimo_input = pygame.time.get_ticks()

    def esta_completa(self):
        return self.caractere_atual >= self.total_caracteres

    def completar_digitacao(self):
        self.caractere_atual = float(self.total_caracteres)
        self.estado = "AGUARDANDO"

    def velocidade_efetiva(self):
        mult = obter_multiplicador_velocidade_texto(self.game) if self.usar_velocidade_configurada else 1.0
        return self.velocidade_base * mult

    def atualizar(self, dt=None):
        if dt is None:
            dt = getattr(self.game, "dt", 1.0 / 60.0) if self.game is not None else (1.0 / 60.0)
        if not isinstance(dt, (int, float)) or dt <= 0:
            dt = 1.0 / 60.0
        if self.estado == "DIGITANDO":
            self.caractere_atual += self.velocidade_efetiva() * (dt * 60.0)
            if self.caractere_atual >= self.total_caracteres:
                self.caractere_atual = float(self.total_caracteres)
                self.estado = "AGUARDANDO"
                return True
        return False

    def processar_avanco(self, forcar=False):
        tempo_atual = pygame.time.get_ticks()
        if not forcar and self.estado == "AGUARDANDO" and self.tempo_ultimo_input > 0 and tempo_atual - self.tempo_ultimo_input < 140:
            return "DEBOUNCE"
        self.tempo_ultimo_input = tempo_atual
        if not self.esta_completa():
            self.completar_digitacao()
            return "COMPLETOU"
        return "CONFIRMAR"

    def obter_dica_avanco(self):
        return self.dicas[0] if not self.esta_completa() else self.dicas[1]

    def _calcular_geometria(self, largura_tela, altura_tela):
        w = int(largura_tela or self.largura)
        h = int(altura_tela or self.altura)
        if w != self.largura:
            self.largura = w
            self._recalcular_linhas(w)
        self.altura = h

        alt_bloco = 0
        for _, _, extra_y in self.linhas_renderizaveis:
            alt_bloco += self.altura_linha + extra_y
        alt_bloco = max(self.altura_linha, alt_bloco)

        topo_titulo = 0
        offset_titulo = 68 if self.titulo else 0
        y_base = (h // 2) - ((alt_bloco + offset_titulo) // 2) + self.deslocamento_y
        if self.titulo:
            y_titulo = y_base
            y_texto_ini = y_base + offset_titulo
            topo_titulo = y_titulo
        else:
            y_titulo = y_base
            y_texto_ini = y_base

        return w, h, y_titulo, y_texto_ini, alt_bloco

    def obter_areas_protegidas(self, largura_tela=None, altura_tela=None, margem=28):
        w, h, y_titulo, y_texto_ini, alt_bloco = self._calcular_geometria(largura_tela, altura_tela)
        margem_px = max(0, int(margem))
        areas = []

        larguras = [self.fonte_texto.size(linha)[0] for linha, _, _ in self.linhas_renderizaveis if linha]
        if self.titulo and self.fonte_titulo:
            larguras.append(self.fonte_titulo.size(self.titulo)[0])
        max_w = max(larguras) if larguras else 280

        topo_bloco = y_titulo if self.titulo else y_texto_ini
        if self.mostrar_flor:
            topo_bloco -= 52
        fundo_bloco = y_texto_ini + alt_bloco
        rect_bloco = pygame.Rect((w - max_w) // 2, topo_bloco, max_w, max(40, fundo_bloco - topo_bloco))
        areas.append(rect_bloco.inflate(margem_px * 2, margem_px * 2))

        max_w_dica = max(self.fonte_dica.size(d)[0] for d in self.dicas)
        max_h_dica = max(self.fonte_dica.size(d)[1] for d in self.dicas)
        rect_dica = pygame.Rect((w - max_w_dica) // 2, h - self.pos_y_dica_offset, max_w_dica, max_h_dica)
        areas.append(rect_dica.inflate(margem_px * 2, margem_px * 2))
        return areas

    def desenhar(self, tela, efeito_petalas=None, alpha=255.0, alpha_petalas=0.78, apenas_fundo=False):
        larg, alt = tela.get_size()
        tela.fill(self.cor_fundo)

        areas = self.obter_areas_protegidas(larg, alt)
        if efeito_petalas is not None:
            efeito_petalas.desenhar(tela, areas_excluidas=areas, alpha_multiplicador=alpha_petalas)
        if apenas_fundo:
            return

        w, h, y_titulo, y_texto_ini, _ = self._calcular_geometria(larg, alt)
        alpha_int = int(max(0, min(255, alpha)))

        if self.mostrar_flor:
            desenhar_flor_botanica(tela, w // 2, y_texto_ini - 30, cor=CINZA_LINHO, escala=0.7)

        if self.titulo and self.fonte_titulo:
            s_tit = self.fonte_titulo.render(self.titulo, True, self.cor_titulo)
            if alpha_int < 255:
                s_tit.set_alpha(alpha_int)
            tela.blit(s_tit, ((w - s_tit.get_width()) // 2, y_titulo))
            y_div = y_titulo + s_tit.get_height() + 10
            pygame.draw.line(tela, self.cor_titulo, (w // 2 - 180, y_div), (w // 2 + 180, y_div), 1)

        total_visivel = int(self.caractere_atual)
        acumulados = 0
        piscar = (pygame.time.get_ticks() // 420) % 2 == 0
        y_cursor_linha = y_texto_ini

        for idx, (linha, cor_linha, extra_y) in enumerate(self.linhas_renderizaveis):
            y_cursor_linha += extra_y
            len_linha = len(linha)
            if total_visivel <= acumulados:
                y_cursor_linha += self.altura_linha
                continue

            largura_comp = self.fonte_texto.size(linha)[0]
            x_inicio = (w // 2) - (largura_comp // 2)

            if total_visivel >= acumulados + len_linha:
                texto_render = linha
                acumulados += len_linha
                ultima_visivel = idx == len(self.linhas_renderizaveis) - 1
                desenhar_cursor = ultima_visivel and (not self.esta_completa()) and piscar
            else:
                chars_nesta = total_visivel - acumulados
                texto_render = linha[:chars_nesta]
                acumulados += len_linha
                desenhar_cursor = (not self.esta_completa()) and piscar

            if texto_render:
                render = self.fonte_texto.render(texto_render, True, cor_linha)
                if alpha_int < 255:
                    render.set_alpha(alpha_int)
                tela.blit(render, (x_inicio, y_cursor_linha))

                if desenhar_cursor:
                    x_c = x_inicio + render.get_width() + 2
                    y_c = y_cursor_linha + 6
                    cursor_surf = pygame.Surface((2, max(16, self.altura_linha - 16)), pygame.SRCALPHA)
                    alpha_c = alpha_int if alpha_int < 255 else 200
                    cursor_surf.fill((*cor_linha[:3], alpha_c))
                    tela.blit(cursor_surf, (x_c, y_c))

            y_cursor_linha += self.altura_linha

        dica_txt = self.obter_dica_avanco()
        r_dica = self.fonte_dica.render(dica_txt, True, UI_TEXTO_APAGADO)
        if alpha_int < 255:
            r_dica.set_alpha(alpha_int)
        tela.blit(r_dica, ((w - r_dica.get_width()) // 2, h - self.pos_y_dica_offset))
