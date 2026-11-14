import copy
import json
import logging
import os

from src.entities.NPC import NPC
from src.mechanics.dialogue_manager import DialogueManager
from src.mechanics.shop import Loja
from src.utils.resource_manager import PASTA_ASSETS

logger = logging.getLogger(__name__)


class NPCFactory:
    """Fábrica orientada a dados para criação de NPCs a partir de npcs.json."""

    _CAMINHO_CATALOGO_PADRAO = os.path.normpath(
        os.path.join(os.path.dirname(__file__), "..", "data", "npcs.json")
    )

    _FALLBACK_MINIMO = {
        "carroceiro": {
            "nome": "Carroceiro",
            "arquetipo": "aldeao",
            "sprite_pasta": "aventureiro",
            "dimensoes": {"alvo_h": 74, "largura": 36, "altura": 36},
            "velocidade": 2,
            "vida_maxima": 999,
            "dialogo_id": "hub_carroceiro",
            "tem_loja": False,
            "loja_id": None,
        },
        "anciao_aldous": {
            "nome": "Ancião Aldous",
            "arquetipo": "anciao",
            "sprite_pasta": "aldous_lider",
            "dimensoes": {"alvo_h": 74, "largura": 36, "altura": 36},
            "velocidade": 0,
            "vida_maxima": 999,
            "dialogo_id": "hub_aldous",
            "tem_loja": False,
            "loja_id": None,
        },
        "curandeira_elara": {
            "nome": "Curandeira Elara",
            "arquetipo": "curandeira",
            "sprite_pasta": "elara_curandeira",
            "dimensoes": {"alvo_h": 74, "largura": 36, "altura": 36},
            "velocidade": 0,
            "vida_maxima": 999,
            "dialogo_id": "hub_elara",
            "tem_loja": True,
            "loja_id": "botanica_elara",
        },
        "ferreiro_torvald": {
            "nome": "Ferreiro Torvald",
            "arquetipo": "ferreiro",
            "sprite_pasta": "torvald_ferreiro",
            "dimensoes": {"alvo_h": 82, "largura": 40, "altura": 36},
            "velocidade": 0,
            "vida_maxima": 999,
            "dialogo_id": "hub_torvald",
            "tem_loja": True,
            "loja_id": "forja_torvald",
        },
        "guarda_doran": {
            "nome": "Guarda Doran",
            "arquetipo": "guarda",
            "sprite_pasta": "guarda_doran",
            "dimensoes": {"alvo_h": 78, "largura": 38, "altura": 36},
            "velocidade": 0,
            "vida_maxima": 999,
            "dialogo_id": "hub_doran",
            "tem_loja": False,
            "loja_id": None,
        },
    }

    _CATALOGO = {}
    _IDS_DIALOGOS = None

    @classmethod
    def carregar_de_json(cls, caminho_json=None):
        """Carrega o catálogo de NPCs de um JSON, com fallback defensivo em caso de erro."""
        caminho = caminho_json or cls._CAMINHO_CATALOGO_PADRAO
        try:
            with open(caminho, "r", encoding="utf-8") as arquivo:
                dados = json.load(arquivo)
            if not isinstance(dados, dict) or not dados:
                raise ValueError("Catálogo de NPCs vazio ou inválido.")
            cls._CATALOGO = copy.deepcopy(dados)
        except Exception as erro:
            logger.warning(
                "[NPCFactory] Falha ao carregar '%s' (%s); usando catálogo mínimo em memória.",
                caminho,
                erro,
            )
            cls._CATALOGO = copy.deepcopy(cls._FALLBACK_MINIMO)

        cls._IDS_DIALOGOS = None
        return cls._CATALOGO

    @classmethod
    def _garantir_carregamento(cls):
        if not cls._CATALOGO:
            cls.carregar_de_json()

    @classmethod
    def obter_catalogo(cls):
        """Retorna cópia do catálogo carregado de NPCs."""
        cls._garantir_carregamento()
        return copy.deepcopy(cls._CATALOGO)

    @classmethod
    def _obter_ids_dialogos(cls):
        if cls._IDS_DIALOGOS is None:
            cls._IDS_DIALOGOS = set(DialogueManager().banco_dialogos.keys())
        return cls._IDS_DIALOGOS

    @classmethod
    def _validar_referencias(cls, npc_id, cfg):
        """Valida diálogo, loja e pasta de sprites do NPC, emitindo warnings sem quebrar."""
        dialogo_id = cfg.get("dialogo_id")
        if isinstance(dialogo_id, str) and dialogo_id.strip():
            ids_dialogos = cls._obter_ids_dialogos()
            if dialogo_id not in ids_dialogos:
                logger.warning(
                    "[NPCFactory] NPC '%s' referencia dialogo_id inexistente: '%s'.",
                    npc_id,
                    dialogo_id,
                )

        tem_loja = bool(cfg.get("tem_loja", False))
        loja_id = cfg.get("loja_id")
        if tem_loja and not loja_id:
            logger.warning(
                "[NPCFactory] NPC '%s' possui tem_loja=True sem loja_id definido.",
                npc_id,
            )
        elif isinstance(loja_id, str) and loja_id.strip():
            loja_canonica = Loja.normalizar_id(loja_id)
            catalogo_lojas = Loja._obter_catalogo()
            if loja_canonica not in catalogo_lojas:
                logger.warning(
                    "[NPCFactory] NPC '%s' referencia loja_id inexistente: '%s'.",
                    npc_id,
                    loja_id,
                )

        sprite_pasta = cfg.get("sprite_pasta")
        if sprite_pasta:
            caminho_sprites = os.path.join(PASTA_ASSETS, "npc", str(sprite_pasta))
            if not os.path.isdir(caminho_sprites):
                logger.warning(
                    "[NPCFactory] NPC '%s' referencia pasta de sprites inexistente: '%s'.",
                    npc_id,
                    caminho_sprites,
                )

    @classmethod
    def criar(cls, npc_id, x=0, y=0, **overrides):
        """Instancia um NPC a partir do catálogo por npc_id, aceitando overrides de cena."""
        cls._garantir_carregamento()
        chave = str(npc_id or "").strip().lower()
        template = cls._CATALOGO.get(chave)

        if template is None:
            logger.warning(
                "[NPCFactory] NPC '%s' não encontrado no catálogo; usando configuração mínima.",
                npc_id,
            )
            cfg = {
                "nome": str(npc_id or "Aldeão"),
                "arquetipo": "aldeao",
                "sprite_pasta": None,
                "dimensoes": {"alvo_h": 74, "largura": 36, "altura": 36},
                "velocidade": 0,
                "vida_maxima": 999,
                "dialogo_id": None,
                "tem_loja": False,
                "loja_id": None,
            }
        else:
            cfg = copy.deepcopy(template)

        if overrides:
            for k, v in overrides.items():
                cfg[k] = copy.deepcopy(v)

        npc_id_final = cfg.get("npc_id") or chave or str(cfg.get("nome", "npc")).strip().lower().replace(" ", "_")
        cfg["npc_id"] = npc_id_final

        cls._validar_referencias(npc_id_final, cfg)

        return NPC(
            nome=cfg.get("nome", npc_id_final),
            x=x,
            y=y,
            velocidade=cfg.get("velocidade", 0),
            vida_maxima=cfg.get("vida_maxima", 999),
            npc_id=npc_id_final,
            dialogo_id=cfg.get("dialogo_id"),
            tem_loja=cfg.get("tem_loja", False),
            loja_id=cfg.get("loja_id"),
            arquetipo=cfg.get("arquetipo"),
            config=cfg,
        )
