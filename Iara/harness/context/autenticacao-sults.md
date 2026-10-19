# Autenticação SULTS da Iara

Atualizado em 16/10/2026. A Iara usa a biblioteca interna `libs/Sults` e o fluxo de login RPA já empregado no Faturas. A validação real no tenant depende de rede autorizada e de uma conta de homologação; os testes automatizados substituem o cliente por um falso sem tráfego externo.

## Fluxo implementado

1. Em produção, o formulário envia usuário e senha somente para `POST /api/v1/autenticacao/login` da Iara.
2. A rota valida os campos e chama `PortaAutenticacaoCorporativa.validar_credenciais` pelo adapter injetado no Backend.
3. Credenciais recusadas recebem uma resposta genérica. Falha de comunicação com o SULTS deve virar `ProvedorAutenticacaoIndisponivel`; nenhuma mensagem técnica ou credencial é devolvida ao navegador.
4. Após validação positiva, a Iara gera seu próprio token aleatório de sessão, armazena somente o hash no SQLite e entrega o token em cookie `HttpOnly`, `SameSite=Strict` e `Secure` fora do modo local.
5. O Frontend mantém o token CSRF somente em memória e envia o cabeçalho nas operações de escrita. O token SULTS nunca é usado como cookie Iara.
6. O identificador opaco que o adapter recebe é pseudonimizado com HMAC e `IARA_AUTH_IDENTITY_KEY` para derivar o UUID estável usado como proprietário do histórico. O identificador do SULTS não é persistido.
7. A sessão pode ser restaurada por `GET /api/v1/autenticacao/sessao` e revogada por `DELETE /api/v1/autenticacao/sessao`.

O acesso local em `localhost` continua automático, sintético e restrito à própria identidade de demonstração. A rota corporativa não é habilitada em `APP_ENV=development` e exige opt-in explícito `IARA_CORPORATE_AUTH_ENABLED=true` fora do modo local, além de `IARA_AUTH_IDENTITY_KEY` válido. O adapter usa o tenant HTTPS fixo do Faturas. O Backend limita oito tentativas por login pseudonimizado em quinze minutos, entre processos que compartilham o SQLite, antes de consultar o ERP. A borda precisa aplicar adicionalmente limite por origem no ambiente publicado.

O RPA confirma sucesso pelo status 200 do POST e pela presença dos tokens transitórios; o adapter apaga o retorno, os cookies e os atributos do cliente e fecha a conexão. A Iara deriva a identidade local do login confirmado e não armazena nem usa os tokens SULTS como sessão. Como a biblioteca não fornece um ID imutável da pessoa, logins alternativos para a mesma conta podem formar históricos locais distintos; a equipe deve validar esse comportamento na homologação.

## Teste local da tela e da sessão fake

O acesso sem login continua como comportamento padrão em `localhost`. Para exercitar o formulário antes da integração oficial, o Backend aceita um modo opt-in exclusivo de `APP_ENV=development`, protegido pela validação de loopback:

- Defina `IARA_DEV_AUTH_TEST_ENABLED=true`, `IARA_DEV_AUTH_TEST_USERNAME` e `IARA_DEV_AUTH_TEST_PASSWORD` apenas em `Backend/.env`.
- Abra `http://localhost:5173/conversas/nova?login=teste`.
- O formulário valida as credenciais apenas contra o adapter fake local, cria uma sessão sintética da demonstração e permite testar recusa de senha, cookie e sessão.
- Essa validação não acessa o SULTS, não prova que uma conta corporativa funciona e não permite consultar conversas de gestores.
- Remova ou desligue a flag para retornar à entrada automática usual. Fora de desenvolvimento, essa configuração não habilita a rota corporativa.

Não use senha corporativa real nesse teste. As credenciais sintéticas devem ser diferentes das contas do SULTS e permanecer fora do Git.

## Opções de integração

