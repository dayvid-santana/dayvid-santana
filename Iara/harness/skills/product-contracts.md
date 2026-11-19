---
id: iara.product-contracts
---

# Contratos de produto da Iara

## Fronteiras

A API Iara é a fronteira pública entre browser, persistência e Model Gateway. A UI conhece IDs, estados e blocos públicos da Iara; não conhece SDKs, nomes internos, headers nem payloads específicos de providers. Serviços analíticos também devem converter os resultados para os mesmos blocos públicos.

A URL e a credencial da API da Iara são configuração privada do Backend (`IARA_BASE_URL` e `IARA_API_KEY` carregadas localmente de `Backend/.env`, ou injetadas pelo ambiente seguro em produção). Ela nunca faz parte do contrato HTTP/browser. O modelo é selecionado pela configuração/alias do Gateway, não por um identificador de provider exposto à UI.

O gestor não escolhe nem vê provider ou modelo. O Backend pode persistir a identidade usada como metadado interno de histórico e auditoria; ela não faz parte do contrato público consumido pelo Frontend. A solicitação do gestor segue diretamente à LLM da Iara, sem pré-classificação ou reescrita por uma LLM intermediária. O Backend compõe um System Prompt versionado com instrução de aplicação e pedido original e envia até 40 mensagens recentes da conversa (incluindo o pedido atual composto).

Para dados empresariais, a fonte selecionada é o Grafana MCP. O Backend consulta ferramentas de leitura autorizadas e encaminha resultados necessários ao Model Gateway; a LLM interpreta e apresenta esses resultados nos blocos tipados da Iara. Não há acesso direto da aplicação ao banco empresarial nem análise espontânea. A LLM só descreve tendências ou calcula indicadores quando o gestor pedir explicitamente, usando dados retornados pela consulta autorizada; não inventa valores nem causas. Transporte, autenticação, catálogo de ferramentas e acesso ao MCP permanecem pendentes. Desenvolvimento e testes usam fixtures JSON sintéticas; elas também são a fonte padrão da demonstração por período prolongado. Consultas reais exigem autorização explícita.

O Frontend apresenta Markdown em `text` sem executar HTML bruto. JSON, código, HTML solto e fences permanecem como texto. Somente o HTML posterior a `iara-visuals` segue em `api_html`, na mensagem v2, para o iframe isolado. O renderer permite os scripts e recursos desse HTML; o iframe não recebe `allow-same-origin`, cookies ou credenciais da aplicação. Blocos legados `html` e `code` são apresentados literalmente.

## Conteúdo de mensagem

### Fonte e distribuição dos schemas compartilhados

Os schemas canônicos v1 e v2 são versionados em `Iara/contracts` neste repositório. Em um workspace com checkouts separados de Backend e Frontend, execute `Iara/scripts/exportarContratos.ps1 -workspaceRoot <raiz-do-workspace>` para copiar os quatro arquivos à pasta comum `<raiz-do-workspace>/contracts`. O script valida JSON e confirma os hashes SHA-256, sem reconstruir os schemas. A cópia do workspace é gerada a partir da revisão versionada; não a edite como fonte independente.

Uma resposta é uma lista ordenada de blocos discriminados: `text`, `code`, `kpi`, `kpi_group`, `table`, `chart`, `html`, `api_html`, `error` e `processing`. Cada tipo tem um discriminador público e campos definidos no schema da versão da mensagem. O Backend valida o envelope público e os blocos tipados legados, enquanto preserva o conteúdo de `text` e o HTML recebido em `api_html`.

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
