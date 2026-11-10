# src/utils/save_manager.py
import json
import os
import shutil
import logging
import datetime

logger = logging.getLogger(__name__)

DIRETORIO_ATUAL = os.path.dirname(os.path.abspath(__file__)) 
DIRETORIO_SRC = os.path.dirname(DIRETORIO_ATUAL)              
DIRETORIO_RAIZ = os.path.dirname(DIRETORIO_SRC)               

PASTA_SAVES = os.path.join(DIRETORIO_RAIZ, "saves")
MAX_SLOTS = 4

NOMES_AMIGAVEIS_CENARIOS = {
    "CASA": "Cabana de Halia",
    "ESTRADA": "Estrada da Floresta",
    "ESTRADA_2": "Bloqueio Rochoso",
    "OAKHAVEN": "Vila de Oakhaven",
    "ORLA_NORTE": "Orla Norte (Fronteira)",
    "OAKHAVEN_DESTRUIDA": "Ruínas de Oakhaven",
    "NINHO_DRAGAO": "Ninho do Dragão",
}


def _obter_caminho_arquivo(slot, tipo="manual"):
    """Retorna o caminho do arquivo correspondente ao slot e tipo ('manual' ou 'autosave')."""
    if tipo == "autosave":
        return os.path.join(PASTA_SAVES, f"autosave_slot_{slot}.json")
    return os.path.join(PASTA_SAVES, f"slot_{slot}.json")


