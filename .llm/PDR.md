# PRD – Bolão da Copa 2026

## 1. Visão Geral

### Nome do Produto

Bolão da Copa 2026

### Objetivo

Desenvolver uma plataforma web para gerenciamento de um bolão da Copa do Mundo 2026, permitindo o cadastro de participantes, registro de palpites, cálculo automático de pontuação, classificação em tempo real, acompanhamento da premiação e visualização de estatísticas do campeonato.

O sistema substituirá o controle manual realizado atualmente através de planilhas e mensagens, centralizando todas as informações em uma única plataforma acessível por desktop e dispositivos móveis.

---

# 2. Contexto do Projeto

O bolão já está em andamento.

Atualmente já existem:

* Participantes cadastrados informalmente.
* Jogos da competição definidos.
* Palpites realizados para jogos já ocorridos.
* Resultados oficiais de partidas já encerradas.
* Ranking calculado manualmente.

A plataforma deverá permitir a migração desses dados históricos para continuidade do bolão sem perda de informações.

---

# 3. Objetivos do Produto

## Objetivos Principais

* Centralizar o gerenciamento do bolão.
* Automatizar a apuração de resultados.
* Automatizar o cálculo de pontuação.
* Eliminar controles manuais.
* Disponibilizar ranking atualizado em tempo real.
* Facilitar o acompanhamento da premiação.

## Objetivos Secundários

* Disponibilizar dashboards e estatísticas.
* Demonstrar boas práticas de engenharia de software.
* Utilizar arquitetura moderna baseada em nuvem.
* Servir como projeto de portfólio.

---

# 4. Arquitetura Tecnológica

## Frontend

* Streamlit

## Linguagem

* Python 3.12

## Banco de Dados

* PostgreSQL
* Supabase Free Tier

## Autenticação

* Supabase Auth

## Analytics

* Pandas
* Plotly

## Infraestrutura

* Docker
* Render

## Controle de Versão

* Git
* GitHub

---

# 5. Estrutura do Projeto

O projeto deverá possuir:

## Arquivos obrigatórios

* README.md
* requirements.txt
* Dockerfile
* docker-compose.yml
* .gitignore
* .env.example

## Configuração

Arquivo .env contendo:

* SUPABASE_URL
* SUPABASE_KEY
* SUPABASE_SERVICE_ROLE_KEY
* APP_ENV
* APP_NAME

## .gitignore

Ignorar:

* .env
* .venv
* **pycache**
* logs
* .streamlit/secrets.toml
* arquivos temporários
* artefatos de build

---

# 6. Perfis de Usuário

## Administrador

Permissões:

* Gerenciar participantes
* Importar arquivos CSV
* Gerenciar jogos
* Registrar resultados oficiais
* Corrigir dados históricos
* Recalcular ranking
* Consultar dashboards administrativos

## Participante

Permissões:

* Realizar palpites
* Consultar seus palpites
* Consultar ranking
* Visualizar dashboards
* Atualizar telefone

---

# 7. Cadastro de Usuários

Campos obrigatórios:

* Nome completo
* E-mail
* Telefone
* Senha

Validações:

* Nome completo obrigatório
* E-mail único
* Telefone único
* Senha obrigatória

Dados armazenados:

* id
* nome_completo
* email
* telefone
* perfil
* ativo
* created_at
* updated_at

---

# 8. Autenticação

Utilizar Supabase Auth.

Funcionalidades:

* Cadastro
* Login
* Logout
* Recuperação de senha
* Alteração de senha
* Persistência de sessão

---

# 9. Gestão de Jogos

Os jogos serão carregados inicialmente através de importação CSV realizada pelo administrador.

O sistema não deverá exigir cadastro manual individual dos jogos durante a configuração inicial.

Cada partida deverá possuir:

* id
* seleção_1
* seleção_2
* data
* horário
* grupo ou chave
* etapa da competição
* status

## Etapas possíveis

* Fase de Grupos
* Oitavas de Final
* Quartas de Final
* Semifinal
* Disputa de 3º Lugar
* Final

## Status possíveis

* Agendado
* Em andamento
* Finalizado

---

# 10. Importação Inicial dos Jogos

O administrador deverá conseguir importar toda a tabela oficial da Copa através de um único arquivo CSV.

Campos:

* seleção_1
* seleção_2
* data
* horário
* grupo
* etapa

Exemplo:

Brasil,Espanha,2026-06-12,16:00,A,Fase de Grupos

Argentina,França,2026-06-13,19:00,B,Fase de Grupos

Após a importação inicial, não será necessário cadastrar jogos manualmente.

---

