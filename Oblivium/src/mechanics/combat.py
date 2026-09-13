# src/mechanics/combat.py
import pygame
import random
import math
from src.mechanics.skills import SkillsRegistry
from src.mechanics.conditions import Condicao
from src.entities.Enemy import Enemy
from src.entities.Boss import Boss
from src.utils.colors import (
    UI_FUNDO_PADRAO, CINZA_CLARO, CINZA_ESCURO, UI_TEXTO_DESTAQUE, 
    UI_TEXTO_APAGADO, TXT_SISTEMA_NARRADOR, TXT_PENSAMENTO_INTERNO,
    NOME_HALIA, NOME_MALDICAO, TEXTO_ALERTA_COMBATE,
    BARRA_VIDA_JOGADOR, BARRA_VIDA_INIMIGO, BARRA_MANA, FUNDO_BARRA,
    BRANCO, PRETO, BOTAO_FECHAR_NORMAL, BOTAO_FECHAR_HOVER
)

class TextoFlutuante:
    """Gerencia textos flutuantes de dano, cura ou status na tela de combate."""
    def __init__(self, texto, x, y, cor=TEXTO_ALERTA_COMBATE, duracao=60, velocidade_y=-1.3):
        self.texto = str(texto)
        self.x = float(x)
        self.y = float(y)
        self.cor = cor
        self.duracao = duracao
        self.vida = duracao
        self.velocidade_y = velocidade_y

    def atualizar(self):
        self.y += self.velocidade_y
        self.vida -= 1
        return self.vida > 0

    def desenhar(self, tela, fonte):
        if self.vida <= 0: return
        alpha = max(0, min(255, int((self.vida / self.duracao) * 255)))
        superficie = fonte.render(self.texto, True, self.cor)
        superficie.set_alpha(alpha)
        # Sombra suave para contraste
        sombra = fonte.render(self.texto, True, PRETO)
        sombra.set_alpha(int(alpha * 0.7))
        tela.blit(sombra, (int(self.x) + 2, int(self.y) + 2))
        tela.blit(superficie, (int(self.x), int(self.y)))


