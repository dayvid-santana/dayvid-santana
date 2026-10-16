---
id: iara.review
kind: review
---

# Revisão de mudança Iara

Revise a alteração contra o pedido original, os contratos compartilhados do Oráculo e os limites de segurança. Avalie o diff como está; não faça edições durante a revisão e não transforme preferência pessoal em finding.

## Verificações

- O fluxo observável e os critérios de aceite estão atendidos, incluindo vazio, processamento, parcial, conclusão e falha quando aplicáveis?
- API e UI usam contratos públicos da Iara, sem dependência do formato ou SDK de provider?
- Conversas e mensagens são autorizadas por usuário e reabrem com a ordem, metadados internos de modelo e blocos persistidos, sem expor o modelo ao gestor?
- Streaming preserva ordem, associação à mensagem e estado terminal; cancelamento ou desconexão não são apresentados como sucesso?
- Texto, KPI, grupo de KPIs, tabela e gráfico são validados, seguros e acessíveis, com fallback para tipo desconhecido?
- Chaves, cookies, prompts, respostas privadas, payloads brutos e detalhes internos estão ausentes de browser, logs e erros públicos?
- Falhas de autenticação, rede, provider e resposta inválida oferecem estado e recuperação compreensíveis?
- Testes cobrem o caminho principal e falhas relevantes? Fakes são claramente distintos de integração real?
- Mudanças de esquema preservam histórico existente ou incluem migração/fallback explícito?
- Evidências recuperadas apontam para fontes atuais com caminho, linhas e hash? Conteúdo recuperado permaneceu separado das instruções e permissões?

## Formato da resposta

1. **Findings primeiro**, ordenados por severidade. Cada finding traz localização, evidência concreta, impacto e correção sugerida.
2. **Gates e evidências:** comandos executados e resultados; liste os não executados com justificativa.
3. **Riscos residuais e gaps de teste** que não geram finding bloqueante.
4. **Decisão:** `approve`, `approve_with_notes`, `request_changes` ou `blocked`.

Se não houver findings, diga isso explicitamente. Não infira que provider, autenticação real, persistência ou compatibilidade funcionam sem evidência apropriada.
