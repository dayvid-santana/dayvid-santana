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
