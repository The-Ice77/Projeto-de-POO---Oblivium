# Módulos Legados (`src.legacy`)

Este pacote preserva arquivos históricos substituídos ao longo do desenvolvimento do projeto **Oblivium**, conforme a política de não-destruição (`REGRAS_DO_PROJETO.md` §3) e a Decisão D2 do plano de refatoração.

> **Atenção:** nenhum código em `src/` deve importar módulos deste pacote durante o gameplay normal. Use os substitutos atuais indicados abaixo.

| Arquivo em `src/legacy/` | Origem | Substituto Atual |
| :--- | :--- | :--- |
| `cutscene_timeskip.py` | `src/mechanics/cutscene_timeskip.py` | `src/mechanics/cutscene_reconstrucao_visual.py` (`CutsceneReconstrucaoVisual`) |
| `magia.py` | `src/mechanics/magia.py` | `src/mechanics/skills.py` (`MagiaOfensiva`) e `src/mechanics/grimorio.py` (`GrimorioHalia`) |
| `dialogos.py` | `src/data/dialogos.py` | `src/mechanics/dialogue_manager.py` (`DialogueManager`) + `src/data/dialogos/*.json` |
| `colors_hex_antigo.py` | `src/utils/colors#.py` | `src/utils/colors.py` (tuplas RGB) |
