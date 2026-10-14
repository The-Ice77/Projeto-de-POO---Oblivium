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

---

### Atualização v[0.7.3] — Fauna Viva, Sistema Climático e Pirotecnia Arcana
#### Implementação, Correção e Aprimoramento
- **Fauna Viva na Estrada 1 (`PassaroAmbiente`)**: Adição de passarinhos empoleirados na grama da Estrada Rural com IA viva de descanso, bicar de sementes e pulinhos orgânicos. Ao notar a aproximação de Halia (< 110px), eles alçam voo batendo asas em curva diagonal suave, com sombras 2.5D que diminuem com a altitude e retorno gradual ao solo.
- **Sistema Climático Modular (`EfeitoChuva`)**: Criação do gerenciador de clima com suporte a Chuva Comum e Chuva Pesada (Tempestade). Utiliza as texturas originais do projeto (`rain light`, `rain dark` e `rain splash`), física rápida de vento, splashes de respingos no solo, filtro atmosférico Dark Fantasy e relâmpagos esporádicos na tempestade. Suporte a zonas protegidas (sem chuva dentro de casas) e atalho no Dev Console (`C` ou `9`).
- **Minigame de Levitação Reativo em Tempo Real**: O minigame agora responde tanto a toques de teclado (`Espaço`) quanto a cliques contínuos do mouse. As rochas de bloqueio no cenário movem-se fisicamente em tempo real: ao clicar, erguem-se no ar e avançam para as margens desobstruídas; ao soltar o clique, o decaimento faz as pedras descerem suavemente e voltarem para a posição original de bloqueio.
- **Efeitos Visuais Claros de Levitação nas Pedras**: Projeção de sombras 2.5D dinâmicas no chão (encolhendo com a elevação), círculos rúnicos e anéis de gravidade concêntricos girando na base do solo, auras luminosas azuis/ciano com pulso de energia ao redor das rochas e partículas arcanas ascendentes.
- **Bola de Fogo Cinematográfica e Impacto Destrutivo**: Projétil animado multicamadas em voo veloz emitindo rastro dinâmico de fagulhas e brasas crepitantes. No impacto, screen shake vigoroso, clarão de detonação com anéis de onda de choque e fragmentos de pedra ejetados em arcos balísticos.
- **Bagunça e Chamas no Ambiente com Sprites de Fogo**: A desobstrução por fogo agora acende múltiplos focos de incêndio animados no cenário da Estrada 2 utilizando diretamente as sprites oficiais do projeto (`chama_fogueira_larga`, `chama_coluna_fogo`, `chama_braseiro_medio`, `chama_fogo_pequeno` e `chama_fagulhas_brasas`) com marcas de fuligem no chão e brasas crepitantes no ar.

---

### Atualização v[0.7.4] — Arquitetura de Fauna POO, Chamas Autônomas, Clima Invernal e Polimento de Levitação
#### Implementação, Correção e Aprimoramento
- **Hierarquia Abstrata de Animais (`Animal(Entidade, ABC)`)**: Refatoração da arquitetura biológica do jogo. `Animal` agora é uma classe abstrata herdando diretamente da entidade base `Entidade` (`Entity.py`). Possui métodos concretos para animação, detecção de proximidade do jogador e projeção de sombras, e métodos abstratos (`reagir_ao_jogador`, `atualizar_comportamento`). Implementação robusta de `Passaro(Animal)` e criação da base para `Gato(Animal)` (aproveitando as sprites de gatos do projeto). Proxy retrocompatível em `src/entities/passaro.py`.
- **Ajuste Fiel das Sombras dos Pássaros**: Redesenho da projeção de sombra: formato elíptico proporcional e delicado (6x3 px), opacidade suave (alpha 65), fixado na base dos pezinhos no solo. A sombra atenua suavemente e desaparece quando o pássaro alça voo acima de 40px de altitude, eliminando saltos visuais, bugs de decolagem e sombras desproporcionais.
- **Organização e Padronização de Sprites (Fogo, Explosão e Sangue)**: Reorganização de todos os novos recursos fornecidos pelo jogador. Criação de pastas padronizadas em `assets/efeitos/explosao/` (`explosao_1`: 50 frames, `explosao_2`: 33 frames, `explosao_3`: 33 frames) e `assets/efeitos/sangue/` (`sangue_1` a `sangue_5`: 30 frames cada). `ResourceManager` aprimorado com ordenação natural por regex e tolerância de carregamento sem modo de vídeo inicializado.
- **Explosão Real com Nova Sequência de Sprites**: Integração dos 50 frames da `explosao_1` (100x100px) diretamente no `CutsceneManager`. O impacto da bola de fogo agora reproduz a sequência completa de detonação com escala 180x180px, complementada por choque térmico expansivo, screen shake vigoroso e fragmentos rochosos arremessados pelos ares.
- **Chamas Reais e Independentes (`ChamaIndependente`)**: Criação da entidade POO `ChamaIndependente` (`src/entities/chama.py`) para os focos de fogo do overworld. Cada chama opera de modo autônomo com ciclo de animação dessincronizado, micro-respiração térmica individual, iluminação quente (glow) pulsando de forma orgânica no solo e emissão própria de brasas e fagulhas no ar.
- **Sistema Climático Invernal: Neve e Nevasca**: Expansão do `EfeitoChuva` com suporte aos modos `MODO_NEVE` e `MODO_NEVASCA` utilizando a textura oficial `snowflake(1).png`. Flocos com oscilação senoidal lateral (sway), rotação gradual, turbulência gélida, véu translúcido frio e atalho no Dev Console (`C` ou `9`) ciclando entre Limpo -> Chuva Comum -> Tempestade -> Neve Suave -> Nevasca.
- **Fluxo de Vitória da Levitação (Pouso Imediato com Impacto Sem Replay)**: Ao vencer o minigame de levitação (`res == "VENCEU"`), as pedras não voltam mais para o meio da pista nem reexecutam a subida. Como o jogador já as conduziu até as margens, elas apenas assentam com firmeza no solo com puffs de poeira/terra e micro-tremor de solo. O fluxo marca `magia_ativa = "CONCLUIDO"`, abre diretamente o diálogo `pos_levitar` e segue o jogo sem repetições.

