import os
import json
import gc
import matplotlib.pyplot as plt
import matplotlib.ticker
import seaborn as sns
import pandas as pd
import streamlit as st

from google.cloud import bigquery
from google.cloud import bigquery_storage
from google.oauth2 import service_account
from google.auth.exceptions import DefaultCredentialsError
import google.auth

# ---------- Configuração da página ----------
st.set_page_config(
    page_title="Tech Challenge FIAP - PNAD COVID-19",
    layout="wide",
)

# ---------- Conexão BigQuery ----------
@st.cache_resource
def connect_to_bigquery():
    """
    Retorna um cliente BigQuery usando:
    1. ADC (Cloud Run / gcloud auth application-default login)
    2. st.secrets["gcp_service_account_key"]
    3. Arquivo local gcp_service_account_key.json
    """
    project_id = "tech-chalenge-covid"
    credentials = None

    # 1) Tenta Application Default Credentials
    try:
        credentials, _ = google.auth.default(
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
    except DefaultCredentialsError:
        pass  # ignora e tenta próximos métodos

    # 2) Streamlit secrets
    if credentials is None and "gcp_service_account_key" in st.secrets:
        key_info = dict(st.secrets["gcp_service_account_key"])
        credentials = service_account.Credentials.from_service_account_info(key_info)

    # 3) Arquivo local
    if credentials is None and os.path.exists("gcp_service_account_key.json"):
        with open("gcp_service_account_key.json", "r") as f:
            credentials = service_account.Credentials.from_service_account_info(
                json.load(f)
            )

    if credentials is None:
        st.error("Não foi possível obter credenciais GCP.")
        st.stop()

    return bigquery.Client(project=project_id, credentials=credentials)


# ---------- Carregamento de dados ----------
@st.cache_data(ttl=3600)
def load_data(
    _client: bigquery.Client,
    uf: str = "Todos",
    sexo: str = "Todos",
    mes: str = "Todos",
) -> pd.DataFrame:
    """Trae de BigQuery solo las filas que cumplen los filtros."""
    # Construye cláusulas WHERE dinámicas
    where = []
    if uf != "Todos":
        where.append(f"uf_desc = '{uf}'")
    if sexo != "Todos":
        where.append(f"sexo_desc = '{sexo}'")
    if mes != "Todos":
        where.append(f"DataReferencia_Mes = '{mes}'")

    where_sql = "WHERE " + " AND ".join(where) if where else ""

    sql = f"""
        SELECT
            uf_desc,
            Idade,
            sexo_desc,
            escolaridade_desc,
            FaixaRendimento_desc,
            Febre_desc,
            Tosse_desc,
            DificuldadeRespirar_desc,
            PerdaOlfatoPaladar_desc,
            ProcurouAtendimento_desc,
            InternadoHospital_desc,
            Trabalhou_desc,
            AuxilioEmergencial_desc,
            DataReferencia_Mes
        FROM `tech-chalenge-covid.pnad_covid_processed.pnad_covid_analitica_consolidada`
        {where_sql}
    """
    df = _client.query(sql).to_dataframe(create_bqstorage_client=True)
    df["DataReferencia_Mes"] = df["DataReferencia_Mes"].astype(str)
    return df





# ---------- Funções de Plotagem ----------
def plot_distribuicao_uf(df: pd.DataFrame, ax):
    contagem = df["uf_desc"].value_counts(dropna=False).head(15)
    sns.barplot(x=contagem.index, y=contagem.values, palette="viridis", ax=ax, legend=False)
    ax.set_title("Respondentes por UF (Top 15)", fontsize=12)
    ax.set_xlabel("UF", fontsize=9)
    ax.set_ylabel("Nº Respondentes", fontsize=9)
    ax.tick_params(axis="x", rotation=45, labelsize=8)
    plt.setp(ax.get_xticklabels(), ha="right", rotation_mode="anchor")


def plot_distribuicao_idade(df: pd.DataFrame, ax):
    sns.histplot(df["Idade"].dropna().astype(float), bins=20, kde=True, color="skyblue", ax=ax)
    ax.set_title("Distribuição de Idade", fontsize=12)
    ax.set_xlabel("Idade (anos)", fontsize=9)
    ax.set_ylabel("Frequência", fontsize=9)
    ax.grid(axis="y", alpha=0.75, linestyle="--")
    ax.tick_params(labelsize=8)


def plot_distribuicao_sexo(df: pd.DataFrame, ax):
    contagem = df["sexo_desc"].value_counts(dropna=False)
    ax.pie(contagem, labels=contagem.index, autopct="%1.1f%%", startangle=90,
           colors=["lightcoral", "lightskyblue"], wedgeprops={"edgecolor": "black"},
           textprops={"fontsize": 9})
    ax.set_title("Distribuição por Sexo", fontsize=12)


def _ordered_bar(df_col: pd.Series, ordem, palette, title, xlabel, ax):
    cats = df_col.unique()
    ordem_final = [c for c in ordem if c in cats] or list(cats)
    counts = df_col.value_counts(dropna=False).reindex(ordem_final).fillna(0)
    sns.barplot(x=counts.index, y=counts.values, palette=palette, ax=ax)
    ax.set_title(title, fontsize=12)
    ax.set_xlabel(xlabel, fontsize=9)
    ax.set_ylabel("Nº", fontsize=9)
    ax.tick_params(axis="x", rotation=45, labelsize=8)
    plt.setp(ax.get_xticklabels(), ha="right", rotation_mode="anchor")


def plot_distribuicao_escolaridade(df, ax):
    ordem = [
        "Sem instrução", "Fundamental incompleto", "Fundamental completa", "Médio incompleto",
        "Médio completo", "Superior incompleto", "Superior completo",
        "Pós-graduação, mestrado ou doutorado", "Não Informado"
    ]
    _ordered_bar(df["escolaridade_desc"], ordem, "Spectral",
                 "Distribuição por Escolaridade", "Escolaridade", ax)


def plot_distribuicao_rendimento(df, ax):
    ordem = [
        "0 - 100", "101 - 300", "301 - 600", "601 - 800", "801 - 1.600", "1.601 - 3.000",
        "3.001 - 10.000", "10.001 - 50.000", "50.001 - 100.000", "Mais de 100.000", "Não Informado"
    ]
    _ordered_bar(df["FaixaRendimento_desc"], ordem, "magma",
                 "Distribuição por Faixa de Rendimento", "Faixa (R$)", ax)


def plot_prevalencia_sintomas(df, sintomas_map, axes):
    for ax, (nome, coluna) in zip(axes.flatten(), sintomas_map.items()):
        counts = df[coluna].value_counts(dropna=False)
        sns.barplot(x=counts.index, y=counts.values, palette="pastel", ax=ax)
        ax.set_title(nome, fontsize=10)
        ax.set_ylabel("Nº", fontsize=8)
        ax.tick_params(axis="x", rotation=45, labelsize=8)


def plot_procura_atendimento(df, ax):
    sintoma = (df["Febre_desc"] == "Sim") | (df["Tosse_desc"] == "Sim") | \
              (df["DificuldadeRespirar_desc"] == "Sim") | (df["PerdaOlfatoPaladar_desc"] == "Sim")
    df_sint = df[sintoma]
    counts = df_sint["ProcurouAtendimento_desc"].value_counts(dropna=False)
    sns.barplot(x=counts.index, y=counts.values, palette="Set2", ax=ax)
    ax.set_title("Procura Atendimento (Sintom.)", fontsize=12)


def plot_internacao(df, ax):
    sintoma = (df["Febre_desc"] == "Sim") | (df["Tosse_desc"] == "Sim") | \
              (df["DificuldadeRespirar_desc"] == "Sim") | (df["PerdaOlfatoPaladar_desc"] == "Sim")
    df_ = df[sintoma & (df["ProcurouAtendimento_desc"] == "Sim")]
    counts = df_["InternadoHospital_desc"].value_counts(dropna=False)
    sns.barplot(x=counts.index, y=counts.values, palette="coolwarm", ax=ax)
    ax.set_title("Internação (Sintom. c/ Atendimento)", fontsize=12)


def plot_situacao_trabalho(df, ax):
    counts = df["Trabalhou_desc"].value_counts(dropna=False)
    ax.pie(counts, labels=counts.index, autopct="%1.1f%%", startangle=90,
           wedgeprops={"edgecolor": "black"}, textprops={"fontsize": 9})
    ax.set_title("Trabalhou na Semana?", fontsize=12)


def plot_auxilio(df, ax):
    counts = df["AuxilioEmergencial_desc"].value_counts(dropna=False)
    sns.barplot(x=counts.index, y=counts.values, palette="YlGnBu", ax=ax)
    ax.set_title("Recebeu Auxílio Emergencial?", fontsize=12)


def plot_evolucao_sintomas(df, sintomas_map, ax):
    df["DataRef_dt"] = pd.to_datetime(df["DataReferencia_Mes"], errors="coerce")
    df = df.dropna(subset=["DataRef_dt"])
    lista = []
    for nome, col in sintomas_map.items():
        perc = df.groupby("DataRef_dt")[col].value_counts(normalize=True).mul(100).unstack(fill_value=0)
        if "Sim" in perc:
            lista.append(perc[["Sim"]].rename(columns={"Sim": nome}))
    if lista:
        evo = pd.concat(lista, axis=1).fillna(0).sort_index()
        evo.plot(ax=ax, marker="o", fontsize=8)
        ax.set_title('Evolução % Sintomas "Sim"', fontsize=12)
        ax.grid(ls="--", alpha=0.7)
        ax.tick_params(axis="x", rotation=45, labelsize=8)
        ax.xaxis.set_major_formatter(matplotlib.ticker.FixedFormatter(evo.index.strftime("%m/%y")))


def plot_evolucao_eco(df, ax):
    df["DataRef_dt"] = pd.to_datetime(df["DataReferencia_Mes"], errors="coerce")
    df = df.dropna(subset=["DataRef_dt"])
    trab = df.groupby("DataRef_dt")["Trabalhou_desc"].value_counts(normalize=True).mul(100).unstack(fill_value=0)
    aux = df.groupby("DataRef_dt")["AuxilioEmergencial_desc"].value_counts(normalize=True).mul(100).unstack(fill_value=0)

    idx = trab.index.union(aux.index)
    df_ee = pd.DataFrame(index=idx)
    df_ee["% Trab (Sim)"] = trab.get("Sim", 0)
    df_ee["% Aux (Sim)"] = aux.get("Sim", 0)

    l1 = ax.plot(df_ee.index, df_ee["% Trab (Sim)"], marker="o", c="b", label="% Trab (Sim)")
    ax.set_ylabel("% (Trab)", color="b", fontsize=9)
    ax.tick_params(axis="y", labelcolor="b", labelsize=8)

    ax2 = ax.twinx()
    l2 = ax2.plot(df_ee.index, df_ee["% Aux (Sim)"], marker="x", c="r", label="% Aux (Sim)")
    ax2.set_ylabel("% (Aux)", color="r", fontsize=9)
    ax2.tick_params(axis="y", labelcolor="r", labelsize=8)

    ax.set_title("Evolução Trabalho e Auxílio", fontsize=12)
    ax.legend(l1 + l2, ["% Trab (Sim)", "% Aux (Sim)"], fontsize=7)
    ax.grid(ls="--", alpha=0.7)
    ax.tick_params(axis="x", rotation=45, labelsize=8)
    ax.xaxis.set_major_formatter(matplotlib.ticker.FixedFormatter(df_ee.index.strftime("%m/%y")))


# ---------- Main ----------
client = connect_to_bigquery()
df_orig = load_data(client)

# Sidebar filtros
st.sidebar.image("https://www.fiap.com.br/wp-content/uploads/2022/08/logo-fiap.svg", width=80)
st.sidebar.title("Filtros")

mes_map = {
    "2020-05-01": "Maio/2020",
    "2020-07-01": "Julho/2020",
    "2020-09-01": "Setembro/2020",
}
meses_disp = ["Todos"] + [mes_map.get(m, m) for m in sorted(df_orig["DataReferencia_Mes"].unique())]
mes_escolhido = st.sidebar.selectbox("Mês:", options=meses_disp)

uf_opc = ["Todos"] + sorted(df_orig["uf_desc"].unique())
uf_sel = st.sidebar.selectbox("UF:", options=uf_opc)

sexo_opc = ["Todos"] + sorted(df_orig["sexo_desc"].unique())
sexo_sel = st.sidebar.selectbox("Sexo:", options=sexo_opc)

# Aplica filtros
df = df_orig.copy()
if mes_escolhido != "Todos":
    valor_raw = next((k for k, v in mes_map.items() if v == mes_escolhido), mes_escolhido)
    df = df[df["DataReferencia_Mes"] == valor_raw]

if uf_sel != "Todos":
    df = df[df["uf_desc"] == uf_sel]

if sexo_sel != "Todos":
    df = df[df["sexo_desc"] == sexo_sel]

# ---------- KPIs ----------
st.image("https://www.fiap.com.br/wp-content/uploads/2022/08/logo-fiap.svg", width=130)
st.title("Tech Challenge: Análise PNAD COVID-19")
st.subheader("Data Analytics – Planejamento Hospitalar")
st.markdown("Análise interativa dos microdados da PNAD COVID-19 (Maio, Julho, Setembro 2020).")

st.header("Métricas Chave")
if not df.empty:
    col1, col2, col3 = st.columns(3)
    col1.metric("Respondentes", f"{df.shape[0]:,}")

    febre = df[df["Febre_desc"] == "Sim"].shape[0]
    col2.metric("% Febre (Sim)", f"{febre / df.shape[0] * 100:.1f}%")

    aux = df[df["AuxilioEmergencial_desc"] == "Sim"].shape[0]
    col3.metric("% Auxílio (Sim)", f"{aux / df.shape[0] * 100:.1f}%")
else:
    st.info("Nenhum dado para os filtros selecionados.")
    st.stop()

# ---------- Gráficos ----------
sns.set_theme(style="whitegrid")

# Perfil demográfico
st.markdown("---")
st.header("Perfil Demográfico e Socioeconômico")
fig1, ax1 = plt.subplots(1, 2, figsize=(12, 4))
plot_distribuicao_uf(df, ax1[0])
plot_distribuicao_idade(df, ax1[1])
st.pyplot(fig1)
plt.close(fig1); gc.collect()

fig2, ax2 = plt.subplots(1, 3, figsize=(15, 4))
plot_distribuicao_sexo(df, ax2[0])
plot_distribuicao_escolaridade(df, ax2[1])
plot_distribuicao_rendimento(df, ax2[2])
st.pyplot(fig2)
plt.close(fig2); gc.collect()

# Sintomas e atendimento
st.markdown("---")
st.header("Análise Clínica dos Sintomas e Procura por Atendimento")
sint_map = {
    "Febre": "Febre_desc",
    "Tosse": "Tosse_desc",
    "Dif. Respirar": "DificuldadeRespirar_desc",
    "Perda Olfato/Paladar": "PerdaOlfatoPaladar_desc",
}
fig3, ax3 = plt.subplots(2, 2, figsize=(10, 8))
plot_prevalencia_sintomas(df, sint_map, ax3)
st.pyplot(fig3)
plt.close(fig3); gc.collect()

fig4, ax4 = plt.subplots(1, 2, figsize=(12, 4))
plot_procura_atendimento(df, ax4[0])
plot_internacao(df, ax4[1])
st.pyplot(fig4)
plt.close(fig4); gc.collect()

# Impacto econômico
st.markdown("---")
st.header("Impacto Econômico e Auxílios")
fig5, ax5 = plt.subplots(1, 2, figsize=(12, 4))
plot_situacao_trabalho(df, ax5[0])
plot_auxilio(df, ax5[1])
st.pyplot(fig5)
plt.close(fig5); gc.collect()

# Evolução temporal
st.markdown("---")
st.header("Análise Temporal (Evolução Mensal)")
st.markdown("*Filtros de UF/Sexo aplicados; Mês ignorado para este gráfico.*")
df_temp = df_orig.copy()
if uf_sel != "Todos":
    df_temp = df_temp[df_temp["uf_desc"] == uf_sel]
if sexo_sel != "Todos":
    df_temp = df_temp[df_temp["sexo_desc"] == sexo_sel]

fig6, ax6 = plt.subplots(1, 2, figsize=(15, 5))
plot_evolucao_sintomas(df_temp, sint_map, ax6[0])
plot_evolucao_eco(df_temp, ax6[1])
st.pyplot(fig6)
plt.close(fig6); gc.collect()

# Rodapé
st.markdown("---")
st.markdown("""
**Fonte:** PNAD COVID-19, IBGE (Mai, Jul, Set 2020).  
**Tech Challenge FIAP – Data Analytics**  
Autores: Rosicleia C. Mota, Guillermo J. C. Privat, Kelly P. M. Campos.
""")

st.sidebar.markdown("---")
st.sidebar.markdown("Desenvolvido para o Tech Challenge FIAP por:")
st.sidebar.markdown("- Rosicleia C. Mota")
st.sidebar.markdown("- Guillermo J. C. Privat")
st.sidebar.markdown("- Kelly P. M. Campos")
