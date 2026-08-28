# Runbook operacional

## Objetivo

Este runbook orienta a pessoa de plantão a verificar o serviço sem modificar a origem dos dados e sem apagar evidências de auditoria.

## Inicialização

1. Confirmar variáveis do ambiente e disponibilidade do PostgreSQL.
2. Executar a preparação/migration aprovada.
3. Iniciar a API.
4. Verificar `GET /health`.
5. Verificar `GET /ready`.
6. Verificar `GET /api/sistemas`.
7. Consultar `/api/monitoramento/varreduras` e confirmar que o agendamento está conforme esperado.
8. Abrir o frontend e validar matriz, alertas e administração.

## API viva, mas não pronta

Sintoma: `/health` retorna 200 e `/ready` retorna 503.

1. Ler `checks.database` e `checks.senior`.
2. Se `database` falhar, validar URL, DNS, credencial, firewall, schema e pool.
3. Se `senior` falhar, validar URL/view, permissões somente leitura, contrato das dez colunas e conectividade a partir do container.
4. Corrigir a dependência e repetir `/ready`.
5. Não desabilitar o readiness para mascarar a causa.

## Varredura não iniciou

1. Consultar `/api/monitoramento/varreduras`.
2. Confirmar `automatico_habilitado`, intervalo e `em_andamento`.
3. Conferir logs de startup e `AUTO_SCAN_ENABLED`.
4. Verificar se há sistema ativo e fonte Senior com colaboradores válidos.
5. Disparar uma varredura manual de um colaborador.

## Varredura está em andamento por muito tempo

1. Não iniciar outro processo nem matar o container sem preservar logs.
2. Consultar chamadas recentes e última falha por sistema.
3. Verificar timeout configurado e `REQUEST_CONCURRENCY_PER_SYSTEM`.
4. Conferir indisponibilidade ou rate limit da origem.
5. Se for necessário reiniciar, registrar horário, motivo e última execução conhecida; o lock é memória do processo e será recriado no startup.
6. Após reiniciar, validar que os snapshots do último lote permanecem e executar um ciclo controlado.

## Sistema externo com falhas

Classifique antes de agir: autenticação (`401/403`), rate limit (`429`), ausência (`404` ou código configurado), rede/TLS, timeout, payload ou servidor (`5xx`).

1. Usar `POST /api/sistemas/{slug}/teste` com CPF autorizado.
2. Consultar `ultima_falha` e `causa` em `/api/monitoramento/varreduras`.
3. Comparar URL, método, paginação, header e schema com a documentação da origem.
4. Não marcar falha como `SEM_ACESSO` manualmente.
5. Se a API estiver indisponível, manter o sistema ativo e acompanhar a próxima varredura, ou desativá-lo com decisão registrada caso haja risco operacional.

## Payload inválido

1. Capturar o `snapshot_id` e a versão do schema.
2. Comparar `erros_validacao` com a resposta real.
3. Testar o mesmo payload no editor administrativo.
4. Criar nova versão do schema/mapeamento; não alterar a interpretação histórica.
5. Reexecutar teste e uma varredura de amostra.

## Banco indisponível

1. Preservar logs e timestamp.
2. Validar conexão sem alterar dados.
3. Consultar saúde do PostgreSQL, conexões, espaço e locks.
4. Após recuperação, executar `/ready`.
5. Verificar se a varredura automática retomou e se não existem duplicações indevidas.
6. Restaurar backup somente após aprovação e em ambiente separado primeiro.

## Alerta não resolveu

`RESOLVIDO` não é transição manual. Remova/corrija o acesso no sistema de origem, execute uma varredura bem-sucedida e confirme o snapshot sem acesso. Se o alerta continuar, verifique sistema consultado, chave composta, CPF e última versão de schema.

## Incidente e comunicação

Registrar: início/fim, ambiente, impacto, sistemas afetados, última varredura válida, causa técnica, ação tomada, snapshots preservados, responsável e próximo passo. Nunca incluir API key, senha, CPF completo ou payload sensível no ticket.

