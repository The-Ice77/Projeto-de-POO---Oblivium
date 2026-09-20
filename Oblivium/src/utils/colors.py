# src/utils/colors.py

# ==============================================================================
# 1. CORES BASE & FUNDAMENTAIS (DESIGN DARK FANTASY / CARVÃO PROFUNDO & MARFIM)
# ==============================================================================
BRANCO = (255, 255, 255)
BRANCO_LIMPIDO = (252, 250, 246)            # Branco límpido sem saturação excessiva
PRETO = (0, 0, 0)
PRETO_PROFUNDO = (6, 6, 8)                  # Fundo escuro absoluto
CARVAO_PROFUNDO = (10, 10, 14)              # #0A0A0E - Fundo escuro fosco e suave
CINZA_ARDOSIA = (30, 32, 38)                # Tom ardósia escuro para containers e painéis
CINZA_GRAFITE = (22, 22, 26)                # Grafite escuro
CINZA_ESCURO = (38, 38, 44)                 # Fundo de barras descarregadas e bordas discretas
CINZA_LINHO = (196, 191, 182)               # #C4BFB6 - Linho para linhas de 1px/2px e divisórias
CINZA_CLARO = (215, 210, 202)               # Borda sutil e texto secundário
MARFIM_OFFWHITE = (246, 243, 236)           # #F6F3EC - Off-white suave límpido para tipografia
GIZ_SUAVE = (225, 220, 212)                 # Branco giz suave
DOURADO_ENVELHECIDO = (215, 190, 135)       # Dourado pálido para destaques de botões e runas

# Destaques Especiais de Hover (Padrão Azul Clarinho do Menu Inicial)
AZUL_HOVER_MENU = (160, 205, 240)           # Azul etéreo luminoso do menu inicial
AZUL_HOVER_BG = (28, 42, 60)                # Fundo translúcido para hover azulado
AZUL_HOVER_BORDA = (180, 220, 250)          # Borda com brilho sutil

# ==============================================================================
# 2. ESTILO DARK FANTASY / PAINÉIS, DIÁLOGOS & TOOLTIPS
# ==============================================================================
PERGAMINHO_BG = (16, 16, 20)                # Substituído por fundo carvão escuro elegante
PERGAMINHO_BG_HOVER = (28, 42, 60)          # Fundo de opção selecionada em azul escuro suave
PERGAMINHO_TINTA = (246, 243, 236)          # Texto em marfim límpido
PERGAMINHO_TINTA_SUAVE = (180, 175, 168)    # Tinta secundária para notas e subtítulos
PERGAMINHO_BORDA = (196, 191, 182)          # Contorno fino de 1px
PERGAMINHO_TAG_BG = (24, 24, 30)            # Aba de nome do falante

# Cores de Texto dos Autores / Narrativa
TXT_SISTEMA_NARRADOR = (235, 218, 185)      # Ouro suave para narrador e seleções
TXT_PENSAMENTO_INTERNO = (160, 205, 240)    # Azul acinzentado etéreo para reflexões de Halia
TXT_PENSAMENTO_FANTASMA = (180, 215, 245)   # Azul etéreo suave para memórias
TXT_ECO_PASSADO = (230, 215, 235)           # Lavanda envelhecido para lembranças

# Cores das Tags de Nome
NOME_HALIA = (145, 215, 165)                # Verde sálvia suave
NOME_MALDICAO = (225, 55, 65)               # Carmesim profundo

# Estados Globais da UI (Painéis / Menus / Flashbacks)
UI_FUNDO_PADRAO = (10, 10, 14)              # Preto carvão suave fosco
UI_TEXTO_APAGADO = (125, 125, 132)          # Cinza ardósia apagado para notas secundárias
UI_TEXTO_DESTAQUE = (246, 243, 236)         # Marfim / Off-white límpido

# Botões da UI
BOTAO_FECHAR_NORMAL = (165, 45, 50)         # Carmim escuro envelhecido
BOTAO_FECHAR_HOVER = (215, 70, 75)          # Carmim iluminado

