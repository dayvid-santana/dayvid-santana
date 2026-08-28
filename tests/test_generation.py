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
from dsi_profile.models import ProfileConfig
from dsi_profile.services.generation_service import GenerationService

VALID_LANGUAGE_REPORT = """{
  "github_username": "dayvid-santana",
  "generated_at": "2026-08-28T12:00:00Z",
  "repository_count": 3,
  "total_bytes": 1000,
  "operator_title": "OMEGA-CLASS PYTHON OPERATOR",
  "languages": [
    {
      "name": "Python",
      "byte_count": 800,
      "percentage": 80.0,
      "repository_count": 2,
      "rank_code": "OMEGA",
      "title": "PRIMARY SPECIALIZATION"
    },
    {
      "name": "HTML",
      "byte_count": 200,
      "percentage": 20.0,
      "repository_count": 1,
      "rank_code": "ALPHA",
      "title": "CORE PROFICIENCY"
    }
  ]
}"""

VALID_MISSION_STATS = """{
  "github_username": "dayvid-santana",
  "generated_at": "2026-08-28T12:00:00Z",
  "repository_count": 3,
  "star_count": 10,
  "pull_request_count": 5,
  "issue_count": 2,
  "commit_count": 42
}"""


def _generate(
    config: ProfileConfig,
    output_directory: Path,
    tmp_path: Path,
    language_report_path: Path | None = None,
    mission_stats_path: Path | None = None,
) -> list[Path]:
    """Gera com paths de telemetria isolados por padrão, para testes herméticos."""
    return GenerationService(Path("templates")).generate(
        config,
        output_directory,
        language_report_path=language_report_path or (tmp_path / "missing-languages.json"),
        mission_stats_path=mission_stats_path or (tmp_path / "missing-stats.json"),
    )


def test_generates_readme_and_valid_svg_assets(tmp_path: Path) -> None:
    """Os assets devem existir, ser XML válido e ser referenciados no README."""
    config = load_profile_config(Path("config/profile.yaml"))
    artifacts = _generate(config, tmp_path, tmp_path)
    readme = (tmp_path / "README.md").read_text(encoding="utf-8")
    assert len(artifacts) == 17
    assert "assets/dsi-banner.svg" in readme
    assert "assets/language-console.svg" in readme
    assert "assets/capabilities-console.svg" in readme
    assert "assets/mission-telemetry.svg" in readme
    assert "assets/tech-stack-console.svg" in readme
    assert "assets/system-readiness.svg" in readme
    assert "assets/deployment-map.svg" in readme
    assert "<!-- DSI:AUTO:START -->" in readme
    for asset in artifacts[:-1]:
        assert asset.suffix == ".svg"
        assert ElementTree.fromstring(asset.read_text(encoding="utf-8")).tag.endswith("svg")


def test_generation_is_deterministic(tmp_path: Path) -> None:
    """Dados iguais devem produzir um README idêntico em execuções sucessivas."""
    config = load_profile_config(Path("config/profile.yaml"))
    first = _generate(config, tmp_path, tmp_path)
    readme_first = (tmp_path / "README.md").read_text(encoding="utf-8")
    _generate(config, tmp_path, tmp_path)
    assert (tmp_path / "README.md").read_text(encoding="utf-8") == readme_first
    assert len(first) == 17


def test_readiness_and_deployment_map_are_valid_svg(tmp_path: Path) -> None:
    """Os novos painéis táticos devem ser XML válido e conter dados do operador."""
    config = load_profile_config(Path("config/profile.yaml"))
    _generate(config, tmp_path, tmp_path)
    readiness = (tmp_path / "assets" / "system-readiness.svg").read_text(encoding="utf-8")
    deployment = (tmp_path / "assets" / "deployment-map.svg").read_text(encoding="utf-8")
    assert ElementTree.fromstring(readiness).tag.endswith("svg")
    assert ElementTree.fromstring(deployment).tag.endswith("svg")
    assert "SYSTEM READINESS" in readiness
    assert config.profile.node in deployment


def test_readme_shows_placeholder_when_language_report_missing(tmp_path: Path) -> None:
    """Sem `data/languages.json`, o README orienta a rodar fetch-languages."""
    config = load_profile_config(Path("config/profile.yaml"))
    _generate(config, tmp_path, tmp_path)
    readme = (tmp_path / "README.md").read_text(encoding="utf-8")
    assert "Language proficiency data not generated yet" in readme
    console = (tmp_path / "assets" / "language-console.svg").read_text(encoding="utf-8")
    assert "NO TELEMETRY RECEIVED" in console
    assert ElementTree.fromstring(console).tag.endswith("svg")


