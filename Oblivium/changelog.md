# Changelog Oblivium
### Atualização v[0.3.0] - Qualidade de Vida
- Adicionado menu de pausa enquanto o jogador está no jogo
- Adicionado sistema de save com base na criação de slots ( registra tempo de jogo )
- Melhorias na caixa de diálogo com opção de sair e outras páginas com opções de conversa
- Melhorias no inicial com a adição dos créditos e configurações com possibilidade de alterar teclas e velocidade de texto
Adição do menu de configuração com alteração de teclas e outros
- Adicionado botão de correr para a Halia
- Adicionada opção de continuar podendo excluir os dados de um slot com um save e também continuar o progresso do jogo
- Correção de Bugs causadas pela adição dos novos recursos
### Atualização v[0.3.5] - Base para a v0.4
- Adição da base do sistema de inventário ( muito inicial e rudimentar, a ser implementado sua conversa com outros arquivos para melhor funcionalidade )
- Adição de um hud com acesso ao inventário e que mostra a vida atual e mana da protagonista além da progressão do sistema de memória
- Melhorias efetuadas no encontro com inimigos que não respeitavam corretamente o espaço da Halia na tela
- Correção de bugs ocasionados pelo sistema de save implementado na versão anterior e os encontrados graças as alterações, com exemplo: Surgimento dos itens após coletar; permanência de memória; transição falha para a "ESTRADA 2" e inimigos não respeitavam corretamente a Halia.

### Atualização v[0.3.6]
#### Implementação, Correção e Aprimoramento
- Implementação do suporte a sprites ou criação da base do mesmo para facilitar o trabalho no futuro
- Gerenciador de sprites adicionado, com capacidade de carregar sprite ( adição para carregar animações em breve )
- Criação do sistema de combate para progressão da história e solidificação das mecânicas
- Implementação da classe magia para utilização em áreas distintas do jogo
- Melhoria no hud com automatização do mesmo, transparência ao explorar uma região que ele ocupa e ficar indisponível em certas cenas
- Melhoria no indicador de recuperação de memória ( cada fase indicada uma cor )
- Testes realizados com substituição de partes do jogo por sprites realizadas e bem sucedidas

### Atualização v[0.3.7] - Arquitetura de Animações e POO
#### Implementação, Correção e Aprimoramento
- Atualização no `ResourceManager` com a nova classe `Animacao` e métodos para leitura de linhas e recortes precisos de sprites com múltiplas animações.
- Atualização da classe `Entidade` para funcionar como um molde (injeção de dependência), gerindo as animações nativamente com o método `aplicar_pacote_animacoes`.
- Limpeza e adequação das classes `Player`, `NPC`, `Enemy` e `Boss` para herdarem puramente da classe `Entidade` sem acoplamento de arquivos fixos.
**Testes:**
- Correção de um bug crítico onde a animação de "andar" da personagem continuava executando infinitamente após parar o movimento.
- Aprimoramento na renderização matemática de `Entidade`, garantindo que imagens gigantes (ex: 160x144) sejam desenhadas centralizadas na hitbox de colisão (40x40) sem quebrar o contato com o mapa.
- Condução e validação de testes temporários utilizando pacotes completos de animações (Idle, Walk, Attack, Death) redimensionadas corretamente na escala do jogo.

### Atualização v[0.3.8] - Adição de Artes e Melhoria no Sistema de Save
#### Implementação
- Atualização da classe `Item` para trabalhar utilizando o novo gerenciador de sprites.
- Atualização da classe `Game` para salvar novos parâmetros no sistema de save do jogo.
- Atualização da classe `HUD` para trabalhar com as novas artes para o menu, sendo ela a bolsa para o inventário e o amuleto da progressão de memória.
- Atualização do `maploader` para trabalhar com as novas sprites dos itens.
#### Testes
- Rodando o código algumas vezes para verificação do tamanho das sprites e seu posicionamento.

### Atualização v[0.3.8.5] Correção de erros
- Correção de bugs encontrados devido as atualizações da versão anterior

### Atualização v[0.4.0] - Sistema Completo de Combate por Turnos, Puzzles e Persistência
#### Implementação, Correção e Aprimoramento
- **Sistema de 6 Atributos (POO)**: Implementação de Força, Destreza, Constituição, Intelecto, Sabedoria e Presença na classe `Entidade` e derivadas (`Player`, `Enemy`, `Boss`).
- **Catálogo de Habilidades e Bestiário JSON**: Carregamento dinâmico e desacoplado de `skills.json`, `bestiario.json` e `condicoes.json`.
- **Motor e Interface de Combate por Turnos**: Batalha por turnos com controles híbridos (Mouse/Teclado), HUD estilizado de acordo com a identidade visual de Oblivium, barras interpoladas, tremor de impacto e textos flutuantes.
- **Sistema de Mana para Inimigos e Chefes**: Atribuição de `mana_base` e `mana_maxima` para todos os monstros, permitindo ao Boss conjurar seus ataques especiais (*Impacto Anômalo*, *Onda Corrosiva*) com dedução de MP e IA inteligente.
- **Harmonização de Puzzles e Overworld**: Interação direta com a tecla `[E]` nas rochas da Estrada 2 e remoção física de obstáculos via `mapa_casa.desobstruir_estrada()`.
- **Correção no Sistema de Save/Load**: Preservação total de saves manuais sem auto-saves indesejados pós-batalha, desobstrução automática de cenários concluídos ao carregar, e reset estrito de memórias para 0 em Novos Jogos.
- **Suporte Standalone**: Configuração de resolução de raiz nos módulos para permitir execução direta via terminal sem `ModuleNotFoundError`.

