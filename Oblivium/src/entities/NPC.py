# src/entities/NPC.py
import math
import pygame
from src.entities.Entity import Entidade
import os
from src.utils.resource_manager import Animacao, ResourceManager, PASTA_ASSETS


class NPC(Entidade):
    """
    Entidade de Personagem Não-Jogável (NPC) de Oblivium.

    Suporta:
    - Árvores de diálogo modulares via `dialogo_id`.
    - Integração com `QuestManager`:
      * Enquanto o NPC tiver uma missão ATIVA com requisitos pendentes, ele trava
        no diálogo da missão em andamento e sua loja permanece bloqueada.
      * Quando o jogador cumpre todos os requisitos de campo e interage com o NPC
        novamente, o NPC dispara o diálogo de conclusão, conclui a missão e libera
        novamente suas conversas e sua loja.
    - Renderização pixel-art autêntica por arquétipo (`anciao`, `curandeira`, `ferreiro`,
      `guarda`, `carroceiro`, `aldeao`) com respiração sutil, sombra 2.5D e indicador de missão.
    """

    _CACHE_SPRITES_NPC = {}

    def __init__(
        self,
        nome,
        x,
        y,
        velocidade=0,
        vida_maxima=999,
        npc_id=None,
        dialogo_id=None,
        tem_loja=False,
        loja_id=None,
        arquetipo=None
    ):
        super().__init__(nome, vida_maxima, x, y, velocidade)

        self.largura = 36
        self.altura = 36
        self.npc_id = npc_id or str(nome).strip().lower().replace(" ", "_")
        self.dialogo_id = dialogo_id
        self.dialogos = dialogo_id or []
        self.tem_loja = bool(tem_loja)
        self.loja_id = loja_id
        self.arquetipo = arquetipo or self._inferir_arquetipo()

        # Calibração de Proporções e Hitboxes 2.5D por Arquétipo (Itens 2.1 e 2.2)
        dimensoes_arquetipos = {
            "ferreiro": (82, 40, 36),     # Torvald: forjador robusto e alto
            "torvald": (82, 40, 36),
            "roland": (84, 42, 38),       # Roland: paladino em placa pesada
            "sylvan": (65, 42, 32),       # Sylvan: guerreiro anão largo e baixo
            "doran": (78, 38, 36),        # Doran: sentinela de cota de malha
            "guarda": (78, 38, 36),
            "caelen": (76, 36, 36),       # Caelen: clérigo esguio com túnica
            "anciao": (74, 36, 36),       # Aldous: ancião curvado com cajado
            "curandeira": (74, 36, 36),   # Elara: curandeira botânica
            "elara": (74, 36, 36),
            "aldeao": (74, 36, 36)
        }
        chave_arq = self.arquetipo.lower()
        if "torvald" in self.npc_id:
            chave_arq = "torvald"
        elif "elara" in self.npc_id:
            chave_arq = "elara"
        elif "sylvan" in self.npc_id:
            chave_arq = "sylvan"
        elif "roland" in self.npc_id:
            chave_arq = "roland"
        elif "caelen" in self.npc_id:
            chave_arq = "caelen"

        self.alvo_h, self.largura, self.altura = dimensoes_arquetipos.get(chave_arq, (74, 36, 36))
        self._configurar_sprites_padrao()

    def _inferir_arquetipo(self):
        chave = f"{self.npc_id} {self.nome}".lower()
        if "aldous" in chave or "anciao" in chave or "ancião" in chave:
            return "anciao"
        if "elara" in chave or "curandeira" in chave or "botanica" in chave:
            return "curandeira"
        if "torvald" in chave or "ferreiro" in chave or "forja" in chave:
            return "ferreiro"
        if "doran" in chave or "guarda" in chave or "sentinela" in chave:
            return "guarda"
        return "aldeao"

    @classmethod
    def _gerar_frames_arquetipo(cls, arquetipo):
        if arquetipo in cls._CACHE_SPRITES_NPC:
            return cls._CACHE_SPRITES_NPC[arquetipo]

        paletas = {
            "anciao": {
                "manto": (118, 92, 68),
                "manto_sombra": (84, 64, 46),
                "detalhe": (212, 182, 110),
                "pele": (228, 198, 172),
                "cabelo": (220, 222, 228),
                "barba": True,
                "acessorio": "cajado"
            },
            "curandeira": {
                "manto": (64, 118, 86),
                "manto_sombra": (42, 82, 58),
                "detalhe": (182, 220, 168),
                "pele": (236, 206, 182),
                "cabelo": (146, 78, 52),
                "barba": False,
                "acessorio": "ervas"
            },
            "ferreiro": {
                "manto": (92, 62, 48),
                "manto_sombra": (62, 40, 30),
                "detalhe": (165, 172, 182),
                "pele": (216, 176, 148),
                "cabelo": (72, 50, 38),
                "barba": True,
                "acessorio": "martelo"
            },
            "guarda": {
                "manto": (88, 98, 114),
                "manto_sombra": (58, 66, 78),
                "detalhe": (185, 62, 58),
                "pele": (224, 192, 166),
                "cabelo": (65, 58, 52),
                "barba": False,
                "acessorio": "lanca"
            },
            "aldeao": {
                "manto": (102, 110, 122),
                "manto_sombra": (70, 76, 86),
                "detalhe": (175, 160, 130),
                "pele": (226, 196, 170),
                "cabelo": (90, 70, 52),
                "barba": False,
                "acessorio": None
            }
        }
        cfg = paletas.get(arquetipo, paletas["aldeao"])
        contorno = (24, 22, 28)

        frames = []
        for idx_frame in (0, 1):
            # Desenha em grid pixel-art 23x35 e escala 2x (46x70) para nitidez pixel-art idêntica à Halia
            gw, gh = 23, 35
            surf_px = pygame.Surface((gw, gh), pygame.SRCALPHA)
            dy = idx_frame  # Respiração sutil de 1 texel no torso/cabeça

            # Botas
            pygame.draw.rect(surf_px, contorno, (7, 30, 4, 4))
            pygame.draw.rect(surf_px, contorno, (12, 30, 4, 4))
            pygame.draw.rect(surf_px, (58, 44, 34), (8, 30, 2, 3))
            pygame.draw.rect(surf_px, (58, 44, 34), (13, 30, 2, 3))

            # Corpo / Túnica
            pygame.draw.rect(surf_px, contorno, (5, 14 + dy, 13, 17 - dy))
            pygame.draw.rect(surf_px, cfg["manto"], (6, 15 + dy, 11, 15 - dy))
            pygame.draw.rect(surf_px, cfg["manto_sombra"], (6, 24, 11, 6))
            # Faixa / Avental / Tabardo central
            pygame.draw.rect(surf_px, cfg["detalhe"], (9, 15 + dy, 5, 13 - dy))
            pygame.draw.rect(surf_px, (48, 38, 28), (6, 21 + dy, 11, 2))

            # Ombros e Braços
            pygame.draw.rect(surf_px, contorno, (3, 15 + dy, 3, 10))
            pygame.draw.rect(surf_px, contorno, (17, 15 + dy, 3, 10))
            pygame.draw.rect(surf_px, cfg["manto"], (4, 16 + dy, 2, 7))
            pygame.draw.rect(surf_px, cfg["manto"], (17, 16 + dy, 2, 7))
            pygame.draw.rect(surf_px, cfg["pele"], (4, 23 + dy, 2, 2))
            pygame.draw.rect(surf_px, cfg["pele"], (17, 23 + dy, 2, 2))

            # Cabeça
            pygame.draw.rect(surf_px, contorno, (6, 4 + dy, 11, 11))
            pygame.draw.rect(surf_px, cfg["pele"], (7, 6 + dy, 9, 8))
            # Cabelo / Elmo
            if arquetipo == "guarda":
                pygame.draw.rect(surf_px, (130, 140, 155), (6, 4 + dy, 11, 4))
                pygame.draw.rect(surf_px, cfg["detalhe"], (10, 2 + dy, 3, 3))
            else:
                pygame.draw.rect(surf_px, cfg["cabelo"], (6, 4 + dy, 11, 3))
                pygame.draw.rect(surf_px, cfg["cabelo"], (6, 6 + dy, 2, 5))
                pygame.draw.rect(surf_px, cfg["cabelo"], (15, 6 + dy, 2, 5))

            # Olhos
            surf_px.set_at((9, 9 + dy), contorno)
            surf_px.set_at((13, 9 + dy), contorno)

            # Barba (Ancião / Ferreiro)
            if cfg["barba"]:
                pygame.draw.rect(surf_px, cfg["cabelo"], (8, 12 + dy, 7, 5))
                pygame.draw.rect(surf_px, cfg["cabelo"], (9, 17 + dy, 5, 2))

            # Acessório característico
            if cfg["acessorio"] == "cajado":
                pygame.draw.rect(surf_px, (110, 78, 44), (2, 7, 2, 26))
                pygame.draw.rect(surf_px, (235, 205, 115), (1, 5 + dy, 4, 3))
            elif cfg["acessorio"] == "lanca":
                pygame.draw.rect(surf_px, (105, 76, 48), (19, 4, 2, 29))
                pygame.draw.rect(surf_px, (195, 205, 220), (18, 1, 4, 4))
            elif cfg["acessorio"] == "martelo":
                pygame.draw.rect(surf_px, (110, 76, 44), (18, 17 + dy, 2, 9))
                pygame.draw.rect(surf_px, (140, 148, 160), (16, 15 + dy, 6, 4))
            elif cfg["acessorio"] == "ervas":
                pygame.draw.rect(surf_px, (138, 96, 58), (16, 21 + dy, 5, 4))
                pygame.draw.rect(surf_px, (95, 195, 115), (17, 19 + dy, 3, 2))

            surf_final = pygame.transform.scale(surf_px, (gw * 2, gh * 2))
            frames.append(surf_final)

        cls._CACHE_SPRITES_NPC[arquetipo] = frames
        return frames

    def _resolver_pasta_sprites(self):
        chave = f"{self.npc_id} {self.nome} {self.arquetipo}".lower()
        if any(k in chave for k in ["aldous", "anciao", "ancião", "lider"]):
            return "aldous_lider"
        if any(k in chave for k in ["elara", "curandeira", "botanica", "botânica"]):
            return "elara_curandeira"
        if any(k in chave for k in ["torvald", "ferreiro", "forja"]):
            return "torvald_ferreiro"
        if any(k in chave for k in ["guarda_doran", "doran", "guarda", "sentinela", "cavaleiro"]):
            return "guarda_doran"
        if any(k in chave for k in ["carroceiro", "carroca", "carroça", "aventureiro"]):
            return "aventureiro"
        if any(k in chave for k in ["sylvan", "anao", "anão"]):
            return "sylvan_anao"
        if any(k in chave for k in ["roland", "paladino"]):
            return "roland_paladino"
        if any(k in chave for k in ["caelen", "clerigo", "clérigo"]):
            return "caelen_clerigo"
        if "bartender" in chave or "atendente" in chave:
            return "taberneira_bartender"
        if any(k in chave for k in ["taberneiro", "taverna"]):
            if os.path.exists(os.path.join(PASTA_ASSETS, "npc", "taberneiro_chefe")):
                return "taberneiro_chefe"
            return "taberneiro"
        return None

    def _configurar_sprites_padrao(self):
        pasta_nome = self._resolver_pasta_sprites()
        if pasta_nome:
            chave_cache = f"npc_real_{pasta_nome}"
            if chave_cache in self._CACHE_SPRITES_NPC:
                frames_idle = self._CACHE_SPRITES_NPC[chave_cache]
                self.animacoes["idle"] = Animacao(frames_idle, velocidade=0.06, loop=True)
                self.imagem_atual = frames_idle[0] if frames_idle else None
                return

            caminho_idle = os.path.join(PASTA_ASSETS, "npc", pasta_nome, "idle")
            if not os.path.exists(caminho_idle):
                caminho_idle = os.path.join(PASTA_ASSETS, "npc", pasta_nome, "andar_baixo")

            if os.path.exists(caminho_idle):
                arquivos = sorted([f for f in os.listdir(caminho_idle) if f.lower().endswith(".png")])
                frames = []
                for arq in arquivos:
                    img_path = os.path.join("npc", pasta_nome, os.path.basename(caminho_idle), arq).replace("\\", "/")
                    surf = ResourceManager.carregar_imagem(img_path)
                    if surf:
                        orig_w, orig_h = surf.get_size()
                        alvo_h = getattr(self, "alvo_h", 74)
                        alvo_w = max(1, int(orig_w * (alvo_h / orig_h)))
                        # Preservação estrita de nitidez pixel art por vizinho mais próximo (sem desfoque)
                        surf_scaled = pygame.transform.scale(surf, (alvo_w, alvo_h))
                        frames.append(surf_scaled)

                if frames:
                    self._CACHE_SPRITES_NPC[chave_cache] = frames
                    self.animacoes["idle"] = Animacao(frames, velocidade=0.06, loop=True)
                    self.imagem_atual = frames[0]

                    # Carrega animações adicionais se existirem na pasta do NPC
                    pasta_npc_abs = os.path.join(PASTA_ASSETS, "npc", pasta_nome)
                    for anim_sec in ["dialogue", "special", "walk", "sell"]:
                        pasta_sec = os.path.join(pasta_npc_abs, anim_sec)
                        if os.path.exists(pasta_sec):
                            arqs_sec = sorted([f for f in os.listdir(pasta_sec) if f.lower().endswith(".png")])
                            f_sec = []
                            for arq_s in arqs_sec:
                                rel_p = os.path.join("npc", pasta_nome, anim_sec, arq_s).replace("\\", "/")
                                s_sec = ResourceManager.carregar_imagem(rel_p)
                                if s_sec:
                                    ow, oh = s_sec.get_size()
                                    alvo_h = getattr(self, "alvo_h", 74)
                                    nw = max(1, int(ow * (alvo_h / oh)))
                                    sc = pygame.transform.scale(s_sec, (nw, alvo_h))
                                    f_sec.append(sc)
                            if f_sec:
                                self.animacoes[anim_sec] = Animacao(f_sec, velocidade=0.08, loop=True)
                    return

        # Fallback procedural
        frames = self._gerar_frames_arquetipo(self.arquetipo)
        self.animacoes["idle"] = Animacao(frames, velocidade=0.04, loop=True)
        self.imagem_atual = frames[0] if frames else None

    def definir_dialogos(self, lista_ou_id):
        """Define o que o NPC vai falar ao interagir (aceita ID em string ou lista)."""
        if isinstance(lista_ou_id, str):
            self.dialogo_id = lista_ou_id
        self.dialogos = lista_ou_id

    def tem_missao_ativa(self, quest_manager=None):
        """Retorna True se este NPC possui uma missão atualmente ATIVA."""
        if not quest_manager:
            return False
        missao = (
            quest_manager.obter_missao_ativa_do_npc(self.npc_id)
            or quest_manager.obter_missao_ativa_do_npc(self.nome)
        )
        return missao is not None

    def pode_abrir_loja(self, quest_manager=None):
        """
        Retorna True se o NPC possui loja e seus pré-requisitos de missão foram cumpridos:
        - Torvald (Ferreiro): Bloqueado até a conclusão de 'missao_pedra_forja'.
        - Elara (Curandeira): Bloqueada até a conclusão de 'missao_ervas_medicinais'.
        - Taberneiro / Outros: Disponível desde o início, exceto se houver missão ativa pendente.
        """
        if not self.tem_loja:
            return False

        if quest_manager and hasattr(quest_manager, "missoes"):
            # Torvald / Forja: requer conclusão da missão da rocha de minério
            if self.arquetipo == "ferreiro" or "torvald" in self.npc_id or "forja" in str(self.loja_id or "").lower():
                m_torvald = quest_manager.missoes.get("missao_pedra_forja")
                if not m_torvald or m_torvald.get("status") != "CONCLUIDA":
                    return False

            # Elara / Botânica: requer conclusão da missão das ervas medicinais
            if self.arquetipo == "curandeira" or "elara" in self.npc_id or "botanica" in str(self.loja_id or "").lower():
                m_elara = quest_manager.missoes.get("missao_ervas_medicinais")
                if not m_elara or m_elara.get("status") != "CONCLUIDA":
                    return False

        if self.tem_missao_ativa(quest_manager):
            return False
        return True

    def obter_marcador_missao(self, quest_manager=None):
        """
        Retorna ('?', cor) se houver missão pronta para entregar,
        ('…', cor) se houver missão em andamento,
        ('!', cor) se houver missão disponível para iniciar com este NPC,
        ou None caso contrário.
        """
        if not quest_manager or not hasattr(quest_manager, "missoes"):
            return None

        norm_fn = getattr(quest_manager, "_normalizar_npc", lambda s: str(s or "").strip().lower())
        chaves_npc = {
            norm_fn(self.npc_id),
            norm_fn(self.nome)
        }
        # 1. Missão ATIVA deste NPC
        missao_ativa = (
            quest_manager.obter_missao_ativa_do_npc(self.npc_id)
            or quest_manager.obter_missao_ativa_do_npc(self.nome)
        )
        if missao_ativa:
            mid = missao_ativa.get("id") if isinstance(missao_ativa, dict) else getattr(missao_ativa, "id", None)
            pronta = (
                quest_manager.pronta_para_entregar(mid)
                if hasattr(quest_manager, "pronta_para_entregar") and mid
                else False
            )
            if pronta:
                return ("?", (255, 215, 70))
            return ("...", (180, 205, 235))

        # 2. Missão DISPONIVEL / NAO_INICIADA vinculada a este NPC
        catalogo = getattr(quest_manager, "catalogo_missoes", None) or getattr(quest_manager, "missoes", {})
        for m in catalogo.values():
            status_m = getattr(m, "status", m.get("status") if isinstance(m, dict) else None)
            emissor_m = (
                (m.get("npc_id") or m.get("doador") or m.get("npc_emissor") or "")
                if isinstance(m, dict)
                else getattr(m, "npc_emissor", "")
            )
            if status_m in ("DISPONIVEL", "NAO_INICIADA"):
                emissor_norm = norm_fn(emissor_m)
                if any(c and (c == emissor_norm or c in emissor_norm or emissor_norm in c) for c in chaves_npc):
                    return ("!", (255, 215, 70))
        return None

    def obter_dialogo_interacao(self, quest_manager=None):
        """
        Determina qual diálogo iniciar quando Halia interage com o NPC:
        1. Em Oakhaven Destruída (pós-ataque do Dragão): utiliza os hubs dramáticos de crise ou vitória.
        2. Se houver missão ATIVA deste NPC pronta para entregar -> Conclui a missão e retorna `dialogo_conclusao`.
        3. Se houver missão ATIVA deste NPC ainda em andamento -> Trava em `dialogo_andamento` (loja bloqueada).
        4. Caso contrário -> Retorna o hub normal `dialogo_id`.
        """
        game_ref = getattr(self, "game", None)
        if game_ref and getattr(game_ref, "oakhaven_destruida", False):
            if getattr(game_ref, "dragao_derrotado", False):
                if "aldous" in self.npc_id.lower():
                    return "hub_aldous_vitoria"
                elif "elara" in self.npc_id.lower():
                    return "hub_elara_vitoria"
                elif "doran" in self.npc_id.lower():
                    return "hub_doran_vitoria"
            return self.dialogo_id or self.dialogos

        if quest_manager:
            res = quest_manager.processar_interacao_npc(self.npc_id)
            if res["estado"] == "LIVRE":
                res = quest_manager.processar_interacao_npc(self.nome)

            if res["estado"] in ("ANDAMENTO", "CONCLUIDA") and res.get("dialogo_id"):
                return res["dialogo_id"]

        return self.dialogo_id or self.dialogos

    def interagir(self, game):
        """Inicia o diálogo adequado na caixa de diálogo do jogo ao pressionar [E]."""
        self.game = game
        qm = getattr(game, "missoes", None) or getattr(game, "quest_manager", None)
        alvo_dialogo = self.obter_dialogo_interacao(qm)

        # À noite após a ronda de fronteira, Aldous convida Halia a descansar na Casa de Hóspedes
        # (APENAS na vila intacta antes do ataque aéreo do dragão)
        if (
            getattr(game, "oakhaven_noite", False)
            and not getattr(game, "oakhaven_destruida", False)
            and not getattr(game, "dragao_derrotado", False)
            and (self.arquetipo == "anciao" or "aldous" in self.npc_id.lower() or "aldous" in self.nome.lower())
        ):
            alvo_dialogo = "aldous_descanso_noite"

        if alvo_dialogo and hasattr(game, "caixa_dialogo") and game.caixa_dialogo:
            game.caixa_dialogo.iniciar_dialogo(alvo_dialogo)
            return alvo_dialogo
        return None

    def obter_topo_cabeca(self):
        """Retorna a coordenada Y do topo real da cabeça/elmo do NPC no mundo."""
        if self.imagem_atual:
            return self.y - (self.imagem_atual.get_height() - self.altura)
        return self.y - (getattr(self, "alvo_h", 74) - self.altura)

    def obter_posicao_marcador(self):
        """
        Retorna as coordenadas (cx, cy) base para o marcador/bolinha de interesse flutuante.
        Calcula dinamicamente a partir do topo real do sprite do NPC.
        Para o cavaleiro/guarda (Guarda Doran / Roland), aplica folga ampliada
        para garantir que seu elmo e cabeça fiquem 100% visíveis e desobstruídos.
        """
        topo_sprite = self.obter_topo_cabeca()
        chave = f"{self.npc_id} {self.nome} {self.arquetipo}".lower()
        eh_cavaleiro = any(k in chave for k in ["cavaleiro", "guarda", "doran", "roland", "paladino", "sentinela"])

        # O badge circular possui raio 12 (diâmetro 24).
        # Para o cavaleiro: folga de 38px do centro da bolinha ao topo do elmo
        # garante ~26px livres entre a borda inferior da bolinha e a cabeça do cavaleiro.
        # Para os demais NPCs: folga de 28px garante ~16px livres acima da cabeça.
        distancia = 38 if eh_cavaleiro else 28

        cx = int(self.x + self.largura // 2)
        cy = int(topo_sprite - distancia)
        return cx, cy

    def desenhar(self, tela, quest_manager=None):
        # Sombra elíptica suave nos pés do NPC
        sombra = pygame.Surface((32, 12), pygame.SRCALPHA)
        pygame.draw.ellipse(sombra, (16, 18, 22, 105), (0, 0, 32, 12))
        tela.blit(sombra, (int(self.x + self.largura // 2 - 16), int(self.y + self.altura - 7)))

        # Alterna entre animação de fala (dialogue) e ociosa (idle) conforme o diálogo ativo
        caixa = getattr(self, "caixa_dialogo", None)
        if not caixa and hasattr(self, "game") and getattr(self.game, "caixa_dialogo", None):
            caixa = self.game.caixa_dialogo
        if caixa and getattr(caixa, "ativo", False):
            autor_atual = getattr(caixa, "dados_atuais", {}).get("autor", "")
            if autor_atual and (self.nome.lower() in autor_atual.lower() or autor_atual.lower() in self.nome.lower()):
                if "dialogue" in self.animacoes and self.estado_atual != "dialogue":
                    self.mudar_estado("dialogue")
            elif self.estado_atual == "dialogue" and "idle" in self.animacoes:
                self.mudar_estado("idle")
        elif self.estado_atual == "dialogue" and "idle" in self.animacoes:
            self.mudar_estado("idle")

        # Utiliza o método desenhar herdado da Entidade se houver sprites
        anim = self.animacoes.get(self.estado_atual)
        if self.imagem_atual or (anim and getattr(anim, 'frames', None)):
            super().desenhar(tela)
        else:
            rect_npc = pygame.Rect(int(self.x), int(self.y), self.largura, self.altura)
            pygame.draw.rect(tela, (70, 90, 100), rect_npc)
            pygame.draw.rect(tela, (100, 120, 130), rect_npc, 2)

        # Marcador flutuante de missão/interesse acima da cabeça (! / ? / ...)
        if quest_manager:
            marcador = self.obter_marcador_missao(quest_manager)
            if marcador:
                simbolo, cor = marcador
                flutuar = int(math.sin(pygame.time.get_ticks() * 0.006) * 3)
                fonte = ResourceManager.carregar_fonte("ui", 18)
                txt = fonte.render(simbolo, True, cor)
                cx, cy_base = self.obter_posicao_marcador()
                cy = int(cy_base + flutuar)
                badge = pygame.Surface((24, 24), pygame.SRCALPHA)
                pygame.draw.circle(badge, (20, 24, 32, 210), (12, 12), 11)
                pygame.draw.circle(badge, (*cor, 235), (12, 12), 11, 2)
                tela.blit(badge, (cx - 12, cy - 12))
                tela.blit(txt, (cx - txt.get_width() // 2, cy - txt.get_height() // 2))
