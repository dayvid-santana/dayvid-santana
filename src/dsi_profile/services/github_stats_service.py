# DSI GitHub Command Center
# Autor: Dayvid Santana
# Criado em: 28/08/2026
# Editado em: 28/08/2026
# Objetivo: Agregar métricas públicas de atividade (commits, stars, PRs, issues, repos) do GitHub.
"""Coleta de métricas agregadas de atividade via API pública do GitHub."""

from __future__ import annotations

import os
from datetime import UTC, datetime
from types import TracebackType

import httpx

from dsi_profile.exceptions import GitHubApiError
from dsi_profile.models import MissionStats

GITHUB_API_BASE = "https://api.github.com"
PER_PAGE = 100


class GitHubStatsService:
    """Consulta a API pública do GitHub e agrega estrelas, PRs, issues e commits do usuário.

    A contagem de commits usa a Search API (`/search/commits`), que indexa apenas commits
    vinculados a um e-mail verificado do GitHub e pode ficar incompleta ou, em repositórios
    muito forkados, contar o mesmo commit várias vezes — trate-a como uma aproximação.
    """

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

    def __enter__(self) -> GitHubStatsService:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()

    def build_report(self, username: str, include_forks: bool = False) -> MissionStats:
        """Agrega repositórios, estrelas, PRs, issues e commits do usuário em um único relatório."""
        repository_count, star_count = self._repository_totals(username, include_forks)
        pull_request_count = self._search_total(f"author:{username} type:pr")
        issue_count = self._search_total(f"author:{username} type:issue")
        commit_count = self._search_total(f"author:{username}", endpoint="/search/commits")
        return MissionStats(
            github_username=username,
            generated_at=datetime.now(UTC),
            repository_count=repository_count,
            star_count=star_count,
            pull_request_count=pull_request_count,
            issue_count=issue_count,
            commit_count=commit_count,
        )

    def _repository_totals(self, username: str, include_forks: bool) -> tuple[int, int]:
        """Retorna (quantidade de repositórios, soma de estrelas) entre os repositórios próprios."""
        repository_count = 0
        star_count = 0
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
            for repo in payload:
                if repo.get("fork") and not include_forks:
                    continue
                repository_count += 1
                star_count += repo.get("stargazers_count", 0)
            if len(payload) < PER_PAGE:
                break
            page += 1
        return repository_count, star_count

    def _search_total(self, query: str, endpoint: str = "/search/issues") -> int:
        """Retorna `total_count` de uma busca da Search API do GitHub."""
        response = self._client.get(endpoint, params={"q": query, "per_page": 1})
        self._raise_for_status(response)
        total_count: int = response.json().get("total_count", 0)
        return total_count

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
