# src/utils/save_manager.py
import json
import os

DIRETORIO_ATUAL = os.path.dirname(os.path.abspath(__file__)) 
DIRETORIO_SRC = os.path.dirname(DIRETORIO_ATUAL)              
DIRETORIO_RAIZ = os.path.dirname(DIRETORIO_SRC)               

PASTA_SAVES = os.path.join(DIRETORIO_RAIZ, "saves")
MAX_SLOTS = 4

def _obter_caminho_arquivo(slot, tipo="manual"):
    """Retorna o caminho do arquivo correspondente ao slot e tipo ('manual' ou 'autosave')."""
    if tipo == "autosave":
        return os.path.join(PASTA_SAVES, f"autosave_slot_{slot}.json")
    return os.path.join(PASTA_SAVES, f"slot_{slot}.json")

def salvar_dados(slot, dados, tipo="manual"):
    """Salva os dados do jogo no slot especificado como 'manual' ou 'autosave'."""
    if not os.path.exists(PASTA_SAVES):
        os.makedirs(PASTA_SAVES) 
        
    caminho = _obter_caminho_arquivo(slot, tipo)
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4)

def carregar_dados(slot, tipo="manual"):
    """Carrega os dados de um save manual ou autosave do slot especificado."""
    caminho = _obter_caminho_arquivo(slot, tipo)
    if os.path.exists(caminho):
        with open(caminho, "r", encoding="utf-8") as f:
            return json.load(f)
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
    Deleta os arquivos de save do slot especificado.
    tipo pode ser 'manual', 'autosave' ou 'ambos'.
    """
    if tipo in ["manual", "ambos"]:
        caminho_man = _obter_caminho_arquivo(slot, "manual")
        if os.path.exists(caminho_man):
            os.remove(caminho_man)
            
    if tipo in ["autosave", "ambos"]:
        caminho_auto = _obter_caminho_arquivo(slot, "autosave")
        if os.path.exists(caminho_auto):
            os.remove(caminho_auto)

def _extrair_resumo_dado(dados):
    if not dados:
        return {"existe": False}
    return {
        "existe": True,
        "cenario": dados.get("cenario_atual", "Desconhecido"),
        "tempo_jogado": dados.get("tempo_jogado", 0.0),
        "halia": dados.get("halia", {}),
        "tipo_save": dados.get("tipo_save", "manual")
    }

def obter_resumo_slots():
    """
    Retorna um dicionário com o status e informações detalhadas dos 4 slots de salvamento,
    discriminando tanto o Save Manual quanto o Autosave de cada slot.
    """
    resumos = {}
    for slot in range(1, MAX_SLOTS + 1):
        dados_manual = carregar_dados(slot, "manual")
        dados_autosave = carregar_dados(slot, "autosave")
        
        resumos[slot] = {
            "manual": _extrair_resumo_dado(dados_manual),
            "autosave": _extrair_resumo_dado(dados_autosave),
            "tem_qualquer": (dados_manual is not None or dados_autosave is not None)
        }
    return resumos