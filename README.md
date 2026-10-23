# DOCUMENTAÇÃO DO PROJETO - PROGRAMAÇÃO ORIENTADA A OBJETOS

## Desenvolvedores:

- Davi Gomes Suassuna
- João Victor Sales de Azevedo Silva

### Oblivium - Um Jogo Sobre Lembrar

Oblivium é um jogo no estilo RPG feito em pixel art com visão top-down desenvolvido inicialmente para PC. O jogo utiliza de modo obrigatório Python e Pygame com possível adição de mais bibliotecas conforme decorrer do desenolvimento do jogo.
O jogo se inicia melancólico e inicialmente sem quaisquer tipo de cores, onde a protagonista explora cidades e locais antigos em busca de recuperar suas memórias perdidas em uma aventura anterior em conjunto de seus aliados que a deixaram a muito tempo.

    - Pontos Importantes:
        A protagonista é uma elfa que vive a milénios,
        amaldiçoada com o esquecimento.
        Sua história é totalmente dependente do quão importante
        memórias são para ela, ignorar isso é ignorar a
        história do  jogo.

### Objetivo do Jogo

O objetivo do jogo é ajudar Halia em uma jornada através de cidades e um grande continete revivendo suas antiga aventura em busca de recuperar suas memórias do momento mais importante de sua vida e das pessoas mais importantes do mesmo. O jogador deverá passar por cada cidade, resolver puzzles, pequenos desafios, conversar com pessoas e investigar a história da própria personagem. O jogador irá vencer ao chegar na última fase tendo completado com êxito as anteriores e derrotando a maldição responsável pelo seu esquecimento.

    - Obrigatório:
    Explorar ambientes
    Interagir com NPCs
    Resolver enigmas
    Recuperar fragmentos de memória
    Tentar Sobreviver aos combates

### Personagem Principal - Halia

Halia é uma antiga elfa que vive a cerca de mais de 2000 anos que sofre com uma maldição do esquecimento. No geral Halia é alguém meio apática, mas se importa muito com os amigos, adora gengibre e raízes no geral, mas perde a paciência com desorganização e odeia cosquinha.

#### Características Principais:

- Personalidade apática, porém gentil
- Poderosa usuária de magia, a prática a milênios
- Busca recuperar sua identidade e memórias
- Acumuladora de Itens mágicos e não lida bem com dinheiro, gastando rapidamente
- Ama magia acima de tudo

#### Movimentação:

Sua movimentação é simples, seguindo o padrão de jogos comuns utilizando das seguintes teclas:

**W** → cima
**A** → esquerda
**S** → baixo
**D** → direita

O jogo não possuirá botão de pular visto que segue o formato top-down.

#### Aparência:

- 1,70m;
- Cabelo castanho escuro, usa rabo de cavalo;
- Olhos verdes como jade;
- Possui sardas no rosto, na região das bochechas;
- Possui a cor de pele branca;
- Sua vestimenta se resume a: Botas de couro, sobretudo de mago, saia verde, blusa de manga comprida, colete de couro marrom e cinto justo;
- Seus equipamentos são apenas um cajado e bolsa de carteiro.

#### Atributos:

- **Vida (HP)**: Um atributo destinado ao combate.
- **Energia mágica**: Também usado para combates como principal mas dessa vez tendo devida funcionalidade para puzzles comuns.
- **Velocidade**: Define a velocidade de movimento pelo mapa.
- **Fragmentos de memória**: Principal atributo que medirá como o mundo irá se comportar, como a personagem deverá se comportar e o progresso do jogo, será dividido em partes específicas.
- **Dinheiro**: Poderá ser utilizado para aquisição de itens importantes e progressão em determinadas áreas. Será adquirido conforme missões e progressão no jogo.

### Inimigos e Obstáculos

Os inimigos do jogo serão criaturas mágicas ou seres comuns, encontrados entre cidades ou atacando as mesmas. Os obstáculos poderão ser o terreno, testes e enigmas ou grandes barreiras. No geral serão resolvidos com magia.