| Caminho | Como funciona | Vantagens | Custos e riscos | Recomendação |
| --- | --- | --- | --- | --- |
| Validar credenciais pelo Backend e emitir sessão Iara | O Backend usa a biblioteca SULTS do Faturas, valida a identidade e cria cookie próprio. | Sessão e autorização da Iara ficam sob controle do Backend; token SULTS não chega ao navegador. | Depende de acesso ao tenant, limites de login e disponibilidade do SULTS. | **Implementado**, pendente de validação real em homologação. |
| Receber token SULTS e validar no Backend | Um fluxo corporativo obtém o token e o Backend o valida antes de emitir sessão Iara. | Pode evitar reenviar senha se o ERP já oferece token delegado apropriado. | Exige saber emissor, audiência, assinatura/validação, expiração e revogação; não usar token sem contrato oficial. | Alternativa se o Líder Técnico confirmar um fluxo de token suportado. |
| SSO federado (OIDC/SAML) | O navegador é redirecionado ao provedor corporativo e a Iara recebe uma asserção/código validável no servidor. | Melhor alinhamento a SSO e políticas corporativas, sem senha local da Iara. | Depende de configuração e responsabilidade do Líder Técnico; maior trabalho de integração e callback. | Caminho futuro se o SULTS/empresa fornecer esse mecanismo. |

Os caminhos de token delegado e SSO permanecem alternativas futuras. A Iara usa a mesma biblioteca interna do Faturas, com o destino HTTPS fixo e sem copiar credenciais de outro produto.

## Dependências para ativar o SULTS

- Acesso de homologação autorizado ao tenant SULTS, conta de teste e validação de respostas reais de sucesso, recusa, conta desativada e indisponibilidade, sem imprimir credenciais ou resposta bruta.
- Confirmar com o Líder Técnico se o login canônico é suficiente como identidade estável ou se o ERP disponibiliza um ID imutável da pessoa.
- Configurar proteção por origem na borda e confirmar que o banco compartilhado entre réplicas suporta o limite persistido antes de ativar o login para gestores.
- Segredo forte `IARA_AUTH_IDENTITY_KEY`, igual entre réplicas e persistente entre reinícios/implantações. Gerar fora do código e manter no `.env` local ignorado pelo Git; em produção, DevOps injeta o segredo.
- Para gerar um valor local, use `python -c "import secrets; print(secrets.token_urlsafe(48))"` e guarde a saída somente em `Backend/.env`.
- A aplicação já registra limites por login no Backend sem guardar seu valor em claro. A borda ainda precisa limitar tentativas por origem; métricas de recusa agregadas não estão prontas.
- Critérios definidos pelo Líder Técnico para rotação da chave: mudá-la altera os UUIDs derivados e pode separar o histórico antigo da identidade nova.

## Arquivos principais

- Backend: `Backend/app/portas/autenticacao.py`, `Backend/app/adaptadores/autenticacao_corporativa.py` (factory), `Backend/app/adaptadores/autenticacao_sults.py`, `Backend/app/adaptadores/limitador_login.py`, `Backend/libs/Sults/`, `Backend/app/autenticacao.py`, `Backend/app/main.py`, `Backend/app/configuracao.py` e `Backend/sql/esquema.sql`.
- Frontend: `Frontend/src/api.ts`, `Frontend/src/funcionalidades/autenticacao/PaginaLogin.tsx` e `Frontend/src/funcionalidades/autenticacao/componentes/FormularioLogin/FormularioLogin.tsx`.
- Exemplo de produto: `C:\projects\Faturas_Front-end\src\features\autenticacao` e `src/features/operador/infrastructure/operadorApiHttp.ts`.

## Verificação de segurança desta integração

Referência consultada: [OWASP ASVS 5.0.0](https://owasp.org/projects/asvs), versão estável em 16/10/2026. O requisito `v5.0.0-6.1.1` orienta documentar limites contra força bruta: `limitador_login.py` usa oito tentativas por login em quinze minutos, retorna `429` e `Retry-After`, e os testes verificam a contagem compartilhada; a proteção por origem na borda ainda depende de DevOps. O requisito `v5.0.0-3.3.4` orienta manter o cookie de sessão inacessível ao JavaScript: `criar_sessao_corporativa` usa `HttpOnly`; o teste de rota verifica emissão da sessão Iara sem token SULTS. O requisito `v5.0.0-13.2.4` orienta limitar destinos externos: o adapter fixa o tenant HTTPS e o cliente copiado rejeita redirecionamento pós-login fora dele. Isso documenta controles específicos, não uma certificação ASVS.

O acesso real ao tenant, a validade da biblioteca frente a mudanças na página de login do SULTS, o comportamento de contas desativadas e a eventual unificação de CPF/email/login da mesma pessoa ainda exigem homologação com o Líder Técnico. A biblioteca possui licença interna: use e execute apenas na rede privada autorizada da empresa.
