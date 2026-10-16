---
id: iara.delivery-workflow
---

# Entrega sequencial full stack

## Quando aplicar

Use esta skill sempre que uma mudança atravessar a API e a interface, alterar persistência, autenticação, streaming ou a forma como uma conversa é reaberta. Mudanças locais devem seguir o workflow da camada afetada e ainda respeitar os contratos compartilhados.

## Sequência de trabalho

1. **Entender o resultado do usuário.** Descreva o fluxo atual e o fluxo esperado, incluindo estados vazios, carregamento, falha, cancelamento e retomada. Converta o pedido em critérios observáveis.
2. **Localizar o contrato.** Inspecione rotas, modelos Pydantic, eventos de streaming e componentes que consomem esses dados. Identifique consumidores antigos e o impacto em conversas persistidas.
3. **Definir a mudança de contrato primeiro.** Especifique nomes, tipos, nulabilidade, ordenação, estados terminais e compatibilidade. Não derive modelos de UI diretamente de payloads do provider.
4. **Implementar e verificar o backend.** Faça autorização e persistência antes de expor o novo comportamento. Use o workflow backend; injete provider fake para testes determinísticos.
5. **Implementar e verificar o frontend.** Consuma apenas a API Iara. Cubra estados de carregamento, streaming parcial, erro e retorno do histórico. Use o workflow frontend.
6. **Executar o fluxo integrado.** Rode o alvo `harness`, os gates das duas camadas e o smoke E2E. Exercite pelo menos um caminho feliz e uma falha relevante.
7. **Fechar com evidência.** Resuma arquivos alterados, verificações executadas, comportamento demonstrável, riscos conhecidos e qualquer decisão ainda pendente.

## Regras de coordenação

- Siga a regra bloqueante compartilhada `iara.task-completion`: mantenha o pedido autorizado ativo até terminar o escopo necessário. Uma entrega parcial, interrupção de ferramenta, limite de tentativas ou resposta de status não encerra a tarefa.
- Se aprovação, decisão, serviço ou credencial impedir um passo, continue o trabalho independente autorizado, registre evidências e atualize a retomada com causa e próximo passo. Não declare concluído enquanto houver trabalho autorizado necessário pendente.
- Em uma interrupção ou retomada, preserve o objetivo original salvo cancelamento/substituição explícitos do usuário; confira o checkpoint e retome no passo que falta.

- A execução deste projeto é sequencial; não presuma disponibilidade de agentes auxiliares.
- Se o contrato não estiver claro, faça uma proposta pequena e compatível com a implementação existente antes de expandi-lo.
- Preserve compatibilidade das conversas armazenadas. Se a forma persistida mudar, defina leitura dos registros antigos ou uma migração explícita.
- Não confunda um fake com prova de disponibilidade do provider real. Nomeie e mantenha separadas as verificações locais e a demonstração externa.
- Não passe credenciais, prompts ou conteúdo privado entre camadas em logs, artefatos de teste ou mensagens de erro.
- Todo estado transitório precisa de destino terminal: concluído, falhou ou cancelado.

## Critérios de conclusão

- Os critérios do pedido podem ser observados em UI ou API e têm testes associados.
- O backend valida entrada, autoriza o dono do recurso e persiste o estado necessário para retomar.
- A UI apresenta estados de sucesso e de falha sem expor payload interno.
- Contratos antigos continuam aceitos ou existe migração compatível.
- Harness, testes das camadas e smoke integrado passam; qualquer gate não executado fica declarado no handoff.
- Cada critério autorizado está atendido ou há bloqueio específico documentado; limite de iteração, item adiado ou resultado parcial não é tratado como sucesso.