### Atualização v[0.4.1] - Submenu de Ações Táticas, Feedback de Esquiva e Ordem de Turnos
#### Implementação, Correção e Aprimoramento
- **Submenu Concentrar (Ações Táticas)**: Agrupamento da opção *"Concentrar"* no menu principal de combate em um submenu contendo:
  - *Foco Espiritual*: Canaliza energia espiritual para recuperar MP, deixando a personagem vulnerável (+35% de dano sofrido).
  - *Defender*: Assume postura de guarda total, reduzindo danos recebidos pela metade e aumentando expressivamente a evasão (+45% de esquiva).
- **Consistência na Fila de Turnos (Fim dos Ataques Duplos)**: A iniciativa agora é calculada uma única vez no início do combate (`ordem_turnos_base`), garantindo que cada participante aja estritamente uma vez por rodada em ordem round-robin, eliminando o comportamento onde inimigos (como o Boss ou a Sombra 2) atacavam duas vezes seguidas na virada de rodada.
- **Destaque Visual e Log de Esquivas**: Mensagens de esquiva no histórico de combate e textos flutuantes (`"ESQUIVOU!"` em Cyan e `"EM GUARDA!"`) destacados com animação suave e cores distintas para feedback imediato das ações defensivas.

### Atualização v[0.4.2] - Nova Tela Inicial, Sistema de Partículas e Botões Gráficos
#### Implementação, Correção e Aprimoramento
- **Nova Identidade Visual da Tela Inicial**: Implementação completa dos novos assets em 32-bit RGBA com fundo preto puro, título estilizado de destaque, versão posicionada no canto inferior direito e texto especial alinhado na base.
- **Componente POO `BotaoGrafico` com Cross-Fade Suave**: Botões com substituição fluida de opacidade entre os estados normal e hover com respiração luminosa orgânica, hitboxes centralizadas e desativação automática quando o cursor não está sobre opções.
- **Motor de Partículas Genérico (`animations.py`)**: Implementação de `ParticulaFlutuante` e `EfeitoChuvaParticulas`, simulando uma chuva orgânica com física independente, oscilação senoidal (*sway*) e rotação individual.
- **Extração C-Accelerated em `ResourceManager`**: Adição de `extrair_sprites_individuais` e `carregar_imagem_com_transparencia` acelerados via máscaras nativas em C (`pygame.mask`), isolando automaticamente 66 pétalas únicas e reduzindo o tempo de carregamento para uma fração de segundo.

### Atualização v[0.4.3] - Alinhamento Visual Editorial, Diálogos com Retratos e Refinamento de Sistemas
#### Implementação, Correção e Aprimoramento
- **Alinhamento Estético Editorial e Dark Fantasy**:
  - Padronização completa da paleta de cores em todas as telas com Carvão Profundo (`#0A0A0E`), Marfim Off-White (`#F6F3EC`), Cinza Linho (`#C4BFB6`) e destaques em azul claro suave (`AZUL_HOVER_MENU`).
  - Consolidação tipográfica universal com *Sunday* para títulos/nomes, *Just Breathe* para passagens poéticas/narrativas e *Contrail One* para estatísticas, opções e interfaces funcionais.
- **Caixa de Diálogos com Retratos e Sistema de Escolhas em 2 Colunas**:
  - Suporte universal a retratos (Portraits) para NPCs (Torvin, Carroceiro) e Halia com moldura interna escura e avatar fallback estilizado.
  - Menu de escolhas organizado lado a lado em 2 colunas com navegação intuitiva por teclado (setas/WASD para alternar entre opções e páginas), cabeçalho de conversa e botão de fechar `[X]` sem sobreposições.
  - Indicador de avanço limpo e estático no rodapé (`▼ [ ENTER ou Clique para avançar ]`), removendo caixas azuis flutuantes.
- **Mapeamento de Controles Unificado e Intuitivo**:
  - **Minigames**: Operação exclusiva via tecla **ESPAÇO**, eliminando interferências de cliques acidentais de mouse.
  - **Avançar / Pular (Diálogos, Intro, Flashbacks, Memórias)**: Operação consistente através de **ENTER** ou **CLIQUE DO MOUSE**.
