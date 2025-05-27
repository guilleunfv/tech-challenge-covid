import streamlit as st
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account
import json
import matplotlib.pyplot as plt
import seaborn as sns
import os # Para verificar arquivo local de credenciais

# Configuração da página
st.set_page_config(layout="wide", page_title="Tech Challenge FIAP - PNAD COVID-19")

# --- Autenticação e Carregamento de Dados ---

@st.cache_resource # Cacheia o recurso (cliente BigQuery)
def connect_to_bigquery():
    """Conecta-se ao BigQuery usando credenciais do Streamlit Secrets ou arquivo local."""
    credentials = None # Inicializar credentials
    try:
        # Tenta carregar do Streamlit Secrets (para deploy)
        key_info_dict = st.secrets["gcp_service_account_key"] 
        
        if not isinstance(key_info_dict, dict):
            key_info_dict = dict(key_info_dict)

        credentials = service_account.Credentials.from_service_account_info(key_info_dict)
        st.sidebar.success("Autenticado via Streamlit Secrets.")
    
    except FileNotFoundError: 
        local_key_path = "gcp_service_account_key.json"
        if os.path.exists(local_key_path):
            try:
                with open(local_key_path, 'r') as f:
                    key_dict_local_json = json.load(f) 
                credentials = service_account.Credentials.from_service_account_info(key_dict_local_json)
                st.sidebar.info("Autenticado via arquivo JSON local.")
            except Exception as e_local_file: 
                st.sidebar.error(f"Erro ao carregar chave local: {e_local_file}")
                st.stop()
        else:
            st.sidebar.error("Credenciais GCP não encontradas (nem st.secrets, nem gcp_service_account_key.json).")
            st.error("Erro de Autenticação: Verifique as credenciais do GCP.")
            st.stop() 
    
    except Exception as e: 
        st.sidebar.error(f"Erro ao carregar credenciais do st.secrets: {e}")
        st.error("Erro de Autenticação: Verifique as credenciais do GCP no Streamlit Cloud.")
        st.stop()

    if credentials is None:
        st.sidebar.error("Falha crítica na obtenção de credenciais.")
        st.error("Erro de Autenticação: Não foi possível obter as credenciais.")
        st.stop()
        
    client = bigquery.Client(project='tech-chalenge-covid', credentials=credentials)
    return client

@st.cache_data(ttl=3600) # Cacheia os dados por 1 hora
def load_data(_client):
    """Carrega os dados da tabela consolidada do BigQuery."""
    sql_query = """
    SELECT * 
    FROM `tech-chalenge-covid.pnad_covid_processed.pnad_covid_analitica_consolidada`
    """ # Considerar seleccionar solo columnas necesarias si la tabla es muy grande
    try:
        df = _client.query(sql_query).to_dataframe()
        if 'DataReferencia_Mes' in df.columns:
            df['DataReferencia_Mes'] = df['DataReferencia_Mes'].astype(str)
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados do BigQuery: {e}")
        return pd.DataFrame()

# Inicializar cliente e carregar dados
client_bq = connect_to_bigquery()
df_pnad = load_data(client_bq)

if df_pnad.empty:
    st.warning("Não foi possível carregar os dados. Verifique a conexão, a tabela no BigQuery e as dependências (como 'db-dtypes').")
    st.stop()

# --- Funções Auxiliares de Plotagem ---

def plot_distribuicao_uf(df_filtered, ax):
    contagem_uf = df_filtered['uf_desc'].value_counts(dropna=False).head(15)
    sns.barplot(x=contagem_uf.index, y=contagem_uf.values, palette="viridis", ax=ax)
    ax.set_title('Distribuição de Respondentes por UF (Top 15)', fontsize=14)
    ax.set_xlabel('Unidade da Federação', fontsize=10)
    ax.set_ylabel('Número de Respondentes', fontsize=10)
    ax.tick_params(axis='x', rotation=45) # CORRIGIDO: 'ha' removido
    # Para ajustar melhor a alineación si es necesario después de la rotación:
    plt.setp(ax.get_xticklabels(), ha="right", rotation_mode="anchor")


