# src/ui/quest_tracker.py
import pygame
from src.utils.colors import (
    CARVAO_PROFUNDO, CINZA_LINHO, CINZA_ARDOSIA,
    MARFIM_OFFWHITE, UI_TEXTO_APAGADO
)
from src.utils.resource_manager import ResourceManager
from src.ui.ui_utils import desenhar_painel_padrao


class QuestTracker:
    """
    HUD Tracker de Missões no Canto Superior Direito da Tela.

    Características:
    - Exibição compacta, editorial e elegante da missão ativamente rastreada.
    - Exibe o título da missão e a checklist com progresso dos objetivos.
    - Suporte a recolhimento/expansão com clique no botão [-] / [+] ou atalho [J].
    - Transparência dinâmica (Fade de Proximidade): atenua o alpha suavemente
      caso a protagonista Halia se aproxime da zona superior direita da tela.
    - Oculta-se automaticamente quando não há missões ativas em andamento.
    """

    def __init__(self, largura_tela=1280, altura_tela=720):
        self.largura_tela = largura_tela
        self.altura_tela = altura_tela

        # Dimensões e posicionamento fixo no canto superior direito
        self.largura_box = 275
        self.x = self.largura_tela - self.largura_box - 24
        self.y = 22

        # Tipografia Editorial Dark Fantasy
        self.fonte_cabecalho = ResourceManager.carregar_fonte("sunday", 16)
        self.fonte_titulo = ResourceManager.carregar_fonte("contrail", 15)
        self.fonte_objetivo = ResourceManager.carregar_fonte("contrail", 13)
        self.fonte_mini = ResourceManager.carregar_fonte("contrail", 12)

        # Estado de Expansão e Hover
        self.expandido = True
        self.rect_botao_toggle = pygame.Rect(0, 0, 0, 0)
        self.rect_painel = pygame.Rect(0, 0, 0, 0)
        self.hover_toggle = False

        # Controle de Fade por Proximidade
        self.alpha_atual = 255

    def toggle_expandir(self):
        """Alterna entre modo expandido e modo recolhido compacto."""
        self.expandido = not self.expandido

    def handle_event(self, evento):
        """Processa cliques no botão de minimizar/expandir ou atalhos."""
        if evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_j:
                self.toggle_expandir()
                return True

        elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            if self.rect_botao_toggle.collidepoint(evento.pos):
                self.toggle_expandir()
                return True
        return False

    def desenhar(self, tela, game):
        """Renderiza o Tracker no canto da tela respeitando a visibilidade e proximidade."""
        # 1. Ocultação contextual (diálogos, cutscenes, transições)
        if hasattr(game, 'caixa_dialogo') and game.caixa_dialogo.ativo:
            return
        if hasattr(game, 'transicao') and game.transicao.estado != "INATIVO":
            return
        if hasattr(game, 'flashback_sistema') and game.flashback_sistema.estado != "INATIVO":
            return
        if hasattr(game, 'tela_despertar') and getattr(game.tela_despertar, 'estado', 'INATIVO') != 'INATIVO':
            return

        # 2. Obtém a missão rastreada ativa
        if not hasattr(game, 'missoes') or not game.missoes:
            return

        missao = game.missoes.obter_missao_rastreada()
        if not missao:
            return  # Nenhuma missão ativa para rastrear

        objetivos = missao.get("objetivos", [])

        # 3. Cálculo de Altura Dinâmica
        if self.expandido:
            # Cabeçalho (30px) + Título da Missão (22px) + Objetivos (20px cada) + Padding (12px)
            h_calculada = 32 + 22 + (len(objetivos) * 20) + 10
        else:
            h_calculada = 32

        self.rect_painel = pygame.Rect(self.x, self.y, self.largura_box, h_calculada)

        # 4. Fade Dinâmico de Proximidade da Halia
        halia = getattr(game, 'halia', None)
        alvo_alpha = 255
        if halia:
            zona_proximidade = self.rect_painel.inflate(35, 35)
            rect_halia = pygame.Rect(int(halia.x), int(halia.y), getattr(halia, 'largura', 40), getattr(halia, 'altura', 40))
            if rect_halia.colliderect(zona_proximidade):
                alvo_alpha = 50

        if self.alpha_atual < alvo_alpha:
            self.alpha_atual = min(alvo_alpha, self.alpha_atual + 20)
        elif self.alpha_atual > alvo_alpha:
            self.alpha_atual = max(alvo_alpha, self.alpha_atual - 20)

        # 5. Superfície com canal alfa
        surf_tracker = pygame.Surface((self.largura_box, h_calculada), pygame.SRCALPHA)

        # Fundo e bordas sutis
        alpha_fundo = int((self.alpha_atual / 255.0) * 220)
        alpha_borda = int((self.alpha_atual / 255.0) * 190)

        desenhar_painel_padrao(surf_tracker, pygame.Rect(0, 0, self.largura_box, h_calculada),
                               cor_fundo=(*CARVAO_PROFUNDO[:3], alpha_fundo),
                               cor_borda=(*CINZA_LINHO[:3], alpha_borda),
                               alpha=alpha_fundo)

        # 6. Cabeçalho: [Ícone] MISSÃO ATIVA e Botão [-] / [+]
        cor_cabecalho = (240, 195, 95)
        txt_cab = self.fonte_cabecalho.render("📜 MISSÃO ATIVA", True, cor_cabecalho)
        txt_cab.set_alpha(self.alpha_atual)
        surf_tracker.blit(txt_cab, (12, 8))

        # Botão Toggle
        simbolo_btn = "−" if self.expandido else "+"
        self.rect_botao_toggle = pygame.Rect(self.x + self.largura_box - 28, self.y + 6, 20, 20)

        pos_mouse = pygame.mouse.get_pos()
        hover_toggle = self.rect_botao_toggle.collidepoint(pos_mouse)
        cor_btn = MARFIM_OFFWHITE if hover_toggle else CINZA_LINHO

        txt_tog = self.fonte_cabecalho.render(simbolo_btn, True, cor_btn)
        txt_tog.set_alpha(self.alpha_atual)
        surf_tracker.blit(txt_tog, (self.largura_box - 24, 7))

        # 7. Conteúdo Expandido (Título da Missão e Objetivos)
        if self.expandido:
            # Linha sutil separando cabeçalho
            pygame.draw.line(surf_tracker, (*CINZA_ARDOSIA[:3], int(alpha_borda * 0.7)), (10, 31), (self.largura_box - 10, 31), 1)

            # Título da Missão
            titulo_str = missao.get("titulo", "Missão")
            if len(titulo_str) > 28:
                titulo_str = titulo_str[:25] + "..."
            txt_tit = self.fonte_titulo.render(titulo_str, True, MARFIM_OFFWHITE)
            txt_tit.set_alpha(self.alpha_atual)
            surf_tracker.blit(txt_tit, (12, 38))

            # Lista de Objetivos
            y_obj_rel = 60
            for obj in objetivos:
                concluido = obj.get("concluido", False)
                atual = obj.get("atual", 0)
                alvo = obj.get("alvo", 1)
                desc = obj.get("descricao", "")

                if concluido:
                    marcador = "✓ "
                    cor_marcador = (140, 215, 170)
                    cor_texto = UI_TEXTO_APAGADO
                    prog_str = "(Concluído)"
                else:
                    marcador = "○ "
                    cor_marcador = (245, 205, 80)
                    cor_texto = CINZA_LINHO
                    prog_str = f"({atual}/{alvo})" if alvo > 1 else ""

                # Trunca descrição se necessário
                max_caracteres = 23 if prog_str else 28
                desc_curta = desc if len(desc) <= max_caracteres else desc[:max_caracteres - 3] + "..."

                linha_obj = f"{marcador}{desc_curta} {prog_str}".strip()
                txt_obj = self.fonte_objetivo.render(linha_obj, True, cor_texto)
                txt_obj.set_alpha(self.alpha_atual)
                surf_tracker.blit(txt_obj, (14, y_obj_rel))

                y_obj_rel += 20

        # Blita a superfície renderizada na tela
        tela.blit(surf_tracker, (self.x, self.y))