- **Minigames Mágicos & Cutscenes**:
  - Correção na validação de vitória da Levitação Gravitacional (`MinigameMash`), garantindo o encerramento imediato ao alcançar 100% e transição contínua para a cutscene de desobstrução das pedras.
  - Animação da cutscene de levitação com limites de frame rate seguros (`timer >= 50`), prevenindo travamentos no overworld.
- **Sequência Solene de Despertar de Memória (`TelaDespertarMemoria`)**:
  - Estruturação em 5 etapas com *crossfades* suaves de opacidade (`alpha_conteudo`):
    1. *Título*: Exibição minimalista de *"✦ MEMÓRIA RESTAURADA ✦"* com flor botânica decorativa.
    2. *Estágio*: Exibição destacada de *"Estágio X de 7 — [Nome]"* com a cor temática do fragmento.
    3. *Impacto do Amuleto*: Animação centralizada com contração, *screen shake* e dispersão de partículas etéreas.
    4. *Detalhes*: Layout lateral aberto exibindo a narrativa em *Just Breathe*, o anseio de Halia e novos feitiços despertados.
    5. *Retorno*: *Fade out* suave de volta à exploração do mapa.
- **Pop-up de Interação no Overworld**:
  - Indicador `[ Pressione E para ... ]` posicionado diretamente acima do alvo interagível (itens no chão, porta, Carroceiro e pedras) e renderizado na camada superior (*Z-Index*) sobre os sprites do cenário e personagens.
- **Telas Auxiliares e Interface Geral**:
  - Harmonização das telas de Pausa, Configurações, Controles, Créditos e Gerenciamento de Saves/Slots com a identidade visual unificada.
  - Títulos de seções nos Créditos destacados em azul claro com espaçamento generoso e padronização da fonte de agradecimentos.

### Atualização v[0.5.0] - Sistema Completo de Inventário, Itens Polimórficos, Crafting, Loja e Integração em Combate
#### Implementação, Correção e Aprimoramento
- **Hierarquia Polimórfica de Itens (`src/mechanics/items.py` e `src/data/items.json`)**:
  - Implementação de `ItemBase` e subclasses: `ConsumivelItem` (cura de HP/MP, purificação, frascos de dano elemental com status), `EquipamentoItem` (roupas, mantos, cajados, anéis e amuletos com bônus em atributos primários e stats derivados), `GrimorioItem` (tomos arcanos vinculados a feitiços), `MaterialItem` (ingredientes de alquimia/forja) e `ItemChave` (relíquias e chaves de progressão protegidas contra venda).
- **Fábrica de Itens Centralizada (`ItemFactory`)**:
  - Criação dinâmica e tipada com leitura de catálogo JSON e fallback seguro em memória.
- **Componente de Inventário Funcional (`Inventario`)**:
  - Controle de capacidade expansível de slots, empilhamento automático de itens acumuláveis, gerenciamento de equipamentos equipados (`ROUPA`, `CAJADO`, `ACESSORIO_1`, `ACESSORIO_2`, `GRIMORIO_1`, `GRIMORIO_2`) e consolidação de bônus dinâmicos nos atributos de Halia.
- **Interface Editorial de Inventário (`InventoryState`)**:
  - 5 abas de navegação (`Bolsa`, `Equipamentos`, `Grimórios`, `Materiais`, `Chaves`), visualização da bagagem com contadores de quantidade `xN` e níveis `+N`, suporte completo a Teclado/Mouse (clique esquerdo para equipar/usar e clique direito para desequipar) e tooltips dinâmicos em estilo pergaminho Dark Souls.
- **Sistema de Crafting e Aprimoramento (`CraftingManager` e `src/data/receitas.json`)**:
  - Validação de receitas de alquimia, forja e tecelagem com consumo atômico de materiais e moedas, além de aprimoramento progressivo de equipamentos (+1 a +5) consumindo Minério Sombrio.
- **Sistema de Loja Mercantil com Estoque Limitado (`Loja` e `ShopState`)**:
  - Mercador itinerante com catálogo e estoque finito, suporte à compra e venda com cálculo em tempo real de moedas e verificação de capacidade da bolsa.
- **Integração de Consumíveis no Combate por Turnos (`CombatScreen`)**:
  - Novo `SUBMENU_ITENS` com suporte a itens de suporte direto e frascos arremessáveis contra inimigos vivos, dedução atômica da bolsa, logs contextuais e textos flutuantes.
- **Sistema de Notificações Push / Toasts (`NotificationManager`)**:
  - Fila de mensagens no canto superior direito empilhadas sem sobreposição, com animação de slide/fade e temporizadores calibrados.
- **Persistência Completa nos 4 Slots de Save**:
  - Serialização e desserialização profunda de inventário, equipamentos equipados e moedas em `salvar_estado`, `carregar_estado` e `resetar_progresso`, garantindo retrocompatibilidade com saves antigos.