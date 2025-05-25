-- =======================================================
-- Tabela dim_sexo
-- Descrição: Dimensão de Sexo (Masculino / Feminino)
-- =======================================================

CREATE TABLE IF NOT EXISTS `tech-chalenge-covid`.pnad_covid_dominios.dim_sexo (
    sexo_cod INT64 NOT NULL OPTIONS(description="Código do Sexo"),
    sexo_desc STRING OPTIONS(description="Descrição do Sexo")
);


INSERT INTO `tech-chalenge-covid`.pnad_covid_dominios.dim_sexo (sexo_cod, sexo_desc)
VALUES
    (1, 'Homem'),
    (2, 'Mulher');