def test_readme_shows_language_proficiency_when_report_present(tmp_path: Path) -> None:
    """Com um relatório válido, o console SVG exibe linguagens e o título do operador."""
    config = load_profile_config(Path("config/profile.yaml"))
    language_report_path = tmp_path / "languages.json"
    language_report_path.write_text(VALID_LANGUAGE_REPORT, encoding="utf-8")
    _generate(config, tmp_path, tmp_path, language_report_path=language_report_path)
    readme = (tmp_path / "README.md").read_text(encoding="utf-8")
    assert "Language proficiency data not generated yet" not in readme
    console = (tmp_path / "assets" / "language-console.svg").read_text(encoding="utf-8")
    assert ElementTree.fromstring(console).tag.endswith("svg")
    assert "OMEGA-CLASS PYTHON OPERATOR" in console
    assert "Python" in console and "HTML" in console
    assert "OMEGA" in console and "ALPHA" in console


def test_capabilities_console_renders_technologies_and_core_readout(tmp_path: Path) -> None:
    """O console de capacidades exibe cada tecnologia e destaca a de maior nível como core."""
    config = load_profile_config(Path("config/profile.yaml"))
    _generate(config, tmp_path, tmp_path)
    console = (tmp_path / "assets" / "capabilities-console.svg").read_text(encoding="utf-8")
    assert ElementTree.fromstring(console).tag.endswith("svg")
    for technology in config.technologies:
        assert technology.name in console
    top = max(config.technologies, key=lambda technology: technology.level)
    assert f"CORE: {top.name.upper()}" in console


def test_mission_telemetry_shows_placeholder_when_stats_missing(tmp_path: Path) -> None:
    """Sem `data/mission-stats.json`, o console orienta a rodar fetch-stats."""
    config = load_profile_config(Path("config/profile.yaml"))
    _generate(config, tmp_path, tmp_path)
    readme = (tmp_path / "README.md").read_text(encoding="utf-8")
    assert "Mission telemetry not generated yet" in readme
    console = (tmp_path / "assets" / "mission-telemetry.svg").read_text(encoding="utf-8")
    assert "NO TELEMETRY RECEIVED" in console
    assert ElementTree.fromstring(console).tag.endswith("svg")


def test_mission_telemetry_renders_metrics_when_stats_present(tmp_path: Path) -> None:
    """Com estatísticas válidas, o console exibe cada métrica agregada."""
    config = load_profile_config(Path("config/profile.yaml"))
    mission_stats_path = tmp_path / "mission-stats.json"
    mission_stats_path.write_text(VALID_MISSION_STATS, encoding="utf-8")
    _generate(config, tmp_path, tmp_path, mission_stats_path=mission_stats_path)
    readme = (tmp_path / "README.md").read_text(encoding="utf-8")
    assert "Mission telemetry not generated yet" not in readme
    console = (tmp_path / "assets" / "mission-telemetry.svg").read_text(encoding="utf-8")
    assert ElementTree.fromstring(console).tag.endswith("svg")
    assert ">42<" in console
    assert ">10<" in console
    assert "@dayvid-santana" in console


def test_tech_stack_console_renders_languages_and_focus_sectors(tmp_path: Path) -> None:
    """O console de tech stack combina barras de linguagem e o radar de categorias."""
    config = load_profile_config(Path("config/profile.yaml"))
    language_report_path = tmp_path / "languages.json"
    language_report_path.write_text(VALID_LANGUAGE_REPORT, encoding="utf-8")
    _generate(config, tmp_path, tmp_path, language_report_path=language_report_path)
    console = (tmp_path / "assets" / "tech-stack-console.svg").read_text(encoding="utf-8")
    assert ElementTree.fromstring(console).tag.endswith("svg")
    assert "Python" in console and "HTML" in console
    categories = {technology.category for technology in config.technologies}
    for category in categories:
        assert category in console


def test_generate_command_writes_requested_output(tmp_path: Path) -> None:
    """A CLI expõe o primeiro conjunto visual através de generate."""
    result = CliRunner().invoke(app, ["generate", "--output", str(tmp_path)])
    assert result.exit_code == 0
    assert (tmp_path / "assets" / "dsi-banner.svg").is_file()


def test_no_animations_generates_static_svg(tmp_path: Path) -> None:
    """A flag da CLI remove animações sem remover o conteúdo visual estático."""
    result = CliRunner().invoke(app, ["generate", "--output", str(tmp_path), "--no-animations"])
    banner = (tmp_path / "assets" / "dsi-banner.svg").read_text(encoding="utf-8")
    assert result.exit_code == 0
    assert "<animate" not in banner
    assert "SYSTEM ONLINE" in banner
