<!--
DSI GitHub Command Center
Autor: Dayvid Santana
Criado em: 28/08/2026
Editado em: 28/08/2026
Objetivo: Documentar o comando fetch-stats e o schema do JSON publicado como API estática.
-->
# Mission Telemetry — API Estática

O comando `dsi-profile fetch-stats` agrega estrelas, pull requests, issues e uma contagem
aproximada de commits do usuário no GitHub, e grava o resultado em JSON. Como o `language`
report (veja [LANGUAGE_PROFICIENCY_API.md](LANGUAGE_PROFICIENCY_API.md)), o arquivo é
commitado no repositório e funciona como uma API somente-leitura via
`raw.githubusercontent.com`.

## Uso

```bash
export GITHUB_TOKEN="ghp_..."   # opcional, mas recomendado (ver limites abaixo)
dsi-profile fetch-stats --username SEU_USUARIO --output data/mission-stats.json
```

Sem `--username`, usa `profile.github_username` de `config/profile.yaml`. Use
`--include-forks` para somar estrelas de repositórios forkados na contagem.

## Schema do JSON

```json
{
  "github_username": "octocat",
  "generated_at": "2026-08-28T12:00:00Z",
  "repository_count": 3,
  "star_count": 10,
  "pull_request_count": 5,
  "issue_count": 2,
  "commit_count": 42
}
```

## Limitações importantes

- **`repository_count`** e **`star_count`** vêm da REST API (`/users/{user}/repos`) e são
  exatos, considerando apenas repositórios próprios não-forkados (por padrão).
- **`pull_request_count`** e **`issue_count`** vêm da Search API
  (`/search/issues?q=author:{user}+type:pr|issue`) e contam apenas PRs/issues abertos pelo
  usuário em repositórios públicos indexados.
- **`commit_count`** vem da Search API de commits (`/search/commits?q=author:{user}`) e é
  **aproximado**: só conta commits vinculados a um e-mail verificado do GitHub, e pode contar
  o mesmo commit várias vezes em repositórios muito forkados (o commit aparece indexado em
  cada fork). Trate como uma estimativa, não como uma métrica exata — é o mesmo tipo de
  limitação de qualquer gerador de "stats card" de perfil GitHub baseado na Search API.
- A Search API tem um limite de taxa próprio e mais restritivo que o da REST API (10
  requisições/minuto sem token, 30/minuto com token) — por isso `GITHUB_TOKEN` é recomendado.

## Console visual animado

`dsi-profile generate` também renderiza `assets/mission-telemetry.svg`: um cartão com os
cinco números acima, ícones com pulso sutil e efeito de brilho — embutido no README raiz logo
após "Personnel Record". Sem `data/mission-stats.json`, o console mostra "NO TELEMETRY
RECEIVED" em vez de falhar a geração.

## Atualização automática

O workflow [`update-profile.yml`](../.github/workflows/update-profile.yml) já roda
`fetch-stats` diariamente junto com `fetch-languages`, então `data/mission-stats.json` fica
sempre refletindo a atividade atual sem intervenção manual.
