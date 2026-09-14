# src/mechanics/skills.py
import random
import json
import os
import sys

# Garante que a pasta raiz do projeto ('Oblivium') esteja no sys.path
_raiz_projeto = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _raiz_projeto not in sys.path:
    sys.path.insert(0, _raiz_projeto)

from src.mechanics.conditions import Condicao

class AcaoCombate:
    """
    Classe base para todas as ações executáveis em combate (Ataques, Magias, Foco, Suporte).
    Implementa o padrão Strategy / Command para execução desacoplada.
    """
    def __init__(self, id_acao, nome, descricao, tipo, elemento="FISICO", custo_mana=0, alvo_tipo="INIMIGO_UNICO", poder_base=10, condicao_aplicada=None):
        self.id_acao = id_acao
        self.nome = nome
        self.descricao = descricao
        self.tipo = tipo            # "FISICO", "MAGICO", "CURA", "FOCO", "BUFF", "DEBUFF"
        self.elemento = elemento    # "FISICO", "FOGO", "ARCANO", "SAGRADO", "SOMBRA", "NEUTRO"
        self.custo_mana = custo_mana
        self.alvo_tipo = alvo_tipo  # "INIMIGO_UNICO", "TODOS_INIMIGOS", "PROPRIO", "ALIADO"
        self.poder_base = poder_base
        self.condicao_aplicada = condicao_aplicada # Dict com {"id_condicao": ..., "chance": ...}

    @property
    def tipo_alvo(self):
        """Retorna o tipo de alvo em formato minúsculo padronizado."""
        return str(self.alvo_tipo).lower()

    @tipo_alvo.setter
    def tipo_alvo(self, valor):
        self.alvo_tipo = valor

    def pode_usar(self, conjurador):
        """Verifica se o conjurador tem recursos (mana/vida) para executar a ação."""
        if not getattr(conjurador, 'vivo', True):
            return False
        if self.custo_mana > 0:
            mana_atual = getattr(conjurador, 'mana_atual', 0)
            return mana_atual >= self.custo_mana
        return True

    def deduzir_custos(self, conjurador):
        """Deduz o custo de mana do conjurador."""
        if self.custo_mana > 0 and hasattr(conjurador, 'gastar_mana'):
            return conjurador.gastar_mana(self.custo_mana)
        elif self.custo_mana > 0 and hasattr(conjurador, 'mana_atual'):
            conjurador.mana_atual -= self.custo_mana
            return True
        return True

    def calcular_critico(self, conjurador):
        """Determina se a ação gerou um acerto crítico baseado em Destreza e Presença."""
        if not hasattr(conjurador, 'atributos'):
            return False, 1.0
        chance = conjurador.atributos.calcular_chance_critico()
        rolagem = random.uniform(0, 100)
        if rolagem <= chance:
            return True, 1.5
        return False, 1.0

    def tentar_aplicar_condicao(self, alvo):
        """Aplica condição de estado caso configurada e a rolagem de chance tenha sucesso."""
        if not self.condicao_aplicada or not hasattr(alvo, 'adicionar_condicao'):
            return None

        chance = self.condicao_aplicada.get("chance", 30)
        id_cond = self.condicao_aplicada.get("id_condicao", "queimadura")
        duracao = self.condicao_aplicada.get("duracao", None)
        intensidade = self.condicao_aplicada.get("intensidade", None)

        if random.uniform(0, 100) <= chance:
            nova_cond = Condicao.criar(id_cond, duracao=duracao, intensidade=intensidade)
            alvo.adicionar_condicao(nova_cond)
            return nova_cond
        return None

    def verificar_acerto(self, conjurador, alvo):
        """
        Calcula se o ataque/magia acertou o alvo com base em Destreza, atributos e postura defensiva.
        Retorna (acertou: bool, motivo: str) onde motivo pode ser 'acerto', 'esquiva' ou 'erro'.
        """
        if not hasattr(alvo, 'atributos') or not hasattr(conjurador, 'atributos'):
            return True, "acerto"

        # Se o alvo estiver atordoado ou incapacitado, acerto garantido (100%)
        if getattr(alvo, 'esta_atordoado', False):
            return True, "acerto"

        # Precisão do atacante
        if self.tipo == "FISICO":
            precisao_base = 86.0
            bonus_conjurador = (conjurador.atributos.mod_des * 2.0) + (conjurador.atributos.mod_for * 0.5)
        else: # MAGICO
            precisao_base = 88.0
            bonus_conjurador = (conjurador.atributos.mod_int * 2.0) + (conjurador.atributos.mod_sab * 1.0)

        # Evasão do defensor (base de agilidade + modificador de Destreza)
        evasao_base = 8.0
        evasao_alvo = evasao_base + max(0.0, alvo.atributos.mod_des * 3.0)
        
        # Postura defensiva (Defender) concede enorme bônus de esquiva (+45%)
        if getattr(alvo, 'defendendo', False):
            evasao_alvo += 45.0
            
        # Estado vulnerável (Foco Espiritual) reduz drasticamente a esquiva (-15%)
        if getattr(alvo, 'vulneravel', False):
            evasao_alvo = max(0.0, evasao_alvo - 15.0)

        # Chance final de acerto
        chance_acerto = max(25.0, min(95.0, precisao_base + bonus_conjurador - evasao_alvo))
        rolagem = random.uniform(0, 100)

        if rolagem <= chance_acerto:
            return True, "acerto"
        else:
            # Se o alvo estava defendendo ou tem evasão relevante, conta como esquiva ágil
            if getattr(alvo, 'defendendo', False) or evasao_alvo >= 10.0 or random.random() < 0.75:
                return False, "esquiva"
            return False, "erro"

    def executar(self, conjurador, alvos):
        """
        Executa a ação sobre uma lista de alvos.
        Retorna um dicionário com o relatório detalhado da execução para a UI / Combat Log.
        """
        raise NotImplementedError("Subclasses devem implementar o método executar.")


