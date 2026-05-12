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
O Objetivo do jogo é ajudar Halia em uma jornada através de cidades e um grande continete revivendo suas antiga aventura em busca de recuperar suas memórias do momento mais importante de sua vida e das pessoas mais importantes do mesmo. O jogador deverá passar por cada cidade, resolver puzzles, pequenos desafios, conversar com pessoas e investigar a história da própria personagem. O jogador irá vencer ao chegar na última fase tendo completado com êxito as anteriores e derrotando a maldição responsável pelo seu esquecimento.

    - Obrigatório:
    Explorar ambientes
    Interagir com NPCs
    Resolver enigmas
    Recuperar fragmentos de memória
    Sobreviver aos combates

### Personagem Principal - Halia
Halia é uma antiga elfa que vive a cerca de mais de 2000 anos que sofre com uma maldição do esquecimento. No geral Halia é alguém meio apática, mas se importa muito com os amigos, adora gengibre e raízes no geral, mas perde a paciência com desorganização e odeia cosquinha.
#### Características Principais:
- Personalidade apática, porém gentil
- Poderosa usuária de magia, a prática a milénios
- Busca recuperar sua identidade e memórias
- Acumuladora de Itens mágicos e não lida bem com dinheiro o gastando rapidamente
- Ama magia acima de tudo

#### Movimentação:
Sua movimentação é simples seguindo o padrão de jogos comuns utilizando das seguintes teclas: 

**W** → cima
**A** → esquerda
**S** → baixo
**D** → direita

O jogo não possuirá botão de pular visto o formato top-down. 
#### Aparência:
- 1,70m; 
- Cabelo castanho escuro, usa rabo de cavalo; 
- Olhos verdes como jade; 
- Possui sardas no rosto, na região das bochecas;
- Possui a cor de pele branca; 
- Sua vestimenta se resume a: Botas de couro, sobretudo de mago, saia verde, blusa de manga comprida, colete de couro marrom e cinto justo;
- Seus equipamentos são apenas um cajado e bolsa de carteiro.

#### Atributos:
- **Vida (HP)**: Uma atributo destinado ao combate mas que possui influências na narrativa, onde caso o personagem esteja muito machucado sua linha de fala deverá ser diferente e os npcs deverão reagir diferente.
- **Energia mágica**: Também usado para combates como principal mas dessa vez tendo devida funcionalidade para puzzlez comuns.
- **Velocidade**: define a velocidade de movimento pelo mapa.
- **Fragmentos de memória**: Principal atributo que medirá como o mundo irá se comportar, como a personagem deverá se comportar e progresso do jogo, será dividido em partes específicas.
- **Dinheiro**: Poderá ser utilizado para aquisição de itens importantes e progressão em determinadas áreas. Será adquirido conforme missões e progressão no jogo.
### Inimigos e Obstáculos
Os inimigos do jogo serão criaturas mágicas ou seres comuns, encontrados entre cidades ou atacando as mesmas. Os obstáculos poderão ser o terreno, testes e enigmas ou grandes barreiras. No geral serão resolvidos com magia.

- **Tipos de Inimigos**: Criaturas como slimes, orcs, ou inimigos padrões como bandidos, elfos e etc.
  - *Comportamentos Inimigos*: No geral terão movimento automático, com ações padrões que conforme nível irão além de atacar para também defender, esquivar dos ataques do oponente. Funcionará através de um combate padrão por turno. É importante que possuam um sistema de patrulha para perceber a protagonista.
- **Tipos de Obstáculo**: barreiras mágicas, objetos bloqueando caminhos, puzzles ambientais, enigmas e etc.
  - *Comportamentos Obstáculos*: Serão geralmente fixos e irão possuir fases ou etapas para serem resolvidos, se possível alguns deverão ter um minigame mais elaborado, mas no geral consiste em buscar um item, completar uma charada e utilizar magia de modo esperto.

- **Colisão**: Ao entrar em combate com criaturas caso o jogador chegue a 0 de vida será derrotado, com o personagem retornando ao último checkpoint salvo. O combate normalmente só poderá ser encerrado caso um dos dois perca, mas existirá uma opção de fuga. Para obstáculos no geral o jogador ficará com sua passagem bloqueada, a depender do puzzle é possível receber leves consequências ou será resumido a paralisação do progresso enquanto não for resolvido com êxito.

### Cenário (Mapa)
O jogo possui múltiplas cidades onde terão os elementos mais importantes, mas também áreas conectadas, desenvolvidos de modo linear com a história.

- **Ambientes**: Serão vilas, florestas antigas e grandes, ruínas, castelos, estradas e áreas mágicas. Deverão seguir uma estética medieval e mágica, como rpg's mais clássicos.
- **Elementos do mapa**: Possuirá npc's para interação e eles serão extremamente importantes para progressão do jogo; 
Caminhos exploráveis onde a personagem poderá encontrar ruínas com itens; 
áreas bloqueadas protegidas por desafios de intelecto ou força; 
objetos interativos que poderão ser coletados para concluir missões ou desafios.
- **Objetivo final e Itens**: Os itens ficarão distribuídos pelo cenário em lojas onde poderão ser comprados ou em antigas ruínas que podem ser saqueadas. Itens também poderão ser adquiridos eliminado inimigos ou concluindo desafios.
O objetivo final do mapa é após explorar as cidades chegar ao grande castlo onde Halia enfrentará a origem de sua maldição, um local que a mesma há havia visitado.