def plot_distribuicao_idade(df_filtered, ax):
    if not df_filtered['Idade'].dropna().empty:
        idade_para_plot = df_filtered['Idade'].dropna().astype(float)
        sns.histplot(idade_para_plot, bins=30, kde=True, color="skyblue", ax=ax)
        ax.set_title('Distribuição de Idade dos Respondentes', fontsize=14)
        ax.set_xlabel('Idade (anos)', fontsize=10)
        ax.set_ylabel('Frequência', fontsize=10)
        ax.grid(axis='y', alpha=0.75)
    else:
        ax.text(0.5, 0.5, "Sem dados de idade para exibir", ha='center', va='center', transform=ax.transAxes)

def plot_distribuicao_sexo(df_filtered, ax):
    contagem_sexo = df_filtered['sexo_desc'].value_counts(dropna=False)
    if not contagem_sexo.empty:
        ax.pie(contagem_sexo, labels=contagem_sexo.index, autopct='%1.1f%%', startangle=90,
               colors=['lightcoral', 'lightskyblue'], wedgeprops={"edgecolor":"black"}, textprops={'fontsize': 10})
        ax.set_title('Distribuição Percentual por Sexo', fontsize=14)
    else:
        ax.text(0.5, 0.5, "Sem dados de sexo para exibir", ha='center', va='center', transform=ax.transAxes)

def plot_distribuicao_escolaridade(df_filtered, ax):
    ordem_escolaridade = [
        'Sem instrução', 'Fundamental incompleto', 'Fundamental completa',
        'Médio incompleto', 'Médio completo', 'Superior incompleto',
        'Superior completo', 'Pós-graduação, mestrado ou doutorado', 'Não Informado'
    ]
    # Filtrar categorias presentes para evitar erros com reindex
    categorias_presentes = df_filtered['escolaridade_desc'].unique()
    ordem_presente = [cat for cat in ordem_escolaridade if cat in categorias_presentes]
    
    if not ordem_presente: # Si no hay ninguna categoría de la lista ordenada presente
        contagem_escolaridade = df_filtered['escolaridade_desc'].value_counts(dropna=False)
    else:
        contagem_escolaridade = df_filtered['escolaridade_desc'].value_counts(dropna=False).reindex(ordem_presente).fillna(0)

    if not contagem_escolaridade.dropna().empty: # Considerar .sum() > 0 si fillna(0)
        sns.barplot(x=contagem_escolaridade.index, y=contagem_escolaridade.values, palette='Spectral', ax=ax)
        ax.set_title('Distribuição por Escolaridade', fontsize=14)
        ax.set_xlabel('Nível de Escolaridade', fontsize=10)
        ax.set_ylabel('Número de Respondentes', fontsize=10)
        ax.tick_params(axis='x', rotation=45, ha="right")
    else:
        ax.text(0.5, 0.5, "Sem dados de escolaridade", ha='center', va='center', transform=ax.transAxes)


def plot_distribuicao_rendimento(df_filtered, ax):
    ordem_faixa_rendimento = [
        '0 - 100', '101 - 300', '301 - 600', '601 - 800', '801 - 1.600',
        '1.601 - 3.000', '3.001 - 10.000', '10.001 - 50.000',
        '50.001 - 100.000', 'Mais de 100.000', 'Não Informado'
    ]
    categorias_presentes = df_filtered['FaixaRendimento_desc'].unique()
    ordem_presente = [cat for cat in ordem_faixa_rendimento if cat in categorias_presentes]

    if not ordem_presente:
        contagem_rend = df_filtered['FaixaRendimento_desc'].value_counts(dropna=False)
    else:
        contagem_rend = df_filtered['FaixaRendimento_desc'].value_counts(dropna=False).reindex(ordem_presente).fillna(0)

    if not contagem_rend.dropna().empty:
        sns.barplot(x=contagem_rend.index, y=contagem_rend.values, palette='magma', ax=ax)
        ax.set_title('Distribuição por Faixa de Rendimento', fontsize=14)
        ax.set_xlabel('Faixa de Rendimento (R$)', fontsize=10)
        ax.set_ylabel('Número de Respondentes', fontsize=10)
        ax.tick_params(axis='x', rotation=45, ha="right")
    else:
        ax.text(0.5, 0.5, "Sem dados de rendimento", ha='center', va='center', transform=ax.transAxes)

