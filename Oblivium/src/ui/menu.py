import pygame
import sys

pygame.init()

screen = pygame.display.set_mode((720, 720))
pygame.display.set_caption("Menu Oblivium")

WHITE = (255,255,255)
LIGHT = (170,170,170)
DARK = (100,100,100)
BG = (60,25,60)

font = pygame.font.SysFont("Corbel", 40)

def game():
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        screen.fill((40, 40, 40))

        text = font.render("Iniciando...", True, WHITE)
        screen.blit(text, (250, 350))

        pygame.display.update()


def credits():
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return  # Volta para o menu

        screen.fill(BG)

        title = font.render("Créditos", True, WHITE)
        line1 = font.render("Desenvolvido por Sumzin", True, WHITE)
        line2 = font.render("Desenvolvido por Mestre Shiffu", True, WHITE)
        line3 = font.render("Projeto feito com Python e Pygame", True, WHITE)

        screen.blit(title, (280, 200))
        screen.blit(line1, (150, 300))
        screen.blit(line2, (150, 350))
        screen.blit(line3, (100, 400))

        pygame.display.update()

def start_menu():

    while True:

        screen.fill(BG)
        mouse = pygame.mouse.get_pos()

        play_button = pygame.Rect(300, 280, 140, 50)
        credits_button = pygame.Rect(300, 360, 140, 50)
        quit_button = pygame.Rect(300, 440, 140, 50)

        pygame.draw.rect(screen, LIGHT if play_button.collidepoint(mouse) else DARK, play_button)
        pygame.draw.rect(screen, LIGHT if credits_button.collidepoint(mouse) else DARK, credits_button)
        pygame.draw.rect(screen, LIGHT if quit_button.collidepoint(mouse) else DARK, quit_button)

        play_text = font.render("Play", True, WHITE)
        credits_text = font.render("Créditos", True, WHITE)
        quit_text = font.render("Quit", True, WHITE)

        screen.blit(play_text, (335, 285))
        screen.blit(credits_text, (305, 365))
        screen.blit(quit_text, (335, 445))

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:

                if play_button.collidepoint(mouse):
                    game()

                if credits_button.collidepoint(mouse):
                    credits()

                if quit_button.collidepoint(mouse):
                    pygame.quit()
                    sys.exit()

        pygame.display.update()

start_menu()