# ==============================================================================
# SUBCLASSES ESPECÍFICAS DE AÇÕES
# ==============================================================================

class AtaqueFisico(AcaoCombate):
    """Ataque físico direto escalado com Força e Destreza."""
    def __init__(self, id_acao, nome, descricao, poder_base=12, custo_mana=0, alvo_tipo="INIMIGO_UNICO", elemento="FISICO", condicao_aplicada=None):
        super().__init__(id_acao, nome, descricao, tipo="FISICO", elemento=elemento, custo_mana=custo_mana, alvo_tipo=alvo_tipo, poder_base=poder_base, condicao_aplicada=condicao_aplicada)

    def executar(self, conjurador, alvos):
        if not self.pode_usar(conjurador):
            return {"sucesso": False, "mensagem": f"{conjurador.nome} não tem mana suficiente!"}

        self.deduzir_custos(conjurador)
        resultados = []

        if not isinstance(alvos, list):
            alvos = [alvos]

        for alvo in alvos:
            if not getattr(alvo, 'vivo', True):
                continue

            # 1. Verifica se o ataque acertou ou errou/esquivou
            acertou, motivo = self.verificar_acerto(conjurador, alvo)
            if not acertou:
                if motivo == "esquiva":
                    msg = f"{conjurador.nome} usou {self.nome}, mas {alvo.nome} se esquivou agilmente!"
                else:
                    msg = f"{conjurador.nome} usou {self.nome}, mas errou o ataque contra {alvo.nome}!"
                
                resultados.append({
                    "alvo": alvo,
                    "dano": 0,
                    "cura": 0,
                    "errou": True,
                    "motivo": motivo,
                    "critico": False,
                    "tipo_dano": "FISICO",
                    "mensagem": msg
                })
                continue

            # 2. Executa cálculo de dano e crítico em caso de acerto
            critico, mult_crit = self.calcular_critico(conjurador)
            mod_for = getattr(conjurador.atributos, 'mod_for', 0) if hasattr(conjurador, 'atributos') else 0
            mod_des = getattr(conjurador.atributos, 'mod_des', 0) if hasattr(conjurador, 'atributos') else 0
            variacao = random.randint(-2, 2)

            dano_bruto = int((self.poder_base + (mod_for * 1.5) + (mod_des * 0.8) + variacao) * mult_crit)
            dano_bruto = max(1, dano_bruto)

            dano_sofrido = alvo.aplicar_dano(dano_bruto, tipo="fisico")
            
            cond_aplicada = self.tentar_aplicar_condicao(alvo)
            texto_crit = " (CRÍTICO!)" if critico else ""
            texto_cond = f" [{cond_aplicada.nome} {cond_aplicada.icone}]" if cond_aplicada else ""
            msg = f"{conjurador.nome} usou {self.nome} em {alvo.nome} causando {dano_sofrido} de dano{texto_crit}{texto_cond}."
            
            resultados.append({
                "alvo": alvo,
                "dano": dano_sofrido,
                "cura": 0,
                "errou": False,
                "motivo": "acerto",
                "critico": critico,
                "condicao": cond_aplicada,
                "tipo_dano": "FISICO",
                "mensagem": msg
            })

        return {
            "sucesso": True,
            "acao": self,
            "conjurador": conjurador,
            "resultados": resultados
        }


