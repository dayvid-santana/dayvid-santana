# DSI GitHub Command Center
# Autor: Dayvid Santana
# Criado em: 28/08/2026
# Editado em: 28/08/2026
# Objetivo: Orquestrar a geração determinística do README e dos primeiros assets visuais DSI.
"""Serviço de geração de perfil."""

from pathlib import Path

from pydantic import ValidationError

from dsi_profile.language_colors import color_for_language
from dsi_profile.models import LanguageReport, MissionStats, ProfileConfig
from dsi_profile.renderer import TemplateRenderer
from dsi_profile.services.sector_chart import SectorChart, build_sector_chart

SECTIONS = (
    ("01", "PERSONNEL RECORD", "PERSONNEL RECORD // IDENTITY VERIFIED"),
    ("02", "ACTIVE OPERATIONS", "ACTIVE OPERATIONS // MISSION CONTROL"),
    ("03", "SYSTEM CAPABILITIES", "SYSTEM CAPABILITIES // READINESS MATRIX"),
    ("04", "ACTIVITY TELEMETRY", "ACTIVITY TELEMETRY // DATA UPLINK"),
    ("05", "MISSION LOG", "MISSION LOG // OPERATOR DIRECTIVE"),
    ("06", "COMMUNICATION CHANNELS", "COMMUNICATION CHANNELS // SECURE ROUTING"),
    ("07", "LANGUAGE PROFICIENCY", "LANGUAGE PROFICIENCY // SOURCE CODE ANALYSIS"),
    ("08", "MISSION TELEMETRY", "MISSION TELEMETRY // GITHUB ACTIVITY SNAPSHOT"),
    ("09", "TECH STACK", "TECH STACK // LANGUAGE AND FOCUS BREAKDOWN"),
)

DEFAULT_LANGUAGE_REPORT_PATH = Path("data/languages.json")
DEFAULT_MISSION_STATS_PATH = Path("data/mission-stats.json")


class GenerationService:
    """Produz os artefatos de perfil a partir de uma configuração já validada."""

    def __init__(self, templates_directory: Path) -> None:
        self._renderer = TemplateRenderer(templates_directory)

    def generate(
        self,
        config: ProfileConfig,
        output_directory: Path,
        language_report_path: Path = DEFAULT_LANGUAGE_REPORT_PATH,
        mission_stats_path: Path = DEFAULT_MISSION_STATS_PATH,
    ) -> list[Path]:
        """Gera README, banner e divisores e retorna a lista ordenada de arquivos criados."""
        languages_report = self._load_language_report(language_report_path)
        context = {
            "profile": config.profile,
            "mission": config.mission,
            "focus": config.focus,
            "projects": config.projects,
            "technologies": config.technologies,
            "social": config.social,
            "theme": config.theme,
            "enable_animations": config.generation.enable_animations,
            "languages_report": languages_report,
            "mission_stats": self._load_mission_stats(mission_stats_path),
            "language_color": color_for_language,
            "sector_chart": self._build_focus_sector_chart(config),
        }
        artifacts = [
            self._renderer.write(
                output_directory / "assets" / "dsi-banner.svg",
                self._renderer.render("svg/banner.svg.j2", **context),
            ),
            self._renderer.write(
                output_directory / "assets" / "language-console.svg",
                self._renderer.render("svg/language-console.svg.j2", **context),
            ),
            self._renderer.write(
                output_directory / "assets" / "capabilities-console.svg",
                self._renderer.render("svg/capabilities-console.svg.j2", **context),
            ),
            self._renderer.write(
                output_directory / "assets" / "mission-telemetry.svg",
                self._renderer.render("svg/mission-telemetry.svg.j2", **context),
            ),
            self._renderer.write(
                output_directory / "assets" / "tech-stack-console.svg",
                self._renderer.render("svg/tech-stack-console.svg.j2", **context),
            ),
        ]
        for index, title, code in SECTIONS:
            slug = title.lower().replace(" ", "-")
            artifacts.append(
                self._renderer.write(
                    output_directory / "assets" / "sections" / f"{index}-{slug}.svg",
                    self._renderer.render(
                        "svg/separator.svg.j2",
                        index=index,
                        title=title,
                        code=code,
                        theme=config.theme,
                        enable_animations=config.generation.enable_animations,
                    ),
                )
            )
        artifacts.append(
            self._renderer.write(
                output_directory / "README.md",
                self._renderer.render("README.md.j2", **context),
            )
        )
        return artifacts

    @staticmethod
    def _load_language_report(path: Path) -> LanguageReport | None:
        """Carrega o relatório de linguagens gerado por `fetch-languages`, se existir."""
        if not path.is_file():
            return None
        try:
            return LanguageReport.model_validate_json(path.read_text(encoding="utf-8"))
        except ValidationError:
            return None

    @staticmethod
    def _load_mission_stats(path: Path) -> MissionStats | None:
        """Carrega as métricas agregadas geradas por `fetch-stats`, se existirem."""
        if not path.is_file():
            return None
        try:
            return MissionStats.model_validate_json(path.read_text(encoding="utf-8"))
        except ValidationError:
            return None

    @staticmethod
    def _build_focus_sector_chart(config: ProfileConfig) -> SectorChart | None:
        """Agrupa as tecnologias declaradas por categoria e monta o radar "Focus Sectors".

        Centro/raio combinam com a coluna direita do template tech-stack-console.svg.j2.
        """
        counts: dict[str, int] = {}
        for technology in config.technologies:
            counts[technology.category] = counts.get(technology.category, 0) + 1
        ordered_counts = sorted(counts.items(), key=lambda item: item[1], reverse=True)
        theme = config.theme
        colors = [theme.primary, theme.warning, theme.success, theme.secondary]
        return build_sector_chart(
            ordered_counts, colors, center_x=940.0, center_y=260.0, radius=85.0
        )
