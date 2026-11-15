# src/mechanics/rpg/grimorio.py
import json
import os

from src.mechanics.rpg.skills import SkillsRegistry
from src.utils.constants import PASTA_DATA


class GrimorioHalia:
    """
    Gerenciador exclusivo da progressão e aquisição do Grimório Arcano de Halia.
    Usa `skills.json` (`SkillsRegistry`) como autoridade única para stats e instâncias
    de combate, mantendo em `grimorio_halia.json` apenas regras de desbloqueio.
    """
    _PROGRESSAO = {}

    @classmethod
    def carregar_catalogo(cls, caminho_json=None):
        """Carrega as regras de progressão do grimório a partir do arquivo JSON."""
        if caminho_json is None:
            caminho_json = os.path.join(PASTA_DATA, "grimorio_halia.json")

        if not os.path.exists(caminho_json):
            print(f"[GrimorioHalia] Aviso: Arquivo '{caminho_json}' nao encontrado.")
            return False

        try:
            with open(caminho_json, "r", encoding="utf-8") as f:
                cls._PROGRESSAO = json.load(f)
            if not SkillsRegistry._catalogo:
                SkillsRegistry.carregar_de_json()
            return True
        except Exception as e:
            print(f"[GrimorioHalia] Erro ao carregar grimorio_halia.json: {e}")
            return False

    @classmethod
    def _garantir_carregamento(cls):
        if not cls._PROGRESSAO:
            cls.carregar_catalogo()

    @classmethod
    def obter_info_magia(cls, id_magia):
        """Compõe dados canônicos de combate (`skills.json`) com metadados de progressão."""
        cls._garantir_carregamento()
        prog = cls._PROGRESSAO.get(id_magia)
        skill_raw = SkillsRegistry.obter_dados_raw(id_magia)
        if prog is None and skill_raw is None:
            return None
        combinado = {}
        if skill_raw:
            combinado.update(skill_raw)
        if prog:
            combinado.update(prog)
        return combinado

    @classmethod
    def obter_todas_magias(cls):
        """Retorna todas as magias do grimório compostas com os dados canônicos de `skills.json`."""
        cls._garantir_carregamento()
        resultado = {}
        for id_magia in cls._PROGRESSAO:
            info = cls.obter_info_magia(id_magia)
            if info:
                resultado[id_magia] = info
        return resultado

    @classmethod
    def obter_magias_desbloqueadas(cls, total_memorias=0):
        """
        Retorna os IDs de magias desbloqueadas automaticamente pelas memórias atuais.
        Magias com `memorias_necessarias: null` só são obtidas por tomos/marcos específicos.
        """
        cls._garantir_carregamento()
        desbloqueadas = []
        for id_magia, meta in cls._PROGRESSAO.items():
            req = meta.get("memorias_necessarias")
            if req is not None and total_memorias >= req:
                desbloqueadas.append(id_magia)
        return desbloqueadas

    @classmethod
    def obter_novas_magias_desbloqueadas(cls, total_memorias):
        """Retorna os metadados compostos das magias despertadas no marco exato `total_memorias`."""
        cls._garantir_carregamento()
        if total_memorias is None:
            return []
        novas = []
        for id_magia, meta in cls._PROGRESSAO.items():
            req = meta.get("memorias_necessarias")
            if req is not None and req == total_memorias:
                info = cls.obter_info_magia(id_magia)
                if info:
                    novas.append(info)
        return novas

    @classmethod
    def pode_adquirir_por_fonte(cls, id_magia, total_memorias=0):
        """
        Verifica se uma magia pode ser aprendida ou ativada via tomo/ensinamento
        no estágio atual de memória de Halia.
        """
        cls._garantir_carregamento()
        meta = cls._PROGRESSAO.get(id_magia)
        if not meta:
            return True, ""
        min_mem = meta.get("memorias_minimas_aquisicao")
        if min_mem is None:
            min_mem = meta.get("memorias_necessarias")
        if min_mem is not None and total_memorias < min_mem:
            info = cls.obter_info_magia(id_magia) or {}
            nome = info.get("nome", id_magia.replace("_", " ").title())
            return False, f"Sincronia insuficiente: requer Memória {min_mem} para compreender '{nome}'."
        return True, ""

    @classmethod
    def obter_status_aquisicao_item(cls, item, halia=None):
        """Retorna requisitos de Memória, elegibilidade e rótulo de estado para tomos e ensinamentos."""
        if not item:
            return None
        magia_id = getattr(item, "magia_id", None)
        if not magia_id:
            return None

        cls._garantir_carregamento()
        meta = cls._PROGRESSAO.get(magia_id) or {}
        info = cls.obter_info_magia(magia_id) or {}
        nome_magia = info.get("nome", magia_id.replace("_", " ").title())

        min_mem = meta.get("memorias_minimas_aquisicao")
        if min_mem is None:
            min_mem = meta.get("memorias_necessarias")

        mem_atual = getattr(halia, "fragmentos_memoria", 0) if halia else 0
        ja_conhece = bool(
            halia
            and (
                magia_id in getattr(halia, "magias_desbloqueadas", [])
                or magia_id in getattr(halia, "feiticos_aprendidos", set())
            )
        )
        pode_fonte, motivo_fonte = cls.pode_adquirir_por_fonte(magia_id, mem_atual)
        pode_usar = ja_conhece or pode_fonte

        if ja_conhece:
            requisito_texto = f"Sincronia: Feitiço já dominado (Memória {mem_atual})"
        elif min_mem is not None and min_mem > 0:
            suf = f" [Atendido: {mem_atual}]" if mem_atual >= min_mem else f" (Atual: {mem_atual})"
            requisito_texto = f"Requer Memória {min_mem}{suf}"
        else:
            requisito_texto = "Sem requisito mínimo de Memória"

        return {
            "magia_id": magia_id,
            "nome_magia": nome_magia,
            "memorias_minimas": min_mem,
            "memorias_atuais": mem_atual,
            "ja_conhece": ja_conhece,
            "pode_usar": pode_usar,
            "motivo_bloqueio": "" if pode_usar else motivo_fonte,
            "requisito_texto": requisito_texto,
        }

    @classmethod
    def criar_acao(cls, id_magia):
        """Delega à autoridade central (`SkillsRegistry`) a criação de uma ação independente."""
        return SkillsRegistry.criar_instancia(id_magia)


# Inicializa o catálogo ao importar o módulo
GrimorioHalia.carregar_catalogo()
