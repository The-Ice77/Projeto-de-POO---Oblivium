# src/ui/flashback.py
import math
import random
import pygame
from src.utils.colors import (
    PRETO, TXT_ECO_PASSADO, TXT_PENSAMENTO_FANTASMA, 
    TXT_SISTEMA_NARRADOR, UI_TEXTO_APAGADO
)
from src.utils.resource_manager import ResourceManager
from src.utils.animations import EfeitoPetalas
from src.maps.mapa_flashback import MapaFlashbackAcampamento
from src.mechanics.cena_base import CenaBase


class Flashback(CenaBase):
    """
    Sistema de Memórias e Flashbacks de Halia (Oblivium):
    
    Dois modos imersivos integrados à arquitetura canônica do projeto:
    1. 'acampamento': Cena visual viva renderizada no mapa real (MapaFlashbackAcampamento)
       com fogueira acesa animada, props autênticos de estrada/floresta, árvores ancestrais,
       estrelas na abóbada celeste e os quatro heróis ao redor do fogo.
       Os diálogos são delegados 100% à DialogueBox oficial do jogo (src/ui/dialogue_box.py),
       com retratos, tipografia canônica, máquina de escrever e efeitos sonoros.
    2. 'texto': Escuridão solene e poética com digitação typewriter e pétalas flutuantes,
       utilizado para ecos ancestrais da ruína.
    """

    def __init__(self, largura, altura, game=None):
        self.estado = "INATIVO"  # INATIVO, ESCURECENDO, ESCURIDAO, CLAREANDO
        super().__init__(game=game, on_concluido=None)
        self.largura = largura
        self.altura = altura
        self.superficie_preta = pygame.Surface((largura, altura))
        self.superficie_preta.fill(PRETO)
        
        # Cenário real de acampamento em CenarioBase
        self.mapa_acampamento = MapaFlashbackAcampamento(
            game=game, largura_tela=largura, altura_tela=altura
        )

        # Fontes do modo texto introspectivo
        self.fonte_flashback = ResourceManager.carregar_fonte("just_breathe", 36)
        self.fonte_avanco = ResourceManager.carregar_fonte("contrail", 18)

        self.alpha = 0.0
        self.velocidade = 5 
        self.tipo = "texto"  # "texto" ou "acampamento"
        self.tempo_cena = 0.0
        self.dialogo_iniciado = False
        self._consequencias_aplicadas = False
        
        # Pétalas de memória em segundo plano
        self.efeito_petalas = EfeitoPetalas(
            largura, altura, 
            quantidade_petalas=22, 
            alpha=(100, 180),
            escala=(0.55, 0.85)
        )
        
        # Máquina de escrever para o modo texto
        self.texto_alpha = 255
        self.texto_estado = "DIGITANDO"
        self.velocidade_texto = 5     
        self.caractere_atual = 0.0
        self.velocidade_digitacao = 0.50
        
        self.textos = []
        self.indice_texto = 0
        self.tempo_ultimo_input = 0

    @property
    def ativo(self):
        return self.estado != "INATIVO"

    @ativo.setter
    def ativo(self, valor):
        if not valor:
            self.estado = "INATIVO"
        elif self.estado == "INATIVO":
            self.estado = "ESCURECENDO"

    # =========================================================================
    # Ciclo de Vida do Flashback
    # =========================================================================
    def iniciar(self, textos_memorias=None, tipo=None, game=None, on_concluido=None):
        if game is not None:
            self.game = game
            self.mapa_acampamento.game = game

        self._reiniciar_estado_execucao(on_concluido=on_concluido)
        self._consequencias_aplicadas = False
        self.textos = textos_memorias or []
        self.indice_texto = 0
        self.estado = "ESCURECENDO"
        self.alpha = 0.0
        self.tempo_cena = 0.0
        self.dialogo_iniciado = False

        # Auto-detecção inteligente do tipo de flashback se não especificado
        if tipo is not None:
            self.tipo = tipo
        else:
            tem_amigos = False
            for t in self.textos:
                conteudo = f"{t.get('autor', '')} {t.get('texto', '')}".lower()
                if any(w in conteudo for w in ["sylvan", "roland", "caelen", "amigo", "forja", "escudo"]):
                    tem_amigos = True
                    break
            self.tipo = "acampamento" if tem_amigos else "texto"
        
        # Reseta os controles de texto
        self.texto_alpha = 255
        self.texto_estado = "DIGITANDO"
        self.caractere_atual = 0.0
        self.tempo_ultimo_input = pygame.time.get_ticks()
        self.efeito_petalas.reiniciar(inicializar_na_tela=True)

    def handle_event(self, evento):
        """Processa entradas de teclado ou mouse quando o flashback está ativo."""
        if not self.ativo:
            return False
        if evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_ESCAPE:
                self.pular()
                return True
            if evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE, pygame.K_e):
                if self.estado == "ESCURIDAO":
                    self.processar_input()
                    return True
        elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            if self.estado == "ESCURIDAO":
                self.processar_input()
                return True
        return False

    def _aplicar_consequencias_narrativas(self):
        """Aplica os desbloqueios narrativos pós-flashback uma única vez por ciclo."""
        if self._consequencias_aplicadas or not self.game:
            return
        self._consequencias_aplicadas = True

        if getattr(self.game, "flashback_monumento_ativo", False):
            self.game.flashback_monumento_ativo = False
            if hasattr(self.game, "caixa_dialogo") and self.game.caixa_dialogo:
                self.game.caixa_dialogo.iniciar_dialogo([
                    {
                        "autor": "Narrador",
                        "texto": "O calor daquela fogueira distante ainda ecoa no peito de Halia. As risadas francas de Sylvan, a vigília calma de Roland e o chá de ervas de Caelen... Ela não está sozinha nesta batalha."
                    }
                ])
        elif getattr(self.game, "flashback_sylvan_ativo", False):
            self.game.flashback_sylvan_ativo = False
            if hasattr(self.game, "halia") and self.game.halia and self.game.halia.fragmentos_memoria < 2:
                self.game.halia.recuperar_memoria(1)
            if hasattr(self.game, "mapa_casa") and self.game.mapa_casa:
                self.game.mapa_casa.carregar_cenario("NINHO_DRAGAO")
                ninho = getattr(self.game.mapa_casa, "cenario_objeto", None)
                if ninho:
                    ninho.ninho_amanhecer = True
                    ninho.dragao_derrotado = True
                    if hasattr(ninho, "inicializar_cenario"):
                        ninho.inicializar_cenario()
            if hasattr(self.game, "halia") and self.game.halia:
                self.game.halia.x, self.game.halia.y = 610, 380
                self.game.halia.direcao = "cima"
                self.game.halia.mudar_estado("idle")
            if getattr(self.game, "slot_atual", None) and hasattr(self.game, "salvar_estado"):
                self.game.salvar_estado(self.game.slot_atual, tipo="autosave")
            if hasattr(self.game, "caixa_dialogo") and self.game.caixa_dialogo:
                self.game.caixa_dialogo.iniciar_dialogo([
                    {
                        "autor": "Narrador",
                        "texto": "O riso caloroso de Sylvan ainda ecoa como uma brasa acolhedora na memória de Halia. A força daquela amizade antiga dissipa suas dores. O dragão colossal jaz inerte sob a luz límpida da aurora. É hora de descer pela trilha sul e levar as boas notícias ao povo de Oakhaven."
                    }
                ])
        else:
            if hasattr(self.game, "flashback_magia_concluido"):
                self.game.flashback_magia_concluido = True
            if hasattr(self.game, "conquistas") and self.game.conquistas:
                self.game.conquistas.desbloquear("eco_passado")
            if getattr(self.game, "slot_atual", None) and hasattr(self.game, "salvar_estado"):
                self.game.salvar_estado(self.game.slot_atual, tipo="autosave")
            if hasattr(self.game, "caixa_dialogo") and self.game.caixa_dialogo:
                self.game.caixa_dialogo.iniciar_dialogo("escolha_magias")

    def finalizar(self):
        """Encerra o flashback garantindo estado limpo, narrativa e callback único."""
        if self.tipo == "acampamento" and self.game and hasattr(self.game, "caixa_dialogo") and self.game.caixa_dialogo:
            if self.game.caixa_dialogo.ativo:
                self.game.caixa_dialogo.ativo = False
                if hasattr(self.game.caixa_dialogo, "em_escolha"):
                    self.game.caixa_dialogo.em_escolha = False

        self.alpha = 0.0
        self.estado = "INATIVO"
        self.dialogo_iniciado = False
        self.concluido = True
        self._aplicar_consequencias_narrativas()
        return self._executar_callback_conclusao()

    def pular(self):
        """Pula o flashback preservando todas as consequências narrativas de conclusão."""
        return self.finalizar()

    def _obter_texto_formatado_atual(self):
        """Retorna o texto da memória atual para o modo texto introspectivo."""
        if not self.textos or self.indice_texto >= len(self.textos):
            return "", TXT_SISTEMA_NARRADOR
            
        dados_texto = self.textos[self.indice_texto]
        autor = dados_texto.get("autor", "")
        frase = dados_texto.get("texto", "")
        
        if autor == "Eco do Passado":
            texto_final = f'"{frase}"'
            cor_texto = TXT_ECO_PASSADO
        elif autor == "Pensamento":
            texto_final = f"({frase})"
            cor_texto = TXT_PENSAMENTO_FANTASMA
        else:
            texto_final = frase
            cor_texto = TXT_SISTEMA_NARRADOR
            
        return texto_final, cor_texto

    def processar_input(self, forcar=False):
        """Gerencia o avanço exclusivo do modo texto puro (modo acampamento é gerido pela DialogueBox)."""
        if self.tipo == "acampamento":
            # No modo acampamento, todo o input é conduzido diretamente pela DialogueBox oficial!
            if self.game and hasattr(self.game, 'caixa_dialogo') and self.game.caixa_dialogo.ativo:
                self.game.caixa_dialogo.proximo_texto()
            return

        if self.estado != "ESCURIDAO": 
            return

        tempo_atual = pygame.time.get_ticks()
        if not forcar and self.texto_estado == "WAIT" and tempo_atual - self.tempo_ultimo_input < 140: 
            return
        self.tempo_ultimo_input = tempo_atual

        texto_final, _ = self._obter_texto_formatado_atual()
        
        if self.texto_estado == "DIGITANDO":
            self.caractere_atual = float(len(texto_final))
            self.texto_estado = "WAIT"
        elif self.texto_estado == "WAIT":
            self.texto_estado = "FADE_OUT"

    def atualizar(self, dt=None):
        if self.estado == "INATIVO":
            return False

        if dt is None:
            dt = getattr(self.game, "dt", 1.0 / 60.0) if self.game else (1.0 / 60.0)
        if not isinstance(dt, (int, float)) or dt <= 0:
            dt = 1.0 / 60.0

        self.tempo_cena += dt

        # Atualiza a chuva sutil de pétalas
        self.efeito_petalas.atualizar(dt)

        # Atualiza animações físicas e visuais do acampamento
        if self.tipo == "acampamento":
            self.mapa_acampamento.atualizar(dt)

        # Transição de entrada (fade in)
        if self.estado == "ESCURECENDO":
            self.alpha += self.velocidade * 35.0 * dt
            if self.alpha >= 255:
                self.alpha = 255.0
                self.estado = "ESCURIDAO"
                
                # Se for acampamento, aciona a DialogueBox oficial imediatamente com a lista de falas!
                if self.tipo == "acampamento":
                    if self.game and hasattr(self.game, 'caixa_dialogo') and self.textos and not self.dialogo_iniciado:
                        self.dialogo_iniciado = True
                        self.game.caixa_dialogo.iniciar_dialogo(self.textos)
                else:
                    self.texto_alpha = 255.0
                    self.texto_estado = "DIGITANDO"
                    self.caractere_atual = 0.0

        elif self.estado == "ESCURIDAO":
            if self.tipo == "acampamento":
                # Monitora a conclusão do diálogo na DialogueBox oficial
                if self.dialogo_iniciado:
                    if self.game and hasattr(self.game, 'caixa_dialogo'):
                        if not self.game.caixa_dialogo.ativo:
                            # A conversa dos amigos foi concluída na caixa oficial! Inicia o fade out!
                            self.estado = "CLAREANDO"
                else:
                    if self.game and hasattr(self.game, 'caixa_dialogo') and self.textos:
                        self.dialogo_iniciado = True
                        self.game.caixa_dialogo.iniciar_dialogo(self.textos)
                    else:
                        self.estado = "CLAREANDO"
            else:
                # Máquina de escrever do modo texto puro
                texto_final, _ = self._obter_texto_formatado_atual()
                total_chars = len(texto_final)
                
                if self.texto_estado == "DIGITANDO":
                    self.caractere_atual += self.velocidade_digitacao * (dt * 60.0)
                    if self.caractere_atual >= total_chars:
                        self.caractere_atual = float(total_chars)
                        self.texto_estado = "WAIT"
                
                elif self.texto_estado == "FADE_OUT":
                    self.texto_alpha -= (self.velocidade_texto * 2.2) * (dt * 60.0)
                    if self.texto_alpha <= 0:
                        self.texto_alpha = 255.0
                        self.caractere_atual = 0.0
                        self.indice_texto += 1
                        
                        if self.indice_texto >= len(self.textos):
                            self.estado = "CLAREANDO"
                        else:
                            self.texto_estado = "DIGITANDO"

        elif self.estado == "CLAREANDO":
            self.alpha -= self.velocidade * 35.0 * dt
            if self.alpha <= 0:
                self.finalizar()
                return True  # Flashback 100% concluído!

        return False

    def _quebrar_texto(self, texto, largura_maxima, fonte=None):
        f = fonte or self.fonte_flashback
        palavras = texto.split(' ')
        linhas = []
        linha_atual = ""
        for palavra in palavras:
            teste_linha = linha_atual + palavra + " "
            if f.size(teste_linha)[0] <= largura_maxima:
                linha_atual = teste_linha
            else:
                if linha_atual: 
                    linhas.append(linha_atual.rstrip())
                linha_atual = palavra + " "
        if linha_atual: 
            linhas.append(linha_atual.rstrip())
        return linhas

    # =========================================================================
    # Desenho Principal (Acampamento vs Modo Texto)
    # =========================================================================
    def desenhar(self, tela):
        if self.estado == "INATIVO": 
            return

        # 1. Modo Visual de Acampamento no Mapa Real
        if self.tipo == "acampamento":
            # Desenha o mapa real com todos os seus elementos autênticos
            self.mapa_acampamento.desenhar(tela)

            # Pétalas sutis de recordação
            self.efeito_petalas.desenhar(tela, alpha_multiplicador=0.7)

            # Transições suaves de entrada e saída
            if self.estado == "ESCURECENDO":
                fade_alpha = max(0, min(255, int(255 - self.alpha)))
                if fade_alpha > 0:
                    overlay = pygame.Surface((self.largura, self.altura))
                    overlay.fill((8, 10, 16))
                    overlay.set_alpha(fade_alpha)
                    tela.blit(overlay, (0, 0))
            elif self.estado == "CLAREANDO":
                fade_alpha = max(0, min(255, int(255 - self.alpha)))
                if fade_alpha > 0:
                    overlay = pygame.Surface((self.largura, self.altura))
                    overlay.fill((8, 10, 16))
                    overlay.set_alpha(fade_alpha)
                    tela.blit(overlay, (0, 0))
            return

        # 2. Modo Clássico de Texto Puro sobre Escuridão
        self.superficie_preta.set_alpha(max(0, min(255, int(self.alpha))))
        tela.blit(self.superficie_preta, (0, 0))

        areas_excluidas = []
        if self.indice_texto < len(self.textos):
            texto_final, _ = self._obter_texto_formatado_atual()
            linhas = self._quebrar_texto(texto_final, self.largura - 240)
            altura_linha = 40
            altura_bloco = len(linhas) * altura_linha
            y_inicial = (self.altura // 2) - (altura_bloco // 2)
            larguras = [self.fonte_flashback.size(l)[0] for l in linhas] if linhas else [300]
            max_w = max(larguras, default=300)
            rect_txt = pygame.Rect(
                (self.largura // 2) - (max_w // 2) - 35,
                y_inicial - 25,
                max_w + 70,
                altura_bloco + 50
            )
            areas_excluidas.append(rect_txt)

        if self.estado in ("ESCURECENDO", "ESCURIDAO", "CLAREANDO"):
            alpha_petalas = min(1.0, max(0.08, self.alpha / 220.0))
            self.efeito_petalas.desenhar(tela, areas_excluidas=areas_excluidas, alpha_multiplicador=alpha_petalas)

        if self.estado == "ESCURIDAO" and self.indice_texto < len(self.textos):
            texto_final, cor_texto = self._obter_texto_formatado_atual()
            linhas = self._quebrar_texto(texto_final, self.largura - 240)
            altura_linha = 40
            altura_bloco = len(linhas) * altura_linha
            y_inicial = (self.altura // 2) - (altura_bloco // 2)

            total_visivel = int(self.caractere_atual)
            caracteres_acumulados = 0
            piscar_cursor = (pygame.time.get_ticks() // 420) % 2 == 0

            for i, linha in enumerate(linhas):
                len_linha = len(linha)
                largura_linha_completa = self.fonte_flashback.size(linha)[0]
                x_inicio_linha = (self.largura // 2) - (largura_linha_completa // 2)
                
                if total_visivel <= caracteres_acumulados:
                    break
                elif total_visivel >= caracteres_acumulados + len_linha:
                    texto_render = linha
                    caracteres_acumulados += len_linha
                    desenhar_cursor = (i == len(linhas) - 1 and self.texto_estado == "DIGITANDO" and piscar_cursor)
                else:
                    chars_nesta = total_visivel - caracteres_acumulados
                    texto_render = linha[:chars_nesta]
                    caracteres_acumulados += len_linha
                    desenhar_cursor = (self.texto_estado == "DIGITANDO" and piscar_cursor)

                if texto_render:
                    render = self.fonte_flashback.render(texto_render, True, cor_texto)
                    if self.texto_alpha < 255:
                        render.set_alpha(int(max(0, min(255, self.texto_alpha))))
                    tela.blit(render, (x_inicio_linha, y_inicial + (i * altura_linha)))

                    if desenhar_cursor:
                        x_cursor = x_inicio_linha + render.get_width() + 2
                        y_cursor = y_inicial + (i * altura_linha) + 8
                        cursor_surf = pygame.Surface((2, 24), pygame.SRCALPHA)
                        alpha_c = int(max(0, min(255, self.texto_alpha))) if self.texto_alpha < 255 else 200
                        cursor_surf.fill((*cor_texto[:3], alpha_c))
                        tela.blit(cursor_surf, (x_cursor, y_cursor))

            if self.texto_estado == "DIGITANDO":
                aviso_txt = "Clique ou pressione [ENTER / ESPAÇO] para acelerar"
            else:
                aviso_txt = "Clique ou pressione [ENTER / ESPAÇO] para recordar"
                
            avancar = self.fonte_avanco.render(aviso_txt, True, UI_TEXTO_APAGADO)
            tela.blit(avancar, ((self.largura // 2) - (avancar.get_width() // 2), self.altura - 50))