class MagiaOfensiva(AcaoCombate):
    """Magia de dano elemental / arcano escalada com Intelecto e Sabedoria."""
    def __init__(self, id_acao, nome, descricao, elemento, custo_mana, poder_base=20, alvo_tipo="INIMIGO_UNICO", condicao_aplicada=None):
        super().__init__(id_acao, nome, descricao, tipo="MAGICO", elemento=elemento, custo_mana=custo_mana, alvo_tipo=alvo_tipo, poder_base=poder_base, condicao_aplicada=condicao_aplicada)

    def executar(self, conjurador, alvos):
        if not self.pode_usar(conjurador):
            return {"sucesso": False, "mensagem": f"{conjurador.nome} não tem mana suficiente para {self.nome}!"}

        self.deduzir_custos(conjurador)
        resultados = []

        if not isinstance(alvos, list):
            alvos = [alvos]

        for alvo in alvos:
            if not getattr(alvo, 'vivo', True):
                continue

            # 1. Verifica se a magia acertou ou errou/esquivou
            acertou, motivo = self.verificar_acerto(conjurador, alvo)
            if not acertou:
                if motivo == "esquiva":
                    msg = f"{conjurador.nome} conjurou {self.nome}, mas {alvo.nome} esquivou-se da magia!"
                else:
                    msg = f"{conjurador.nome} conjurou {self.nome}, mas a magia errou o alvo {alvo.nome}!"
                
                resultados.append({
                    "alvo": alvo,
                    "dano": 0,
                    "cura": 0,
                    "errou": True,
                    "motivo": motivo,
                    "critico": False,
                    "tipo_dano": "MAGICO",
                    "elemento": self.elemento,
                    "mensagem": msg
                })
                continue

            # 2. Executa cálculo de dano e crítico em caso de acerto
            critico, mult_crit = self.calcular_critico(conjurador)
            mod_int = getattr(conjurador.atributos, 'mod_int', 0) if hasattr(conjurador, 'atributos') else 0
            mod_sab = getattr(conjurador.atributos, 'mod_sab', 0) if hasattr(conjurador, 'atributos') else 0
            variacao = random.randint(-2, 3)

            dano_bruto = int((self.poder_base + (mod_int * 2.2) + (mod_sab * 0.8) + variacao) * mult_crit)
            dano_bruto = max(2, dano_bruto)

            dano_sofrido = alvo.aplicar_dano(dano_bruto, tipo="magico")
            
            cond_aplicada = self.tentar_aplicar_condicao(alvo)
            texto_crit = " (CRÍTICO MÁGICO!)" if critico else ""
            texto_cond = f" [{cond_aplicada.nome} {cond_aplicada.icone}]" if cond_aplicada else ""
            msg = f"{conjurador.nome} conjurou {self.nome} em {alvo.nome} causando {dano_sofrido} de dano [{self.elemento}]{texto_crit}{texto_cond}."
            
            resultados.append({
                "alvo": alvo,
                "dano": dano_sofrido,
                "cura": 0,
                "errou": False,
                "motivo": "acerto",
                "critico": critico,
                "condicao": cond_aplicada,
                "tipo_dano": "MAGICO",
                "elemento": self.elemento,
                "mensagem": msg
            })

        return {
            "sucesso": True,
            "acao": self,
            "conjurador": conjurador,
            "resultados": resultados
        }


