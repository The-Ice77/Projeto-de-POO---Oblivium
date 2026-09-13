# src/entities/enemy_factory.py
import random
import copy
import json
import os
from src.entities.Enemy import Enemy
from src.entities.Boss import Boss
from src.mechanics.attributes import Atributos

class EnemyFactory:
    """
    Fábrica e Bestiário centralizado para instanciar inimigos e chefes de forma padronizada,
    com suporte a carregamento via JSON (src/data/bestiario.json), escalonamento de nível
    e geração aleatória de encontros.
    """

    _BESTIARIO = {}

    @classmethod
    def carregar_de_json(cls, caminho_json=None):
        """Carrega todas as fichas de inimigos a partir do arquivo JSON."""
        if caminho_json is None:
            diretorio_atual = os.path.dirname(os.path.abspath(__file__))
            caminho_json = os.path.join(diretorio_atual, "..", "data", "bestiario.json")

        if not os.path.exists(caminho_json):
            print(f"[EnemyFactory] Aviso: Arquivo '{caminho_json}' não encontrado. Usando catálogo em memória.")
            return False

        try:
            with open(caminho_json, "r", encoding="utf-8") as f:
                cls._BESTIARIO = json.load(f)
            return True
        except Exception as e:
            print(f"[EnemyFactory] Erro ao carregar bestiario.json: {e}")
            return False

    @classmethod
    def _garantir_carregamento(cls):
        """Garante que o Bestiário esteja carregado antes de qualquer operação."""
        if not cls._BESTIARIO:
            sucesso = cls.carregar_de_json()
            if not sucesso:
                # Fallback mínimo em memória se o JSON falhar
                cls._BESTIARIO = {
                    "sombra_menor": {
                        "nome": "Sombra Menor",
                        "classe": "Enemy",
                        "vida_base": 30,
                        "velocidade": 2.5,
                        "dano_base": 8,
                        "atributos": {"forca": 9, "destreza": 13, "constituicao": 9, "intelecto": 8, "sabedoria": 7, "presenca": 8},
                        "habilidades": ["ataque_basico", "golpe_sombrio"],
                        "recompensas": {"moedas": 8, "memorias": 0, "xp": 12},
                        "dimensoes": [35, 45],
                        "cor": [80, 30, 110]
                    },
                    "anomalia_maior": {
                        "nome": "Anomalia Maior",
                        "classe": "Boss",
                        "vida_base": 80,
                        "velocidade": 2.0,
                        "dano_base": 16,
                        "atributos": {"forca": 14, "destreza": 11, "constituicao": 16, "intelecto": 15, "sabedoria": 12, "presenca": 16},
                        "habilidades": ["golpe_sombrio", "impacto_anomalo"],
                        "recompensas": {"moedas": 45, "memorias": 1, "xp": 80},
                        "dimensoes": [55, 75],
                        "cor": [150, 0, 200]
                    }
                }

    # =========================================================================
    # MÉTODOS DE INSTANCIAÇÃO
    # =========================================================================

    @classmethod
    def criar(cls, id_tipo, x=1280, y=300, nivel=1, nome_custom=None, sprite=None):
        """
        Instancia um inimigo a partir do ID do Bestiário carregado do JSON.
        Permite escalonar o nível e sobrescrever o nome ou sprite.
        """
        cls._garantir_carregamento()
        
        template = cls._BESTIARIO.get(id_tipo)
        if not template:
            print(f"[EnemyFactory] Aviso: Tipo '{id_tipo}' não encontrado. Criando Sombra Menor como fallback.")
            template = cls._BESTIARIO.get("sombra_menor")

        # Escalonamento suave por nível
        fator_nivel = 1.0 + (nivel - 1) * 0.15
        vida_maxima = int(template["vida_base"] * fator_nivel)
        dano = int(template["dano_base"] * fator_nivel)

        # Copia e escala atributos
        attrs_base = template["atributos"]
        atributos = Atributos(
            forca=int(attrs_base["forca"] * fator_nivel),
            destreza=int(attrs_base["destreza"] * fator_nivel),
            constituicao=int(attrs_base["constituicao"] * fator_nivel),
            intelecto=int(attrs_base["intelecto"] * fator_nivel),
            sabedoria=int(attrs_base["sabedoria"] * fator_nivel),
            presenca=int(attrs_base["presenca"] * fator_nivel)
        )

        nome = nome_custom or template["nome"]
        recompensas = copy.deepcopy(template["recompensas"])
        recompensas["moedas"] = int(recompensas["moedas"] * fator_nivel)
        recompensas["xp"] = int(recompensas["xp"] * fator_nivel)

        tipo_classe = template.get("classe", "Enemy")
        classe_instancia = Boss if tipo_classe == "Boss" else Enemy

        inimigo = classe_instancia(
            nome=nome,
            vida_maxima=vida_maxima,
            velocidade=template["velocidade"],
            x=x,
            y=y,
            sprite=sprite,
            dano=dano,
            atributos=atributos,
            recompensas=recompensas
        )

        inimigo.habilidades = list(template.get("habilidades", ["ataque_basico"]))
        dimensoes = template.get("dimensoes", [40, 40])
        inimigo.largura = dimensoes[0]
        inimigo.altura = dimensoes[1]
        
        cor = template.get("cor", [150, 30, 50])
        inimigo.cor = tuple(cor)

        return inimigo

    @classmethod
    def criar_boss(cls, id_boss, x=1280, y=310, nivel=1, nome_custom=None, sprite=None):
        """Cria e retorna uma instância configurada de Boss a partir do JSON."""
        return cls.criar(id_tipo=id_boss, x=x, y=y, nivel=nivel, nome_custom=nome_custom, sprite=sprite)

    # =========================================================================
    # GERAÇÃO ALEATÓRIA DE ENCONTROS
    # =========================================================================

    @classmethod
    def gerar_encontro(cls, regiao="estrada", dificuldade=1, posicoes_custom=None):
        """
        Gera uma lista balanceada de 1 a 3 inimigos para uma batalha na região especificada.
        """
        cls._garantir_carregamento()

        posicoes_padrao = [
            (1280, 290),
            (1280, 420),
            (1280, 350)
        ]
        posicoes = posicoes_custom or posicoes_padrao

        tabelas_regiao = {
            "estrada": ["sombra_menor", "sombra_guardia", "espectro_errante"],
            "floresta": ["sombra_menor", "espectro_errante"],
            "ruinas": ["sombra_guardia", "espectro_errante"]
        }

        opcoes_inimigos = tabelas_regiao.get(regiao.lower(), ["sombra_menor"])
        
        qtd = random.randint(1, 2) if dificuldade == 1 else random.randint(2, 3)
        qtd = min(qtd, len(posicoes))

        grupo_inimigos = []
        for i in range(qtd):
            tipo_sorteado = random.choice(opcoes_inimigos)
            pos_x, pos_y = posicoes[i]
            sufixo = f" {i + 1}" if qtd > 1 else ""
            
            nome_modelo = cls._BESTIARIO[tipo_sorteado]["nome"]
            nome_final = f"{nome_modelo}{sufixo}"
            
            inimigo = cls.criar(tipo_sorteado, x=pos_x, y=pos_y, nivel=dificuldade, nome_custom=nome_final)
            grupo_inimigos.append(inimigo)

        return grupo_inimigos

    @classmethod
    def listar_todos_tipos(cls):
        """Retorna todos os IDs registrados no Bestiário."""
        cls._garantir_carregamento()
        return list(cls._BESTIARIO.keys())

    @classmethod
    def obter_info_bestiario(cls, id_tipo):
        """Retorna uma cópia das informações de template do inimigo."""
        cls._garantir_carregamento()
        return copy.deepcopy(cls._BESTIARIO.get(id_tipo))

# Inicializa o carregamento do JSON ao importar o módulo
EnemyFactory.carregar_de_json()
