# src/main.py
import os
import sys
import pygame

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.game import Game

def main():
    pygame.init()
    
    # Inicializa o coração do motor do jogo
    oblivium = Game()
    oblivium.run()
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()