---

### Atualização v[0.7.5] — Sombra Orgânica 2.5D, Novas Chamas Laranjas e Pirotecnia Épica
#### Implementação, Correção e Aprimoramento
- **Física 2.5D e Sombra Rigorosa do Pássaro**: Padronização dos frames das animações em 32x32px com ponto pivô estável no centro horizontal (`x = 16`) e base de pés no solo (`bottom = 22`), todos voltados canonicamente para a direita. Eliminados os solavancos causados pela folha original onde o pássaro andava dentro do quadro. A sombra agora permanece milimetricamente alinhada com os pés no solo (`self.y + 6`), acompanhando a parábola de salto (`altitude` até 11px) e atenuando com precisão de profundidade 2.5D.
- **Pulo Orgânico Sem Travamento**: Calibrada a velocidade de avanço no solo (55 a 80 px/s) e a transição fluida entre repouso, impulso aéreo e pouso suave, sem que o pássaro fique preso ou teletransporte na troca de animações.
- **Chamas Laranjas 100% Íntegras Sem Cortes**: Identificada a causa-raiz onde o fatiamento anterior dividia as chamas ao meio horizontalmente. Todas as 8 variações de chamas laranjas foram re-extraídas em sua altura completa (até 46px), garantindo labaredas esguias, pontas de fogo ondulando e brasas de contato com o solo inteiramente preservadas, sem cortes em nenhuma das bordas.
- **Correção da Ancoragem e Estabilidade da Pixel Art**: Eliminação do bug de chamas enterradas no solo. O ponto de contato agora ancora com precisão a base da chama na superfície da terra (`self.y - fh`), com iluminação quente (glow) e emissão de fagulhas calibradas, sem distorção fracionária de escala.
- **Explosão Ampliada para Visualização Total**: Expansão do tempo de detonação no `CutsceneManager` para 85 ticks (~1.4s), permitindo apreciar todos os 50 frames da nova animação de explosão oficial com escala épica de 220px, onda de choque expansiva e dispersão balística de rocha estilhaçada.
- **Classe Base Abstrata para Props (`ElementoCenario(ABC)`)**: Criação de `src/entities/elemento_cenario.py` seguindo o mesmo padrão de POO adotado na fauna (`Animal`). Centraliza ancoragem no solo, dessincronização de animações, halos de luz (glow) dinâmicos e emissão autônoma de partículas. `ChamaIndependente` agora herda dessa classe base, abrindo espaço para futuras tochas, fontes e props interativos.
- **Limpeza de Arquitetura**: Remoção dos módulos legados `src/entities/passaro.py` e `src/entities/chama.py`, consolidando a fauna viva em `src/entities/animal.py` e os props de cenário em `src/entities/elemento_cenario.py`.

---

### Atualização v[0.7.6] — Panteão das Chamas Multicores, Pássaro Proporcional e Limpeza de Assets
#### Implementação, Correção e Aprimoramento
- **Extração Completa de Chamas Multicores**: Recorte sistemático e sem cortes de todas as variações cromáticas do asset pack oficial (`laranja`, `azul`, `verde`, `roxa`, `amarela`, `branca`) e variantes de fumaça (`fumaca_media`, `fumaca_fogueira`, `fumaca_mini`, `fumaca_coluna`, `fumaca_braseiro`). Total de 473 frames de fogo perfeitamente gerados e organizados em `assets/efeitos/fogo/`.
- **Suporte Nativo a Chamas Multicores (`ChamaIndependente`)**: Dicionário `CORES_CONFIG` expandido com iluminação dinâmica (glow interno e externo) e paletas temáticas de fagulhas para cada uma das 6 cores de chamas, permitindo invocar labaredas arcanas, azuis gélidas, místicas roxas ou brancas radiantes no cenário.
- **Validação Rigorosa de 100% dos Assets**: Teste automatizado de integridade via Pygame em todas as 739 imagens de efeitos (`fogo`: 60 pastas / 473 frames, `explosao`: 3 pastas / 116 frames, `sangue`: 5 pastas / 150 frames), confirmando 0 erros e ausência de cortes nas bordas.
- **Exclusão Segura da Pasta Estrangeira**: Comprovação de que todos os sprites e animações foram devidamente transferidos e recortados, seguida da remoção definitiva da pasta temporária `assets/fogo, explosão e sangue`, mantendo o diretório `assets/` limpo e padronizado.
- **Aumento Proporcional do Pássaro**: Introduzido suporte a fator de escala dinâmica na hierarquia de `Animal(Entidade, ABC)`. O `Passaro` foi ajustado com escala `1.35x` (passando de ~14px para ~19px na tela), com raio de sombra 2.5D ampliado proporcionalmente (`w=8`, `h=4`) e ancoragem perfeita no solo, garantindo presença visual mais nítida e harmoniosa na Estrada 1 sem perder o charme da pixel art.