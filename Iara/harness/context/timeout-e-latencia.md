# Pendência: timeout e latência

Atualizado em 20/10/2026. O timeout total do Backend foi confirmado em quatro execuções anteriores. A instrumentação foi corrigida e uma chamada sintética pelo provider real foi medida por estágio; ela não reproduziu timeout. Nenhum limite foi alterado.

## Sintomas observados

- Em uma rodada recente de 13 cenários, com 14 solicitações, o primeiro conteúdo visível apareceu em geral entre 23 e 71 segundos.
- Duas solicitações ultrapassaram o limite de observação de 72 segundos usado pelo monitor do teste. Havia conteúdo visível; esse resultado não comprova que o Backend encerrou a solicitação por timeout.
- Em 15/10/2026, uma resposta completa do provider levou cerca de 77 segundos.
- A meta de 5–7 segundos para o primeiro conteúdo foi mencionada anteriormente e deve ser comparada com medições atuais antes de ser tratada como SLO vigente.

## Verificação interativa e logs — 20/10/2026

- O Compose estava saudável e o Backend confirmou `APP_ENV=development`, provider `iara`, alias `principal` e presença de chave/URL configuradas. Os valores secretos não foram exibidos.
- Duas solicitações sintéticas foram enviadas pelo chat usando o provider configurado. A resposta curta concluiu em aproximadamente 2,9 s; a resposta explicativa mais longa concluiu em aproximadamente 6,1 s. Nenhuma das duas expirou. Esses tempos são da solicitação completa, não do primeiro token.
- A fila `erros_sistema` contém quatro falhas `timeout` em 19/10. Comparadas aos aceites HTTP correspondentes, elas ocorreram aproximadamente 120,0–120,4 s depois. Uma solicitação ainda persistida durou 120,373 s. Isso confirma que o prazo total de 120 s do Backend disparou nesses casos; não foi apenas o limite de observação de 72 s.
- O prazo do SDK/provider continua em 360 s. Como o `asyncio.wait_for` do Backend limita a geração a 120 s, essa camada encerra a operação antes do timeout de rede configurado, nos casos medidos.
- Os logs técnicos registraram o POST de aceite em 6–10 ms e o GET de `/eventos` SSE em apenas 2–6 ms. A solicitação real continuou por segundos ou até 120 s. O middleware mede a criação/início do `StreamingResponse`, não a duração do corpo SSE; esse valor não serve como duração da geração.
- A fila de erros conserva apenas código e tipo (`timeout`/`ErroGateway`), sem etapa ou duração. Não foi possível saber se cada caso ficou aguardando o primeiro chunk do provider, recebeu deltas e demorou para concluir, ou ficou na normalização final.
- A rota de métricas internas estava desativada no ambiente atual porque `IARA_METRICS_TOKEN` não estava configurado. Nos logs Docker examinados também não apareceu a linha de conclusão do provider esperada pelo logger INFO.

## Correções e reprodução instrumentada — 20/10/2026

- O middleware agora mede e persiste o tempo até o fim do corpo HTTP/SSE, incluindo desconexão/interrupção. Um teste unitário com corpo SSE de 60 ms verifica que o registro só ocorre depois do consumo e inclui essa espera.
- Os loggers operacionais da API, do Gateway e das solicitações agora emitem eventos `INFO` mesmo quando o logger raiz está em `WARNING`. Os campos são serializados em texto seguro: UUID de correlação, provider lógico, etapa/código estável, rota template e duração; mensagens, prompts, credenciais e payload não são registrados.
- O Gateway marca primeiro evento recebido do provider, primeiro texto do provider, primeiro delta público, conclusão e cancelamento, incluindo a etapa em que ocorreu o cancelamento. Timeout do provider, falha de conexão e prazo total do Backend recebem categorias internas diferentes (`timeout_provider`, `conexao_provider`, `prazo_backend`); o código público continua `timeout`.
- A reprodução integrada em `APP_ENV=development` enviou uma solicitação sintética curta usando o provider real `iara`; não usou dados empresariais. O fluxo concluiu e emitiu `solicitacao.iniciada`, estados, deltas e `solicitacao.concluida`. As medições do Backend foram: primeiro evento do provider **140 ms**, primeiro texto do provider **1.908 ms**, primeiro delta público **2.098 ms**, operação concluída **2.111 ms** e corpo SSE completo **2.128 ms**. O cliente PowerShell observou 4.188 ms, incluindo seu próprio overhead; a métrica autoritativa do Backend é a linha correlacionada de 2.128 ms.
- No código anterior, o nível efetivo `WARNING` suprimia os marcos operacionais `INFO`; após a correção, os logs correlacionados ficaram visíveis no container. O diagnóstico administrativo também passou a registrar o GET SSE com duração na escala do stream, não da abertura da resposta.
- `scripts/harness.ps1 -Target backend` passou: Ruff, **183 testes**, cobertura **85,89%** (mínimo exigido: 80%). Os testes cobrem duração SSE, primeiro evento/cancelamento do provider, categorização do prazo total do Backend e configuração allowlisted dos loggers.

