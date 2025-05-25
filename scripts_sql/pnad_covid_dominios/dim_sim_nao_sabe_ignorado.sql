-- =======================================================
-- Tabela dim_sim_nao_sabe_ignorado
-- Descrição: Respostas binárias com opções de "não sabe" e "ignorado"
-- =======================================================

-- Criar a tabela dim_sim_nao_sabe_ignorado
CREATE TABLE IF NOT EXISTS `tech-chalenge-covid`.pnad_covid_dominios.dim_sim_nao_sabe_ignorado (
    resposta_cod INT64 NOT NULL OPTIONS(description="Código da Resposta Genérica Sim/Não/Não Sabe/Ignorado"),
    resposta_desc STRING OPTIONS(description="Descrição da Resposta Genérica")
);

-- Inserir dados na dim_sim_nao_sabe_ignorado
INSERT INTO `tech-chalenge-covid`.pnad_covid_dominios.dim_sim_nao_sabe_ignorado (resposta_cod, resposta_desc)
VALUES
    (1, 'Sim'),
    (2, 'Não'),
    (3, 'Não sabe'),
    (9, 'Ignorado');