# src/maps/oakhaven/mapa_vila_destruida.py
import pygame
from src.maps.oakhaven.mapa_vila import MapaOakhaven
from src.maps.oakhaven.terreno_utils import criar_sombra_contato_estrutura
from src.utils.resource_manager import ResourceManager
from src.entities.npc_factory import NPCFactory
from src.entities.elemento_cenario import ChamaIndependente


class MapaOakhavenDestruida(MapaOakhaven):
    """
    Cenário de Oakhaven Destruída / Em Chamas na manhã seguinte, quando Halia acorda
    com o ataque de Ignis'Vahr, o Dragão Vermelho Ancestral, antes de persegui-lo até o Ninho do Dragão.
    Utiliza os assets reais de ruínas, telhados incendiados e monumentos destruídos de assets/cenario/vila.
    """

    def __init__(self, game, largura_tela, altura_tela):
        self.reparos_aplicados = set()
        self._fator_brasa = 1.0
        self.sprites_intactos = {}
        super().__init__(game, largura_tela, altura_tela)
        self.nome = "OAKHAVEN_DESTRUIDA"
        self._brasa_surf_cache = None

    def _obter_superficie_brasa(self):
        """Cache da camada atmosférica de fumaça e brasas sobre a vila atacada."""
        if self._brasa_surf_cache is None:
            surf = pygame.Surface((self.largura_mundo, self.altura_mundo), pygame.SRCALPHA)
            surf.fill((65, 22, 12, 48))
            self._brasa_surf_cache = surf
        return self._brasa_surf_cache

    def carregar_recursos(self):
        super().carregar_recursos()
        p_vila = "assets/cenario/vila"

        self.sprites_intactos = {
            "monumento": self.spr_monumento,
            "fonte": self.spr_fonte,
            "lojas": dict(self.sprites_lojas),
            "casas": dict(self.sprites_casas),
            "barracas": dict(self.sprites_barracas),
            "props": dict(self.sprites_props),
        }

        def _carregar_escala(caminho, escala):
            img = ResourceManager.carregar_imagem(caminho)
            if not img:
                return None
            nw = max(1, int(img.get_width() * escala))
            nh = max(1, int(img.get_height() * escala))
            return ResourceManager.carregar_imagem(caminho, (nw, nh))

        self.spr_entulho_pedras = _carregar_escala("assets/cenario/vegetacao_pedras_separadas/Rocks/Rocks_018.png", 2.0)
        self.spr_banco_quebrado = _carregar_escala(f"{p_vila}/Props/Bancos/banco_madeira_quebrado.png", 0.28)

        # Substitui o Monumento, a Fonte, Casas, Lojas, Barracas e Props pelas versões danificadas/em ruínas
        self.spr_monumento = _carregar_escala(f"{p_vila}/Props/Monumentos/monumento_herois_danificado.png", 0.28) or self.spr_monumento
        self.spr_fonte = _carregar_escala(f"{p_vila}/Props/Fontes/fonte_pedra_danificada.png", 0.32) or self.spr_fonte

        ruina_loja_14 = _carregar_escala(f"{p_vila}/Lojas/Frente/loja_14_ruina_telhado_danificado.png", 0.42)
        ruina_loja_15 = _carregar_escala(f"{p_vila}/Lojas/Frente/loja_15_ruina_incendio_telhado.png", 0.42)
        ruina_loja_16 = _carregar_escala(f"{p_vila}/Lojas/Frente/loja_16_ruina_grande_desabada.png", 0.42)
        ruina_loja_17 = _carregar_escala(f"{p_vila}/Lojas/Frente/loja_17_ruina_chamine_escombros.png", 0.42)

        if ruina_loja_16:
            self.sprites_lojas["taverna_frente"] = ruina_loja_16
        if ruina_loja_14:
            self.sprites_lojas["livraria_frente"] = ruina_loja_14
            self.sprites_lojas["padaria_frente"] = ruina_loja_14
        if ruina_loja_15:
            self.sprites_lojas["magia_frente"] = ruina_loja_15
            self.sprites_lojas["emporio_frente"] = ruina_loja_15
        if ruina_loja_17:
            self.sprites_lojas["floricultura_frente"] = ruina_loja_17
            self.sprites_lojas["carpintaria_frente"] = ruina_loja_17

        ruina_c1_12 = _carregar_escala(f"{p_vila}/Casas/Conjunto_1/Frente/casa_12_ruina_vigas_desabadas.png", 0.42)
        ruina_c1_13 = _carregar_escala(f"{p_vila}/Casas/Conjunto_1/Frente/casa_13_ruina_estrutura_queimada.png", 0.42)
        ruina_c1_14 = _carregar_escala(f"{p_vila}/Casas/Conjunto_1/Frente/casa_14_ruina_chamine_escombros.png", 0.42)
        ruina_c2_12 = _carregar_escala(f"{p_vila}/Casas/Conjunto_2/Frente/casa_12_lateral_destruida.png", 0.42)

        if ruina_c1_12:
            self.sprites_casas["c1_f01"] = ruina_c1_12
            self.sprites_casas["c1_f03"] = ruina_c1_12
        if ruina_c1_13:
            self.sprites_casas["c1_f02"] = ruina_c1_13
            # A Casa de Hóspedes (c1_f05) onde Halia dorme permanece com estrutura em pé para permitir sua saída
            self.sprites_casas["c2_f01_jardim"] = ruina_c1_13
        if ruina_c1_14:
            self.sprites_casas["c1_f07"] = ruina_c1_14
            self.sprites_casas["c2_f04_relogio"] = ruina_c1_14
        if ruina_c2_12:
            self.sprites_casas["c2_f03_hera"] = ruina_c2_12
            self.sprites_casas["c2_f06_dois_andares"] = ruina_c2_12

        ruina_b14 = _carregar_escala(f"{p_vila}/Barracas/Frente/barraca_14_ruina_saqueada.png", 0.34)
        ruina_b15 = _carregar_escala(f"{p_vila}/Barracas/Frente/barraca_15_ruina_queimada.png", 0.34)
        ruina_b16 = _carregar_escala(f"{p_vila}/Barracas/Frente/barraca_16_ruina_pedra_destruida.png", 0.34)
        if ruina_b14:
            self.sprites_barracas["b_hortifruti"] = ruina_b14
        if ruina_b15:
            self.sprites_barracas["b_flores"] = ruina_b15
            self.sprites_barracas["b_ferraria"] = ruina_b15
        if ruina_b16:
            self.sprites_barracas["b_alquimia"] = ruina_b16
            self.sprites_barracas["b_aventureiro"] = ruina_b16

        carroca_dest = _carregar_escala(f"{p_vila}/Props/Cargas_e_Transporte/carroca_destruida.png", 0.30)
        banco_queb = _carregar_escala(f"{p_vila}/Props/Bancos/banco_madeira_quebrado.png", 0.25)
        estandarte_rasg = _carregar_escala(f"{p_vila}/Props/Placas_e_Estandartes/estandarte_rasgado.png", 0.28)
        if carroca_dest:
            self.sprites_props["carroca"] = carroca_dest
        if banco_queb:
            self.sprites_props["banco_madeira"] = banco_queb
        if estandarte_rasg:
            self.sprites_props["estandarte"] = estandarte_rasg

    def inicializar_cenario(self):
        super().inicializar_cenario()
        self.reparos_aplicados = set()
        self._fator_brasa = 1.0
        # Na vila destruída pelas chamas do dragão, a fauna não está presente
        for animal in self.animais:
            animal.visivel = False

        # Escombros removíveis durante a reconstrução em campo (pares visual + colisor por ID)
        add_est = getattr(self, "_add_estrutura_fn", None)
        if callable(add_est):
            sp_ent_forja = self.sprites_props.get("carroca") or getattr(self, "spr_entulho_pedras", None)
            sp_ent_bot = getattr(self, "spr_banco_quebrado", None) or getattr(self, "spr_entulho_pedras", None)
            if sp_ent_forja:
                add_est(
                    sp_ent_forja,
                    1775,
                    612,
                    hitbox_rel=(8, 18, 68, 22),
                    sombra=True,
                    id_estrutura="entulho_forja",
                    categoria="entulho",
                )
            if sp_ent_bot:
                add_est(
                    sp_ent_bot,
                    485,
                    592,
                    hitbox_rel=(6, 14, 48, 18),
                    sombra=True,
                    id_estrutura="entulho_botanica",
                    categoria="entulho",
                )

        # Remove hitboxes dos NPCs anteriores criados no super() (como o Ferreiro em seu local original)
        hitboxes_npcs = [pygame.Rect(int(npc.x), int(npc.y), npc.largura, npc.altura) for npc in self.npcs]
        self.hitboxes = [h for h in self.hitboxes if h not in hitboxes_npcs]

        # Na praça de Oakhaven Destruída, os sobreviventes estão reunidos acolhendo Halia:
        # Ancião Aldous, Curandeira Elara e Guarda Doran (o Ferreiro Torvald permanece fora de cena na forja/escombros)
        self.npcs = [
            NPCFactory.criar(
                "anciao_aldous",
                x=1060,
                y=615,
                dialogo_id="hub_aldous_destruida",
                tem_loja=False,
            ),
            NPCFactory.criar(
                "curandeira_elara",
                x=1110,
                y=615,
                dialogo_id="hub_elara_destruida",
                tem_loja=False,
            ),
            NPCFactory.criar(
                "guarda_doran",
                x=1160,
                y=615,
                dialogo_id="hub_doran_destruida",
                tem_loja=False,
            ),
        ]
        for npc in self.npcs:
            self.hitboxes.append(pygame.Rect(int(npc.x), int(npc.y), npc.largura, npc.altura))

        # Múltiplos focos de incêndio espalhados pelas ruínas de Oakhaven após o ataque do Dragão
        self.focos_fogo = [
            ChamaIndependente(390, 290, tipo="grande", escala=1.1, glow_base=45),
            ChamaIndependente(660, 285, tipo="media", escala=1.0, glow_base=38),
            ChamaIndependente(240, 560, tipo="chao_larga", escala=1.0, glow_base=40),
            ChamaIndependente(650, 565, tipo="media", escala=0.95, glow_base=36),
            ChamaIndependente(1010, 560, tipo="chao_pequena", escala=0.9, glow_base=30),
            ChamaIndependente(1220, 555, tipo="chao_pequena", escala=0.9, glow_base=30),
            ChamaIndependente(1520, 280, tipo="grande", escala=1.05, glow_base=42),
            ChamaIndependente(1760, 285, tipo="chao_larga", escala=1.0, glow_base=38),
            ChamaIndependente(1919, 557, tipo="chao_larga", escala=1.0, glow_base=38),
            ChamaIndependente(1540, 815, tipo="media", escala=0.95, glow_base=35),
            ChamaIndependente(410, 815, tipo="media", escala=0.95, glow_base=35),
            ChamaIndependente(640, 1085, tipo="grande", escala=1.05, glow_base=42),
            ChamaIndependente(1310, 1085, tipo="chao_larga", escala=1.0, glow_base=38),
        ]

    def _obter_estrutura_por_id(self, id_estrutura):
        for est in self.estruturas_ysort:
            if est.get("id") == id_estrutura:
                return est
        return None

    def _restaurar_sprite_por_id(self, id_estrutura, sprite_intacto):
        est = self._obter_estrutura_por_id(id_estrutura)
        if not est or not sprite_intacto:
            return None
        sw, sh = sprite_intacto.get_size()
        est["sprite"] = sprite_intacto
        est["sw"] = sw
        est["sh"] = sh
        est["rect"] = pygame.Rect(int(est["x"]), int(est["y"]), sw, sh)
        if est.get("sombra"):
            est["sombra_surf"], est["sombra_offset"] = criar_sombra_contato_estrutura(
                sprite_intacto, cor=(14, 18, 16, 75)
            )
        if est.get("hitbox_ref") and est["hitbox_ref"] in self.hitboxes and est.get("categoria") in ("casa", "loja"):
            hb = est["hitbox_ref"]
            hb.x = int(est["x"] + sw * 0.08)
            hb.y = int(est["y"] + sh * 0.58)
            hb.width = int(sw * 0.84)
            hb.height = int(sh * 0.36)
        return est

    def _remover_estrutura_por_id(self, id_estrutura):
        alvo = self._obter_estrutura_por_id(id_estrutura)
        if not alvo:
            return False
        hb = alvo.get("hitbox_ref")
        if hb and hb in self.hitboxes:
            self.hitboxes.remove(hb)
        if alvo in self.estruturas_ysort:
            self.estruturas_ysort.remove(alvo)
        return True

    def preparar_cena_reconstrucao(self):
        """Prepara os atores nos bairros sem recriar o cenário com carregar_cenario()."""
        for npc in self.npcs:
            npc.mudar_estado("idle")
        ids_existentes = {getattr(n, "npc_id", "") for n in self.npcs}
        if "ferreiro_torvald" not in ids_existentes:
            torvald = NPCFactory.criar("ferreiro_torvald", x=1635, y=625, dialogo_id=None, tem_loja=False)
            self.npcs.append(torvald)
        self.reposicionar_ator_cena("guarda_doran", 1185, 615)

    def reposicionar_ator_cena(self, npc_id, x, y, virado_direita=None):
        """Move um NPC existente na cena cinematográfica mantendo sua instância e animações."""
        for npc in self.npcs:
            if getattr(npc, "npc_id", "") == npc_id:
                npc.x = float(x)
                npc.y = float(y)
                if hasattr(npc, "sincronizar_teleporte"):
                    npc.sincronizar_teleporte()
                if virado_direita is not None:
                    npc.virado_direita = bool(virado_direita)
                return npc
        return None

    def aplicar_etapa_reconstrucao(self, etapa_id):
        """Aplica reparos visuais e físicos em tempo real por ID estável, de modo idempotente."""
        if etapa_id in self.reparos_aplicados:
            return False

        intactos = self.sprites_intactos or {}
        lojas_i = intactos.get("lojas", {})
        casas_i = intactos.get("casas", {})
        barracas_i = intactos.get("barracas", {})
        props_i = intactos.get("props", {})

        if etapa_id == "forja":
            pares = [
                ("barraca_ferraria", barracas_i.get("b_ferraria")),
                ("barraca_aventureiro", barracas_i.get("b_aventureiro")),
                ("carroca_forja", props_i.get("carroca")),
                ("loja_armeria", lojas_i.get("armeria_frente")),
                ("loja_padaria", lojas_i.get("padaria_frente")),
                ("loja_emporio", lojas_i.get("emporio_frente")),
                ("loja_carpintaria", lojas_i.get("carpintaria_frente")),
                ("casa_c1_f07", casas_i.get("c1_f07")),
                ("casa_c2_f06_dois_andares", casas_i.get("c2_f06_dois_andares")),
            ]
            for sid, sp in pares:
                self._restaurar_sprite_por_id(sid, sp)
            self._remover_estrutura_por_id("entulho_forja")
            self.focos_fogo = [
                f for f in self.focos_fogo
                if f.x < 1350 or (abs(f.x - 1919) < 8 and abs(f.y - 557) < 8)
            ]
            self.reparos_aplicados.add("forja")
            return True

        if etapa_id == "botanica":
            pares = [
                ("loja_magia", lojas_i.get("magia_frente")),
                ("loja_floricultura", lojas_i.get("floricultura_frente")),
                ("loja_taverna", lojas_i.get("taverna_frente")),
                ("loja_livraria", lojas_i.get("livraria_frente")),
                ("barraca_hortifruti", barracas_i.get("b_hortifruti")),
                ("barraca_flores", barracas_i.get("b_flores")),
                ("barraca_alquimia", barracas_i.get("b_alquimia")),
                ("casa_c1_f04", casas_i.get("c1_f04")),
                ("casa_c2_f05_sobrado", casas_i.get("c2_f05_sobrado")),
            ]
            for sid, sp in pares:
                self._restaurar_sprite_por_id(sid, sp)
            self._remover_estrutura_por_id("entulho_botanica")
            self.focos_fogo = [f for f in self.focos_fogo if f.x >= 900]
            self.reparos_aplicados.add("botanica")
            return True

        if etapa_id == "praca":
            pares = [
                ("monumento_praca", intactos.get("monumento")),
                ("fonte_praca", intactos.get("fonte")),
                ("estandarte_norte_esq", props_i.get("estandarte")),
                ("estandarte_norte_dir", props_i.get("estandarte")),
                ("banco_taverna", props_i.get("banco_madeira")),
                ("casa_c1_f03", casas_i.get("c1_f03")),
                ("casa_c2_f03_hera", casas_i.get("c2_f03_hera")),
            ]
            for sid, sp in pares:
                self._restaurar_sprite_por_id(sid, sp)
            # Preserva apenas a chama interior da fornalha de Torvald
            self.focos_fogo = [
                f for f in self.focos_fogo
                if abs(f.x - 1919) < 8 and abs(f.y - 557) < 8
            ]
            self._fator_brasa = 0.0
            for animal in self.animais:
                animal.visivel = True
            self.reparos_aplicados.add("praca")
            return True

        return False

    def desenhar_mundo_ysort(self, tela, entidades_dinamicas=None, area_visivel=None):
        super().desenhar_mundo_ysort(tela, entidades_dinamicas=entidades_dinamicas, area_visivel=area_visivel)
        # Atmosfera de fumaça e brasa sobre a vila atacada pelo Dragão (atenua ao restaurar a praça)
        fator = max(0.0, min(1.0, float(getattr(self, "_fator_brasa", 1.0))))
        if fator > 0.02:
            surf_brasa = self._obter_superficie_brasa()
            surf_brasa.set_alpha(int(255 * fator))
            if area_visivel:
                tela.blit(surf_brasa, area_visivel.topleft, area_visivel)
            else:
                tela.blit(surf_brasa, (0, 0))