### Conclusão desta rodada

O **limite que encerrou pelo menos quatro solicitações é o timeout total do Backend (120 s)**. A amostra atual bem-sucedida mostra que o fluxo instrumentado funciona e terminou em aproximadamente 2,1 s, com a maior parte da espera entre o primeiro evento e o primeiro texto do provider. Ela não reproduz nem explica retrospectivamente as falhas de 19/10.

Os tempos acima não identificam, por si só, a camada responsável. Não confundir o limite do monitor do teste com os timeouts da aplicação ou do provider.

## Limites atualmente registrados

- Cliente do provider: timeout de rede de 360 segundos, sem retry automático.
- Backend: prazo total padrão de 120 segundos, configurável entre 1 e 360 segundos.
- Durante a espera: status operacional periódico a cada 15 segundos. Esse status não reinicia nem amplia o prazo e não chama a LLM novamente.
- O limite anterior de 40 segundos se referia à proposta de espera para a integração de dados/MCP. Essa integração HTTP direta ainda não está configurada; não aplicar esse limite à chamada atual da LLM sem uma decisão específica.

## Como diagnosticar uma nova ocorrência

Para uma solicitação lenta, correlacione as linhas pelo UUID técnico do request e a solicitação. Os marcos abaixo já são registrados sem conteúdo de conversa, prompts, resposta, chaves ou dados empresariais:

1. envio do Frontend até aceite do Backend;
2. início da chamada ao provider;
3. conexão/primeiro evento recebido do provider;
4. primeiro delta útil recebido pelo Backend e primeiro texto visível no Frontend;
5. conclusão, cancelamento ou falha em cada camada;
6. tempo de reconexão SSE, se ocorrer.

Ao comparar os registros, identificar se o encerramento veio do monitor local, navegador/proxy, limite total do Backend, timeout de rede do provider, cancelamento do usuário ou falha remota. A mensagem visível ao usuário e o código interno da falha devem ser comparados com o mesmo ID de correlação.

## Próxima ação

Se houver nova demora, consultar os logs do container e o painel administrativo usando o mesmo `request_id`: `provider_primeiro_evento`, `provider_primeiro_texto`, `iara_primeiro_delta_publico`, `operacao_provider_concluida`/`operacao_provider_falhou`, `provider_cancelado`, `timeout_prazo_backend` e a conclusão HTTP do GET SSE. A etapa com a maior duração identifica onde o tempo foi consumido; o tipo interno do erro identifica qual relógio encerrou. Não aumentar timeouts como substituto da investigação nem atribuir a falha à API de dados sem evidência.

## Estado da conclusão

- **Confirmado:** pelo menos quatro solicitações foram encerradas pelo prazo total de 120 segundos do Backend; as falhas ocorreram aproximadamente 120 s após o aceite.
- **Corrigido e testado:** duração HTTP até o fim do corpo SSE; logs operacionais `INFO` visíveis no container; categorização interna dos timeouts; marcos do primeiro evento, primeiro texto, primeiro delta público e cancelamento.
- **Confirmado em uma amostra:** provider real respondeu sem timeout; primeiro delta público em 2.098 ms e conclusão em 2.111 ms; duração HTTP SSE registrada em 2.128 ms.
- **Ainda impossível de determinar retrospectivamente:** a etapa interna das quatro falhas de 19/10, pois não existiam marcos por estágio na ocasião. Uma nova falha poderá ser localizada com os registros implementados.
- **Pendente:** primeiro texto percebido/recebido no navegador e validação em amostras lentas reais. A meta de 5–7 s para primeiro conteúdo deve ser comparada com novas medições antes de ser tratada como SLO vigente.
