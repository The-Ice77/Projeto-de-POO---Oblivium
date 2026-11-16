# src/mechanics/cutscenes/cutscene_reconstrucao_visual.py
import math
import random
import pygame

from src.mechanics.cutscenes.cena_base import CenaBase
from src.ui.dialogue_box import DialogueBox
from src.ui.ui_utils import quebrar_texto_em_linhas


class ParticulaReconstrucao:
    """Partícula mágica de restauração no espaço do mundo (fagulhas, orvalho lunar ou pólen)."""

    __slots__ = ("x", "y", "vx", "vy", "vida", "vida_max", "raio", "fase_seno", "cor")

    def __init__(self, x_min, x_max, y_min, y_max, tipo="luz_dourada"):
        self.x = random.uniform(x_min, x_max)
        self.y = random.uniform(y_min, y_max)
        self.vx = random.uniform(-0.35, 0.35)
        self.vy = random.uniform(-1.15, -0.35)
        self.vida = random.uniform(36.0, 86.0)
        self.vida_max = float(self.vida)
        self.raio = random.uniform(1.8, 3.8)
        self.fase_seno = random.uniform(0.0, math.pi * 2.0)

        if tipo == "fagulha_arcana":
            self.cor = random.choice([
                (255, 185, 78),
                (255, 224, 118),
                (135, 210, 255),
                (190, 244, 255),
            ])
        elif tipo == "orvalho_lunar":
            self.cor = random.choice([
                (155, 232, 255),
                (195, 255, 228),
                (224, 214, 255),
                (180, 255, 212),
            ])
        else:
            self.cor = random.choice([
                (255, 236, 152),
                (255, 214, 98),
                (255, 246, 194),
                (242, 222, 174),
            ])

    def atualizar(self, dt=1.0 / 60.0):
        fator = dt * 60.0
        self.vida -= fator
        self.fase_seno += 0.08 * fator
        self.x += (self.vx + math.sin(self.fase_seno) * 0.45) * fator
        self.y += self.vy * fator
        return self.vida > 0.0

    def desenhar(self, tela):
        ratio = max(0.0, min(1.0, self.vida / max(1.0, self.vida_max)))
        alpha = int(215 * math.sin(ratio * math.pi))
        if alpha <= 0:
            return
        r_px = max(2, int(self.raio * 2))
        surf = pygame.Surface((r_px * 2, r_px * 2), pygame.SRCALPHA)
        pygame.draw.circle(surf, (*self.cor[:3], alpha), (r_px, r_px), max(1, int(self.raio)))
        tela.blit(surf, (int(self.x) - r_px, int(self.y) - r_px))


