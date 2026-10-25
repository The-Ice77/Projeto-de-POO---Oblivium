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

---

### Atualização v[0.7.7] — Aerodinâmica Orgânica e Voo Tranquilo da Fauna
#### Implementação, Correção e Aprimoramento
- **Voo Tranquilo, Sereno e Contemplativo (`Passaro`)**: Reformulação completa da velocidade de voo e ritmo de asas. A velocidade horizontal foi calibrada para uma faixa calma de 62 a 78 px/s (com elevação suave de 22 a 28 px/s), permitindo ao jogador apreciar a travessia aérea do pássaro pelo cenário sem disparar como um míssil.
- **Cadência Suave de Batimento de Asas**: Redução da velocidade da animação (`0.15`), conferindo um ritmo relaxado e elegante às asas (~2.3 batimentos por segundo), com ciclos visíveis de abertura e sustentação.
- **Micro-Flutuação Orgânica em Sincronia de Asas**: Flutuação vertical puramente sincronizada com a fase de empuxo das asas ($\pm 1.2\text{px}$ casado com a batida para baixo), simulando sustentação biológica real e eliminando tremores ou oscilações de alta frequência.
- **Preservação e Nitidez da Pixel Art**: Eliminação de rotações angulares fracionárias contínuas que causavam distorção de pixel e tremor em 1px. O pássaro utiliza sua postura diagonal nativa desenhada pelo artista ($20^\circ$ ascendente), mantendo a silhueta 100% nítida e estável.
- **Pouso em Planeio Gracioso**: Ao descer para o ninho (`pousando`), o pássaro plana com batimentos mais espaçados (`0.12`), desacelerando gradualmente nos últimos metros até pousar delicadamente na relva.
- **Correção dos Frames de Animação de Voo**: Restauração da opacidade total nos frames `voo_06.png` e `voo_07.png`, eliminando o bug de semi-transparência intermitente.

---

### Atualização v[0.7.8] — Efeitos de Sangue e Animações de Morte
#### Implementação, Correção e Aprimoramento
- **Efeito de Sangue em Halia**: Disparo dos efeitos visuais de sangue (`sangue_1` a `sangue_5`) sobre o torso de Halia ao sofrer dano em combate.
- **Animações de Morte dos Inimigos**: Reprodução completa do ciclo de colapso e dissolução suave dos monstros derrotados na arena.
- **Estabilidade de Posições na Arena**: Fixação das coordenadas táticas dos inimigos durante a batalha, evitando solavancos com a queda de oponentes.
- **Correção de Aliases de Animação**: Mapeamento unificado dos estados `dead`, `morte` e `morrer` nas classes base e no `ResourceManager`.

---

### Atualização v[0.7.9] — Interface e Arquitetura de Áudio
#### Implementação, Correção e Aprimoramento
- **Barras de Volume das Configurações**: Desacoplamento da coordenada horizontal das barras de volume em relação ao tamanho do texto numérico, garantindo alinhamento fixo e independente.
- **Reação do Mouse na Seleção de Controles**: Ajuste no hover dos cards da tela de seleção de controles para responder estritamente quando o ponteiro estiver sobre eles.
- **Limpeza do Gerenciador de Áudio**: Remoção dos bipes e efeitos sonoros sintéticos procedurais, mantendo o motor limpo, silencioso e preparado para os arquivos de som oficiais.

---

### Atualização v[0.8.0] — Desacoplamento de Textos de Combate
#### Implementação, Correção e Aprimoramento
- **Isolamento de Textos em JSON**: Criação de `src/data/combat_texts.json` centralizando mensagens de morte, ações, avisos de mana e banners de vitória/derrota.
- **Classe CombatNarrator**: Módulo desacoplado para carregar e formatar dinamicamente a narrativa do combate.
- **Refatoração do Motor de Combate**: Remoção de dezenas de strings hardcoded de `combat.py`.

---

### Atualização v[0.8.1] — Desacoplamento da Renderização de Combate
#### Implementação, Correção e Aprimoramento
- **Módulo CombatRenderer**: Criação de `src/mechanics/combat_renderer.py` isolando todo o pipeline de renderização gráfica do combate (cenário, sprites 2.5D, barras de vida/mana interpoladas, submenus com paginação, tooltips de habilidades e banners).
- **Redução e Modularização**: Redução de ~585 linhas em `combat.py` (de ~2.022 para ~1.436 linhas), transformando a classe principal em um motor focado em turnos e regras de batalha.
- **Sincronização de Hitboxes**: Manutenção das referências de colisão e retângulos interativos para preservação completa dos controles por mouse e teclado.

---

