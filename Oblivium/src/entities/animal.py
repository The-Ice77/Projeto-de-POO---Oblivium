# src/entities/animal.py
import pygame
import random
import math
from abc import ABC, abstractmethod
from src.entities.Entity import Entidade
from src.utils.resource_manager import ResourceManager, Animacao


class Animal(Entidade, ABC):
    """
    Classe base abstrata para todos os animais e criaturas da fauna de Oblivium.
    Herda de Entidade, reaproveitando:
    - Posição (x, y), velocidade, ciclo de vida e orientação direcional.
    - Dicionário de animações e máquina de estados.
    
    Adiciona funcionalidades universais da fauna:
    - Ponto de origem/ninho no cenário (x_origem, y_origem).
    - Altitude vertical (elevação Z do solo para saltos ou voo).
    - Renderização de sombra suave, proporcional e sem ruídos visuais.
    - Detecção e reação à proximidade do jogador (Halia).
    """

    def __init__(self, nome, x, y, velocidade=80.0, vida_maxima=10, largura=24, altura=24, direcao_inicial="direita", escala=1.0):
        super().__init__(
            nome=nome,
            vida_maxima=vida_maxima,
            x=x,
            y=y,
            velocidade=velocidade
        )
        self.x_origem = float(x)
        self.y_origem = float(y)
        self.altitude = 0.0  # Altura Z em relação ao plano do chão

        self.largura = largura
        self.altura = altura
        self.virado_direita = (direcao_inicial == "direita")
        self.escala = float(escala)
        self.visivel = True
        self.angulo = 0.0  # Inclinação angular (graus) para alinhamento aerodinâmico à trajetória
        self.offset_y_ondulacao = 0.0  # Micro-flutuação senoidal vertical acompanhando as asas

        # Temporizador e máquina de estados do animal
        self.timer_acao = random.uniform(1.5, 3.5)
        self.raio_alerta = 100.0  # Raio de detecção de aproximação de Halia

        # Parâmetros de renderização da sombra delicada 2.5D
        self.sombra_raio_w = 5
        self.sombra_raio_h = 3
        self.sombra_alpha = 70

    def verificar_proximidade_jogador(self, pos_jogador):
        """Calcula a distância até o jogador e dispara a reação do animal se estiver no raio de alerta."""
        if not pos_jogador or not self.visivel:
            return False
        px, py = pos_jogador
        dist = math.hypot(self.x - px, self.y - py)
        if dist < self.raio_alerta:
            self.reagir_ao_jogador(pos_jogador)
            return True
        return False

    @abstractmethod
    def reagir_ao_jogador(self, pos_jogador):
        """Comportamento específico da espécie ao notar o jogador (fugir voando, correr, etc.)."""
        pass

    @abstractmethod
    def atualizar_comportamento(self, dt):
        """Lógica interna de IA de cada espécie de animal (idle, bicar, pulinho, etc.)."""
        pass

    def atualizar(self, dt=0.016, pos_jogador=None):
        """Método template padrão que orquestra a IA, reação e animação do animal."""
        if not self.visivel:
            self.atualizar_comportamento(dt)
            return

        # Verifica aproximação se o animal estiver em estado receptivo (no solo)
        if self.altitude <= 2.0:
            self.verificar_proximidade_jogador(pos_jogador)

        # Atualiza a física e estados específicos da espécie
        self.atualizar_comportamento(dt)

    def desenhar_sombra(self, tela):
        """
        Desenha uma sombra sutil, elíptica e proporcional diretamente nos pés do animal.
        Fator de altura garante que a sombra encolhe e desvanece suavemente ao subir,
        sem nunca ficar distorcida ou flutuar fora do solo.
        """
        if not self.visivel or self.altitude > 60.0:
            return

        # Conforme sobe, a sombra encolhe suavemente e desaparece
        fator_eleva = max(0.0, 1.0 - (self.altitude / 60.0))
        rw = max(1, int(self.sombra_raio_w * (0.50 + 0.50 * fator_eleva)))
        rh = max(1, int(self.sombra_raio_h * (0.50 + 0.50 * fator_eleva)))
        alpha = int(self.sombra_alpha * (0.40 + 0.60 * fator_eleva))

        if rw >= 1 and rh >= 1 and alpha > 5:
            surf_sombra = pygame.Surface((rw * 2 + 2, rh * 2 + 2), pygame.SRCALPHA)
            pygame.draw.ellipse(surf_sombra, (18, 22, 20, alpha), (1, 1, rw * 2, rh * 2))
            
            # Ancorada exatamente nos pés do animal no solo
            offset_chao = int(6 * getattr(self, 'escala', 1.0))
            pos_sombra_x = int(self.x - rw)
            pos_sombra_y = int(self.y + offset_chao - rh)
            tela.blit(surf_sombra, (pos_sombra_x, pos_sombra_y))

    def desenhar(self, tela):
        """Renderiza a sombra suave no solo e a sprite animada da criatura com rotação de trajetória."""
        if not self.visivel:
            return

        # 1. Sombra projetada no solo
        self.desenhar_sombra(tela)

        # 2. Imagem atual da entidade
        img = self.get_imagem_renderizacao()
        if not img:
            return

        # Aplica espelhamento horizontal conforme a direção em que o animal olha
        if not self.virado_direita:
            img = pygame.transform.flip(img, True, False)

        # Aplica escala caso configurada
        if getattr(self, 'escala', 1.0) != 1.0:
            sw = max(1, int(img.get_width() * self.escala))
            sh = max(1, int(img.get_height() * self.escala))
            img = pygame.transform.scale(img, (sw, sh))

        # Aplica rotação para alinhamento corporal à direção exata de voo
        angulo = getattr(self, 'angulo', 0.0)
        if abs(angulo) > 0.5:
            img = pygame.transform.rotate(img, angulo)

        # Posicionamento com compensação da altitude Z (voo ou salto) e micro-ondulação das asas
        ondulacao = getattr(self, 'offset_y_ondulacao', 0.0)
        pos_x = int(self.x - img.get_width() // 2)
        pos_y = int((self.y - self.altitude + ondulacao) - img.get_height() // 2)

        tela.blit(img, (pos_x, pos_y))

    def get_imagem_renderizacao(self):
        """Retorna o frame atual da animação do estado corrente."""
        anim = self.animacoes.get(self.estado_atual)
        if anim and hasattr(anim, 'get_imagem'):
            return anim.get_imagem()
        return self.imagem_atual


class Passaro(Animal):
    """
    Representa o pássaro silvestre que habita a Estrada de Oblivium.
    Herda de Animal e implementa:
    - Descanso, respiração, bicar sementes e pulinhos orgânicos.
    - Sombra 2.5D que acompanha o solo durante saltos e atenua no ar.
    - Fuga aérea graciosa ao notar Halia (< 105px), subindo em curva batendo asas.
    - Retorno suave ao solo após alguns segundos de voo distante.
    """

    def __init__(self, x, y, direcao_inicial="direita"):
        super().__init__(
            nome="Passarinho",
            x=x,
            y=y,
            velocidade=120.0,
            largura=26,
            altura=26,
            direcao_inicial=direcao_inicial,
            escala=1.35
        )
        self.raio_alerta = 105.0

        # Sombra proporcional ao tamanho do pássaro ligeiramente aumentado
        self.sombra_raio_w = 8
        self.sombra_raio_h = 4
        self.sombra_alpha = 75

        # Física e aerodinâmica de voo orgânico e tranquilo
        self.vx = 0.0
        self.vy = 0.0
        self.vx_alvo = 0.0
        self.taxa_subida_atual = 0.0
        self.taxa_subida_alvo = 25.0
        self.tempo_voo = 0.0
        self.timer_retorno = 0.0
        self.alvo_x = self.x_origem
        self.alvo_y = self.y_origem

        # Carrega os frames canônicos centralizados sem bugs de recorte
        frames_idle = ResourceManager.carregar_frames_pasta("animais/passaro/animacoes/idle")
        frames_pulo = ResourceManager.carregar_frames_pasta("animais/passaro/animacoes/pulo")
        frames_bicar = ResourceManager.carregar_frames_pasta("animais/passaro/animacoes/bicar")
        frames_voo = ResourceManager.carregar_frames_pasta("animais/passaro/animacoes/voo")

        # Configura as animações na estrutura herdada de Entidade com cadência calma e serena
        self.animacoes["idle"] = Animacao(frames_idle, velocidade=0.15, loop=True)
        self.animacoes["pulo"] = Animacao(frames_pulo, velocidade=0.16, loop=False)
        self.animacoes["bicar"] = Animacao(frames_bicar, velocidade=0.18, loop=False)
        self.animacoes["voo"] = Animacao(frames_voo, velocidade=0.15, loop=True)

        self.estado_atual = "idle"

    def reagir_ao_jogador(self, pos_jogador):
        """Ao notar a aproximação de Halia, alça voo sereno e tranquilo batendo asas suavemente."""
        if self.estado_atual in ["idle", "pulo", "bicar"]:
            self.estado_atual = "voo"
            self.tempo_voo = 0.0
            px, py = pos_jogador
            
            # Foge na direção oposta ao jogador (vetor relativo no plano 2.5D)
            dx = self.x - px
            dy = self.y - py
            if abs(dx) < 1.0:
                dx = random.choice([-1.0, 1.0])

            self.virado_direita = (dx > 0)
            
            # Velocidade horizontal tranquila e contemplativa (sem disparar como foguete)
            vel_h = random.uniform(62.0, 78.0)
            self.vx_alvo = (1.0 if self.virado_direita else -1.0) * vel_h
            self.vx = self.vx_alvo * 0.45
            
            # Deslocamento calmo no plano do chão afastando-se suavemente de Halia
            dir_y = 1.0 if dy > 0 else -0.8
            self.vy = random.uniform(-10.0, -3.0) + dir_y * random.uniform(2.0, 5.0)
            
            # Subida suave e graciosa (elevação calma)
            self.taxa_subida_atual = random.uniform(38.0, 48.0)
            self.taxa_subida_alvo = random.uniform(22.0, 28.0)
            self.altitude = 4.0
            self.angulo = 0.0
            self.offset_y_ondulacao = 0.0

            voo_anim = self.animacoes.get("voo")
            if voo_anim:
                voo_anim.velocidade = 0.16  # Batimento calmo e cadenciado
                voo_anim.resetar()

    def atualizar_comportamento(self, dt):
        """Executa a máquina de estados do pássaro com física fluida e batimento orgânico de asas."""
        anim_atual = self.animacoes.get(self.estado_atual)
        if anim_atual:
            anim_atual.atualizar()

        if self.estado_atual in ["idle", "bicar", "pulo"]:
            self.offset_y_ondulacao = 0.0
            self.angulo = 0.0

        if self.estado_atual == "idle":
            self.altitude = 0.0
            self.timer_acao -= dt
            if self.timer_acao <= 0.0:
                self._sortear_acao_solo()

        elif self.estado_atual == "bicar":
            self.altitude = 0.0
            if anim_atual and anim_atual.concluida:
                self.estado_atual = "idle"
                self.timer_acao = random.uniform(1.2, 2.8)
                anim_atual.resetar()

        elif self.estado_atual == "pulo":
            self.x += self.vx * dt
            # Parábola orgânica e fluida de elevação vertical durante o salto no solo
            if anim_atual:
                total_f = max(1, len(anim_atual.frames) - 1)
                prog = min(1.0, max(0.0, anim_atual.frame_atual / total_f))
                self.altitude = math.sin(prog * math.pi) * 11.0
                if anim_atual.concluida:
                    self.altitude = 0.0
                    self.estado_atual = "idle"
                    self.timer_acao = random.uniform(1.6, 3.2)
                    self.vx = 0.0
                    anim_atual.resetar()

        elif self.estado_atual == "voo":
            self.tempo_voo += dt

            # Aceleração serena até a velocidade de cruzeiro tranquila
            self.vx += (self.vx_alvo - self.vx) * min(1.0, 3.0 * dt)
            self.taxa_subida_atual += (self.taxa_subida_alvo - self.taxa_subida_atual) * min(1.0, 2.5 * dt)

            if abs(self.vx) > 0.5:
                self.virado_direita = (self.vx > 0)

            self.x += self.vx * dt
            self.y += self.vy * dt
            self.altitude += self.taxa_subida_atual * dt

            # Sprite permanece com sua pixel art original 100% nítida e sem distorção angular
            self.angulo = 0.0

            # Flutuação vertical orgânica em sincronia exata com o ciclo das asas (fase de sustentação)
            if anim_atual:
                fase_asa = ((anim_atual.frame_atual % 4.0) / 4.0) * 2.0 * math.pi
                self.offset_y_ondulacao = -math.cos(fase_asa) * 1.2
            else:
                self.offset_y_ondulacao = 0.0

            # Só desaparece ao sair fisicamente dos limites da tela
            altura_efetiva = self.y - self.altitude
            if self.x < -80 or self.x > 1360 or altura_efetiva < -80:
                self.visivel = False
                self.timer_retorno = random.uniform(10.0, 18.0)
                self.estado_atual = "fora_da_tela"
                self.angulo = 0.0
                self.offset_y_ondulacao = 0.0

        elif self.estado_atual == "fora_da_tela":
            self.timer_retorno -= dt
            if self.timer_retorno <= 0.0:
                self._iniciar_pouso()

        elif self.estado_atual == "pousando":
            self.tempo_voo += dt
            dx = self.alvo_x - self.x
            dy = self.alvo_y - self.y
            dist = math.hypot(dx, dy)

            # Orienta suavemente na direção do ninho/solo
            if abs(dx) > 3.0:
                self.virado_direita = (dx > 0)

            if dist > 5.0 and self.altitude > 1.5:
                # Aproximação suave e desaceleração progressiva ao chegar perto do solo
                fator_prox = min(1.0, dist / 45.0)
                vel_descida = max(24.0, 56.0 * fator_prox)
                
                passo_x = (dx / dist) * vel_descida * dt
                passo_y = (dy / dist) * vel_descida * dt
                self.x += passo_x
                self.y += passo_y

                taxa_descida = max(12.0, 26.0 * min(1.0, self.altitude / 30.0))
                self.altitude = max(0.0, self.altitude - taxa_descida * dt)
                self.angulo = 0.0

                # Micro-ondulação suave das asas enquanto plana
                if anim_atual:
                    fase_asa = ((anim_atual.frame_atual % 4.0) / 4.0) * 2.0 * math.pi
                    self.offset_y_ondulacao = -math.cos(fase_asa) * 0.8 * min(1.0, self.altitude / 20.0)
            else:
                self.x = self.alvo_x
                self.y = self.alvo_y
                self.altitude = 0.0
                self.angulo = 0.0
                self.offset_y_ondulacao = 0.0
                self.estado_atual = "idle"
                self.timer_acao = random.uniform(2.5, 4.5)
                voo_anim = self.animacoes.get("voo")
                if voo_anim:
                    voo_anim.velocidade = 0.15

    def _sortear_acao_solo(self):
        """Alterna entre olhar para o outro lado, bicar o chão ou dar pulinho curto."""
        r = random.random()
        if r < 0.25:
            self.virado_direita = not self.virado_direita
            self.timer_acao = random.uniform(1.5, 3.0)
        elif r < 0.60:
            self.estado_atual = "bicar"
            bicar_anim = self.animacoes.get("bicar")
            if bicar_anim:
                bicar_anim.resetar()
        else:
            self.estado_atual = "pulo"
            dir_mult = 1.0 if self.virado_direita else -1.0
            
            # Vira de direção se estiver se afastando muito do ninho
            if (self.x + dir_mult * 35.0 - self.x_origem) > 65.0:
                self.virado_direita = False
                dir_mult = -1.0
            elif (self.x + dir_mult * 35.0 - self.x_origem) < -65.0:
                self.virado_direita = True
                dir_mult = 1.0

            self.vx = dir_mult * random.uniform(55.0, 80.0)
            pulo_anim = self.animacoes.get("pulo")
            if pulo_anim:
                pulo_anim.resetar()

    def _iniciar_pouso(self):
        """Prepara o retorno do pássaro para descer no cenário em planeio suave."""
        self.visivel = True
        self.estado_atual = "pousando"
        self.tempo_voo = 0.0
        self.alvo_x = self.x_origem + random.uniform(-35.0, 35.0)
        self.alvo_y = self.y_origem + random.uniform(-10.0, 10.0)
        
        # Nasce suavemente no céu próximo em direção ao ninho
        dist_x = random.uniform(100.0, 140.0)
        sinal = random.choice([-1.0, 1.0])
        self.x = self.alvo_x + (sinal * dist_x)
        self.y = self.alvo_y - 45.0
        self.altitude = 65.0
        self.virado_direita = (self.alvo_x > self.x)
        self.angulo = 0.0
        self.offset_y_ondulacao = 0.0

        voo_anim = self.animacoes.get("voo")
        if voo_anim:
            voo_anim.velocidade = 0.12  # Voo sereno e planado ao descer
            voo_anim.resetar()


class Gato(Animal):
    """
    Representa um felino doméstico/selvagem para compor a fauna (ex: Casa de Halia / Vilarejo).
    Herda de Animal e está pronto para ser instanciado e explorado.
    """

    def __init__(self, x, y, direcao_inicial="direita"):
        super().__init__(
            nome="Gato",
            x=x,
            y=y,
            velocidade=65.0,
            largura=28,
            altura=22,
            direcao_inicial=direcao_inicial
        )
        self.raio_alerta = 85.0
        self.sombra_raio_w = 8
        self.sombra_raio_h = 4
        self.sombra_alpha = 75

        # Carrega ações do gato da pasta de sprites
        frames_idle = ResourceManager.carregar_frames_pasta("animais/gato/acoes_separadas", filtro="gato_acao_01")
        frames_andar = ResourceManager.carregar_frames_pasta("animais/gato/acoes_separadas", filtro="gato_acao_02")
        frames_correr = ResourceManager.carregar_frames_pasta("animais/gato/acoes_separadas", filtro="gato_acao_03")

        self.animacoes["idle"] = Animacao(frames_idle, velocidade=0.15, loop=True)
        self.animacoes["andar"] = Animacao(frames_andar, velocidade=0.20, loop=True)
        self.animacoes["correr"] = Animacao(frames_correr, velocidade=0.28, loop=True)

        self.estado_atual = "idle"

    def reagir_ao_jogador(self, pos_jogador):
        """Ao ver Halia muito próxima, dá alguns passos rápidos para trás e deita ou olha alerta."""
        if self.estado_atual == "idle":
            px, _ = pos_jogador
            self.virado_direita = (px < self.x)
            self.timer_acao = random.uniform(2.0, 4.0)

    def atualizar_comportamento(self, dt):
        anim = self.animacoes.get(self.estado_atual)
        if anim:
            anim.atualizar()

        self.timer_acao -= dt
        if self.timer_acao <= 0.0:
            r = random.random()
            if r < 0.40:
                self.virado_direita = not self.virado_direita
                self.timer_acao = random.uniform(2.0, 4.0)
            elif r < 0.70:
                self.estado_atual = "idle"
                self.timer_acao = random.uniform(3.0, 6.0)
            else:
                self.timer_acao = random.uniform(2.0, 4.0)


# Aliases de conveniência
PassaroAmbiente = Passaro