def plot_prevalencia_sintomas(df_filtered, sintomas_principais, axes):
    axes_flat = axes.flatten()
    for i, (nome_sintoma, coluna_sintoma) in enumerate(sintomas_principais.items()):
        ax = axes_flat[i]
        if coluna_sintoma in df_filtered.columns:
            contagem = df_filtered[coluna_sintoma].value_counts(dropna=False)
            if not contagem.empty:
                sns.barplot(x=contagem.index, y=contagem.values, ax=ax, palette="pastel")
                ax.set_title(f'{nome_sintoma}', fontsize=12)
                ax.set_ylabel('Nº Respondentes', fontsize=8)
                ax.tick_params(axis='x', rotation=45, labelsize=8)
            else:
                ax.text(0.5, 0.5, "Sem dados", ha='center', va='center', transform=ax.transAxes)
        else:
            ax.text(0.5, 0.5, f"Coluna {coluna_sintoma} não encontrada", ha='center', va='center', transform=ax.transAxes)

def plot_procura_atendimento_sintomaticos(df_filtered, ax):
    if not all(col in df_filtered.columns for col in ['Febre_desc', 'Tosse_desc', 'DificuldadeRespirar_desc', 'PerdaOlfatoPaladar_desc', 'ProcurouAtendimento_desc']):
        ax.text(0.5, 0.5, "Colunas de sintomas/atendimento ausentes", ha='center', va='center', transform=ax.transAxes)
        return

    df_filtered_copy = df_filtered.copy() # Evitar SettingWithCopyWarning
    df_filtered_copy['Teve_Algum_Sintoma_Principal'] = (
        (df_filtered_copy['Febre_desc'] == 'Sim') |
        (df_filtered_copy['Tosse_desc'] == 'Sim') |
        (df_filtered_copy['DificuldadeRespirar_desc'] == 'Sim') |
        (df_filtered_copy['PerdaOlfatoPaladar_desc'] == 'Sim')
    )
    df_com_sintomas = df_filtered_copy[df_filtered_copy['Teve_Algum_Sintoma_Principal'] == True]
    
    if not df_com_sintomas.empty:
        contagem_procura = df_com_sintomas['ProcurouAtendimento_desc'].value_counts(dropna=False)
        if not contagem_procura.empty:
            sns.barplot(x=contagem_procura.index, y=contagem_procura.values, palette="Set2", ax=ax)
            ax.set_title('Procura Atendimento (Sintomáticos)', fontsize=14)
            ax.set_ylabel('Nº Respondentes', fontsize=10)
            ax.set_xlabel('Procurou Atendimento?', fontsize=10)
        else:
            ax.text(0.5, 0.5, "Sem dados de procura (sintomáticos)", ha='center', va='center', transform=ax.transAxes)
    else:
        ax.text(0.5, 0.5, "Sem sintomáticos para análise", ha='center', va='center', transform=ax.transAxes)

def plot_internacao_sintomaticos_atendimento(df_filtered, ax):
    required_cols = ['Febre_desc', 'Tosse_desc', 'DificuldadeRespirar_desc', 'PerdaOlfatoPaladar_desc', 'ProcurouAtendimento_desc', 'InternadoHospital_desc']
    if not all(col in df_filtered.columns for col in required_cols):
        ax.text(0.5, 0.5, "Colunas de sintomas/internação ausentes", ha='center', va='center', transform=ax.transAxes)
        return
        
    df_filtered_copy = df_filtered.copy()
    if 'Teve_Algum_Sintoma_Principal' not in df_filtered_copy.columns:
         df_filtered_copy['Teve_Algum_Sintoma_Principal'] = (
            (df_filtered_copy['Febre_desc'] == 'Sim') | (df_filtered_copy['Tosse_desc'] == 'Sim') |
            (df_filtered_copy['DificuldadeRespirar_desc'] == 'Sim') | (df_filtered_copy['PerdaOlfatoPaladar_desc'] == 'Sim')
        )
    df_sintomas_e_procurou = df_filtered_copy[
        (df_filtered_copy['Teve_Algum_Sintoma_Principal'] == True) & 
        (df_filtered_copy['ProcurouAtendimento_desc'] == 'Sim')
    ]

    if not df_sintomas_e_procurou.empty:
        contagem_internado = df_sintomas_e_procurou['InternadoHospital_desc'].value_counts(dropna=False)
        if not contagem_internado.empty:
            sns.barplot(x=contagem_internado.index, y=contagem_internado.values, palette="coolwarm", ax=ax)
            ax.set_title('Internação (Sintomáticos que Procuraram Atend.)', fontsize=14)
            ax.set_ylabel('Nº Respondentes', fontsize=10)
            ax.set_xlabel('Foi Internado?', fontsize=10)
        else:
            ax.text(0.5, 0.5, "Sem dados de internação", ha='center', va='center', transform=ax.transAxes)
    else:
        ax.text(0.5, 0.5, "Sem dados para esta análise", ha='center', va='center', transform=ax.transAxes)

