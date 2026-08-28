# DSI GitHub Command Center
# Autor: Dayvid Santana
# Criado em: 28/08/2026
# Editado em: 28/08/2026
# Objetivo: Modelar e validar a configuração declarativa de um perfil DSI.
"""Modelos Pydantic usados pela configuração de perfil."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator, model_validator

HEX_COLOR_PATTERN = re.compile(r"^#[0-9A-Fa-f]{6}$")
SAFE_OUTPUT_DIRECTORY = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]*$")


class Profile(BaseModel):
    """Identificação pública do operador e da divisão DSI."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    github_username: Annotated[str, Field(min_length=1, max_length=39)]
    display_name: Annotated[str, Field(min_length=1, max_length=100)]
    organization_name: Annotated[str, Field(min_length=1, max_length=120)]
    organization_short_name: Annotated[str, Field(min_length=2, max_length=12)]
    organization_subtitle: Annotated[str, Field(min_length=1, max_length=120)]
    role: Annotated[str, Field(min_length=1, max_length=100)]
    callsign: Annotated[str, Field(min_length=1, max_length=30)]
    node: Annotated[str, Field(min_length=1, max_length=30)]
    division: Annotated[str, Field(min_length=1, max_length=100)]
    status: Annotated[str, Field(min_length=1, max_length=40)]
    clearance: Annotated[str, Field(min_length=1, max_length=40)]
    location: Annotated[str, Field(min_length=1, max_length=100)]
    locale: Annotated[str, Field(min_length=2, max_length=20)]


class Mission(BaseModel):
    """Missão profissional exibida no perfil."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    title: Annotated[str, Field(min_length=1, max_length=160)]
    description: Annotated[str, Field(min_length=1, max_length=1_000)]


class Technology(BaseModel):
    """Capacidade técnica e respectivo nível declarado."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    name: Annotated[str, Field(min_length=1, max_length=60)]
    category: Annotated[str, Field(min_length=1, max_length=80)]
    status: Annotated[str, Field(min_length=1, max_length=40)]
    level: Annotated[int, Field(ge=0, le=100)]


class Project(BaseModel):
    """Operação selecionada manualmente para destaque no perfil."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    id: Annotated[str, Field(min_length=1, max_length=80, pattern=r"^[a-z0-9][a-z0-9-]*$")]
    codename: Annotated[str, Field(min_length=1, max_length=60)]
    name: Annotated[str, Field(min_length=1, max_length=100)]
    description: Annotated[str, Field(min_length=1, max_length=500)]
    repository: HttpUrl | None = None
    classification: Annotated[str, Field(min_length=1, max_length=60)]
    status: Annotated[str, Field(min_length=1, max_length=60)]
    priority: Annotated[str, Field(min_length=1, max_length=30)]
    technologies: Annotated[list[str], Field(min_length=1, max_length=12)]

    @field_validator("repository", mode="before")
    @classmethod
    def empty_repository_is_none(cls, value: object) -> object:
        """Converte URL vazia do YAML em valor ausente explícito."""
        return None if value == "" else value


class Social(BaseModel):
    """Canais de comunicação opcionais e validados."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    github: HttpUrl | None = None
    linkedin: HttpUrl | None = None
    email: str | None = None

    @field_validator("github", "linkedin", "email", mode="before")
    @classmethod
    def empty_social_value_is_none(cls, value: object) -> object:
        """Converte strings vazias em canais não configurados."""
        return None if value == "" else value


