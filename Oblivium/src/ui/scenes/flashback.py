# src/ui/flashback.py
import pygame
from src.utils.colors import (
    PRETO, TXT_ECO_PASSADO, TXT_PENSAMENTO_FANTASMA, 
    TXT_SISTEMA_NARRADOR, UI_TEXTO_APAGADO
)
from src.utils.resource_manager import ResourceManager
from src.utils.animations import EfeitoPetalas
from src.maps.mapa_flashback import MapaFlashbackAcampamento
from src.mechanics.cutscenes import CenaBase
from src.ui.scenes.texto_editorial import ApresentacaoTextoEditorial


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
        self.apresentacao_texto = ApresentacaoTextoEditorial(
            game=game,
            largura=largura,
            altura=altura,
            cor_fundo=PRETO,
            fonte_texto=self.fonte_flashback,
            fonte_dica=self.fonte_avanco,
            margem_horizontal=240,
            altura_linha=40,
            velocidade_base=self.velocidade_digitacao,
            pos_y_dica_offset=50,
            dicas=(
                "Clique ou pressione [ENTER / ESPAÇO] para acelerar",
                "Clique ou pressione [ENTER / ESPAÇO] para recordar",
            ),
        )

    def _sincronizar_texto_atual(self):
        texto_final, cor_texto = self._obter_texto_formatado_atual()
        self.apresentacao_texto.game = self.game
        self.apresentacao_texto.velocidade_base = self.velocidade_digitacao
        self.apresentacao_texto.definir_conteudo([(texto_final, cor_texto)] if texto_final else [])
        self.caractere_atual = 0.0

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
    def _sincronizar_ambiente(self, fade_ms=300):
        sincronizar = getattr(self.game, "sincronizar_ambiente_cenario", None)
        if callable(sincronizar):
            sincronizar(fade_ms=fade_ms)

    def _limpar_audio(self):
        audio = getattr(self.game, "audio", None)
        parar = getattr(audio, "parar_sfx_contexto", None)
        if callable(parar):
            parar("flashback", fade_ms=120)

    def _fechar_dialogo_acampamento(self):
        caixa = getattr(self.game, "caixa_dialogo", None)
        if self.tipo == "acampamento" and self.dialogo_iniciado and caixa:
            caixa.ativo = False
            if hasattr(caixa, "em_escolha"):
                caixa.em_escolha = False

    def _iniciar_saida(self):
        if self.estado != "CLAREANDO":
            self.estado = "CLAREANDO"
            self._sincronizar_ambiente()

    def iniciar(self, textos_memorias=None, tipo=None, game=None, on_concluido=None):
        if self.ativo:
            self.cancelar(sincronizar_ambiente=False)
        if game is not None:
            self.game = game
            self.mapa_acampamento.game = game

        self.on_concluido = None
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
        self._sincronizar_texto_atual()
        self.efeito_petalas.reiniciar(inicializar_na_tela=True)
        self._sincronizar_ambiente()
        if self.game and getattr(self.game, "audio", None):
            self.game.audio.tocar_musica(
                "cutscene_magia", loop=-1, fade_ms=1000, salvar_anterior=True, contexto="cutscene"
            )

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
            ctrl = None
            if hasattr(self.game, "estados") and "JOGANDO" in self.game.estados:
                ctrl = getattr(self.game.estados["JOGANDO"], "oakhaven_controller", None)
            if ctrl and hasattr(ctrl, "concluir_flashback_sylvan_pos_dragao"):
                ctrl.concluir_flashback_sylvan_pos_dragao()
            else:
                if hasattr(self.game, "halia") and self.game.halia and self.game.halia.fragmentos_memoria < 2:
                    self.game.halia.recuperar_memoria(1, adiar_autosave=True)
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
                self.game.etapa_epilogo = "DESPERTAR_PENDENTE"
                if getattr(self.game, "slot_atual", None) and hasattr(self.game, "salvar_estado"):
                    self.game.salvar_estado(self.game.slot_atual, tipo="autosave")
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
        if not self.ativo:
            return False
        self._fechar_dialogo_acampamento()
        # Suspende a fogueira antes que a conclusão possa abrir outra cena.
        self._iniciar_saida()
        self._limpar_audio()

        self.alpha = 0.0
        self.estado = "INATIVO"
        self.dialogo_iniciado = False
        self.concluido = True
        self._aplicar_consequencias_narrativas()
        resultado = self._executar_callback_conclusao()
        self._sincronizar_ambiente()

        despertar_pendente = bool(
            self.game
            and (
                getattr(self.game, "etapa_epilogo", None) == "DESPERTAR_PENDENTE"
                or getattr(getattr(self.game, "tela_despertar", None), "estado", "INATIVO") != "INATIVO"
            )
        )
        if not despertar_pendente and self.game and hasattr(self.game, "sincronizar_trilha_cenario"):
            self.game.sincronizar_trilha_cenario(fade_ms=1000)
        return resultado

    def cancelar(self, sincronizar_ambiente=True):
        """Descarta o ciclo ativo sem desbloqueios, autosave ou callback."""
        if not self.ativo:
            return False
        self._fechar_dialogo_acampamento()
        if sincronizar_ambiente:
            self._iniciar_saida()
        self._limpar_audio()
        self.alpha = 0.0
        self.estado = "INATIVO"
        self.dialogo_iniciado = False
        self.concluido = True
        self._consequencias_aplicadas = True
        self._callback_executado = True
        self.on_concluido = None
        if sincronizar_ambiente:
            self._sincronizar_ambiente()
        return True

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

        if self.texto_estado == "DIGITANDO":
            self.apresentacao_texto.completar_digitacao()
            self.caractere_atual = float(self.apresentacao_texto.total_caracteres)
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

        # Atualiza a chuva sutil de pétalas com opacidade suavizada durante leitura
        dialogo_ativo = bool(self.game and getattr(getattr(self.game, "caixa_dialogo", None), "ativo", False))
        if self.tipo == "acampamento":
            alpha_alvo = 0.35 if dialogo_ativo else 0.70
        elif self.estado == "ESCURIDAO":
            alpha_alvo = 0.78
        else:
            alpha_alvo = min(1.0, max(0.08, self.alpha / 220.0))
        self.efeito_petalas.atualizar(dt, alpha_alvo=alpha_alvo)

        # Atualiza animações físicas e visuais do acampamento
        if self.tipo == "acampamento":
            self.mapa_acampamento.atualizar(dt)

        # Transição de entrada (fade in)
        if self.estado == "ESCURECENDO":
            self.alpha += self.velocidade * 35.0 * dt
            if self.alpha >= 255:
                self.alpha = 255.0
                self.estado = "ESCURIDAO"
                self._sincronizar_ambiente()
                
                # Se for acampamento, aciona a DialogueBox oficial imediatamente com a lista de falas!
                if self.tipo == "acampamento":
                    if self.game and hasattr(self.game, 'caixa_dialogo') and self.textos and not self.dialogo_iniciado:
                        self.dialogo_iniciado = True
                        self.game.caixa_dialogo.iniciar_dialogo(self.textos)
                else:
                    self.texto_alpha = 255.0
                    self.texto_estado = "DIGITANDO"
                    self._sincronizar_texto_atual()

        elif self.estado == "ESCURIDAO":
            if self.tipo == "acampamento":
                # Monitora a conclusão do diálogo na DialogueBox oficial
                if self.dialogo_iniciado:
                    if self.game and hasattr(self.game, 'caixa_dialogo'):
                        if not self.game.caixa_dialogo.ativo:
                            # A conversa dos amigos foi concluída na caixa oficial! Inicia o fade out!
                            self._iniciar_saida()
                else:
                    if self.game and hasattr(self.game, 'caixa_dialogo') and self.textos:
                        self.dialogo_iniciado = True
                        self.game.caixa_dialogo.iniciar_dialogo(self.textos)
                    else:
                        self._iniciar_saida()
            else:
                # Máquina de escrever do modo texto puro (compartilhada via ApresentacaoTextoEditorial)
                if self.texto_estado == "DIGITANDO":
                    self.apresentacao_texto.game = self.game
                    self.apresentacao_texto.velocidade_base = self.velocidade_digitacao
                    terminou = self.apresentacao_texto.atualizar(dt)
                    self.caractere_atual = self.apresentacao_texto.caractere_atual
                    if terminou or self.apresentacao_texto.esta_completa():
                        self.caractere_atual = float(self.apresentacao_texto.total_caracteres)
                        self.texto_estado = "WAIT"
                
                elif self.texto_estado == "FADE_OUT":
                    self.texto_alpha -= (self.velocidade_texto * 2.2) * (dt * 60.0)
                    if self.texto_alpha <= 0:
                        self.texto_alpha = 255.0
                        self.caractere_atual = 0.0
                        self.indice_texto += 1
                        
                        if self.indice_texto >= len(self.textos):
                            self._iniciar_saida()
                        else:
                            self.texto_estado = "DIGITANDO"
                            self._sincronizar_texto_atual()

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

    def obter_areas_protegidas(self, largura=None, altura=None, margem=28):
        """Retorna áreas reais de texto do flashback ou caixa de diálogo ativa com margem."""
        w = largura or self.largura
        h = altura or self.altura
        margem_px = max(0, int(margem))
        areas = []

        if self.game and getattr(getattr(self.game, "caixa_dialogo", None), "ativo", False):
            areas.extend(self.game.caixa_dialogo.obter_areas_protegidas(w, h, margem=margem_px))

        if self.tipo != "acampamento" and self.indice_texto < len(self.textos):
            areas.extend(self.apresentacao_texto.obter_areas_protegidas(w, h, margem=margem_px))
        return areas

    # =========================================================================
    # Desenho Principal (Acampamento vs Modo Texto)
    # =========================================================================
    def desenhar(self, tela):
        if self.estado == "INATIVO": 
            return

        areas_excluidas = self.obter_areas_protegidas(tela.get_width(), tela.get_height())

        # 1. Modo Visual de Acampamento no Mapa Real
        if self.tipo == "acampamento":
            # Desenha o mapa real com todos os seus elementos autênticos
            self.mapa_acampamento.desenhar(tela)

            # Pétalas sutis de recordação respeitando caixa de diálogo ativa
            self.efeito_petalas.desenhar(tela, areas_excluidas=areas_excluidas)

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

        # 2. Modo Clássico de Texto Puro sobre Escuridão (compartilhado via ApresentacaoTextoEditorial)
        alpha_fade_tela = None if self.estado == "ESCURIDAO" else min(1.0, max(0.08, self.alpha / 220.0))
        em_texto = self.estado == "ESCURIDAO" and self.indice_texto < len(self.textos)
        self.apresentacao_texto.desenhar(
            tela,
            efeito_petalas=self.efeito_petalas if self.estado in ("ESCURECENDO", "ESCURIDAO", "CLAREANDO") else None,
            alpha=self.texto_alpha if em_texto else self.alpha,
            alpha_petalas=alpha_fade_tela,
            apenas_fundo=not em_texto,
        )
        if self.estado != "ESCURIDAO" and self.alpha < 255:
            self.superficie_preta.set_alpha(max(0, min(255, int(255 - self.alpha))))
            tela.blit(self.superficie_preta, (0, 0))
