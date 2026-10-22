# src/mechanics/combat_narrator.py
import os
import json
import logging

logger = logging.getLogger(__name__)

class CombatNarrator:
    """
    Gerenciador e Narrador Desacoplado de Textos e Diálogos de Combate de Oblivium.
    
    Responsabilidades:
    - Carrega de forma centralizada as strings narrativas a partir de 'src/data/combat_texts.json'.
    - Gera mensagens dramáticas e contextuais para mortes causadas por condições (DoT) ou ações diretas.
    - Fornece rótulos de interface, textos flutuantes (popups) e banners de vitória, derrota e fuga.
    - Garante fallback seguro em memória caso o arquivo JSON sofra qualquer falha de leitura.
    """
    _dados = None

    @classmethod
    def _garantir_carregamento(cls):
        """Carrega e armazena em cache os textos externos de combate."""
        if cls._dados is not None:
            return

        caminho_json = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "combat_texts.json")
        try:
            with open(caminho_json, "r", encoding="utf-8") as f:
                cls._dados = json.load(f)
        except Exception as e:
            logger.error("Falha ao carregar combat_texts.json: %s. Utilizando dicionário vazio de fallback.", e)
            cls._dados = {}

    @classmethod
    def obter_mensagem(cls, chave, **kwargs):
        """Retorna uma mensagem do sistema devidamente interpolada com os parâmetros informados."""
        cls._garantir_carregamento()
        msg_template = cls._dados.get("mensagens_sistema", {}).get(chave, "")
        if not msg_template:
            return ""
        try:
            return msg_template.format(**kwargs)
        except Exception:
            return msg_template

    @classmethod
    def obter_popup(cls, chave):
        """Retorna texto curto para popups e números flutuantes na arena."""
        cls._garantir_carregamento()
        return cls._dados.get("popups_flutuantes", {}).get(chave, chave.upper())

    @classmethod
    def obter_titulo_submenu(cls, chave):
        """Retorna o cabeçalho textual estilizado para os submenus de ações."""
        cls._garantir_carregamento()
        return cls._dados.get("titulos_submenus", {}).get(chave, "")

    @classmethod
    def obter_banner(cls, chave):
        """Retorna textos para os banners de encerramento da batalha."""
        cls._garantir_carregamento()
        return cls._dados.get("banners_fim_combate", {}).get(chave, "")

    @classmethod
    def gerar_mensagem_morte_condicao(cls, entidade, relatorios, eh_jogador=False):
        """
        Gera mensagem contextual dramática quando a entidade morre por efeito contínuo (DoT) no início do turno.
        """
        cls._garantir_carregamento()
        secao = cls._dados.get("morte_condicao", {})
        templates = secao.get("halia" if eh_jogador else "inimigo", {})

        elementos_causadores = []
        ids_causadores = []
        for r in relatorios:
            cond = r.get("condicao")
            if cond:
                elementos_causadores.append(getattr(cond, 'elemento', '').upper())
                ids_causadores.append(getattr(cond, 'id_condicao', '').lower())

        alvo_nome = getattr(entidade, 'nome', 'Inimigo')

        if "FOGO" in elementos_causadores or "queimadura" in ids_causadores:
            chave_elem = "FOGO"
        elif "VENENO" in elementos_causadores or "veneno" in ids_causadores:
            chave_elem = "VENENO"
        elif "FISICO" in elementos_causadores or "sangramento" in ids_causadores:
            chave_elem = "FISICO"
        elif "GELO" in elementos_causadores or "congelado" in ids_causadores:
            chave_elem = "GELO"
        elif "SOMBRA" in elementos_causadores or "miasma" in ids_causadores:
            chave_elem = "SOMBRA"
        else:
            chave_elem = "PADRAO"

        template = templates.get(chave_elem, templates.get("PADRAO", f"{alvo_nome} sucumbiu em batalha."))
        return template.format(alvo=alvo_nome)

    @classmethod
    def gerar_mensagem_morte_acao(cls, alvo, acao, eh_jogador=False):
        """
        Gera mensagem contextual dramática quando a entidade morre por um ataque ou magia direta.
        """
        cls._garantir_carregamento()
        secao = cls._dados.get("morte_acao", {})
        templates = secao.get("halia" if eh_jogador else "inimigo", {})

        elemento = getattr(acao, 'elemento', 'FISICO').upper() if acao else 'FISICO'
        tipo = getattr(acao, 'tipo', 'FISICO').upper() if acao else 'FISICO'
        nome_acao = getattr(acao, 'nome', 'Golpe') if acao else 'Golpe'
        alvo_nome = getattr(alvo, 'nome', 'Inimigo')

        if elemento == "FOGO":
            chave_elem = "FOGO"
        elif elemento == "ARCANO":
            chave_elem = "ARCANO"
        elif elemento == "SOMBRA":
            chave_elem = "SOMBRA"
        elif elemento == "GELO":
            chave_elem = "GELO"
        elif elemento in ["ELETRICO", "TROVAO", "RAIO"]:
            chave_elem = "ELETRICO"
        elif tipo == "FISICO":
            chave_elem = "FISICO"
        else:
            chave_elem = "PADRAO"

        template = templates.get(chave_elem, templates.get("PADRAO", f"{alvo_nome} foi derrotado por {nome_acao}."))
        return template.format(alvo=alvo_nome, acao=nome_acao)
