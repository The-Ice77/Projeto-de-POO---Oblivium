import pygame
from ui.menu import Menu

pygame.init()

LARGURA = 800
ALTURA = 600

tela = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("Oblivium")

clock = pygame.time.Clock()

menu = Menu()

rodando = True

while rodando:

    for evento in pygame.event.get():

        if evento.type == pygame.QUIT:
            rodando = False

        elif evento.type == pygame.KEYDOWN:

            if evento.key == pygame.K_UP:
                menu.selecionada = (
                    menu.selecionada - 1
                ) % len(menu.opcoes)

            elif evento.key == pygame.K_DOWN:
                menu.selecionada = (
                    menu.selecionada + 1
                ) % len(menu.opcoes)

            elif evento.key == pygame.K_RETURN:

                opcao = menu.opcoes[menu.selecionada]

                print(f"Opção selecionada: {opcao}")

                if opcao == "Jogar":
                    print("Iniciando jogo...")

                elif opcao == "Créditos":
                    print("Mostrar créditos")

                elif opcao == "Sair":
                    rodando = False

    menu.desenhar(tela)

    pygame.display.flip()

    clock.tick(60)

pygame.quit()