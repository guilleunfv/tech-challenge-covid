CREATE OR REPLACE TABLE `tech-chalenge-covid`.pnad_covid_processed.pnad_covid_analitica_consolidada AS
SELECT
    *,  -- Seleciona todas as colunas da tabela processada de Maio
    PARSE_DATE('%Y%m', CAST(Ano * 100 + Mes_cod AS STRING)) AS DataReferencia_Mes -- Cria uma coluna de data (primeiro dia do mês)
FROM `tech-chalenge-covid`.pnad_covid_processed.pessoas_052020_processed

UNION ALL  -- Empilha os resultados da query abaixo

SELECT
    *,  -- Seleciona todas as colunas da tabela processada de Julho
    PARSE_DATE('%Y%m', CAST(Ano * 100 + Mes_cod AS STRING)) AS DataReferencia_Mes
FROM `tech-chalenge-covid`.pnad_covid_processed.pessoas_072020_processed

UNION ALL  -- Empilha os resultados da query abaixo

SELECT
    *,  -- Seleciona todas as colunas da tabela processada de Setembro
    PARSE_DATE('%Y%m', CAST(Ano * 100 + Mes_cod AS STRING)) AS DataReferencia_Mes
FROM `tech-chalenge-covid`.pnad_covid_processed.pessoas_092020_processed;