# API HTTP

## Convenções

- Prefixo das rotas de negócio: `/api`.
- Datas são retornadas em ISO 8601 UTC com milissegundos.
- Listas paginadas usam `data`/`itens` e `pagination` conforme o endpoint.
- Erros de validação de entrada retornam `422`; recurso inexistente normalmente retorna `404`.
- A documentação interativa do FastAPI fica em `/docs`.

## Infraestrutura e sessão

| Método | Rota | Função |
| --- | --- | --- |
| GET | `/health` | processo vivo |
| GET | `/ready` | banco + fonte Senior disponíveis |
| GET | `/api/sessao` | sessão mock atual |

## Consulta do dashboard

| Método | Rota | Função |
| --- | --- | --- |
| GET | `/api/sistemas` | sistemas ativos; administração pode incluir inativos |
| GET | `/api/filtros` | empresas, filiais, cargos e tipos disponíveis |
| GET | `/api/matriz` | matriz paginada, com busca server-side |
| GET | `/api/colaboradores` | contrato legado de listagem |
| GET | `/api/indicadores` | contadores operacionais |
| GET | `/api/resumo` ou `/api/dashboard/resumo` | resumo do painel |
| GET | `/api/filiais/metricas` | métricas de uma ou mais filiais |
| GET | `/api/cargos` | resumo por cargo |
| GET | `/api/cargos/{cargo_id}/colaboradores` | matriz paginada de um cargo |
| GET | `/api/colaboradores/{collaborator_id}/sistemas` | acessos do colaborador por sistema |
| GET | `/api/colaboradores/{collaborator_id}/sistemas/{slug}/detalhes` | detalhe de um snapshot |

### Busca e paginação da matriz

`GET /api/matriz?page=1&limit=200&search=ana` pesquisa nome, matrícula, CPF com ou sem pontuação, empresa, filial, nome da filial, código e descrição do cargo. O total é calculado antes de `LIMIT/OFFSET`.

Resposta atual:

```json
{
  "data": [],
  "pagination": {"total": 1450, "page": 1, "limit": 200, "totalPages": 8}
}
```

Chaves legadas continuam temporariamente para migração gradual do frontend.

## Alertas e regra crítica

| Método | Rota | Função |
| --- | --- | --- |
| POST | `/api/situacao-sete` | cálculo sob demanda para sistemas enviados |
| GET | `/api/alertas` | listar/filtrar alertas paginados |
| PATCH | `/api/alertas/{alert_id}` | alterar status de gestão; ignorado exige justificativa |

Filtros de alertas: `tipo`, `empresa`, `status`, `page` e `limit`. A API elimina alertas obsoletos de Situação 7 quando o colaborador ou o acesso atual já não satisfaz a regra.

## Administração de sistemas

| Método | Rota | Função |
| --- | --- | --- |
| POST | `/api/sistemas` | cadastrar integração |
| PUT | `/api/sistemas/{slug}` | atualizar configuração |
| DELETE | `/api/sistemas/{slug}` | remover cadastro e relações associadas |
| POST | `/api/sistemas/{slug}/logo` | enviar logo de imagem |
| GET | `/api/sistemas/{slug}/schemas` | listar versões |
| POST | `/api/sistemas/{slug}/schemas` | criar e ativar versão |
| POST | `/api/sistemas/{slug}/teste` | testar uma integração por CPF |
| POST | `/api/sistemas/teste?slug=...` | forma alternativa do teste |

O cadastro individual exige `url_template`, `json_schema` e `mapping_rules`. O cadastro em lista exige `campo_cpf`; com `campo_acesso` o backend pode derivar um mapeamento básico.

## Descoberta assistida

| Método | Rota | Função |
| --- | --- | --- |
| POST | `/api/sistemas/discover` | sondar URL com CPF de teste e sugerir configuração |
| POST | `/api/sistemas/discover/confirm` | confirmar sugestão e cadastrar |

Esse fluxo não deve escolher o primeiro item de uma lista sem confirmar que o CPF corresponde.

## Operação de varredura

| Método | Rota | Função |
| --- | --- | --- |
| POST | `/api/varreduras` | executar ciclo manual |
| GET | `/api/monitoramento/varreduras` | situação da trava, agendamento, contagens e últimas chamadas |
| GET | `/api/inconsistencias` | inconsistências da ingestão do Senior |

## Estáticos

Logos ficam disponíveis em `/static/logos`. O backend também serve o diretório estático geral em `/static`.

