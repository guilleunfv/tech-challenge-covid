CREATE OR REPLACE TABLE `tech-chalenge-covid`.pnad_covid_processed.pessoas_072020_processed AS
SELECT
    -- Identificadores e Pesos
    raw.Ano,
    raw.V1013 AS Mes_cod,
    CAST(raw.V1032 AS FLOAT64) AS Peso_Amostral,

    -- Variáveis da PNAD Selecionadas e Decodificadas
    -- População
    CAST(raw.UF AS INT64) AS UF_cod,
    COALESCE(dim_uf.uf_desc, 'Não Informado') AS uf_desc,
    CAST(raw.A002 AS INT64) AS Idade,
    CAST(raw.A003 AS INT64) AS Sexo_cod,
    COALESCE(dim_sexo.sexo_desc, 'Não Informado') AS sexo_desc,
    CAST(raw.A004 AS INT64) AS CorRaca_cod,
    COALESCE(dim_cor_raca.cor_raca_desc, 'Não Informado') AS cor_raca_desc,
    CAST(raw.A005 AS INT64) AS Escolaridade_cod,
    COALESCE(dim_escolaridade.escolaridade_desc, 'Não Informado') AS escolaridade_desc,

    -- Clínica
    CAST(raw.B0011 AS INT64) AS Febre_cod,
    COALESCE(dim_febre.resposta_desc, 'Não Informado') AS Febre_desc,
    CAST(raw.B0012 AS INT64) AS Tosse_cod,
    COALESCE(dim_tosse.resposta_desc, 'Não Informado') AS Tosse_desc,
    CAST(raw.B0014 AS INT64) AS DificuldadeRespirar_cod,
    COALESCE(dim_dif_resp.resposta_desc, 'Não Informado') AS DificuldadeRespirar_desc,
    CAST(raw.B00111 AS INT64) AS PerdaOlfatoPaladar_cod,
    COALESCE(dim_olf_pal.resposta_desc, 'Não Informado') AS PerdaOlfatoPaladar_desc,
    CAST(raw.B002 AS INT64) AS ProcurouAtendimento_cod,
    COALESCE(dim_proc_atend.resposta_desc, 'Não Informado') AS ProcurouAtendimento_desc,
    CAST(raw.B005 AS INT64) AS InternadoHospital_cod,
    COALESCE(dim_internado.internado_desc, 'Não Informado') AS InternadoHospital_desc,
    CAST(raw.B007 AS INT64) AS PlanoSaude_cod,
    COALESCE(dim_plano_saude.resposta_desc, 'Não Informado') AS PlanoSaude_desc,

    -- Econômica
    CAST(raw.C001 AS INT64) AS Trabalhou_cod,
    COALESCE(dim_trabalhou.resposta_desc, 'Não Informado') AS Trabalhou_desc,
    CAST(raw.C002 AS INT64) AS AfastadoTrabalho_cod,
    COALESCE(dim_afast_trab.resposta_desc, 'Não Informado') AS AfastadoTrabalho_desc,
    CAST(raw.C007 AS INT64) AS PosicaoOcupacao_cod,
    COALESCE(dim_pos_ocup.pos_ocup_desc, 'Não Informado') AS PosicaoOcupacao_desc,
    FORMAT("%02d", CAST(raw.C01011 AS INT64)) AS FaixaRendimento_cod_str,
    COALESCE(dim_faixa_rend.faixa_rend_desc, 'Não Informado') AS FaixaRendimento_desc,
    CAST(raw.C01012 AS NUMERIC) AS RendimentoHabitual_Valor,
    CAST(raw.D0051 AS INT64) AS AuxilioEmergencial_cod,
    COALESCE(dim_aux_emerg.resposta_desc, 'Não Informado') AS AuxilioEmergencial_desc

FROM
    `tech-chalenge-covid`.pnad_covid_raw.pessoas_072020_raw AS raw -- << MUDANÇA AQUI
-- JOINs com as tabelas de domínio (permanecem os mesmos)
LEFT JOIN `tech-chalenge-covid`.pnad_covid_dominios.dim_uf ON CAST(raw.UF AS INT64) = dim_uf.uf_cod
LEFT JOIN `tech-chalenge-covid`.pnad_covid_dominios.dim_sexo ON CAST(raw.A003 AS INT64) = dim_sexo.sexo_cod
LEFT JOIN `tech-chalenge-covid`.pnad_covid_dominios.dim_cor_raca ON CAST(raw.A004 AS INT64) = dim_cor_raca.cor_raca_cod
LEFT JOIN `tech-chalenge-covid`.pnad_covid_dominios.dim_escolaridade ON CAST(raw.A005 AS INT64) = dim_escolaridade.escolaridade_cod
LEFT JOIN `tech-chalenge-covid`.pnad_covid_dominios.dim_sim_nao_sabe_ignorado AS dim_febre ON CAST(raw.B0011 AS INT64) = dim_febre.resposta_cod
LEFT JOIN `tech-chalenge-covid`.pnad_covid_dominios.dim_sim_nao_sabe_ignorado AS dim_tosse ON CAST(raw.B0012 AS INT64) = dim_tosse.resposta_cod
LEFT JOIN `tech-chalenge-covid`.pnad_covid_dominios.dim_sim_nao_sabe_ignorado AS dim_dif_resp ON CAST(raw.B0014 AS INT64) = dim_dif_resp.resposta_cod
LEFT JOIN `tech-chalenge-covid`.pnad_covid_dominios.dim_sim_nao_sabe_ignorado AS dim_olf_pal ON CAST(raw.B00111 AS INT64) = dim_olf_pal.resposta_cod
LEFT JOIN `tech-chalenge-covid`.pnad_covid_dominios.dim_sim_nao_sabe_ignorado AS dim_proc_atend ON CAST(raw.B002 AS INT64) = dim_proc_atend.resposta_cod
LEFT JOIN `tech-chalenge-covid`.pnad_covid_dominios.dim_internado_hospital AS dim_internado ON CAST(raw.B005 AS INT64) = dim_internado.internado_cod
LEFT JOIN `tech-chalenge-covid`.pnad_covid_dominios.dim_sim_nao_sabe_ignorado AS dim_plano_saude ON CAST(raw.B007 AS INT64) = dim_plano_saude.resposta_cod
LEFT JOIN `tech-chalenge-covid`.pnad_covid_dominios.dim_sim_nao_sabe_ignorado AS dim_trabalhou ON CAST(raw.C001 AS INT64) = dim_trabalhou.resposta_cod
LEFT JOIN `tech-chalenge-covid`.pnad_covid_dominios.dim_sim_nao_sabe_ignorado AS dim_afast_trab ON CAST(raw.C002 AS INT64) = dim_afast_trab.resposta_cod
LEFT JOIN `tech-chalenge-covid`.pnad_covid_dominios.dim_posicao_ocupacao AS dim_pos_ocup ON CAST(raw.C007 AS INT64) = dim_pos_ocup.pos_ocup_cod
LEFT JOIN `tech-chalenge-covid`.pnad_covid_dominios.dim_faixa_rendimento AS dim_faixa_rend ON FORMAT("%02d", CAST(raw.C01011 AS INT64)) = dim_faixa_rend.faixa_rend_cod
LEFT JOIN `tech-chalenge-covid`.pnad_covid_dominios.dim_sim_nao_sabe_ignorado AS dim_aux_emerg ON CAST(raw.D0051 AS INT64) = dim_aux_emerg.resposta_cod
;