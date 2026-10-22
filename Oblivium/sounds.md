# ◈ Guia Geral de Áudio e Sonoplastia — Oblivium ◈

Este documento cataloga todos os recursos sonoros (trilhas musicais, ambientes e efeitos sonoros) necessários para o jogo, especificando nomes de arquivo esperados pelo `AudioManager`, diretórios de destino, especificações técnicas e as referências originais de inspiração.

---

## 📁 Estrutura de Diretórios de Áudio

Todos os arquivos devem ser colocados dentro de `Oblivium/assets/audio/`:

```
Oblivium/assets/audio/
├── music/               # Trilhas musicais de fundo (BGM) e temas de cutscenes
├── ambience/            # Efeitos sonoros contínuos em loop (BGS / Clima / Ambientes)
└── sfx/                 # Efeitos sonoros pontuais (SFX)
    ├── ui/              # Navegação, cliques e confirmações de interface
    ├── combate/         # Golpes, danos, magias, esquivas e impactos
    ├── mundo/           # Portas, passos, interações com cenário
    └── itens/           # Coleta de itens, uso de poções e inventário
```

> **Formatos recomendados:**
> - **Músicas e Ambientes:** Formato `.ogg` (ou `.mp3`), taxa de amostragem de 44.1 kHz, estéreo, com pontos de loop limpos.
> - **Efeitos Sonoros (SFX):** Formato `.ogg` ou `.wav` (PCM 16-bit), sem silêncio no início ou final do arquivo.

---

## 🎼 1. Trilhas Musicais (BGM)
*Diretório:* `assets/audio/music/`