def plot_situacao_trabalho(df_filtered, ax):
    if 'Trabalhou_desc' not in df_filtered.columns:
        ax.text(0.5, 0.5, "Coluna 'Trabalhou_desc' ausente", ha='center', va='center', transform=ax.transAxes)
        return
    contagem_trabalhou = df_filtered['Trabalhou_desc'].value_counts(dropna=False)
    if not contagem_trabalhou.empty:
        ax.pie(contagem_trabalhou, labels=contagem_trabalhou.index, autopct='%1.1f%%', startangle=90,
               wedgeprops={"edgecolor":"black"}, textprops={'fontsize': 10})
        ax.set_title('Trabalhou na Semana de Referência', fontsize=14)
    else:
        ax.text(0.5, 0.5, "Sem dados de trabalho", ha='center', va='center', transform=ax.transAxes)

def plot_auxilio_emergencial(df_filtered, ax):
    if 'AuxilioEmergencial_desc' not in df_filtered.columns:
        ax.text(0.5, 0.5, "Coluna 'AuxilioEmergencial_desc' ausente", ha='center', va='center', transform=ax.transAxes)
        return
    contagem_auxilio = df_filtered['AuxilioEmergencial_desc'].value_counts(dropna=False)
    if not contagem_auxilio.empty:
        sns.barplot(x=contagem_auxilio.index, y=contagem_auxilio.values, palette="YlGnBu", ax=ax)
        ax.set_title('Recebeu Auxílio Emergencial?', fontsize=14)
        ax.set_ylabel('Nº Respondentes', fontsize=10)
        ax.set_xlabel('')
    else:
        ax.text(0.5, 0.5, "Sem dados de auxílio", ha='center', va='center', transform=ax.transAxes)


def plot_evolucao_temporal_sintomas(df_original_temporal, sintomas_para_temporal, ax):
    # df_original_temporal já deve estar filtrado por UF/Sexo se necessário, mas não por mês
    df_sintomas_temporal_list = []
    for nome_sintoma, coluna_sintoma in sintomas_para_temporal.items():
        if coluna_sintoma in df_original_temporal.columns:
            df_copy = df_original_temporal.copy()
            try: # Adicionado try-except para conversão de data
                df_copy['DataReferencia_Mes_dt'] = pd.to_datetime(df_copy['DataReferencia_Mes'], errors='coerce')
                df_copy.dropna(subset=['DataReferencia_Mes_dt'], inplace=True) # Remover linhas onde a conversão falhou
                if df_copy.empty:
                    continue
            except Exception as e_date_conv:
                st.warning(f"Erro ao converter DataReferencia_Mes para datetime para {nome_sintoma}: {e_date_conv}")
                continue
            
            percentual_sim_por_mes = df_copy.groupby('DataReferencia_Mes_dt')[coluna_sintoma].value_counts(normalize=True).mul(100).unstack(fill_value=0)
            if 'Sim' in percentual_sim_por_mes.columns:
                df_temp = percentual_sim_por_mes[['Sim']].copy()
                df_temp.rename(columns={'Sim': nome_sintoma}, inplace=True)
                df_sintomas_temporal_list.append(df_temp)
    
    if df_sintomas_temporal_list:
        df_sintomas_evolucao = pd.concat(df_sintomas_temporal_list, axis=1).fillna(0)
        df_sintomas_evolucao = df_sintomas_evolucao.sort_index() 
        
        if not df_sintomas_evolucao.empty:
            df_sintomas_evolucao.plot(kind='line', marker='o', ax=ax)
            ax.set_title('Evolução % Sintomas "Sim"', fontsize=14)
            ax.set_ylabel('% Respondentes', fontsize=10)
            ax.set_xlabel('Mês de Referência', fontsize=10)
            ax.legend(title='Sintoma', fontsize=8)
            ax.grid(True, linestyle='--', alpha=0.7)
            ax.tick_params(axis='x', rotation=45)
            ax.xaxis.set_major_formatter(plt.FixedFormatter(df_sintomas_evolucao.index.strftime('%m/%Y')))
        else:
            ax.text(0.5, 0.5, "Sem dados para evolução de sintomas", ha='center', va='center', transform=ax.transAxes)
    else:
        ax.text(0.5, 0.5, "Não foi possível gerar dados para evolução", ha='center', va='center', transform=ax.transAxes)


