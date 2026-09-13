# src/mechanics/conditions.py
import random
import json
import os

class Condicao:
    """
    Representa uma condição ou efeito de estado temporário aplicado a uma entidade em combate.
    Carregado a partir do arquivo declarativo src/data/condicoes.json.
    (Ex: Em Chamas, Envenenado, Sangrando, Atordoado, Fortalecido).
    """
    _MODELOS = {}

    def __init__(self, id_condicao, nome, tipo, duracao=2, intensidade=5, elemento="NEUTRO", icone="✦", descricao=""):
        self.id_condicao = id_condicao
        self.nome = nome
        self.tipo = tipo            # "DOT" (dano por turno), "CC" (controle/atordoamento), "BUFF", "DEBUFF"
        self.duracao = duracao      # Quantidade de rodadas/turnos restantes
        self.intensidade = intensidade # Dano por turno ou bônus/penalidade
        self.elemento = elemento
        self.icone = icone
        self.descricao = descricao

    def processar_inicio_turno(self, entidade):
        """
        Executa os efeitos da condição no início do turno da entidade.
        Retorna um dicionário com os detalhes do efeito para o Combat Log e UI.
        """
        if not getattr(entidade, 'vivo', True):
            return None

        resultado = {
            "condicao": self,
            "entidade": entidade,
            "dano": 0,
            "cura": 0,
            "impede_acao": False,
            "mensagem": ""
        }

        # 1. Efeitos de Dano Contínuo (DoT)
        if self.tipo == "DOT":
            # Teste de Constituição pode mitigar parte do veneno
            dano = self.intensidade
            if self.elemento == "VENENO" and hasattr(entidade, 'atributos'):
                mod_con = entidade.atributos.mod_con
                dano = max(1, dano - max(0, mod_con))

            entidade.receber_dano(dano)
            resultado["dano"] = dano
            resultado["mensagem"] = f"{entidade.nome} sofreu {dano} de dano de {self.nome} {self.icone}!"

        # 2. Efeitos de Controle de Grupo (CC / Atordoamento / Congelamento)
        elif self.tipo == "CC":
            resultado["impede_acao"] = True
            resultado["mensagem"] = f"{entidade.nome} está {self.nome} {self.icone} e não pode agir este turno!"

        # 3. Buffs / Defesas Passivas
        elif self.tipo == "BUFF":
            entidade.defendendo = True
            resultado["mensagem"] = f"{entidade.nome} está sob efeito de {self.nome} {self.icone}!"

        # Reduz a duração restante da condição
        self.duracao -= 1
        return resultado

    def expirou(self):
        """Verifica se o efeito da condição chegou ao fim."""
        return self.duracao <= 0

    @classmethod
    def carregar_de_json(cls, caminho_json=None):
        """Carrega todas as definições de condições a partir do JSON."""
        if caminho_json is None:
            diretorio_atual = os.path.dirname(os.path.abspath(__file__))
            caminho_json = os.path.join(diretorio_atual, "..", "data", "condicoes.json")

        if not os.path.exists(caminho_json):
            print(f"[Condicao] Aviso: Arquivo '{caminho_json}' não encontrado. Usando catálogo em memória.")
            return False

        try:
            with open(caminho_json, "r", encoding="utf-8") as f:
                cls._MODELOS = json.load(f)
            return True
        except Exception as e:
            print(f"[Condicao] Erro ao carregar condicoes.json: {e}")
            return False

    @classmethod
    def _garantir_carregamento(cls):
        if not cls._MODELOS:
            sucesso = cls.carregar_de_json()
            if not sucesso:
                cls._MODELOS = {
                    "queimadura": {"nome": "Em Chamas", "tipo": "DOT", "duracao": 2, "intensidade": 7, "elemento": "FOGO", "icone": "🔥"},
                    "veneno": {"nome": "Envenenado", "tipo": "DOT", "duracao": 3, "intensidade": 5, "elemento": "VENENO", "icone": "☠️"},
                    "atordoado": {"nome": "Atordoado", "tipo": "CC", "duracao": 1, "intensidade": 0, "elemento": "NEUTRO", "icone": "💫"}
                }

    @classmethod
    def criar(cls, id_condicao, duracao=None, intensidade=None):
        """Instancia uma condição a partir do ID carregado do JSON."""
        cls._garantir_carregamento()
        cfg = cls._MODELOS.get(id_condicao.lower(), cls._MODELOS.get("queimadura"))
        
        return cls(
            id_condicao=id_condicao,
            nome=cfg["nome"],
            tipo=cfg["tipo"],
            duracao=duracao if duracao is not None else cfg["duracao"],
            intensidade=intensidade if intensidade is not None else cfg["intensidade"],
            elemento=cfg.get("elemento", "NEUTRO"),
            icone=cfg.get("icone", "✦"),
            descricao=cfg.get("descricao", "")
        )

# Inicializa o carregamento do JSON ao importar o módulo
Condicao.carregar_de_json()
