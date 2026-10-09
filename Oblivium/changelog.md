# ◈ Changelog Oblivium ◈
*Histórico de versões, implementações e refinamentos de Oblivium.*

---

### Atualização v[0.3.0] — Qualidade de Vida
#### Implementação, Correção e Aprimoramento
- **Menu de Pausa**: Adição de menu de pausa funcional durante a exploração do mundo.
- **Sistema de Saves**: Criação de múltiplos slots de salvamento com registro do tempo de jogo.
- **Caixa de Diálogo**: Opção de saída rápida e paginação com ramificações de conversa.
- **Menu Principal**: Adição de tela de créditos e configurações (teclas e velocidade do texto).
- **Mecânica de Corrida**: Suporte à tecla de corrida (`Shift`) para a Halia.
- **Gerenciamento de Slots**: Opções para carregar, continuar e excluir arquivos de save.
- **Correções**: Estabilização de bugs decorrentes das novas rotinas de interface.

---

### Atualização v[0.3.5] — Fundação de Inventário e HUD
#### Implementação, Correção e Aprimoramento
- **Base de Inventário**: Estruturação inicial do sistema de itens e bagagem da protagonista.
- **HUD Dinâmico**: Exibição de barras de vida, mana e progressão dos fragmentos de memória.
- **Ajuste de Encontros**: Correção do distanciamento e da zona de colisão dos inimigos.
- **Persistência de Coletas**: Fim da duplicação de itens após a coleta e correções na transição para a Estrada 2.

---

### Atualização v[0.3.6] — Estrutura de Sprites e Combate
#### Implementação, Correção e Aprimoramento
- **Gerenciador de Recursos**: Base centralizada para carregamento de texturas e imagens 32-bit.
- **Sistema de Combate**: Criação do primeiro protótipo funcional de batalhas por turnos.
- **Módulo de Magias**: Implementação da classe base para conjurações arcanas.
- **HUD Inteligente**: Ocultação dinâmica durante cutscenes e transparência contextual.
- **Filtro de Memória**: Indicação visual de cores no mapa de acordo com o estágio de despertar.

---

### Atualização v[0.3.7] — Arquitetura de Animações e POO
#### Implementação, Correção e Aprimoramento
- **Motor de Animações**: Introdução da classe `Animacao` e recorte de spritesheets no `ResourceManager`.
- **Herança de Entidades**: Classes `Player`, `NPC`, `Enemy` e `Boss` refatoradas como derivadas puras de `Entity`.
- **Fim da Marcha Infinita**: Correção onde a animação de corrida prosseguia mesmo com a personagem parada.
- **Ancoragem 2.5D**: Centralização matemática de sprites grandes sobre a base física de colisão.

---

### Atualização v[0.3.8] — Artes dos Itens e Persistência
#### Implementação, Correção e Aprimoramento
- **Sprites nos Itens**: Integração da classe `Item` ao novo carregador de texturas.
- **HUD Renovado**: Novas artes desenhadas para a bolsa de inventário e o amuleto de memórias.
- **Persistência Expandida**: Registro de novos parâmetros de status e flags na classe `Game`.
- **Cenário e Objetos**: Atualização do `MapLoader` para suportar os novos ícones do mapa.

---

### Atualização v[0.3.8.5] — Correções e Estabilidade
#### Implementação, Correção e Aprimoramento
- **Polimento Geral**: Resolução de inconsistências de posicionamento e bugs apontados nas artes anteriores.

---

### Atualização v[0.4.0] — Combate por Turnos, Atributos e Puzzles
#### Implementação, Correção e Aprimoramento
- **Sistema de 6 Atributos**: Implementação de Força, Destreza, Constituição, Intelecto, Sabedoria e Presença.
- **Catálogo JSON**: Carregamento dinâmico de `skills.json`, `bestiario.json` e `condicoes.json`.
- **Arena de Batalha**: Combate por turnos com controles híbridos (Mouse/Teclado), barras interpoladas e textos flutuantes.
- **Gestão de Mana Inimiga**: Inimigos e Chefes agora consomem MP para habilidades especiais.
- **Puzzles no Overworld**: Desobstrução física de rochas na Estrada 2 via magia e interação direta `[E]`.
- **Blindagem de Saves**: Preservação de saves manuais sem sobreescrita indesejada e reinício estrito de memórias em Novos Jogos.

---

### Atualização v[0.4.1] — Ações Táticas e Balanceamento de Turnos
#### Implementação, Correção e Aprimoramento
- **Submenu Concentrar**: Inclusão de ações táticas (*Foco Espiritual* para recuperar MP e *Defender* para mitigar dano e esquivar).
- **Fila Única de Iniciativa**: Cálculo de turnos round-robin impedindo ataques duplos de inimigos consecutivos.
- **Feedback de Evasão**: Destaque visual e mensagens dinâmicas de esquiva no histórico de combate.

---

### Atualização v[0.4.2] — Tela Inicial, Partículas e Otimizações
#### Implementação, Correção e Aprimoramento
- **Nova Identidade Visual da Tela Inicial**: Arte 32-bit RGBA com fundo preto puro e tipografia institucional.
- **Botões Gráficos Interativos**: Componente `BotaoGrafico` com cross-fade suave e respiração luminosa no hover.
- **Motor de Partículas**: Simulação orgânica de chuva com física senoidal e rotação individual (`animations.py`).
- **Aceleração em C**: Recorte ultrarrápido de sprites via máscaras nativas (`pygame.mask`) no `ResourceManager`.

