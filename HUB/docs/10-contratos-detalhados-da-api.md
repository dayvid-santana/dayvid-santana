# Contratos detalhados da API

Este documento complementa a lista de rotas de [API HTTP](06-api-http.md). O contrato definitivo exposto pela aplicação é o OpenAPI gerado em `/openapi.json`; exemplos abaixo representam o comportamento implementado e podem conter campos de compatibilidade legados.

## Convenções de erro

Erros de validação do FastAPI normalmente seguem:

```json
{
  "detail": [
    {"loc": ["body", "cpf"], "msg": "...", "type": "..."}
  ]
}
```

Erros de regra ou recurso usam:

```json
{"detail": "Sistema não encontrado"}
```

Status mais comuns: `200` sucesso, `201` criação, `204` remoção sem corpo, `404` recurso ausente, `409` conflito de slug, `422` entrada inválida e `503` readiness indisponível.

## Saúde

### `GET /health`

Não consulta dependências.

```json
{"status": "ok"}
```

### `GET /ready`

Verifica banco/schema do Hub e fonte Senior.

```json
{"status":"ok","checks":{"database":"ok","senior":"ok"},"senior_source":"csv"}
```

Quando uma verificação falha, retorna `503` com `status: "not_ready"` e o mapa de checks.

## Sessão

### `GET /api/sessao`

Contrato atual do provedor mock:

```json
{
  "autenticado": true,
  "usuario": {"id": 1, "nome": "Admin Mock", "perfil": "ADMIN"}
}
```

Não é autenticação de produção. O frontend tenta `POST /api/login` primeiro e faz fallback para esta rota quando recebe `404` ou `405`.

## Colaboradores e matriz

### `GET /api/colaboradores`

Parâmetros: `nome`, `cpf`, `matricula`, `empresa`, `filial`, `cargo`, `situacao`, `tipo`, `page` e `limit` (padrão 150, máximo 1000). A resposta preserva o contrato legado:

```json
{
  "colaboradores": [],
  "total_colaboradores": 120,
  "pagina": 1,
  "limite": 150,
  "total_paginas": 1,
  "ultima_atualizacao": "2026-08-24T12:00:00.000Z"
}
```

### `GET /api/matriz`

Parâmetros: `page` (padrão 1), `limit` (padrão 200, máximo 1000), `search`, `empresa`, `filial`, `cargo`, `situacao` e `tipo`. A pesquisa server-side cobre nome, matrícula, CPF, empresa, filial, nome da filial e cargo.

```json
{
  "data": [
    {
      "id": "1|10|CLT|123",
      "nome_colaborador": "Pessoa Exemplo",
      "numero_cpf": "12345678909",
      "codigo_empresa": "1",
      "codigo_filial": "10",
      "codigo_situacao_colaborador": 1,
      "cells": {
        "erp-financeiro": {
          "status": "Com acesso",
          "http_status": 200,
          "tempo_resposta_ms": 42.5
        }
      }
    }
  ],
  "pagination": {"total": 120, "page": 1, "limit": 200, "totalPages": 1}
}
```

O campo `cells` pode incluir diagnóstico, perfis, permissões, versão de schema, erros de validação e data da consulta. O backend também mantém chaves antigas temporariamente para compatibilidade.

## Resumos e filtros

### `GET /api/indicadores`

```json
{"colaboradores":120,"acessos_ativos":320,"acessos_divergentes":4,"integracoes":5}
```

Os indicadores consideram sistemas ativos cujo host não seja de desenvolvimento (`localhost`, loopback, `.local` ou `.test`).

### `GET /api/resumo` e `/api/dashboard/resumo`

```json
{
  "total_colaboradores": 120,
  "acessos_ativos": 320,
  "acessos_divergentes": 4,
  "integracoes": 5,
  "atualizado_em": "2026-08-24T12:00:00.000Z"
}
```

### `GET /api/filtros`

```json
{
  "empresas": ["1"],
  "filiais": [{"codigo":"10","nome_fantasia":"Matriz","empresa":"1"}],
  "cargos": ["Analista"],
  "tipos": ["CLT"]
}
```

### `GET /api/filiais/metricas?filial=1|10`

O parâmetro `filial` pode ser repetido.

```json
{
  "sistemas": [{"slug":"erp-financeiro","nome":"ERP Financeiro","acessos_ativos":12}],
  "erros_integracao": 1,
  "divergencias": 2,
  "colaboradores_criticos": 2
}
```

