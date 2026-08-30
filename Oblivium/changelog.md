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
