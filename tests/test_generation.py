# DSI GitHub Command Center
# Autor: Dayvid Santana
# Criado em: 28/08/2026
# Editado em: 28/08/2026
# Objetivo: Validar a geração determinística do README e dos assets SVG DSI.
"""Testes do serviço de geração visual."""

from pathlib import Path
from xml.etree import ElementTree

from typer.testing import CliRunner

from dsi_profile.cli import app
from dsi_profile.config import load_profile_config
from dsi_profile.services.generation_service import GenerationService


def test_generates_readme_and_valid_svg_assets(tmp_path: Path) -> None:
    """Os assets devem existir, ser XML válido e ser referenciados no README."""
    config = load_profile_config(Path("config/profile.yaml"))
    artifacts = GenerationService(Path("templates")).generate(config, tmp_path)
    readme = (tmp_path / "README.md").read_text(encoding="utf-8")
    assert len(artifacts) == 8
    assert "assets/dsi-banner.svg" in readme
    assert "<!-- DSI:AUTO:START -->" in readme
    for asset in artifacts[:-1]:
        assert asset.suffix == ".svg"
        assert ElementTree.fromstring(asset.read_text(encoding="utf-8")).tag.endswith("svg")


def test_generation_is_deterministic(tmp_path: Path) -> None:
    """Dados iguais devem produzir um README idêntico em execuções sucessivas."""
    config = load_profile_config(Path("config/profile.yaml"))
    service = GenerationService(Path("templates"))
    service.generate(config, tmp_path)
    first = (tmp_path / "README.md").read_text(encoding="utf-8")
    service.generate(config, tmp_path)
    assert (tmp_path / "README.md").read_text(encoding="utf-8") == first


def test_generate_command_writes_requested_output(tmp_path: Path) -> None:
    """A CLI expõe o primeiro conjunto visual através de generate."""
    result = CliRunner().invoke(app, ["generate", "--output", str(tmp_path)])
    assert result.exit_code == 0
    assert (tmp_path / "assets" / "dsi-banner.svg").is_file()
