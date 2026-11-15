# Guia Oficial de Áudio e Trilhas — Oblivium

Estado real da infraestrutura sonora integrada no jogo e gerenciada por [audio_manager.py](file:///Oblivium/src/core/audio_manager.py) com manifesto em [audio_manifest.json](file:///Oblivium/src/data/audio_manifest.json).

---

## 1. Trilhas Musicais Integradas (`assets/audio/music/*.ogg`)

Todas as 12 faixas fornecidas em `assets/audio/Trilha Sonora Oblivium/` (`11` `.m4a` + `1` `.mp3`) foram decodificadas em PCM 44.1 kHz estéreo, aparadas nos cortes musicais ativos sem fade-outs ou silêncios nas extremidades dos loops (`loop_padrao = -1`), niveladas por compressor/limitador suave e normalizadas com teto anti-clipping pós-codec (`clipped_samples = 0`, pico <= `-1.23 dBFS`) para **Ogg Vorbis estéreo 44.1 kHz (`-b:a 192k`)**, mantendo todos os arquivos-fonte originais intactos.

| Arquivo OGG | Origem | Título / Obra / Compositor | Recorte / Duração | Ganho / Pico / RMS | Contexto e Aliases |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `menu_tema.ogg` | `Kevin Penkin - OLD STORIES.m4a` | **OLD STORIES** — *Made in Abyss OST* (Kevin Penkin) | `1.85s–404.90s` (`403.06s`, loop contínuo) | `-1.67 dB` / `-4.00 dBFS` / `-19.00 dB` | `menu_tema` (Menu Principal, Slots, Pausa/Opções fora de cena) |
| `tema_intro.ogg` | `Evan Call - For 1000 Years.m4a` | **For 1000 Years** — *Frieren OST* (Evan Call) | `3.60s–130.80s` (`127.20s`, loop contínuo) | `+7.92 dB` / `-1.67 dBFS` / `-19.06 dB` | `tema_intro`, `cutscene_intro` (Introdução do Novo Jogo) |
| `tema_exploracao.ogg` | `Evan Call - Life Is Worth Living.m4a` | **Life Is Worth Living** — *Frieren OST* (Evan Call) | `3.15s–119.70s` (`116.55s`, loop contínuo) | `+15.53 dB` / `-2.02 dBFS` / `-19.00 dB` | `tema_exploracao`, `casa_halia`, `estrada_floresta`, `vila_oakhaven`, `tema_vila` (Cabana, Estradas, Orla Norte, Oakhaven e Reconstrução) |
| `tema_memorias.ogg` | `Evan Call - Life and Legacy.m4a` | **Life and Legacy** — *Frieren OST* (Evan Call) | `0.85s–149.40s` (`148.55s`, loop contínuo) | `+7.23 dB` / `-2.32 dBFS` / `-19.00 dB` | `tema_memorias`, `cutscene_magia` (Flashbacks e Tela de Despertar de Memória) |
| `combate_comum.ogg` | `Shiro SAGISU - Treachery.m4a` | **Treachery** — *Bleach OST* (Shiro SAGISU) | `0.35s–196.90s` (`196.55s`, loop contínuo) | `-4.19 dB` / `-3.51 dBFS` / `-17.60 dB` | `combate_comum` (Combates padrão e emboscada dos Mímicos) |
| `combate_chefe.ogg` | `Evan Call - Demon's Bane.m4a` | **Demon's Bane** — *Frieren OST* (Evan Call) | `0.45s–223.95s` (`223.50s`, loop contínuo) | `+1.46 dB` / `-1.28 dBFS` / `-17.61 dB` | `combate_chefe` (Reservada para mini-chefes/elites táticos e confrontos especiais) |
| `ataque_dragao.ogg` | `Ancient Magic_spotdown.org.mp3` | **Ancient Magic** — *Frieren OST* (Evan Call) | `0.38s–130.74s` (`130.36s`, loop contínuo) | `+1.03 dB` / `-1.23 dBFS` / `-17.84 dB` | `ataque_dragao` (Ataque aéreo de Ignis'Vahr em `CinematicaAtaqueDragao` e Oakhaven destruída pré-Ninho) |
| `combate_dragao.ogg` | `Evan Call - Dragon Smasher.m4a` | **Dragon Smasher** — *Frieren OST* (Evan Call) | `0.38s–109.20s` (`108.82s`, loop contínuo) | `-4.80 dB` / `-3.40 dBFS` / `-17.61 dB` | `combate_dragao` (Ninho do Dragão pré-chefe e batalha contra Ignis'Vahr) |
| `vitoria.ogg` | `Yasunori Nishiki - Victory Fanfare.m4a` | **Victory Fanfare** — *Octopath Traveler II OST* (Yasunori Nishiki) | `0.38s–4.25s` (`3.87s`, sem loop) | `-4.31 dB` / `-4.41 dBFS` / `-17.61 dB` | `vitoria` (Fanfarra concisa encerrada no fim da cadência de vitória) |
| `derrota.ogg` | `Evan Call - Before the Light Fades.m4a` | **Before the Light Fades** — *Frieren OST* (Evan Call) | `0.55s–6.85s` (`6.30s`, sem loop) | `+7.14 dB` / `-4.74 dBFS` / `-18.81 dB` | `derrota` (Frase dramática curta para tela de derrota) |
| `tema_melancolico.ogg` | `MUSASHI PROJECT - 哀と悲.m4a` | **哀と悲 (Sadness and Sorrow)** — *Naruto OST* (Toshio Masuda / MUSASHI PROJECT) | `0.95s–166.35s` (`165.40s`, loop contínuo) | `-0.19 dB` / `-2.79 dBFS` / `-19.00 dB` | `tema_melancolico`, `ninho_amanhecer`, `oakhaven_destruida` (Amanhecer pós-dragão no Ninho e Oakhaven destruída antes da reconstrução) |
| `tema_encerramento.ogg` | `Evan Call - Journey of a Lifetime ~ Frieren Main Theme.m4a` | **Journey of a Lifetime ~ Frieren Main Theme** — *Frieren OST* (Evan Call) | `0.85s–176.10s` (`175.25s`, loop contínuo) | `-5.38 dB` / `-3.92 dBFS` / `-18.80 dB` | `tema_encerramento`, `cutscene_final`, `creditos_demo` (Despedida pelo Portão Sul e créditos finais da Demo) |

### Garantias de Execução do `AudioManager`
- **Fade sequencial não bloqueante**: `tocar_musica(..., fade_ms)` executa atenuação (`SAINDO`), troca de stream e entrada (`ENTRANDO`) quadro a quadro em `AudioManager.update(dt)`, chamado em `Game.run()`, sem `time.sleep` e sem congelar quadros.
- **Continuidade entre aliases**: aliases que resolvem para o mesmo arquivo físico (`casa_halia` -> `estrada_floresta` -> `vila_oakhaven`; `cutscene_magia` entre `Flashback` e `TelaDespertarMemoria`; `cutscene_final` -> `creditos_demo`) não reiniciam o streaming da música.
- **Blindagem de contexto e retorno ao Menu**: tokens de geração e contexto impedem que `restaurar_musica_anterior` ao fechar combate sobrescreva uma cutscene posterior (`tema_melancolico`, `cutscene_magia`, `menu_tema`), e voltar ao `MENU` encerra ambiências e limpa a pilha de retorno.
- **Normalização de volume**: `definir_volume_*` distingue corretamente escalas percentuais inteiras (`int(1)` -> `0.01`, `100` -> `1.0`) e unitárias (`float(1.0)` -> `1.0`), além de suportar `definir_mute(bool)`.

---

## 2. Efeitos Sonoros (`assets/audio/sfx/`) — Integrados (105 arquivos)

Os efeitos sonoros curados dos pacotes oficiais estão normalizados (44,1 kHz estéreo `.ogg` Vorbis, normalização por janela RMS de 20 ms e proteção anti-clipping com `0` amostras clipadas) e organizados por contexto em `Oblivium/assets/audio/sfx/`, com **seleção aleatória não repetitiva de variações** (`_02`, `_03`, `_04`) no [`AudioManager`](src/core/audio_manager.py):

- **`sfx/ui/` (27 arquivos):** `ui_cursor` (`01..03`), `ui_hover`, `ui_slider`, `ui_confirmar` (`01..03`), `ui_aceitar`, `ui_voltar`, `ui_erro` (`01..03`), `ui_trancado`, `ui_dialogo`, `ui_notificacao`, `ui_clique_pedra`, `ui_clique_madeira`, `ui_clique_ferro`, `quest_nova`, `quest_concluida`, `level_up`, `livro_abrir`, `pagina_virar`, `pergaminho_abrir`, `toggle_on`, `toggle_off`.
- **`sfx/combate/` (48 arquivos):** `ataque_acerto` (`01..03`), `ataque_critico`, `ataque_erro` (`01..02`), `ataque_espada` (`01..02`), `defesa_escudo` (`01..03`), `magia_cast`, `magia_fogo` (`01..03`), `magia_gelo` (`01..03`), `magia_raio` (`01..03`), `magia_cura` (`01..04`), `explosao` (`01..03`), `rugido_monstro` (`01..03`), `slime` (`01..03`), `flecha` (`01..03`), `dano_halia` (`01..03`), `dano_inimigo` (`01..03`), `esquiva` (`01..03`), `fuga`, `concentrar`.
- **`sfx/itens/` (15 arquivos):** `item_coletar`, `item_pocao` (`01..04`), `garrafa_abrir`, `moeda` (`01..04`), `saco_moedas` (`01..03`), `equipar_armadura`, `desembainhar`.
- **`sfx/mundo/` (15 arquivos):** `porta_abrir` (`01..03`), `porta_fechar`, `bau_abrir` (`01..04`), `forja_bigorna`, além de passos individuais recortados sem sobreposição e sincronizados com cadência/terreno em **`passo_grama_01..03.ogg`** e **`passo_pedra_01..03.ogg`**.

*(As pastas originais dos pacotes e `sons.zip` em `Oblivium/assets/audio/` foram mantidas intactas conforme solicitado.)*

---

## 3. Sons de Ambiente (`assets/audio/ambience/`) — Integrados (11 arquivos)

Loops contínuos normalizados (~ `-23 dBFS RMS`, `0` amostras clipadas) acionados automaticamente por [`Game.sincronizar_ambiente_cenario`](src/core/game.py) (com prioridade para clima) e [`CenarioBase.obter_ambiente_cenario`](src/maps/cenario_base.py):
- `chuva.ogg`: chuva comum e tempestade em [`EfeitoChuva`](src/utils/clima.py).
- `vento_noite.ogg`: neve, nevasca e brisa noturna contínua.
- `vento_suave.ogg`: Oakhaven, amanhecer pós-dragão no Ninho e vila reconstruída.
- `floresta_dia.ogg`: Estradas (`ESTRADA`, `ESTRADA_2`) e Orla Norte em tempo limpo.
- `fogueira.ogg`: acampamento no Flashback, Oakhaven destruída em chamas e cabana à noite.
- `caverna_lava_01..03.ogg`: Ninho do Dragão antes da derrota de Ignis'Vahr.
- `cachoeira_01..03.ogg`: variações de água corrente disponíveis no manifesto.

### Mixagem Padrão e Controles em Configurações
- **Mixagem Padrão do Jogo (`Game.PADROES_AUDIO`)**: `Master 100%` • `Música 55%` • `Efeitos (SFX) 95%` • `Ambiente 70%`, equilibrando trilha (~`-23,6 dBFS`), camada climática (~`-26,1 dBFS`) e efeitos de combate/passos/UI em primeiro plano.
- **Prólogo (`CutsceneManager`)**: disparo da *Bola de Fogo* toca `magia_fogo` e a detonação das rochas na Estrada 2 toca `explosao`.
- **Controles Finos (`SettingsState` + `config_usuario.json`)**: barras arrastáveis/clicáveis contínuas, botões `[-]`/`[+]`, passo de `5%` (`1%` com `Shift`), roda do mouse, atalho/opção **Silenciar Tudo (`[M]`)**, **Restaurar Padrões (`[R]`)**, prévia ao vivo de ambiente no Menu e persistência em `saves/config_usuario.json`.

### Licenças e Atribuições de SFX / Ambiência
- **Fantasy UI SFX Free by heyheythere** — https://heyheythere.itch.io/fantasy-ui-sfx-free — **CC BY 4.0** (atribuído também na tela de Créditos do jogo).
- **FantasySFX Sampler** por **AHTu20** — https://ahtu20.itch.io — Uso comercial/pessoal permitido sem redistribuição isolada do pacote.
- **Ambient Loops Free Lite 3** por **yetiancai** — Uso permitido em jogos comerciais/não comerciais sem redistribuição isolada do pacote.

**Recomendação de escuta final:** antes da apresentação, validar em dispositivo de áudio real o equilíbrio entre passos (`passo_grama`/`passo_pedra`), ambiências, ataques elementais e trilha musical.
