# DSI GitHub Command Center
# Autor: Dayvid Santana
# Criado em: 28/08/2026
# Editado em: 28/08/2026
# Objetivo: Verificar a interface de validação exposta pela CLI.
"""Testes de comandos Typer."""

from pathlib import Path

from typer.testing import CliRunner

from dsi_profile.cli import app

runner = CliRunner()


def test_validate_command_accepts_example_configuration() -> None:
    """A CLI retorna sucesso para a configuração fornecida."""
    result = runner.invoke(app, ["validate", "--config", "config/profile.yaml"])
    assert result.exit_code == 0
    assert "CONFIGURATION VALID" in result.stdout


def test_validate_command_reports_invalid_file(tmp_path: Path) -> None:
    """A CLI retorna código de erro sem traceback para YAML inválido."""
    path = tmp_path / "invalid.yaml"
    path.write_text("profile: [", encoding="utf-8")
    result = runner.invoke(app, ["validate", "--config", str(path)])
    assert result.exit_code == 1
    assert "VALIDATION FAILED" in result.stdout


def test_help_is_available() -> None:
    """O comando raiz deve documentar os comandos disponíveis."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "validate" in result.stdout
