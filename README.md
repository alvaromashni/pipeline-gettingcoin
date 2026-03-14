# Exchange Rate ELT Pipeline

Projeto de estudos desenvolvido para praticar conceitos de engenharia de dados, incluindo
consumo de APIs REST, modelagem de banco de dados relacional e construção de pipelines ELT
(Extract, Load, Transform).

O projeto extrai cotações de moedas (USD, EUR, BRL, GBP) da API pública Frankfurter,
armazena os dados brutos em um banco PostgreSQL utilizado como datalake simplificado,
e disponibiliza os dados processados por meio de uma API REST construida em Java com Spring Boot.

---

## Tecnologias utilizadas

- Python 3.11+ — extração e carga dos dados
- PostgreSQL — armazenamento (datalake)
- psycopg2 — conexao Python com PostgreSQL
- python-dotenv — gerenciamento de variaveis de ambiente
- APScheduler / schedule — agendamento da extração

---

## Arquitetura

```
[Frankfurter API] --> [extractor.py] --> [loader.py] --> [PostgreSQL]
                                                              |
                                                     [Spring Boot API]
                                                              |
                                                    [GET /rates/latest]
                                                    [GET /rates/summary]
                                                    [GET /rates/compare]
```

O fluxo segue o padrão ELT:

1. Extract — o script Python consome o endpoint da Frankfurter API buscando as cotacoes dos ultimos 7 dias
2. Load — os dados brutos são inseridos na tabela `raw.exchange_rates` no PostgreSQL sem transformacao
3. Transform — a API Java lê os dados do banco, aplica cálculos (média, variação, comparação) e os expõe via endpoints REST

---

## Estrutura do projeto

```
exchange-rate-elt/
|
|-- extractor/               # modulo Python de extracao e carga
|   |-- config.py            # configuracoes e variaveis de ambiente
|   |-- extractor.py         # chamadas a Frankfurter API
|   |-- loader.py            # insercao dos dados no PostgreSQL
|   |-- main.py              # orquestrador e agendamento
|   |-- requirements.txt
|
|-- api/                     # projeto Spring Boot
|   |-- src/
|   |-- pom.xml
|
|-- .env                     # variaveis de ambiente (nao commitado)
|-- .env.example             # modelo de variaveis (commitado sem valores)
|-- .gitignore
|-- README.md
```

---

## Configuracao do ambiente

### Pre-requisitos

- Python 3.11+
- Java 17+
- PostgreSQL rodando localmente ou via Docker
- Maven

### Variaveis de ambiente

Copie o arquivo de exemplo e preencha com seus dados:

```bash
cp .env.example .env
```

Conteudo do `.env`:

```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=datalake
DB_USER=postgres
DB_PASSWORD=sua_senha

API_BASE_URL=https://api.frankfurter.dev/v1
BASE_CURRENCY=USD
TARGET_CURRENCIES=EUR,BRL,GBP
DAYS_BACK=7
```

---

## Como executar

### Extracao (Python)

```bash
cd extractor
pip install -r requirements.txt
python main.py
```

O pipeline roda imediatamente ao iniciar e depois agenda uma execucao diaria a meia-noite.

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

---

## Conceitos praticados

- Consumo de API REST com Python
- Pipeline ELT (diferente de ETL — a transformação ocorre após a carga)
- Modelagem de banco de dados com schemas separados (raw / analytics)
- Idempotência em inserções com `ON CONFLICT DO NOTHING`
- Gerenciamento de credenciais com variáveis de ambiente
- Agendamento de tarefas com `schedule`
- API REST com Spring Boot e consultas ao PostgreSQL

---

## Observacoes

Este é um projeto de estudos. O objetivo é praticar o ciclo completo de um pipeline de dados
em escala reduzida, desde a extração de uma fonte externa até a exposição dos dados por uma API própria.
Nao é indicado para uso em produção sem revisão de segurança, tratamento de erros robusto e testes adequados.

A API Frankfurter é gratuita, de código aberto, e não requer autenticação.
Mais informações em: https://frankfurter.dev