### Atualização v[0.8.2] — Desacoplamento de Entradas e Navegação de Menus
#### Implementação, Correção e Aprimoramento
- **Módulo CombatInputHandler**: Criação de `src/mechanics/combat_input.py` centralizando a escuta de eventos de teclado, cliques e rolagem de mouse (scroll).
- **Gerenciamento de Navegação e Submenus**: Transferência das rotinas de abertura e rolagem dos menus de Ataque, Magia, Concentração, Itens e Alvo para o novo controlador.
- **Modularização Profunda**: Redução adicional de 463 linhas em `combat.py` (de 1.436 para 973 linhas), consolidando a meta de manter o arquivo abaixo de 1.000 linhas.

---

### Atualização v[0.8.3] — Modularização do Inventário e Persistência de Saves
#### Implementação, Correção e Aprimoramento
- **Módulo SaveManager Centralizado**: Extração da persistência, serialização/desserialização de entidades, blindagem de autosaves e reinicialização de novo jogo da classe `Game` para `src/core/save_manager.py`. Redução de ~256 linhas em `game.py` (de 573 para 317 linhas).
- **Verificação de Integridade de Slots**: Adição de rotina defensiva `verificar_integridade_slot()` no `SaveManager` para validação estrutural e verificação de integridade de JSON e esquema de dados antes do carregamento.
- **Renderizadores Modulares de Abas**: Criação do pacote `src/states/inventory_tabs/` com renderizadores gráficos desacoplados:
  - `tab_inventario.py` (`TabInventarioRenderer`): Equipamentos arcanos, slots de Grimórios, grelha da bolsa e sub-abas.
  - `tab_perfil.py` (`TabPerfilRenderer`): Barras interpoladas de HP/MP, carteira decomposta, parâmetros derivados e ficha de atributos D20.
  - `tab_magia.py` (`TabMagiaRenderer`): Grimório de magias com scroll, escalamento arcano de intelecto e badges.
  - `tab_crafting.py` (`TabCraftingRenderer`): Bancada selada de criação, forja e manipulação de reagentes.
- **Redução em inventory_states.py**: Redução de 420 linhas no arquivo principal do menu de inventário (de 974 para 554 linhas), preservando 100% da compatibilidade de eventos, cliques e interfaces.

---

### Atualização v[0.9.0] — Sistema de Conquistas & Rastreador de Missões
#### Implementação, Correção e Aprimoramento
- **Sistema de Conquistas Estilo Steam**:
  - Armazenamento global e persistente em `saves/conquistas.json`, independente de slots de save individuais.
  - Catálogo de 15 conquistas narrativas e de gameplay com auto-desbloqueio da Platina (`mestre_platinador`).
  - Integração visual com botões artísticos dedicados (`16.png` e `17.png`) no Menu Principal e Menu de Pausa.
  - Nova tela `ConquistasState` com medidor de platina, filtros contextuais (*Todas*, *Desbloqueadas*, *Bloqueadas*), rolagem fluida e cartões ornamentados Dark Fantasy.
- **Notificações Push Centralizadas**:
  - Reposicionamento das notificações de brinde do canto superior direito para o topo central (`centro superior`), com animação slide-down e coroa dourada especial para conquistas.
- **Rastreador de Missões (Quest Tracker HUD)**:
  - Sistema de missões com ciclo de vida `DISPONIVEL` -> `ATIVA` -> `CONCLUIDA` em `src/mechanics/quest_manager.py`.
  - HUD minimalista no canto superior direito (`x=981, y=22`) com esmaecimento de proximidade quando Halia se aproxima, recolhimento/expansão via tecla `[J]` ou clique, e altura dinâmica.
  - Catálogo inicial de missões da vila em `src/data/missoes.json` (*O Refúgio de Oakhaven*, *Reagentes para a Cura*, *Ronda nas Fronteiras*).
- **Proteção e Redefinição de Dados**:
  - Adição da opção defensiva "Redefinir Dados..." no menu de configurações com modal solene de confirmação com dois passos (foco padrão em "Cancelar").
  - Limpeza atômica de todos os 4 slots de save (incluindo autosaves) e redefinição de todas as conquistas do jogo.
- **Integração Completa de Gatilhos de Gameplay**:
  - Vinculação de gatilhos automáticos para todas as 15 conquistas (movimento inicial na casa, itens coletados, partida na carruagem, pássaro assustado, flashback de memória, quebra-cabeças de Levitação e Bola de Fogo, vitória e foco tático em combate, nível 2 de sincronia, fabricação de receitas e aceitação de missões).

---

### Atualização v[0.9.1] — Ritual Ígneo, Levitação QTE e Rebalanceamento de Inimigos
#### Implementação, Correção e Aprimoramento
- **Puzzle da Bola de Fogo (Ritual da Tríplice Fagulha)**:
  - Reformulação completa de `MinigameTiming` para um ritual em 3 etapas progressivas (*Fagulha Inicial*, *Combustão Térmica* e *Ignição Plena Devastadora*).
  - Cada etapa acelera o cursor e estreita a zona crítica de calor, com orbes visuais de progresso e explosões de fagulhas em caso de sucesso.
