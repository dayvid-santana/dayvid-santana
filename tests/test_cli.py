# DSI GitHub Command Center
# Autor: Dayvid Santana
# Criado em: 28/08/2026
# Editado em: 28/08/2026
# Objetivo: Verificar a interface de validação exposta pela CLI.
"""Testes de comandos Typer."""

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from typer.testing import CliRunner

from dsi_profile import cli
from dsi_profile.cli import app
from dsi_profile.exceptions import GitHubApiError
from dsi_profile.models import LanguageReport, LanguageStat

runner = CliRunner()


class _FakeLanguageService:
    """Substitui o serviço real de coleta de linguagens nos testes de CLI."""

    def __init__(self, *_: object, **__: object) -> None:
        pass

    def __enter__(self) -> "_FakeLanguageService":
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def build_report(self, username: str, include_forks: bool = False) -> LanguageReport:
        return LanguageReport(
            github_username=username,
            generated_at=datetime.now(UTC),
            repository_count=1,
            total_bytes=800,
            operator_title="OMEGA-CLASS PYTHON OPERATOR",
            languages=[
                LanguageStat(
                    name="Python",
                    byte_count=800,
                    percentage=100.0,
                    repository_count=1,
                    rank_code="OMEGA",
                    title="PRIMARY SPECIALIZATION",
                )
            ],
        )


class _FailingLanguageService(_FakeLanguageService):
    """Simula uma falha de API do GitHub."""

    def build_report(self, username: str, include_forks: bool = False) -> LanguageReport:
        raise GitHubApiError("Usuário ou repositório GitHub não encontrado")


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


def test_fetch_languages_writes_json_report(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """O comando deve gravar o relatório de proficiência como JSON no caminho solicitado."""
    monkeypatch.setattr(cli, "GitHubLanguageService", _FakeLanguageService)
    output = tmp_path / "languages.json"
    args = ["fetch-languages", "--username", "octocat", "--output", str(output)]
    result = runner.invoke(app, args)
    assert result.exit_code == 0
    assert "OMEGA-CLASS PYTHON OPERATOR" in result.stdout
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["github_username"] == "octocat"
    assert payload["operator_title"] == "OMEGA-CLASS PYTHON OPERATOR"
    assert payload["languages"][0]["name"] == "Python"


def test_fetch_languages_defaults_username_to_profile_config(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Sem --username, o comando deve usar profile.github_username do YAML informado."""
    monkeypatch.setattr(cli, "GitHubLanguageService", _FakeLanguageService)
    output = tmp_path / "languages.json"
    result = runner.invoke(
        app,
        ["fetch-languages", "--config", "config/profile.yaml", "--output", str(output)],
    )
    assert result.exit_code == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["github_username"] == "SEU_USUARIO"


def test_fetch_languages_reports_api_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Falhas na API do GitHub devem retornar código de saída 1 e mensagem clara."""
    monkeypatch.setattr(cli, "GitHubLanguageService", _FailingLanguageService)
    output = tmp_path / "languages.json"
    result = runner.invoke(app, ["fetch-languages", "--username", "ghost", "--output", str(output)])
    assert result.exit_code == 1
    assert "LANGUAGE FETCH FAILED" in result.stdout
    assert not output.exists()
