# Integrações e motor de varredura

## Fontes do Senior

### CSV — desenvolvimento/protótipo

Arquivo padrão: `data/colaboradores.csv`. Deve possuir as dez colunas do contrato. Linhas inválidas e duplicadas são descartadas e ficam disponíveis em `GET /api/inconsistencias`.

### View PostgreSQL — produção

Definida por `SENIOR_SQL_DATABASE_URL` e `SENIOR_SQL_VIEW`. A view precisa expor o mesmo contrato do CSV. O backend consulta apenas leitura; o Hub não altera o sistema Senior.

## Dois tipos de integração externa

### Individual

O sistema é consultado para cada colaborador. `url_template` deve conter `{cpf}`; antes da chamada o backend substitui o placeholder pelo CPF normalizado.

### Lista

O sistema expõe uma coleção paginada, sem uma consulta por CPF. O backend baixa as páginas uma vez e indexa os registros pelo campo configurado em `campo_cpf`. `campo_acesso` pode ser usado para derivar o mapeamento simples quando ele não for fornecido.

## Autenticação externa

Tipos aceitos no cadastro: `token`, `bearer`, `basic`, `header` e `none`. O nome do cabeçalho é configurável. O segredo não é devolvido no `GET /api/sistemas` nem deve aparecer em logs. Com `none`, uma credencial enviada é rejeitada para evitar configuração ambígua.

## Pipeline de uma consulta individual

```text
colaborador Senior
  -> CPF normalizado
  -> URL/método/cabeçalhos
  -> resposta HTTP
  -> classificação técnica
  -> JSON Schema (se sucesso)
  -> seleção de item (se necessário)
  -> mapeamento para NormalizedAccess
  -> regra de negócio (divergência/alerta)
  -> snapshot persistido
```

## Classificação dos resultados

| Situação da chamada | Estado persistido |
| --- | --- |
| HTTP de sucesso + acesso ativo | `COM_ACESSO` |
| Código de ausência configurado | `SEM_ACESSO` |
| HTTP sucesso + schema/mapeamento inválido | `PAYLOAD_INVALIDO` |
| timeout | `TEMPO_EXCEDIDO` |
| autenticação, rate limit, rede, 5xx ou demais falhas | `ERRO_INTEGRACAO` |
| acesso ativo em regra crítica | `ACESSO_DIVERGENTE` |

O código de ausência é configurável por sistema, embora `404` seja o padrão. Uma resposta sem acesso não deve ser confundida com um HTTP 401/403 ou timeout.

## Varredura manual

`POST /api/varreduras` aguarda a trava se outra varredura estiver em andamento, executa o ciclo e devolve apenas o resumo:

```json
{
  "colaboradores_processados": 1200,
  "snapshots_criados": 4800,
  "lotes_processados": 6,
  "status": "concluída",
  "inconsistencias": []
}
```

Use `employee_id` para uma chave composta específica e `batch_size` para sobrescrever o lote. Os detalhes ficam em matriz, detalhes de acesso e monitoramento.

## Varredura automática

Ativada por padrão. Executa uma varredura imediata no início e repete depois do intervalo configurado. Apenas sistemas ativos participam. Um erro em um sistema é registrado e não impede o processamento dos demais.

- `AUTO_SCAN_ENABLED`: `true`/`false`.
- `SCAN_INTERVAL_MINUTES`: padrão 15.
- `INGESTION_BATCH_SIZE`: padrão 200.
- `REQUEST_CONCURRENCY_PER_SYSTEM`: padrão 10.

## Diagnóstico

Cada snapshot pode registrar `failure_cause`, `error_detail`, HTTP, duração e aviso. Para integrações em lista, `list_fetch_status` registra a página e os contadores da coleta. `GET /api/monitoramento/varreduras` reúne esse material sem expor payload bruto.

## Versionamento

Alterar schema ou mapeamento cria uma nova versão. A anterior continua no banco para explicar snapshots históricos. Novos resultados usam a versão ativa no momento da consulta e salvam sua referência no snapshot.