class CutsceneReconstrucaoVisual(CenaBase):
    """
    Diretor cinematográfico da reconstrução e despedida de Oakhaven no mapa real.
    Opera diretamente sobre `MapaOakhavenDestruida` -> `MapaOakhaven`, controlando
    foco de câmera, reparos idempotentes por ID, partículas no mundo, caminhada de
    partida pelo Portão Sul e transição única para `CreditsState("DEMO")`.
    """

    TEMPO_LEITURA_POS_TEXTO = 1.8

    FASES_RECONSTRUCAO = (
        {
            "id": "CHEGADA",
            "no_dialogo": "chegada",
            "etapa_mapa": None,
            "duracao": 4.5,
            "tempo_reparo": 0.0,
            "foco": (1102.0, 585.0),
            "zona_particulas": (880, 1340, 480, 740),
            "tipo_particula": "luz_dourada",
            "epoca": "O ALVORECER SOBRE OAKHAVEN",
            "titulo": "Silêncio Após a Tempestade",
            "texto": "Ao amanhecer, os moradores separam o que ainda pode ser usado. Halia se aproxima de uma viga caída, e Doran vem ajudar. ‘Por aqui’, diz ele, indicando a passagem.",
            "halia": {"pos": (1102, 650), "direcao": "baixo", "estado": "idle_baixo"},
            "atores": [("anciao_aldous", 1045, 610, True), ("guarda_doran", 1170, 610, False)],
        },
        {
            "id": "FORJA",
            "no_dialogo": "forja",
            "etapa_mapa": "forja",
            "duracao": 6.8,
            "tempo_reparo": 2.4,
            "foco": (1760.0, 560.0),
            "zona_particulas": (1540, 1980, 430, 760),
            "tipo_particula": "fagulha_arcana",
            "epoca": "SEMANAS DEPOIS — BAIRRO LESTE",
            "titulo": "A Forja e o Ferro Renascido",
            "texto": "Torvald confere o encaixe enquanto Halia aquece o metal. ‘Mais um pouco... pronto. Agora segura aqui pra mim.’ O martelo volta a soar. Quando terminam a peça, ele já separa a próxima.",
            "halia": {"pos": (1715, 650), "direcao": "baixo", "estado": "special_baixo"},
            "atores": [("ferreiro_torvald", 1635, 625, True)],
        },
        {
            "id": "BOTANICA",
            "no_dialogo": "botanica",
            "etapa_mapa": "botanica",
            "duracao": 6.8,
            "tempo_reparo": 2.4,
            "foco": (480.0, 555.0),
            "zona_particulas": (220, 680, 420, 720),
            "tipo_particula": "orvalho_lunar",
            "epoca": "UM MÊS DEPOIS — ALAMEDA OESTE",
            "titulo": "O Herbário e o Despertar da Terra",
            "texto": "Elara afofa a terra em volta dos primeiros brotos. Halia faz cair uma chuva fina sobre os canteiros. ‘Só um pouco’, pede Elara. ‘As raízes ainda estão pequenas.’ Halia diminui a magia e as duas continuam o trabalho.",
            "halia": {"pos": (455, 650), "direcao": "baixo", "estado": "special_baixo"},
            "atores": [("curandeira_elara", 535, 625, False)],
        },
        {
            "id": "PRACA",
            "no_dialogo": "praca",
            "etapa_mapa": "praca",
            "duracao": 6.8,
            "tempo_reparo": 2.4,
            "foco": (1102.0, 595.0),
            "zona_particulas": (860, 1350, 450, 770),
            "tipo_particula": "luz_dourada",
            "epoca": "O DIA DA RENOVAÇÃO",
            "titulo": "A Praça Central Consagrada",
            "texto": "A fonte volta a correr sob a magia de Halia. Aldous deixa a lista de reparos de lado. ‘Quando terminar, fique um pouco. Tem água fresca.’ Os moradores vão se reunindo na praça, e Halia escuta a conversa enquanto conclui o trabalho.",
            "halia": {"pos": (1102, 642), "direcao": "baixo", "estado": "special_baixo"},
            "atores": [("anciao_aldous", 1020, 615, True), ("guarda_doran", 1185, 615, False)],
        },
    )

    def __init__(self, game, playing_state=None):
        super().__init__(game=game, on_concluido=None)
        self.playing_state = playing_state
        self.largura = getattr(game, "LARGURA", 1280) if game is not None else 1280
        self.altura = getattr(game, "ALTURA", 720) if game is not None else 720

        self.fase_atual = "INATIVO"
        self.indice_fase = 0
        self.tempo_cena = 0.0
        self.tempo_pos_digitacao = 0.0
        self.tempo_total_reconstrucao = 0.0
        self.caractere_atual = 0.0
        self._foco_camera = (1102.0, 585.0)
        self._fade_alpha = 0.0
        self._despedida_iniciada = False
        self._consequencias_aplicadas = False
        self._reparo_fase_aplicado = False
        self.particulas = []
        self._caixa_fallback = None
        self._indice_caixa_fallback = -1

        caixa = self._obter_caixa_dialogo()
        self.fonte_texto = caixa.fonte_texto
        self.velocidade_digitacao = 60.0 * max(0.25, float(getattr(caixa, "velocidade_texto", 1.0)))

    def _usando_caixa_jogo(self):
        return bool(self.game is not None and getattr(self.game, "caixa_dialogo", None) is not None)

    def _obter_caixa_dialogo(self):
        if self._usando_caixa_jogo():
            return self.game.caixa_dialogo
        if self._caixa_fallback is None:
            self._caixa_fallback = DialogueBox(self.largura, game=self.game)
        return self._caixa_fallback

    def _obter_dados_narracao_fase(self, fase, caixa):
        no_id = fase.get("no_dialogo")
        banco = getattr(getattr(caixa, "manager", None), "banco_dialogos", {})
        no_json = banco.get("reconstrucao_oakhaven", {}).get("nos", {}).get(no_id) if isinstance(banco, dict) else None
        if isinstance(no_json, dict) and no_json.get("texto"):
            return {"autor": no_json.get("autor", fase["titulo"]), "texto": no_json["texto"]}
        return {"autor": f"{fase['epoca']} — {fase['titulo']}", "texto": fase["texto"]}

    def iniciar(self, on_concluido=None):
        """Inicia o acompanhamento cinematográfico sobre o mapa real de Oakhaven."""
        self._reiniciar_estado_execucao(on_concluido=on_concluido)
        self.largura = getattr(self.game, "LARGURA", self.largura) if self.game is not None else self.largura
        self.altura = getattr(self.game, "ALTURA", self.altura) if self.game is not None else self.altura
        self._despedida_iniciada = False
        self._consequencias_aplicadas = False
        self._fade_alpha = 0.0
        self.tempo_total_reconstrucao = 0.0
        self.particulas.clear()
        self.ativo = True

        if self.game and hasattr(self.game, "mapa_casa"):
            if self.game.mapa_casa.cenario_atual != "OAKHAVEN_DESTRUIDA" and getattr(
                self.game, "oakhaven_destruida", True
            ):
                self.game.mapa_casa.carregar_cenario("OAKHAVEN_DESTRUIDA")
            cen = getattr(self.game.mapa_casa, "cenario_objeto", None)
            if cen and hasattr(cen, "preparar_cena_reconstrucao"):
                cen.preparar_cena_reconstrucao()

        self._configurar_fase_reconstrucao(0)

        if self.game and getattr(self.game, "audio", None):
            if hasattr(self.game.audio, "parar_ambiente"):
                self.game.audio.parar_ambiente(fade_ms=600)
            self.game.audio.tocar_musica("vila_oakhaven", loop=-1, fade_ms=1000, contexto="cutscene")

    def iniciar_partida(self, on_concluido=None):
        """Inicia a caminhada final de Halia pelo Portão Sul rumo ao Vale dos Moinhos."""
        self._reiniciar_estado_execucao(on_concluido=on_concluido)
        self.largura = getattr(self.game, "LARGURA", self.largura) if self.game is not None else self.largura
        self.altura = getattr(self.game, "ALTURA", self.altura) if self.game is not None else self.altura
        self.ativo = True
        self.fase_atual = "PARTIDA"
        self.tempo_cena = 0.0
        self._fade_alpha = 0.0
        self._consequencias_aplicadas = False
        self.particulas.clear()

        if self.game and hasattr(self.game, "mapa_casa") and self.game.mapa_casa.cenario_atual != "OAKHAVEN":
            self.game.mapa_casa.carregar_cenario("OAKHAVEN")

        halia = getattr(self.game, "halia", None)
        if halia:
            halia.x = 1102.0
            halia.y = 860.0
            halia.direcao = "baixo"
            halia.mudar_estado("andar_baixo")
            self._foco_camera = (halia.x + halia.largura * 0.5, halia.y + halia.altura * 0.5)

        if self.playing_state and hasattr(self.playing_state, "atualizar_camera"):
            self.playing_state.atualizar_camera(instantaneo=True)

        if self.game and getattr(self.game, "audio", None):
            if hasattr(self.game.audio, "limpar_contexto_combate"):
                self.game.audio.limpar_contexto_combate()
            elif hasattr(self.game.audio, "musica_anterior"):
                self.game.audio.musica_anterior = None
            self.game.audio.tocar_musica(
                "cutscene_final", loop=-1, fade_ms=1200, salvar_anterior=False, contexto="cutscene"
            )

    def _configurar_fase_reconstrucao(self, indice):
        self.indice_fase = max(0, min(indice, len(self.FASES_RECONSTRUCAO) - 1))
        fase = self.FASES_RECONSTRUCAO[self.indice_fase]
        self.fase_atual = fase["id"]
        self.tempo_cena = 0.0
        self.tempo_pos_digitacao = 0.0
        self.caractere_atual = 0.0
        self._reparo_fase_aplicado = False
        self._foco_camera = fase["foco"]
        self.particulas.clear()

        halia = getattr(self.game, "halia", None)
        h_cfg = fase["halia"]
        if halia:
            halia.x = float(h_cfg["pos"][0])
            halia.y = float(h_cfg["pos"][1])
            halia.direcao = h_cfg["direcao"]
            halia.virado_direita = h_cfg["direcao"] == "direita"
            estado_h = h_cfg["estado"] if h_cfg["estado"] in getattr(halia, "animacoes", {}) else "idle_baixo"
            halia.mudar_estado(estado_h)

        cen = getattr(getattr(self.game, "mapa_casa", None), "cenario_objeto", None)
        if cen and hasattr(cen, "reposicionar_ator_cena"):
            for npc_id, nx, ny, virado_dir in fase["atores"]:
                cen.reposicionar_ator_cena(npc_id, nx, ny, virado_direita=virado_dir)

        if self.playing_state and hasattr(self.playing_state, "atualizar_camera") and self.indice_fase == 0:
            self.playing_state.atualizar_camera(instantaneo=True)

        caixa = self._obter_caixa_dialogo()
        self.fonte_texto = caixa.fonte_texto
        self.velocidade_digitacao = 60.0 * max(0.25, float(getattr(caixa, "velocidade_texto", 1.0)))
        caixa.iniciar_dialogo([self._obter_dados_narracao_fase(fase, caixa)])
        self._indice_caixa_fallback = self.indice_fase

        self._spawn_particulas_fase(fase, quantidade=18)

    def _spawn_particulas_fase(self, fase, quantidade=4):
        x_min, x_max, y_min, y_max = fase["zona_particulas"]
        tipo = fase["tipo_particula"]
        for _ in range(quantidade):
            self.particulas.append(ParticulaReconstrucao(x_min, x_max, y_min, y_max, tipo=tipo))

    def _aplicar_reparo_fase_atual(self, fase):
        if self._reparo_fase_aplicado:
            return
        self._reparo_fase_aplicado = True
        etapa = fase.get("etapa_mapa")
        cen = getattr(getattr(self.game, "mapa_casa", None), "cenario_objeto", None)
        if etapa and cen and hasattr(cen, "aplicar_etapa_reconstrucao"):
            cen.aplicar_etapa_reconstrucao(etapa)
            self._spawn_particulas_fase(fase, quantidade=22)

    def _avancar_fase_reconstrucao(self):
        fase_corrente = self.FASES_RECONSTRUCAO[self.indice_fase]
        self._aplicar_reparo_fase_atual(fase_corrente)
        prox = self.indice_fase + 1
        if prox < len(self.FASES_RECONSTRUCAO):
            self._configurar_fase_reconstrucao(prox)
        else:
            self._concluir_etapa_visual_para_despedida()

    def _concluir_etapa_visual_para_despedida(self):
        if self._despedida_iniciada:
            return
        self._despedida_iniciada = True
        self.ativo = False
        self.fase_atual = "DESPEDIDA"
        self.particulas.clear()

        cen = getattr(getattr(self.game, "mapa_casa", None), "cenario_objeto", None)
        if cen and hasattr(cen, "aplicar_etapa_reconstrucao"):
            for etapa in ("forja", "botanica", "praca"):
                cen.aplicar_etapa_reconstrucao(etapa)

        if self.game:
            self.game.oakhaven_noite = False
            self.game.oakhaven_destruida = False
            if hasattr(self.game, "mapa_casa") and self.game.mapa_casa:
                self.game.mapa_casa.carregar_cenario("OAKHAVEN")
                npcs_praca = {
                    "anciao_aldous": (1025, 615, True),
                    "ferreiro_torvald": (965, 650, True),
                    "curandeira_elara": (1160, 650, False),
                    "guarda_doran": (1220, 615, False),
                }
                for npc in getattr(self.game.mapa_casa, "npcs", []):
                    cfg = npcs_praca.get(getattr(npc, "npc_id", ""))
                    if cfg:
                        npc.x, npc.y, npc.virado_direita = float(cfg[0]), float(cfg[1]), cfg[2]
                        npc.mudar_estado("idle")
                        if hasattr(npc, "sincronizar_teleporte"):
                            npc.sincronizar_teleporte()

            halia = getattr(self.game, "halia", None)
            if halia:
                halia.x, halia.y = 1102.0, 685.0
                halia.direcao = "cima"
                halia.mudar_estado("idle_cima")
            if self.playing_state and hasattr(self.playing_state, "atualizar_camera"):
                self.playing_state.atualizar_camera(instantaneo=True)

            self.game.etapa_epilogo = "DESPEDIDA_PENDENTE"
            self.game.despedida_demo_exibida = True
            if getattr(self.game, "slot_atual", None) and hasattr(self.game, "salvar_estado"):
                self.game.salvar_estado(self.game.slot_atual, tipo="autosave", silenciar_notificacao=True)
            if hasattr(self.game, "caixa_dialogo") and self.game.caixa_dialogo:
                self.game.caixa_dialogo.iniciar_dialogo("despedida_demo_oakhaven")

    def _encerrar_para_creditos_demo(self):
        if self._consequencias_aplicadas:
            return
        self._consequencias_aplicadas = True
        self.fase_atual = "CONCLUIDA"
        self.particulas.clear()

        if self.game:
            self.game.oakhaven_noite = False
            self.game.oakhaven_destruida = False
            self.game.etapa_epilogo = "DEMO_CONCLUIDA"

            halia = getattr(self.game, "halia", None)
            if halia:
                halia.x, halia.y = 1102.0, 650.0
                halia.direcao = "baixo"
                halia.mudar_estado("idle_baixo")
            if self.playing_state and hasattr(self.playing_state, "atualizar_camera"):
                self.playing_state.atualizar_camera(instantaneo=True)

            if getattr(self.game, "audio", None):
                if hasattr(self.game.audio, "parar_ambiente"):
                    self.game.audio.parar_ambiente(fade_ms=500)
                if hasattr(self.game.audio, "musica_anterior"):
                    self.game.audio.musica_anterior = None

            if getattr(self.game, "slot_atual", None) and hasattr(self.game, "salvar_estado"):
                self.game.salvar_estado(self.game.slot_atual, tipo="autosave", silenciar_notificacao=True)

            estados = getattr(self.game, "estados", {})
            cred = estados.get("CREDITOS") if isinstance(estados, dict) else None
            if cred and hasattr(cred, "iniciar_modo_demo"):
                cred.iniciar_modo_demo()
            if hasattr(self.game, "mudar_estado"):
                self.game.mudar_estado("CREDITOS")

    def obter_foco_camera(self):
        """Retorna as coordenadas de foco mundial para a câmera durante a cinemática."""
        if self.fase_atual == "PARTIDA" and self.game and getattr(self.game, "halia", None):
            h = self.game.halia
            return (float(h.x + h.largura * 0.5), float(h.y + h.altura * 0.5))
        return self._foco_camera

    def _lidar_avanco_manual(self):
        if self.fase_atual == "PARTIDA":
            return True
        fase = self.FASES_RECONSTRUCAO[self.indice_fase]
        caixa = self._obter_caixa_dialogo()
        estava_digitando = bool(
            caixa.ativo
            and (
                caixa.caractere_atual < caixa.tamanho_total
                or caixa.indice_pagina_texto + 1 < caixa.total_paginas_texto
            )
        )
        if estava_digitando:
            caixa.proximo_texto()
            self.caractere_atual = float(caixa.caractere_atual)
            if not caixa.ativo:
                self._avancar_fase_reconstrucao()
        else:
            caixa.ativo = False
            self._avancar_fase_reconstrucao()
        return True

    def handle_event(self, evento):
        if not self.ativo:
            return False

        if evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_ESCAPE:
                self.pular()
                return True
            if evento.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_e):
                return self._lidar_avanco_manual()

        elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            return self._lidar_avanco_manual()

        return False

    def atualizar(self, dt=None):
        if not self.ativo:
            return
        if dt is None:
            dt = getattr(self.game, "dt", 1.0 / 60.0) if self.game is not None else (1.0 / 60.0)
        dt_real = max(0.001, float(dt))
        self.tempo_cena += dt_real

        if self.fase_atual == "PARTIDA":
            halia = getattr(self.game, "halia", None)
            if halia:
                halia.y += 105.0 * dt_real
                halia.direcao = "baixo"
                halia.mudar_estado("andar_baixo")
                self._foco_camera = (float(halia.x + halia.largura * 0.5), float(halia.y + halia.altura * 0.5))
                if halia.y >= 1220.0:
                    self._fade_alpha = min(255.0, ((halia.y - 1220.0) / 115.0) * 255.0)
                if halia.y >= 1335.0 or self.tempo_cena >= 5.5:
                    self.finalizar()
            else:
                self.finalizar()
            return

        self.tempo_total_reconstrucao += dt_real
        fase = self.FASES_RECONSTRUCAO[self.indice_fase]
        caixa = self._obter_caixa_dialogo()
        self.velocidade_digitacao = 60.0 * max(0.25, float(getattr(caixa, "velocidade_texto", 1.0)))
        if caixa.ativo:
            caixa.atualizar(dt=dt_real)
            self.caractere_atual = float(caixa.caractere_atual)
            digitacao_concluida = (
                caixa.caractere_atual >= caixa.tamanho_total
                and caixa.indice_pagina_texto + 1 >= caixa.total_paginas_texto
            )
        else:
            self.caractere_atual = float(len(fase["texto"]))
            digitacao_concluida = True

        if digitacao_concluida:
            self.tempo_pos_digitacao += dt_real
        else:
            self.tempo_pos_digitacao = 0.0

        if self.tempo_cena >= fase["tempo_reparo"]:
            self._aplicar_reparo_fase_atual(fase)

        self.particulas = [p for p in self.particulas if p.atualizar(dt_real)]
        if len(self.particulas) < 34 and random.random() < min(1.0, dt_real * 14.0):
            self._spawn_particulas_fase(fase, quantidade=1)

        if (
            digitacao_concluida
            and self.tempo_cena >= fase["tempo_reparo"]
            and self.tempo_cena >= fase["duracao"]
            and self.tempo_pos_digitacao >= self.TEMPO_LEITURA_POS_TEXTO
        ):
            caixa.ativo = False
            self._avancar_fase_reconstrucao()

    def desenhar_mundo(self, tela):
        """Renderiza efeitos da reconstrução em coordenadas reais do mapa (antes do crop da câmera)."""
        if not self.ativo or self.fase_atual == "PARTIDA":
            return
        for p in self.particulas:
            p.desenhar(tela)

    def desenhar_tela(self, tela):
        """Renderiza somente o fade de partida; a narração usa sempre a DialogueBox oficial."""
        if not self.ativo:
            return
        larg, alt = tela.get_size()

        if self.fase_atual == "PARTIDA":
            alpha = int(max(0, min(255, self._fade_alpha)))
            if alpha > 0:
                fade = pygame.Surface((larg, alt), pygame.SRCALPHA)
                fade.fill((0, 0, 0, alpha))
                tela.blit(fade, (0, 0))
            return

        if not self._usando_caixa_jogo():
            caixa = self._obter_caixa_dialogo()
            fase = self.FASES_RECONSTRUCAO[self.indice_fase]
            if self._indice_caixa_fallback != self.indice_fase or not caixa.ativo:
                caixa.iniciar_dialogo([self._obter_dados_narracao_fase(fase, caixa)])
                self._indice_caixa_fallback = self.indice_fase
            if self.caractere_atual > caixa.caractere_atual:
                caixa.caractere_atual = min(float(caixa.tamanho_total), float(self.caractere_atual))
            caixa.desenhar(tela)

    def _quebrar_texto(self, texto, largura_max):
        return quebrar_texto_em_linhas(texto, self.fonte_texto, largura_max)

    def desenhar(self, tela):
        self.desenhar_tela(tela)

    def finalizar(self):
        if self.fase_atual in ("CHEGADA", "FORJA", "BOTANICA", "PRACA"):
            self._concluir_etapa_visual_para_despedida()
            return False
        resultado = super().finalizar()
        self._encerrar_para_creditos_demo()
        return resultado
