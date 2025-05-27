import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from google.cloud import bigquery
from google.oauth2 import service_account
import json, os, matplotlib.ticker as mticker

##############################################################################
# Configurações gerais da página
##############################################################################

st.set_page_config(page_title="Dashboard PNAD‑COVID 2020", page_icon="🦠", layout="wide")

# ---------------------------------------------------------------------------
# 1) AUTENTICAÇÃO GCP
# ---------------------------------------------------------------------------
@st.cache_resource(show_spinner="🔑 Conectando ao BigQuery…")
def get_bq_client():
    """Devolve um cliente BigQuery usando a chave que está em st.secrets
    (ou opcionalmente em gcp_service_account_key.json para teste local)."""
    key_info = None
    if "gcp_service_account_key" in st.secrets:
        key_info = st.secrets["gcp_service_account_key"]
        # Quando o secret vem em TOML estilo tabela, precisamos convertê‑lo p/ dict
        if not isinstance(key_info, dict):
            key_info = dict(key_info)
    elif os.path.exists("gcp_service_account_key.json"):
        with open("gcp_service_account_key.json", "r") as f:
            key_info = json.load(f)
    else:
        st.error("❌ Credenciais GCP não encontradas. Configure em *Secrets* ou deixe o arquivo gcp_service_account_key.json na raiz.")
        st.stop()

    creds = service_account.Credentials.from_service_account_info(key_info)
    return bigquery.Client(project="tech-chalenge-covid", credentials=creds)

# ---------------------------------------------------------------------------
# 2) CARREGAMENTO DE DADOS – apenas colunas realmente usadas, para não estourar memória
# ---------------------------------------------------------------------------
COLS = [
    "DataReferencia_Mes", "uf_desc", "sexo_desc", "Idade", "escolaridade_desc",
    "FaixaRendimento_desc", "Febre_desc", "Tosse_desc", "DificuldadeRespirar_desc",
    "PerdaOlfatoPaladar_desc", "ProcurouAtendimento_desc", "InternadoHospital_desc",
    "Trabalhou_desc", "AuxilioEmergencial_desc"
]

@st.cache_data(ttl="1h", show_spinner="📥 Baixando dados da PNAD‑COVID…")
def load_data(client: bigquery.Client) -> pd.DataFrame:
    sql = f"""
        SELECT {', '.join(COLS)}
        FROM `tech-chalenge-covid.pnad_covid_processed.pnad_covid_analitica_consolidada`
    """
    try:
        df = client.query(sql).to_dataframe()
        if "DataReferencia_Mes" in df.columns:
            df["DataReferencia_Mes"] = pd.to_datetime(df["DataReferencia_Mes"]).dt.strftime("%Y-%m")
        return df
    except Exception as e:
        st.error(f"Erro ao consultar BigQuery: {e}")
        return pd.DataFrame()

client = get_bq_client()
df_raw = load_data(client)
if df_raw.empty:
    st.stop()

# ---------------------------------------------------------------------------
# 3) SIDEBAR – Filtros
# ---------------------------------------------------------------------------
st.sidebar.title("Filtros")
meses = ["Todos"] + sorted(df_raw["DataReferencia_Mes"].unique().tolist())
mes = st.sidebar.selectbox("Mês", meses)
ufs = ["Todos"] + sorted(df_raw["uf_desc"].unique())
uf = st.sidebar.selectbox("UF", ufs)
sexos = ["Todos"] + sorted(df_raw["sexo_desc"].unique())
sexo = st.sidebar.selectbox("Sexo", sexos)

# Aplicar filtros
mask = pd.Series(True, index=df_raw.index)
if mes != "Todos":
    mask &= df_raw["DataReferencia_Mes"] == mes
if uf != "Todos":
    mask &= df_raw["uf_desc"] == uf
if sexo != "Todos":
    mask &= df_raw["sexo_desc"] == sexo

df = df_raw[mask]

# ---------------------------------------------------------------------------
# 4) MÉTRICAS PRINCIPAIS
# ---------------------------------------------------------------------------
col1, col2, col3 = st.columns(3)
col1.metric("Respondentes", f"{len(df):,}")
prev_febre = (df["Febre_desc"] == "Sim").mean() * 100 if not df.empty else 0
col2.metric("% Febre (Sim)", f"{prev_febre:.1f}%")
prev_aux = (df["AuxilioEmergencial_desc"] == "Sim").mean() * 100 if not df.empty else 0
col3.metric("% Auxílio (Sim)", f"{prev_aux:.1f}%")

# ---------------------------------------------------------------------------
# 5) FUNÇÕES DE GRÁFICO (resumidas – já testam coluna antes de plotar)
# ---------------------------------------------------------------------------

