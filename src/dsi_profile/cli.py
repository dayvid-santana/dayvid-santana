# DSI GitHub Command Center
# Autor: Dayvid Santana
# Criado em: 28/08/2026
# Editado em: 28/08/2026
# Objetivo: Disponibilizar a interface de linha de comando da ferramenta DSI.
"""Comandos Typer do DSI GitHub Command Center."""

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from dsi_profile.config import load_profile_config
from dsi_profile.exceptions import ProfileConfigurationError

app = typer.Typer(no_args_is_help=True, help="DSI GitHub Command Center.")
console = Console()
ConfigPath = Annotated[Path, typer.Option("--config", "-c", help="Caminho do profile.yaml.")]


@app.callback()
def main() -> None:
    """Agrupa os comandos operacionais do Command Center."""


@app.command()
def validate(config: ConfigPath = Path("config/profile.yaml")) -> None:
    """Valida o YAML e suas regras de consistência sem gerar arquivos."""
    try:
        profile_config = load_profile_config(config)
    except ProfileConfigurationError as error:
        console.print(f"[red]VALIDATION FAILED[/red] {error}")
        raise typer.Exit(code=1) from error
    console.print(
        "[green]CONFIGURATION VALID[/green] "
        f"operator={profile_config.profile.display_name} "
        f"projects={len(profile_config.projects)} technologies={len(profile_config.technologies)}"
    )
