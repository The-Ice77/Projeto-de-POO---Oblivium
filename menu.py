import pygame

class Menu:

    def __init__(self):

        self.opcoes = [
            "Jogar",
            "Créditos",
            "Sair"
        ]

        self.selecionada = 0

        self.fonte_titulo = pygame.font.Font(None, 80)
        self.fonte_subtitulo = pygame.font.Font(None, 40)
        self.fonte_menu = pygame.font.Font(None, 50)

    def desenhar(self, tela):

        tela.fill((40, 40, 40))

        titulo = self.fonte_titulo.render(
            "Oblivium",
            True,
            (255, 255, 255)
        )

        subtitulo = self.fonte_subtitulo.render(
            "Um Jogo Sobre Lembrar",
            True,
            (180, 180, 180)
        )

        tela.blit(
            titulo,
            (
                tela.get_width() // 2 - titulo.get_width() // 2,
                100
            )
        )

        tela.blit(
            subtitulo,
            (
                tela.get_width() // 2 - subtitulo.get_width() // 2,
                180
            )
        )

        for i, opcao in enumerate(self.opcoes):

            if i == self.selecionada:
                texto = f"> {opcao} <"
            else:
                texto = opcao

            render = self.fonte_menu.render(
                texto,
                True,
                (255, 255, 255)
            )

            tela.blit(
                render,
                (
                    tela.get_width() // 2 - render.get_width() // 2,
                    300 + i * 60
                )
            )