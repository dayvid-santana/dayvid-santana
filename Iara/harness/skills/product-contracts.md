---
id: iara.product-contracts
---

# Contratos de produto da Iara

## Fronteiras

A API Iara é a fronteira pública entre browser, persistência e Model Gateway. A UI conhece IDs, estados e blocos públicos da Iara; não conhece SDKs, nomes internos, headers nem payloads específicos de providers. Serviços analíticos também devem converter os resultados para os mesmos blocos públicos.

A credencial OpenAI é configuração privada do backend (`OPENAI_API_KEY` carregada localmente de `Backend/.env`, ou injetada pelo ambiente seguro em produção). Ela nunca faz parte do contrato HTTP/browser. O modelo é selecionado pela configuração/alias do Gateway, não por um identificador de provider exposto à UI.

O gestor não escolhe nem vê provider ou modelo. O Backend pode persistir a identidade usada como metadado interno de histórico e auditoria; ela não faz parte do contrato público consumido pelo Frontend. A solicitação do gestor segue diretamente à LLM da Iara, sem pré-classificação ou reescrita por uma LLM intermediária. O Backend compõe um System Prompt versionado com instrução de aplicação e pedido original e envia até 40 mensagens recentes da conversa (incluindo o pedido atual composto).

Para dados empresariais, a fonte selecionada é o Grafana MCP. O Backend consulta ferramentas de leitura autorizadas e encaminha resultados necessários ao Model Gateway; a LLM interpreta e apresenta esses resultados nos blocos tipados da Iara. Não há acesso direto da aplicação ao banco empresarial nem análise espontânea. A LLM só descreve tendências ou calcula indicadores quando o gestor pedir explicitamente, usando dados retornados pela consulta autorizada; não inventa valores nem causas. Transporte, autenticação, catálogo de ferramentas e acesso ao MCP permanecem pendentes. Desenvolvimento e testes usam fixtures JSON sintéticas; elas também são a fonte padrão da demonstração por período prolongado. Consultas reais exigem autorização explícita.

HTML arbitrário do modelo nunca é injetado na página. Até contrato versionado e sanitização isolada existirem, são aceitos somente os blocos tipados existentes; HTML recebido como texto é escapado.

## Conteúdo de mensagem

Uma resposta é uma lista ordenada de blocos discriminados. Os tipos previstos são texto, KPI, grupo de KPIs, tabela, gráfico, erro e processamento. Cada tipo precisa de um discriminador explícito e de campos definidos por esquema; campos desconhecidos devem ser rejeitados na entrada confiável ou tratados pelo fallback seguro da UI, sem renderizar o payload cru.

- Preserve o ID, o tipo, a ordem e os dados necessários de cada bloco ao salvar e reabrir a conversa.
- Valores numéricos devem carregar unidade e precisão adequadas. Valores comparativos devem identificar período e contexto; proveniência deve ser declarada quando houver fonte analítica.
- Uma tabela deve ter esquema de colunas e linhas compatíveis. Um gráfico deve declarar série, categorias, unidades e resumo textual equivalente.
- Exemplos de demonstração são sintéticos e precisam ser identificados como tal. Não implicam uma fonte de dados real.
- Mensagens de erro não devem incorporar texto bruto do provider ou dados confidenciais.

## Eventos de streaming

Use os eventos canônicos já registrados no projeto: início de mensagem, delta de conteúdo, conclusão de bloco, conclusão de mensagem e falha. Cada evento pertence a uma conversa e mensagem identificáveis. A sequência é monotônica por mensagem; blocos mantêm ordem estável. Após um evento terminal (`message.completed`, `message.failed` ou cancelamento registrado), não pode haver novos deltas.

O cliente precisa distinguir uma mensagem parcial de uma concluída. Reconexão ou repetição não pode duplicar mensagens silenciosamente. O registro persistido deve permitir retomar a conversa com a mesma ordem visual, mesmo que o cliente tenha perdido a conexão durante a geração.

## Evolução

1. Atualize o modelo Pydantic e seus exemplos primeiro.
2. Atualize o adapter para emitir o contrato normalizado.
3. Atualize tipos, parser de eventos e renderizadores do frontend.
4. Considere conversas antigas, versão de esquema, campos ausentes e tipo desconhecido.
5. Adicione testes de validação, serialização, persistência, streaming e renderização acessível.

Evite mudanças incompatíveis aditivas disfarçadas: documente defaults, nulabilidade e o comportamento de clientes antigos. O contrato só está pronto quando backend, browser e histórico interpretam o mesmo conteúdo.