class Theme(BaseModel):
    """Paleta de cores da identidade visual DSI."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    name: Annotated[str, Field(min_length=1, max_length=60)]
    background: str
    background_secondary: str
    primary: str
    secondary: str
    text: str
    muted: str
    warning: str
    success: str
    grid: str
    border: str

    @field_validator(
        "background",
        "background_secondary",
        "primary",
        "secondary",
        "text",
        "muted",
        "warning",
        "success",
        "grid",
        "border",
    )
    @classmethod
    def validate_hex_color(cls, value: str) -> str:
        """Aceita somente cores hexadecimais completas e previsíveis."""
        if not HEX_COLOR_PATTERN.fullmatch(value):
            raise ValueError("deve ser uma cor hexadecimal no formato #RRGGBB")
        return value.upper()


class Generation(BaseModel):
    """Opções de produção de arquivos derivados."""

    model_config = ConfigDict(extra="forbid")
    enable_animations: bool = True
    generate_dark_variant: bool = True
    generate_light_variant: bool = True
    include_github_statistics: bool = True
    include_repository_statistics: bool = True
    include_activity_section: bool = True
    output_directory: str = "dist"

    @field_validator("output_directory")
    @classmethod
    def validate_output_directory(cls, value: str) -> str:
        """Bloqueia caminhos absolutos e traversal na saída configurada."""
        candidate = Path(value)
        if value != "." and (
            candidate.is_absolute()
            or ".." in candidate.parts
            or not SAFE_OUTPUT_DIRECTORY.fullmatch(value)
        ):
            raise ValueError("deve ser um caminho relativo seguro sem '..'")
        return value


class ProfileConfig(BaseModel):
    """Agregado validado de toda a configuração de um perfil."""

    model_config = ConfigDict(extra="forbid")
    profile: Profile
    mission: Mission
    focus: Annotated[list[str], Field(min_length=1, max_length=20)]
    technologies: Annotated[list[Technology], Field(min_length=1, max_length=50)]
    projects: Annotated[list[Project], Field(max_length=30)]
    social: Social
    theme: Theme
    generation: Generation

    @model_validator(mode="after")
    def validate_references_and_project_ids(self) -> ProfileConfig:
        """Garante IDs únicos e referências de tecnologia consistentes."""
        project_ids = [project.id for project in self.projects]
        if len(project_ids) != len(set(project_ids)):
            raise ValueError("projects contém IDs duplicados")
        known_technologies = {technology.name.casefold() for technology in self.technologies}
        unknown = {
            name
            for project in self.projects
            for name in project.technologies
            if name.casefold() not in known_technologies
        }
        if unknown:
            raise ValueError(
                f"projects referencia tecnologias não declaradas: {', '.join(sorted(unknown))}"
            )
        return self


class LanguageStat(BaseModel):
    """Proficiência agregada em uma linguagem, calculada a partir de todos os repositórios."""

    model_config = ConfigDict(extra="forbid")
    name: Annotated[str, Field(min_length=1, max_length=60)]
    byte_count: Annotated[int, Field(ge=0)]
    percentage: Annotated[float, Field(ge=0, le=100)]
    repository_count: Annotated[int, Field(ge=0)]
    rank_code: Annotated[str, Field(min_length=1, max_length=20)]
    title: Annotated[str, Field(min_length=1, max_length=80)]


class LanguageReport(BaseModel):
    """Relatório de proficiência em linguagens, publicado como API JSON estática."""

    model_config = ConfigDict(extra="forbid")
    github_username: Annotated[str, Field(min_length=1, max_length=39)]
    generated_at: datetime
    repository_count: Annotated[int, Field(ge=0)]
    total_bytes: Annotated[int, Field(ge=0)]
    operator_title: Annotated[str, Field(min_length=1, max_length=80)]
    languages: list[LanguageStat]


class MissionStats(BaseModel):
    """Métricas agregadas de atividade pública no GitHub, publicadas como API JSON estática."""

    model_config = ConfigDict(extra="forbid")
    github_username: Annotated[str, Field(min_length=1, max_length=39)]
    generated_at: datetime
    repository_count: Annotated[int, Field(ge=0)]
    star_count: Annotated[int, Field(ge=0)]
    pull_request_count: Annotated[int, Field(ge=0)]
    issue_count: Annotated[int, Field(ge=0)]
    commit_count: Annotated[int, Field(ge=0)]
