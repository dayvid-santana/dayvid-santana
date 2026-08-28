# DSI GitHub Command Center
# Autor: Dayvid Santana
# Criado em: 28/08/2026
# Editado em: 28/08/2026
# Objetivo: Verificar o carregamento e as regras de validação da configuração YAML.
"""Testes de configuração."""

from pathlib import Path

import pytest

from dsi_profile.config import load_profile_config
from dsi_profile.exceptions import ProfileConfigurationError


def test_loads_example_profile() -> None:
    """O arquivo de exemplo completo deve ser aceito."""
    config = load_profile_config(Path("config/profile.yaml"))
    assert config.profile.callsign == "DS-01"
    assert config.theme.primary == "#74D9FF"


@pytest.mark.parametrize(
    ("field", "value", "expected"),
    [
        ("primary", "blue", "cor hexadecimal"),
        ("primary", "#12345", "cor hexadecimal"),
        ("primary", "#1234567", "cor hexadecimal"),
    ],
)
def test_rejects_invalid_theme_color(tmp_path: Path, field: str, value: str, expected: str) -> None:
    """Cores devem usar exclusivamente o formato hexadecimal completo."""
    source = Path("config/profile.yaml").read_text(encoding="utf-8")
    path = tmp_path / "profile.yaml"
    path.write_text(source.replace('primary: "#74D9FF"', f'{field}: "{value}"'), encoding="utf-8")
    with pytest.raises(ProfileConfigurationError, match=expected):
        load_profile_config(path)


def test_rejects_duplicate_project_id(tmp_path: Path) -> None:
    """Operações não podem reutilizar o mesmo identificador."""
    source = Path("config/profile.yaml").read_text(encoding="utf-8")
    duplicate_project = "\n".join(
        [
            '  - id: "operation-001"',
            '    codename: "COPY"',
            '    name: "Copy"',
            '    description: "Copy"',
            '    repository: ""',
            '    classification: "TEST"',
            '    status: "ACTIVE"',
            '    priority: "LOW"',
            '    technologies: ["Python"]',
        ]
    )
    duplicate = source.replace("social:", f"{duplicate_project}\nsocial:")
    path = tmp_path / "profile.yaml"
    path.write_text(duplicate, encoding="utf-8")
    with pytest.raises(ProfileConfigurationError, match="IDs duplicados"):
        load_profile_config(path)


def test_rejects_level_outside_range(tmp_path: Path) -> None:
    """Níveis de capacidade ficam no intervalo fechado de zero a cem."""
    source = Path("config/profile.yaml").read_text(encoding="utf-8")
    path = tmp_path / "profile.yaml"
    path.write_text(source.replace("level: 90", "level: 101"), encoding="utf-8")
    with pytest.raises(ProfileConfigurationError, match="less than or equal to 100"):
        load_profile_config(path)


def test_rejects_missing_file(tmp_path: Path) -> None:
    """A ausência de configuração deve produzir mensagem legível."""
    with pytest.raises(ProfileConfigurationError, match="não encontrado"):
        load_profile_config(tmp_path / "missing.yaml")