- **Puzzle da Levitação Gravitacional com Quick Time Events (QTE Rítmico)**:
  - Substituição do mash simples por um sistema rítmico de runas gravitacionais (`W`, `A`, `S`, `D`, `ESPAÇO`) em `MinigameMash`.
  - Glifo rúnico com anel temporal dinâmico em arco e feedback de acerto/erro.
  - Movimentação das rochas no cenário de Estrada 2 sincronizada diretamente em tempo real: acertos impulsionam as pedras para as margens (+24%), enquanto erros e expiração de tempo provocam perda de sustentação e decaimento com poeira.
- **Rebalanceamento de Inimigos**:
  - **Demônios Inferiores**: Vida base fortalecida de 30 para 42, dano base aumentado de 8 para 11, e atributos calibrados para garantir combates mais desafiadores na Estrada 2.
  - Sincronização dos valores de fallback na `EnemyFactory`.
- **Acessibilidade e Controles Unificados**:
  - Suporte híbrido completo tanto por teclado quanto por cliques de mouse em ambos os novos minigames de magia.

---

### Atualização v[0.9.2] — Progressão de Levitação, Silenciamento de Dev Toasts e Testes de Banners
#### Implementação, Correção e Aprimoramento
- **Correção da Progressão Narrativa na Levitação**:
  - Solução definitiva para a interrupção após o minigame gravitacional: criação do método `_finalizar_minigame_levitacao()` invocado imediatamente tanto pelo processamento de eventos (teclado/mouse) quanto pelo loop de atualização.
  - As rochas assentam com precisão nas margens da pista, a conquista `levitacao` é desbloqueada, o diálogo `pos_levitar` é disparado e a transição para a cutscene e combate do Demônio Superior prossegue sem travas.
- **Console Dev Aprimorado e Silencioso**:
  - Removidos os toasts/notificações intrusivas disparados na tela durante o acionamento de atalhos no Dev Menu; o feedback agora é enviado limpo para o console de desenvolvimento (`print("[DEV] ...")`).
  - Grade visual expandida para 10 comandos em 2 colunas x 5 linhas com diagramação Dark Fantasy refinada (880x510px).
- **Novas Opções de Teste no Dev Menu**:
  - **Opção `[ 9 ]` Testar Conquista**: Dispara o banner Steam-style estilizado no topo da tela alternando ciclicamente entre conquistas normais e a Platina real (`⚜`).
  - **Opção `[ 0 ]` Testar Missão**: Ativa/avança missões no Rastreador (Quest Tracker HUD) e dispara o banner comemorativo de objetivos.
- **Refinamento de Paleta Dark Fantasy**:
  - Substituição de tons dourados e amarelos saturados na tela de conquistas e badges por tons nobres de Prata Arcana (`#d0daf0` e `#8fa0c0`), Marfim Offwhite e Cinza Linho, harmonizando com a estética gótica de Oblivium.

---

### Atualização v[0.9.3] — Calibragem de Demônios, Puzzles de Magia e Controle de Missões
#### Implementação, Correção e Aprimoramento
- **Rebalanceamento dos Demônios**:
  - **Demônio Inferior** (`demonio_inferior`, `sombra_menor`, `gulosinho`): Redução sutil de dificuldade para suavizar combates em dupla (`vida_base` de 42 para 36, `dano_base` de 11 para 9, Força 10, Destreza 12 e Constituição 10).
  - **Demônio Superior** (`demonio_superior`, `anomalia_maior`, `gulosao`, `Boss`): Fortalecimento moderado para preservar sua imponência como Chefe (`vida_base` de 64 para 78, `mana_base` 55, `dano_base` de 12 para 15, Força 14, Destreza 12, Constituição 14, Intelecto 13 e Presença 14), além de calibragem nas habilidades `impacto_anomalo` e `onda_corrosiva`.
- **Ajuste de Dificuldade dos Puzzles de Magia**:
  - **Bola de Fogo (`MinigameTiming`)**: Tornado mais acessível com redução da velocidade do cursor nas 3 etapas (`5.5`, `7.5` e `9.5`), ampliação das zonas de acerto (`110px`, `84px` e `60px`) e reinício previsível do cursor na base a cada etapa.
  - **Levitação Gravitacional (`MinigameMash`)**: Tornado mais desafiador com janela de reação mais exigente (`62` ticks base reduzindo até `38` ticks em sequência), maior inércia gravitacional (`-0.14`/frame), ganho de `+13.5%` por acerto (exigindo ~7 a 8 acertos) e penalidade de `-20%` por falha.
