-- Criar a tabela dim_internado_hospital
CREATE TABLE IF NOT EXISTS `tech-chalenge-covid`.pnad_covid_dominios.dim_internado_hospital (
    internado_cod INT64 NOT NULL OPTIONS(description="Código para B005 - Internado ao procurar hospital"),
    internado_desc STRING OPTIONS(description="Descrição para B005 - Internado ao procurar hospital")
);

-- Inserir dados na dim_internado_hospital
INSERT INTO `tech-chalenge-covid`.pnad_covid_dominios.dim_internado_hospital (internado_cod, internado_desc)
VALUES
    (1, 'Sim, ficou internado'),
    (2, 'Não, não ficou internado'),
    (3, 'Não foi atendido'),
    (9, 'Ignorado');