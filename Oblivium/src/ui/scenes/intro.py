# src/ui/intro.py
import pygame
from src.utils.colors import CARVAO_PROFUNDO, MARFIM_OFFWHITE, CINZA_LINHO, UI_TEXTO_APAGADO
from src.utils.resource_manager import ResourceManager
from src.utils.animations import EfeitoPetalas
from src.ui.ui_utils import quebrar_texto_em_linhas, desenhar_flor_botanica
from src.ui.scenes.texto_editorial import ApresentacaoTextoEditorial
from src.mechanics.cutscenes import CenaBase

class Intro(CenaBase):
    """
    Introdução Narrativa de Oblivium:
    - Estética poética e melancólica com chuva de pétalas do menu em Carvão Profundo
    - Efeito máquina de escrever (typewriter) com cursor editorial orgânico
    - Tipografia 'Just Breathe' com acabamento editorial e flor botânica discreta
    - Interação completa por Teclado (ENTER, ESPAÇO) ou Clique do Mouse para acelerar/avançar
    """
    def __init__(self, largura, altura, game=None):
        super().__init__(game=game, on_concluido=None)
        self.largura = largura
        self.altura = altura
        
        self.textos = [
            "Eu me sinto tão... distante, tão silenciosa por dentro...",
            "Quanto tempo se passou desde a última vez que ouvi vozes familiares ao redor da fogueira?",
            "O mundo perdeu suas cores, seu calor... e até os nomes que eu jurava jamais esquecer.",
            "Mas este silêncio cinzento não é descanso. Há promessas que ainda pulsam sob a névoa.",
            "Preciso caminhar outra vez... e lembrar de cada um deles.",
        ]
        
        self.indice_atual = 0
        self.fonte = ResourceManager.carregar_fonte("just_breathe", 32)
        self.fonte_pular = ResourceManager.carregar_fonte("contrail", 16)
        
        # Efeito de pétalas temático idêntico ao menu principal
        self.efeito_petalas = EfeitoPetalas(self.largura, self.altura, quantidade_petalas=24)
        
        self.alpha = 255.0
        self.estado_efeito = "DIGITANDO" # "DIGITANDO", "HOLD", "FADE_OUT"
        
        # Sistema de máquina de escrever compartilhado pela base editorial
        self.caractere_atual = 0.0
        self.velocidade_digitacao = 0.45 # ~27 caracteres por segundo
        self.velocidade_fade = 5
        self.tempo_hold = 2600
        self.tempo_hold_acumulado = 0.0
        self.tempo_inicio_hold = 0
        self.tempo_inicio_intro = 0
        self.apresentacao = ApresentacaoTextoEditorial(
            game=self.game,
            largura=self.largura,
            altura=self.altura,
            fonte_texto=self.fonte,
            fonte_dica=self.fonte_pular,
            margem_horizontal=240,
            altura_linha=40,
            deslocamento_y=-20,
            velocidade_base=self.velocidade_digitacao,
            mostrar_flor=True,
            pos_y_dica_offset=45,
            dicas=(
                "[ Pressione ENTER / ESPAÇO ou Clique para acelerar ]",
                "[ Pressione ENTER / ESPAÇO ou Clique para prosseguir ]",
            ),
        )
        self._sincronizar_slide_atual()

    def _sincronizar_slide_atual(self):
        if self.indice_atual < len(self.textos):
            self.apresentacao.game = self.game
            self.apresentacao.velocidade_base = self.velocidade_digitacao
            self.apresentacao.definir_conteudo([(self.textos[self.indice_atual], MARFIM_OFFWHITE)])
            self.caractere_atual = 0.0

    def iniciar(self, on_concluido=None):
        self._reiniciar_estado_execucao(on_concluido=on_concluido)
        self.ativo = True
        self.indice_atual = 0
        self.caractere_atual = 0.0
        self.alpha = 255.0
        self.estado_efeito = "DIGITANDO"
        self.tempo_hold_acumulado = 0.0
        self.tempo_inicio_intro = pygame.time.get_ticks()
        self._sincronizar_slide_atual()
        self.efeito_petalas.reiniciar(inicializar_na_tela=True)
        self.efeito_petalas.definir_opacidade_alvo(0.78)
        if self.game and getattr(self.game, "audio", None):
            self.game.audio.tocar_musica(
                "cutscene_intro", loop=-1, fade_ms=900, salvar_anterior=False, contexto="intro"
            )

    def obter_areas_protegidas(self, largura=None, altura=None, margem=28):
        """Calcula retângulos reais da frase inteira, flor e dica de rodapé com margem."""
        w = largura or self.largura
        h = altura or self.altura
        return self.apresentacao.obter_areas_protegidas(w, h, margem=margem)

    def handle_event(self, evento):
        """Processa teclado e clique para avançar ou pular a introdução."""
        if not self.ativo:
            return False
        if evento.type == pygame.KEYDOWN:
            if evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE, pygame.K_e):
                self.avancar()
                return True
            if evento.key == pygame.K_ESCAPE:
                self.pular()
                return True
        elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            self.avancar()
            return True
        return False

    def avancar(self):
        """Avança suavemente: completa a digitação ou passa para a próxima frase."""
        if not self.ativo:
            return
        if self.indice_atual >= len(self.textos):
            self.finalizar()
            return
            
        texto_atual = self.textos[self.indice_atual]
        if self.estado_efeito == "DIGITANDO":
            self.apresentacao.completar_digitacao()
            self.caractere_atual = float(self.apresentacao.total_caracteres)
            self.estado_efeito = "HOLD"
            self.tempo_hold_acumulado = 0.0
            self.tempo_inicio_hold = pygame.time.get_ticks()
        elif self.estado_efeito == "HOLD":
            # Se já terminou de digitar, inicia a transição suave de fade out
            self.estado_efeito = "FADE_OUT"

    def finalizar(self):
        """Encerra a introdução e dispara o callback de conclusão uma única vez."""
        self.indice_atual = len(self.textos)
        return super().finalizar()

    def pular(self):
        """Encerra a introdução por completo preservando o fluxo de conclusão."""
        return self.finalizar()

    def atualizar(self, dt=None):
        if not self.ativo:
            return False

        if dt is None:
            dt = getattr(self.game, "dt", 1.0 / 60.0) if self.game else (1.0 / 60.0)
        if not isinstance(dt, (int, float)) or dt <= 0:
            dt = 1.0 / 60.0
        fator_quadro = dt * 60.0
            
        # Atualiza a chuva de pétalas continuamente com fade suave em leitura
        em_leitura = self.indice_atual < len(self.textos) and self.estado_efeito in ("DIGITANDO", "HOLD")
        self.efeito_petalas.atualizar(dt, alpha_alvo=0.78 if em_leitura else 1.0)
        
        if self.indice_atual >= len(self.textos):
            self.finalizar()
            return False
            
        if self.estado_efeito == "DIGITANDO":
            self.apresentacao.game = self.game
            self.apresentacao.velocidade_base = self.velocidade_digitacao
            terminou = self.apresentacao.atualizar(dt)
            self.caractere_atual = self.apresentacao.caractere_atual
            if terminou or self.apresentacao.esta_completa():
                self.estado_efeito = "HOLD"
                self.tempo_hold_acumulado = 0.0
                self.tempo_inicio_hold = pygame.time.get_ticks()
                
        elif self.estado_efeito == "HOLD":
            self.tempo_hold_acumulado += dt * 1000.0
            tempo_atual = pygame.time.get_ticks()
            # Evita atraso de 1 quadro por deriva de ponto flutuante (ex.: 156 * 1000/60 < 2600.0)
            if (self.tempo_hold_acumulado + 1e-6) >= self.tempo_hold or (tempo_atual - self.tempo_inicio_hold > self.tempo_hold):
                self.estado_efeito = "FADE_OUT"
                
        elif self.estado_efeito == "FADE_OUT":
            self.alpha -= self.velocidade_fade * 1.6 * fator_quadro
            if self.alpha <= 0:
                self.alpha = 255.0
                self.caractere_atual = 0.0
                self.tempo_hold_acumulado = 0.0
                self.estado_efeito = "DIGITANDO"
                self.indice_atual += 1
                if self.indice_atual >= len(self.textos):
                    self.finalizar()
                else:
                    self._sincronizar_slide_atual()
                    
        return self.ativo

    def desenhar(self, tela): 
        em_leitura = self.indice_atual < len(self.textos) and self.estado_efeito in ("DIGITANDO", "HOLD")
        self.apresentacao.desenhar(
            tela,
            efeito_petalas=self.efeito_petalas,
            alpha=self.alpha,
            alpha_petalas=0.78 if em_leitura else 1.0,
            apenas_fundo=(self.indice_atual >= len(self.textos)),
        )
