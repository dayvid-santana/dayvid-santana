# Testes e critérios de aceite

## Portões de qualidade

Uma mudança só deve ser promovida quando:

- compila;
- passa lint quando aplicável;
- passa testes unitários;
- passa testes de integração;
- mantém contratos de API compatíveis ou documenta breaking change;
- passa smoke test Docker quando altera infraestrutura;
- possui teste para o caminho de erro relevante.

## Matriz de cobertura

| Área | Cenários mínimos |
| --- | --- |
| Senior CSV/SQL | contrato ausente, CPF inválido, duplicidade, CPF compartilhado, lotes |
| CPF | pontuação, zero à esquerda, valor inválido |
| Schema/mapeamento | schema inválido, caminho JSON, default, tipo, lista por CPF |
| Scanner individual | 200, ausência, 401/403, 429, 5xx, timeout, DNS, payload inválido |
| Scanner lista | paginação, página vazia, total, repetição, duplicidade, falha parcial |
| Snapshots | último registro, versão, histórico, vínculo removido |
| Alertas | criar, atualizar, ignorar com justificativa, resolver após nova varredura |
| Agendamento | execução inicial, intervalo, lock, cancelamento, erro isolado |
| API | filtros, paginação, 404, 409, 422, readiness |
| Frontend | loading, vazio, erro, busca, paginação, detalhes, rota direta, admin |
| Segurança | segredo ausente das respostas/logs, CPF conforme política, CORS |

## Critérios funcionais

### Matriz

- deve exibir apenas colaboradores da fonte atual;
- deve usar o último snapshot por colaborador+sistema;
- deve diferenciar ausência de acesso e falha de integração;
- deve paginar sem carregar toda a matriz no cliente;
- deve explicar `NAO_CONSULTADO`.

### Varredura

- deve processar em lotes;
- não deve rodar manual e automática simultaneamente;
- falha de um sistema não deve impedir os demais;
- deve persistir evidência e diagnóstico;
- deve atualizar alertas conforme o resultado.

### Integração

- deve exigir `{cpf}` no tipo individual;
- deve exigir `campo_cpf` no tipo lista;
- deve validar schema antes de mapear;
- deve selecionar item por CPF;
- deve versionar alterações de contrato.

## Dados de teste

Usar colaboradores fictícios com:

- vínculo ativo e Situação 7;
- CPFs diferentes e mesmo CPF em vínculos distintos;
- filial/cargo diferentes;
- sistemas individual e lista;
- respostas externas simuladas para todos os estados.

Não usar CPF real em fixtures, logs ou screenshots.

## Limites ainda não medidos

O projeto possui testes de comportamento, mas ainda deve estabelecer baseline de volume: quantidade de colaboradores, sistemas, tempo de ciclo, p95 de endpoint, taxa de erro aceitável e tamanho máximo de snapshots. Esses números devem ser definidos antes de uma operação de grande escala.

