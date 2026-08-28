<!--
DSI GitHub Command Center
Autor: Dayvid Santana
Criado em: 28/08/2026
Editado em: 28/08/2026
Objetivo: Documentar o ciclo de desenvolvimento e validação local.
-->
# Desenvolvimento

Use Python 3.12+, crie um ambiente virtual e instale `pip install -e ".[dev]"`. Antes de entregar alterações, execute `ruff check .`, `ruff format --check .`, `mypy src` e `pytest`.

Não versione `.env`, `.cache/` nem artefatos de `dist/` além de `.gitkeep`.
