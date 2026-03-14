# Exchange Rate ELT Pipeline

Projeto de estudos desenvolvido para praticar conceitos de engenharia de dados, incluindo
consumo de APIs REST, orquestracao de pipelines com Apache Airflow, modelagem de banco de
dados relacional e construcao de APIs REST.

O projeto extrai cotacoes de moedas (USD, EUR, BRL, GBP) da API publica Frankfurter,
armazena os dados brutos em um banco PostgreSQL utilizado como datalake simplificado,
e disponibiliza os dados processados por meio de uma API REST construida em Java com Spring Boot.

Todo o ambiente de infraestrutura roda via Docker Compose, incluindo o PostgreSQL e o Airflow.

---

## Tecnologias utilizadas

- Python 3.12 — extracao e carga dos dados
- Apache Airflow 2.9 — orquestracao do pipeline
- PostgreSQL 16 — armazenamento (datalake)
- Java 17 + Spring Boot — API de analise e consulta
- psycopg2 — conexao Python com PostgreSQL
- python-dotenv — gerenciamento de variaveis de ambiente
- Docker + Docker Compose — infraestrutura containerizada

---

## Arquitetura

```
[Frankfurter API]
       |
  [Airflow DAG]
       |
  [extract_rates]         # task Python: busca cotacoes dos ultimos 7 dias
       |
  [load_rates]            # task Python: insere dados no PostgreSQL
       |
  [PostgreSQL / datalake]
       |
  [Spring Boot API]
       |
  [GET /rates/latest]
  [GET /rates/summary]
  [GET /rates/compare]
```

O fluxo segue o padrao ELT:

1. Extract — o Airflow executa a task `extract_rates` que consome a Frankfurter API
2. Load — a task `load_rates` insere os dados brutos na tabela `raw.exchange_rates` sem transformacao
3. Transform — a API Java le os dados do banco, aplica calculos e os expoe via endpoints REST

O Airflow agenda a execucao automaticamente todos os dias as 06:00 UTC.

---

## Estrutura do projeto

```
exchange-rate-elt/
|
|-- dags/
|   |-- exchange_rate_dag.py     # DAG principal do Airflow
|
|-- extractor/                   # pacote Python de extracao e carga
|   |-- __init__.py              # expoe fetch_rates e load_rates para a DAG
|   |-- config.py                # configuracoes lidas das variaveis de ambiente
|   |-- extractor.py             # chamadas a Frankfurter API
|   |-- loader.py                # insercao dos dados no PostgreSQL
|   |-- requirements.txt
|
|-- scripts/
|   |-- init-db.sh               # cria o usuario e banco do Airflow no PostgreSQL
|
|-- api/                         # projeto Spring Boot (em desenvolvimento)
|   |-- src/
|   |-- pom.xml
|
|-- .env                         # variaveis de ambiente (nao commitado)
|-- .env.example                 # modelo de variaveis (commitado sem valores)
|-- .gitignore
|-- docker-compose.yml
|-- README.md
```

---

## Configuracao do ambiente

### Pre-requisitos

- Docker Desktop instalado e em execucao
- Java 17+ e Maven (apenas para o modulo da API)
- Git

### Variaveis de ambiente

Copie o arquivo de exemplo e preencha com seus dados:

```bash
cp .env.example .env
```

Conteudo do `.env`:

```
DB_HOST=postgres
DB_PORT=5432
DB_NAME=datalake
DB_USER=postgres
DB_PASSWORD=sua_senha

API_BASE_URL=https://api.frankfurter.dev/v1
BASE_CURRENCY=USD
TARGET_CURRENCIES=EUR,BRL,GBP
DAYS_BACK=7
```

Observacao: os valores `DB_HOST=postgres` e `DB_PORT=5432` sao para uso interno
dos containers Docker. Para conectar via cliente externo (DBeaver, TablePlus etc.),
use `localhost` e a porta mapeada no `docker-compose.yml` (por exemplo, `55433`).

---

## Como executar

### Subindo a infraestrutura

```bash
# 1. sobe o PostgreSQL e aguarda ficar healthy
docker-compose up -d postgres

# 2. inicializa o banco e cria o usuario do Airflow
docker-compose up airflow-init

# 3. aguarda o init terminar com "exited with code 0", depois sobe o Airflow
docker-compose up -d airflow-webserver airflow-scheduler
```

