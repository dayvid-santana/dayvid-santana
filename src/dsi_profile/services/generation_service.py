# DSI GitHub Command Center
# Autor: Dayvid Santana
# Criado em: 28/08/2026
# Editado em: 28/08/2026
# Objetivo: Orquestrar a geração determinística do README e dos primeiros assets visuais DSI.
"""Serviço de geração de perfil."""

from pathlib import Path

from dsi_profile.models import ProfileConfig
from dsi_profile.renderer import TemplateRenderer

SECTIONS = (
    ("01", "PERSONNEL RECORD", "PERSONNEL RECORD // IDENTITY VERIFIED"),
    ("02", "ACTIVE OPERATIONS", "ACTIVE OPERATIONS // MISSION CONTROL"),
    ("03", "SYSTEM CAPABILITIES", "SYSTEM CAPABILITIES // READINESS MATRIX"),
    ("04", "ACTIVITY TELEMETRY", "ACTIVITY TELEMETRY // DATA UPLINK"),
    ("05", "MISSION LOG", "MISSION LOG // OPERATOR DIRECTIVE"),
    ("06", "COMMUNICATION CHANNELS", "COMMUNICATION CHANNELS // SECURE ROUTING"),
)


class GenerationService:
    """Produz os artefatos de perfil a partir de uma configuração já validada."""

    def __init__(self, templates_directory: Path) -> None:
        self._renderer = TemplateRenderer(templates_directory)

    def generate(self, config: ProfileConfig, output_directory: Path) -> list[Path]:
        """Gera README, banner e divisores e retorna a lista ordenada de arquivos criados."""
        context = {
            "profile": config.profile,
            "mission": config.mission,
            "focus": config.focus,
            "projects": config.projects,
            "technologies": config.technologies,
            "social": config.social,
            "theme": config.theme,
            "enable_animations": config.generation.enable_animations,
        }
        artifacts = [
            self._renderer.write(
                output_directory / "assets" / "dsi-banner.svg",
                self._renderer.render("svg/banner.svg.j2", **context),
            )
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