- **Tipos de Inimigos**: Criaturas como slimes, orcs, ou inimigos padrões como bandidos, elfos, demônios e etc.
  - _Comportamentos Inimigos_: No geral terão movimento automático, com ações padrões que conforme nível irão além de atacar para também defender, esquivar dos ataques do oponente. Funcionará através de um combate padrão por turno. É importante que possuam um sistema de patrulha para perceber a protagonista.
- **Tipos de Obstáculo**: barreiras mágicas, objetos bloqueando caminhos, puzzles ambientais, enigmas e etc.
  - _Comportamentos Obstáculos_: Serão geralmente fixos e irão possuir fases ou etapas para serem resolvidos, se possível alguns deverão ter um mini game mais elaborado, mas no geral consiste em buscar um item, completar uma charada e utilizar magia de modo esperto.

- **Colisão**: Ao entrar em combate com criaturas caso o jogador chegue a 0 de vida será derrotado, com o personagem retornando ao último checkpoint salvo. O combate normalmente só poderá ser encerrado caso um dos dois perca, mas existirá uma opção de fuga. Para obstáculos no geral o jogador ficará com sua passagem bloqueada, a depender do puzzle é possível receber leves consequências ou será resumido a paralisação do progresso enquanto não for resolvido com êxito.

### Cenário (Mapa)

O jogo possui múltiplas cidades onde terão os elementos mais importantes, mas também áreas conectadas, desenvolvidos de modo linear com a história.

- **Ambientes**: Serão vilas, florestas antigas e grandes, ruínas, castelos, estradas e áreas mágicas. Deverão seguir uma estética medieval e mágica, como RPGs mais clássicos.
- **Elementos do mapa**: Possuirá NPCs para interação e eles serão extremamente importantes para progressão do jogo;
  Caminhos exploráveis onde a personagem poderá encontrar ruínas com itens;
  áreas bloqueadas protegidas por desafios de intelecto ou força;
  objetos interativos que poderão ser coletados para concluir missões ou desafios.
- **Objetivo final e Itens**: Os itens ficarão distribuídos pelo cenário em lojas onde poderão ser comprados ou em antigas ruínas que podem ser saqueadas. Itens também poderão ser adquiridos eliminado inimigos ou concluindo desafios.
  O objetivo final do mapa é após explorar as cidades chegar ao grande castelo onde Halia enfrentará a origem de sua maldição, um local que a mesma já havia visitado.

### Sistema de Pontuação

No geral o jogo irá possuir dois tipos de pontuação, uma mais simbólica e outra que será realmente importante:

- **Pontuação de Mérito**: Itens, inimigos, memórias e outras ações irão acumular pontos para definir o quão bom foi seu desempenho, considere como exemplo:
  Memória recuperada = 100 pontos
  Puzzle resolvido = 50 pontos
  Monstro derrotado = 25 pontos

- **Pontuação de Progressão**: Uma pontuação estabelecida pela recuperação de memórias que definirá como o jogo evoluir conforme o tempo se passa. Ela define como o cenário mudará e as cores do mundo

### Sistema de Vida

- **Vida inicial**: Halia começará com uma quantidade "fixa" de HP que poderá ser alterada com eventos específicos que ocorrerão ao decorrer do jogo, essa quantidade poderá ser aumentada com itens.

- **Perda de Vida**: Halia poderá perder quantidades significativas de vida ao entrar em combates e receber ataques ou falhar em certos desafios punitivos, caso sua quantidade atual de vida chegue a 0 a personagem irá desmaiar, com o desafio atual ou batalha sendo perdido e o jogador retornando ao último ponto.

- **Recuperação:** Através da compra de itens mágicos como poções de cura, serviços médicos ou descansos.

### Controles

O jogo possuirá diversas teclas com funcionalidades que poderão ser alteradas conforme o tempo, inicialmente o objetivo será:
Teclas - Funções

W - Mover para cima  
A - Mover para esquerda
S - Mover para baixo  
D - Mover para direita  
E - Interagir  
ESC - Abrir menu  
ENTER - Confirmar diálogo  
SPACE - Usar magia/ação
TAB - Abrir informações

