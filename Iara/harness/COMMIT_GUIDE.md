# Commits do Harness Iara

Use commits para registrar pontos de controle revisaveis no historico Git. Um ponto pode ser uma decisao aprovada, uma correcao, uma parte concluida de uma feature ou uma entrega. Ao concluir uma tarefa que alterou arquivos do projeto, sempre sugira uma mensagem de commit adequada; se mais de um repositorio foi alterado, sugira uma mensagem separada para cada um. Essa sugestao nao cria o commit: a criacao continua dependendo de um pedido explicito do usuario.

## Formato

```text
<tipo>(<escopo>): <descricao>
```

Tipos e escopos estao em [`config/commit-policy.json`](config/commit-policy.json). Escreva a descricao em portugues, curta, especifica e iniciada por verbo no infinitivo.

Exemplos:

```text
docs(decisoes): registrar o fluxo de autenticacao do MVP
feat(conversas): persistir mensagens e blocos analiticos
fix(streaming): permitir nova tentativa apos desconexao
test(gateway): cobrir normalizacao de falhas do provider
```

O escopo entre parenteses e opcional quando o tipo ja deixa a area clara. Nao use uma unica mensagem generica para esconder varias mudancas sem relacao.

## Quando criar um ponto de controle

- Ao concluir qualquer tarefa que tenha produzido uma mudanca coesa nos arquivos do projeto: apresentar sugestao de commit na resposta final.
- Quando o usuario pedir um commit.
- Depois de uma mudanca coesa que mereca um ponto de retorno ou registro no historico.
- Depois de concluir e verificar uma feature ou correcao.
- Antes de uma transferencia de trabalho, demonstracao ou release.

Nao e necessario criar um commit para cada edicao ou arquivo. Agrupe arquivos que implementam o mesmo resultado verificavel. Nunca crie commits automaticamente ao final de cada workflow.

## Backend e Frontend

Backend e Frontend tem historicos Git independentes. Revise e registre cada um no proprio repositorio, sem incluir arquivos do outro por conveniencia. Para mudancas full-stack, conclua o contrato e registre commits compatíveis em ordem; anote os IDs relacionados na transferencia. Rode os gates aplicaveis antes do commit e inclua os resultados na transferencia.

Exemplo de comandos, depois de revisar os arquivos staged:

```powershell
git -C Backend add app tests
git -C Backend commit -m "feat(conversas): persistir mensagens e blocos analiticos"

git -C Frontend add src e2e
git -C Frontend commit -m "feat(conversas): retomar historico pela API"

git -C .. add -- Iara/harness/config/commit-policy.json Iara/harness/COMMIT_GUIDE.md Iara/harness/README.md Iara/scripts/validate-harness.py Iara/AGENTS.md
git -C .. commit -m "docs(harness): definir checkpoints de commit"
```

Substitua os caminhos de exemplo pela lista explicita de arquivos da mudanca. Evite `git add .` quando houver arquivos alheios no working tree. Para o Git compartilhado em `C:/projects`, limite-se estritamente a caminhos `Iara/...` listados na politica. Antes de confirmar, revise `git diff --cached` e `git status`.

## Limites de seguranca e historico

Nunca inclua `.env`, credenciais, bancos SQLite de runtime/teste, logs, caches, artefatos gerados, dados reais da empresa ou conteudo privado de conversas. Nao use `--amend`, force push ou reescrita de historico compartilhado sem pedido explicito.

O Harness compartilhado em `Iara/harness/` nao tem um repositorio Git proprio. No workspace atual, ele pertence ao Git externo em `C:/projects`; portanto, registre mudancas compartilhadas nesse historico com uma lista explicita de arquivos sob `Iara/harness/`, `Iara/scripts/`, `Iara/AGENTS.md` ou `Iara/README.md`. Nunca use `git add .` ou `git add Iara` nesse repositorio abrangente. As copias locais do Harness podem ser registradas nos commits de Backend e Frontend quando a mudanca pertence a esses componentes.

## Registro no handoff

Ao concluir ou transferir trabalho, informe para cada repositorio:

- commit criado ou mensagem sugerida, se ainda nao foi solicitado criar;
- arquivos incluidos;
- gates executados e seus resultados;
- IDs de commits relacionados entre Backend e Frontend;
- pendencias que nao entraram no commit.
