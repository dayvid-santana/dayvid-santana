# Glossário e decisões arquiteturais

## Glossário

| Termo | Definição |
| --- | --- |
| Senior | fonte dos dados funcionais dos colaboradores |
| Hub | aplicação centralizadora de auditoria |
| Colaborador | vínculo identificado pela chave composta |
| CPF | chave usada para consultar sistemas externos; não é identidade interna única |
| Chave composta | empresa + filial + tipo + matrícula |
| Sistema integrado | API externa cadastrada no Hub |
| Integração individual | consulta por colaborador usando `{cpf}` |
| Integração lista | coleta paginada indexada por CPF |
| Snapshot | evidência persistida de uma consulta |
| Schema version | versão do contrato de validação/mapeamento usada na consulta |
| Payload bruto | resposta original da API externa |
| Payload normalizado | resposta convertida para `NormalizedAccess` |
| Situação 7 | código funcional usado na regra crítica de auditoria |
| Acesso divergente | acesso ativo incompatível com regra de negócio |
| Alerta | ocorrência persistida para acompanhamento do auditor |
| Sistema operacional | integração ativa e não reservada para desenvolvimento nos indicadores |

## Decisões

### ADR-001 — Backend interpreta integrações

**Decisão:** o backend chama APIs, valida payloads, normaliza dados e calcula estados. O frontend apenas consulta e exibe.

**Motivo:** impedir regras duplicadas e tornar a matriz independente da latência das APIs externas.

### ADR-002 — Snapshot mais recente na matriz

**Decisão:** cada consulta cria snapshot; a matriz usa o mais recente por colaborador+sistema.

**Motivo:** preservar histórico e permitir auditoria/reprodução.

### ADR-003 — CPF não é chave interna

**Decisão:** identidade é a chave composta; CPF serve para consulta externa.

**Motivo:** um CPF pode aparecer em vínculos diferentes no Senior.

### ADR-004 — CSV e SQL sob o mesmo contrato

**Decisão:** ambas as fontes Senior expõem as dez colunas obrigatórias.

**Motivo:** trocar a infraestrutura sem alterar o scanner e o frontend.

### ADR-005 — Integração configurável por schema/mapeamento

**Decisão:** novos sistemas usam JSON Schema e `mapping_rules` antes de exigir código dedicado.

**Motivo:** reduzir custo de integração e manter histórico de versões.

### ADR-006 — Varredura manual e automática compartilham lock

**Decisão:** uma trava impede ciclos concorrentes.

**Motivo:** evitar snapshots conflitantes, pressão duplicada nas origens e alertas inconsistentes.

### ADR-007 — Ausência é diferente de falha

**Decisão:** somente código de ausência configurado produz `SEM_ACESSO`; timeout, rede, autenticação e servidor produzem erro.

**Motivo:** não transformar indisponibilidade em falso negativo de segurança.

### ADR-008 — Preparação de banco explícita

**Decisão:** startup verifica schema; provisionamento/migration altera schema.

**Motivo:** evitar alteração silenciosa em produção.

### ADR-009 — Sessão mock é temporária

**Decisão:** o provedor mock facilita prototipação, mas não é controle de segurança.

**Próximo passo:** definir provedor real, autorização, expiração, logout e auditoria de ações.

