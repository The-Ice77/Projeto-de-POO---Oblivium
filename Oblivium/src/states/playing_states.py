# src/states/playing_states.py
import pygame
import copy
from src.states.states import State
from src.entities.Enemy import Enemy
from src.mechanics.cutscene_manager import CutsceneManager
from src.utils.colors import INDICADOR_INTERACAO
from data.dialogos import *

class PlayingState(State):
    def __init__(self, game):
        super().__init__(game)
        self.game = game
        self.cutscene = CutsceneManager(game)

    def handle_events(self, eventos, teclas):
        self._processar_movimento(teclas)
        
        for evento in eventos:
            if evento.type == pygame.MOUSEMOTION:
                self.game.caixa_dialogo.atualizar_mouse(evento.pos)
                continue
            
            if evento.type == pygame.KEYDOWN:
                self._handle_keydown(evento)
            elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                self._handle_clicks(evento.pos)

    def update(self):
        # --- NOVO: Adiciona o tempo decorrido ao tempo jogado (1/60 de segundo) ---
        self.game.tempo_jogado += 1 / 60.0
        
        self.game.caixa_dialogo.atualizar()
        self.cutscene.atualizar_magia()
        self._update_minigames_e_flashbacks()
        self._update_inimigos_e_triggers()
        self._update_transitions()

        if self.game.caixa_dialogo.opcao_cancelada_id in ["voltar_magia", "desistir_puzzle"]:
            self.game.investigou_pedras = False
            self.game.caixa_dialogo.opcao_cancelada_id = None
    def draw(self, tela):
        self.game.mapa_casa.desenhar(tela)
        self._draw_interactable_prompts(tela)
        
        self.game.carroceiro.desenhar(tela) if self.game.carroceiro_visivel else None
        self.game.halia.desenhar(tela)
        
        for inimigo in self.game.inimigos_em_cena:
            inimigo.desenhar(tela)
            
        self.cutscene.desenhar_efeitos(tela)
        self._draw_ui_overlays(tela)

    def _processar_movimento(self, teclas):
        if self.game.caixa_dialogo.ativo or self.game.transicao.estado != "INATIVO" or \
           self.game.flashback_sistema.estado != "INATIVO" or (self.game.magia_ativa is not None and self.game.magia_ativa != "CONCLUIDO") or \
           self.game.mg_timing.ativo or self.game.mg_mash.ativo or self.game.cena_inimigos_andando:
            return
            
        dx, dy = 0, 0
        if teclas[self.game.controles["Cima"]]: dy = -1
        if teclas[self.game.controles["Baixo"]]: dy = 1
        if teclas[self.game.controles["Esquerda"]]: dx = -1
        if teclas[self.game.controles["Direita"]]: dx = 1
        
        if dx != 0 or dy != 0:
            velocidade_original = self.game.halia.velocidade
            if teclas[self.game.controles["Correr"]]:
                self.game.halia.velocidade = velocidade_original * 1.8
                
            # --- CORREÇÃO DE COLISÃO DO CARROCEIRO ---
            hitboxes_atuais = list(self.game.mapa_casa.hitboxes) # Copia as paredes do mapa
            
            # Adiciona o carroceiro como parede se ele estiver na tela
            if self.game.carroceiro_visivel:
                rect_carroceiro = pygame.Rect(
                    int(self.game.carroceiro.x), 
                    int(self.game.carroceiro.y), 
                    self.game.carroceiro.largura, 
                    self.game.carroceiro.altura
                )
                hitboxes_atuais.append(rect_carroceiro)
            
            self.game.halia.mover(dx, dy, hitboxes_atuais)
            self.game.halia.velocidade = velocidade_original

    def _handle_keydown(self, evento):
        if evento.key == self.game.controles["Pause"]:
            if not self.game.caixa_dialogo.ativo and self.game.transicao.estado == "INATIVO":
                self.game.mudar_estado("PAUSE")
                return

        if self.game.mg_timing.ativo and evento.key == pygame.K_SPACE:
            self._checar_sucesso_timing()
        elif self.game.mg_mash.ativo and evento.key == pygame.K_SPACE:
            self.game.mg_mash.esmagar()
        elif self.game.flashback_sistema.estado == "ESCURIDAO" and evento.key == pygame.K_RETURN:
            self.game.flashback_sistema.processar_input()
        elif self.game.caixa_dialogo.ativo:
            if self.game.caixa_dialogo.em_escolha and evento.key in [pygame.K_UP, pygame.K_DOWN]:
                self.game.caixa_dialogo.controlar_menu_escolhas(evento.key)
            elif evento.key == pygame.K_RETURN:
                self._processar_avanco_dialogo()
        elif evento.key == self.game.controles["Interagir"] and not self.game.cena_inimigos_andando:
            self._processar_interacoes_mundo()

    def _handle_clicks(self, pos):
        if self.game.flashback_sistema.estado == "ESCURIDAO":
            self.game.flashback_sistema.processar_input()
        elif self.game.caixa_dialogo.em_escolha:
            self._processar_clique_escolha(pos)
        elif self.game.caixa_dialogo.ativo:
            self.game.caixa_dialogo.proximo_texto()

    def _checar_sucesso_timing(self):
        if self.game.mg_timing.checar_sucesso():
            self.game.magia_ativa = "FOGO"
            self.game.distanciando_halia = True
            self.game.timer_magia = 0
        else:
            self.game.caixa_dialogo.iniciar_dialogo(copy.deepcopy(dialogo_falha_timing))

    def _update_minigames_e_flashbacks(self):
        if self.game.flashback_sistema.atualizar():
            self.game.flashback_magia_concluido = True 
            self.game.caixa_dialogo.iniciar_dialogo([copy.deepcopy(no_escolhas_magias)])

        if self.game.mg_timing.ativo:
            self.game.mg_timing.atualizar()
        elif self.game.mg_mash.ativo:
            res = self.game.mg_mash.atualizar()
            if res == "VENCEU":
                self.game.magia_ativa = "LEVITAR"
                self.game.distanciando_halia = True
                self.game.timer_magia = 0
            elif res == "PERDEU":
                self.game.caixa_dialogo.iniciar_dialogo(copy.deepcopy(dialogo_falha_mash))

        if self.game.mapa_casa.cenario_atual == "ESTRADA_2" and self.game.investigou_pedras and not self.game.caixa_dialogo.ativo and self.game.magia_ativa is None and not self.game.mg_timing.ativo and not self.game.mg_mash.ativo:
            if self.game.magia_selecionada_temporaria == "FOGO":
                self.game.magia_selecionada_temporaria = None
                self.game.mg_timing.iniciar()
            elif self.game.magia_selecionada_temporaria == "LEVITAR":
                self.game.magia_selecionada_temporaria = None
                self.game.mg_mash.iniciar()

    def _update_inimigos_e_triggers(self):
        if self.game.conversa_combate_ativa and not self.game.caixa_dialogo.ativo:
            self.game.conversa_combate_ativa = False
            self.game.cena_inimigos_andando = True
            if self.game.magia_usada_no_puzzle == "FOGO":
                self.game.inimigos_em_cena.append(Enemy("Sombra 1", 30, 2, 1220, 290, None, 5, True))
                self.game.inimigos_em_cena.append(Enemy("Sombra 2", 30, 2, 1220, 380, None, 5, True))
            elif self.game.magia_usada_no_puzzle == "LEVITAR":
                boss = Enemy("Anomalia Maior", 80, 1.5, 1200, 310, None, 15, True)
                boss.largura, boss.altura = 55, 75
                self.game.inimigos_em_cena.append(boss)

        if self.game.cena_inimigos_andando:
            for inimigo in self.game.inimigos_em_cena:
                inimigo.atualizar_movimento_mapa(self.game.halia.x, self.game.halia.y)
                r_inimigo = pygame.Rect(int(inimigo.x), int(inimigo.y), inimigo.largura, inimigo.altura)
                r_halia = pygame.Rect(int(self.game.halia.x), int(self.game.halia.y), self.game.halia.largura, self.game.halia.altura)
                if r_inimigo.colliderect(r_halia) and not self.game.iniciando_combate:
                    self.game.iniciando_combate = True
                    self.game.transicao.iniciar()

        self._check_map_zone_triggers()

    def _check_map_zone_triggers(self):
        if self.game.caixa_dialogo.ativo or self.game.transicao.estado != "INATIVO" or self.game.cena_inimigos_andando:
            return

        if self.game.mapa_casa.cenario_atual == "CASA" and self.game.mapa_casa.porta_aberta and self.game.halia.x > 580:
            self.game.mapa_casa.porta_aberta = False; self.game.halia.x = 550; self.game.fechando_porta = True
            self.game.caixa_dialogo.iniciar_dialogo(copy.deepcopy(dialogo_fechar_porta))
            
        if self.game.fechando_porta and not self.game.caixa_dialogo.ativo:
            self.game.fechando_porta = False
            self.game.transicao.iniciar("Seguindo viagem...")

        if self.game.mapa_casa.cenario_atual == "ESTRADA" and not self.game.carroceiro_visivel and self.game.halia.x > 640:
            self.game.carroceiro_visivel = True; self.game.carroceiro_andando = True
            self.game.caixa_dialogo.iniciar_dialogo(copy.deepcopy(dialogo_avistar_carroceiro))

        if self.game.mapa_casa.cenario_atual == "ESTRADA_2" and not self.game.investigou_pedras and self.game.halia.x > 1000:
            self.game.investigou_pedras = True; self.game.halia.x = 980
            self.game.caixa_dialogo.iniciar_dialogo([copy.deepcopy(no_escolhas_magias)]) if self.game.flashback_magia_concluido else self.game.caixa_dialogo.iniciar_dialogo(copy.deepcopy(dialogo_investigar_pedras))

        if self.game.carroceiro_andando:
            self._mover_carroceiro_autonomo()

        if self.game.mapa_casa.cenario_atual == "ESTRADA" and self.game.aguardando_fim_viagem and not self.game.caixa_dialogo.ativo:
            self.game.aguardando_fim_viagem = False; self.game.conversa_carroceiro_terminou = True
            self.game.transicao.iniciar("Algumas horas depois...")

    def _mover_carroceiro_autonomo(self):
        next_h = pygame.Rect(int(self.game.carroceiro.x - 2), int(self.game.carroceiro.y), self.game.carroceiro.largura, self.game.carroceiro.altura)
        h_halia = pygame.Rect(int(self.game.halia.x), int(self.game.halia.y), self.game.halia.largura, self.game.halia.altura)
        if not next_h.colliderect(h_halia): self.game.carroceiro.mover(-1, 0)
        if self.game.carroceiro.x <= 900 or next_h.colliderect(h_halia):
            if self.game.carroceiro.x <= 900: self.game.carroceiro.x = 900
            self.game.carroceiro_andando = False; self.game.carroceiro.velocidade = 0
            h_npc = pygame.Rect(int(self.game.carroceiro.x), int(self.game.carroceiro.y), self.game.carroceiro.largura, self.game.carroceiro.altura)
            if h_npc not in self.game.mapa_casa.hitboxes: self.game.mapa_casa.hitboxes.append(h_npc)

    def _processar_avanco_dialogo(self):
        if self.game.caixa_dialogo.em_escolha:
            opcao_atual = self.game.caixa_dialogo.opcoes_disponiveis[self.game.caixa_dialogo.opcao_selecionada]
            if opcao_atual["id"] == "analisar_pedras":
                self.game.caixa_dialogo.ativo = False
                self.game.caixa_dialogo.em_escolha = False
                self.game.flashback_sistema.iniciar(textos_flashback_magia)
                return
            elif opcao_atual["id"] == "escolha_fogo":
                self.game.magia_selecionada_temporaria = "FOGO"
            elif opcao_atual["id"] == "escolha_levitar":
                self.game.magia_selecionada_temporaria = "LEVITAR"
            elif opcao_atual["id"] == "voltar_magia" or opcao_atual["id"] == "desistir_puzzle":
                self.game.investigou_pedras = False
            if opcao_atual["id"] == "prosseguir":
                self.game.aguardando_fim_viagem = True
        self.game.caixa_dialogo.proximo_texto()

    def _processar_clique_escolha(self, pos):
        for i, r in enumerate(self.game.caixa_dialogo.rects_opcoes):
            if r.collidepoint(pos):
                opcao = self.game.caixa_dialogo.opcoes_disponiveis[i]
                if opcao["id"] == "analisar_pedras":
                    self.game.caixa_dialogo.ativo = False
                    self.game.caixa_dialogo.em_escolha = False
                    self.game.flashback_sistema.iniciar(textos_flashback_magia)
                    return
                elif opcao["id"] == "escolha_fogo":
                    self.game.magia_selecionada_temporaria = "FOGO"
                elif opcao["id"] == "escolha_levitar":
                    self.game.magia_selecionada_temporaria = "LEVITAR"
                elif opcao["id"] == "voltar_magia" or opcao["id"] == "desistir_puzzle":
                    self.game.investigou_pedras = False
                if opcao["id"] == "prosseguir":
                    self.game.aguardando_fim_viagem = True
        self.game.caixa_dialogo.clicar_mouse(pos)

    def _processar_interacoes_mundo(self):
        area_interacao = pygame.Rect(self.game.halia.x - 20, self.game.halia.y - 20, self.game.halia.largura + 40, self.game.halia.altura + 40)
        
        for indice, item in enumerate(self.game.mapa_casa.itens_no_chao[:]): 
            if area_interacao.colliderect(item.rect):
                self.game.mapa_casa.itens_no_chao.remove(item)
                
                # Registo por índice fixo da sala (Infalível contra bugs de coordenadas)
                id_unico = f"{self.game.mapa_casa.cenario_atual}_item_{indice}"
                if id_unico not in self.game.itens_coletados:
                    self.game.itens_coletados.append(id_unico)
                    
                self.game.caixa_dialogo.iniciar_dialogo([{"autor": "Sistema", "texto": f"Você guardou: {item.nome}."}])
                return
        
        
        if self.game.mapa_casa.cenario_atual == "CASA" and area_interacao.colliderect(self.game.mapa_casa.porta) and not self.game.mapa_casa.porta_aberta:
            if len(self.game.mapa_casa.itens_no_chao) == 0:
                self.game.mapa_casa.abrir_porta()
                self.game.caixa_dialogo.iniciar_dialogo(copy.deepcopy(dialogo_porta_abriu))
            else:
                self.game.caixa_dialogo.iniciar_dialogo(copy.deepcopy(dialogo_porta_trancada))
            return

        if self.game.mapa_casa.cenario_atual in ["ESTRADA", "ESTRADA_2"] and self.game.carroceiro_visivel:
            if area_interacao.colliderect(pygame.Rect(self.game.carroceiro.x, self.game.carroceiro.y, self.game.carroceiro.largura, self.game.carroceiro.altura)):
                if self.game.mapa_casa.cenario_atual == "ESTRADA":
                    self.game.caixa_dialogo.iniciar_dialogo(copy.deepcopy(dialogo_hub_carroceiro))
                elif self.game.mapa_casa.cenario_atual == "ESTRADA_2":
                    if self.game.magia_ativa == "CONCLUIDO":
                        self.game.caixa_dialogo.iniciar_dialogo(copy.deepcopy(dialogo_carroceiro_pos_puzzle))
                    else:
                        self.game.caixa_dialogo.iniciar_dialogo(copy.deepcopy(dialogo_carroceiro_impedimento))

    def _update_transitions(self):
        if self.game.transicao.update() if hasattr(self.game.transicao, 'update') else self.game.transicao.atualizar():
            if self.game.iniciando_combate:
                self.game.iniciando_combate = False
                self.game.transicao.estado = "CLAREANDO"
                self.game.mudar_estado("COMBATE")
                self.game.tela_combate.iniciar_combate(self.game.halia, self.game.inimigos_em_cena)
            elif self.game.mapa_casa.cenario_atual == "CASA":
                self._entrar_na_estrada_1()
            elif self.game.mapa_casa.cenario_atual == "ESTRADA":
                self._entrar_na_estrada_2()

    def _entrar_na_estrada_1(self):
        self.game.mapa_casa.carregar_cenario("ESTRADA")
        self.game.halia.x, self.game.halia.y = 40, 330
        pygame.event.clear()
        self.game.caixa_dialogo.iniciar_dialogo(copy.deepcopy(dialogo_entrada_estrada1))
        self.game.transicao.estado = "CLAREANDO"

    def _entrar_na_estrada_2(self):
        self.game.mapa_casa.carregar_cenario("ESTRADA_2")
        self.game.conversa_carroceiro_terminou = False; self.game.aguardando_fim_viagem = False
        self.game.magia_ativa = None; self.game.bola_fogo_ativa = False; self.game.cena_inimigos_andando = False
        self.game.inimigos_em_cena.clear()
        
        self.game.halia.x, self.game.halia.y = 60, 330
        self.game.carroceiro_visivel, self.game.carroceiro_andando = True, False
        self.game.carroceiro.velocidade, self.game.carroceiro.x, self.game.carroceiro.y = 0, 200, 330
        
        h_npc = pygame.Rect(int(self.game.carroceiro.x), int(self.game.carroceiro.y), self.game.carroceiro.largura, self.game.carroceiro.altura)
        if h_npc not in self.game.mapa_casa.hitboxes: self.game.mapa_casa.hitboxes.append(h_npc)
        
        pygame.event.clear()
        self.game.caixa_dialogo.iniciar_dialogo(copy.deepcopy(dialogo_entrada_estrada2))
        self.game.transicao.estado = "CLAREANDO"

    def _draw_interactable_prompts(self, tela):
        area_interacao = pygame.Rect(self.game.halia.x - 20, self.game.halia.y - 20, self.game.halia.largura + 40, self.game.halia.altura + 40)
        
        if self.game.mapa_casa.cenario_atual == "CASA" and not self.game.caixa_dialogo.ativo:
            for item in self.game.mapa_casa.itens_no_chao:
                if area_interacao.colliderect(item.rect):
                    txt = self.game.fonte_indicador.render(f"[{pygame.key.name(self.game.controles['Interagir']).upper()}] Pegar", True, INDICADOR_INTERACAO)
                    tela.blit(txt, (item.x + (item.largura // 2) - (txt.get_width() // 2), item.y - 20))
                    break 
            if area_interacao.colliderect(self.game.mapa_casa.porta) and not self.game.mapa_casa.porta_aberta:
                txt = self.game.fonte_indicador.render(f"[{pygame.key.name(self.game.controles['Interagir']).upper()}] Abrir Porta", True, INDICADOR_INTERACAO)
                tela.blit(txt, (self.game.mapa_casa.porta.x + (self.game.mapa_casa.porta.width // 2) - (txt.get_width() // 2), self.game.mapa_casa.porta.y - 20))

        if self.game.mapa_casa.cenario_atual in ["ESTRADA", "ESTRADA_2"] and self.game.carroceiro_visivel:
            r_c = pygame.Rect(self.game.carroceiro.x, self.game.carroceiro.y, self.game.carroceiro.largura, self.game.carroceiro.altura)
            if area_interacao.colliderect(r_c) and not self.game.caixa_dialogo.ativo and self.game.flashback_sistema.estado == "INATIVO" and not self.game.mg_timing.ativo and not self.game.mg_mash.ativo and not self.game.cena_inimigos_andando:
                txt = self.game.fonte_indicador.render(f"[{pygame.key.name(self.game.controles['Interagir']).upper()}] Conversar", True, INDICADOR_INTERACAO)
                tela.blit(txt, (self.game.carroceiro.x + (self.game.carroceiro.largura // 2) - (txt.get_width() // 2), self.game.carroceiro.y - 25))

    def _draw_ui_overlays(self, tela):
        self.game.mg_timing.desenhar(tela)
        self.game.mg_mash.desenhar(tela)
        self.game.transicao.desenhar(tela)
        self.game.caixa_dialogo.desenhar(tela)
        self.game.flashback_sistema.desenhar(tela)