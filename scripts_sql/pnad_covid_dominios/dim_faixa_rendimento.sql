-- =======================================================
-- Tabela dim_faixa_rendimento
-- Descrição: Dimensão da Faixa de Rendimento (PNAD C01011)
-- Alteração: Código como STRING ('00', '01', ...) em vez de INT64
-- =======================================================

-- Criação da tabela
CREATE TABLE IF NOT EXISTS `tech-chalenge-covid`.pnad_covid_dominios.dim_faixa_rendimento (
    faixa_rend_cod STRING NOT NULL OPTIONS(description="Código da Faixa de Rendimento (como string '00'-'09') - PNAD C01011"),
    faixa_rend_desc STRING OPTIONS(description="Descrição da Faixa de Rendimento")
);

-- Inserção dos dados
INSERT INTO `tech-chalenge-covid`.pnad_covid_dominios.dim_faixa_rendimento (faixa_rend_cod, faixa_rend_desc)
VALUES
    ('00', '0 - 100'),
    ('01', '101 - 300'),
    ('02', '301 - 600'),
    ('03', '601 - 800'),
    ('04', '801 - 1.600'),
    ('05', '1.601 - 3.000'),
    ('06', '3.001 - 10.000'),
    ('07', '10.001 - 50.000'),
    ('08', '50.001 - 100.000'),
    ('09', 'Mais de 100.000');