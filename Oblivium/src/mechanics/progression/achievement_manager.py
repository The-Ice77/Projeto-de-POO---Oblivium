# src/mechanics/progression/achievement_manager.py
import json
import os
import datetime
import logging

from src.utils.constants import PASTA_DATA, PASTA_OBLIVIUM, PASTA_SRC
from src.utils import save_storage as save_io

logger = logging.getLogger(__name__)

DIRETORIO_ATUAL = os.path.dirname(os.path.abspath(__file__))
DIRETORIO_SRC = PASTA_SRC
DIRETORIO_RAIZ = PASTA_OBLIVIUM
PASTA_SAVES = save_io.PASTA_SAVES
ARQUIVO_CONQUISTAS_SAVE = os.path.join(PASTA_SAVES, "conquistas.json")
ARQUIVO_CONQUISTAS_CATALOGO = os.path.join(PASTA_DATA, "conquistas.json")


class AchievementManager:
    """
    Gerenciador Global e Persistente de Conquistas (Estilo Steam / Platina).
    
    Características:
    - Independente de saves individuais (progresso global persistido em saves/conquistas.json).
    - Integração direta com NotificationManager para disparar banners comemorativos.
    - Suporte a verificação de Platina automática ao obter todas as conquistas regulares.
    """

    def __init__(self, game=None):
        self.game = game
        self.catalogo = []
        self.conquistas = {}
        self._carregar_catalogo()
        self.carregar_progresso()

    def _carregar_catalogo(self):
        """Carrega a definição oficial das conquistas a partir do catálogo JSON."""
        if os.path.exists(ARQUIVO_CONQUISTAS_CATALOGO):
            try:
                with open(ARQUIVO_CONQUISTAS_CATALOGO, "r", encoding="utf-8") as f:
                    dados = json.load(f)
                    self.catalogo = dados.get("conquistas", [])
            except Exception as e:
                logger.error(f"[AchievementManager] Erro ao carregar catalogo: {e}")
                self.catalogo = []

        # Inicializa o dicionário em memória
        self.conquistas = {}
        for c in self.catalogo:
            cid = c.get("id")
            if cid:
                self.conquistas[cid] = {
                    "id": cid,
                    "titulo": c.get("titulo", "Conquista"),
                    "descricao": c.get("descricao", ""),
                    "categoria": c.get("categoria", "GERAL"),
                    "icone": c.get("icone", "✦"),
                    "cor": c.get("cor", [180, 215, 245]),
                    "secreta": c.get("secreta", False),
                    "oculta_ate_desbloquear": c.get("oculta_ate_desbloquear", False),
                    "conta_platina": c.get("conta_platina", True),
                    "desbloqueada": False,
                    "data_desbloqueio": None
                }

    def carregar_progresso(self):
        """Lê o arquivo global de conquistas em saves/conquistas.json."""
        if not os.path.exists(ARQUIVO_CONQUISTAS_SAVE):
            return

        try:
            with open(ARQUIVO_CONQUISTAS_SAVE, "r", encoding="utf-8") as f:
                dados_salvos = json.load(f)
                
            desbloqueadas_salvas = dados_salvos.get("desbloqueadas", {})
            for cid, info in desbloqueadas_salvas.items():
                if cid in self.conquistas:
                    self.conquistas[cid]["desbloqueada"] = True
                    self.conquistas[cid]["data_desbloqueio"] = info.get("data")
        except Exception as e:
            logger.error(f"[AchievementManager] Erro ao carregar progresso de conquistas: {e}")

    def salvar_progresso(self):
        """Persiste o status de todas as conquistas desbloqueadas em saves/conquistas.json."""
        try:
            if not os.path.exists(PASTA_SAVES):
                os.makedirs(PASTA_SAVES, exist_ok=True)

            desbloqueadas = {}
            for cid, c in self.conquistas.items():
                if c["desbloqueada"]:
                    desbloqueadas[cid] = {
                        "titulo": c["titulo"],
                        "data": c["data_desbloqueio"]
                    }

            dados = {
                "versao": "1.0",
                "ultima_atualizacao": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "total_desbloqueadas": len(desbloqueadas),
                "desbloqueadas": desbloqueadas
            }

            with open(ARQUIVO_CONQUISTAS_SAVE, "w", encoding="utf-8") as f:
                json.dump(dados, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logger.error(f"[AchievementManager] Erro ao salvar conquistas: {e}")

    def esta_desbloqueada(self, id_conquista):
        """Retorna True se a conquista especificada já estiver desbloqueada."""
        return self.conquistas.get(id_conquista, {}).get("desbloqueada", False)

    def desbloquear(self, id_conquista):
        """
        Desbloqueia a conquista, registra a data atual, salva em disco e emite notificação.
        Retorna True se foi um novo desbloqueio.
        """
        if id_conquista not in self.conquistas:
            return False

        conquista = self.conquistas[id_conquista]
        if conquista["desbloqueada"]:
            return False  # Já estava desbloqueada anteriormente

        # Registra novo desbloqueio
        agora = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        conquista["desbloqueada"] = True
        conquista["data_desbloqueio"] = agora
        self.salvar_progresso()

        # Notificação Push Especial
        if self.game and hasattr(self.game, 'notificacoes') and self.game.notificacoes:
            self.game.notificacoes.notificar_conquista(conquista)

        # Efeito Sonoro Comemorativo
        if self.game and hasattr(self.game, 'audio') and self.game.audio:
            self.game.audio.tocar_sfx("ui_confirmar")

        # Verifica se todas as regulares foram desbloqueadas para liberar a Platina
        self._verificar_platina()
        return True

    def _verificar_platina(self):
        """Concede a platina quando todas as conquistas regulares foram obtidas."""
        if self.esta_desbloqueada("mestre_platinador"):
            return

        conquistas_regulares = [
            cid for cid, c in self.conquistas.items()
            if cid != "mestre_platinador" and c.get("conta_platina", True)
        ]
        todas_regulares = all(self.conquistas[cid]["desbloqueada"] for cid in conquistas_regulares)

        if todas_regulares and len(conquistas_regulares) > 0:
            self.desbloquear("mestre_platinador")

    def obter_todas(self, incluir_ocultas=False):
        """A lista pública não revela sequer a existência de um segredo bloqueado."""
        return [
            c for c in self.conquistas.values()
            if incluir_ocultas or not c.get("oculta_ate_desbloquear", False) or c["desbloqueada"]
        ]

    def obter_progresso(self):
        """Retorna o progresso da platina pública, sem contar conquistas opcionais."""
        publicas_platina = [c for c in self.conquistas.values() if c.get("conta_platina", True)]
        total = len(publicas_platina)
        if total == 0:
            return 0, 0, 0
        desbloqueadas = sum(1 for c in publicas_platina if c["desbloqueada"])
        porcentagem = int((desbloqueadas / total) * 100)
        return desbloqueadas, total, porcentagem

    def resetar_todas_conquistas(self):
        """Bloqueia todas as conquistas e regrava o arquivo zerado em disco."""
        for c in self.conquistas.values():
            c["desbloqueada"] = False
            c["data_desbloqueio"] = None

        self.salvar_progresso()
        logger.info("[AchievementManager] Todas as conquistas foram redefinidas.")

    def redefinir_todas(self):
        """Alias para resetar_todas_conquistas."""
        self.resetar_todas_conquistas()

    def obter_desbloqueadas(self):
        """Retorna uma lista com os IDs de todas as conquistas já desbloqueadas."""
        return [cid for cid, c in self.conquistas.items() if c["desbloqueada"]]
