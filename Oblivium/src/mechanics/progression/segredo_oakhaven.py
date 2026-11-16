"""Regras e progresso por partida da assinatura escondida em Oakhaven."""

import math


class SegredoOakhaven:
    VERSAO = 1
    INDICIOS = {
        "quadro": "Na casa das canecas,",
        "canteiro": "onde a parede encontra o bosque,",
        "bancada": "mantenha a mão sobre a madeira. Não dê um passo.",
    }
    DURACAO_GESTO = 1.5
    ALCANCE = 36.0
    CONQUISTA = "assinatura_oculta_demo"

    def __init__(self):
        self.resetar()

    def resetar(self):
        self.indicios_lidos = set()
        self.concluida = False
        self.interromper()

    def interromper(self):
        self.tempo_gesto = 0.0
        self._posicao_inicio = None

    @property
    def progresso(self):
        return min(1.0, self.tempo_gesto / self.DURACAO_GESTO)

    def registrar_indicio(self, identificador):
        if identificador not in self.INDICIOS:
            return False
        novo = identificador not in self.indicios_lidos
        self.indicios_lidos.add(identificador)
        self.interromper()
        return novo

    def pode_tentar(self, posicao, direcao, ponto, direcao_alvo):
        return (
            not self.concluida
            and self.indicios_lidos == set(self.INDICIOS)
            and direcao == direcao_alvo
            and math.dist(posicao, ponto) <= self.ALCANCE
        )

    def atualizar(self, dt, *, pressionando, posicao, direcao, ponto,
                  direcao_alvo, disponivel=True, movimentando=False):
        """Retorna True somente no quadro da primeira conclusão legítima.

        Quadros maiores que 100 ms interrompem o gesto, evitando que retomar
        uma janela suspensa ou um travamento complete a espera de uma vez.
        """
        if (not disponivel or movimentando or not pressionando
                or not isinstance(dt, (int, float)) or isinstance(dt, bool)
                or not math.isfinite(dt) or not 0 < dt <= 0.1
                or not self.pode_tentar(posicao, direcao, ponto, direcao_alvo)):
            self.interromper()
            return False
        if self._posicao_inicio is not None and math.dist(posicao, self._posicao_inicio) > 0.1:
            self.interromper()
            return False
        self._posicao_inicio = tuple(posicao)
        self.tempo_gesto += dt
        if self.tempo_gesto + 1e-9 < self.DURACAO_GESTO:
            return False
        self.concluida = True
        self.interromper()
        return True

    def to_dict(self):
        return {
            "versao": self.VERSAO,
            "indicios_lidos": sorted(self.indicios_lidos),
            "concluida": self.concluida,
        }

    def carregar(self, dados):
        self.resetar()
        if not isinstance(dados, dict):
            return
        indicios = dados.get("indicios_lidos", [])
        if isinstance(indicios, list):
            self.indicios_lidos = {i for i in indicios if isinstance(i, str) and i in self.INDICIOS}
        self.concluida = (dados.get("concluida") is True
                          and self.indicios_lidos == set(self.INDICIOS))