class MagiaCura(AcaoCombate):
    """Magia de restauração de pontos de vida escalada com Sabedoria e Presença."""
    def __init__(self, id_acao, nome, descricao, custo_mana=15, poder_base=25, alvo_tipo="PROPRIO", condicao_aplicada=None):
        super().__init__(id_acao, nome, descricao, tipo="CURA", elemento="SAGRADO", custo_mana=custo_mana, alvo_tipo=alvo_tipo, poder_base=poder_base, condicao_aplicada=condicao_aplicada)

    def executar(self, conjurador, alvos):
        if not self.pode_usar(conjurador):
            return {"sucesso": False, "mensagem": f"{conjurador.nome} não tem mana suficiente para {self.nome}!"}

        self.deduzir_custos(conjurador)
        resultados = []

        if not isinstance(alvos, list):
            alvos = [alvos]

        for alvo in alvos:
            if not getattr(alvo, 'vivo', True):
                continue

            mod_sab = getattr(conjurador.atributos, 'mod_sab', 0) if hasattr(conjurador, 'atributos') else 0
            mod_pre = getattr(conjurador.atributos, 'mod_pre', 0) if hasattr(conjurador, 'atributos') else 0
            variacao = random.randint(-1, 3)

            cura_bruta = max(5, self.poder_base + (mod_sab * 2.5) + (mod_pre * 1.2) + variacao)
            vida_antes = alvo.vida_atual
            alvo.curar(cura_bruta)
            cura_efetiva = alvo.vida_atual - vida_antes

            msg = f"{conjurador.nome} usou {self.nome} e recuperou {cura_efetiva} de vida ({alvo.vida_atual}/{alvo.vida_maxima})."
            
            resultados.append({
                "alvo": alvo,
                "dano": 0,
                "cura": cura_efetiva,
                "critico": False,
                "tipo_dano": "CURA",
                "mensagem": msg
            })

        return {
            "sucesso": True,
            "acao": self,
            "conjurador": conjurador,
            "resultados": resultados
        }


class AcaoDefender(AcaoCombate):
    """Ação tática que assume postura de guarda para reduzir danos pela metade e esquivar de ataques."""
    def __init__(self, id_acao="defender", nome="Defender", descricao="Assume postura de guarda. Reduz danos recebidos pela metade e esquiva com facilidade."):
        super().__init__(id_acao, nome, descricao, tipo="DEFESA", elemento="NEUTRO", custo_mana=0, alvo_tipo="PROPRIO", poder_base=0)

    def executar(self, conjurador, alvos=None):
        conjurador.defendendo = True
        conjurador.vulneravel = False
        conjurador.focado = False

        msg = f"{conjurador.nome} assumiu postura defensiva em guarda total, reduzindo danos e preparando esquiva!"
        
        return {
            "sucesso": True,
            "acao": self,
            "conjurador": conjurador,
            "defendendo": True,
            "mensagem": msg,
            "resultados": [{
                "alvo": conjurador,
                "dano": 0,
                "cura": 0,
                "defendendo": True,
                "critico": False,
                "mensagem": msg
            }]
        }