| Nome do Arquivo Esperado | Faixa de Referência (Inspiração) | Trecho / Momento no Jogo | Link de Referência |
| :--- | :--- | :--- | :--- |
| `menu_tema.ogg` | *Tema Melancólico / Dark Fantasy* | Menu Principal, Seleção de Saves e Controles | — |
| `cutscene_intro.ogg` | **For 1000 Years** (Frieren OST) | Cena de introdução do jogo (trecho inicial) | [[Spotify]](https://open.spotify.com/intl-pt/track/5REuZbHvPSPieO9GmI9cTT) |
| `casa_halia.ogg` | **Life is Worth Living** (Frieren OST) | Despertar e exploração da cabana de Halia | [[Spotify]](https://open.spotify.com/intl-pt/track/25LDFStf0IOKR5CKkW7X4o) |
| `estrada_floresta.ogg` | **Life is Worth Living** (Frieren OST) | Exploração externa das Estradas 1 e 2 | [[Spotify]](https://open.spotify.com/intl-pt/track/25LDFStf0IOKR5CKkW7X4o) |
| `cutscene_magia.ogg` | **Life and Legacy** (Frieren OST) | Momento do despertar e descoberta da magia | [[Spotify]](https://open.spotify.com/intl-pt/track/1kFcdw9X2f2jJ8h6xY8pPq) |
| `combate_comum.ogg` | **Skirmish** (Frieren OST) | Luta contra demônios inferiores / monstros comuns | [[Spotify]](https://open.spotify.com/intl-pt/track/14bU8u65T3Wq3l3q3q3q3q) |
| `combate_chefe.ogg` | **Demon's Bane** (Frieren OST) | Luta contra demônios superiores / chefes de área | [[Spotify]](https://open.spotify.com/intl-pt/track/14bU8u65T3Wq3l3q3q3q3q) |
| `combate_dragao.ogg` | **Dragon Smasher** (Frieren OST) | Batalha climática contra o dragão ancestral | [[Spotify]](https://open.spotify.com/intl-pt/track/1Bn5xNMZYDfUk5e1eisPei) |
| `vitoria.ogg` | *Fanfarra Curta de Vitória (~4s)* | Tela de vitória e recompensas pós-batalha | — |
| `derrota.ogg` | *Jingle Fúnebre de Game Over (~5s)* | Queda de Halia e tela de derrota | — |
| `cutscene_final.ogg` | **Journey Of a Lifetime** (Frieren OST) | Última cena e encerramento do jogo | [[Spotify]](https://open.spotify.com/intl-pt/track/0ZpugAMYdppMFqp8FAGidT) |

---

## 🍃 2. Sons de Ambiente Contínuos (BGS)
*Diretório:* `assets/audio/ambience/`  
*Características:* Devem tocar em loop contínuo suave, sem estalos na junção.

| Nome do Arquivo Esperado | Descrição Sonora | Momento de Uso no Jogo |
| :--- | :--- | :--- |
| `vento_noite.ogg` | Vento noturno suave soprando entre galhos e folhagens | Exploração noturna (sistema de clima) |
| `chuva.ogg` | Chuva moderada contínua com gotas na relva e pedras | Clima de chuva ativo no mapa |
| `tempestade.ogg` | Chuva forte com ventania e trovões ocasionais | Clima tempestuoso |
| `lareira.ogg` | Crepitar suave de brasa, fogo e lenha queimando | Interior da cabana de Halia e fogueiras |

---

## 🖱️ 3. Efeitos Sonoros de Interface (UI)
*Diretório:* `assets/audio/sfx/ui/` *(ou diretamente em `assets/audio/sfx/`)*

| Nome do Arquivo Esperado | Descrição Sonora | Momento de Uso no Jogo |
| :--- | :--- | :--- |
| `ui_cursor.ogg` | Toque sutil, tecla de madeira suave ou clique tátil | Navegar com teclado/mouse entre menus, botões e opções |
| `ui_confirmar.ogg` | Ressonância positiva metálica/mágica suave | Confirmar escolhas, avançar diálogos e aceitar ações |
| `ui_voltar.ogg` | Tom suave descendente de desmarcação | Tecla ESC, retornar menus e fechar janelas |
| `ui_erro.ogg` | Tom abafado de recusa/bloqueio | Ação bloqueada, mana insuficiente ou comando inválido |
| `ui_dialogo.ogg` | Blip sutil ultra-curto (~15 a 25ms) | Efeito de datilografia na exibição do texto dos NPCs |

---

## 🚪 4. Efeitos Sonoros de Mundo e Exploração
*Diretório:* `assets/audio/sfx/mundo/` e `assets/audio/sfx/itens/`

| Nome do Arquivo Esperado | Descrição Sonora | Momento de Uso no Jogo |
| :--- | :--- | :--- |
| `porta_abrir.ogg` | Trinco de ferro destrancando e ranger de madeira | Entrar na casa de Halia ou interiores |
| `porta_fechar.ogg` | Batente suave e fecho de porta de madeira | Sair de interiores para os mapas externos |
| `item_coletar.ogg` | Brilho sonoro metálico e suave | Apanhar itens, baús e recursos do chão |
| `pocao.ogg` | Desrolhar frasco de vidro e absorção de energia | Ingerir poção de cura/mana no inventário ou batalha |
| `passos_grama.ogg` *(opcional)* | Passadas sutis em vegetação/terra | Movimentação a pé de Halia no mapa |

---

## ⚔️ 5. Efeitos Sonoros de Combate
*Diretório:* `assets/audio/sfx/combate/`

| Nome do Arquivo Esperado | Descrição Sonora | Momento de Uso no Jogo |
| :--- | :--- | :--- |
| `acerto.ogg` | Impacto seco de golpe físico de lâmina/cajado | Acerto de ataque corpo a corpo no oponente |
| `dano_inimigo.ogg` | Som de carne/armadura atingida e corte | Inimigo sofrendo dano |
| `dano_halia.ogg` | Golpe pesado e som cortante | Halia sofrendo dano e efeito visual de sangue |
| `critico.ogg` | Impacto forte e estrondoso com agudo de energia | Golpe crítico desferido em batalha |
| `ataque_erro.ogg` | Som de vento cortante rápido (*woosh*) | Golpe errando o alvo |
| `esquiva.ogg` | Deslizamento rápido e movimento ágil | Halia ou inimigo desviando de ataque |
| `magia.ogg` | Zumbido etéreo e projeção de energia arcana | Disparo de magias ofensivas |
| `concentrar.ogg` | Tom grave de foco e aura mágica de proteção | Halia usando comando Concentrar / Guarda |
| `morte_inimigo.ogg` | Dissipação etérea, colapso ou desintegração | Finalização da animação de morte do monstro |
| `fuga.ogg` | Passadas rápidas com rajada de vento | Fugir com sucesso de um combate |

---

## ⚙️ Como o Sistema Processa os Arquivos

1. **Busca Automática:** O `AudioManager` busca os arquivos pelo alias amigável (ex: `"ui_cursor"`, `"combate_comum"`), checando automaticamente as extensões `.ogg`, `.wav` e `.mp3` nas pastas correspondentes.
2. **Fallback Silencioso:** Se um arquivo ainda não tiver sido inserido na pasta, o motor **não trava** e **não gera ruídos sintéticos**, permanecendo silencioso até que o arquivo real seja adicionado.
3. **Canais Independentes:**
   - **BGM:** Canal de música do Pygame com transição suave (`fade_ms`).
   - **BGS:** Canal reservado `CANAL_AMBIENTE_ID = 0` para sons contínuos de clima.
   - **SFX:** Até 32 canais dinâmicos simultâneos para efeitos sonoros rápidos sem corte.
