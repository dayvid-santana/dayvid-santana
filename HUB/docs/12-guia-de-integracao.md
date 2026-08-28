# Guia de integração de um sistema externo

## Resultado esperado

Ao final, o sistema deve aparecer na matriz, responder ao teste administrativo, participar de uma varredura e produzir um snapshot com status compreensível.

## Pré-requisitos

- URL acessível a partir do backend, não apenas do navegador.
- CPF de teste autorizado.
- definição do que significa “acesso ativo” na origem.
- código HTTP que representa ausência; por padrão, `404`.
- credencial armazenada fora do código e disponível para o ambiente.
- exemplo de resposta de sucesso e ausência.

## Escolher o tipo

| Situação da API | Tipo |
| --- | --- |
| aceita CPF na URL e devolve uma pessoa | `individual` |
| devolve coleção paginada e o backend precisa indexar por CPF | `lista` |

## Opção A — integração individual

### Cadastro mínimo

```json
{
  "slug":"portal-beneficios",
  "nome":"Portal de Benefícios",
  "url_template":"https://beneficios.exemplo.com/api/users/{cpf}",
  "tipo_integracao":"individual",
  "tipo_autenticacao":"bearer",
  "chave_acesso":"segredo-do-ambiente",
  "timeout_seconds":10,
  "json_schema":{
    "type":"object",
    "required":["id","enabled"],
    "properties":{"id":{"type":["string","integer"]},"enabled":{"type":"boolean"}}
  },
  "mapping_rules":{
    "access_active":{"path":"$.enabled","type":"boolean"},
    "origin_id":{"path":"$.id","type":"string"},
    "profiles":{"path":"$.profiles[*]","type":"string"},
    "attributes":"$"
  }
}
```

O `url_template` precisa conter `{cpf}`. A resposta HTTP 200 passa pelo schema; depois o mapeamento deve gerar `access_active`.

## Opção B — integração em lista

### Cadastro mínimo

```json
{
  "slug":"sults",
  "nome":"SULTS",
  "url_template":"https://api.exemplo.com/v1/pessoas",
  "tipo_integracao":"lista",
  "campo_cpf":"cpf",
  "campo_acesso":"enabled",
  "parametro_pagina":"start",
  "parametro_limite":"limit",
  "tamanho_pagina":100,
  "tipo_autenticacao":"token",
  "chave_acesso":"segredo-do-ambiente"
}
```

O backend busca a coleção uma vez por ciclo, seleciona os registros cujo CPF corresponde e aplica o mapeamento. Se `mapping_rules` for omitido, `campo_acesso` deriva `access_active`, `origin_id` e `attributes`.

## Usar descoberta assistida

1. Envie `POST /api/sistemas/discover` com URL, CPF de teste e credencial.
2. Revise as tentativas, status HTTP, formato detectado, campo CPF e sugestões.
3. Confirme apenas se o item selecionado corresponde ao CPF, nunca apenas porque houve HTTP 200.
4. Envie a configuração revisada para `POST /api/sistemas/discover/confirm`.
5. Consulte a versão criada em `/api/sistemas/{slug}/schemas`.

A descoberta é somente leitura até a confirmação.

## Validar antes da primeira varredura

1. `GET /ready` a partir do ambiente do backend.
2. `POST /api/sistemas/{slug}/teste` com CPF autorizado.
3. Confirmar status, HTTP, causa, schema, mapeamento e `access_active`.
4. Conferir se a credencial não apareceu na resposta nem nos logs.
5. Executar `POST /api/varreduras?employee_id=...` para uma pessoa.
6. Consultar `/api/matriz` e `/api/colaboradores/{id}/sistemas/{slug}/detalhes`.
7. Ativar o sistema somente depois de validar a regra.

## Checklist de contrato

- [ ] CPF normaliza para 11 dígitos.
- [ ] Campo de acesso distingue booleano verdadeiro/falso.
- [ ] Ausência não é confundida com erro de integração.
- [ ] Schema rejeita payload incompleto.
- [ ] Mapeamento cobre perfis, permissões e data quando existentes.
- [ ] Lista não escolhe o primeiro registro cegamente.
- [ ] Paginação para em condição válida e não repete página.
- [ ] Timeout é menor ou igual ao SLA acordado.
- [ ] Credencial é diferente por ambiente.
- [ ] Sistema de desenvolvimento não entra em indicador operacional.

## Troubleshooting rápido

| Sintoma | Verificar |
| --- | --- |
| `401/403` | tipo, nome do cabeçalho e credencial |
| `429` | limite, tamanho da página e concorrência |
| HTTP nulo | DNS, rota, proxy, TLS e CA |
| `PAYLOAD_INVALIDO` | exemplo real, schema e caminho JSON |
| `SEM_ACESSO` inesperado | código de ausência e CPF enviado |
| lista sem registros | `campo_cpf`, paginação e formato `data` |
| CPF duplicado | aviso de duplicidade e regra de seleção |