class CombatScreen:
    """
    Motor e Interface Gráfica de Combate por Turnos de Oblivium.
    Identidade visual sóbria, painel inferior amplo, espaçamento equilibrado entre entidades
    e compatibilidade total com mouse e teclado.
    """
    def __init__(self, largura, altura):
        self.largura = largura
        self.altura = altura
        
        # Fontes do Combate
        self.fonte_titulo = pygame.font.Font(None, 42)
        self.fonte_nomes = pygame.font.Font(None, 32)
        self.fonte_status = pygame.font.Font(None, 22)
        self.fonte_menu = pygame.font.Font(None, 30)
        self.fonte_log = pygame.font.Font(None, 24)
        self.fonte_dano = pygame.font.Font(None, 34)
        self.fonte_tooltip = pygame.font.Font(None, 22)
        
        # Estrutura do Menu Principal
        self.opcoes_menu_principal = ["Atacar", "Magias", "Concentrar", "Fugir"]
        self.indice_menu = 0
        
        # Submenu de Magias
        self.magias_disponiveis = []
        self.indice_magia = 0
        
        # Seleção de Alvo
        self.indice_alvo = 0
        self.acao_selecionada = None
        
        # Entidades e Fila de Turnos
        self.jogador = None
        self.inimigos = []
        self.ordem_turnos = [] 
        self.indice_turno_atual = 0
        
        # Callbacks Desacoplados
        self.on_vitoria = None
        self.on_derrota = None
        self.on_fuga = None
        
        # Estados do Motor de Combate
        self.estado_combate = "INATIVO"
        
        # Log e Mensagens de Batalha
        self.historico_log = []
        self.mensagem_atual = ""
        self.timer_acao = 0
        self.textos_flutuantes = []
        
        # Efeitos Visuais e Interpolação de Barras
        self.vidas_visuais = {}
        self.manas_visuais = {}
        self.shake_timers = {}
        self.tick_arena = 0
        
        # Hitboxes de Interação de Mouse
        self.rects_menu_principal = []
        self.rects_magias = []
        self.rects_inimigos = []
        self.rect_botao_voltar = pygame.Rect(0, 0, 0, 0)
        self.rect_banner = pygame.Rect(0, 0, 0, 0)
        
        # Recompensas Acumuladas
        self.recompensas_vitoria = {"moedas": 0, "memorias": 0, "xp": 0}

    # =========================================================================
    # INICIALIZAÇÃO DO COMBATE
    # =========================================================================

    def iniciar_combate(self, jogador, inimigos, on_vitoria=None, on_derrota=None, on_fuga=None):
        """Prepara e inicia uma nova sessão de combate."""
        self.jogador = jogador
        self.inimigos = [i for i in inimigos if getattr(i, 'vivo', True)]
        self.on_vitoria = on_vitoria
        self.on_derrota = on_derrota
        self.on_fuga = on_fuga
        
        self.indice_menu = 0
        self.indice_magia = 0
        self.indice_alvo = 0
        self.acao_selecionada = None
        self.textos_flutuantes.clear()
        self.historico_log.clear()
        self.shake_timers.clear()
        
        # Inicializa valores visuais de HP e MP
        self.vidas_visuais[self.jogador] = float(self.jogador.vida_atual)
        self.manas_visuais[self.jogador] = float(self.jogador.mana_atual)
        for inimigo in self.inimigos:
            self.vidas_visuais[inimigo] = float(inimigo.vida_atual)

        # Notifica jogador
        if hasattr(self.jogador, 'entrar_combate'):
            self.jogador.entrar_combate()

        # Carrega grimório do jogador
        self._carregar_magias_jogador()

        self.adicionar_log("A batalha começou!")
        self._iniciar_nova_rodada()

    def _carregar_magias_jogador(self):
        """Carrega a lista de ações disponíveis para o jogador."""
        self.magias_disponiveis.clear()
        ids_magias = getattr(self.jogador, 'magias_desbloqueadas', ["ataque_basico", "bola_de_fogo", "levitar", "brisa_curativa"])
        for id_magia in ids_magias:
            acao = SkillsRegistry.get(id_magia)
            if acao:
                self.magias_disponiveis.append(acao)

    def _iniciar_nova_rodada(self):
        """Calcula a ordem de iniciativa de todas as criaturas vivas."""
        participantes = [self.jogador] + [i for i in self.inimigos if getattr(i, 'vivo', True)]
        
        # Reseta defesas ativas do turno anterior
        for p in participantes:
            if hasattr(p, 'resetar_turno_combate'):
                p.resetar_turno_combate()

        # Ordena por iniciativa decrescente
        self.ordem_turnos = sorted(
            participantes,
            key=lambda ent: ent.calcular_iniciativa() if hasattr(ent, 'calcular_iniciativa') else 10,
            reverse=True
        )
        self.indice_turno_atual = 0
        self._avancar_para_proximo_turno()

    def _avancar_para_proximo_turno(self):
        """Avança a vez para a próxima entidade viva da fila."""
        # 1. Verifica se todos os inimigos foram derrotados
        inimigos_vivos = self._obter_inimigos_vivos()
        if not inimigos_vivos:
            self._finalizar_vitoria()
            return

        # 2. Verifica se o jogador foi derrotado
        if not getattr(self.jogador, 'vivo', True) or self.jogador.vida_atual <= 0:
            self._finalizar_derrota()
            return

        # 3. Se a rodada acabou, começa nova rodada
        if self.indice_turno_atual >= len(self.ordem_turnos):
            self._iniciar_nova_rodada()
            return

        entidade_atual = self.ordem_turnos[self.indice_turno_atual]
        
        # Pula entidades mortas
        if not getattr(entidade_atual, 'vivo', True):
            self.indice_turno_atual += 1
            self._avancar_para_proximo_turno()
            return

        # 4. Processa Condições / DoT / CC no início do turno
        if hasattr(entidade_atual, 'processar_condicoes_inicio_turno'):
            relatorios, impede_acao = entidade_atual.processar_condicoes_inicio_turno()
            for r in relatorios:
                if r.get("mensagem"):
                    self.adicionar_log(r["mensagem"])
                if r.get("dano", 0) > 0:
                    self.adicionar_texto_flutuante(f"-{r['dano']}", entidade_atual.x + 20, entidade_atual.y, TEXTO_ALERTA_COMBATE)
                    self.shake_timers[entidade_atual] = 8

            if not getattr(entidade_atual, 'vivo', True):
                self.adicionar_log(f"{entidade_atual.nome} sucumbiu às condições!")
                self.indice_turno_atual += 1
                self._avancar_para_proximo_turno()
                return

            if impede_acao:
                self.timer_acao = 40
                self.estado_combate = "EXECUTANDO_ACAO"
                return

        # 5. Define se é turno do Jogador ou IA do Inimigo
        if entidade_atual is self.jogador:
            self.estado_combate = "MENU_PRINCIPAL"
            self.indice_menu = 0
            self.adicionar_log("Sua vez! Escolha uma ação.")
        else:
            self.estado_combate = "TURNO_INIMIGO"
            self.timer_acao = 45

    # =========================================================================
    # PROCESSAMENTO DE EVENTOS (TECLADO E MOUSE)
    # =========================================================================

    def processar_eventos(self, evento):
        # 1. Movimento do Mouse (Hover)
        if evento.type == pygame.MOUSEMOTION:
            pos = evento.pos
            if self.estado_combate == "MENU_PRINCIPAL":
                for idx, r in enumerate(self.rects_menu_principal):
                    if r.collidepoint(pos):
                        self.indice_menu = idx
                        break

            elif self.estado_combate == "SUBMENU_MAGIA":
                for idx, r in enumerate(self.rects_magias):
                    if r.collidepoint(pos):
                        self.indice_magia = idx
                        break

            elif self.estado_combate == "SELECIONANDO_ALVO":
                for idx, r in enumerate(self.rects_inimigos):
                    if r.collidepoint(pos):
                        self.indice_alvo = idx
                        break

        # 2. Clique do Mouse (Botão Esquerdo)
        elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            pos = evento.pos
            
            # Telas finais: Clique em qualquer lugar fecha
            if self.estado_combate in ["VITORIA", "DERROTA", "FUGIU"]:
                self._concluir_fechamento_combate()
                return

            if self.estado_combate == "MENU_PRINCIPAL":
                for idx, r in enumerate(self.rects_menu_principal):
                    if r.collidepoint(pos):
                        self.indice_menu = idx
                        self._selecionar_opcao_menu_principal()
                        return

            elif self.estado_combate == "SUBMENU_MAGIA":
                if self.rect_botao_voltar.collidepoint(pos):
                    self.estado_combate = "MENU_PRINCIPAL"
                    return
                for idx, r in enumerate(self.rects_magias):
                    if r.collidepoint(pos):
                        self.indice_magia = idx
                        self._selecionar_magia_grimorio()
                        return

            elif self.estado_combate == "SELECIONANDO_ALVO":
                for idx, r in enumerate(self.rects_inimigos):
                    if r.collidepoint(pos):
                        self.indice_alvo = idx
                        inimigos_vivos = self._obter_inimigos_vivos()
                        if idx < len(inimigos_vivos):
                            self._executar_acao_jogador(self.acao_selecionada, inimigos_vivos[idx])
                        return

        # 3. Teclado
        elif evento.type == pygame.KEYDOWN:
            if self.estado_combate in ["VITORIA", "DERROTA", "FUGIU"]:
                if evento.key in [pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE]:
                    self._concluir_fechamento_combate()
                return

            if self.estado_combate == "MENU_PRINCIPAL":
                if evento.key in [pygame.K_UP, pygame.K_w]:
                    self.indice_menu = (self.indice_menu - 1) % len(self.opcoes_menu_principal)
                elif evento.key in [pygame.K_DOWN, pygame.K_s]:
                    self.indice_menu = (self.indice_menu + 1) % len(self.opcoes_menu_principal)
                elif evento.key in [pygame.K_RETURN, pygame.K_SPACE, pygame.K_e]:
                    self._selecionar_opcao_menu_principal()

            elif self.estado_combate == "SUBMENU_MAGIA":
                if evento.key in [pygame.K_UP, pygame.K_w]:
                    self.indice_magia = (self.indice_magia - 1) % len(self.magias_disponiveis)
                elif evento.key in [pygame.K_DOWN, pygame.K_s]:
                    self.indice_magia = (self.indice_magia + 1) % len(self.magias_disponiveis)
                elif evento.key in [pygame.K_RETURN, pygame.K_SPACE, pygame.K_e]:
                    self._selecionar_magia_grimorio()
                elif evento.key == pygame.K_ESCAPE:
                    self.estado_combate = "MENU_PRINCIPAL"

            elif self.estado_combate == "SELECIONANDO_ALVO":
                inimigos_vivos = self._obter_inimigos_vivos()
                if not inimigos_vivos:
                    return

                if evento.key in [pygame.K_UP, pygame.K_w]:
                    self.indice_alvo = (self.indice_alvo - 1) % len(inimigos_vivos)
                elif evento.key in [pygame.K_DOWN, pygame.K_s]:
                    self.indice_alvo = (self.indice_alvo + 1) % len(inimigos_vivos)
                elif evento.key in [pygame.K_RETURN, pygame.K_SPACE, pygame.K_e]:
                    alvo = inimigos_vivos[self.indice_alvo]
                    self._executar_acao_jogador(self.acao_selecionada, alvo)
                elif evento.key == pygame.K_ESCAPE:
                    self.estado_combate = "MENU_PRINCIPAL"

    # =========================================================================
    # LÓGICA DE SELEÇÃO E EXECUÇÃO DE AÇÕES
    # =========================================================================

    def _selecionar_opcao_menu_principal(self):
        opcao = self.opcoes_menu_principal[self.indice_menu]

        if opcao == "Atacar":
            self.acao_selecionada = SkillsRegistry.get("ataque_basico")
            inimigos_vivos = self._obter_inimigos_vivos()
            if len(inimigos_vivos) == 1:
                self._executar_acao_jogador(self.acao_selecionada, inimigos_vivos[0])
            else:
                self.estado_combate = "SELECIONANDO_ALVO"
                self.indice_alvo = 0

        elif opcao == "Magias":
            self._carregar_magias_jogador()
            self.estado_combate = "SUBMENU_MAGIA"
            self.indice_magia = 0

        elif opcao == "Concentrar":
            foco = SkillsRegistry.get("foco")
            self._executar_acao_jogador(foco, self.jogador)

        elif opcao == "Fugir":
            self._tentar_fuga()

    def _selecionar_magia_grimorio(self):
        if not self.magias_disponiveis:
            return

        magia = self.magias_disponiveis[self.indice_magia]
        if self.jogador.mana_atual < magia.custo_mana:
            self.adicionar_log(f"Mana insuficiente ({self.jogador.mana_atual}/{magia.custo_mana} MP)!")
            return

        alvo_tipo_padrao = getattr(magia, 'tipo_alvo', getattr(magia, 'alvo_tipo', 'inimigo_unico')).lower()
        if alvo_tipo_padrao in ["aliado", "proprio"]:
            self._executar_acao_jogador(magia, self.jogador)
        elif alvo_tipo_padrao in ["todos_inimigos", "todos"]:
            self._executar_acao_jogador(magia, self.inimigos)
        else: # inimigo_unico
            inimigos_vivos = self._obter_inimigos_vivos()
            if len(inimigos_vivos) == 1:
                self._executar_acao_jogador(magia, inimigos_vivos[0])
            else:
                self.acao_selecionada = magia
                self.estado_combate = "SELECIONANDO_ALVO"
                self.indice_alvo = 0

    def _executar_acao_jogador(self, acao, alvo):
        """Executa a ação escolhida pelo jogador com cálculo de dano e feedback."""
        if not acao:
            acao = SkillsRegistry.get("ataque_basico")

        self.estado_combate = "EXECUTANDO_ACAO"
        self.timer_acao = 75
        
        resultado = acao.executar(self.jogador, alvo)
        
        # 1. Trata mensagem única direta (ex: Foco)
        if resultado.get("mensagem"):
            self.adicionar_log(resultado["mensagem"])

        if resultado.get("cura", 0) > 0:
            self.adicionar_texto_flutuante(f"+{resultado['cura']}", self.jogador.x + 30, self.jogador.y - 10, BARRA_VIDA_JOGADOR)
        if resultado.get("mana_recuperada", 0) > 0:
            self.adicionar_texto_flutuante(f"+{resultado['mana_recuperada']} MP", self.jogador.x + 30, self.jogador.y + 15, BARRA_MANA)

        # 2. Trata lista de resultados de alvos (ataques e magias)
        for r in resultado.get("resultados", []):
            if r.get("mensagem"):
                self.adicionar_log(r["mensagem"])
                
            alvo_r = r.get("alvo")
            if r.get("dano", 0) > 0 and alvo_r:
                self.adicionar_texto_flutuante(f"-{r['dano']}", alvo_r.x + 20, alvo_r.y, TEXTO_ALERTA_COMBATE)
                self.shake_timers[alvo_r] = 12
            elif r.get("cura", 0) > 0 and alvo_r:
                self.adicionar_texto_flutuante(f"+{r['cura']}", alvo_r.x + 20, alvo_r.y - 10, BARRA_VIDA_JOGADOR)

    def _executar_turno_inimigo(self, inimigo):
        """IA do inimigo: seleciona habilidade temática de monstro e executa contra Halia."""
        self.estado_combate = "EXECUTANDO_ACAO"
        self.timer_acao = 75
        
        # Escolhe ação temática do kit do monstro
        kit = getattr(inimigo, 'habilidades', ["garras_sombrias", "golpe_sombrio"])
        id_escolhido = random.choice(kit) if kit else "garras_sombrias"
        acao = SkillsRegistry.get(id_escolhido)
        if not acao:
            acao = SkillsRegistry.get("garras_sombrias") or SkillsRegistry.get("golpe_sombrio")

        resultado = acao.executar(inimigo, self.jogador)
        
        if resultado.get("mensagem"):
            self.adicionar_log(resultado["mensagem"])
            
        for r in resultado.get("resultados", []):
            if r.get("mensagem"):
                self.adicionar_log(r["mensagem"])
            if r.get("dano", 0) > 0:
                self.adicionar_texto_flutuante(f"-{r['dano']}", self.jogador.x + 30, self.jogador.y, TEXTO_ALERTA_COMBATE)
                self.shake_timers[self.jogador] = 12

    def _tentar_fuga(self):
        """Calcula a probabilidade de fuga baseada na Destreza."""
        inimigos_vivos = self._obter_inimigos_vivos()
        des_inimigos = sum(i.atributos.destreza for i in inimigos_vivos) / max(1, len(inimigos_vivos))
        des_jogador = self.jogador.atributos.destreza
        
        # Chance base de 50% + 4% por ponto de vantagem em Destreza
        chance = max(20.0, min(90.0, 50.0 + (des_jogador - des_inimigos) * 4.0))
        rolagem = random.uniform(0, 100)
        
        if rolagem <= chance:
            self.adicionar_log("Halia recuou com sucesso para um local seguro.")
            self.estado_combate = "FUGIU"
        else:
            self.adicionar_log("Tentativa de fuga falhou! Os inimigos bloquearam o caminho.")
            self.timer_acao = 45
            self.estado_combate = "EXECUTANDO_ACAO"

    # =========================================================================
    # ATUALIZAÇÃO DO MOTOR DE COMBATE
    # =========================================================================

    def atualizar(self):
        """Loop de atualização de timers, animações de texto, interpolação de HP e turnos."""
        self.tick_arena += 1

        # Atualiza interpolação suave de HP e MP
        if self.jogador:
            v_atual = self.vidas_visuais.get(self.jogador, float(self.jogador.vida_atual))
            self.vidas_visuais[self.jogador] += (self.jogador.vida_atual - v_atual) * 0.15
            
            m_atual = self.manas_visuais.get(self.jogador, float(self.jogador.mana_atual))
            self.manas_visuais[self.jogador] += (self.jogador.mana_atual - m_atual) * 0.15

        for inimigo in self.inimigos:
            v_atual = self.vidas_visuais.get(inimigo, float(inimigo.vida_atual))
            self.vidas_visuais[inimigo] += (inimigo.vida_atual - v_atual) * 0.15

        # Atualiza timers de tremor (shake)
        for ent in list(self.shake_timers.keys()):
            if self.shake_timers[ent] > 0:
                self.shake_timers[ent] -= 1
            else:
                del self.shake_timers[ent]

        # Atualiza textos flutuantes
        self.textos_flutuantes = [t for t in self.textos_flutuantes if t.atualizar()]

        # Execução de timer de leitura de ação
        if self.estado_combate == "EXECUTANDO_ACAO":
            if self.timer_acao > 0:
                self.timer_acao -= 1
            else:
                self.indice_turno_atual += 1
                self._avancar_para_proximo_turno()

        # Execução do turno do inimigo
        elif self.estado_combate == "TURNO_INIMIGO":
            if self.timer_acao > 0:
                self.timer_acao -= 1
            else:
                if self.indice_turno_atual < len(self.ordem_turnos):
                    inimigo_atual = self.ordem_turnos[self.indice_turno_atual]
                    self._executar_turno_inimigo(inimigo_atual)
                else:
                    self._avancar_para_proximo_turno()

        return self.estado_combate

    # =========================================================================
    # RESOLUÇÃO DE BATALHA (VITÓRIA / DERROTA / RECOMPENSAS)
    # =========================================================================

    def _finalizar_vitoria(self):
        """Distribui recompensas acumuladas de todos os inimigos e exibe banner."""
        self.recompensas_vitoria = {"moedas": 0, "memorias": 0, "xp": 0}
        
        for inimigo in self.inimigos:
            rec = getattr(inimigo, 'recompensas', {})
            self.recompensas_vitoria["moedas"] += rec.get("moedas", 10)
            self.recompensas_vitoria["memorias"] += rec.get("memorias", 0)
            self.recompensas_vitoria["xp"] += rec.get("xp", 15)

        # Entrega recompensas à Halia
        if hasattr(self.jogador, 'ganhar_dinheiro'):
            self.jogador.ganhar_dinheiro(self.recompensas_vitoria["moedas"])
        if hasattr(self.jogador, 'recuperar_memoria') and self.recompensas_vitoria["memorias"] > 0:
            self.jogador.recuperar_memoria(self.recompensas_vitoria["memorias"])

        self.adicionar_log(f"Vitoria! Recebeu {self.recompensas_vitoria['moedas']} moedas e {self.recompensas_vitoria['memorias']} memorias.")
        self.estado_combate = "VITORIA"

    def _finalizar_derrota(self):
        """Configura estado de derrota."""
        self.adicionar_log("Halia sucumbiu e foi resgatada ao ultimo checkpoint...")
        self.estado_combate = "DERROTA"

    def _concluir_fechamento_combate(self):
        """Dispara os callbacks configurados ao encerrar."""
        if hasattr(self.jogador, 'sair_combate'):
            self.jogador.sair_combate()

        if self.estado_combate == "VITORIA" and callable(self.on_vitoria):
            self.on_vitoria()
        elif self.estado_combate == "DERROTA" and callable(self.on_derrota):
            self.on_derrota()
        elif self.estado_combate == "FUGIU" and callable(self.on_fuga):
            self.on_fuga()

    # =========================================================================
    # MÉTODOS DE RENDERIZAÇÃO E POLIMENTO VISUAL
    # =========================================================================

    def _obter_inimigos_vivos(self):
        return [i for i in self.inimigos if getattr(i, 'vivo', True)]

    def adicionar_log(self, mensagem):
        self.mensagem_atual = mensagem
        self.historico_log.append(mensagem)
        if len(self.historico_log) > 6:
            self.historico_log.pop(0)

    def adicionar_texto_flutuante(self, texto, x, y, cor=TEXTO_ALERTA_COMBATE):
        self.textos_flutuantes.append(TextoFlutuante(texto, x, y, cor=cor))

    def desenhar_barra(self, tela, x, y, valor_atual, valor_maximo, cor_barra, cor_fundo=FUNDO_BARRA, largura=180, altura=12):
        """Desenha barras estilizadas com borda suave e visual interpolado."""
        razao = max(0.0, min(1.0, valor_atual / valor_maximo)) if valor_maximo > 0 else 0.0
        largura_atual = int(largura * razao)
        
        # Fundo da barra
        pygame.draw.rect(tela, cor_fundo, (x, y, largura, altura))
        # Preenchimento
        if largura_atual > 0:
            pygame.draw.rect(tela, cor_barra, (x, y, largura_atual, altura))
        # Borda no padrão da UI de Oblivium
        pygame.draw.rect(tela, CINZA_CLARO, (x, y, largura, altura), 1)

    def desenhar(self, tela):
        """Renderiza a arena, personagens, HUDs, menus, tooltips e banners no padrão de Oblivium."""
        # 1. FUNDO PADRÃO ESCURO DE OBLIVIUM
        tela.fill(UI_FUNDO_PADRAO)
        
        # Linha horizontal de horizonte sutil
        pygame.draw.line(tela, CINZA_ESCURO, (0, 390), (self.largura, 390), 1)

        # 2. RENDERIZAR INIMIGOS (Lado Direito com Espaçamento Amplo)
        self.rects_inimigos.clear()
        inimigos_vivos = [i for i in self.inimigos if getattr(i, 'vivo', True)]
        total_inimigos = len(inimigos_vivos)

        for idx, inimigo in enumerate(inimigos_vivos):
            pos_x = self.largura - 350
            
            # Espaçamento vertical bem distribuído conforme a quantidade
            if total_inimigos == 1:
                pos_y = 150
            elif total_inimigos == 2:
                pos_y = 75 + (idx * 175)
            else:
                pos_y = 50 + (idx * 130)
            
            # Efeito de tremor (Shake) ao tomar dano
            offset_shake_x = random.randint(-3, 3) if self.shake_timers.get(inimigo, 0) > 0 else 0
            offset_shake_y = random.randint(-2, 2) if self.shake_timers.get(inimigo, 0) > 0 else 0
            
            draw_x = pos_x + offset_shake_x
            draw_y = pos_y + offset_shake_y

            # Plataforma / Sombra sutil no chão sob o inimigo
            pygame.draw.ellipse(tela, (22, 22, 26), (draw_x - 10, draw_y + 80, 100, 20))

            # Hitbox para clique de mouse
            rect_hitbox = pygame.Rect(draw_x - 10, draw_y - 25, 240, 125)
            self.rects_inimigos.append(rect_hitbox)

            # Cursor de Seleção de Alvo
            if self.estado_combate == "SELECIONANDO_ALVO" and idx == self.indice_alvo:
                cursor_txt = self.fonte_titulo.render(">", True, TXT_SISTEMA_NARRADOR)
                tela.blit(cursor_txt, (draw_x - 30, draw_y + 15))
                pygame.draw.rect(tela, TXT_SISTEMA_NARRADOR, rect_hitbox, 1)

            # Renderiza Imagem ou Bloco Colorido
            imagem = getattr(inimigo, 'imagem_atual', None)
            if imagem:
                img_combate = pygame.transform.scale(imagem, (inimigo.largura * 2, inimigo.altura * 2))
                tela.blit(img_combate, (draw_x, draw_y))
            else:
                rect_inimigo = pygame.Rect(draw_x, draw_y, getattr(inimigo, 'largura', 40) * 2, getattr(inimigo, 'altura', 40) * 2)
                cor_bloco = BRANCO if self.shake_timers.get(inimigo, 0) > 6 else getattr(inimigo, 'cor', (140, 40, 50))
                pygame.draw.rect(tela, cor_bloco, rect_inimigo)
                pygame.draw.rect(tela, CINZA_CLARO, rect_inimigo, 2)

            # Nome do Inimigo
            texto_nome = self.fonte_nomes.render(inimigo.nome, True, TEXTO_ALERTA_COMBATE)
            tela.blit(texto_nome, (draw_x, draw_y - 28))
            
            # Badges de Condições Ativas
            offset_icone_x = draw_x + texto_nome.get_width() + 8
            for cond in getattr(inimigo, 'condicoes', []):
                txt_badge = self.fonte_status.render(f"{cond.icone}:{cond.duracao}", True, TXT_SISTEMA_NARRADOR)
                tela.blit(txt_badge, (offset_icone_x, draw_y - 25))
                offset_icone_x += txt_badge.get_width() + 6

            # Barra de Vida Suave Interpolada
            vida_v = self.vidas_visuais.get(inimigo, float(inimigo.vida_atual))
            self.desenhar_barra(tela, draw_x, draw_y + (getattr(inimigo, 'altura', 40) * 2) + 8, vida_v, inimigo.vida_maxima, BARRA_VIDA_INIMIGO, largura=150)
            txt_hp = self.fonte_status.render(f"{int(vida_v)}/{inimigo.vida_maxima}", True, UI_TEXTO_DESTAQUE)
            tela.blit(txt_hp, (draw_x + 158, draw_y + (getattr(inimigo, 'altura', 40) * 2) + 6))

        # 3. RENDERIZAR HALIA (Lado Esquerdo - Sem Círculo)
        halia_x, halia_y = 160, 160
        offset_h_x = random.randint(-3, 3) if self.shake_timers.get(self.jogador, 0) > 0 else 0
        offset_h_y = random.randint(-2, 2) if self.shake_timers.get(self.jogador, 0) > 0 else 0
        
        draw_hx = halia_x + offset_h_x
        draw_hy = halia_y + offset_h_y

        # Plataforma / Sombra sutil no chão sob a Halia (sem aura)
        pygame.draw.ellipse(tela, (22, 22, 26), (draw_hx - 10, draw_hy + 90, 105, 22))

        # Imagem ou Bloco da Halia
        img_halia = getattr(self.jogador, 'imagem_atual', None)
        if img_halia:
            img_c = pygame.transform.scale(img_halia, (self.jogador.largura * 2, self.jogador.altura * 2))
            tela.blit(img_c, (draw_hx, draw_hy))
        else:
            rect_h = pygame.Rect(draw_hx, draw_hy, 75, 95)
            cor_h = BRANCO if self.shake_timers.get(self.jogador, 0) > 6 else (34, 139, 34)
            pygame.draw.rect(tela, cor_h, rect_h)
            pygame.draw.rect(tela, CINZA_CLARO, rect_h, 2)

        # Nome da Halia
        txt_halia = self.fonte_nomes.render(self.jogador.nome, True, NOME_HALIA)
        tela.blit(txt_halia, (draw_hx, draw_hy - 32))
        
        # Badges de Condições da Halia
        offset_h_badge = draw_hx + txt_halia.get_width() + 8
        for cond in getattr(self.jogador, 'condicoes', []):
            txt_badge_h = self.fonte_status.render(f"{cond.icone}:{cond.duracao}", True, TXT_SISTEMA_NARRADOR)
            tela.blit(txt_badge_h, (offset_h_badge, draw_hy - 30))
            offset_h_badge += txt_badge_h.get_width() + 6

        # Barras Interpoladas de HP e MP da Halia
        vida_h_v = self.vidas_visuais.get(self.jogador, float(self.jogador.vida_atual))
        mana_h_v = self.manas_visuais.get(self.jogador, float(self.jogador.mana_atual))

        self.desenhar_barra(tela, draw_hx, draw_hy + 105, vida_h_v, self.jogador.vida_maxima, (200, 40, 50), largura=180)
        tela.blit(self.fonte_status.render(f"HP {int(vida_h_v)}/{self.jogador.vida_maxima}", True, UI_TEXTO_DESTAQUE), (draw_hx + 190, draw_hy + 103))

        self.desenhar_barra(tela, draw_hx, draw_hy + 125, mana_h_v, self.jogador.mana_maxima, (50, 130, 210), largura=180)
        tela.blit(self.fonte_status.render(f"MP {int(mana_h_v)}/{self.jogador.mana_maxima}", True, UI_TEXTO_DESTAQUE), (draw_hx + 190, draw_hy + 123))

        # 4. CAIXA INFERIOR DE MENUS E COMBAT LOG AMPLA (PADRÃO DIALOGUE BOX)
        altura_painel = 245
        painel_rect = pygame.Rect(40, self.altura - altura_painel - 20, self.largura - 80, altura_painel)
        pygame.draw.rect(tela, UI_FUNDO_PADRAO, painel_rect)
        pygame.draw.rect(tela, CINZA_CLARO, painel_rect, 2)

        # Divisão Interna: Seção de Ações (Esquerda 360px) | Seção de Log (Direita)
        largura_secao_menu = 360
        pygame.draw.line(tela, CINZA_ESCURO, (painel_rect.x + largura_secao_menu, painel_rect.y), (painel_rect.x + largura_secao_menu, painel_rect.bottom), 1)

        # RENDERIZAR MENU PRINCIPAL
        self.rects_menu_principal.clear()
        if self.estado_combate == "MENU_PRINCIPAL":
            for i, opcao in enumerate(self.opcoes_menu_principal):
                item_y = painel_rect.y + 20 + (i * 50)
                item_rect = pygame.Rect(painel_rect.x + 20, item_y, largura_secao_menu - 40, 42)
                self.rects_menu_principal.append(item_rect)
                
                if i == self.indice_menu:
                    pygame.draw.rect(tela, (28, 28, 34), item_rect)
                    pygame.draw.rect(tela, CINZA_CLARO, item_rect, 1)
                    cor = TXT_SISTEMA_NARRADOR
                    marcador = "> "
                else:
                    cor = CINZA_CLARO
                    marcador = "  "
                    
                txt = self.fonte_menu.render(f"{marcador}{opcao}", True, cor)
                tela.blit(txt, (item_rect.x + 14, item_rect.y + 8))

        # RENDERIZAR SUBMENU DE MAGIAS COM TOOLTIP
        self.rects_magias.clear()
        if self.estado_combate == "SUBMENU_MAGIA":
            self.rect_botao_voltar = pygame.Rect(painel_rect.x + 20, painel_rect.y + 12, 100, 26)
            pygame.draw.rect(tela, (25, 25, 30), self.rect_botao_voltar)
            pygame.draw.rect(tela, CINZA_CLARO, self.rect_botao_voltar, 1)
            txt_voltar = self.fonte_status.render("< Voltar", True, UI_TEXTO_DESTAQUE)
            tela.blit(txt_voltar, (self.rect_botao_voltar.x + 14, self.rect_botao_voltar.y + 5))

            for i, magia in enumerate(self.magias_disponiveis):
                item_y = painel_rect.y + 46 + (i * 44)
                item_rect = pygame.Rect(painel_rect.x + 20, item_y, largura_secao_menu - 40, 38)
                self.rects_magias.append(item_rect)
                
                if i == self.indice_magia:
                    pygame.draw.rect(tela, (28, 28, 34), item_rect)
                    pygame.draw.rect(tela, CINZA_CLARO, item_rect, 1)
                    cor = TXT_SISTEMA_NARRADOR
                    marcador = "> "
                else:
                    cor = CINZA_CLARO
                    marcador = "  "
                    
                custo_txt = f"({magia.custo_mana} MP)" if magia.custo_mana > 0 else "(Gratis)"
                txt = self.fonte_menu.render(f"{marcador}{magia.nome} {custo_txt}", True, cor)
                tela.blit(txt, (item_rect.x + 10, item_rect.y + 6))

            # Exibe painel de detalhes (Tooltip) da magia selecionada
            if self.indice_magia < len(self.magias_disponiveis):
                magia_sel = self.magias_disponiveis[self.indice_magia]
                self._desenhar_tooltip_magia(tela, magia_sel, painel_rect.x + largura_secao_menu + 20, painel_rect.bottom - 55)

        # RENDERIZAR SELEÇÃO DE ALVOS
        elif self.estado_combate == "SELECIONANDO_ALVO":
            txt_alvo = self.fonte_menu.render("Selecione o Inimigo Alvo:", True, TXT_SISTEMA_NARRADOR)
            tela.blit(txt_alvo, (painel_rect.x + 20, painel_rect.y + 15))
            
            inimigos_vivos = self._obter_inimigos_vivos()
            for i, inimigo in enumerate(inimigos_vivos):
                cor = TXT_SISTEMA_NARRADOR if i == self.indice_alvo else CINZA_CLARO
                marcador = "> " if i == self.indice_alvo else "  "
                txt_i = self.fonte_status.render(f"{marcador}{inimigo.nome} ({inimigo.vida_atual}/{inimigo.vida_maxima} HP)", True, cor)
                tela.blit(txt_i, (painel_rect.x + 20, painel_rect.y + 55 + (i * 32)))

        # RENDERIZAR COMBAT LOG (Seção Direita)
        pos_log_x = painel_rect.x + largura_secao_menu + 30
        pos_log_y = painel_rect.y + 16
        
        txt_cabecalho_log = self.fonte_status.render("HISTORICO DE COMBATE", True, UI_TEXTO_APAGADO)
        tela.blit(txt_cabecalho_log, (pos_log_x, pos_log_y))
        
        linhas_exibidas = self.historico_log[-4:] if self.estado_combate == "SUBMENU_MAGIA" else self.historico_log[-6:]
        for idx, linha in enumerate(linhas_exibidas):
            cor_linha = BRANCO if idx == len(linhas_exibidas) - 1 else CINZA_CLARO
            txt_linha = self.fonte_log.render(linha, True, cor_linha)
            tela.blit(txt_linha, (pos_log_x, pos_log_y + 28 + (idx * 28)))

        # 5. RENDERIZAR NÚMEROS FLUTUANTES
        for tf in self.textos_flutuantes:
            tf.desenhar(tela, self.fonte_dano)

        # 6. TELAS ESPECIAIS (Banners de Vitória, Derrota e Fuga)
        if self.estado_combate in ["VITORIA", "DERROTA", "FUGIU"]:
            self._desenhar_banner_fim_combate(tela)

    def _desenhar_tooltip_magia(self, tela, magia, x, y):
        """Desenha uma faixa descritiva elegante para a magia selecionada."""
        rect_tt = pygame.Rect(x, y, self.largura - x - 55, 42)
        pygame.draw.rect(tela, (20, 20, 25), rect_tt)
        pygame.draw.rect(tela, CINZA_CLARO, rect_tt, 1)

        detalhe = f"[{magia.elemento}] Poder: {magia.poder_base} | {magia.descricao}"
        txt_d = self.fonte_tooltip.render(detalhe, True, UI_TEXTO_DESTAQUE)
        tela.blit(txt_d, (rect_tt.x + 12, rect_tt.y + 11))

    def _desenhar_banner_fim_combate(self, tela):
        overlay = pygame.Surface((self.largura, self.altura), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 195))
        tela.blit(overlay, (0, 0))

        largura_b, altura_b = 640, 260
        rx = (self.largura - largura_b) // 2
        ry = (self.altura - altura_b) // 2
        self.rect_banner = pygame.Rect(rx, ry, largura_b, altura_b)
        
        pygame.draw.rect(tela, UI_FUNDO_PADRAO, self.rect_banner)
        
        if self.estado_combate == "VITORIA":
            cor_borda = TXT_SISTEMA_NARRADOR
            titulo = "VITORIA!"
            msg1 = f"Recompensas: +{self.recompensas_vitoria['moedas']} Moedas | +{self.recompensas_vitoria['memorias']} Memoria(s)"
            msg2 = "Pressione [ENTER], [ESPACO] ou clique para continuar..."
        elif self.estado_combate == "DERROTA":
            cor_borda = TEXTO_ALERTA_COMBATE
            titulo = "DERROTA"
            msg1 = "Halia sucumbiu e foi resgatada ao ultimo checkpoint..."
            msg2 = "Pressione [ENTER] ou clique para reiniciar..."
        else: # FUGIU
            cor_borda = TXT_PENSAMENTO_INTERNO
            titulo = "ESCAPOU"
            msg1 = "Halia recuou com sucesso para um local seguro."
            msg2 = "Pressione [ENTER] ou clique para retornar..."

        pygame.draw.rect(tela, cor_borda, self.rect_banner, 2)

        txt_t = self.fonte_titulo.render(titulo, True, cor_borda)
        tela.blit(txt_t, (rx + (largura_b - txt_t.get_width()) // 2, ry + 35))

        txt_m1 = self.fonte_menu.render(msg1, True, UI_TEXTO_DESTAQUE)
        tela.blit(txt_m1, (rx + (largura_b - txt_m1.get_width()) // 2, ry + 105))

        txt_m2 = self.fonte_status.render(msg2, True, UI_TEXTO_APAGADO)
        tela.blit(txt_m2, (rx + (largura_b - txt_m2.get_width()) // 2, ry + 195))