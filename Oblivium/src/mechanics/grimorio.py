# src/mechanics/grimorio.py
import json
import os
import sys

# Garante que a pasta raiz do projeto ('Oblivium') esteja no sys.path
_raiz_projeto = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _raiz_projeto not in sys.path:
    sys.path.insert(0, _raiz_projeto)

from src.mechanics.skills import AcaoCombate

class GrimorioHalia:
    """
    Gerenciador exclusivo do Grimório Arcano de Halia.
    Contém todo o conhecimento de alta magia da protagonista, destravando
    feitiços ancestrais conforme os fragmentos de memória são resgatados.
    """
    _CATALOGO = {}

    @classmethod
    def carregar_catalogo(cls, caminho_json=None):
        """Carrega as definições do grimório da Halia a partir do arquivo JSON."""
        if caminho_json is None:
            diretorio_atual = os.path.dirname(os.path.abspath(__file__))
            caminho_json = os.path.join(diretorio_atual, "..", "data", "grimorio_halia.json")

        if not os.path.exists(caminho_json):
            print(f"[GrimorioHalia] Aviso: Arquivo '{caminho_json}' nao encontrado.")
            return False

        try:
            with open(caminho_json, "r", encoding="utf-8") as f:
                cls._CATALOGO = json.load(f)
            return True
        except Exception as e:
            print(f"[GrimorioHalia] Erro ao carregar grimorio_halia.json: {e}")
            return False

    @classmethod
    def _garantir_carregamento(cls):
        if not cls._CATALOGO:
            cls.carregar_catalogo()

    @classmethod
    def obter_todas_magias(cls):
        """Retorna todas as magias existentes no grimório da Halia."""
        cls._garantir_carregamento()
        return dict(cls._CATALOGO)

    @classmethod
    def obter_magias_desbloqueadas(cls, total_memorias=0):
        """
        Retorna a lista de IDs de magias disponíveis para Halia
        com base na quantidade de memórias resgatadas.
        """
        cls._garantir_carregamento()
        desbloqueadas = []
        for id_magia, info in cls._CATALOGO.items():
            if total_memorias >= info.get("memorias_necessarias", 0):
                desbloqueadas.append(id_magia)
        return desbloqueadas

    @classmethod
    def obter_novas_magias_desbloqueadas(cls, total_memorias):
        """
        Retorna a lista de magias recém-desbloqueadas exatamente
        no marco atual de memórias.
        """
        cls._garantir_carregamento()
        novas = []
        for id_magia, info in cls._CATALOGO.items():
            if info.get("memorias_necessarias", 0) == total_memorias:
                novas.append(info)
        return novas

    @classmethod
    def criar_acao(cls, id_magia):
        """Instancia e retorna um objeto AcaoCombate para a magia do Grimório."""
        cls._garantir_carregamento()
        info = cls._CATALOGO.get(id_magia)
        if not info:
            return None

        return AcaoCombate(
            id_acao=info["id_acao"],
            nome=info["nome"],
            descricao=info["descricao"],
            tipo=info["tipo"],
            elemento=info.get("elemento", "ARCANO"),
            custo_mana=info.get("custo_mana", 0),
            alvo_tipo=info.get("alvo_tipo", "INIMIGO_UNICO"),
            poder_base=info.get("poder_base", 10),
            condicao_aplicada=info.get("condicao_aplicada", None)
        )

# Inicializa o catálogo ao importar o módulo
GrimorioHalia.carregar_catalogo()
