# Copa Insights — Bolão da Copa do Mundo 2026

Aplicação web de bolão e analytics para a Copa do Mundo 2026. Participantes
registram palpites para os jogos, a pontuação é calculada automaticamente
quando os resultados oficiais são lançados, e dashboards mostram ranking e
estatísticas do bolão.

A especificação completa do produto está em [`.llm/PDR.md`](.llm/PDR.md).

## Arquitetura

App único em **Streamlit** que conversa diretamente com o **Supabase**
(Auth + Postgres + Row Level Security), sem backend separado:

```
app_pages/   → UI (Streamlit), uma página por tela
services/    → regras de negócio (validações, orquestração)
repositories/→ acesso a dados via supabase-py
core/        → configuração (.env) e constantes/enums
supabase/migrations/ → histórico versionado do schema SQL
```

- **Autenticação**: Supabase Auth (cadastro, login, logout, recuperação de
  senha). O JWT do usuário é usado em todas as queries, então o Postgres
  aplica RLS automaticamente por usuário.
- **Pontuação**: calculada e persistida por funções/triggers no Postgres
  quando um jogo é marcado como "Finalizado" (acerto do vencedor = 1 ponto,
  placar exato = 3 pontos).
- **Perfis**: `administrador` e `participante`. A autorização nas policies
  de RLS usa `auth.jwt() -> 'app_metadata' ->> 'perfil'` (nunca
  `user_metadata`), exposta via a função `public.is_admin()`.

## Pré-requisitos

