# DSI GitHub Command Center
# Autor: Dayvid Santana
# Criado em: 28/08/2026
# Editado em: 28/08/2026
# Objetivo: Renderizar templates Jinja2 e gravar artefatos gerados de modo determinístico.
"""Infraestrutura de renderização para README e SVGs."""

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape


class TemplateRenderer:
    """Renderiza templates locais sem permitir dependências implícitas de rede."""

    def __init__(self, templates_directory: Path) -> None:
        self._environment = Environment(
            loader=FileSystemLoader(templates_directory),
            autoescape=select_autoescape(enabled_extensions=("html", "xml", "svg")),
            keep_trailing_newline=True,
            trim_blocks=True,
            lstrip_blocks=True,
            undefined=StrictUndefined,
        )

    def render(self, template_name: str, **context: Any) -> str:
        """Retorna o template preenchido com o contexto explicitamente informado."""
        return str(self._environment.get_template(template_name).render(**context))

    def write(self, destination: Path, content: str) -> Path:
        """Grava conteúdo UTF-8, criando somente os diretórios-pai necessários."""
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8", newline="\n")
        return destination
