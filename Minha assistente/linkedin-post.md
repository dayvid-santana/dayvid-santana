# Construindo uma assistente de IA pessoal para o meu dia a dia de dev

Nas últimas semanas venho construindo, nas horas vagas, uma assistente de IA pessoal para me
ajudar no trabalho de desenvolvimento — não um chatbot genérico, mas algo que realmente conhece
os meus repositórios e pode operar sobre eles.

Compartilho aqui algumas decisões de arquitetura e aprendizados, porque acho que dizem mais sobre
o processo do que o resultado final.

## O que ela faz hoje

**Conversa sobre o código de verdade.** Nada de respostas genéricas: cada resposta vem com
citações estruturadas — arquivo, linhas, commit — apontando exatamente de onde a informação saiu.
Se não há evidência no repositório, ela diz isso, em vez de inventar.

**Roda agentes que analisam e, quando autorizado, escrevem código.** Um catálogo de mais de vinte
agentes especializados (revisão de diff, segurança, banco de dados, contratos de API, performance,
padrões de projeto...) faz análises de leitura sob demanda. Para tarefas que alteram arquivos, o
fluxo é: gerar um plano → decisão humana explícita quando a mudança é estrutural (autenticação,
schema, contrato público) → só então executar, sempre num branch e worktree isolados, nunca no
código que já está aberto. Nada é mesclado sem eu revisar o diff.

**Conversa por voz, sem depender de nenhum serviço externo novo.** Em vez de montar um pipeline de
áudio inteiro (gravação, upload, transcrição em servidor, síntese), usei as APIs de fala nativas
do próprio navegador. Reconhecimento e síntese de voz rodam no cliente; o texto reconhecido segue
pelo mesmo caminho que uma mensagem digitada. Zero dependência nova, zero chave de API adicional.

## Decisões que valeram a pena

- **Local-first por padrão.** A API que orquestra os agentes só escuta em loopback, sem
  autenticação — porque não deveria sair da máquina. Segurança por design, não por configuração.
- **Nunca escrever sem confirmação explícita.** Toda ação que pode alterar arquivos passa por uma
  confirmação visível na interface antes de rodar — não existe "atalho" para pular essa etapa.
- **Separar análise de execução.** Um agente pode ler, analisar e sugerir livremente; escrever é
  um caminho à parte, com aprovação e isolamento de verdade (branch + worktree próprios).
- **Provider de IA plugável.** O motor de linguagem por trás da análise é intercambiável — hoje
  uso um agente de codificação já autenticado na máquina, sem precisar gerenciar mais uma chave de
  API.

## Um aprendizado técnico interessante

Um dos agentes de IA que uso no backend recebe o contexto selecionado dentro de um sandbox de
arquivos, com uma instrução em texto do tipo "leia este arquivo e responda". Em parte das
execuções, o próprio modelo respondia como se não tivesse acesso ao arquivo — mesmo ele estando
ali, disponível para leitura. Não é um bug de código: é o comportamento não determinístico de um
agente que decide, por conta própria, se vai ou não acionar uma ferramenta de leitura. Um lembrete
de que orquestrar múltiplos agentes de IA exige tratar cada resposta como potencialmente
inconsistente, não como uma chamada de função determinística.

## Por que compartilhar isso

Não é sobre a ferramenta em si, mas sobre um jeito de pensar: dar autonomia real a agentes de IA
sobre código de produção só faz sentido com camadas explícitas de segurança — aprovação humana,
isolamento de execução, e nenhuma ação destrutiva sem confirmação visível. É um equilíbrio que
ainda estou ajustando, e a cada iteração aprendo algo novo sobre onde a automação ajuda de verdade
e onde ela só desloca o risco para outro lugar.

---

*Projeto pessoal, em construção contínua. Se você está pensando em dar mais autonomia para
agentes de IA no seu próprio fluxo de trabalho, adoraria trocar ideias sobre os trade-offs.*
