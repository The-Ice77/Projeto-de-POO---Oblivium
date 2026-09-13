# src/entities/player.py
from src.entities.Entity import Entidade
from src.mechanics.attributes import Atributos
from src.utils.resource_manager import ResourceManager, Animacao

class Player(Entidade):
    def __init__(self, nome="Halia", vida_maxima=100, x=210, y=280, velocidade=3, mana_maxima=50, dinheiro=0, atributos=None):
        # Atributos padrão da Halia (Foco em Magia, Agilidade e Presença)
        if atributos is None:
            atributos = Atributos(
                forca=8,
                destreza=12,
                constituicao=12,
                intelecto=15,
                sabedoria=13,
                presenca=14
            )
            
        super().__init__(nome, vida_maxima, x, y, velocidade, atributos=atributos)

        # Atributos exclusivos do jogador
        self.mana_maxima = mana_maxima
        self.mana_atual = mana_maxima
        self.fragmentos_memoria = 0
        self.dinheiro = dinheiro

        # Grimório / Lista de Magias e Habilidades Desbloqueadas (IDs no SkillsRegistry)
        self.magias_desbloqueadas = ["ataque_basico", "bola_de_fogo", "levitar", "brisa_curativa"]

        # Estado do jogador
        self.em_combate = False

    def recalcular_status_derivados(self, manter_porcentagem=True):
        """Atualiza a vida e mana máxima com base nos atributos atuais (ex: após level up ou itens)."""
        pct_vida = self.vida_atual / self.vida_maxima if self.vida_maxima > 0 else 1.0
        pct_mana = self.mana_atual / self.mana_maxima if self.mana_maxima > 0 else 1.0
        
        self.vida_maxima = self.atributos.calcular_vida_maxima(vida_base=40)
        self.mana_maxima = self.atributos.calcular_mana_maxima(mana_base=11)
        
        if manter_porcentagem:
            self.vida_atual = int(self.vida_maxima * pct_vida)
            self.mana_atual = int(self.mana_maxima * pct_mana)
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
        """Restaura vida e mana para os valores máximos."""
        self.vida_atual = self.vida_maxima
        self.mana_atual = self.mana_maxima
        self.vivo = True

    # Sistema de Magia Legado / Compatibilidade
    def usar_magia(self, custo_mana):
        if not self.vivo:
            print(f"{self.nome} não pode usar magia.")
            return False

        if self.gastar_mana(custo_mana):
            print(f"{self.nome} usou magia! Mana restante: {self.mana_atual}/{self.mana_maxima}")
            return True
        else:
            print("Mana insuficiente!")
            return False

    # Sistema de Memória
    def recuperar_memoria(self, quantidade):
        self.fragmentos_memoria += quantidade
        print(f"{self.nome} recuperou {quantidade} fragmento(s) de memória!")
        print(f"Total de memórias: {self.fragmentos_memoria}")

    # Sistema de Dinheiro
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

    # Combate
    def entrar_combate(self):
        self.em_combate = True
        self.defendendo = False
        print(f"{self.nome} entrou em combate!")

    def sair_combate(self):
        self.em_combate = False
        self.defendendo = False
        print(f"{self.nome} saiu do combate!")

    # Sobrescrita
    def morrer(self):
        super().morrer()
        print(f"{self.nome} desmaiou e retornará ao último checkpoint.")

    # Status
    def mostrar_status(self):
        print("< --- PLAYER --- >")
        print(f"Nome: {self.nome}")
        print(f"Vida: {self.vida_atual}/{self.vida_maxima}")
        print(f"Mana: {self.mana_atual}/{self.mana_maxima}")
        print(f"Atributos: {self.atributos}")
        print(f"Fragmentos de Memórias: {self.fragmentos_memoria}")
        print(f"Dinheiro: {self.dinheiro}")
        print(f"Posição: ({int(self.x)}, {int(self.y)})")