def plot_evolucao_temporal_eco(df_original_temporal, ax):
    df_copy = df_original_temporal.copy()
    try:
        df_copy['DataReferencia_Mes_dt'] = pd.to_datetime(df_copy['DataReferencia_Mes'], errors='coerce')
        df_copy.dropna(subset=['DataReferencia_Mes_dt'], inplace=True)
        if df_copy.empty:
            ax.text(0.5, 0.5, "Sem dados de data válidos para evolução econômica", ha='center', va='center', transform=ax.transAxes)
            return
    except Exception as e_date_conv_eco:
        st.warning(f"Erro ao converter DataReferencia_Mes para datetime (eco): {e_date_conv_eco}")
        ax.text(0.5, 0.5, "Erro na conversão de datas (eco)", ha='center', va='center', transform=ax.transAxes)
        return

    evolucao_trabalhou = df_copy.groupby('DataReferencia_Mes_dt')['Trabalhou_desc'].value_counts(normalize=True).mul(100).unstack(fill_value=0)
    evolucao_auxilio = df_copy.groupby('DataReferencia_Mes_dt')['AuxilioEmergencial_desc'].value_counts(normalize=True).mul(100).unstack(fill_value=0)

    # Garantir que o índice seja datetime
    idx = evolucao_trabalhou.index if not evolucao_trabalhou.empty else (evolucao_auxilio.index if not evolucao_auxilio.empty else pd.DatetimeIndex([]))
    if idx.empty:
        ax.text(0.5, 0.5, "Sem dados para evolução econômica", ha='center', va='center', transform=ax.transAxes)
        return
        
    df_evolucao_eco = pd.DataFrame(index=idx)

    if 'Sim' in evolucao_trabalhou.columns: df_evolucao_eco['% Trabalhou (Sim)'] = evolucao_trabalhou['Sim']
    else: df_evolucao_eco['% Trabalhou (Sim)'] = 0
    
    if 'Sim' in evolucao_auxilio.columns: df_evolucao_eco['% Recebeu Auxílio (Sim)'] = evolucao_auxilio['Sim']
    else: df_evolucao_eco['% Recebeu Auxílio (Sim)'] = 0
    
    df_evolucao_eco = df_evolucao_eco.sort_index()

    if not df_evolucao_eco.empty and df_evolucao_eco.index.is_all_dates:
        line1 = ax.plot(df_evolucao_eco.index, df_evolucao_eco['% Trabalhou (Sim)'], marker='o', color='blue', label='% Trabalhou (Sim)')
        ax.set_ylabel('% Respondentes (Trabalho)', fontsize=10, color='blue')
        ax.tick_params(axis='y', labelcolor='blue')
        
        ax2 = ax.twinx()
        line2 = ax2.plot(df_evolucao_eco.index, df_evolucao_eco['% Recebeu Auxílio (Sim)'], marker='x', color='red', label='% Recebeu Auxílio (Sim)')
        ax2.set_ylabel('% Respondentes (Auxílio)', fontsize=10, color='red')
        ax2.tick_params(axis='y', labelcolor='red')

        ax.set_title('Evolução Trabalho e Auxílio', fontsize=14)
        ax.set_xlabel('Mês de Referência', fontsize=10)
        
        lines = line1 + line2
        labels = [l.get_label() for l in lines]
        ax.legend(lines, labels, loc='best', fontsize=8)
        
        ax.grid(True, linestyle='--', alpha=0.7)
        ax.tick_params(axis='x', rotation=45)
        ax.xaxis.set_major_formatter(plt.FixedFormatter(df_evolucao_eco.index.strftime('%m/%Y')))

    else:
        ax.text(0.5, 0.5, "Sem dados válidos para evolução econômica", ha='center', va='center', transform=ax.transAxes)


# --- Interface Streamlit ---
st.image("https://fiap.com.br/wp-content/themes/fiap2020/img/logo-fiap.svg", width=150) # Logo FIAP
st.title("Tech Challenge: Análise PNAD COVID-19")
st.subheader("Data Analytics - Planejamento Hospitalar")

