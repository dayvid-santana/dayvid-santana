# Visão geral e necessidades atendidas

## O problema de negócio

Uma organização costuma manter o cadastro funcional dos colaboradores em um sistema de RH, como o Senior, e as permissões de cada pessoa espalhadas por vários sistemas corporativos. Sem uma visão consolidada, a auditoria precisa abrir cada sistema, usar critérios diferentes e comparar manualmente informações que mudam em ritmos distintos.

O risco mais relevante é a permanência de acesso depois de uma mudança funcional. Um colaborador desligado ou afastado pode continuar habilitado em sistemas críticos, e uma alteração de cargo pode deixar permissões incompatíveis com a função atual.

## O que o Hub resolve

O Hub centraliza a leitura desses dados e transforma o resultado em uma matriz única de auditoria. Ele resolve principalmente:

- **Fragmentação:** reúne acessos de diferentes APIs em uma única tela.
- **Falta de comparabilidade:** converte respostas heterogêneas para um modelo normalizado.
- **Dependência de consultas ao vivo:** persiste snapshots para que a interface seja rápida e reproduzível.
- **Baixa rastreabilidade:** guarda status técnico, HTTP, tempo de resposta, erros, payload normalizado e versão do contrato usada.
- **Detecção tardia de risco:** identifica acessos ativos de colaboradores em Situação 7.
- **Integrações caras de manter:** permite cadastrar sistemas, JSON Schema e regras de mapeamento sem criar uma classe específica para cada API.
- **Diagnóstico difícil:** separa autenticação, rede, timeout, limite de requisições, HTTP e payload inválido.
- **Escala de consulta:** suporta integração individual por CPF ou consulta de uma coleção paginada por ciclo.

## Quem usa

| Perfil | Necessidade | Visões principais |
| --- | --- | --- |
| Auditor/segurança | localizar acessos e priorizar riscos | Matriz e Alertas |
| RH/gestor | analisar pessoas por unidade e cargo | Filiais e Cargos |
| Administrador | cadastrar integrações e contratos | Administração |
| Operação/desenvolvimento | verificar saúde e falhas de varredura | `/health`, `/ready` e monitoramento |

## O que o sistema não faz

- Não altera sistemas externos nem remove acessos na origem.
- Não é a fonte oficial do cadastro funcional; o Senior continua sendo a fonte dos colaboradores.
- Não deve ser tratado como um IAM ou como o provedor de identidade dos usuários.
- Não faz consultas externas a cada abertura da matriz.
- Não considera automaticamente toda falha de integração como ausência de acesso.

## Regra crítica: Situação 7

O código `codigo_situacao_colaborador = 7`, vindo do Senior, identifica o conjunto de colaboradores que precisa de auditoria especial. Quando essa pessoa possui acesso ativo ou divergente em um sistema, o caso é evidenciado como risco.

O backend persiste/atualiza alertas do tipo `SITUACAO_7` durante a varredura. A consulta sob demanda `POST /api/situacao-sete` também calcula a situação para os sistemas ativos enviados pelo frontend, mas não cria alertas.

## Princípios que orientam o projeto

1. **Backend como fonte de interpretação:** o frontend recebe estados e dados já normalizados.
2. **Histórico antes de sobrescrita:** uma nova varredura cria snapshots; o último é usado na matriz.
3. **Falha explícita:** uma integração indisponível vira erro/timeout/payload inválido, nunca “sem acesso” por conveniência.
4. **CPF controlado no servidor (meta de segurança):** o CPF é usado nas chamadas externas pelo backend, mas o comportamento atual ainda o expõe normalizado em respostas públicas; o mascaramento está documentado como correção necessária em [Segurança e privacidade](14-seguranca-e-privacidade.md).
5. **Produção fail-fast:** configuração de produção incompleta deve impedir a inicialização.