- Python 3.12
- Conta/projeto no [Supabase](https://supabase.com)
- Docker + Docker Compose (opcional, para rodar containerizado)

## Configuração local

1. Crie e ative um ambiente virtual:

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   ```

2. Instale as dependências:

   ```bash
   pip install -r requirements.txt
   ```

3. Copie `.env.example` para `.env` e preencha os valores:

   ```bash
   cp .env.example .env
   ```

   | Variável | Descrição |
   |---|---|
   | `SUPABASE_URL` | URL do projeto Supabase (Project Settings → API) |
   | `SUPABASE_KEY` | Chave **publishable/anon** — usada nas operações normais, com RLS aplicado |
   | `SUPABASE_SERVICE_ROLE_KEY` | Chave **service_role** — usada apenas em fluxos administrativos (importação histórica, promoção de admin). Nunca é enviada ao navegador. Pode ficar vazia até as fases administrativas serem implementadas |
   | `APP_ENV` | `development` ou `production` |
   | `APP_NAME` | Nome exibido no app |
   | `APP_URL` | URL base do app (ex.: `http://localhost:8501` em dev, URL pública em produção). Usada como `redirect_to` nos e-mails de confirmação de cadastro e recuperação de senha do Supabase Auth |

4. No Supabase Dashboard, vá em **Authentication → URL Configuration** e
   adicione o valor de `APP_URL` (com `/**` ao final, ex.:
   `http://localhost:8501/**`) em **Redirect URLs**. Sem isso, os links de
   confirmação de cadastro e de recuperação de senha enviados por e-mail são
   rejeitados pelo Supabase. Repita esse passo com a URL de produção quando
   fizer o deploy.

5. Rode o app:

   ```bash
   streamlit run streamlit_app.py
   ```

   Acesse em [http://localhost:8501](http://localhost:8501).

   > **Nota (Windows/redes corporativas)**: se a inspeção de TLS do
   > antivírus/proxy corporativo causar erros de
   > `SSLCertVerificationError: unable to get local issuer certificate` ao
   > falar com o Supabase, o app já usa o pacote `truststore` para validar
   > certificados TLS com o repositório de certificados do sistema
   > operacional em vez do bundle do `certifi` — não é necessário nenhum
   > passo extra, basta `pip install -r requirements.txt`.

## Promovendo o primeiro administrador

As áreas em **Admin** (gestão de jogos, resultados, usuários etc.) só
aparecem para usuários com `perfil = administrador`. Após cadastrar
normalmente o usuário que será o administrador, promova-o com:

```bash
python scripts/bootstrap_admin.py usuario@example.com
```

Esse script usa a `SUPABASE_SERVICE_ROLE_KEY` (precisa estar configurada no
`.env`) para atualizar `app_metadata.perfil` no Supabase Auth — usado pelas
políticas de RLS — e o campo `perfil` em `profiles`, usado pela navegação do
app.

## Rodando com Docker

```bash
docker compose up --build
```

Isso constrói a imagem (Python 3.12-slim), instala as dependências e expõe o
app em [http://localhost:8501](http://localhost:8501). O arquivo `.env` é
carregado via `env_file` no `docker-compose.yml`. Não há serviço de banco no
compose — o Postgres é o do Supabase (cloud).

## Deploy no Render

A aplicação é publicada como um **Web Service Docker** no
[Render](https://render.com), usando o [`Dockerfile`](Dockerfile) da raiz. O
banco de dados continua sendo o Supabase — não há serviço de banco no Render.
O container lê a porta da variável `PORT` (definida automaticamente pelo
Render) e expõe `/_stcore/health` para o health check. Em produção, o app é
acessado pelo domínio próprio `www.mestredospalpites.com.br` e é exibido como
"Mestre dos Palpites" (`APP_NAME`).

### Opção 1 — Blueprint (`render.yaml`)

1. No Render, **New +** → **Blueprint** e selecione este repositório. O
   Render lê o [`render.yaml`](render.yaml) e cria o Web Service
   `mestredospalpites` automaticamente (runtime Docker, plano Free, health
   check `/_stcore/health`, `APP_NAME=Mestre dos Palpites` e
   `APP_URL=https://www.mestredospalpites.com.br`).
2. Preencha as variáveis marcadas como obrigatórias no dashboard
   (`SUPABASE_URL`, `SUPABASE_KEY`, `SUPABASE_SERVICE_ROLE_KEY`) — ver a
   tabela de variáveis em [Configuração local](#configuração-local).
3. Configure o domínio próprio (ver "Domínio próprio" abaixo). Até lá, o
   serviço também responde em `https://mestredospalpites.onrender.com`.

### Opção 2 — Web Service manual

1. **New +** → **Web Service** → conecte este repositório.
2. **Name**: `mestredospalpites`.
3. **Runtime**: Docker.
4. **Plan**: Free (ou superior).
5. **Health Check Path**: `/_stcore/health`.
6. Configure as variáveis de ambiente da tabela em
   [Configuração local](#configuração-local), com `APP_ENV=production`,
   `APP_NAME=Mestre dos Palpites` e `APP_URL=https://www.mestredospalpites.com.br`.

### Domínio próprio (mestredospalpites.com.br)

O domínio canônico é `www.mestredospalpites.com.br`, com o domínio raiz
(`mestredospalpites.com.br`) redirecionando para ele:

1. No serviço `mestredospalpites`, vá em **Settings → Custom Domains** →
   **Add Custom Domain**.
2. Adicione `www.mestredospalpites.com.br` — o Render mostra um registro
   **CNAME** para criar no provedor de DNS do domínio, apontando para o host
   `*.onrender.com` do serviço.
3. Adicione também `mestredospalpites.com.br` (raiz) — como domínios raiz não
   aceitam CNAME, o Render indica um registro **ALIAS/ANAME** (ou **A**,
   dependendo do provedor de DNS).
4. Na própria página de Custom Domains, marque `www.mestredospalpites.com.br`
   como domínio primário e configure `mestredospalpites.com.br` para
   redirecionar para ele.
5. A propagação do DNS pode levar de minutos a algumas horas; o Render valida
   os registros e emite o certificado TLS (Let's Encrypt) automaticamente.

### Pós-deploy: redirect URLs no Supabase

Repita o passo 4 de [Configuração local](#configuração-local) com a URL de
produção: no Supabase Dashboard, **Authentication → URL Configuration →
Redirect URLs**, adicione `https://www.mestredospalpites.com.br/**`. Sem isso,
os links de confirmação de cadastro e recuperação de senha enviados por e-mail
em produção são rejeitados.

> **Plano Free do Render**: o serviço "dorme" após um período de
> inatividade; o primeiro acesso após esse período pode levar cerca de 1
> minuto para responder (cold start).

## Banco de dados (Supabase)

O schema (tabelas, views, funções de pontuação, triggers e políticas de RLS)
está versionado em [`supabase/migrations/`](supabase/migrations/). Para
aplicar em um novo projeto Supabase, execute o conteúdo do arquivo de
migration mais recente via SQL Editor, MCP `execute_sql` ou
`supabase db query`.

Tabelas principais:

- `profiles` — extensão de `auth.users` (nome, e-mail, telefone, perfil, status)
- `matches` — jogos (seleções, data/hora, etapa, status, placar oficial)
- `predictions` — palpites por usuário/jogo, com pontuação calculada
- `audit_log` — trilha de alterações administrativas

Views de leitura para dashboards: `v_ranking`, `v_match_prediction_distribution`,
`v_match_accuracy`.

## Status do projeto

Em desenvolvimento. Roadmap completo no plano de implementação. Fases
concluídas: scaffolding do projeto, schema inicial do banco, autenticação
(cadastro, login, logout, recuperação de senha, sessão e perfil), gestão de
jogos (importação CSV inicial e listagem, área `Admin → Jogos`), palpites
(participante registra/edita palpites em jogos ainda não iniciados, vê
histórico de jogos encerrados com placar oficial e pontuação, área
`Meus palpites`), resultados oficiais (admin lança o placar de um jogo, que
é marcado como Finalizado e tem a pontuação dos palpites recalculada
automaticamente por trigger no banco, área `Admin → Resultados`) e
classificação (ranking geral via `v_ranking`, com posição/pontos/placares
exatos/acertos de vencedor, e premiação — quantidade de participantes, valor
arrecadado e distribuído, área `Classificação`), dashboards com Pandas e
Plotly (área `Dashboards`): visão **Geral** com ranking, top 3 e premiação
atual; **Meu desempenho** com posição, pontos, placares exatos, acertos de
vencedor e evolução da pontuação ao longo dos jogos; e **Jogos** com a taxa
de acerto por partida (`v_match_accuracy`) e a distribuição dos placares
apostados por jogo (`v_match_prediction_distribution`); e importação
histórica + correção administrativa + auditoria (PDR §16/§14/§18, área
`Admin → Importação histórica`, `Admin → Correção histórica` e
`Admin → Auditoria`): importação via CSV de participantes (cria usuários no
Supabase Auth com senha temporária — requer `SUPABASE_SERVICE_ROLE_KEY`),
palpites e resultados históricos (com recálculo automático do ranking),
correção manual de palpites de qualquer participante em qualquer jogo
(mesmo já iniciado/finalizado, com recálculo imediato da pontuação), botão
"Recalcular ranking" e trilha de auditoria de todas essas ações; e identidade
visual final e responsividade (PDR §19, tema verde/branco inspirado no
Lance!): bandeiras dos países (`core/flags.py`, emoji por código ISO 3166-1)
exibidas em confrontos nas páginas de jogos, palpites, dashboards e nas
prévias de importação; indicadores visuais de status do jogo (⚪ Agendado /
🟡 Em andamento / 🟢 Finalizado); medalhas (🥇🥈🥉) e destaque da própria linha
na tabela de classificação; branding da sidebar (nome e ícone do app acima
dos dados do usuário logado); contêineres com borda em "Meus palpites"; linhas
de KPI (`st.container(horizontal=True)` com `st.metric(..., border=True)`,
que se reorganizam em telas estreitas) em `Classificação`, `Dashboard geral`
e `Meu desempenho`; e a nova página `Admin → Usuários`, que lista
participantes/administradores, permite ativar/desativar participantes e
promover/rebaixar administradores (via `service_role key`, com aviso sobre a
necessidade de renovação do token de sessão para o usuário afetado); e
apelido (nickname) do usuário: novo campo obrigatório e único em
`profiles`, coletado no cadastro junto do nome completo — o nome completo
fica restrito ao cadastro, enquanto o apelido (mais curto) é o nome de
exibição em toda a aplicação (sidebar, `Meu perfil`, `Classificação` e
`Dashboard geral`/Top 3), com `v_ranking` atualizada para expor `nickname`; e
preparação para deploy no Render (PDR §20): `Dockerfile` ajustado para ler a
porta de `$PORT` (definida pelo Render) com fallback para 8501 e healthcheck
em Python (a imagem `python:3.12-slim` não inclui `curl`), `.dockerignore`
para reduzir o contexto de build, `render.yaml` (Blueprint de Web Service
Docker, plano Free, health check em `/_stcore/health`) e a seção
"Deploy no Render" no README com o passo a passo (Blueprint ou Web Service
manual, variáveis de ambiente e atualização das redirect URLs do Supabase
Auth em produção). A publicação em si requer conectar este repositório a uma
conta no Render — não realizada neste ambiente.
