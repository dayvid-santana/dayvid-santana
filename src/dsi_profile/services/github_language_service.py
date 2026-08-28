# DSI GitHub Command Center
# Autor: Dayvid Santana
# Criado em: 28/08/2026
# Editado em: 28/08/2026
# Objetivo: Agregar bytes de código por linguagem em todos os repositórios de um usuário GitHub.
"""Coleta de proficiência em linguagens via API pública do GitHub."""

from __future__ import annotations

import os
from datetime import UTC, datetime
from types import TracebackType

import httpx

from dsi_profile.exceptions import GitHubApiError
from dsi_profile.models import LanguageReport, LanguageStat

GITHUB_API_BASE = "https://api.github.com"
PER_PAGE = 100

# Faixas de percentual (decrescentes) mapeadas para um código e um título de proficiência.
RANK_TIERS: tuple[tuple[float, str, str], ...] = (
    (30.0, "OMEGA", "PRIMARY SPECIALIZATION"),
    (15.0, "ALPHA", "CORE PROFICIENCY"),
    (5.0, "BRAVO", "OPERATIONAL PROFICIENCY"),
    (1.0, "CHARLIE", "FIELD FAMILIARITY"),
    (0.0, "DELTA", "RECONNAISSANCE EXPOSURE"),
)


def _rank_for(percentage: float) -> tuple[str, str]:
    """Retorna (código, título) do primeiro patamar cujo limite a porcentagem atinge."""
    for threshold, code, title in RANK_TIERS:
        if percentage >= threshold:
            return code, title
    return RANK_TIERS[-1][1], RANK_TIERS[-1][2]


class GitHubLanguageService:
    """Consulta a API pública do GitHub e agrega bytes de código por linguagem."""

    def __init__(
        self,
        token: str | None = None,
        timeout: float = 15.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        resolved_token = token if token is not None else os.environ.get("GITHUB_TOKEN")
        if resolved_token:
            headers["Authorization"] = f"Bearer {resolved_token}"
        self._client = httpx.Client(
            base_url=GITHUB_API_BASE, headers=headers, timeout=timeout, transport=transport
        )

    def close(self) -> None:
        """Libera a conexão HTTP subjacente."""
        self._client.close()

    def __enter__(self) -> GitHubLanguageService:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()

    def build_report(self, username: str, include_forks: bool = False) -> LanguageReport:
        """Agrega bytes por linguagem em todos os repositórios do usuário e monta o relatório."""
        repositories = self._list_repositories(username, include_forks=include_forks)
        totals: dict[str, int] = {}
        repo_counts: dict[str, int] = {}
        for repository in repositories:
            for language, byte_count in self._repository_languages(username, repository).items():
                totals[language] = totals.get(language, 0) + byte_count
                repo_counts[language] = repo_counts.get(language, 0) + 1

        total_bytes = sum(totals.values())
        stats = []
        for name, byte_count in totals.items():
            percentage = round((byte_count / total_bytes * 100) if total_bytes else 0.0, 2)
            rank_code, title = _rank_for(percentage)
            stats.append(
                LanguageStat(
                    name=name,
                    byte_count=byte_count,
                    percentage=percentage,
                    repository_count=repo_counts[name],
                    rank_code=rank_code,
                    title=title,
                )
            )
        stats.sort(key=lambda stat: stat.byte_count, reverse=True)

        top_language = stats[0] if stats else None
        operator_title = (
            f"{top_language.rank_code}-CLASS {top_language.name.upper()} OPERATOR"
            if top_language
            else "UNCLASSIFIED OPERATOR"
        )

        return LanguageReport(
            github_username=username,
            generated_at=datetime.now(UTC),
            repository_count=len(repositories),
            total_bytes=total_bytes,
            operator_title=operator_title,
            languages=stats,
        )

    def _list_repositories(self, username: str, include_forks: bool) -> list[str]:
        """Lista (paginando) os repositórios próprios do usuário, ignorando forks por padrão."""
        repositories: list[str] = []
        page = 1
        while True:
            response = self._client.get(
                f"/users/{username}/repos",
                params={"per_page": PER_PAGE, "page": page, "type": "owner"},
            )
            self._raise_for_status(response)
            payload = response.json()
            if not payload:
                break
            repositories.extend(
                repo["name"] for repo in payload if include_forks or not repo.get("fork")
            )
            if len(payload) < PER_PAGE:
                break
            page += 1
        return repositories

    def _repository_languages(self, username: str, repository: str) -> dict[str, int]:
        """Retorna o mapa de linguagem -> bytes de um repositório específico."""
        response = self._client.get(f"/repos/{username}/{repository}/languages")
        self._raise_for_status(response)
        result: dict[str, int] = response.json()
        return result

    @staticmethod
    def _raise_for_status(response: httpx.Response) -> None:
        """Converte erros da API do GitHub em exceções de domínio com mensagens acionáveis."""
        if response.status_code == 403 and "rate limit" in response.text.lower():
            raise GitHubApiError(
                "GitHub API rate limit excedido. Defina a variável de ambiente GITHUB_TOKEN "
                "com um token de acesso pessoal para aumentar o limite."
            )
        if response.status_code == 404:
            raise GitHubApiError(f"Usuário ou repositório GitHub não encontrado: {response.url}")
        if response.status_code >= 400:
            raise GitHubApiError(
                f"Falha ao consultar a API do GitHub ({response.status_code}): {response.url}"
            )
