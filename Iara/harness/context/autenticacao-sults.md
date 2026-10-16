# Esqueleto de autenticação SULTS

Atualizado em 16/10/2026. Este documento registra a fronteira implementada e as decisões técnicas ainda necessárias para conectar o ERP. O projeto Faturas serve como referência de fluxo, não como contrato de API do SULTS.

## Fluxo implementado

1. Em produção, o formulário envia usuário e senha somente para `POST /api/v1/autenticacao/login` da Iara.
2. A rota valida os campos e chama `PortaAutenticacaoCorporativa.validar_credenciais` pelo adapter injetado no Backend.
3. Credenciais recusadas recebem uma resposta genérica. Falha de comunicação com o SULTS deve virar `ProvedorAutenticacaoIndisponivel`; nenhuma mensagem técnica ou credencial é devolvida ao navegador.
4. Após validação positiva, a Iara gera seu próprio token aleatório de sessão, armazena somente o hash no SQLite e entrega o token em cookie `HttpOnly`, `SameSite=Strict` e `Secure` fora do modo local.
5. O Frontend mantém o token CSRF somente em memória e envia o cabeçalho nas operações de escrita. O token SULTS nunca é usado como cookie Iara.
6. O identificador opaco que o adapter recebe é pseudonimizado com HMAC e `IARA_AUTH_IDENTITY_KEY` para derivar o UUID estável usado como proprietário do histórico. O identificador do SULTS não é persistido.
7. A sessão pode ser restaurada por `GET /api/v1/autenticacao/sessao` e revogada por `DELETE /api/v1/autenticacao/sessao`.

O acesso local em `localhost` continua automático, sintético e restrito à própria identidade de demonstração. A rota corporativa não é habilitada em `APP_ENV=development` e exige opt-in explícito `IARA_CORPORATE_AUTH_ENABLED=true` fora do modo local. O adapter SULTS não está configurado; portanto, o fluxo corporativo responde como indisponível até receber uma implementação real, chave de pseudonimização e proteção contra abuso.

## Opções de integração

| Caminho | Como funciona | Vantagens | Custos e riscos | Recomendação |
| --- | --- | --- | --- | --- |
| Validar credenciais pelo Backend e emitir sessão Iara | O Backend encaminha credenciais ao mecanismo oficial do SULTS, valida a identidade e cria cookie próprio. | Replica o fluxo usado pelo Faturas; sessão e autorização da Iara ficam sob controle do Backend; token SULTS não chega ao navegador. | Depende do endpoint/RPA oficial, proteção contra abuso, timeout e disponibilidade do SULTS. | **Escolhido para o esqueleto atual**, condicionado à documentação do Líder Técnico. |
| Receber token SULTS e validar no Backend | Um fluxo corporativo obtém o token e o Backend o valida antes de emitir sessão Iara. | Pode evitar reenviar senha se o ERP já oferece token delegado apropriado. | Exige saber emissor, audiência, assinatura/validação, expiração e revogação; não usar token sem contrato oficial. | Alternativa se o Líder Técnico confirmar um fluxo de token suportado. |
| SSO federado (OIDC/SAML) | O navegador é redirecionado ao provedor corporativo e a Iara recebe uma asserção/código validável no servidor. | Melhor alinhamento a SSO e políticas corporativas, sem senha local da Iara. | Depende de configuração e responsabilidade do Líder Técnico; maior trabalho de integração e callback. | Caminho futuro se o SULTS/empresa fornecer esse mecanismo. |

Não escolher entre os caminhos 2 e 3 sem confirmação do Líder Técnico e documentação oficial. Não copiar URL, payload, cookies ou credenciais do Faturas: aquele repositório mostra apenas o contrato e a experiência já adotados naquele produto.

## Dependências para ativar o SULTS

- Endpoint e protocolo oficiais, incluindo se o fluxo será usuário/senha, token delegado ou SSO.
- Formato de sucesso e identidade estável a receber; não é necessário obter nome/e-mail se a UI não for exibi-los.
- Erros de credenciais recusadas, conta desativada, indisponibilidade, rate limiting e timeout.
- Endereço de ambiente de teste, método de autorização e requisitos de rede, fornecidos pelo Líder Técnico.
- Segredo forte `IARA_AUTH_IDENTITY_KEY`, igual entre réplicas e persistente entre reinícios/implantações. Gerar fora do código e manter no `.env` local ignorado pelo Git; em produção, DevOps injeta o segredo.
- Para gerar um valor local, use `python -c "import secrets; print(secrets.token_urlsafe(48))"` e guarde a saída somente em `Backend/.env`.
- Antes de ativar `IARA_CORPORATE_AUTH_ENABLED`, definir rate limiting de tentativas de login na borda e Backend, mais métricas de recusa sem registrar usuário/senha. A cota atual de conversas se aplica somente depois da sessão e não protege a rota de login.
- Critérios definidos pelo Líder Técnico para rotação da chave: mudá-la altera os UUIDs derivados e pode separar o histórico antigo da identidade nova.

## Arquivos principais

- Backend: `Backend/app/portas/autenticacao.py`, `Backend/app/adaptadores/autenticacao_corporativa.py` (factory/composição), `Backend/app/autenticacao.py`, `Backend/app/main.py`, `Backend/app/configuracao.py` e `Backend/app/persistencia.py`.
- Frontend: `Frontend/src/api.ts`, `Frontend/src/funcionalidades/autenticacao/PaginaLogin.tsx` e `Frontend/src/funcionalidades/autenticacao/componentes/FormularioLogin/FormularioLogin.tsx`.
- Exemplo de produto: `C:\projects\Faturas_Front-end\src\features\autenticacao` e `src/features/operador/infrastructure/operadorApiHttp.ts`.
