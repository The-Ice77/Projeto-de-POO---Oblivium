# src/entities/player.py
import os
import sys

# Garante que a pasta raiz do projeto ('Oblivium') esteja no sys.path
_raiz_projeto = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _raiz_projeto not in sys.path:
    sys.path.insert(0, _raiz_projeto)

from src.entities.Entity import Entidade
from src.mechanics.attributes import Atributos
from src.mechanics.grimorio import GrimorioHalia
from src.mechanics.inventory import Inventario
from src.mechanics.item_factory import ItemFactory
from src.utils.resource_manager import ResourceManager, Animacao

class Player(Entidade):
    """
    Representa Halia, a protagonista de Oblivium.
    Conceito Narrativo & Mecânico:
    Halia é uma Grã-Maga de nível máximo arcanista, mas devido a uma perda profunda de memória,
    sua mente e capacidades encontram-se seladas/reprimidas no início do jogo.
    Conforme resgata Fragmentos de Memória, ela desbloqueia parcelas do seu verdadeiro poder,
    ampliando seus atributos e despertando os feitiços ancestrais do seu Grimório.
    """
    NIVEL_VERDADEIRO = 50 # Grã-Maga Suprema

    def __init__(self, nome="Halia", vida_maxima=100, x=210, y=280, velocidade=3, mana_maxima=50, dinheiro=0, atributos=None):
        # Atributos iniciais contidos (Mente reprimida pela amnésia)
        if atributos is None:
            atributos = Atributos(
                forca=7,
                destreza=10,
                constituicao=10,
                intelecto=13,
                sabedoria=11,
                presenca=12
            )
            
        super().__init__(nome, vida_maxima, x, y, velocidade, atributos=atributos, mana_maxima=mana_maxima)

        # Controle de Memórias e Sincronia
        self.fragmentos_memoria = 0
        self.dinheiro = dinheiro
        self.nivel_sincronia = 1

        # Sistema de Inventário & Equipamentos
        self.inventario = Inventario()
        self.inicializar_inventario_padrao()

        # Ações Físicas Disponíveis (Submenu de Ataque Físico)
        self.ataques_fisicos = ["ataque_basico", "golpe_concentrado"]

        # Grimório Exclusivo da Halia (Desbloqueado dinamicamente por memórias)
        self.magias_desbloqueadas = []
        self.atualizar_grimorio()

        # Recalcula vida e mana base para o estado inicial
        self.recalcular_status_derivados(manter_porcentagem=False)
        # Halia inicia com vida e mana totais
        self.vida_atual = self.vida_maxima
        self.mana_atual = self.mana_maxima

        # Estado de Combate
        self.em_combate = False

    def inicializar_inventario_padrao(self):
        """No início do jogo, Halia começa sem equipamentos ou moedas até coletá-los na casa."""
        pass

    @property
    def moedas_ouro(self):
        """1 Moeda de Ouro = 10 de Prata = 200 de Cobre."""
        return self.dinheiro // 200

    @property
    def moedas_prata(self):
        """20 Moedas de Cobre = 1 de Prata."""
        return (self.dinheiro % 200) // 20

    @property
    def moedas_cobre(self):
        return self.dinheiro % 20

    def formatar_moedas(self):
        """Retorna uma string formatada com os valores decompostos de Ouro, Prata e Cobre."""
        partes = []
        if self.moedas_ouro > 0:
            partes.append(f"{self.moedas_ouro} Ouro")
        if self.moedas_prata > 0:
            partes.append(f"{self.moedas_prata} Prata")
        if self.moedas_cobre > 0 or not partes:
            partes.append(f"{self.moedas_cobre} Cobre")
        return ", ".join(partes)

    def tem_grimorio_desbloqueado(self):
        """
        Retorna se a aba de magias está desbloqueada.
        Neste momento inicial, o acesso direto à aba de magias permanece selado.
        """
        return False


    def atualizar_grimorio(self):
        """Sincroniza as magias conhecidas por Halia com o Grimório com base nas memórias."""
        self.magias_desbloqueadas = GrimorioHalia.obter_magias_desbloqueadas(self.fragmentos_memoria)

    def obter_atributos_totais(self):
        """
        Retorna uma instância temporária de Atributos somando os atributos base de Halia
        com todos os bônus concedidos por roupas, cajados e acessórios equipados.
        """
        bonus_eq = self.inventario.obter_bonus_totais_equipamentos()["atributos"] if hasattr(self, 'inventario') else {}
        return Atributos(
            forca=self.atributos.forca + bonus_eq.get("forca", 0),
            destreza=self.atributos.destreza + bonus_eq.get("destreza", 0),
            constituicao=self.atributos.constituicao + bonus_eq.get("constituicao", 0),
            intelecto=self.atributos.intelecto + bonus_eq.get("intelecto", 0),
            sabedoria=self.atributos.sabedoria + bonus_eq.get("sabedoria", 0),
            presenca=self.atributos.presenca + bonus_eq.get("presenca", 0)
        )

    def recalcular_status_derivados(self, manter_porcentagem=True):
        """Atualiza a vida e mana máxima com base nos atributos totais (base + equipamentos)."""
        vida_max_anterior = getattr(self, 'vida_maxima', 100)
        mana_max_anterior = getattr(self, 'mana_maxima', 50)
        pct_vida = self.vida_atual / vida_max_anterior if vida_max_anterior > 0 else 1.0
        pct_mana = self.mana_atual / mana_max_anterior if mana_max_anterior > 0 else 1.0
        
        # Base de HP e MP escala suavemente com a sincronia de memória
        vida_base_ajustada = 40 + (self.fragmentos_memoria * 8)
        mana_base_ajustada = 20 + (self.fragmentos_memoria * 10)

        attrs_totais = self.obter_atributos_totais()
        bonus_stats = self.inventario.obter_bonus_totais_equipamentos()["stats"] if hasattr(self, 'inventario') else {}

        self.vida_maxima = attrs_totais.calcular_vida_maxima(vida_base=vida_base_ajustada) + bonus_stats.get("vida_maxima_bonus", 0)
        self.mana_maxima = attrs_totais.calcular_mana_maxima(mana_base=mana_base_ajustada) + bonus_stats.get("mana_maxima_bonus", 0)
        
        if manter_porcentagem:
            # Se a vida máxima aumentou por Constituição/Upgrade, o ganho também é somado à vida atual
            delta_vida = max(0, self.vida_maxima - vida_max_anterior)
            delta_mana = max(0, self.mana_maxima - mana_max_anterior)
            self.vida_atual = min(self.vida_maxima, self.vida_atual + delta_vida)
            self.mana_atual = min(self.mana_maxima, self.mana_atual + delta_mana)
        else:
            self.vida_atual = min(self.vida_atual, self.vida_maxima)
            self.mana_atual = min(self.mana_atual, self.mana_maxima)

    def recuperar_mana(self, quantidade):
        """Recupera mana sem ultrapassar o limite máximo."""
        if not self.vivo: return
        self.mana_atual = min(self.mana_maxima, self.mana_atual + quantidade)

    def gastar_mana(self, custo):
        """Deduz mana se houver o suficiente. Retorna True se sucesso, False se insuficiente."""
        if self.mana_atual >= custo:
            self.mana_atual -= custo
            return True
        return False

    def restaurar_total(self):
        """Restaura vida e mana para os valores máximos e limpa estados."""
        super().restaurar_total()

    # ==========================================
    # SISTEMA DE MEMÓRIA & EVOLUÇÃO
    # ==========================================
    def recuperar_memoria(self, quantidade):
        """
        Ao recuperar fragmentos de memória, Halia reconecta-se com seu passado,
        aumentando seus atributos essenciais e despertando feitiços esquecidos.
        """
        self.fragmentos_memoria += quantidade
        self.nivel_sincronia = 1 + self.fragmentos_memoria

        # Bônus de Atributos pelo despertar da mente
        self.atributos.intelecto += (quantidade * 2)
        self.atributos.sabedoria += (quantidade * 2)
        self.atributos.presenca += (quantidade * 1)
        self.atributos.constituicao += (quantidade * 1)
        self.atributos.destreza += (quantidade * 1)

        # Atualiza limites derivados e ao ganhar CON além da vida máxima também ganha vida atual
        self.recalcular_status_derivados(manter_porcentagem=True)
        self.curar(15 * quantidade)
        self.recuperar_mana(15 * quantidade)

        # Verifica novos feitiços no Grimório
        magias_antigas = set(self.magias_desbloqueadas)
        self.atualizar_grimorio()
        novas_magias = [m for m in self.magias_desbloqueadas if m not in magias_antigas]

        print(f"[Memoria] {self.nome} recuperou {quantidade} fragmento(s) de memoria! (Total: {self.fragmentos_memoria})")
        print(f"[Memoria] Nivel de Sincronia Arcano aumentado para {self.nivel_sincronia}!")
        if novas_magias:
            nomes_novos = [GrimorioHalia.obter_todas_magias().get(m, {}).get("nome", m) for m in novas_magias]
            print(f"[Grimorio] Novos feiticos despertados: {', '.join(nomes_novos)}")

        return novas_magias

    # ==========================================
    # SISTEMA FINANCEIRO
    # ==========================================
    def ganhar_dinheiro(self, quantidade):
        self.dinheiro += quantidade
        print(f"{self.nome} recebeu {quantidade} moedas.")

    def gastar_dinheiro(self, quantidade):
        if self.dinheiro >= quantidade:
            self.dinheiro -= quantidade
            print(f"{self.nome} gastou {quantidade} moedas.")
            return True
        else:
            print("Dinheiro insuficiente!")
            return False

    # ==========================================
    # CICLO DE COMBATE
    # ==========================================
    def entrar_combate(self):
        self.em_combate = True
        self.defendendo = False
        self.vulneravel = False
        self.focado = False
        print(f"{self.nome} entrou em combate!")

    def sair_combate(self):
        self.em_combate = False
        self.defendendo = False
        self.vulneravel = False
        self.focado = False
        print(f"{self.nome} saiu do combate!")

    def morrer(self):
        super().morrer()
        print(f"{self.nome} desmaiou e retornará ao último checkpoint.")

    def mostrar_status(self):
        print("< --- HALIA (GRÃ-MAGA) --- >")
        print(f"Nome: {self.nome} | Sincronia de Memória: Nível {self.nivel_sincronia} (Potencial: {self.NIVEL_VERDADEIRO})")
        print(f"Vida: {self.vida_atual}/{self.vida_maxima} | Mana: {self.mana_atual}/{self.mana_maxima}")
        print(f"Atributos: {self.atributos}")
        print(f"Memórias Resgatadas: {self.fragmentos_memoria}")
        print(f"Ataques Físicos: {self.ataques_fisicos}")
        print(f"Magias Ativas no Grimório: {self.magias_desbloqueadas}")