### Fluxo do Jogo

O jogo seguirá um fluxo linear com isso sendo dependente para a progressão da história do mesmo. Aqui definimos como o jogo seguirá de modo resumido:

1. O jogador inicia no menu principal
2. Uma introdução apresenta Halia
3. O jogador passa a explorar cidades e áreas
4. Resolve puzzles e conversa com NPCs, cumprindo seus pedidos ou apenas descobrindo fragmentos da história
5. Enfrenta monstros e desafios que paralisam o caminho
6. Recupera memórias e desbloqueia cores no mundo conforme passa por cidades e cumpre desafios ou vence batalhas
7. Avança para a nova e última região
8. Descobre a verdade sobre a maldição
9. Enfrenta o boss final
10. Recupera suas memórias

- **Vitória**: Completar a história e derrotar a maldição.

- **Derrota**: Fracassar em combate ou desafios sem conseguir continuar.

### Regras do Jogo

- O jogador não pode atravessar paredes ou obstáculos.
- Algumas áreas permanecem bloqueadas até puzzles serem resolvidos.
- NPCs podem fornecer pistas importantes.
- O jogador precisa completar fases em ordem.
- O combate acontece em turno.
- Algumas magias serão necessárias para avançar.
- Não é possível fugir de certas batalhas

### Estrutura do Projeto

Essa estrutura é provisória e foi moldada com uso de ferramentas e baseada em repositórios no github, sendo assim poderá receber sérias alterações como alterações de nomes e etc.

