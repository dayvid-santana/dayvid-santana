# DSI GitHub Command Center
# Autor: Dayvid Santana
# Criado em: 28/08/2026
# Editado em: 28/08/2026
# Objetivo: Mapear linguagens para as cores de marca usadas pelo GitHub (linguist).
"""Tabela estática de cores de linguagem, para colorir barras de proficiência."""

GITHUB_LANGUAGE_COLORS: dict[str, str] = {
    "Python": "#3572A5",
    "TypeScript": "#3178C6",
    "JavaScript": "#F1E05A",
    "HTML": "#E34C26",
    "CSS": "#563D7C",
    "SCSS": "#C6538C",
    "Java": "#B07219",
    "Kotlin": "#A97BFF",
    "C": "#555555",
    "C++": "#F34B7D",
    "C#": "#178600",
    "Go": "#00ADD8",
    "Rust": "#DEA584",
    "Ruby": "#701516",
    "PHP": "#4F5D95",
    "Swift": "#F05138",
    "Shell": "#89E051",
    "PowerShell": "#012456",
    "Dockerfile": "#384D54",
    "Jinja": "#A52A22",
    "YAML": "#CB171E",
    "JSON": "#292929",
    "Markdown": "#083FA1",
    "Vue": "#41B883",
    "Svelte": "#FF3E00",
    "Astro": "#FF5A03",
    "Objective-C": "#438EFF",
    "Scala": "#C22D40",
    "Elixir": "#6E4A7E",
    "Haskell": "#5E5086",
    "Lua": "#000080",
    "Perl": "#0298C3",
    "R": "#198CE7",
    "Dart": "#00B4AB",
    "Assembly": "#6E4C13",
    "Makefile": "#427819",
    "TeX": "#3D6117",
    "Vim Script": "#199F4B",
    "SQL": "#E38C00",
}

DEFAULT_LANGUAGE_COLOR = "#74D9FF"


def color_for_language(name: str) -> str:
    """Retorna a cor de marca conhecida da linguagem, ou um ciano padrão como fallback."""
    return GITHUB_LANGUAGE_COLORS.get(name, DEFAULT_LANGUAGE_COLOR)
