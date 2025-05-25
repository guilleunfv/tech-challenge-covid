-- =======================================================
-- Tabela dim_escolaridade
-- Descrição: Níveis de escolaridade
-- =======================================================

-- Criar a tabela dim_escolaridade
CREATE TABLE IF NOT EXISTS `tech-chalenge-covid`.pnad_covid_dominios.dim_escolaridade (
    escolaridade_cod INT64 NOT NULL OPTIONS(description="Código da Escolaridade"),
    escolaridade_desc STRING OPTIONS(description="Descrição da Escolaridade")
);

-- Inserir dados na dim_escolaridade
INSERT INTO `tech-chalenge-covid`.pnad_covid_dominios.dim_escolaridade (escolaridade_cod, escolaridade_desc)
VALUES
    (1, 'Sem instrução'),
    (2, 'Fundamental incompleto'),
    (3, 'Fundamental completa'),
    (4, 'Médio incompleto'),
    (5, 'Médio completo'),
    (6, 'Superior incompleto'),
    (7, 'Superior completo'),
    (8, 'Pós-graduação, mestrado ou doutorado');