def safe_barplot(series: pd.Series, title: str, ax, palette="viridis"):
    if series.empty:
        ax.text(0.5, 0.5, "Sem dados", ha="center", va="center")
    else:
        sns.barplot(x=series.index, y=series.values, palette=palette, ax=ax)
        ax.set_title(title)
        ax.set_ylabel("")
        ax.tick_params(axis="x", rotation=45)

# ---------------------------------------------------------------------------
# 6) PAINEL DEMOGRÁFICO & SOCIOECONÔMICO
# ---------------------------------------------------------------------------
st.header("Perfil Demográfico & Socioeconômico")
fig, axs = plt.subplots(2, 2, figsize=(14, 10))

safe_barplot(df["uf_desc"].value_counts().head(10), "Top‑10 UFs", axs[0, 0])
if not df["Idade"].dropna().empty:
    sns.histplot(df["Idade"].dropna(), bins=30, ax=axs[0, 1], color="skyblue")
    axs[0, 1].set_title("Distribuição de Idade")
else:
    axs[0, 1].text(0.5, 0.5, "Sem idade", ha="center", va="center")

safe_barplot(df["sexo_desc"].value_counts(), "Sexo", axs[1, 0], palette="coolwarm")
safe_barplot(df["FaixaRendimento_desc"].value_counts().head(10), "Faixa de Rendimento", axs[1, 1], palette="magma")

plt.tight_layout()
st.pyplot(fig)
plt.close(fig)

# ---------------------------------------------------------------------------
# 7) CLÍNICO – Sintomas & Atendimento
# ---------------------------------------------------------------------------
st.header("Sintomas & Procura por Atendimento")
fig2, ax2 = plt.subplots(1, 2, figsize=(14, 5))

sint_cols = {"Febre": "Febre_desc", "Tosse": "Tosse_desc", "Dif. Respirar": "DificuldadeRespirar_desc", "Perda Olf/Pala": "PerdaOlfatoPaladar_desc"}
prev = {nome: (df[col] == "Sim").mean()*100 for nome, col in sint_cols.items() if col in df}
if prev:
    sns.barplot(x=list(prev.keys()), y=list(prev.values()), ax=ax2[0], palette="pastel")
    ax2[0].set_title("Prevalência de Sintomas (%)")
else:
    ax2[0].text(0.5,0.5,"Sem dados sintomas",ha="center",va="center")

# Procura atendimento entre sintomáticos
has_symptom = pd.Series(False, index=df.index)
for col in sint_cols.values():
    if col in df:
        has_symptom |= df[col] == "Sim"
procura = df[has_symptom]["ProcurouAtendimento_desc"].value_counts()
safe_barplot(procura, "Procurou Atendimento (Sintomáticos)", ax2[1], palette="Set2")

plt.tight_layout(); st.pyplot(fig2); plt.close(fig2)

# ---------------------------------------------------------------------------
# 8) ECONÔMICO & AUXÍLIO
# ---------------------------------------------------------------------------
st.header("Trabalho & Auxílio Emergencial")
fig3, ax3 = plt.subplots(1, 2, figsize=(14, 5))

safe_barplot(df["Trabalhou_desc"].value_counts(), "Trabalhou na Semana?", ax3[0], palette="Blues")
safe_barplot(df["AuxilioEmergencial_desc"].value_counts(), "Recebeu Auxílio?", ax3[1], palette="Greens")
plt.tight_layout(); st.pyplot(fig3); plt.close(fig3)

# ---------------------------------------------------------------------------
# 9) EVOLUÇÃO TEMPORAL
# ---------------------------------------------------------------------------
st.header("Evolução Mensal")
fig4, ax4 = plt.subplots(figsize=(10, 4))

evol = df_raw.groupby("DataReferencia_Mes")["Febre_desc"].apply(lambda s: (s == "Sim").mean()*100)
if not evol.empty:
    evol.sort_index().plot(marker="o", ax=ax4)
    ax4.set_ylabel("% Febre (Sim)")
    ax4.set_xlabel("Mês")
    ax4.yaxis.set_major_formatter(mticker.PercentFormatter())
    ax4.grid(ls="--", alpha=0.6)
else:
    ax4.text(0.5, 0.5, "Sem dados p/ evolução", ha="center", va="center")
st.pyplot(fig4); plt.close(fig4)

# ---------------------------------------------------------------------------
# 10) RODAPÉ
# ---------------------------------------------------------------------------
st.markdown("---")
st.write("Fonte: **IBGE – PNAD COVID‑19 (Maio/Julho/Setembro 2020)** | Tech Challenge – FIAP Data Analytics")
st.write("Autores: Rosicleia Cavalcante • Guillermo J. C. Privat • Kelly P. M. Campos")