---

### Atualização v[0.4.3] — Padrão Editorial, Diálogos e Sequências Solenes
#### Implementação, Correção e Aprimoramento
- **Estética Editorial Dark Fantasy**: Paleta padronizada (Carvão Profundo, Marfim e Cinza Linho) e fontes consolidadas (*Sunday*, *Contrail* e *Just Breathe*).
- **Diálogos com Retratos**: Suporte universal a retratos de NPCs/Halia e menu de escolhas em duas colunas.
- **Controles Unificados**: Minigames operados exclusivamente por **ESPAÇO** e avanços de diálogo por **ENTER/Mouse**.
- **Sequência de Memória**: Tela de despertar em 5 etapas com screen shake e partículas etéreas.
- **Indicadores de Interação**: Prompts flutuantes `[E]` renderizados na camada superior sobre alvos no mapa.

---

### Atualização v[0.5.0] — Inventário Completo, Crafting e Economia
#### Implementação, Correção e Aprimoramento
- **Hierarquia Polimórfica de Itens**: Classes especializadas para consumíveis, equipamentos, grimórios e materiais.
- **Interface de Bolsa**: 5 abas organizadas, contadores de quantidade/nível e tooltips dinâmicos em pergaminho.
- **Forja e Alquimia**: Sistema de crafting de receitas e aprimoramento de equipamentos até +5.
- **Mercador e Loja**: Sistema de compra e venda com estoque limitado e cálculo financeiro em tempo real.
- **Consumíveis em Combate**: Uso de poções de cura e frascos arremessáveis via submenu de itens.
- **Notificações Push**: Fila de toasts animados no topo da tela sem poluição visual.

---

### Atualização v[0.6.0] — Cenários Orgânicos, Arquitetura e Autotiling
#### Implementação, Correção e Aprimoramento
- **Autotiling Orgânico**: Transições suaves entre grama e terra, lago sereno com quinas curvadas e floresta densa.
- **Residência de Halia**: Paredes de madeira modulares, móveis proporcionais e porta frontal rústica nivelada.
- **Estrada 2 Repaginada**: Área de deslizamento com árvores caídas e barreira rochosa detalhada.
- **Filtro de Memória Dinâmico**: Transição suave e contínua de saturação conforme a recuperação da protagonista.

---

### Atualização v[0.7.0] — Refinamento Visual de Sprites, Demônios e Menu Dev
#### Implementação, Correção e Aprimoramento
- **Limpeza Completa de Sprites**: Remoção minuciosa de halos, ruídos e bordas brancas/cinzas em todas as 103 sprites de Halia e dos inimigos.
- **Demônios Inferior e Superior**: Renomeação oficial das criaturas (antigos Gulosinho e Gulosão) e reestruturação completa de suas pastas e fichas no Bestiário.
- **Correção da Marcha dos Inimigos**: Fim do bug onde monstros andavam de costas; ciclo de caminhada agora executa de forma suave e contínua encarando o jogador.
- **Repouso da Halia em Cutscenes**: Halia agora permanece imóvel em repouso direcional durante diálogos, cenas e marcha de inimigos, eliminando a corrida no lugar.
- **Redesign do Console de Desenvolvedor**: Painel interativo com filigranas pergaminho, fontes do jogo, suporte a mouse/teclado e remoção de emojis crus.
- **Sistema de Saves Aprimorado**: Registro da direção e estado de repouso no save, com miniaturas das sprites e indicadores de progresso na tela de slots.

---

### Atualização v[0.7.1] — Ambientação Florestal e Efeitos de Folhas
#### Implementação, Correção e Aprimoramento
- **Efeito de Folhas Verdes no Cenário**: Partículas orgânicas flutuando com velocidade senoidal, brisa suave e giro contínuo para enriquecer a atmosfera do overworld.
- **Isolamento da Residência de Halia**: Exclusão da área interna da casa contra a queda de folhas, garantindo que o quarto e móveis fiquem protegidos sob o teto.
- **Limpeza Tática de Combate**: Manutenção da arena de batalha limpa e sem interferência visual de folhas caindo durante os turnos de combate.

---

### Atualização v[0.7.2] — Poética Visual: Pétalas, Datilografia e Ritmo de Combate
#### Implementação, Correção e Aprimoramento
- **Introdução Datilografada com Pétalas**: Narrativa de abertura com efeito máquina de escrever (typewriter), layout estável anti-oscilação, cursor editorial piscante e chuva de pétalas do menu principal sob fundo Carvão Profundo.
- **Memórias e Flashbacks Imersivos**: Textos do *Eco do Passado* e pensamentos de Halia agora são revelados caractere por caractere com chuva suave de pétalas de memória e aceleração interativa (`Enter`, `Espaço` ou clique do mouse).
- **Transição de Cenários Aprimorada**: Brisa atmosférica de pétalas flutuando durante o fade, acompanhada de títulos de capítulos e locais datilografados sobre ornamentação botânica com opção de avanço dinâmico.
- **Motor de Partículas Modular**: Adicionado `alpha_multiplicador` dinâmico em tempo real, método `reiniciar()` para reposicionamento instantâneo e suporte a `**kwargs` em `EfeitoPetalas` para escalas e velocidades personalizadas.
- **Regeneração de Mana em Combate**: Inimigos agora regeneram mana adequadamente a cada passagem de turno baseando-se no atributo de Sabedoria, com animação de barra interpolada, feedback flutuante na arena e IA tática para concentração.