- **Controle de Ativação e Teste de Missões**:
  - Vinculação direta ao `QuestManager` (`game.missoes` / `game.quest_manager`) com suporte ao ciclo completo do catálogo (`missao_boas_vindas`, `missao_ervas_medicinais`, `missao_ronda_fronteiras`).
  - Adição do controle configurável **Missões `[J]`** (ativa missão inicial ou recolhe/expande o Quest Tracker HUD) e atalho rápido **`[M]`** / **`[0]` no Dev Menu** para ativar missões e avançar objetivos etapa por etapa em tempo real.

---

### Atualização v[0.9.4] — Quest Tracker Simultâneo (1 Principal + 1 Secundária), Curadoria de Conquistas & Ícones Procedurais
#### Implementação, Correção e Aprimoramento
- **Desassociação de Teclas de Teste e Atalho `[O]` para Missões**:
  - Desassociadas as teclas de teste do gameplay livre; a tecla oficial **`[O]` (`pygame.K_o`)** agora é dedicada exclusivamente a **minimizar e expandir** o HUD de Missões durante a exploração.
  - O controle de ativação/progresso rápido de missões permanece centralizado no Console de Desenvolvedor (`'` -> opção `[0]`).
- **Quest Tracker Ampliado com 1 Missão Principal + 1 Secundária Simultâneas**:
  - Regra de negócio aplicada no `QuestManager`: o jogador pode manter ativas simultaneamente no máximo **1 Missão Principal** e **1 Missão Secundária**.
  - `QuestTracker` redimensionado (`350px` de largura, tipografia ampliada `18pt`/`20pt`/`16pt` e alto contraste) exibindo **ambas as missões ativas juntas** na tela, separadas por divisória ornamentada e identificadas por insígnias procedurais (`Principal` em âmbar dourado e `Secundária` em prata azulada).
- **Curadoria de Conquistas Especiais e Únicas**:
  - Remoção das conquistas triviais de início de jogo (dar 1 passo no quarto, coletar moedas iniciais, pegar o cajado básico, falar com o carroceiro, assustar pássaro).
  - Consolidação de **10 marcos realmente significativos** em `conquistas.json`, incluindo *Caçadora do Abismo* (`cacadora_abissal`, ao derrotar o Demônio Superior) e *Cumpridor de Promessas* (`cumpridor_promessas`, ao concluir integralmente uma missão).
- **Geração Procedural de Ícones e Emblemas via Código (`ui_utils.py`)**:
  - Eliminação de blocos vazios e glifos Unicode ausentes nas fontes customizadas (`sunday.ttf` / `contrail.ttf`).
  - Criação de geradores vetoriais procedurais para **todos os 10 emblemas de conquistas**, **botões de fechar `[X]`**, **botões de minimizar/expandir `[-]`/`[+]`**, **moedas de Ouro/Prata/Cobre** e **ilustrações dos slots de Equipamentos e Grimórios**.

---

### Atualização v[0.9.5] — Refatoração Arquitetural de Artes (`IconRegistry` & `TilemapBuilder`) e Polimento do HUD/Inventário
#### Implementação, Correção e Aprimoramento
- **HUD e Inventário**:
  - Remoção do bloco lateral ao lado das barras de status (`HP`/`MP`) da Halia no `HUD`, tornando o painel superior esquerdo mais limpo e compacto (`250x78` px).
  - Preservação dos ícones antigos para os slots de Equipamentos (`ROUPA`, `CAJADO`, `ACESSORIO_1`, `ACESSORIO_2`) e Grimórios (`GRIMORIO`).
  - Nos itens da Bolsa e da Loja, utilização estrita apenas das sprites oficiais de itens que existem no projeto (`props/Cajado.png` e `props/Grimório.png`), mantendo o modelo original de **apenas texto** para itens que não possuem sprite própria.
- **Refatoração Arquitetural (Padrão *Flyweight* / *Factory* e Princípio da Responsabilidade Única — SRP)**:
  - Criação do [`IconRegistry`](Oblivium/src/ui/icon_registry.py): centraliza a resolução de sprites oficiais de itens e gera **uma única vez em cache (`pygame.Surface` RGBA)** todos os ícones procedurais (conquistas, notificações, moedas, marcadores de missão e slots), eliminando recálculos geométricos a cada frame (60 FPS).
  - Limpeza de [`ui_utils.py`](Oblivium/src/ui/ui_utils.py): focado exclusivamente em primitivas de layout, barras interpoladas, quebras de texto e `BotaoGrafico`.
  - Criação do [`TilemapBuilder`](Oblivium/src/maps/tilemap_builder.py): extração da lógica de composição de terrenos, estradas e autotiling que antes sobrecarregava o [`ResourceManager`](Oblivium/src/utils/resource_manager.py).
  - Unificação do roteamento de persistência em `PlayingState` e `SlotsState` através da instância orientada a objetos `game.save_manager` ([`SaveManager`](Oblivium/src/core/save_manager.py)).
