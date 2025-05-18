"""Utilidades de **limpeza** dos microdados **PNAD‑COVID 19**.

Uso rápido a partir da raiz do repositório:

    python -m src.clean_pnad data/raw/PNAD_COVID_052020.csv \
           data/cleaned/PNAD_COVID_052020_clean.csv

O script executa:
1. Leitura do CSV bruto (separador ",", codificação UTF‑8).
2. Seleção das 20 variáveis definidas no Tech Challenge.
3. Tratamento de valores ausentes + recodificação (Sim/Não, resultado de teste).
4. Gravação do CSV limpo no caminho informado.
"""

from __future__ import annotations
import argparse
import os
import pandas as pd

# ---------- Configurações globais ----------
COLS_INTERES = [
    "UF", "A001", "A003",                    # estado, sexo, idade
    "B0011", "B0012", "B0013", "B0014", "B0015", "B0016", "B0017", "B0018", "B0019",  # sintomas
    "B002", "C007", "C008",                  # atendimento e testagem
    "D0011", "D0021", "D0031",               # emprego e renda
    "F001", "F006",                           # auxílio e home‑office
]

# Nomes legíveis para as colunas
MAP_RENOMEIA = {
    "UF": "estado",
    "A001": "sexo",
    "A003": "idade",
    "B0011": "sintoma_febre",
    "B0012": "sintoma_tosse",
    "B0013": "sintoma_garganta",
    "B0014": "sintoma_falta_ar",
    "B0015": "sintoma_cabeca",
    "B0016": "sintoma_peito",
    "B0017": "sintoma_nausea",
    "B0018": "sintoma_diarreia",
    "B0019": "sintoma_olfato_paladar",
    "B002": "procurou_atendimento",
    "C007": "fez_teste",
    "C008": "resultado_teste",
    "D0011": "trabalhou_semana",
    "D0021": "rendimento_habitual",
    "D0031": "rendimento_efetivo",
    "F001": "recebeu_auxilio",
    "F006": "trabalho_remoto",
}

# Colunas binárias (1=Sim, 2=Não)
BIN_COLS = [
    "sintoma_febre", "sintoma_tosse", "sintoma_garganta", "sintoma_falta_ar",
    "sintoma_cabeca", "sintoma_peito", "sintoma_nausea", "sintoma_diarreia",
    "sintoma_olfato_paladar", "procurou_atendimento", "fez_teste", "trabalho_remoto",
]

MAP_BINARIO = {1: "Sim", 2: "Não"}
MAP_RES_TESTE = {48: "Positivo", 12: "Negativo", 36: "Indeterminado"}

# ------------- Funções -----------------

def tratar_nulos(df: pd.DataFrame) -> pd.DataFrame:
    """Aplica imputação e recodificação padrão para a PNAD‑COVID."""
    df = df.copy()
    # Procurou atendimento / fez teste – ausentes ⇒ 2 (Não)
    df[["procurou_atendimento", "fez_teste"]] = (
        df[["procurou_atendimento", "fez_teste"]].fillna(2)
    )
    # Resultado de teste – mapear códigos e preencher ausentes
    df["resultado_teste"] = (
        df["resultado_teste"].map(MAP_RES_TESTE).fillna("Sem Teste")
    )
    # Trabalho remoto – ausentes ⇒ 2 (Não)
    df["trabalho_remoto"] = df["trabalho_remoto"].fillna(2)
    # Converter todos binários para Sim/Não
    df[BIN_COLS] = df[BIN_COLS].replace(MAP_BINARIO)
    return df


def processar_csv(entrada: str, saida: str) -> None:
    """Processa *entrada* e grava CSV limpo em *saida*."""
    if not os.path.exists(entrada):
        raise FileNotFoundError(entrada)

    df = pd.read_csv(
        entrada,
        sep=",",
        encoding="utf-8",
        usecols=COLS_INTERES,
        engine="python",
    )
    df.rename(columns=MAP_RENOMEIA, inplace=True)
    df = tratar_nulos(df)

    os.makedirs(os.path.dirname(saida), exist_ok=True)
    df.to_csv(saida, index=False)
    print(f"✅  Arquivo limpo salvo em {saida}  ({len(df):,} linhas)")


# ------------- Interface CLI ------------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Limpa microdados PNAD‑COVID 2020.")
    parser.add_argument("entrada", help="Caminho do CSV bruto.")
    parser.add_argument("saida", help="Caminho de saída para o CSV limpo.")
    return parser


def main():
    args = _build_parser().parse_args()
    processar_csv(args.entrada, args.saida)


if __name__ == "__main__":
    main()