O painel do Airflow estara disponivel em `http://localhost:8080`.
Credenciais padrao: `admin` / `admin`.

### Executando o pipeline

1. Acessa `http://localhost:8080`
2. Localiza a DAG `exchange_rate_elt`
3. Ativa o toggle para habilitar a DAG
4. Clica no botao de play (Trigger DAG) para executar manualmente

O pipeline executa duas tasks em sequencia:

```
extract_rates  -->  load_rates
```

### API (Spring Boot)

```bash
cd api
mvn spring-boot:run
```

A API estara disponivel em `http://localhost:8080`.

---

## Endpoints da API

| Metodo | Endpoint | Descricao |
|--------|----------|-----------|
| GET | `/rates/latest` | Cotacao mais recente de cada moeda |
| GET | `/rates/summary?currency=USD` | Media, maxima e minima da semana |
| GET | `/rates/compare?from=USD&to=BRL` | Variacao percentual no periodo |

---

## Banco de dados

O PostgreSQL roda dentro do Docker com dois bancos separados:

- `airflow` — uso interno do Airflow (metadados, logs de execucao, historico de DAGs)
- `datalake` — dados do pipeline

### Schema `raw`

Armazena os dados exatamente como vieram da API, sem transformacao:

```sql
CREATE TABLE raw.exchange_rates (
    id              SERIAL PRIMARY KEY,
    date            DATE NOT NULL,
    base_currency   VARCHAR(3) NOT NULL,
    target_currency VARCHAR(3) NOT NULL,
    rate            NUMERIC(18, 6) NOT NULL,
    extracted_at    TIMESTAMP DEFAULT NOW(),
    UNIQUE (date, base_currency, target_currency)
);
```

A constraint `UNIQUE` garante idempotencia — rodar o pipeline mais de uma vez
no mesmo dia nao duplica os registros.

### Schema `analytics`

View com os dados preparados para consulta pela API:

```sql
CREATE VIEW analytics.rates_view AS
SELECT
    date,
    base_currency,
    target_currency,
    rate,
    AVG(rate) OVER (PARTITION BY target_currency) AS avg_rate,
    MAX(rate) OVER (PARTITION BY target_currency) AS max_rate,
    MIN(rate) OVER (PARTITION BY target_currency) AS min_rate
FROM raw.exchange_rates;
```

### Consultando os dados

Via terminal (sem cliente externo):

```bash
docker exec -it elt-pipeline-postgres-1 psql -U postgres -d datalake \
  -c "SELECT * FROM raw.exchange_rates ORDER BY date DESC LIMIT 10;"
```

Via DBeaver ou outro cliente SQL, conecte com:

```
Host:     localhost
Port:     55433        (porta mapeada no docker-compose.yml)
Database: datalake
User:     postgres
SSL:      disable
```

Na arvore de navegacao do DBeaver, expanda `Schemas > raw > Tables` para
visualizar a tabela `exchange_rates`.

---

## Conceitos praticados

- Consumo de API REST com Python
- Pipeline ELT (diferente de ETL — a transformacao ocorre apos a carga)
- Orquestracao de pipelines com Apache Airflow (DAGs, tasks, agendamento)
- Containerizacao com Docker e Docker Compose
- Comunicacao entre containers via rede interna do Docker
- Modelagem de banco de dados com schemas separados (raw / analytics)
- Idempotencia em insercoes com `ON CONFLICT DO NOTHING`
- Gerenciamento de credenciais com variaveis de ambiente
- Pacotes Python com imports relativos
- API REST com Spring Boot e consultas ao PostgreSQL

---

## Observacoes

Este e um projeto de estudos. O objetivo e praticar o ciclo completo de um pipeline de dados
em escala reduzida, desde a extracao de uma fonte externa ate a exposicao dos dados por uma API propria.
Nao e indicado para uso em producao sem revisao de seguranca, tratamento de erros robusto e testes adequados.

A API Frankfurter e gratuita, de codigo aberto, e nao requer autenticacao.
Mais informacoes em: https://frankfurter.dev