class AcaoFoco(AcaoCombate):
    """Ação que canaliza energia espiritual para recuperar Mana, abrindo a guarda e deixando o conjurador vulnerável."""
    def __init__(self, id_acao="foco_espiritual", nome="Foco Espiritual", descricao="Canaliza energia espiritual para recuperar grande quantidade de Mana, mas fica vulnerável (+35% dano)."):
        super().__init__(id_acao, nome, descricao, tipo="FOCO", elemento="NEUTRO", custo_mana=0, alvo_tipo="PROPRIO", poder_base=15)

    def executar(self, conjurador, alvos=None):
        mod_pre = getattr(conjurador.atributos, 'mod_pre', 0) if hasattr(conjurador, 'atributos') else 0
        mod_sab = getattr(conjurador.atributos, 'mod_sab', 0) if hasattr(conjurador, 'atributos') else 0
        
        mana_recuperada = max(12, 12 + (mod_pre * 3) + (mod_sab * 2) + random.randint(2, 5))
        
        mana_antes = getattr(conjurador, 'mana_atual', 0)
        if hasattr(conjurador, 'recuperar_mana'):
            conjurador.recuperar_mana(mana_recuperada)
        elif hasattr(conjurador, 'mana_atual'):
            conjurador.mana_atual = min(conjurador.mana_maxima, conjurador.mana_atual + mana_recuperada)
        mana_efetiva = conjurador.mana_atual - mana_antes

        # Ao concentrar, abre a guarda ficando vulnerável
        conjurador.defendendo = False
        conjurador.vulneravel = True
        conjurador.focado = True

        msg = f"{conjurador.nome} concentrou sua energia recuperando {mana_efetiva} MP, mas ficou vulnerável a ataques (+35% dano)!"
        
        return {
            "sucesso": True,
            "acao": self,
            "conjurador": conjurador,
            "mana_recuperada": mana_efetiva,
            "vulneravel": True,
            "mensagem": msg,
            "resultados": [{
                "alvo": conjurador,
                "dano": 0,
                "cura": 0,
                "mana_recuperada": mana_efetiva,
                "vulneravel": True,
                "critico": False,
                "mensagem": msg
            }]
        }


# ==============================================================================
# REGISTRO CENTRAL DE HABILIDADES (REGISTRY PATTERN)
# ==============================================================================

