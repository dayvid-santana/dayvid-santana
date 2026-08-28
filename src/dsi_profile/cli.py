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
from dsi_profile.exceptions import GitHubApiError, ProfileConfigurationError
from dsi_profile.services.generation_service import GenerationService
from dsi_profile.services.github_language_service import GitHubLanguageService

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


@app.command()
def generate(
    config: ConfigPath = Path("config/profile.yaml"),
    output: Annotated[Path | None, typer.Option("--output", "-o")] = None,
    no_animations: Annotated[bool, typer.Option("--no-animations")] = False,
) -> None:
    """Gera o README de perfil, banner e divisores SVG em um diretório de saída."""
    try:
        profile_config = load_profile_config(config)
        if no_animations:
            profile_config.generation.enable_animations = False
        output_directory = output or Path(profile_config.generation.output_directory)
        artifacts = GenerationService(Path("templates")).generate(profile_config, output_directory)
    except ProfileConfigurationError as error:
        console.print(f"[red]GENERATION FAILED[/red] {error}")
        raise typer.Exit(code=1) from error
    console.print(f"[green]PROFILE GENERATED[/green] {len(artifacts)} files in {output_directory}")


@app.command("fetch-languages")
def fetch_languages(
    username: Annotated[
        str | None,
        typer.Option("--username", "-u", help="Usuário GitHub (padrão: profile.github_username)."),
    ] = None,
    config: ConfigPath = Path("config/profile.yaml"),
    output: Annotated[
        Path, typer.Option("--output", "-o", help="Caminho do JSON de saída.")
    ] = Path("data/languages.json"),
    include_forks: Annotated[
        bool, typer.Option("--include-forks", help="Inclui repositórios forkados na agregação.")
    ] = False,
) -> None:
    """Agrega bytes de código por linguagem em todos os repositórios e publica um JSON estático."""
    resolved_username = username
    if resolved_username is None:
        try:
            resolved_username = load_profile_config(config).profile.github_username
        except ProfileConfigurationError as error:
            console.print(f"[red]LANGUAGE FETCH FAILED[/red] {error}")
            raise typer.Exit(code=1) from error
    try:
        with GitHubLanguageService() as service:
            report = service.build_report(resolved_username, include_forks=include_forks)
    except GitHubApiError as error:
        console.print(f"[red]LANGUAGE FETCH FAILED[/red] {error}")
        raise typer.Exit(code=1) from error
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report.model_dump_json(indent=2) + "\n", encoding="utf-8", newline="\n")
    console.print(
        f"[green]LANGUAGE REPORT GENERATED[/green] {report.operator_title} · "
        f"{len(report.languages)} languages across {report.repository_count} repositories "
        f"-> {output}"
    )
