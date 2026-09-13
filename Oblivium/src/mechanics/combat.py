# src/mechanics/combat.py
import pygame
import random
from src.mechanics.skills import SkillsRegistry
from src.mechanics.conditions import Condicao
from src.entities.Enemy import Enemy
from src.entities.Boss import Boss

class TextoFlutuante:
    """Gerencia números flutuantes de dano, cura ou texto na tela de combate."""
    def __init__(self, texto, x, y, cor=(255, 50, 50), duracao=60, velocidade_y=-1.2):
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
        tela.blit(superficie, (int(self.x), int(self.y)))


class CombatScreen:
    """
    Motor completo de combate por turnos reutilizável, desacoplado de mapas específicos.
    Gerencia fila de iniciativa (DES), menus de ações/magias/itens, IA dos inimigos,
    sistema de condições (DoT/CC), recompensas e callbacks.
    """
    def __init__(self, largura, altura):
        self.largura = largura
        self.altura = altura
        
        # Fontes do Combate
        self.fonte_titulo = pygame.font.Font(None, 40)
        self.fonte_nomes = pygame.font.Font(None, 32)
        self.fonte_status = pygame.font.Font(None, 22)
        self.fonte_menu = pygame.font.Font(None, 28)
        self.fonte_log = pygame.font.Font(None, 24)
        self.fonte_dano = pygame.font.Font(None, 36)
        
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
        self.ordem_turnos = [] # Lista de tuplas (iniciativa, entidade)
        self.indice_turno_atual = 0
        
        # Callbacks
        self.on_vitoria = None
        self.on_derrota = None
        self.on_fuga = None
        
        # Estados do Motor de Combate
        self.estado_combate = "INATIVO"
        # Estados possíveis:
        # "MENU_PRINCIPAL", "SUBMENU_MAGIA", "SELECIONANDO_ALVO",
        # "EXECUTANDO_ACAO", "TURNO_INIMIGO", "VITORIA", "DERROTA", "FUGIU"
        
        # Log e Mensagens de Batalha
        self.historico_log = []
        self.mensagem_atual = ""
        self.timer_acao = 0 # Tempo em frames para ler mensagens
        self.textos_flutuantes = []
        
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
        
        # Notifica jogador
        if hasattr(self.jogador, 'entrar_combate'):
            self.jogador.entrar_combate()

        # Carrega grimório do jogador
        self._carregar_magias_jogador()

        self.adicionar_log("⚔️ A batalha começou!")
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
        inimigos_vivos = [i for i in self.inimigos if getattr(i, 'vivo', True)]
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
                self.adicionar_log(r["mensagem"])
                if r.get("dano", 0) > 0:
                    pos_x = 150 if entidade_atual is self.jogador else (self.largura - 250)
                    pos_y = 250
                    self.adicionar_texto_flutuante(f"-{r['dano']}", pos_x, pos_y, cor=(255, 120, 50))

            # Se a entidade morreu pelo DoT
            if not getattr(entidade_atual, 'vivo', True):
                self.adicionar_log(f"💀 {entidade_atual.nome} foi derrotado!")
                self.indice_turno_atual += 1
                self._avancar_para_proximo_turno()
                return

            # Se a condição impediu a ação (ex: Atordoado/Congelado)
            if impede_acao:
                self.timer_acao = 45
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
        if evento.type != pygame.KEYDOWN:
            return

        # Telas finais aguardam confirmação
        if self.estado_combate in ["VITORIA", "DERROTA", "FUGIU"]:
            if evento.key in [pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE]:
                self._concluir_fechamento_combate()
            return

        # 1. Menu Principal do Jogador
        if self.estado_combate == "MENU_PRINCIPAL":
            if evento.key == pygame.K_UP:
                self.indice_menu = (self.indice_menu - 1) % len(self.opcoes_menu_principal)
            elif evento.key == pygame.K_DOWN:
                self.indice_menu = (self.indice_menu + 1) % len(self.opcoes_menu_principal)
            elif evento.key in [pygame.K_RETURN, pygame.K_SPACE]:
                self._selecionar_opcao_menu_principal()

        # 2. Submenu de Magias
        elif self.estado_combate == "SUBMENU_MAGIA":
            if evento.key == pygame.K_UP:
                self.indice_magia = (self.indice_magia - 1) % len(self.magias_disponiveis)
            elif evento.key == pygame.K_DOWN:
                self.indice_magia = (self.indice_magia + 1) % len(self.magias_disponiveis)
            elif evento.key in [pygame.K_RETURN, pygame.K_SPACE]:
                self._selecionar_magia_grimorio()
            elif evento.key == pygame.K_ESCAPE:
                self.estado_combate = "MENU_PRINCIPAL"

        # 3. Seleção de Alvo Inimigo
        elif self.estado_combate == "SELECIONANDO_ALVO":
            inimigos_vivos = self._obter_inimigos_vivos()
            if not inimigos_vivos: return
            
            if evento.key in [pygame.K_UP, pygame.K_LEFT]:
                self.indice_alvo = (self.indice_alvo - 1) % len(inimigos_vivos)
            elif evento.key in [pygame.K_DOWN, pygame.K_RIGHT]:
                self.indice_alvo = (self.indice_alvo + 1) % len(inimigos_vivos)
            elif evento.key in [pygame.K_RETURN, pygame.K_SPACE]:
                alvo_escolhido = inimigos_vivos[self.indice_alvo]
                self._executar_acao_jogador(self.acao_selecionada, alvo_escolhido)
            elif evento.key == pygame.K_ESCAPE:
                self.estado_combate = "MENU_PRINCIPAL"

    def _selecionar_opcao_menu_principal(self):
        opcao = self.opcoes_menu_principal[self.indice_menu]

        if opcao == "Atacar":
            self.acao_selecionada = SkillsRegistry.get("ataque_basico")
            inimigos_vivos = self._obter_inimigos_vivos()
            if len(inimigos_vivos) == 1:
                self._executar_acao_jogador(self.acao_selecionada, inimigos_vivos[0])
            else:
                self.indice_alvo = 0
                self.estado_combate = "SELECIONANDO_ALVO"

        elif opcao == "Magias":
            self.indice_magia = 0
            self.estado_combate = "SUBMENU_MAGIA"

        elif opcao == "Concentrar":
            acao_foco = SkillsRegistry.get("foco_espiritual")
            self._executar_acao_jogador(acao_foco, self.jogador)

        elif opcao == "Fugir":
            self._tentar_fuga()

    def _selecionar_magia_grimorio(self):
        if not self.magias_disponiveis: return
        magia = self.magias_disponiveis[self.indice_magia]

        if not magia.pode_usar(self.jogador):
            self.adicionar_log(f"⚠️ Mana insuficiente para conjurar {magia.nome} ({self.jogador.mana_atual}/{magia.custo_mana} MP)!")
            return

        self.acao_selecionada = magia
        if magia.alvo_tipo == "PROPRIO":
            self._executar_acao_jogador(magia, self.jogador)
        elif magia.alvo_tipo == "TODOS_INIMIGOS":
            self._executar_acao_jogador(magia, self._obter_inimigos_vivos())
        else:
            inimigos_vivos = self._obter_inimigos_vivos()
            if len(inimigos_vivos) == 1:
                self._executar_acao_jogador(magia, inimigos_vivos[0])
            else:
                self.indice_alvo = 0
                self.estado_combate = "SELECIONANDO_ALVO"

    # =========================================================================
    # EXECUÇÃO DE AÇÕES E IA
    # =========================================================================

    def _executar_acao_jogador(self, acao, alvo):
        """Executa uma ação ou magia escolhida pelo jogador."""
        resultado = acao.executar(self.jogador, alvo)
        
        if not resultado.get("sucesso", False):
            self.adicionar_log(resultado.get("mensagem", "Ação falhou!"))
            return

        # Exibe mensagens e números flutuantes
        for r in resultado.get("resultados", []):
            self.adicionar_log(r["mensagem"])
            alvo_r = r["alvo"]
            
            # Posição do texto flutuante
            if alvo_r is self.jogador:
                pos_x, pos_y = 150, 260
            else:
                pos_x, pos_y = self.largura - 260, 200 + (self.inimigos.index(alvo_r) * 120 if alvo_r in self.inimigos else 0)

            if r.get("dano", 0) > 0:
                cor = (255, 230, 80) if r.get("critico", False) else (255, 60, 60)
                self.adicionar_texto_flutuante(f"-{r['dano']}", pos_x, pos_y, cor=cor)
            elif r.get("cura", 0) > 0:
                self.adicionar_texto_flutuante(f"+{r['cura']}", pos_x, pos_y, cor=(80, 255, 80))
            elif r.get("mana_recuperada", 0) > 0:
                self.adicionar_texto_flutuante(f"+{r['mana_recuperada']} MP", pos_x, pos_y, cor=(80, 180, 255))

        self.timer_acao = 50
        self.estado_combate = "EXECUTANDO_ACAO"

    def _executar_turno_inimigo(self, inimigo):
        """IA simples e inteligente para decisão do inimigo."""
        if not getattr(inimigo, 'vivo', True):
            return

        # Checa fases do Boss
        if isinstance(inimigo, Boss):
            inimigo.verificar_mudanca_fase()

        # Seleciona habilidade
        habilidades_disponiveis = getattr(inimigo, 'habilidades', ["ataque_basico"])
        id_escolhido = random.choice(habilidades_disponiveis)
        acao = SkillsRegistry.get(id_escolhido)
        
        if not acao:
            acao = SkillsRegistry.get("ataque_basico")

        resultado = acao.executar(inimigo, self.jogador)
        
        for r in resultado.get("resultados", []):
            self.adicionar_log(r["mensagem"])
            if r.get("dano", 0) > 0:
                cor = (255, 220, 50) if r.get("critico", False) else (255, 70, 70)
                self.adicionar_texto_flutuante(f"-{r['dano']}", 150, 260, cor=cor)

        self.timer_acao = 50
        self.estado_combate = "EXECUTANDO_ACAO"

    def _tentar_fuga(self):
        """Calcula a probabilidade de fuga baseada na Destreza."""
        inimigos_vivos = self._obter_inimigos_vivos()
        des_inimigos = sum(i.atributos.destreza for i in inimigos_vivos) / max(1, len(inimigos_vivos))
        des_jogador = self.jogador.atributos.destreza
        
        # Chance base de 50% + 4% por ponto de vantagem em Destreza
        chance = max(20.0, min(90.0, 50.0 + (des_jogador - des_inimigos) * 4.0))
        rolagem = random.uniform(0, 100)
        
        if rolagem <= chance:
            self.adicionar_log("🏃 Halia conseguiu escapar da batalha!")
            self.estado_combate = "FUGIU"
        else:
            self.adicionar_log("❌ Tentativa de fuga falhou! Os inimigos bloquearam o caminho.")
            self.timer_acao = 45
            self.estado_combate = "EXECUTANDO_ACAO"

    # =========================================================================
    # ATUALIZAÇÃO DO MOTOR DE COMBATE
    # =========================================================================

    def atualizar(self):
        """Loop de atualização de timers, animações de texto e fluxo de turnos."""
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
                inimigo_atual = self.ordem_turnos[self.indice_turno_atual]
                self._executar_turno_inimigo(inimigo_atual)

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

        self.adicionar_log(f"🏆 VITÓRIA! Recebeu {self.recompensas_vitoria['moedas']} moedas e {self.recompensas_vitoria['memorias']} memórias.")
        self.estado_combate = "VITORIA"

    def _finalizar_derrota(self):
        """Configura estado de derrota."""
        self.adicionar_log("💀 Halia desmaiou e foi derrotada pelas sombras...")
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
    # MÉTODOS UTILITÁRIOS E RENDERIZAÇÃO
    # =========================================================================

    def _obter_inimigos_vivos(self):
        return [i for i in self.inimigos if getattr(i, 'vivo', True)]

    def adicionar_log(self, mensagem):
        self.mensagem_atual = mensagem
        self.historico_log.append(mensagem)
        if len(self.historico_log) > 6:
            self.historico_log.pop(0)

    def adicionar_texto_flutuante(self, texto, x, y, cor=(255, 60, 60)):
        self.textos_flutuantes.append(TextoFlutuante(texto, x, y, cor=cor))

    def desenhar_barra(self, tela, x, y, valor_atual, valor_maximo, cor_barra, cor_fundo=(40, 40, 50), largura=160, altura=14):
        razao = max(0, min(1, valor_atual / valor_maximo)) if valor_maximo > 0 else 0
        largura_atual = int(largura * razao)
        
        pygame.draw.rect(tela, cor_fundo, (x, y, largura, altura))
        pygame.draw.rect(tela, cor_barra, (x, y, largura_atual, altura))
        pygame.draw.rect(tela, (200, 200, 220), (x, y, largura, altura), 1)

    def desenhar(self, tela):
        """Renderiza a arena, participantes, HUDs, menus e textos flutuantes."""
        tela.fill((18, 22, 32))
        
        # Fundo do chão da arena
        pygame.draw.rect(tela, (25, 30, 42), (0, 380, self.largura, self.altura - 380))
        pygame.draw.line(tela, (50, 60, 80), (0, 380), (self.largura, 380), 2)

        # 1. RENDERIZAR INIMIGOS (Lado Direito)
        inimigos_vivos = self._obter_inimigos_vivos()
        for idx, inimigo in enumerate(self.inimigos):
            if not getattr(inimigo, 'vivo', True):
                continue
                
            pos_x = self.largura - 320
            pos_y = 120 + (idx * 130)
            
            # Destaque / Cursor de Seleção de Alvo
            if self.estado_combate == "SELECIONANDO_ALVO" and idx == self.indice_alvo:
                cursor_txt = self.fonte_titulo.render("▶", True, (255, 230, 80))
                tela.blit(cursor_txt, (pos_x - 35, pos_y + 10))

            # Renderiza Imagem ou Bloco Colorido
            imagem = getattr(inimigo, 'imagem_atual', None)
            if imagem:
                img_combate = pygame.transform.scale(imagem, (inimigo.largura * 2, inimigo.altura * 2))
                tela.blit(img_combate, (pos_x, pos_y))
            else:
                rect_inimigo = pygame.Rect(pos_x, pos_y, getattr(inimigo, 'largura', 40) * 2, getattr(inimigo, 'altura', 40) * 2)
                pygame.draw.rect(tela, getattr(inimigo, 'cor', (150, 30, 50)), rect_inimigo)
                pygame.draw.rect(tela, (255, 255, 255), rect_inimigo, 2)

            # Nome e Condições
            texto_nome = self.fonte_nomes.render(inimigo.nome, True, (255, 120, 120))
            tela.blit(texto_nome, (pos_x, pos_y - 28))
            
            # Ícones de Condições ativas
            icones_cond = " ".join([c.icone for c in getattr(inimigo, 'condicoes', [])])
            if icones_cond:
                txt_icones = self.fonte_status.render(icones_cond, True, (255, 220, 100))
                tela.blit(txt_icones, (pos_x + texto_nome.get_width() + 8, pos_y - 25))

            # Barra de Vida
            self.desenhar_barra(tela, pos_x, pos_y + (getattr(inimigo, 'altura', 40) * 2) + 8, inimigo.vida_atual, inimigo.vida_maxima, (210, 45, 45))
            txt_hp = self.fonte_status.render(f"{inimigo.vida_atual}/{inimigo.vida_maxima}", True, (240, 240, 240))
            tela.blit(txt_hp, (pos_x + 165, pos_y + (getattr(inimigo, 'altura', 40) * 2) + 6))

        # 2. RENDERIZAR HALIA (Lado Esquerdo)
        halia_x, halia_y = 140, 240
        img_halia = getattr(self.jogador, 'imagem_atual', None)
        if img_halia:
            img_c = pygame.transform.scale(img_halia, (self.jogador.largura * 2, self.jogador.altura * 2))
            tela.blit(img_c, (halia_x, halia_y))
        else:
            rect_h = pygame.Rect(halia_x, halia_y, 75, 95)
            pygame.draw.rect(tela, (34, 139, 34), rect_h)
            pygame.draw.rect(tela, (200, 255, 200), rect_h, 2)

        txt_halia = self.fonte_nomes.render(self.jogador.nome, True, (120, 255, 120))
        tela.blit(txt_halia, (halia_x, halia_y - 35))
        
        # Ícones de Condições da Halia
        icones_h = " ".join([c.icone for c in getattr(self.jogador, 'condicoes', [])])
        if icones_h:
            txt_ic_h = self.fonte_status.render(icones_h, True, (255, 220, 100))
            tela.blit(txt_ic_h, (halia_x + txt_halia.get_width() + 8, halia_y - 32))

        # Barras de HP e MP da Halia
        self.desenhar_barra(tela, halia_x, halia_y + 105, self.jogador.vida_atual, self.jogador.vida_maxima, (50, 200, 70), largura=180)
        tela.blit(self.fonte_status.render(f"HP {self.jogador.vida_atual}/{self.jogador.vida_maxima}", True, (255, 255, 255)), (halia_x + 190, halia_y + 103))

        self.desenhar_barra(tela, halia_x, halia_y + 125, self.jogador.mana_atual, self.jogador.mana_maxima, (50, 120, 230), largura=180)
        tela.blit(self.fonte_status.render(f"MP {self.jogador.mana_atual}/{self.jogador.mana_maxima}", True, (255, 255, 255)), (halia_x + 190, halia_y + 123))

        # 3. CAIXA INFERIOR DE MENUS E LOGS
        altura_painel = 210
        painel_rect = pygame.Rect(30, self.altura - altura_painel - 20, self.largura - 60, altura_painel)
        pygame.draw.rect(tela, (12, 15, 22), painel_rect)
        pygame.draw.rect(tela, (70, 80, 100), painel_rect, 2)

        # Divisão Interna: Menu à Esquerda (Largura 300) | Log à Direita
        largura_menu = 320
        pygame.draw.line(tela, (50, 60, 80), (painel_rect.x + largura_menu, painel_rect.y), (painel_rect.x + largura_menu, painel_rect.bottom), 2)

        # RENDERIZAR MENU ATIVO
        if self.estado_combate == "MENU_PRINCIPAL":
            for i, opcao in enumerate(self.opcoes_menu_principal):
                cor = (255, 230, 80) if i == self.indice_menu else (200, 200, 210)
                marcador = "▶ " if i == self.indice_menu else "   "
                txt = self.fonte_menu.render(f"{marcador}{opcao}", True, cor)
                tela.blit(txt, (painel_rect.x + 25, painel_rect.y + 25 + (i * 40)))

        elif self.estado_combate == "SUBMENU_MAGIA":
            txt_voltar = self.fonte_status.render("[ESC] Voltar", True, (160, 160, 180))
            tela.blit(txt_voltar, (painel_rect.x + 20, painel_rect.y + 10))
            
            for i, magia in enumerate(self.magias_disponiveis):
                cor = (255, 230, 80) if i == self.indice_magia else (200, 200, 210)
                marcador = "▶ " if i == self.indice_magia else "   "
                custo_txt = f"({magia.custo_mana} MP)" if magia.custo_mana > 0 else "(Grátis)"
                txt = self.fonte_menu.render(f"{marcador}{magia.nome} {custo_txt}", True, cor)
                tela.blit(txt, (painel_rect.x + 20, painel_rect.y + 35 + (i * 38)))

        elif self.estado_combate == "SELECIONANDO_ALVO":
            txt_alvo = self.fonte_menu.render("Selecione o Alvo:", True, (255, 230, 80))
            tela.blit(txt_alvo, (painel_rect.x + 25, painel_rect.y + 30))
            
            inimigos_vivos = self._obter_inimigos_vivos()
            for i, inimigo in enumerate(inimigos_vivos):
                cor = (255, 230, 80) if i == self.indice_alvo else (180, 180, 190)
                marcador = "▶ " if i == self.indice_alvo else "   "
                txt_i = self.fonte_status.render(f"{marcador}{inimigo.nome} ({inimigo.vida_atual} HP)", True, cor)
                tela.blit(txt_i, (painel_rect.x + 25, painel_rect.y + 70 + (i * 30)))

        # RENDERIZAR COMBAT LOG (Lado Direito)
        pos_log_x = painel_rect.x + largura_menu + 25
        pos_log_y = painel_rect.y + 20
        
        txt_cabecalho_log = self.fonte_status.render("HISTÓRICO DE COMBATE", True, (130, 140, 160))
        tela.blit(txt_cabecalho_log, (pos_log_x, pos_log_y))
        
        for idx, linha in enumerate(self.historico_log[-5:]):
            cor_linha = (255, 255, 255) if idx == len(self.historico_log[-5:]) - 1 else (170, 175, 190)
            txt_linha = self.fonte_log.render(linha, True, cor_linha)
            tela.blit(txt_linha, (pos_log_x, pos_log_y + 28 + (idx * 28)))

        # 4. RENDERIZAR NÚMEROS FLUTUANTES
        for tf in self.textos_flutuantes:
            tf.desenhar(tela, self.fonte_dano)

        # 5. TELAS ESPECIAIS (Banners de Vitória, Derrota e Fuga)
        if self.estado_combate in ["VITORIA", "DERROTA", "FUGIU"]:
            self._desenhar_banner_fim_combate(tela)

    def _desenhar_banner_fim_combate(self, tela):
        overlay = pygame.Surface((self.largura, self.altura), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 190))
        tela.blit(overlay, (0, 0))

        largura_b, altura_b = 640, 300
        rx = (self.largura - largura_b) // 2
        ry = (self.altura - altura_b) // 2
        
        pygame.draw.rect(tela, (20, 25, 35), (rx, ry, largura_b, altura_b))
        
        if self.estado_combate == "VITORIA":
            cor_borda = (80, 220, 100)
            titulo = "VITÓRIA!"
            msg1 = f"Recompensas: +{self.recompensas_vitoria['moedas']} Moedas | +{self.recompensas_vitoria['memorias']} Memória(s)"
            msg2 = "Pressione [ENTER] ou [ESPAÇO] para continuar..."
        elif self.estado_combate == "DERROTA":
            cor_borda = (220, 60, 60)
            titulo = "DERROTA"
            msg1 = "Halia sucumbiu às sombras e foi resgatada ao checkpoint..."
            msg2 = "Pressione [ENTER] para reiniciar..."
        else: # FUGIU
            cor_borda = (220, 200, 60)
            titulo = "ESCAPOU"
            msg1 = "Halia recuou com sucesso para um local seguro."
            msg2 = "Pressione [ENTER] para retornar..."

        pygame.draw.rect(tela, cor_borda, (rx, ry, largura_b, altura_b), 3)

        txt_t = self.fonte_titulo.render(titulo, True, cor_borda)
        tela.blit(txt_t, (rx + (largura_b - txt_t.get_width()) // 2, ry + 40))

        txt_m1 = self.fonte_menu.render(msg1, True, (240, 240, 240))
        tela.blit(txt_m1, (rx + (largura_b - txt_m1.get_width()) // 2, ry + 120))

        txt_m2 = self.fonte_status.render(msg2, True, (180, 180, 180))
        tela.blit(txt_m2, (rx + (largura_b - txt_m2.get_width()) // 2, ry + 220))