class SkillsRegistry:
    """
    Catálogo centralizado de todas as habilidades, magias e ações de combate do jogo.
    Permite registrar novas habilidades e buscá-las por ID de forma global.
    """
    _catalogo = {}

    @classmethod
    def registrar(cls, acao):
        """Registra uma ação ou magia no catálogo."""
        cls._catalogo[acao.id_acao] = acao

    @classmethod
    def get(cls, id_acao):
        """Retorna uma ação pelo ID ou None se não existir."""
        if not cls._catalogo:
            cls.inicializar_catalogo_padrao()

        aliases = {
            "defender": "defender",
            "defesa": "defender",
            "guarda": "defender",
            "foco": "foco_espiritual",
            "concentrar": "foco_espiritual",
            "ataque": "ataque_basico",
            "cajado": "ataque_basico",
            "fogo": "bola_de_fogo",
            "cura": "brisa_curativa"
        }
        id_str = str(id_acao).lower()
        chave = aliases.get(id_str, id_str)
        return cls._catalogo.get(chave) or cls._catalogo.get(id_acao)

    @classmethod
    def listar_todas(cls):
        """Retorna lista de todas as ações registradas."""
        return list(cls._catalogo.values())

    @classmethod
    def obter_magias_iniciais_player(cls):
        """Retorna as magias que Halia possui no início da jornada."""
        return [
            cls.get("ataque_basico"),
            cls.get("bola_de_fogo"),
            cls.get("levitar"),
            cls.get("brisa_curativa")
        ]

    @classmethod
    def carregar_de_json(cls, caminho_json=None):
        """Carrega todas as habilidades e magias a partir do arquivo JSON."""
        if caminho_json is None:
            diretorio_atual = os.path.dirname(os.path.abspath(__file__))
            caminho_json = os.path.join(diretorio_atual, "..", "data", "skills.json")
            
        if not os.path.exists(caminho_json):
            print(f"[SkillsRegistry] Aviso: Arquivo '{caminho_json}' não encontrado. Usando catálogo em memória.")
            return False

        try:
            with open(caminho_json, "r", encoding="utf-8") as f:
                dados = json.load(f)

            cls._catalogo.clear()
            for id_acao, info in dados.items():
                tipo = info.get("tipo", "MAGICO").upper()
                cond = info.get("condicao_aplicada", None)
                
                if tipo == "FISICO":
                    instancia = AtaqueFisico(
                        id_acao=info["id_acao"],
                        nome=info["nome"],
                        descricao=info.get("descricao", ""),
                        poder_base=info.get("poder_base", 12),
                        custo_mana=info.get("custo_mana", 0),
                        alvo_tipo=info.get("alvo_tipo", "INIMIGO_UNICO"),
                        elemento=info.get("elemento", "FISICO"),
                        condicao_aplicada=cond
                    )
                elif tipo == "CURA":
                    instancia = MagiaCura(
                        id_acao=info["id_acao"],
                        nome=info["nome"],
                        descricao=info.get("descricao", ""),
                        custo_mana=info.get("custo_mana", 15),
                        poder_base=info.get("poder_base", 25),
                        alvo_tipo=info.get("alvo_tipo", "PROPRIO"),
                        condicao_aplicada=cond
                    )
                elif tipo == "DEFESA":
                    instancia = AcaoDefender(
                        id_acao=info["id_acao"],
                        nome=info["nome"],
                        descricao=info.get("descricao", "")
                    )
                elif tipo == "FOCO":
                    instancia = AcaoFoco(
                        id_acao=info["id_acao"],
                        nome=info["nome"],
                        descricao=info.get("descricao", "")
                    )
                else: # MAGICO
                    instancia = MagiaOfensiva(
                        id_acao=info["id_acao"],
                        nome=info["nome"],
                        descricao=info.get("descricao", ""),
                        elemento=info.get("elemento", "ARCANO"),
                        custo_mana=info.get("custo_mana", 10),
                        poder_base=info.get("poder_base", 20),
                        alvo_tipo=info.get("alvo_tipo", "INIMIGO_UNICO"),
                        condicao_aplicada=cond
                    )
                
                cls.registrar(instancia)
            return True
        except Exception as e:
            print(f"[SkillsRegistry] Erro ao carregar skills.json: {e}")
            return False

    @classmethod
    def inicializar_catalogo_padrao(cls):
        """Inicializa o catálogo prioritariamente a partir do JSON."""
        sucesso = cls.carregar_de_json()
        if not sucesso:
            # Fallback seguro caso o JSON não esteja disponível
            cls.registrar(AtaqueFisico("ataque_basico", "Golpe com Cajado", "Ataque físico", 12))
            cls.registrar(AcaoDefender("defender", "Defender", "Assume postura defensiva"))
            cls.registrar(AcaoFoco("foco_espiritual", "Concentrar", "Recupera Mana"))
            cls.registrar(MagiaOfensiva("bola_de_fogo", "Bola de Fogo", "Fogo", "FOGO", 12, 22))
            cls.registrar(MagiaOfensiva("levitar", "Pulso de Gravidade", "Arcano", "ARCANO", 14, 24))
            cls.registrar(MagiaCura("brisa_curativa", "Brisa Curativa", "Cura", 15, 28))

# Inicializa o catálogo padrão automaticamente ao carregar o módulo
SkillsRegistry.inicializar_catalogo_padrao()