### Sistema de Pontuação
No geral o jogo irá possuir dois tipos de pontuação, uma mais simbólica e outra que será realmente importante:
- **Pontuação de Mérito**: Itens, inimigos, memórias e outras ações irão acumular pontos para definir o quão bom foi seu desempenho, considere como exemplo: 
Memória recuperada = 100 pontos
Puzzle resolvido = 50 pontos
Monstro derrotado = 25 pontos

- **Pontuação de Progressão**: Uma pontuação estabelicida pela recuperação de memórias que definirá como o jogo evoluir conforme o tempo se passa. Ela define como o cenário mudará e as cores do mundo

### Sistema de Vida
- **Vida inicial**: Halia começará com uma quantidade "fixa" de HP que poderá ser alterada com eventos específicos que ocorrerão ao decorrer do jogo, essa quantidade poderá ser aumentada com itens.

- **Perda de vida**: Halia poderá perder quantidades significativas de vida ao entrar em combates e receber ataques ou falhar em certos desafios punitivos, caso sua quantidade atual de vida chegue a 0 a personagem irá desmaiar, com o desafio atual ou batalha sendo perdido e o jogador retornando ao último ponto.

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
Essas são apenas regras iniciais básicas que serãom complementadas conforme o desenvolvimento: 
- O jogador não pode atravessar paredes ou obstáculos.
- Algumas áreas permanecem bloqueadas até puzzles serem resolvidos.
- NPCs podem fornecer pistas importantes.
- O jogador precisa completar fases em ordem.
- O combate acontece em turno.
- Algumas magias serão necessárias para avançar.

### Estrutura do Projeto
Essa estrutura é provisória e foi moldada com uso de ferramentas e baseamento em repositórios no github, sendo assim poderá receber sérias alterações como alterações de nomes e etc.

Oblivium/
│
├── assets/
│   │
│   ├── sprites/
│   │   │
│   │   ├── player/
│   │   │   └── halia/
│   │   │
│   │   ├── npcs/
│   │   │   ├── torvin/
│   │   │   ├── lion/
│   │   │   ├── tyrion/
│   │   │   └── villagers/
│   │   │
│   │   └── enemies/
│   │       ├── phase_1/
│   │       ├── phase_2/
│   │       ├── phase_3/
│   │       ├── phase_4/
│   │       └── phase_5/
│   │
│   ├── music/
│   │   │
│   │   ├── memory_levels/
│   │   │   ├── level_1/
│   │   │   ├── level_2/
│   │   │   ├── level_3/
│   │   │   ├── level_4/
│   │   │   └── level_5/
│   │   │
│   │   └── regions/
│   │       ├── phase_1_ecos_cinzentos/
│   │       ├── phase_2_raizes_perdidas/
│   │       ├── phase_3_vozes_do_passado/
│   │       ├── phase_4_fragmentos_da_verdade/
│   │       └── phase_5_oblivium/
│   │
│   ├── sounds/
│   │   │
│   │   ├── ambient/
│   │   ├── village/
│   │   ├── combat/
│   │   ├── magic/
│   │   ├── ui/
│   │   ├── puzzles/
│   │   └── cutscenes/
│   │
│   ├── maps/
│   │   │
│   │   ├── phase_1_ecos_cinzentos/
│   │   ├── phase_2_raizes_perdidas/
│   │   ├── phase_3_vozes_do_passado/
│   │   ├── phase_4_fragmentos_da_verdade/
│   │   └── phase_5_oblivium/
│   │
│   ├── effects/
│   │   ├── memory_effects/
│   │   ├── magic_effects/
│   │   └── transitions/
│   │
│   └── fonts/
│
├── src/
│   │
│   ├── core/
│   │   ├── game.py
│   │   ├── settings.py
│   │   ├── config.py
│   │   └── state_manager.py
│   │
│   ├── entities/
│   │   ├── player.py
│   │   ├── npc.py
│   │   ├── enemy.py
│   │   ├── boss.py
│   │   └── companion.py
│   │
│   ├── systems/
│   │   ├── battle_system.py
│   │   ├── dialogue_system.py
│   │   ├── puzzle_system.py
│   │   ├── memory_system.py
│   │   ├── save_system.py
│   │   ├── sound_system.py
│   │   └── transition_system.py
│   │
│   ├── maps/
│   │   ├── map_loader.py
│   │   ├── collision.py
│   │   └── phase_manager.py
│   │
│   ├── ui/
│   │   ├── menu.py
│   │   ├── hud.py
│   │   ├── pause_menu.py
│   │   ├── settings_menu.py
│   │   └── dialogue_box.py
│   │
│   ├── phases/
│   │   ├── phase_1.py
│   │   ├── phase_2.py
│   │   ├── phase_3.py
│   │   ├── phase_4.py
│   │   └── phase_5.py
│   │
│   └── main.py
│
├── saves/
│   ├── save_1/
│   ├── save_2/
│   └── save_3/
│
├── README.md
├── requirements.txt
└── .gitignore

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
- Sistema de inventário avançado
- Trilhas sonoras originais
- NPCs com rotinas
- Cutscenes animadas
- Mais puzzles
- Sistema de escolhas
- Efeitos visuais avançados
- Save automático
- Diferentes finais conforme linhas de diálogo