Projeto-de-POO---Oblivium/
│
├── README.md                    # documentação do projeto
├── CRONOGRAMA.md
├── Notas/
│   └── arquivo.text
├── Storyboard/
│   └── Storyboard_compressed.pdf
│
└── Oblivium/
    ├── changelog.md
    ├── sounds.md                # guia de áudio esperado pelo AudioManager
    │
    ├── assets/
    │   ├── animais/
    │   │   ├── gato/                    # acoes_separadas/ (17 ações x 3 frames + sheets) [69]
    │   │   └── passaro/                 # animacoes/{bicar,idle,pulo,voo}, pulo/, voo/ [161]
    │   │
    │   ├── audio/                       # ainda vazio (só .gitkeep)
    │   │   ├── music/
    │   │   ├── ambience/
    │   │   └── sfx/
    │   │
    │   ├── cenario/ [2216]
    │   │   ├── 01_Paredes_Externas/     # Parede_Tipo_01..03, cada um com:
    │   │   │   └── Parede_Tipo_0X/      #   01_Frente_Corridas, 02_Atras_Corridas,
    │   │   │                            #   03_Laterais_Verticais, 04_Quinas_e_Cantos,
    │   │   │                            #   05_Salas_Montadas, 06_Portas_e_Janelas
    │   │   ├── 02_Pisos_Externos/       # 01_Grama_Verde, 02_Pedra_Cinza, 03_Terra_Marrom,
    │   │   │                            # 04_Neve_Branca, 05_Areia_Amarela, 06_Agua_Azul
    │   │   ├── 04_Paredes_Internas/     # 01_Comodos..., 02_Frontais, 03_Traseiras,
    │   │   │                            # 04_Laterais_Altas, 05_Arcos_e_Portas, 06_Divisorias_e_Colunas
    │   │   ├── 08_Cercas/               # Frente, Atras, Laterais, Curvas_e_Quinas, Postes_e_Portao
    │   │   ├── 10_Pisos_Interior/       # 01_Pisos_Madeira_e_Tabuado
    │   │   ├── armadilhas/              # espinhos_tipo_01..03
    │   │   ├── arvores_animadas/        # 9 árvores x 14 frames
    │   │   ├── arvores_separadas_tipo1/ # Model_01_Size_02..05
    │   │   ├── arvores_separadas_tipo2/ # Model_02_Size_02..05
    │   │   ├── arvores_separadas_tipo3/ # Model_03_Size_02..05
    │   │   ├── paredes_externas/        # casas_vila, wall_tiles_01..03, wall_variatons_01..03
    │   │   ├── pisos_externos/          # agua/pocas_agua, areia, grama, neve, pedra, terra
    │   │   ├── sprites_separadas_interior/
    │   │   │   ├── Buildings_Interior_Interior_Props_01/
    │   │   │   ├── Buildings_Interior_Interior_Walls_01/
    │   │   │   ├── Buildings_Props/objetos_vila/
    │   │   │   ├── Buildings_Roofs/
    │   │   │   ├── Buildings_Shadows/
    │   │   │   └── Buildings_Walls/
    │   │   ├── vegetacao_pedras_separadas/  # Rocks/, Vegetation/arvores_estilo_separado/
    │   │   └── vila/
    │   │       ├── catalogo.html
    │   │       ├── Barracas/{Costas,Frente}
    │   │       ├── Casas/{Conjunto_1,Conjunto_2}
    │   │       ├── Lojas/{Costas,Frente}
    │   │       └── Props/{Bancos,Cargas_e_Transporte,Fontes,Iluminacao_e_Postes,
    │   │                  Monumentos,Placas_e_Estandartes,Vegetacao_e_Jardim}
    │   │
    │   ├── efeitos/ [750]
    │   │   ├── chuva clara/  chuva escura/  chuva splash/   # 1 spritesheet cada
    │   │   ├── explosao/    # explosao_1..3
    │   │   ├── fogo/        # braseiro, chama, chao, coluna, fogueira, fumaca,
    │   │   │                # media, mini, rasteira (cores: amarela, azul, branca,
    │   │   │                #   laranja, roxa, verde)
    │   │   ├── folhas/  nuvens/  snowflake/
    │   │   └── sangue/      # sangue_1..5
    │   │
    │   ├── halia/                       # protagonista [23]
    │   │   ├── andando_direita/  andando_esquerda/
    │   │   ├── costas/  frente/  turnaround/
    │   │
    │   ├── hud/                         # "Sistema de Memórias" 0..7 + bolsa.png
    │   ├── inimigos/ [400]
    │   │   ├── banco/  demonio_grande/  demonio_inferior/  demonio_olho/
    │   │   ├── demonio_pequeno/  demonio_superior/
    │   │   ├── dragao_branco/           # attack_01/02, dead, flight, hurt, idle,
    │   │   └── dragao_vermelho/         # landing, special, takeoff, walk
    │   ├── menu inicial/                # botões (+ hover), título, livro e cajado, pétalas
    │   └── props/                       # Bolsa de Moedas, Cajado, Grimório
    │
    └── src/
        ├── main.py
        │
        ├── core/
        │   ├── game.py
        │   ├── audio_manager.py
        │   └── save_manager.py
        │
        ├── data/                        # conteúdo do jogo em JSON
        │   ├── bestiario.json      ├── items.json
        │   ├── combat_texts.json   ├── missoes.json
        │   ├── condicoes.json      ├── notificacoes.json
        │   ├── conquistas.json     ├── receitas.json
        │   ├── dialogos.json       ├── skills.json
        │   ├── dialogos.py         └── grimorio_halia.json
        │
        ├── entities/
        │   ├── Entity.py   ├── player.py   ├── NPC.py
        │   ├── Enemy.py    ├── Boss.py     ├── enemy_factory.py
        │   ├── animal.py   ├── item.py     └── elemento_cenario.py
        │
        ├── maps/
        │   ├── map_loader.py     ├── cenario_base.py
        │   ├── mapa_casa.py      ├── mapa_estrada.py
        │   └── mapa_estrada_2.py
        │
        ├── mechanics/
        │   ├── combat.py  combat_input.py  combat_narrator.py  combat_renderer.py
        │   ├── attributes.py  conditions.py  skills.py  magia.py  grimorio.py
        │   ├── inventory.py  items.py  item_factory.py  crafting.py  shop.py
        │   ├── dialogue_manager.py  cutscene_manager.py  quest_manager.py
        │   └── achievement_manager.py  minigames.py
        │
        ├── states/
        │   ├── states.py                # base / gerenciador de estados
        │   ├── menu_states.py  intro_states.py  credits_states.py
        │   ├── slots_states.py  settings_states.py  controles_state.py
        │   ├── selecao_controles_state.py
        │   ├── playing_states.py  pause_states.py  combat_states.py
        │   ├── inventory_states.py  shop_states.py  conquistas_state.py
        │   └── inventory_tabs/
        │       ├── __init__.py  tab_inventario.py  tab_magia.py
        │       └── tab_crafting.py  tab_perfil.py
        │
        ├── ui/
        │   ├── hud.py  menu.py  dialogue_box.py  quest_tracker.py
        │   ├── notification_manager.py  transition.py  flashback.py
        │   └── intro.py  tela_despertar.py  ui_utils.py
        │
        └── utils/
            ├── constants.py  colors.py  colors#.py
            ├── resource_manager.py  animations.py  clima.py
            ├── filtro_memoria.py  save_manager.py  dev_commands.py

