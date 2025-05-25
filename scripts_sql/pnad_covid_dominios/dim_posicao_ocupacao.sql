-- =======================================================
-- Tabela dim_posicao_ocupacao
-- Descrição: Dimensão da Posição na Ocupação (PNAD C007)
-- =======================================================

-- Criação da tabela
CREATE TABLE IF NOT EXISTS `tech-chalenge-covid`.pnad_covid_dominios.dim_posicao_ocupacao (
    pos_ocup_cod INT64 NOT NULL OPTIONS(description="Código da Posição na Ocupação - PNAD C007"),
    pos_ocup_desc STRING OPTIONS(description="Descrição da Posição na Ocupação")
);

-- Inserção dos dados
INSERT INTO `tech-chalenge-covid`.pnad_covid_dominios.dim_posicao_ocupacao (pos_ocup_cod, pos_ocup_desc)
VALUES
    (1, 'Trabalhador doméstico (empregado doméstico, cuidados, babá)'),
    (2, 'Militar do exercito, marinha ou aeronáutica'),
    (3, 'Policial militar ou bombeiro militar'),
    (4, 'Empregado do setor privado'),
    (5, 'Empregado do setor público (inclusive empresas de economia mista)'),
    (6, 'Empregador'),
    (7, 'Conta própria'),
    (8, 'Trabalhador familiar não remunerado em ajuda a membro do domicílio ou parente'),
    (9, 'Estava fora do mercado de trabalho (fazia apenas afazeres domésticos, cuidados de pessoas ou produção para próprio consumo)');