def salvar_dados(slot, dados, tipo="manual"):
    """
    Salva os dados do jogo no slot especificado com gravação atômica (.tmp)
    e criação preventiva de backup (.bak) para evitar qualquer corrupção.
    """
    if not os.path.exists(PASTA_SAVES):
        os.makedirs(PASTA_SAVES, exist_ok=True)

    caminho = _obter_caminho_arquivo(slot, tipo)
    caminho_tmp = f"{caminho}.tmp"
    caminho_bak = f"{caminho}.bak"

    # Injeta timestamp e data/hora se ainda não houver
    if "data_hora" not in dados:
        dados["data_hora"] = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    if "timestamp_epoch" not in dados:
        dados["timestamp_epoch"] = datetime.datetime.now().timestamp()

    # 1. Escreve primeiro no arquivo temporário
    with open(caminho_tmp, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

    # 2. Faz backup do arquivo estável anterior (se existir e tiver conteúdo válido)
    if os.path.exists(caminho) and os.path.getsize(caminho) > 0:
        try:
            shutil.copy2(caminho, caminho_bak)
        except Exception as e:
            logger.warning(f"[SaveIO] Falha ao criar backup .bak de {caminho}: {e}")

    # 3. Substitui atomicamente o arquivo principal
    os.replace(caminho_tmp, caminho)


def carregar_dados(slot, tipo="manual"):
    """
    Carrega os dados de um save manual ou autosave do slot especificado.
    Se o arquivo principal estiver ausente ou corrompido, tenta restaurar automaticamente do backup .bak.
    """
    caminho = _obter_caminho_arquivo(slot, tipo)
    caminho_bak = f"{caminho}.bak"

    if os.path.exists(caminho):
        try:
            with open(caminho, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"[SaveIO] Arquivo corrompido em {caminho}: {e}. Tentando restaurar do backup .bak...")

    # Fallback seguro: restauração a partir do arquivo .bak
    if os.path.exists(caminho_bak):
        try:
            with open(caminho_bak, "r", encoding="utf-8") as f:
                dados_recuperados = json.load(f)
                logger.info(f"[SaveIO] Save recuperado com sucesso a partir de {caminho_bak}!")
                # Restaura o arquivo principal a partir do backup íntegro
                shutil.copy2(caminho_bak, caminho)
                return dados_recuperados
        except Exception as e_bak:
            logger.error(f"[SaveIO] Falha crítica ao ler backup {caminho_bak}: {e_bak}")

    return None


def save_existe(slot, tipo=None):
    """
    Verifica se existe save no slot especificado.
    Se tipo for 'manual', checa apenas o save manual.
    Se tipo for 'autosave', checa apenas o autosave.
    Se tipo for None ou 'qualquer', checa se existe manual OU autosave.
    """
    if tipo == "manual":
        return os.path.exists(_obter_caminho_arquivo(slot, "manual"))
    elif tipo == "autosave":
        return os.path.exists(_obter_caminho_arquivo(slot, "autosave"))
    else:
        return os.path.exists(_obter_caminho_arquivo(slot, "manual")) or os.path.exists(_obter_caminho_arquivo(slot, "autosave"))


def verificar_saves_globais():
    """Retorna True se houver qualquer save (manual ou autosave) em qualquer um dos 4 slots."""
    for s in range(1, MAX_SLOTS + 1):
        if save_existe(s):
            return True
    return False


def apagar_dados(slot, tipo="ambos"):
    """
    Deleta os arquivos de save do slot especificado, incluindo arquivos temporários e de backup.
    tipo pode ser 'manual', 'autosave' ou 'ambos'.
    """
    tipos_apagar = []
    if tipo in ["manual", "ambos"]:
        tipos_apagar.append("manual")
    if tipo in ["autosave", "ambos"]:
        tipos_apagar.append("autosave")

    for t in tipos_apagar:
        caminho_base = _obter_caminho_arquivo(slot, t)
        for arq in [caminho_base, f"{caminho_base}.bak", f"{caminho_base}.tmp"]:
            if os.path.exists(arq):
                try:
                    os.remove(arq)
                except Exception as e:
                    logger.warning(f"[SaveIO] Erro ao remover {arq}: {e}")


def _extrair_resumo_dado(dados, slot=None, tipo="manual"):
    """Extrai metadados enriquecidos para exibição em menus de slot e modais comparativos."""
    if not dados:
        return {"existe": False}

    cenario_raw = dados.get("cenario_atual", "Desconhecido")
    flags = dados.get("flags", {})
    oakhaven_noite = flags.get("oakhaven_noite", False)

    if cenario_raw == "OAKHAVEN" and oakhaven_noite:
        cenario_formatado = "Vila de Oakhaven (Noite)"
    else:
        cenario_formatado = NOMES_AMIGAVEIS_CENARIOS.get(
            cenario_raw,
            cenario_raw.replace("_", " ").title()
        )

    # Identificação de Data/Hora (com fallback para mtime do arquivo físico)
    data_hora = dados.get("data_hora", "")
    timestamp_epoch = dados.get("timestamp_epoch", 0.0)
    if not data_hora and slot:
        caminho = _obter_caminho_arquivo(slot, tipo)
        if os.path.exists(caminho):
            mtime = os.path.getmtime(caminho)
            data_hora = datetime.datetime.fromtimestamp(mtime).strftime("%d/%m/%Y %H:%M")
            if timestamp_epoch <= 0:
                timestamp_epoch = mtime

    # Extração de Missão Ativa
    missao_info = dados.get("missao_ativa")
    if not missao_info or not isinstance(missao_info, dict):
        # Fallback retrocompatível: inspeciona o bloco 'missoes'
        missao_info = {"id": None, "titulo": "Sem Missão Ativa", "categoria": "NENHUMA"}
        bloco_missoes = dados.get("missoes", {}).get("missoes", {})
        if isinstance(bloco_missoes, dict):
            for m in bloco_missoes.values():
                if isinstance(m, dict) and m.get("status") == "ATIVA":
                    if m.get("categoria", "").upper() == "PRINCIPAL":
                        missao_info = {
                            "id": m.get("id"),
                            "titulo": m.get("titulo", "Missão Principal"),
                            "categoria": "PRINCIPAL"
                        }
                        break
                    elif missao_info.get("categoria") == "NENHUMA":
                        missao_info = {
                            "id": m.get("id"),
                            "titulo": m.get("titulo", "Missão Secundária"),
                            "categoria": "SECUNDARIA"
                        }

    halia = dados.get("halia", {})

    return {
        "existe": True,
        "cenario": cenario_raw,
        "cenario_formatado": cenario_formatado,
        "tempo_jogado": dados.get("tempo_jogado", 0.0),
        "data_hora": data_hora,
        "timestamp_epoch": timestamp_epoch,
        "missao_ativa": missao_info,
        "halia": halia,
        "tipo_save": dados.get("tipo_save", tipo)
    }


def obter_resumo_slots():
    """
    Retorna um dicionário com o status e informações detalhadas dos 4 slots de salvamento,
    discriminando tanto o Save Manual quanto o Autosave de cada slot e identificando
    qual é a versão mais recente em cada um.
    """
    resumos = {}
    for slot in range(1, MAX_SLOTS + 1):
        dados_manual = carregar_dados(slot, "manual")
        dados_autosave = carregar_dados(slot, "autosave")

        resumo_man = _extrair_resumo_dado(dados_manual, slot=slot, tipo="manual")
        resumo_auto = _extrair_resumo_dado(dados_autosave, slot=slot, tipo="autosave")

        # Determina qual versão é a mais recente
        mais_recente = "nenhum"
        if resumo_man.get("existe") and resumo_auto.get("existe"):
            ts_man = resumo_man.get("timestamp_epoch", 0.0)
            ts_auto = resumo_auto.get("timestamp_epoch", 0.0)
            if ts_auto > ts_man + 1.0:
                mais_recente = "autosave"
            elif ts_man > ts_auto + 1.0:
                mais_recente = "manual"
            else:
                # Compara pelo tempo jogado em caso de timestamps próximos
                tj_man = resumo_man.get("tempo_jogado", 0.0)
                tj_auto = resumo_auto.get("tempo_jogado", 0.0)
                mais_recente = "autosave" if tj_auto >= tj_man else "manual"
        elif resumo_man.get("existe"):
            mais_recente = "manual"
        elif resumo_auto.get("existe"):
            mais_recente = "autosave"

        resumos[slot] = {
            "manual": resumo_man,
            "autosave": resumo_auto,
            "tem_qualquer": (dados_manual is not None or dados_autosave is not None),
            "mais_recente": mais_recente
        }
    return resumos