### `GET /api/cargos?search=analista`

```json
{"data":[{"id":"A1","nome":"Analista","colaboradores":20,"acessos_ativos":45}]}
```

`GET /api/cargos/{cargo_id}/colaboradores` aceita `page` e `limit` (padrão 50, máximo 200) e retorna `data` + `pagination`.

## Detalhe de acesso

`GET /api/colaboradores/{collaborator_id}/sistemas` retorna o colaborador, todos os sistemas e o diagnóstico de consulta de cada um. O `collaborator_id` é a chave composta codificada na URL.

`GET /api/colaboradores/{collaborator_id}/sistemas/{slug}/detalhes` retorna:

```json
{
  "status":"Com acesso",
  "http_status":200,
  "tempo_resposta_ms":42.5,
  "payload_original":{},
  "resultado_normalizado":{"access_active":true,"profiles":[]},
  "erros_validacao":[],
  "erro_integracao":null,
  "schema_version_id":3,
  "verificado_em":"2026-08-24T12:00:00.000Z"
}
```

`payload_original` pode conter dados sensíveis e deve ser protegido por autenticação real antes de disponibilizar a API fora da rede confiável.

## Sistemas

### Criação — `POST /api/sistemas`

Campos principais:

```json
{
  "slug":"erp-financeiro",
  "nome":"ERP Financeiro",
  "url_template":"https://erp.exemplo.com/users/{cpf}",
  "ativo":true,
  "timeout_seconds":10,
  "chave_acesso":"segredo",
  "tipo_autenticacao":"bearer",
  "nome_header_autenticacao":"Authorization",
  "tipo_integracao":"individual",
  "json_schema":{},
  "mapping_rules":{}
}
```

Para `tipo_integracao: "lista"`, informe `campo_cpf`; `parametro_pagina`, `parametro_limite` e `tamanho_pagina` configuram a paginação. `campo_acesso` permite derivar um mapeamento básico.

### Atualização — `PUT /api/sistemas/{slug}`

É parcial. Campos omitidos são preservados. `endpoint` e `url_template` são aliases; `chave_api` e `chave_acesso` também. Não envie string vazia para credenciais se deseja preservá-las.

### Lista — `GET /api/sistemas`

Não devolve a chave secreta. Informa apenas `chave_configurada: true/false`, além de URL, tipo, timeout, paginação, método, código de ausência, ordem e logo.

## Schemas e teste

`GET /api/sistemas/{slug}/schemas` lista `{id, versao, ativa, json_schema, mapeamento, criado_em}`. `POST /api/sistemas/{slug}/schemas` recebe `{json_schema, mapeamento}` e cria a próxima versão ativa.

`POST /api/sistemas/{slug}/teste` recebe `{ "cpf": "12345678909" }`. A resposta inclui status de negócio, HTTP, tempo, payload original, resultado normalizado, erros, causa, mensagem amigável, sugestão e se a credencial está configurada.

## Alertas

`GET /api/alertas` aceita `tipo`, `empresa`, `status`, `page` e `limit` (máximo 1000):

```json
{
  "total":1,
  "itens":[{
    "id":10,
    "tipo":"SITUACAO_7",
    "status":"NOVO",
    "sistema":{"slug":"erp-financeiro","nome":"ERP Financeiro"},
    "ultima_verificacao":"2026-08-24T12:00:00.000Z",
    "justificativa":null,
    "colaborador":{},
    "risco":{"http_status":200,"perfis":[],"permissoes":[]}
  }],
  "pagination":{"total":1,"page":1,"limit":200,"totalPages":1}
}
```

`PATCH /api/alertas/{id}` recebe `{ "status": "EM_ANALISE", "justification": null }`. `IGNORADO` exige justificativa; `RESOLVIDO` é rejeitado manualmente e só é aplicado após uma varredura confirmar a ausência.

## Varredura e monitoramento

`POST /api/varreduras` aceita `employee_id` e `batch_size`. `GET /api/monitoramento/varreduras` retorna `em_andamento`, agendamento, última execução, resumo por sistema e chamadas recentes, incluindo causa/HTTP/duração, mas não deve expor segredo.

`POST /api/situacao-sete` recebe `{ "sistemas": ["erp-financeiro"] }`. É leitura sob demanda, descarta sistemas inativos e não cria alertas.