st.markdown("""
Esta aplicação apresenta uma análise interativa dos microdados da pesquisa PNAD COVID-19,
referentes aos meses de Maio, Julho e Setembro de 2020.
O objetivo é entender o comportamento da população durante a pandemia, identificando
características clínicas, socioeconômicas e comportamentais relevantes para o planejamento hospitalar.
""")

# --- Barra Lateral para Filtros ---
st.sidebar.header("Filtros")

df_pnad['DataReferencia_Mes'] = df_pnad['DataReferencia_Mes'].astype(str)
mes_map = {
    "2020-05-01": "Maio/2020",
    "2020-07-01": "Julho/2020",
    "2020-09-01": "Setembro/2020"
}
available_raw_months = sorted(df_pnad['DataReferencia_Mes'].unique())
month_options_display = ["Todos"] + [mes_map.get(m, m) for m in available_raw_months]
month_options_actual = ["Todos"] + available_raw_months

selected_month_display = st.sidebar.selectbox("Mês de Referência:", options=month_options_display, index=0)

selected_month_actual = "Todos"
if selected_month_display != "Todos":
    for actual, display in zip(month_options_actual[1:], month_options_display[1:]): 
        if display == selected_month_display:
            selected_month_actual = actual
            break

all_ufs = ["Todos"] + sorted(df_pnad['uf_desc'].unique().tolist())
selected_uf = st.sidebar.selectbox("UF:", options=all_ufs, index=0)

all_sexos = ["Todos"] + sorted(df_pnad['sexo_desc'].unique().tolist())
selected_sexo = st.sidebar.selectbox("Sexo:", options=all_sexos, index=0)


# Aplicar Filtros
df_filtrado = df_pnad.copy()
if selected_month_actual != "Todos":
    df_filtrado = df_filtrado[df_filtrado['DataReferencia_Mes'] == selected_month_actual]
if selected_uf != "Todos":
    df_filtrado = df_filtrado[df_filtrado['uf_desc'] == selected_uf]
if selected_sexo != "Todos":
    df_filtrado = df_filtrado[df_filtrado['sexo_desc'] == selected_sexo]


# --- KPIs ---
st.header("Métricas Chave (Considerando Filtros)")
if not df_filtrado.empty:
    col1, col2, col3 = st.columns(3)
    col1.metric("Total de Respondentes", f"{df_filtrado.shape[0]:,}")
    
    if 'Febre_desc' in df_filtrado.columns:
        febre_sim = df_filtrado[df_filtrado['Febre_desc'] == 'Sim'].shape[0]
        prevalencia_febre = (febre_sim / df_filtrado.shape[0]) * 100 if df_filtrado.shape[0] > 0 else 0
        col2.metric("Prevalência de Febre ('Sim')", f"{prevalencia_febre:.1f}%")
    else:
        col2.metric("Prevalência de Febre ('Sim')", "N/A")

    if 'AuxilioEmergencial_desc' in df_filtrado.columns:
        auxilio_sim = df_filtrado[df_filtrado['AuxilioEmergencial_desc'] == 'Sim'].shape[0]
        perc_auxilio = (auxilio_sim / df_filtrado.shape[0]) * 100 if df_filtrado.shape[0] > 0 else 0
        col3.metric("% Recebeu Auxílio ('Sim')", f"{perc_auxilio:.1f}%")
    else:
        col3.metric("% Recebeu Auxílio ('Sim')", "N/A")
else:
    st.info("Nenhum dado encontrado para os filtros selecionados.")