# ==============================================================================
# 3. CENÁRIOS & MEIO AMBIENTE
# ==============================================================================
CENARIO_FUNDO_FORA = (8, 8, 10)
CENARIO_CHAO_CASA = (150, 130, 105)         # Piso de pinho/carvalho desbotado
CENARIO_PAREDE_CASA = (85, 58, 44)          # Madeira rústica marrom siena
CENARIO_MOVEIS = (125, 100, 75)             # Móveis de mogno envelhecido
CENARIO_PORTA = (100, 70, 50)               # Porta de carvalho
CENARIO_MADEIRA_VARANDA = (135, 110, 85)    # Varanda externa

# Tons da Estrada e Vegetação
CENARIO_ESTRADA = (135, 120, 102)           # Terra batida acinzentada e mineral
CENARIO_GRAMA_CINZA = (72, 95, 72)          # Verde sálvia/musgo dessaturado
CENARIO_BARREIRAS = (52, 70, 52)            # Floresta densa verde musgo escuro

# ==============================================================================
# 4. ITENS & ENTIDADES
# ==============================================================================
COLOR_BOLSA_MOEDAS = (205, 170, 85)         # Couro dourado pálido
COLOR_LIVRO_ANTIGO = (85, 125, 175)         # Grimório azul ardósia
COLOR_CAJADO_MAGICO = (150, 120, 75)        # Madeira nobre envelhecida

# ==============================================================================
# 5. COMBATE & HUD (BARRAS DE STATUS COM CONTRASTE PROFUNDO)
# ==============================================================================
FUNDO_BATALHA = (12, 14, 18)
BARRA_VIDA_JOGADOR = (205, 45, 55)          # Carmim vivo envelhecido
BARRA_VIDA_INIMIGO = (205, 45, 55)
BARRA_MANA = (55, 140, 225)                 # Azul cerúleo luminoso / éter
BARRA_EXP = (90, 175, 135)                  # Verde jade/sálvia suave
FUNDO_BARRA = (28, 30, 36)
BARRA_FUNDO_ESCURO = FUNDO_BARRA
BORDA_PADRAO = CINZA_LINHO
BORDA_DESTAQUE = MARFIM_OFFWHITE
FUNDO_BARRA_VIDA = (50, 15, 20)             # Fundo vinho escurecido
FUNDO_BARRA_MANA = (15, 28, 55)             # Fundo azul noite escurecido
FUNDO_BARRA_EXP = (20, 40, 32)              # Fundo verde musgo escurecido

FOGO_NUCLEO = (255, 240, 140)
FOGO_INTERMEDIARIO = (240, 135, 45)
FOGO_BORDA = (215, 60, 35)
TEXTO_ALERTA_COMBATE = (235, 65, 65)
INDICADOR_INTERACAO = (246, 243, 236)       # [E] Interagir em off-white limpo

# Elementos de Puzzles
COR_PEDRA_DESLIZAMENTO = (120, 125, 130)    # Rocha mineral
COR_BORDA_PEDRA = (65, 70, 75)              # Contorno ardósia

# ==============================================================================
# 6. CORES DO AMULETO DE MEMÓRIAS (7 FASES ETÉREAS E REFINADAS)
# ==============================================================================
AMULETO_COR_FASE_1 = (115, 180, 205)  # 1. Aquamarine velado
AMULETO_COR_FASE_2 = (135, 190, 155)  # 2. Sálvia místico
AMULETO_COR_FASE_3 = (210, 180, 115)  # 3. Âmbar pálido
AMULETO_COR_FASE_4 = (210, 125, 90)   # 4. Laranja outonal queimado
AMULETO_COR_FASE_5 = (175, 130, 180)  # 5. Lavanda envelhecido
AMULETO_COR_FASE_6 = (205, 90, 105)   # 6. Carmim suave
AMULETO_COR_FASE_7 = (250, 248, 242)  # 7. Marfim puro / Despertar completo
