# src/mechanics/cutscene_manager.py
import pygame

class CutsceneManager:
    def __init__(self, game):
        self.game = game
        
    def atualizar_magia(self):
        if self.game.magia_ativa is None or self.game.magia_ativa == "CONCLUIDO":
            return

        if self.game.distanciando_halia:
            if self.game.halia.x > 850:
                self.game.halia.x -= 4
                self.game.halia.virado_direita = False
                self.game.halia.direcao = "esquerda"
                self.game.halia.mudar_estado("andar")
                self.game.halia.atualizar_animacao()
            else:
                self.game.distanciando_halia = False
                self.game.halia.virado_direita = True
                self.game.halia.direcao = "direita"
                self.game.halia.mudar_estado("idle")
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
                self.game.mapa_casa.desobstruir_estrada("FOGO")
                self.game.caixa_dialogo.iniciar_dialogo("pos_fogo")
                self.game.magia_ativa = "CONCLUIDO"
                self.game.conversa_combate_ativa = True

    def _processar_levitacao(self):
        if self.game.timer_magia < 50:
            if hasattr(self.game.mapa_casa, 'pedras_deslizamento'):
                for idx, pedra in enumerate(self.game.mapa_casa.pedras_deslizamento):
                    if idx % 2 == 0: pedra.y -= 3; pedra.x += 1
                    else: pedra.y += 3; pedra.x += 1
        else:
            self.game.mapa_casa.desobstruir_estrada("LEVITAR")
            self.game.caixa_dialogo.iniciar_dialogo("pos_levitar")
            self.game.magia_ativa = "CONCLUIDO"
            self.game.conversa_combate_ativa = True

    def desenhar_efeitos(self, tela):
        if self.game.mapa_casa.cenario_atual == "ESTRADA_2" and self.game.bola_fogo_ativa:
            pygame.draw.circle(tela, (240, 40, 10), (int(self.game.bola_fogo_x), int(self.game.bola_fogo_y)), 20)
            pygame.draw.circle(tela, (255, 130, 0), (int(self.game.bola_fogo_x), int(self.game.bola_fogo_y)), 13)
            pygame.draw.circle(tela, (255, 240, 100), (int(self.game.bola_fogo_x), int(self.game.bola_fogo_y)), 6)