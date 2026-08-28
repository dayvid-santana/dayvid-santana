<!--
DSI GitHub Command Center
Autor: Dayvid Santana
Criado em: 28/08/2026
Editado em: 28/08/2026
Objetivo: Apresentar o projeto, instalação e fluxo de uso inicial.
-->
# DSI GitHub Command Center

Gerador Python para criar um README de perfil GitHub e assets visuais originais da **DSI — Dayvid Systems Initiative**.

## Requisitos

- Python 3.12 ou superior
- PowerShell no Windows 11 ou WSL 2

## Instalação

Windows 11 (PowerShell):

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

WSL 2:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

## Uso inicial

Edite `config/profile.yaml` e valide a configuração:

```powershell
dsi-profile validate
```

Os próximos comandos de geração, preview e publicação serão entregues nas fases seguintes. A integração GitHub será opcional e lerá `GITHUB_TOKEN` somente do ambiente ou de `.env` local, que não é versionado.

## Desenvolvimento

```powershell
ruff check .
ruff format --check .
mypy src
pytest
pytest --cov=src/dsi_profile
```

Veja [o plano de implementação](docs/IMPLEMENTATION_PLAN.md) e as regras para contribuidores automatizados em [AGENTS.md](AGENTS.md).

## Licença

MIT. Veja [LICENSE](LICENSE).