if not df_filtrado.empty:
    # --- Layout Principal com Seções ---
    st.markdown("---")
    st.header("Perfil Demográfico e Socioeconômico")
    
    try:
        fig_demografico1, axes_demografico1 = plt.subplots(1, 2, figsize=(15, 5))
        plot_distribuicao_uf(df_filtrado, axes_demografico1[0])
        plot_distribuicao_idade(df_filtrado, axes_demografico1[1])
        plt.tight_layout()
        st.pyplot(fig_demografico1)
        plt.clf() 

        fig_demografico2, axes_demografico2 = plt.subplots(1, 3, figsize=(20, 5)) 
        plot_distribuicao_sexo(df_filtrado, axes_demografico2[0])
        plot_distribuicao_escolaridade(df_filtrado, axes_demografico2[1])
        plot_distribuicao_rendimento(df_filtrado, axes_demografico2[2])
        plt.tight_layout()
        st.pyplot(fig_demografico2)
        plt.clf()
    except Exception as e_plot_demo:
        st.error(f"Erro ao gerar gráficos demográficos: {e_plot_demo}")


    st.markdown("---")
    st.header("Análise Clínica dos Sintomas e Procura por Atendimento")
    
    sintomas_principais_map = {
        'Febre': 'Febre_desc',
        'Tosse': 'Tosse_desc',
        'Dificuldade para Respirar': 'DificuldadeRespirar_desc',
        'Perda de Olfato/Paladar': 'PerdaOlfatoPaladar_desc'
    }
    try:
        fig_sintomas, axes_sintomas = plt.subplots(2, 2, figsize=(12, 10))
        plot_prevalencia_sintomas(df_filtrado, sintomas_principais_map, axes_sintomas)
        fig_sintomas.suptitle('Prevalência dos Principais Sintomas Reportados', fontsize=16, y=1.02)
        plt.tight_layout(rect=[0, 0, 1, 0.98]) 
        st.pyplot(fig_sintomas)
        plt.clf()

        fig_clinico2, axes_clinico2 = plt.subplots(1, 2, figsize=(15, 5))
        plot_procura_atendimento_sintomaticos(df_filtrado, axes_clinico2[0])
        plot_internacao_sintomaticos_atendimento(df_filtrado, axes_clinico2[1])
        plt.tight_layout()
        st.pyplot(fig_clinico2)
        plt.clf()
    except Exception as e_plot_clinico:
        st.error(f"Erro ao gerar gráficos clínicos: {e_plot_clinico}")


    st.markdown("---")
    st.header("Impacto Econômico e Auxílios")
    try:
        fig_economico, axes_economico = plt.subplots(1, 2, figsize=(15, 6))
        plot_situacao_trabalho(df_filtrado, axes_economico[0])
        plot_auxilio_emergencial(df_filtrado, axes_economico[1])
        plt.tight_layout()
        st.pyplot(fig_economico)
        plt.clf()
    except Exception as e_plot_eco:
        st.error(f"Erro ao gerar gráficos econômicos: {e_plot_eco}")

    # --- Análise Temporal ---
    st.markdown("---")
    st.header("Análise Temporal (Evolução Mensal)")
    st.markdown("*Nota: Gráficos temporais abaixo consideram 'Todos os Meses', mas respeitam filtros de UF e Sexo, se aplicados.*")

    df_temporal = df_pnad.copy()
    if selected_uf != "Todos":
        df_temporal = df_temporal[df_temporal['uf_desc'] == selected_uf]
    if selected_sexo != "Todos":
        df_temporal = df_temporal[df_temporal['sexo_desc'] == selected_sexo]
    
    if not df_temporal.empty:
        try:
            fig_temporal, axes_temporal = plt.subplots(1, 2, figsize=(20, 6))
            plot_evolucao_temporal_sintomas(df_temporal, sintomas_principais_map, axes_temporal[0])
            plot_evolucao_temporal_eco(df_temporal, axes_temporal[1])
            plt.tight_layout()
            st.pyplot(fig_temporal)
            plt.clf()
        except Exception as e_plot_tempo:
            st.error(f"Erro ao gerar gráficos temporais: {e_plot_tempo}")
    else:
        st.info("Não há dados para exibir gráficos temporais com os filtros de UF/Sexo aplicados.")

else: 
    if client_bq: 
        st.info("Nenhum dado encontrado para os filtros selecionados. Tente uma combinação diferente.")

# --- Rodapé ---
st.markdown("---")
st.markdown("""
**Fonte dos Dados:** PNAD COVID-19, IBGE (Maio, Julho, Setembro 2020).  
**Tech Challenge FIAP - Data Analytics**  
**Autores:** Rosicleia C. Mota, Guillermo J. C. Privat, Kelly P. M. Campos.
""")
st.sidebar.markdown("---")
st.sidebar.image("https://fiap.com.br/wp-content/themes/fiap2020/img/logo-fiap.svg", width=100)
st.sidebar.markdown("Desenvolvido para o Tech Challenge FIAP por:")
st.sidebar.markdown("- Rosicleia C. Mota")
st.sidebar.markdown("- Guillermo J. C. Privat")
st.sidebar.markdown("- Kelly P. M. Campos")