### Funcionalidades Mínimas

A primeira versão jogável do projeto deverá conter:

- Menu inicial funcional ( com iniciar, escolher save, configurações e sair )
- Sistema de movimentação do personagem
- Sistema de colisão
- Interação com NPCs
- Sistema básico de diálogos
- Um mapa explorável
- Sistema de progressão por memórias
- Mudança gradual de cores no ambiente
- Pelo menos um puzzle funcional
- Sistema básico de combate em turno
- Sistema de vitória e derrota
- Sistema simples de transição de fases
- Cena final básica

### Melhorias Futuras

Considerando as ideias atuais para o projeto e que o mesmo seja finalizado desse modo, as possíveis melhorias futuras são:

- Mais cidades e mapas
- Mais magias
- Sistema de inventário avançado (feito)
- Trilhas sonoras originais
- NPCs com rotinas
- Cutscenes animadas
- Mais puzzles
- Sistema de escolhas (feito)
- Efeitos visuais avançados
- Save automático (feito)
- Diferentes finais conforme linhas de diálogo

---

## 🏛️ Arquitetura e Engenharia de Software (POO & Design Patterns)

O projeto *Oblivium* segue padrões rigorosos de **Programação Orientada a Objetos (POO)** e boas práticas de arquitetura de software:

### 1. Component Pattern & Composição
- **Sistema de 6 Atributos (`Atributos`):** Força, Destreza, Constituição, Intelecto, Sabedoria e Presença compõem instâncias de `Player`, `Enemy` e `Boss`, calculando dinamicamente modificadores, HP/MP máximo, defesas e iniciativa.

### 2. Registry Pattern & Polimorfismo
- **Catálogo de Habilidades (`SkillsRegistry`):** Magias (`MagiaOfensiva`, `MagiaCura`), golpes físicos (`AtaqueFisico`) e posturas (`AcaoFoco`) herdam de `AcaoCombate` e são registradas dinamicamente a partir de `src/data/skills.json`.

### 3. Factory Method Pattern
- **Fábrica de Inimigos (`EnemyFactory`):** Centraliza a criação de monstros e chefes a partir de `src/data/bestiario.json`, suportando escalonamento de nível e geração procedural de encontros aleatórios balanceados.

### 4. State Pattern & Desacoplamento
- **Motor de Combate por Turnos (`CombatScreen` & `CombatState`):** Totalmente desacoplado do mapa e do overworld, operando via máquina de estados (`MENU_PRINCIPAL`, `SUBMENU_MAGIA`, `SELECIONANDO_ALVO`, `TURNO_INIMIGO`, `VITORIA`, `DERROTA`, `FUGIU`) e disparando *callbacks* assíncronos (`on_vitoria`, `on_derrota`, `on_fuga`).

### 5. Externalização de Dados (JSON Driven)
- Catálogos de dados (`skills.json`, `bestiario.json`, `condicoes.json`) em arquivos JSON externos com suporte a fallback de emergência em memória.

