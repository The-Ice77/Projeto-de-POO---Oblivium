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

# Botões da UI (Novos)
BOTAO_FECHAR_NORMAL = (200, 50, 50)     # Vermelho escuro
BOTAO_FECHAR_HOVER = (255, 100, 100)    # Vermelho claro

# 3. CENÁRIOS & MEIO AMBIENTE (MAPA CASA & ESTRADAS)
CENARIO_FUNDO_FORA = (18, 16, 22)
CENARIO_CHAO_CASA = (165, 125, 85)          # Piso de madeira nobre aconchegante
CENARIO_PAREDE_CASA = (75, 55, 45)          # Parede rústica acolhedora
CENARIO_MOVEIS = (125, 80, 50)              # Móveis de mogno/carvalho polido
CENARIO_PORTA = (105, 65, 40)               # Porta de madeira maciça
CENARIO_MADEIRA_VARANDA = (145, 105, 70)    # Madeira de varanda externa

# Tons da Estrada e Natureza (Cores vivas para transição com o filtro)
CENARIO_ESTRADA = (165, 125, 75)            # Terra batida dourada e terrosa
CENARIO_GRAMA_CINZA = (60, 145, 65)         # Grama verdejante e viva
CENARIO_BARREIRAS = (45, 95, 50)            # Vegetação e árvores verde-floresta

# 4. ITENS & ENTIDADES
COLOR_BOLSA_MOEDAS = (210, 160, 45)         # Bolsa de couro dourado
COLOR_LIVRO_ANTIGO = (65, 120, 210)         # Grimório azul safira encantado
COLOR_CAJADO_MAGICO = (160, 125, 60)        # Cajado de madeira nobre dourada

# 5. COMBATE & MINIJOGOS (RANGES DE MAGIA)
FUNDO_BATALHA = (20, 25, 35)
BARRA_VIDA_JOGADOR = (220, 45, 45)
BARRA_VIDA_INIMIGO = (220, 45, 45)
BARRA_MANA = (45, 120, 240)
FUNDO_BARRA = (35, 35, 42)

FOGO_NUCLEO = (255, 245, 120)
FOGO_INTERMEDIARIO = (255, 140, 20)
FOGO_BORDA = (245, 45, 15)
TEXTO_ALERTA_COMBATE = (255, 60, 60)
INDICADOR_INTERACAO = (255, 255, 180)  # [E] Interagir

# Elementos de Puzzles / Interativos do Cenário
COR_PEDRA_DESLIZAMENTO = (130, 140, 155)      # Rocha com relevo mineral nítido
COR_BORDA_PEDRA = (60, 70, 90)                # Contorno mineral azul-ardósia

# --- CORES DO AMULETO DE MEMÓRIAS (7 FASES) ---
AMULETO_COR_FASE_1 = (90, 160, 210)   # Azul frio inicial
AMULETO_COR_FASE_2 = (120, 190, 140)  # Verde musgo / aurora
AMULETO_COR_FASE_3 = (210, 180, 90)   # Dourado pálido
AMULETO_COR_FASE_4 = (220, 130, 80)   # Âmbar / Laranja
AMULETO_COR_FASE_5 = (180, 90, 180)   # Roxo místico
AMULETO_COR_FASE_6 = (220, 90, 110)   # Carmesim / Vermelho vivo
AMULETO_COR_FASE_7 = (240, 240, 240)  # Branco puro / Despertar completo
