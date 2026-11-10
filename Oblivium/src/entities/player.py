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

from src.utils.resource_manager import ResourceManager, Animacao, PASTA_ASSETS



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



        # Dimensões da Hitbox Física 2.5D (base nos pés de Halia)

        self.largura = 36

        self.altura = 36



        # Controle de Nível e Experiência

        self.nivel = 1

        self.xp = 0

        self.xp_proximo_nivel = self.calcular_xp_proximo(self.nivel)



        # Ensinamentos Arcanos Adicionais & Maestria de Feitiços

        self.feiticos_aprendidos = set()

        self.maestria_feiticos = {}



        # Controle de Memórias e Sincronia

        self.fragmentos_memoria = 0

        self.dinheiro = dinheiro

        self.nivel_sincronia = 1



        # Sistema de Inventário & Equipamentos

        self.inventario = Inventario()

        self.inicializar_inventario_padrao()



        # Ações Físicas Disponíveis (Submenu de Ataque Físico)

        self.ataques_fisicos = ["ataque_basico", "golpe_concentrado", "varredura_de_cajado", "estocada_perfurante"]



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



        # Carrega as animações quadridirecionais completas de Halia

        self.carregar_animacoes()



    def carregar_animacoes(self):

        """

        Carrega as animações quadridirecionais de Halia (Frente, Costas, Direita, Esquerda)

        para os estados Idle e Andar, redimensionadas com proporção estética refinada (46x74).

        """

        w_halia, h_halia = 46, 74



        def carregar(caminho_rel):

            return ResourceManager.carregar_imagem(caminho_rel, (w_halia, h_halia))



        # 1. Frente / Baixo (Sul)

        f_idle_baixo = [carregar("halia/frente/Halia_frente_parado.png")]

        f_andar_baixo = [

            carregar("halia/frente/frame_2_direita.png"),

            carregar("halia/frente/Halia_frente_parado.png"),

            carregar("halia/frente/frame_3_passagem.png"),

            carregar("halia/frente/Halia_frente_parado.png"),

        ]



        # 2. Costas / Cima (Norte)

        f_idle_cima = [carregar("halia/costas/Halia_costas_parado.png")]

        f_andar_cima = [

            carregar("halia/costas/Halia_costas_andando.png"),

            carregar("halia/costas/Halia_costas_parado.png"),

            carregar("halia/costas/Halia_151x240.png"),

            carregar("halia/costas/Halia_costas_parado.png"),

        ]



        # 3. Direita (Leste)

        f_idle_direita = [

            carregar("halia/andando_direita/Halia_parado_direita.png"),

            carregar("halia/andando_direita/Halia_parado_direita_02.png"),

        ]

        f_andar_direita = [

            carregar(f"halia/andando_direita/Halia_andando_direita_0{i}.png")

            for i in range(1, 5)

        ]



        # 4. Esquerda (Oeste)

        f_idle_esquerda = [

            carregar("halia/andando_esquerda/Halia_parado_esquerda.png"),

            carregar("halia/andando_esquerda/Halia_parado_esquerda_02.png"),

        ]

        f_andar_esquerda = [

            carregar(f"halia/andando_esquerda/Halia_andando_esquerda_0{i}.png")

            for i in range(1, 5)

        ]



        # Injeta o pacote completo

        self.definir_animacao("idle_baixo", Animacao(f_idle_baixo, velocidade=0.15))

        self.definir_animacao("andar_baixo", Animacao(f_andar_baixo, velocidade=0.15))

        self.definir_animacao("idle_cima", Animacao(f_idle_cima, velocidade=0.15))

        self.definir_animacao("andar_cima", Animacao(f_andar_cima, velocidade=0.15))

        self.definir_animacao("idle_direita", Animacao(f_idle_direita, velocidade=0.04))

        self.definir_animacao("andar_direita", Animacao(f_andar_direita, velocidade=0.15))

        self.definir_animacao("idle_esquerda", Animacao(f_idle_esquerda, velocidade=0.04))

        self.definir_animacao("andar_esquerda", Animacao(f_andar_esquerda, velocidade=0.15))



        # Aliases de compatibilidade total para saves legados e transições

        self.animacoes["idle"] = self.animacoes["idle_baixo"]

        self.animacoes["andar"] = self.animacoes["andar_baixo"]

        self.animacoes["walk"] = self.animacoes["andar_baixo"]

        # --- Novas Sprites Oficiais de Halia (Combate e Ações Especiais) ---
        pasta_novas = os.path.join(PASTA_ASSETS, "halia", "novas_sprites")
        if os.path.exists(pasta_novas):
            for anim_id, sub_dir, vel_a in [
                ("combate_idle", "idle", 0.08),
                ("combate_special", "special", 0.08),
                ("combate_walk", "walk", 0.12),
                ("combate_dialogue", "dialogue", 0.08),
            ]:
                p_sub = os.path.join(pasta_novas, sub_dir)
                if os.path.exists(p_sub):
                    arqs_n = sorted([f for f in os.listdir(p_sub) if f.lower().endswith(".png")])
                    f_novos = []
                    for arq_n in arqs_n:
                        c_rel = os.path.join("halia", "novas_sprites", sub_dir, arq_n).replace("\\", "/")
                        s_img = ResourceManager.carregar_imagem(c_rel)
                        if s_img:
                            f_novos.append(s_img)
                    if f_novos:
                        self.definir_animacao(anim_id, Animacao(f_novos, velocidade=vel_a, loop=True))



        # Define estado inicial voltada para a frente

        self.direcao = "baixo"

        self.virado_direita = True

        self.mudar_estado("idle_baixo")



    def mover(self, dx, dy, hitboxes_mapa=None):

        """Move Halia aplicando cadência dinâmica de passos ao andar vs correr."""

        vel_anim = 0.22 if self.velocidade > 3.5 else 0.15

        for est in ["andar_baixo", "andar_cima", "andar_direita", "andar_esquerda"]:

            if est in self.animacoes:

                self.animacoes[est].velocidade = vel_anim



        super().mover(dx, dy, hitboxes_mapa)



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





    @staticmethod

    def calcular_xp_proximo(nivel):

        """

        Calcula a quantidade necessária de XP para o próximo nível.

        Curva balanceada para progressão D20:

        Nv 1: 50 | Nv 2: 117 | Nv 3: 194 | Nv 4: 280 | Nv 5: 374

        """

        return int(35 * (max(1, nivel) ** 1.32) + 15 * max(1, nivel))



    def ganhar_xp(self, quantidade):

        """

        Concede experiência arcana a Halia.

        Se acumular o total necessário, sobe de nível (podendo subir múltiplos níveis caso ganhe muito XP).

        """

        if quantidade <= 0:

            return []



        self.xp += int(quantidade)

        print(f"[XP] {self.nome} recebeu {quantidade} de XP! ({self.xp}/{self.xp_proximo_nivel})")



        subiu_niveis = []

        while self.xp >= self.xp_proximo_nivel and self.nivel < self.NIVEL_VERDADEIRO:

            self.xp -= self.xp_proximo_nivel

            info_subida = self.subir_nivel()

            subiu_niveis.append(info_subida)

            self.xp_proximo_nivel = self.calcular_xp_proximo(self.nivel)



        if self.nivel >= self.NIVEL_VERDADEIRO:

            self.xp = 0



        return subiu_niveis



    def subir_nivel(self):

        """

        Eleva o nível de Halia em 1 ponto com crescimento justo de atributos D20,

        recalcula limites vitais e restaura totalmente vida e mana.

        """

        self.nivel += 1



        # Crescimento de Atributos D20 Arcano:

        # Foco primário: INT (+1) e SAB (+1) a cada nível

        # Foco secundário: CON (+1 em níveis pares), PRE (+1 em níveis ímpares), DES (+1 a cada 2 níveis), FOR (+1 a cada 3 níveis)

        ganhos = {

            "intelecto": 1,

            "sabedoria": 1,

            "constituicao": 1 if self.nivel % 2 == 0 else 0,

            "presenca": 1 if self.nivel % 2 == 1 else 0,

            "destreza": 1 if self.nivel % 2 == 0 else 0,

            "forca": 1 if self.nivel % 3 == 0 else 0

        }



        for attr, val in ganhos.items():

            if val > 0:

                setattr(self.atributos, attr, getattr(self.atributos, attr) + val)



        # Recalcula derivadas e restaura totalmente

        self.recalcular_status_derivados(manter_porcentagem=False)

        self.restaurar_total()



        print(f"[LEVEL UP] {self.nome} alcançou o Nível {self.nivel}!")

        print(f"Status Atualizados: HP {self.vida_maxima} | MP {self.mana_maxima} | Atributos: {self.atributos}")



        if hasattr(self, 'game') and hasattr(self.game, 'notificacoes') and self.game.notificacoes:
            if hasattr(self.game.notificacoes, 'notificar_level'):
                self.game.notificacoes.notificar_level(self.nivel)
            elif hasattr(self.game.notificacoes, 'notificar'):
                self.game.notificacoes.notificar("notificacao_level", nivel=self.nivel)
            elif hasattr(self.game.notificacoes, 'adicionar'):
                self.game.notificacoes.adicionar(f"Level Up! {self.nome} atingiu o Nível {self.nivel}!")



        return {"nivel": self.nivel, "ganhos": ganhos}



    def aprender_feitico(self, id_magia, bonus_poder=0, reducao_custo=0, xp_bonus=30):

        """

        Estuda um manuscrito ou tomo, assimilando um feitiço permanentemente.

        - Se novo: desperta a magia e registra maestria inicial Nv. 1.

        - Se já conhecido: aprimora o feitiço, ampliando seu poder e reduzindo custo de mana.

        Concede pontos valiosos de Experiência Arcana (XP).

        """

        catalogo = GrimorioHalia.obter_todas_magias()

        info_magia = catalogo.get(id_magia, {})

        nome_magia = info_magia.get("nome", id_magia.replace("_", " ").title())



        if not hasattr(self, 'feiticos_aprendidos'):

            self.feiticos_aprendidos = set()

        if not hasattr(self, 'maestria_feiticos'):

            self.maestria_feiticos = {}



        ja_conhecia = (id_magia in self.magias_desbloqueadas or id_magia in self.feiticos_aprendidos)



        if not ja_conhecia:

            self.feiticos_aprendidos.add(id_magia)

            self.maestria_feiticos[id_magia] = {

                "nivel_maestria": 1,

                "bonus_poder": bonus_poder,

                "reducao_custo": reducao_custo

            }

            self.atualizar_grimorio()

            self.ganhar_xp(xp_bonus)

            msg = f"{self.nome} decifrou as escrituras e dominou o feitiço '{nome_magia}'! (+{xp_bonus} XP)"

            print(f"[Magia] {msg}")

            return True, msg

        else:

            maestria = self.maestria_feiticos.setdefault(id_magia, {

                "nivel_maestria": 1,

                "bonus_poder": 0,

                "reducao_custo": 0

            })

            maestria["nivel_maestria"] += 1

            maestria["bonus_poder"] += bonus_poder

            maestria["reducao_custo"] = min(10, maestria["reducao_custo"] + reducao_custo)



            xp_concedido = max(20, xp_bonus // 2)

            self.ganhar_xp(xp_concedido)

            msg = (f"Maestria Arcana aprimorada! '{nome_magia}' alcançou Nv. {maestria['nivel_maestria']} "

                   f"(Poder +{maestria['bonus_poder']}, Custo -{maestria['reducao_custo']} MP)! (+{xp_concedido} XP)")

            print(f"[Magia] {msg}")

            return True, msg



    def atualizar_grimorio(self):

        """

        Sincroniza as magias conhecidas por Halia unindo:

        1. Feitiços despertados pelas memórias recuperadas.

        2. Feitiços aprendidos permanentemente por tomos e pergaminhos.

        3. Feitiços concedidos por tomos equipados nos 4 slots de Grimório.

        """

        magias = set(GrimorioHalia.obter_magias_desbloqueadas(self.fragmentos_memoria))



        if hasattr(self, 'feiticos_aprendidos') and self.feiticos_aprendidos:

            magias.update(self.feiticos_aprendidos)



        if hasattr(self, 'inventario') and self.inventario:

            for g_slot in ["GRIMORIO_1", "GRIMORIO_2", "GRIMORIO_3", "GRIMORIO_4"]:

                tomo = self.inventario.equipados.get(g_slot)

                if tomo and getattr(tomo, 'magia_id', None):

                    magias.add(tomo.magia_id)



        self.magias_desbloqueadas = sorted(list(magias))



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

        

        # Base de HP e MP escala harmonicamente com Nível de Halia e Memórias

        nivel = getattr(self, 'nivel', 1)

        vida_base_ajustada = 35 + (nivel * 5) + (self.fragmentos_memoria * 8)

        mana_base_ajustada = 15 + (nivel * 5) + (self.fragmentos_memoria * 10)



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



    def entrar_combate(self):

        """Ao entrar em combate, Halia se posiciona voltada para a direita e inicializa flags de combate."""

        self.direcao = "direita"

        self.definir_estado("idle")

        self.em_combate = True

        self.defendendo = False

        self.vulneravel = False

        self.focado = False

        print(f"{self.nome} entrou em combate!")



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



        if getattr(self, 'nivel_sincronia', 1) >= 2:

            if hasattr(self, 'game') and hasattr(self.game, 'conquistas') and self.game.conquistas:

                self.game.conquistas.desbloquear("sincronia_2")



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



        # Checkpoint de Autosave silencioso ao recuperar memória

        if hasattr(self, 'game') and self.game and getattr(self.game, 'slot_atual', None) and hasattr(self.game, 'salvar_estado'):

            self.game.salvar_estado(self.game.slot_atual, tipo="autosave", silenciar_notificacao=True)



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