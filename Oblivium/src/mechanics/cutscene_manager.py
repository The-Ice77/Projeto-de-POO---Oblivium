# src/mechanics/cutscene_manager.py
import pygame
import copy
from data.dialogos import conversa_pos_fogo, conversa_pos_levitar

class CutsceneManager:
    def __init__(self, game):
        self.game = game
        
    def atualizar_magia(self):
        if self.game.magia_ativa is None or self.game.magia_ativa == "CONCLUIDO":
            return

        if self.game.distanciando_halia:
            if self.game.halia.x > 850:
                self.game.halia.x -= 4
            else:
                self.game.distanciando_halia = False
                if self.game.magia_ativa == "FOGO":
                    self.game.magia_usada_no_puzzle = "FOGO"
                    self.game.bola_fogo_ativa = True
                    self.game.bola_fogo_x = self.game.halia.x + self.game.halia.largura + 10
                    self.game.bola_fogo_y = self.game.halia.y + (self.game.halia.altura // 2)
                elif self.game.magia_ativa == "LEVITAR":
                    self.game.magia_usada_no_puzzle = "LEVITAR"
        else:
            self.game.timer_magia += 1
            if self.game.magia_ativa == "FOGO":
                self._processar_fogo()
            elif self.game.magia_ativa == "LEVITAR":
                self._processar_levitacao()

    def _processar_fogo(self):
        if self.game.bola_fogo_ativa:
            self.game.bola_fogo_x += 14
            if self.game.bola_fogo_x >= 1100:
                self.game.bola_fogo_ativa = False
                if hasattr(self.game.mapa_casa, 'pedras_deslizamento'):
                    for p in self.game.mapa_casa.pedras_deslizamento:
                        if p in self.game.mapa_casa.hitboxes: 
                            self.game.mapa_casa.hitboxes.remove(p)
                    self.game.mapa_casa.pedras_deslizamento = [
                        pygame.Rect(1110, 430, 20, 15), 
                        pygame.Rect(1160, 440, 25, 20), 
                        pygame.Rect(1090, 450, 15, 12)
                    ]
                dialogo_completo = [{"autor": "Narrador", "texto": "BOOM! A bola de fogo estilhaça o bloqueio em mil pedaços."}] + copy.deepcopy(conversa_pos_fogo)
                self.game.caixa_dialogo.iniciar_dialogo(dialogo_completo)
                self.game.magia_ativa = "CONCLUIDO"
                self.game.conversa_combate_ativa = True

    def _processar_levitacao(self):
        if self.game.timer_magia <= 60:
            if hasattr(self.game.mapa_casa, 'pedras_deslizamento'):
                for idx, pedra in enumerate(self.game.mapa_casa.pedras_deslizamento):
                    if idx % 2 == 0: pedra.y -= 3; pedra.x += 1
                    else: pedra.y += 3; pedra.x += 1
        elif self.game.timer_magia == 61:
            for p in self.game.mapa_casa.pedras_deslizamento:
                if p in self.game.mapa_casa.hitboxes: 
                    self.game.mapa_casa.hitboxes.remove(p)
            dialogo_completo = [{"autor": "Narrador", "texto": "Com um gesto suave, as pedras erguem-se no ar e organizam-se nas margens da estrada."}] + copy.deepcopy(conversa_pos_levitar)
            self.game.caixa_dialogo.iniciar_dialogo(dialogo_completo)
            self.game.magia_ativa = "CONCLUIDO"
            self.game.conversa_combate_ativa = True

    def desenhar_efeitos(self, tela):
        if self.game.mapa_casa.cenario_atual == "ESTRADA_2" and self.game.bola_fogo_ativa:
            pygame.draw.circle(tela, (240, 40, 10), (int(self.game.bola_fogo_x), int(self.game.bola_fogo_y)), 20)
            pygame.draw.circle(tela, (255, 130, 0), (int(self.game.bola_fogo_x), int(self.game.bola_fogo_y)), 13)
            pygame.draw.circle(tela, (255, 240, 100), (int(self.game.bola_fogo_x), int(self.game.bola_fogo_y)), 6)