# src/utils/colors.py

# 1. CORES COMPARTILHADAS & GENÉRICAS

BRANCO = (255, 255, 255)
PRETO = (0, 0, 0)
CINZA_ESCURO = (50, 50, 50)
CINZA_CLARO = (200, 200, 200)


# 2. SISTEMA DE DIÁLOGOS (CAIXA DE DIÁLOGO & AUTORES)

# Cores de Texto dos Autores / Narrativa
TXT_SISTEMA_NARRADOR = (255, 215, 0)   # Amarelo/Ouro
TXT_PENSAMENTO_INTERNO = (150, 180, 255) # Azul suave para controle
TXT_PENSAMENTO_FANTASMA = (170, 200, 255) # Azul fantasmagórico para a frase
TXT_ECO_PASSADO = (241, 217, 255)      # Lilás fraco

# Cores das Tags de Nome
NOME_HALIA = (144, 238, 144)           # Verde claro
NOME_MALDICAO = (255, 0, 0)            # Vermelho puro

# Estados Globais da UI (Menu de Escolhas / Flashbacks)
UI_FUNDO_PADRAO = (15, 15, 18)         # Cinza quase preto
UI_TEXTO_APAGADO = (100, 100, 100)      # Cinza apagado
UI_TEXTO_DESTAQUE = (220, 220, 220)     # Branco/Cinza claro


# 3. CENÁRIOS & MEIO AMBIENTE (MAPA CASA & ESTRADAS)

CENARIO_FUNDO_FORA = (12, 12, 14)
CENARIO_CHAO_CASA = (120, 115, 110)
CENARIO_PAREDE_CASA = (45, 40, 40)
CENARIO_MOVEIS = (85, 80, 75)
CENARIO_PORTA = (65, 55, 50)
CENARIO_MADEIRA_VARANDA = (100, 95, 90)

# Tons da Estrada Tutorial (Mundo Cinzento)
CENARIO_ESTRADA = (90, 85, 80)          # Terra batida acinzentada
CENARIO_GRAMA_CINZA = (55, 55, 50)      # Vegetação morta
CENARIO_BARREIRAS = (35, 35, 38)        # Pedras e árvores de bloqueio

# 4. ITENS & ENTIDADES

COLOR_BOLSA_MOEDAS = (100, 80, 60)
COLOR_LIVRO_ANTIGO = (70, 85, 100)
COLOR_CAJADO_MAGICO = (80, 90, 70)


# 5. COMBATE & MINIJOGOS (RANGES DE MAGIA)

FUNDO_BATALHA = (20, 25, 35)
BARRA_VIDA_JOGADOR = (50, 200, 50)
BARRA_VIDA_INIMIGO = (200, 50, 50)
BARRA_MANA = (50, 50, 255)
FUNDO_BARRA = (50, 50, 50)

FOGO_NUCLEO = (255, 240, 100)
FOGO_INTERMEDIARIO = (255, 130, 0)
FOGO_BORDA = (240, 40, 10)
TEXTO_ALERTA_COMBATE = (255, 50, 50)
INDICADOR_INTERACAO = (255, 255, 180)  # [E] Interagir

# Elementos de Puzzles / Interativos do Cenário
COR_PEDRA_DESLIZAMENTO = (110, 105, 105)      # Um cinza mineral mais claro e visível
COR_BORDA_PEDRA = (70, 80, 95)                # Um cinza azulado escuro para dar relevo e destaque