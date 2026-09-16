# src/ui/tela_despertar.py
import pygame
import math
import random
from src.utils.colors import (
    PRETO, UI_FUNDO_PADRAO, CINZA_CLARO, UI_TEXTO_APAGADO,
    TXT_SISTEMA_NARRADOR, TXT_ECO_PASSADO, BRANCO,
    AMULETO_COR_FASE_1, AMULETO_COR_FASE_2, AMULETO_COR_FASE_3, AMULETO_COR_FASE_4,
    AMULETO_COR_FASE_5, AMULETO_COR_FASE_6, AMULETO_COR_FASE_7
)
from src.utils.resource_manager import ResourceManager
from src.ui.ui_utils import quebrar_texto_em_linhas

class TelaDespertarMemoria:
    """
    Sequência Cinemática de Despertar de Memória da Halia:
    1. Tela Preta com Fade
    2. Texto: 'Memória Restaurada'
    3. Texto: 'Estágio X/7 — [Nome]'
    4. Impacto abrupto do Amuleto com explosão de partículas etéreas
    5. Amuleto na lateral + Descrição poética + Anseio da personagem ('Procure ainda mais')
    6. Retorno suave ao jogo disparando a expansão do pulso de cor
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
        self.superficie_fundo.fill(PRETO)
        
        # Fontes Oficiais
        self.fonte_grande = pygame.font.Font(None, 48)
        self.fonte_media = pygame.font.Font(None, 34)
        self.fonte_narrativa = pygame.font.Font(None, 24)
        self.fonte_desejo = pygame.font.Font(None, 26)
        self.fonte_rodape = pygame.font.Font(None, 20)
        
        # Passos da Sequência:
        # INATIVO -> FADE_ENTRADA -> TITULO -> SUBTITULO -> IMPACTO_AMULETO -> DETALHES_LATERAL -> FADE_SAIDA
        self.passo = "INATIVO"
        self.alpha_fundo = 0
        self.alpha_elemento = 0
        
        # Dados da Memória Ativa
        self.estagio_antigo = 0
        self.novo_estagio = 1
        self.on_concluido = None
        
        # Efeito de Impacto Abrupto
        self.escala_impacto = 2.4
        self.shake_timer = 0
        self.flash_impacto_alpha = 0
        self.particulas = []
        
        # Posição do amuleto animado (interpolação para a lateral)
        self.amuleto_x = float(self.largura // 2)
        self.amuleto_y = float(self.altura // 2)
        self.amuleto_x_alvo = float(self.largura // 2)
        
        self.tempo_ultimo_input = 0

        # Cache dos sprites grandes do amuleto (200x200)
        self.sprites_amuleto_grande = {
            i: ResourceManager.carregar_imagem(f"hud/Sistema de Memórias - {i}.png", (200, 200))
            for i in range(8)
        }

    @property
    def estado(self):
        """Compatibilidade de leitura para checagem externa de atividade."""
        return "INATIVO" if self.passo == "INATIVO" else "ATIVO"

    def reiniciar(self):
        """Cancela qualquer animação em andamento e retorna ao estado inativo."""
        self.passo = "INATIVO"
        self.alpha_fundo = 0
        self.alpha_elemento = 0
        self.particulas.clear()
        self.on_concluido = None
        self.shake_timer = 0
        self.flash_impacto_alpha = 0

    def iniciar(self, estagio_antigo, novo_estagio, on_concluido=None):
        """Dispara a sequência cinematográfica completa de despertar."""
        self.estagio_antigo = max(0, min(7, int(estagio_antigo)))
        self.novo_estagio = max(1, min(7, int(novo_estagio)))
        self.on_concluido = on_concluido
        
        self.passo = "FADE_ENTRADA"
        self.alpha_fundo = 0
        self.alpha_elemento = 0
        self.particulas.clear()
        
        self.amuleto_x = float(self.largura // 2)
        self.amuleto_y = float(self.altura // 2)
        self.amuleto_x_alvo = float(self.largura // 2)
        self.tempo_ultimo_input = pygame.time.get_ticks()

    def processar_input(self):
        """Avança o estágio da sequência por input (Enter, Espaço ou Clique)."""
        if self.passo in ["INATIVO", "FADE_ENTRADA", "FADE_SAIDA"]:
            return

        tempo_atual = pygame.time.get_ticks()
        if tempo_atual - self.tempo_ultimo_input < 120:
            return
            
        self.tempo_ultimo_input = tempo_atual

        if self.passo == "TITULO":
            self.passo = "SUBTITULO"
            self.alpha_elemento = 0
            
        elif self.passo == "SUBTITULO":
            self.passo = "IMPACTO_AMULETO"
            self._disparar_impacto_abrupto()
            
        elif self.passo == "IMPACTO_AMULETO":
            self.passo = "DETALHES_LATERAL"
            self.amuleto_x_alvo = 320.0
            self.alpha_elemento = 0
            
        elif self.passo == "DETALHES_LATERAL":
            self.passo = "FADE_SAIDA"

    def _disparar_impacto_abrupto(self):
        """Gera o choque repentino/abrupto do selo arcano sendo cravado na tela."""
        self.escala_impacto = 2.5
        self.shake_timer = 12
        self.flash_impacto_alpha = 240
        self.particulas.clear()
        
        cor_estagio = self.CORES_FASES.get(self.novo_estagio, (220, 240, 255))
        cx, cy = self.largura // 2, self.altura // 2
        
        # Explosão radial de partículas etéreas na cor do novo estágio
        for _ in range(40):
            ang = random.uniform(0, math.pi * 2)
            vel = random.uniform(3.5, 9.0)
            self.particulas.append({
                "x": cx,
                "y": cy,
                "vx": math.cos(ang) * vel,
                "vy": math.sin(ang) * vel,
                "vida": random.randint(30, 55),
                "vida_max": 55,
                "raio": random.randint(2, 5),
                "cor": cor_estagio
            })

    def atualizar(self):
        """Atualiza a interpolação suave, física de partículas e transições."""
        if self.passo == "INATIVO":
            return False

        # 1. Fade de Entrada da Tela Preta
        if self.passo == "FADE_ENTRADA":
            self.alpha_fundo = min(255, self.alpha_fundo + 8)
            if self.alpha_fundo >= 255:
                self.alpha_fundo = 255
                self.passo = "TITULO"
                self.alpha_elemento = 0

        # 2. Fade in dos Textos
        elif self.passo in ["TITULO", "SUBTITULO", "DETALHES_LATERAL"]:
            if self.alpha_elemento < 255:
                self.alpha_elemento = min(255, self.alpha_elemento + 14)

        # 3. Impacto Abrupto e Contração do Amuleto
        elif self.passo == "IMPACTO_AMULETO":
            # Contração rápida e enérgica para 1.0
            self.escala_impacto += (1.0 - self.escala_impacto) * 0.22
            if self.flash_impacto_alpha > 0:
                self.flash_impacto_alpha = max(0, self.flash_impacto_alpha - 15)
            if self.shake_timer > 0:
                self.shake_timer -= 1

        # 4. Deslocamento suave do Amuleto para a lateral
        if self.passo == "DETALHES_LATERAL":
            self.amuleto_x += (self.amuleto_x_alvo - self.amuleto_x) * 0.12

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

        # 5. Fade de Saída e Retorno ao Mundo com Pulso de Cor
        if self.passo == "FADE_SAIDA":
            self.alpha_fundo = max(0, self.alpha_fundo - 10)
            if self.alpha_fundo <= 0:
                self.alpha_fundo = 0
                self.passo = "INATIVO"
                if self.on_concluido:
                    self.on_concluido()
                return True # Concluído

        return False

    def desenhar(self, tela):
        """Renderiza cada etapa da sequência narrativa."""
        if self.passo == "INATIVO":
            return

        # 1. Fundo Preto Imersivo
        self.superficie_fundo.set_alpha(self.alpha_fundo)
        tela.blit(self.superficie_fundo, (0, 0))

        cx = self.largura // 2
        cy = self.altura // 2
        cor_estagio = self.CORES_FASES.get(self.novo_estagio, (230, 230, 240))
        dados = self.DADOS_ESTAGIOS.get(self.novo_estagio, {
            "nome": f"Estágio {self.novo_estagio}",
            "descricao": "Uma parte esquecida de sua existência ressurge na mente de Halia.",
            "desejo": "Procure ainda mais..."
        })

        # ETAPA 1: 'Memória Restaurada'
        if self.passo == "TITULO":
            txt = self.fonte_grande.render("Memória Restaurada", True, BRANCO)
            txt.set_alpha(self.alpha_elemento)
            tela.blit(txt, (cx - (txt.get_width() // 2), cy - 25))

        # ETAPA 2: 'Estágio X/7 — [Nome]'
        elif self.passo == "SUBTITULO":
            txt = self.fonte_media.render(f"Estágio {self.novo_estagio}/7 — {dados['nome']}", True, cor_estagio)
            txt.set_alpha(self.alpha_elemento)
            tela.blit(txt, (cx - (txt.get_width() // 2), cy - 18))

        # ETAPA 3 & 4: Impacto do Amuleto e Detalhes Laterais
        elif self.passo in ["IMPACTO_AMULETO", "DETALHES_LATERAL", "FADE_SAIDA"]:
            # Partículas do impacto
            for p in self.particulas:
                alpha_p = max(0, min(255, int((p["vida"] / p["vida_max"]) * 255)))
                surf_p = pygame.Surface((p["raio"] * 2, p["raio"] * 2), pygame.SRCALPHA)
                pygame.draw.circle(surf_p, (*p["cor"], alpha_p), (p["raio"], p["raio"]), p["raio"])
                tela.blit(surf_p, (int(p["x"]) - p["raio"], int(p["y"]) - p["raio"]))

            # Posição com Screen Shake sutil durante o impacto
            offset_shake_x = random.randint(-4, 4) if self.shake_timer > 0 else 0
            offset_shake_y = random.randint(-4, 4) if self.shake_timer > 0 else 0
            
            pos_amu_x = int(self.amuleto_x + offset_shake_x)
            pos_amu_y = int(self.amuleto_y + offset_shake_y)

            # Desenho do Amuleto
            tamanho = int(200 * self.escala_impacto)
            sprite_novo = self.sprites_amuleto_grande.get(self.novo_estagio)
            
            if sprite_novo:
                s_esc = pygame.transform.smoothscale(sprite_novo, (tamanho, tamanho))
                ret = s_esc.get_rect(center=(pos_amu_x, pos_amu_y))
                s_esc.set_alpha(self.alpha_fundo)
                tela.blit(s_esc, ret.topleft)
            else:
                self._desenhar_amuleto_procedural(tela, pos_amu_x, pos_amu_y, self.novo_estagio, tamanho // 2)

            # Clarão do Impacto
            if self.flash_impacto_alpha > 0:
                surf_flash = pygame.Surface((self.largura, self.altura), pygame.SRCALPHA)
                surf_flash.fill((*cor_estagio, int(self.flash_impacto_alpha * 0.4)))
                tela.blit(surf_flash, (0, 0))

            # ETAPA 4: Painel de Descrição e Desejo da Personagem na Lateral
            if self.passo == "DETALHES_LATERAL":
                x_texto = 470
                y_texto = 230
                
                # Título do Estágio
                txt_tit = self.fonte_media.render(f"Estágio {self.novo_estagio}/7 — {dados['nome']}", True, cor_estagio)
                txt_tit.set_alpha(self.alpha_elemento)
                tela.blit(txt_tit, (x_texto, y_texto))

                # Linha divisória sutil
                pygame.draw.line(tela, CINZA_CLARO, (x_texto, y_texto + 42), (x_texto + 620, y_texto + 42), 1)

                # Descrição da Memória
                linhas_desc = quebrar_texto_em_linhas(f'"{dados["descricao"]}"', self.fonte_narrativa, 620)
                for idx, linha in enumerate(linhas_desc):
                    txt_desc = self.fonte_narrativa.render(linha, True, TXT_ECO_PASSADO)
                    txt_desc.set_alpha(self.alpha_elemento)
                    tela.blit(txt_desc, (x_texto, y_texto + 58 + (idx * 28)))

                # Frase de Anseio/Necessidade da Personagem
                y_desejo = y_texto + 68 + (len(linhas_desc) * 28) + 20
                txt_desejo = self.fonte_desejo.render(f'✦ {dados["desejo"]}', True, TXT_SISTEMA_NARRADOR)
                txt_desejo.set_alpha(self.alpha_elemento)
                tela.blit(txt_desejo, (x_texto, y_desejo))

        # Rodapé Sutil de Avanço
        if self.passo in ["TITULO", "SUBTITULO", "IMPACTO_AMULETO", "DETALHES_LATERAL"]:
            msg_rodape = "Pressione [ENTER] ou clique para retornar" if self.passo == "DETALHES_LATERAL" else "Pressione [ENTER] ou clique para prosseguir"
            txt_avancar = self.fonte_rodape.render(msg_rodape, True, UI_TEXTO_APAGADO)
            txt_avancar.set_alpha(self.alpha_fundo)
            tela.blit(txt_avancar, (cx - (txt_avancar.get_width() // 2), self.altura - 45))

    def _desenhar_amuleto_procedural(self, tela, cx, cy, atuais, raio_externo):
        """Fallback geométrico de alta qualidade."""
        raio_interno = int(raio_externo * 0.42)
        max_mem = 7
        
        pygame.draw.circle(tela, UI_FUNDO_PADRAO, (cx, cy), raio_externo)
        pygame.draw.circle(tela, CINZA_CLARO, (cx, cy), raio_externo, 2)
        pygame.draw.circle(tela, CINZA_CLARO, (cx, cy), raio_interno, 2)
        
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
                cor_fatia = self.CORES_FASES.get(i + 1, (200, 200, 200))
                pygame.draw.polygon(tela, cor_fatia, pontos)
            else:
                pygame.draw.polygon(tela, (28, 28, 34), pontos)
            
            pygame.draw.polygon(tela, (12, 12, 16), pontos, 1)
