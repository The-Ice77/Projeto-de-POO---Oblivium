# src/ui/tela_despertar.py
import pygame
import math
import random
from src.utils.colors import (
    PRETO, CARVAO_PROFUNDO, CINZA_ARDOSIA, CINZA_LINHO, CINZA_CLARO, MARFIM_OFFWHITE,
    UI_TEXTO_APAGADO, TXT_SISTEMA_NARRADOR, TXT_ECO_PASSADO, BRANCO,
    AZUL_HOVER_MENU, AZUL_HOVER_BG, DOURADO_ENVELHECIDO,
    AMULETO_COR_FASE_1, AMULETO_COR_FASE_2, AMULETO_COR_FASE_3, AMULETO_COR_FASE_4,
    AMULETO_COR_FASE_5, AMULETO_COR_FASE_6, AMULETO_COR_FASE_7
)
from src.utils.resource_manager import ResourceManager
from src.ui.ui_utils import quebrar_texto_em_linhas, desenhar_flor_botanica

class TelaDespertarMemoria:
    """
    Sequência Cinemática de Despertar de Memória da Halia:
    Progressão Solene e Suave em 5 Etapas:
    1. 'TITULO': 'Memória Restaurada' centralizado com flor botânica e fundo escuro (sem textos adicionais).
    2. 'ESTAGIO': Transição suave para 'Estágio X de 7 — [Nome do Estágio]'.
    3. 'IMPACTO_AMULETO': Amuleto no centro com impacto, screen shake e partículas da cor do estágio.
    4. 'DETALHES_LATERAL': Amuleto desliza à esquerda e tela exibe a narrativa poética, anseio de Halia e novos feitiços.
    5. 'FADE_SAIDA': Fade out suave retornando à exploração do mundo.
    """

    CORES_FASES = {
        1: AMULETO_COR_FASE_1,
        2: AMULETO_COR_FASE_2,
        3: AMULETO_COR_FASE_3,
        4: AMULETO_COR_FASE_4,
        5: AMULETO_COR_FASE_5,
        6: AMULETO_COR_FASE_6,
        7: AMULETO_COR_FASE_7
    }

    FEITICOS_ESTAGIO = {
        2: "Raio Arcano",
        4: "Bola de Fogo e Levitação",
        6: "Tempestade de Éter",
        7: "Totalidade Arcana"
    }

    DADOS_ESTAGIOS = {
        1: {
            "nome": "O Começo",
            "descricao": "Uma primeira fagulha de consciência rompe a névoa. Os contornos da realidade começam a se erguer diante dos olhos de Halia.",
            "desejo": "Procure ainda mais... a mente anseia por lembranças."
        },
        2: {
            "nome": "Ecos da Estrada",
            "descricao": "Lembranças de passos antigos e da quietude esquecida fluem de volta para o coração de Halia.",
            "desejo": "Ainda há muito a desvendar... continue a jornada."
        },
        3: {
            "nome": "A Forma do Mundo",
            "descricao": "A harmonia entre a essência de Halia e o ambiente se recompõe. O peso do ar e da terra ganham sentido e vida.",
            "desejo": "O passado não pode ficar no esquecimento... busque os fragmentos."
        },
        4: {
            "nome": "Despertar Mágico",
            "descricao": "O pulsar primordial do éter volta a queimar em suas veias. Feitiços ancestrais despertam de um longo silêncio.",
            "desejo": "A magia ressoa... os segredos mais profundos aguardam."
        },
        5: {
            "nome": "Além do Véu",
            "descricao": "As barreiras da amnésia dissolvem-se como fumaça ao vento. A verdade aproxima-se com nitidez.",
            "desejo": "Quase tudo está claro... não recue agora."
        },
        6: {
            "nome": "Sincronia Quase Plena",
            "descricao": "A essência ancestral da Grã-Maga ressoa através do tempo e do espaço. Falta apenas o elo final.",
            "desejo": "Resta apenas um passo para a totalidade."
        },
        7: {
            "nome": "A Totalidade Desperta",
            "descricao": "A integridade de suas memórias e o ápice do poder arcanista foram plenamente reconquistados.",
            "desejo": "Sua mente está livre. A Grã-Maga ergue-se novamente."
        }
    }

    def __init__(self, largura=1280, altura=720):
        self.largura = largura
        self.altura = altura
        
        self.superficie_fundo = pygame.Surface((largura, altura))
        self.superficie_fundo.fill(CARVAO_PROFUNDO)
        
        # Fontes Oficiais
        self.fonte_titulo_grande = ResourceManager.carregar_fonte("sunday", 44)
        self.fonte_titulo = ResourceManager.carregar_fonte("sunday", 38)
        self.fonte_estagio_grande = ResourceManager.carregar_fonte("sunday", 34)
        self.fonte_estagio = ResourceManager.carregar_fonte("sunday", 26)
        self.fonte_narrativa = ResourceManager.carregar_fonte("just_breathe", 25)
        self.fonte_desejo = ResourceManager.carregar_fonte("just_breathe", 22)
        self.fonte_feitico = ResourceManager.carregar_fonte("contrail", 18)
        self.fonte_rodape = ResourceManager.carregar_fonte("contrail", 15)
        
        # Passos: INATIVO -> TITULO -> FADE_TITULO_SAIDA -> ESTAGIO -> FADE_ESTAGIO_SAIDA -> IMPACTO_AMULETO -> DETALHES_LATERAL -> FADE_SAIDA
        self.passo = "INATIVO"
        self.alpha_fundo = 0
        self.alpha_conteudo = 0
        self.alpha_texto = 0
        self.tempo_inicio_passo = 0
        self.tempo_ultimo_input = 0
        
        # Dados da Memória Ativa
        self.estagio_antigo = 0
        self.novo_estagio = 1
        self.on_concluido = None
        
        # Animação do Amuleto
        self.escala_amuleto = 2.6
        self.shake_timer = 0
        self.flash_alpha = 0
        self.particulas = []
        
        self.amuleto_x = float(self.largura // 2)
        self.amuleto_y = float(self.altura // 2)
        self.amuleto_x_alvo = 280.0
        
        # Cache dos sprites grandes do amuleto (220x220)
        self.sprites_amuleto_grande = {
            i: ResourceManager.carregar_imagem(f"hud/Sistema de Memórias - {i}.png", (220, 220))
            for i in range(8)
        }

    @property
    def estado(self):
        return "INATIVO" if self.passo == "INATIVO" else "ATIVO"

    def reiniciar(self):
        self.passo = "INATIVO"
        self.alpha_fundo = 0
        self.alpha_conteudo = 0
        self.alpha_texto = 0
        self.particulas.clear()
        self.on_concluido = None
        self.shake_timer = 0
        self.flash_alpha = 0

    def iniciar(self, estagio_antigo, novo_estagio, on_concluido=None):
        """Inicia a sequência de despertar a partir do passo 1: TITULO."""
        self.estagio_antigo = max(0, min(7, int(estagio_antigo)))
        self.novo_estagio = max(1, min(7, int(novo_estagio)))
        self.on_concluido = on_concluido
        
        self.passo = "TITULO"
        self.alpha_fundo = 0
        self.alpha_conteudo = 0
        self.alpha_texto = 0
        self.particulas.clear()
        
        self.amuleto_x = float(self.largura // 2)
        self.amuleto_y = float(self.altura // 2)
        self.amuleto_x_alvo = 280.0
        self.escala_amuleto = 2.6
        self.tempo_inicio_passo = pygame.time.get_ticks()
        self.tempo_ultimo_input = pygame.time.get_ticks()

    def processar_input(self):
        """Avança a sequência com transições suaves."""
        if self.passo in ["INATIVO", "FADE_TITULO_SAIDA", "FADE_ESTAGIO_SAIDA", "FADE_SAIDA"]:
            return

        agora = pygame.time.get_ticks()
        if agora - self.tempo_ultimo_input < 280:
            return
        self.tempo_ultimo_input = agora

        if self.passo == "TITULO":
            self.passo = "FADE_TITULO_SAIDA"
        elif self.passo == "ESTAGIO":
            self.passo = "FADE_ESTAGIO_SAIDA"
        elif self.passo == "IMPACTO_AMULETO":
            if agora - self.tempo_inicio_passo >= 350:
                self.passo = "DETALHES_LATERAL"
                self.tempo_inicio_passo = agora
                self.alpha_texto = 0
        elif self.passo == "DETALHES_LATERAL":
            if agora - self.tempo_inicio_passo >= 350:
                self.passo = "FADE_SAIDA"
                self.tempo_inicio_passo = agora

    def _disparar_impacto(self):
        self.escala_amuleto = 2.5
        self.shake_timer = 15
        self.flash_alpha = 230
        self.particulas.clear()
        
        cor_estagio = self.CORES_FASES.get(self.novo_estagio, (220, 240, 255))
        cx, cy = self.largura // 2, self.altura // 2
        
        for _ in range(55):
            ang = random.uniform(0, math.pi * 2)
            vel = random.uniform(3.0, 10.0)
            self.particulas.append({
                "x": cx,
                "y": cy,
                "vx": math.cos(ang) * vel,
                "vy": math.sin(ang) * vel,
                "vida": random.randint(35, 65),
                "vida_max": 65,
                "raio": random.randint(2, 5),
                "cor": cor_estagio
            })

    def atualizar(self):
        if self.passo == "INATIVO":
            return False

        agora = pygame.time.get_ticks()
        tempo_passo = agora - self.tempo_inicio_passo

        # 1. Passo: TITULO (Entrada suave)
        if self.passo == "TITULO":
            self.alpha_fundo = min(255, self.alpha_fundo + 8)
            self.alpha_conteudo = min(255, self.alpha_conteudo + 10)

        # Transição Suave: Fade out do Título para o Estágio
        elif self.passo == "FADE_TITULO_SAIDA":
            self.alpha_conteudo = max(0, self.alpha_conteudo - 14)
            if self.alpha_conteudo <= 0:
                self.passo = "ESTAGIO"
                self.tempo_inicio_passo = agora

        # 2. Passo: ESTAGIO (Entrada suave)
        elif self.passo == "ESTAGIO":
            self.alpha_fundo = 255
            self.alpha_conteudo = min(255, self.alpha_conteudo + 12)

        # Transição Suave: Fade out do Estágio para o Impacto do Amuleto
        elif self.passo == "FADE_ESTAGIO_SAIDA":
            self.alpha_conteudo = max(0, self.alpha_conteudo - 16)
            if self.alpha_conteudo <= 0:
                self.passo = "IMPACTO_AMULETO"
                self.tempo_inicio_passo = agora
                self._disparar_impacto()

        # 3. Passo: IMPACTO_AMULETO
        elif self.passo == "IMPACTO_AMULETO":
            self.alpha_fundo = 255
            self.escala_amuleto += (1.0 - self.escala_amuleto) * 0.16
            if self.flash_alpha > 0:
                self.flash_alpha = max(0, self.flash_alpha - 12)
            if self.shake_timer > 0:
                self.shake_timer -= 1
                
            # Transição automática para os detalhes após a animação do impacto
            if tempo_passo > 1300:
                self.passo = "DETALHES_LATERAL"
                self.tempo_inicio_passo = agora
                self.alpha_texto = 0

        # 4. Passo: DETALHES_LATERAL
        elif self.passo == "DETALHES_LATERAL":
            self.amuleto_x += (self.amuleto_x_alvo - self.amuleto_x) * 0.10
            if self.alpha_texto < 255:
                self.alpha_texto = min(255, self.alpha_texto + 10)

        # Atualiza partículas ativas
        vivas = []
        for p in self.particulas:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["vx"] *= 0.94
            p["vy"] *= 0.94
            p["vida"] -= 1
            if p["vida"] > 0:
                vivas.append(p)
        self.particulas = vivas

        # 5. Passo: FADE_SAIDA
        if self.passo == "FADE_SAIDA":
            self.alpha_fundo = max(0, self.alpha_fundo - 10)
            self.alpha_texto = max(0, self.alpha_texto - 12)
            if self.alpha_fundo <= 0:
                self.alpha_fundo = 0
                self.passo = "INATIVO"
                if self.on_concluido:
                    self.on_concluido()
                return True

        return False

    def desenhar(self, tela):
        if self.passo == "INATIVO":
            return

        # Fundo Carvão Profundo
        self.superficie_fundo.set_alpha(self.alpha_fundo)
        tela.blit(self.superficie_fundo, (0, 0))

        cx = self.largura // 2
        cy = self.altura // 2
        cor_estagio = self.CORES_FASES.get(self.novo_estagio, MARFIM_OFFWHITE)
        dados = self.DADOS_ESTAGIOS.get(self.novo_estagio, {
            "nome": f"Estágio {self.novo_estagio}",
            "descricao": "Uma parte esquecida de sua existência ressurge na mente de Halia.",
            "desejo": "Procure ainda mais..."
        })

        # --- ETAPA 1: TELA DE MEMÓRIA RESTAURADA ---
        if self.passo in ["TITULO", "FADE_TITULO_SAIDA"]:
            desenhar_flor_botanica(tela, cx, cy - 35, cor=CINZA_LINHO, escala=1.0)
            
            r_tit = self.fonte_titulo_grande.render("✦ MEMÓRIA RESTAURADA ✦", True, MARFIM_OFFWHITE)
            r_tit.set_alpha(int(self.alpha_conteudo))
            tela.blit(r_tit, r_tit.get_rect(center=(cx, cy + 30)))
            
            r_rod = self.fonte_rodape.render("[ Pressione ENTER ou CLIQUE para continuar ]", True, UI_TEXTO_APAGADO)
            r_rod.set_alpha(int(self.alpha_conteudo))
            tela.blit(r_rod, r_rod.get_rect(center=(cx, self.altura - 45)))
            return

        # --- ETAPA 2: TELA DO ESTÁGIO ---
        if self.passo in ["ESTAGIO", "FADE_ESTAGIO_SAIDA"]:
            desenhar_flor_botanica(tela, cx, cy - 75, cor=CINZA_LINHO, escala=0.85)
            
            r_rot = self.fonte_estagio.render(f"Estágio {self.novo_estagio} de 7", True, CINZA_LINHO)
            r_rot.set_alpha(int(self.alpha_conteudo))
            tela.blit(r_rot, r_rot.get_rect(center=(cx, cy - 10)))
            
            r_nome = self.fonte_titulo_grande.render(f"✦ {dados['nome']} ✦", True, cor_estagio)
            r_nome.set_alpha(int(self.alpha_conteudo))
            tela.blit(r_nome, r_nome.get_rect(center=(cx, cy + 35)))
            
            r_rod = self.fonte_rodape.render("[ Pressione ENTER ou CLIQUE para continuar ]", True, UI_TEXTO_APAGADO)
            r_rod.set_alpha(int(self.alpha_conteudo))
            tela.blit(r_rod, r_rod.get_rect(center=(cx, self.altura - 45)))
            return

        # --- ETAPA 3, 4, 5: IMPACTO, DETALHES LATERAIS E SAÍDA ---
        # Partículas do impacto
        for p in self.particulas:
            alpha_p = max(0, min(255, int((p["vida"] / p["vida_max"]) * 255)))
            surf_p = pygame.Surface((p["raio"] * 2, p["raio"] * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf_p, (*p["cor"], alpha_p), (p["raio"], p["raio"]), p["raio"])
            tela.blit(surf_p, (int(p["x"]) - p["raio"], int(p["y"]) - p["raio"]))

        # Posição com Screen Shake durante o impacto
        offset_shake_x = random.randint(-4, 4) if self.shake_timer > 0 else 0
        offset_shake_y = random.randint(-4, 4) if self.shake_timer > 0 else 0
        
        pos_amu_x = int(self.amuleto_x + offset_shake_x)
        pos_amu_y = int(self.amuleto_y + offset_shake_y)

        # Desenho do Amuleto
        tamanho = int(220 * max(0.9, min(2.6, self.escala_amuleto)))
        sprite_novo = self.sprites_amuleto_grande.get(self.novo_estagio)
        
        if sprite_novo:
            s_esc = pygame.transform.smoothscale(sprite_novo, (tamanho, tamanho))
            ret = s_esc.get_rect(center=(pos_amu_x, pos_amu_y))
            s_esc.set_alpha(self.alpha_fundo)
            tela.blit(s_esc, ret.topleft)
        else:
            self._desenhar_amuleto_procedural(tela, pos_amu_x, pos_amu_y, self.novo_estagio, tamanho // 2)

        # Clarão do Impacto
        if self.flash_alpha > 0:
            surf_flash = pygame.Surface((self.largura, self.altura), pygame.SRCALPHA)
            surf_flash.fill((*cor_estagio, int(self.flash_alpha * 0.35)))
            tela.blit(surf_flash, (0, 0))

        # ETAPA 4 e 5: Detalhes da Memória (Sem caixa pesada ao redor, apenas texto editorial organizado)
        if self.passo in ["DETALHES_LATERAL", "FADE_SAIDA"]:
            x_texto = 480
            y_cur = 155
            largura_texto = self.largura - x_texto - 80

            # 1. Título Superior
            r_tit = self.fonte_titulo.render("✦ Memória Restaurada ✦", True, MARFIM_OFFWHITE)
            r_tit.set_alpha(self.alpha_texto)
            tela.blit(r_tit, (x_texto, y_cur))
            y_cur += 48

            # 2. Subtítulo: Estágio X de 7 — [Nome]
            r_est = self.fonte_estagio_grande.render(f"Estágio {self.novo_estagio} de 7 — {dados['nome']}", True, cor_estagio)
            r_est.set_alpha(self.alpha_texto)
            tela.blit(r_est, (x_texto, y_cur))
            y_cur += 44

            # Divisória fina e elegante
            if self.alpha_texto > 0:
                surf_div = pygame.Surface((largura_texto, 1), pygame.SRCALPHA)
                surf_div.fill((*CINZA_ARDOSIA, int(self.alpha_texto * 0.7)))
                tela.blit(surf_div, (x_texto, y_cur))
            y_cur += 24

            # 3. Descrição Poética da Memória
            linhas_desc = quebrar_texto_em_linhas(f'"{dados["descricao"]}"', self.fonte_narrativa, largura_texto)
            for linha in linhas_desc:
                r_desc = self.fonte_narrativa.render(linha, True, MARFIM_OFFWHITE)
                r_desc.set_alpha(self.alpha_texto)
                tela.blit(r_desc, (x_texto, y_cur))
                y_cur += 32

            # 4. Anseio / Necessidade de Halia
            y_cur += 16
            r_desejo = self.fonte_desejo.render(f'✦ {dados["desejo"]}', True, (245, 215, 140))
            r_desejo.set_alpha(self.alpha_texto)
            tela.blit(r_desejo, (x_texto, y_cur))
            y_cur += 42

            # 5. Feitiço Despertado (se houver)
            feitico_despertado = self.FEITICOS_ESTAGIO.get(self.novo_estagio)
            if feitico_despertado:
                rect_feit = pygame.Rect(x_texto, y_cur, largura_texto, 40)
                pygame.draw.rect(tela, (20, 28, 38), rect_feit, border_radius=3)
                pygame.draw.rect(tela, AZUL_HOVER_MENU, rect_feit, 1, border_radius=3)
                r_feit = self.fonte_feitico.render(f"⚡ Novo Feitiço Despertado: {feitico_despertado}", True, AZUL_HOVER_MENU)
                r_feit.set_alpha(self.alpha_texto)
                tela.blit(r_feit, (rect_feit.x + 16, rect_feit.centery - r_feit.get_height() // 2))

            # 6. Rodapé Informativo para Avançar
            tempo_tick = pygame.time.get_ticks()
            offset_y = int(math.sin(tempo_tick * 0.006) * 2)
            cor_aviso = AZUL_HOVER_MENU
            txt_avancar = self.fonte_rodape.render("[ Pressione ENTER ou CLIQUE para retornar ]", True, cor_aviso)
            tela.blit(txt_avancar, (x_texto + (largura_texto - txt_avancar.get_width()) // 2, self.altura - 48 + offset_y))

    def _desenhar_amuleto_procedural(self, tela, cx, cy, atuais, raio_externo):
        """Fallback geométrico de alta qualidade."""
        raio_interno = int(raio_externo * 0.42)
        max_mem = 7
        
        pygame.draw.circle(tela, CARVAO_PROFUNDO, (cx, cy), raio_externo)
        pygame.draw.circle(tela, CINZA_LINHO, (cx, cy), raio_externo, 1)
        pygame.draw.circle(tela, CINZA_LINHO, (cx, cy), raio_interno, 1)
        
        angulo_fatia = 360 / max_mem
        
        for i in range(max_mem):
            ang_inicial = math.radians(i * angulo_fatia - 90)
            ang_final = math.radians((i + 1) * angulo_fatia - 90)
            
            pontos = []
            for p in range(5):
                a = ang_inicial + (ang_final - ang_inicial) * (p / 4.0)
                pontos.append((cx + (raio_externo - 6) * math.cos(a), cy + (raio_externo - 6) * math.sin(a)))
            for p in range(4, -1, -1):
                a = ang_inicial + (ang_final - ang_inicial) * (p / 4.0)
                pontos.append((cx + (raio_interno + 6) * math.cos(a), cy + (raio_interno + 6) * math.sin(a)))
            
            if i < atuais:
                cor_fatia = self.CORES_FASES.get(i + 1, MARFIM_OFFWHITE)
                pygame.draw.polygon(tela, cor_fatia, pontos)
            else:
                pygame.draw.polygon(tela, (28, 28, 34), pontos)
            
            pygame.draw.polygon(tela, (12, 12, 16), pontos, 1)
