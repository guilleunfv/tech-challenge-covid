-- =======================================================
-- Tabela dim_cor_raca
-- Descrição: Dimensão de Cor/Raça
-- =======================================================

-- Criar a tabela dim_cor_raca
CREATE TABLE IF NOT EXISTS `tech-chalenge-covid`.pnad_covid_dominios.dim_cor_raca (
    cor_raca_cod INT64 NOT NULL OPTIONS(description="Código da Cor ou Raça"),
    cor_raca_desc STRING OPTIONS(description="Descrição da Cor ou Raça")
);

-- Inserir dados na dim_cor_raca
INSERT INTO `tech-chalenge-covid`.pnad_covid_dominios.dim_cor_raca (cor_raca_cod, cor_raca_desc)
VALUES
    (1, 'Branca'),
    (2, 'Preta'),
    (3, 'Amarela'),
    (4, 'Parda'),
    (5, 'Indígena'),
    (9, 'Ignorado');