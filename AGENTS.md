<!--
DSI GitHub Command Center
Autor: Dayvid Santana
Criado em: 28/08/2026
Editado em: 28/08/2026
Objetivo: Orientar agentes de IA sobre convenções, segurança e fluxo de desenvolvimento.
-->
# AGENTS.md

## Visão

DSI GitHub Command Center gera README e assets SVG para perfis GitHub com a identidade original **DSI — Dayvid Systems Initiative**. A referência sci-fi é conceitual; nunca use elementos protegidos de Halo ou de outras franquias.

## Comandos essenciais

```powershell
pip install -e ".[dev]"
ruff check .
ruff format --check .
mypy src
pytest
pytest --cov=src/dsi_profile
dsi-profile validate
```

## Arquitetura e convenções

- Código-fonte em `src/dsi_profile`; a CLI apenas coordena serviços.
- Configuração variável permanece em `config/profile.yaml` e é validada por Pydantic.
- Templates não acessam rede nem escrevem arquivos.
- Use `pathlib`, UTF-8, tipagem estrita e funções pequenas.
- Todo Python novo ou alterado começa com o cabeçalho DSI exigido, preservando a data de criação e atualizando a data de edição.
- Atualize `docs/IMPLEMENTATION_PLAN.md`, `CHANGELOG.md`, `README.md` e testes ao concluir uma fase.
- `dist/` e `.cache/` são gerados; não edite-os manualmente nem remova arquivos desconhecidos.

## Segurança

- Nunca registre, serialize ou inclua `GITHUB_TOKEN` em exceções, testes ou documentação de saída.
- Não execute shell com dados de YAML; normalize caminhos e bloqueie traversal em operações de escrita/publicação.
- Escape conteúdo dinâmico em XML e HTML; valide URLs antes de renderizar.

## Git

- Preserve alterações existentes do usuário.
- Use Conventional Commits, mas não faça commit ou push sem solicitação explícita.
- Execute Ruff, mypy e os testes relevantes antes de propor uma alteração concluída.
