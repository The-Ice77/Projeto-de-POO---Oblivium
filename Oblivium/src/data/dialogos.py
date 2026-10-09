# src/data/dialogos.py
"""
Módulo de Diálogos de Oblivium (Camada de Compatibilidade).

Nota de Arquitetura:
Os diálogos oficiais do jogo foram migrados para 'src/data/dialogos.json'
e são gerenciados de forma orientada a objetos pela classe 'DialogueManager'
('src/mechanics/dialogue_manager.py').

Este arquivo fornece acesso direto às estruturas e sequências do JSON
para scripts de teste e compatibilidade retroativa.
"""

from src.mechanics.dialogue_manager import DialogueManager

_manager = DialogueManager()

def carregar_dialogo(id_conversa):
    """Retorna os nós brutos de uma conversa a partir do dialogos.json."""
    return _manager.banco_dialogos.get(id_conversa, {})

def obter_sequencia(id_conversa):
    """Retorna a sequência linear de falas de uma conversa."""
    return _manager.obter_sequencia_linear(id_conversa)

# Constantes utilitárias mapeadas diretamente para as conversas do JSON
HUB_CARROCEIRO = "hub_carroceiro"
INVESTIGAR_PEDRAS = "investigar_pedras"
ESCOLHA_MAGIAS = "escolha_magias"
FLASHBACK_MAGIA = "flashback_magia"
POS_FOGO = "pos_fogo"
POS_LEVITAR = "pos_levitar"
FALHA_TIMING = "falha_timing"
FALHA_MASH = "falha_mash"
PORTA_ABRIU = "porta_abriu"
PORTA_TRANCADA = "porta_trancada"
FECHAR_PORTA = "fechar_porta"
AVISTAR_CARROCEIRO = "avistar_carroceiro"
ENTRADA_ESTRADA1 = "entrada_estrada1"
ENTRADA_ESTRADA2 = "entrada_estrada2"
CARROCEIRO_ESTRADA2 = "carroceiro_estrada2"
POS_COMBATE_VITORIA = "pos_combate_vitoria"
CARROCEIRO_POS_COMBATE = "carroceiro_pos_combate"
CARROCEIRO_POS_PUZZLE = "carroceiro_pos_puzzle"
CARROCEIRO_IMPEDIMENTO = "carroceiro_impedimento"

# Sequência linear para o Flashback de Magia
textos_flashback_magia = _manager.obter_sequencia_linear(FLASHBACK_MAGIA)