# 11. Gestão de Resultados

Os resultados oficiais serão informados pelo administrador após cada partida.

Campos:

* gols_seleção_1
* gols_seleção_2

Ao salvar o resultado oficial o sistema deverá:

* Atualizar status para Finalizado.
* Recalcular pontuação.
* Atualizar ranking.
* Atualizar dashboards.
* Atualizar projeção de premiação.

---

# 12. Gestão de Palpites

Regras:

* Um palpite por participante por jogo.
* O participante não poderá alterar o palpite após o início da partida.
* O administrador poderá inserir ou corrigir palpites históricos.
* Registrar data e hora do palpite.

Campos:

* participante
* jogo
* gols_seleção_1
* gols_seleção_2
* data_aposta

---

# 13. Sistema de Pontuação

## Regras Oficiais

Acerto do vencedor:

* 1 ponto

Acerto do placar exato:

* 3 pontos

O placar exato não acumula pontos de vencedor.

## Exemplos

Resultado oficial:

Brasil 2 x 1 Espanha

Palpite:

Brasil 1 x 0 Espanha

Pontuação:

1 ponto

Palpite:

Brasil 2 x 1 Espanha

Pontuação:

3 pontos

Palpite:

Brasil 2 x 2 Espanha

Pontuação:

0 ponto

---

# 14. Ranking

O sistema deverá calcular automaticamente:

* Pontuação total
* Quantidade de placares exatos
* Quantidade de acertos de vencedor
* Posição geral

## Funcionalidade Administrativa

Botão:

Recalcular Ranking

Processo:

1. Ler resultados oficiais.
2. Ler palpites.
3. Aplicar regras de pontuação.
4. Atualizar classificação.
5. Atualizar posições.

---

# 15. Premiação

Valor de participação:

R$ 10,00 por participante.

Premiação:

* 1º Lugar → R$ 100,00
* 2º Lugar → R$ 30,00
* 3º Lugar → R$ 10,00

O sistema deverá exibir:

* Ranking atualizado.
* Premiação atual.
* Quantidade de participantes.
* Valor arrecadado.
* Valor distribuído.

---

# 16. Importação de Dados Históricos

Disponível apenas para administradores.

## Participantes

Importação CSV contendo:

* nome
* email
* telefone

## Palpites Históricos

Importação CSV contendo:

* participante
* jogo
* gols_seleção_1
* gols_seleção_2
* data_aposta

## Resultados Históricos

Importação CSV contendo:

* jogo
* gols_seleção_1
* gols_seleção_2

## Requisitos

* Validar duplicidades.
* Exibir erros encontrados.
* Exibir relatório de importação.
* Permitir reprocessamento.
* Recalcular ranking automaticamente após qualquer importação.

---

# 17. Dashboards e Analytics

## Dashboard Geral

* Ranking geral.
* Top 3 participantes.
* Premiação atual.
* Quantidade de participantes.
* Valor arrecadado.

## Dashboard de Participantes

* Evolução da pontuação.
* Acertos de vencedor.
* Placares exatos.
* Desempenho individual.

## Dashboard dos Jogos

* Jogos com maior quantidade de acertos.
* Jogos com menor quantidade de acertos.
* Distribuição dos palpites por partida.

---

# 18. Auditoria

Registrar:

* Importações realizadas.
* Alterações de resultados.
* Alterações de palpites.
* Reprocessamentos de ranking.

Campos:

* usuário
* ação
* data
* detalhe

---

# 19. Responsividade

A aplicação deverá ser totalmente responsiva para:

* Desktop
* Tablet
* Smartphone

Priorizar experiência mobile.

---

# 20. Critérios de Sucesso

O projeto será considerado concluído quando:

* Usuários conseguirem se cadastrar e autenticar.
* Jogos forem carregados via CSV.
* Participantes conseguirem registrar palpites.
* Administrador conseguir informar resultados.
* Ranking for atualizado automaticamente.
* Premiação for exibida corretamente.
* Dashboards estiverem operacionais.
* Aplicação estiver publicada no Render.
* Banco estiver hospedado no Supabase.
* Projeto possuir documentação completa.

---

# 21. Entregáveis

Antes da implementação apresentar:

1. Arquitetura da solução.
2. Diagrama de componentes.
3. Estrutura de diretórios.
4. Modelo ER.
5. Scripts SQL.
6. Estrutura do Supabase.
7. Estrutura do .env.
8. Estrutura do .gitignore.
9. Dockerfile.
10. Docker Compose.
11. Roadmap de desenvolvimento.

Somente após aprovação dessa etapa iniciar a implementação do código.
