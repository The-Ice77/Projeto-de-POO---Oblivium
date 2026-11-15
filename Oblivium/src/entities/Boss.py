# src/entities/Boss.py
import random

from src.entities.Enemy import Enemy
from src.mechanics.attributes import Atributos


class Boss(Enemy):
    """
    Classe para Chefes e Mini-Chefes.
    Herda de Enemy com atributos aprimorados, múltiplas fases, imunidade anti-stunlock e IA tática.
    """

    _TURNOS_IMUNIDADE_CC = 2

    def __init__(self, nome, vida_maxima, velocidade, x, y, sprite=None, dano=15, atributos=None, recompensas=None, mana_maxima=None, pasta_sprites="demonio_superior"):
        if atributos is None:
            atributos = Atributos(
                forca=14,
                destreza=12,
                constituicao=14,
                intelecto=13,
                sabedoria=11,
                presenca=14
            )

        if recompensas is None:
            recompensas = {"moedas": 50, "memorias": 1, "xp": 100}

        super().__init__(nome, vida_maxima, velocidade, x, y, sprite=sprite, dano=dano, agressivo=True, atributos=atributos, recompensas=recompensas, mana_maxima=mana_maxima, pasta_sprites=pasta_sprites)

        self.fase = 1
        self.enfurecido = False
        self.multiplicador_fase = 1.0
        self.preparando_sopro = False
        self.turno_ia = 0
        self.cooldown_sopro = 2
        self.cooldown_escamas = 0

    def restaurar_total(self):
        super().restaurar_total()
        self.fase = 1
        self.enfurecido = False
        self.multiplicador_fase = 1.0
        self.preparando_sopro = False
        self.turno_ia = 0
        self.cooldown_sopro = 2
        self.cooldown_escamas = 0

    def morrer(self):
        self.preparando_sopro = False
        super().morrer()

    def verificar_mudanca_fase(self):
        """Ativa Fase 2 (Enfurecido, +15% de poder) uma única vez quando a vida cai para <= 50%."""
        if (
            getattr(self, "vivo", True)
            and self.vida_atual > 0
            and self.vida_atual <= (self.vida_maxima * 0.50)
            and not self.enfurecido
        ):
            self.enfurecido = True
            self.fase = 2
            self.multiplicador_fase = 1.15
            self.dano = max(self.dano + 1, int(round(self.dano * 1.15)))
            print(f"[BOSS] {self.nome} entrou na Fase 2 (Enfurecido)!")
            return True
        return False

    def _eh_dragao(self):
        kit = getattr(self, "habilidades", ())
        return "dragao" in getattr(self, "pasta_sprites", "").lower() or "sopro_de_brasas" in kit

    def decidir_acao_ia(self):
        """Seleciona a próxima ação ou estado de preparação telegrafada para chefes."""
        from src.mechanics.rpg import SkillsRegistry

        kit = list(getattr(self, "habilidades", ("golpe_sombrio", "investida_sombria")))
        if self._eh_dragao():
            sopro = SkillsRegistry.get("sopro_de_brasas")
            if self.preparando_sopro:
                self.preparando_sopro = False
                if sopro and sopro.pode_usar(self):
                    self.cooldown_sopro = 3 if self.fase >= 2 else 4
                    return sopro

            self.turno_ia += 1
            self.cooldown_sopro = max(0, self.cooldown_sopro - 1)
            self.cooldown_escamas = max(0, self.cooldown_escamas - 1)

            if self.cooldown_sopro == 0 and sopro and sopro.pode_usar(self):
                self.preparando_sopro = True
                return "PREPARAR_SOPRO"

            if (
                "escamas_incandescentes" in kit
                and self.vida_atual < (self.vida_maxima * 0.45)
                and self.cooldown_escamas == 0
                and not getattr(self, "defendendo", False)
            ):
                escamas = SkillsRegistry.get("escamas_incandescentes")
                if escamas and escamas.pode_usar(self) and random.random() < 0.12:
                    self.cooldown_escamas = 8
                    return escamas

            garra = SkillsRegistry.get("garra_draconica") if "garra_draconica" in kit else None
            asas = SkillsRegistry.get("batida_de_asas") if "batida_de_asas" in kit else None
            opcoes = [a for a in (garra, garra, asas) if a and a.pode_usar(self)]
            if opcoes:
                return random.choice(opcoes)

        disponiveis = [SkillsRegistry.get(h) for h in kit if SkillsRegistry.get(h) and SkillsRegistry.get(h).pode_usar(self)]
        if disponiveis:
            com_custo = [a for a in disponiveis if a.custo_mana > 0]
            if com_custo and random.random() < 0.60:
                return random.choice(com_custo)
            return random.choice(disponiveis)
        return SkillsRegistry.get("garra_draconica") or SkillsRegistry.get("golpe_sombrio") or SkillsRegistry.get("ataque_basico")