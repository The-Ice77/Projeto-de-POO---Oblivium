# src/utils/save_manager.py
import json
import os

DIRETORIO_ATUAL = os.path.dirname(os.path.abspath(__file__)) 
DIRETORIO_SRC = os.path.dirname(DIRETORIO_ATUAL)              
DIRETORIO_RAIZ = os.path.dirname(DIRETORIO_SRC)               

PASTA_SAVES = os.path.join(DIRETORIO_RAIZ, "saves")

def salvar_dados(slot, dados):
    if not os.path.exists(PASTA_SAVES):
        os.makedirs(PASTA_SAVES) 
        
    caminho = os.path.join(PASTA_SAVES, f"slot_{slot}.json")
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4)

def carregar_dados(slot):
    caminho = os.path.join(PASTA_SAVES, f"slot_{slot}.json")
    if os.path.exists(caminho):
        with open(caminho, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def save_existe(slot):
    caminho = os.path.join(PASTA_SAVES, f"slot_{slot}.json")
    return os.path.exists(caminho)

def verificar_saves_globais():
    return save_existe(1) or save_existe(2) or save_existe(3)

# --- NOVA FUNÇÃO PARA APAGAR SAVES ---
def apagar_dados(slot):
    """Deleta o arquivo de save do slot especificado."""
    caminho = os.path.join(PASTA_SAVES, f"slot_{slot}.json")
    if os.path.exists(caminho):
        os.remove(caminho)

def obter_resumo_slots():
    """Retorna um dicionário com o status e informações básicas dos 3 slots de salvamento."""
    resumos = {}
    for slot in range(1, 4):
        dados = carregar_dados(slot)
        if dados:
            resumos[slot] = {
                "existe": True,
                "cenario": dados.get("cenario_atual", "Desconhecido"),
                "tempo_jogado": dados.get("tempo_jogado", 0.0),
                "halia": dados.get("halia", {})
            }
        else:
            resumos[slot] = {"existe": False}
    return resumos