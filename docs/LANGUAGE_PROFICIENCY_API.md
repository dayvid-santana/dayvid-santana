<!--
DSI GitHub Command Center
Autor: Dayvid Santana
Criado em: 28/08/2026
Editado em: 28/08/2026
Objetivo: Documentar o comando fetch-languages e o schema do JSON publicado como API estática.
-->
# Proficiência em Linguagens — API Estática

O comando `dsi-profile fetch-languages` consulta a API pública do GitHub, agrega os bytes de
código de todos os repositórios do usuário (excluindo forks por padrão) e grava um relatório
em JSON. Como o arquivo é commitado no repositório, ele funciona como uma API somente-leitura:
qualquer projeto pode consumi-lo via `raw.githubusercontent.com`, sem servidor dedicado.

## Uso

```bash
# Autenticação opcional, mas recomendada para evitar rate limit (60 req/h sem token):
export GITHUB_TOKEN="ghp_..."

dsi-profile fetch-languages --username SEU_USUARIO --output data/languages.json
```

Sem `--username`, o comando usa `profile.github_username` de `config/profile.yaml`.
Use `--include-forks` para contabilizar repositórios forkados na agregação.

## Consumindo em outro projeto

```bash
curl -s https://raw.githubusercontent.com/<usuario>/<repositorio>/main/data/languages.json
```

## Schema do JSON

```json
{
  "github_username": "octocat",
  "generated_at": "2026-08-28T12:00:00Z",
  "repository_count": 42,
  "total_bytes": 1000000,
  "operator_title": "OMEGA-CLASS PYTHON OPERATOR",
  "languages": [
    {
      "name": "Python",
      "byte_count": 800000,
      "percentage": 80.0,
      "repository_count": 30,
      "rank_code": "OMEGA",
      "title": "PRIMARY SPECIALIZATION"
    }
  ]
}
```

`languages` é ordenado do maior para o menor `byte_count`. Cada linguagem recebe um título de
proficiência de acordo com o percentual do total de bytes escritos nela:

| Percentual   | `rank_code` | `title`                     |
| ------------ | ----------- | ---------------------------- |
| ≥ 30%        | `OMEGA`     | PRIMARY SPECIALIZATION       |
| 15% – 30%    | `ALPHA`     | CORE PROFICIENCY             |
| 5% – 15%     | `BRAVO`     | OPERATIONAL PROFICIENCY      |
| 1% – 5%      | `CHARLIE`   | FIELD FAMILIARITY            |
| < 1%         | `DELTA`     | RECONNAISSANCE EXPOSURE      |

`operator_title` resume a linguagem dominante em um único título, ex.:
`OMEGA-CLASS PYTHON OPERATOR`.

## Console visual animado

`dsi-profile generate` também renderiza `assets/language-console.svg`, um painel DSI com
barras de proficiência animadas (uma por linguagem, coloridas pelo `rank_code`), varredura
de fundo e indicador de status — embutido no README raiz logo após a seção "System
Capabilities". Sem `data/languages.json`, o console mostra "NO TELEMETRY RECEIVED" em vez de
falhar a geração.

## Atualização automática

O workflow [`update-profile.yml`](../.github/workflows/update-profile.yml) roda todo dia às
06:00 UTC (e sob demanda via `workflow_dispatch`): executa `fetch-languages` e `generate`, e
faz commit + push apenas quando algo muda. Assim `data/languages.json`, o README e os SVGs
ficam sempre refletindo os repositórios atuais, sem intervenção manual.
