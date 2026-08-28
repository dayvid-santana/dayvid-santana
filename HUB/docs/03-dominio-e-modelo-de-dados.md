# Domínio e modelo de dados

## Identidade do colaborador

Cada linha do Senior deve conter as dez colunas:

`codigo_empresa`, `codigo_filial`, `nome_fantasia_filial`, `tipo_colaborador`, `matricula_colaborador`, `nome_colaborador`, `numero_cpf`, `codigo_situacao_colaborador`, `codigo_cargo` e `descricao_cargo`.

A identidade interna é composta por:

```text
codigo_empresa | codigo_filial | tipo_colaborador | matricula_colaborador
```

O CPF é normalizado para apenas dígitos e é a chave de consulta nos sistemas externos. O mesmo CPF pode aparecer em vínculos diferentes; esses vínculos não devem ser colapsados.

## Modelo normalizado de acesso

Após uma resposta externa válida, o motor produz:

| Campo | Significado |
| --- | --- |
| `access_active` | se o sistema considera o acesso ativo |
| `origin_id` | identificador da pessoa/registro na origem |
| `profiles` | perfis ou grupos atribuídos |
| `permissions` | permissões detalhadas |
| `registered_at` | data de criação/cadastro na origem |
| `attributes` | campos adicionais preservados |

## Estados técnicos da célula

| Código interno | Significado de negócio | Quando aparece |
| --- | --- | --- |
| `COM_ACESSO` | Com acesso | HTTP de sucesso, schema e mapeamento válidos, acesso ativo |
| `SEM_ACESSO` | Sem acesso | código de ausência configurado, por padrão HTTP 404 |
| `PAYLOAD_INVALIDO` | Payload inválido | HTTP de sucesso, mas schema/mapeamento não validam |
| `ERRO_INTEGRACAO` | Erro de integração | HTTP não tratado como ausência, rede ou outra falha |
| `TEMPO_EXCEDIDO` | Tempo excedido | timeout da chamada |
| `NAO_CONSULTADO` | Não consultado | ainda não há snapshot para a combinação |
| `CONSULTANDO` | Consultando | estado transitório/compatibilidade de contrato |
| `ACESSO_DIVERGENTE` | Acesso divergente | acesso ativo que viola regra de negócio, especialmente Situação 7 |

Falha de integração e sem acesso são conceitos diferentes. Um `401`, `403`, `429`, `5xx`, DNS ou timeout não autoriza concluir que a pessoa não possui acesso.

## Entidades persistidas

### `integrated_systems`

Cadastro do sistema: `slug`, nome, URL/template, ativo, timeout, credencial, tipo de autenticação, método HTTP, código de ausência, ordem de exibição, logo e parâmetros de integração em lista.

### `schema_versions`

Versões auditáveis do `json_schema` e `mapping_rules`. Cada sistema pode ter várias versões, mas uma fica ativa para novas consultas. A combinação `system_slug + version` é única.

### `snapshots`

Resultado de uma consulta de acesso. Guarda colaborador, sistema, versão do schema, status, HTTP, tempo, dados do colaborador, payload bruto, payload normalizado, erros de validação, causa técnica, detalhe de falha e aviso não fatal.

Uma nova execução insere novos snapshots. A matriz seleciona o mais recente por `(collaborator_key, system_slug)` usando o índice `ix_snapshots_collaborator_latest`.

### `collaborator_scan_states`

Agregado mais recente por colaborador: data de verificação e quantidades com acesso, sem acesso e com erro.

### `list_fetch_status`

Retrato da última busca paginada de um sistema do tipo lista. Não é histórico; registra sucesso, página de falha, URL, parâmetros, páginas lidas, registros lidos/indexados, duração e avisos.

### `alerts`

Ocorrência de auditoria por colaborador, sistema e tipo. Possui status de gestão, justificativa, última vez vista e data de resolução. A ocorrência é protegida por restrição única.

## Ciclo de vida do alerta

`NOVO` → `EM_ANALISE` → `RECONHECIDO` → `RESOLVIDO` ou `IGNORADO`.

O frontend pode atualizar estados de gestão, mas a API não permite marcar manualmente como `RESOLVIDO`: essa transição depende de uma varredura confirmar que o acesso deixou de existir. `IGNORADO` exige justificativa.

## Privacidade e exposição

O backend não devolve a credencial da integração; devolve, porém, o CPF normalizado dentro dos dados públicos de colaborador. O `AccessMatrix` atual também renderiza esse valor diretamente. Portanto, **o CPF ainda não está mascarado no comportamento atual**. A correção recomendada é mascarar o CPF no serializer público e manter o valor completo somente no backend, quando necessário para integração ou auditoria autorizada.

Payloads brutos, dados funcionais e detalhes de permissões devem ser tratados como sensíveis e não devem ser enviados para logs. O plano de segurança e privacidade está em [Segurança e privacidade](14-seguranca-e-privacidade.md).
