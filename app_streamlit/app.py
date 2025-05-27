import streamlit as st
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account
import json
import matplotlib.pyplot as plt
import seaborn as sns
import os # Para verificar arquivo local de credenciais

# Configuração da página
st.set_page_config(layout="wide", page_title="Dashboard PNAD COVID-19")

# --- Autenticação e Carregamento de Dados ---

@st.cache_resource # Cacheia o recurso (cliente BigQuery)
# EN connect_to_bigquery():
def connect_to_bigquery():
    """Conecta-se ao BigQuery usando credenciais do Streamlit Secrets ou arquivo local."""
    try:
        # Tenta carregar do Streamlit Secrets (para deploy)
        key_info_dict = st.secrets["gcp_service_account_key"] # Directamente es un objeto similar a un diccionario
        
        # Convertir AttrDict a un diccionario estándar si es necesario para from_service_account_info
        if not isinstance(key_info_dict, dict):
            key_info_dict = dict(key_info_dict)

        credentials = service_account.Credentials.from_service_account_info(key_info_dict)
        st.sidebar.success("Autenticado via Streamlit Secrets.")
    
    except FileNotFoundError: # st.secrets não encontrado (provavelmente local)
        # Tenta carregar de um arquivo JSON local (para desenvolvimento local)
        local_key_path = "gcp_service_account_key.json"
        if os.path.exists(local_key_path):
            try:
                with open(local_key_path, 'r') as f:
                    key_dict_local_json = json.load(f) # Aquí sí cargamos un JSON de archivo
                credentials = service_account.Credentials.from_service_account_info(key_dict_local_json)
                st.sidebar.info("Autenticado via arquivo JSON local.")
            except Exception as e_local_file: # Renombrar la variable de excepción
                st.sidebar.error(f"Erro ao carregar chave local: {e_local_file}")
                st.stop()
        else:
            st.sidebar.error("Credenciais GCP não encontradas (nem st.secrets, nem gcp_service_account_key.json).")
            st.error("Erro de Autenticação: Verifique as credenciais do GCP.")
            st.stop() 
    
    except Exception as e: # Este es el 'except' que estaba causando el IndentationError
        st.sidebar.error(f"Erro ao carregar credenciais do st.secrets: {e}")
        st.error("Erro de Autenticação: Verifique as credenciais do GCP no Streamlit Cloud.")
        st.stop()

    # Esta parte debe estar fuera de los bloques try/except si la autenticación fue exitosa dentro de ellos
    # O, si `credentials` se define dentro de los try/except, asegurarse de que siempre se defina o manejar el caso contrario.
    # Asumiendo que 'credentials' se define correctamente si no hay error:
    client = bigquery.Client(project='tech-chalenge-covid', credentials=credentials)
    return client

@st.cache_data(ttl=3600) # Cacheia os dados por 1 hora
def load_data(_client):
    """Carrega os dados da tabela consolidada do BigQuery."""
    sql_query = """
    SELECT *
    FROM `tech-chalenge-covid.pnad_covid_processed.pnad_covid_analitica_consolidada`
    """
    try:
        df = _client.query(sql_query).to_dataframe()
        # Converter DataReferencia_Mes para string para consistência no filtro
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
    st.warning("Não foi possível carregar os dados. Verifique a conexão e a tabela no BigQuery.")
    st.stop()

# --- Funções Auxiliares de Plotagem ---
# (Replicando a lógica do notebook, adaptada para Streamlit)

def plot_distribuicao_uf(df_filtered, ax):
    contagem_uf = df_filtered['uf_desc'].value_counts(dropna=False).head(15)
    sns.barplot(x=contagem_uf.index, y=contagem_uf.values, palette="viridis", ax=ax)
    ax.set_title('Distribuição de Respondentes por UF (Top 15)', fontsize=14)
    ax.set_xlabel('Unidade da Federação', fontsize=10)
    ax.set_ylabel('Número de Respondentes', fontsize=10)
    ax.tick_params(axis='x', rotation=45, ha="right")

def plot_distribuicao_idade(df_filtered, ax):
    if not df_filtered['Idade'].dropna().empty:
        idade_para_plot = df_filtered['Idade'].dropna().astype(float)
        sns.histplot(idade_para_plot, bins=30, kde=True, color="skyblue", ax=ax)
        ax.set_title('Distribuição de Idade dos Respondentes', fontsize=14)
        ax.set_xlabel('Idade (anos)', fontsize=10)
        ax.set_ylabel('Frequência', fontsize=10)
        ax.grid(axis='y', alpha=0.75)
    else:
        ax.text(0.5, 0.5, "Sem dados de idade para exibir", ha='center', va='center')

def plot_distribuicao_sexo(df_filtered, ax):
    contagem_sexo = df_filtered['sexo_desc'].value_counts(dropna=False)
    if not contagem_sexo.empty:
        ax.pie(contagem_sexo, labels=contagem_sexo.index, autopct='%1.1f%%', startangle=90,
               colors=['lightcoral', 'lightskyblue'], wedgeprops={"edgecolor":"black"}, textprops={'fontsize': 10})
        ax.set_title('Distribuição Percentual por Sexo', fontsize=14)
    else:
        ax.text(0.5, 0.5, "Sem dados de sexo para exibir", ha='center', va='center')

def plot_distribuicao_escolaridade(df_filtered, ax):
    ordem_escolaridade = [
        'Sem instrução', 'Fundamental incompleto', 'Fundamental completa',
        'Médio incompleto', 'Médio completo', 'Superior incompleto',
        'Superior completo', 'Pós-graduação, mestrado ou doutorado', 'Não Informado'
    ]
    ordem_presente = [cat for cat in ordem_escolaridade if cat in df_filtered['escolaridade_desc'].unique()]
    contagem_escolaridade = df_filtered['escolaridade_desc'].value_counts(dropna=False).reindex(ordem_presente)
    
    if not contagem_escolaridade.dropna().empty:
        sns.barplot(x=contagem_escolaridade.index, y=contagem_escolaridade.values, palette='Spectral', ax=ax)
        ax.set_title('Distribuição por Escolaridade', fontsize=14)
        ax.set_xlabel('Nível de Escolaridade', fontsize=10)
        ax.set_ylabel('Número de Respondentes', fontsize=10)
        ax.tick_params(axis='x', rotation=45, ha="right")
    else:
        ax.text(0.5, 0.5, "Sem dados de escolaridade", ha='center', va='center')


def plot_distribuicao_rendimento(df_filtered, ax):
    ordem_faixa_rendimento = [
        '0 - 100', '101 - 300', '301 - 600', '601 - 800', '801 - 1.600',
        '1.601 - 3.000', '3.001 - 10.000', '10.001 - 50.000',
        '50.001 - 100.000', 'Mais de 100.000', 'Não Informado'
    ]
    ordem_presente = [cat for cat in ordem_faixa_rendimento if cat in df_filtered['FaixaRendimento_desc'].unique()]
    contagem_rend = df_filtered['FaixaRendimento_desc'].value_counts(dropna=False).reindex(ordem_presente)

    if not contagem_rend.dropna().empty:
        sns.barplot(x=contagem_rend.index, y=contagem_rend.values, palette='magma', ax=ax)
        ax.set_title('Distribuição por Faixa de Rendimento', fontsize=14)
        ax.set_xlabel('Faixa de Rendimento (R$)', fontsize=10)
        ax.set_ylabel('Número de Respondentes', fontsize=10)
        ax.tick_params(axis='x', rotation=45, ha="right")
    else:
        ax.text(0.5, 0.5, "Sem dados de rendimento", ha='center', va='center')

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
                ax.text(0.5, 0.5, "Sem dados", ha='center', va='center')
        else:
            ax.text(0.5, 0.5, f"Coluna {coluna_sintoma} não encontrada", ha='center', va='center')

def plot_procura_atendimento_sintomaticos(df_filtered, ax):
    df_filtered['Teve_Algum_Sintoma_Principal'] = (
        (df_filtered['Febre_desc'] == 'Sim') |
        (df_filtered['Tosse_desc'] == 'Sim') |
        (df_filtered['DificuldadeRespirar_desc'] == 'Sim') |
        (df_filtered['PerdaOlfatoPaladar_desc'] == 'Sim')
    )
    df_com_sintomas = df_filtered[df_filtered['Teve_Algum_Sintoma_Principal'] == True].copy()
    
    if not df_com_sintomas.empty and 'ProcurouAtendimento_desc' in df_com_sintomas.columns:
        contagem_procura = df_com_sintomas['ProcurouAtendimento_desc'].value_counts(dropna=False)
        if not contagem_procura.empty:
            sns.barplot(x=contagem_procura.index, y=contagem_procura.values, palette="Set2", ax=ax)
            ax.set_title('Procura Atendimento (Sintomáticos)', fontsize=14)
            ax.set_ylabel('Nº Respondentes', fontsize=10)
            ax.set_xlabel('Procurou Atendimento?', fontsize=10)
        else:
            ax.text(0.5, 0.5, "Sem dados de procura (sintomáticos)", ha='center', va='center')
    else:
        ax.text(0.5, 0.5, "Sem sintomáticos ou coluna não encontrada", ha='center', va='center')

def plot_internacao_sintomaticos_atendimento(df_filtered, ax):
    # Requer que 'Teve_Algum_Sintoma_Principal' já exista ou seja recalculada
    if 'Teve_Algum_Sintoma_Principal' not in df_filtered.columns:
         df_filtered['Teve_Algum_Sintoma_Principal'] = (
            (df_filtered['Febre_desc'] == 'Sim') | (df_filtered['Tosse_desc'] == 'Sim') |
            (df_filtered['DificuldadeRespirar_desc'] == 'Sim') | (df_filtered['PerdaOlfatoPaladar_desc'] == 'Sim')
        )
    df_sintomas_e_procurou = df_filtered[
        (df_filtered['Teve_Algum_Sintoma_Principal'] == True) & 
        (df_filtered['ProcurouAtendimento_desc'] == 'Sim')
    ].copy()

    if not df_sintomas_e_procurou.empty and 'InternadoHospital_desc' in df_sintomas_e_procurou.columns:
        contagem_internado = df_sintomas_e_procurou['InternadoHospital_desc'].value_counts(dropna=False)
        if not contagem_internado.empty:
            sns.barplot(x=contagem_internado.index, y=contagem_internado.values, palette="coolwarm", ax=ax)
            ax.set_title('Internação (Sintomáticos que Procuraram Atend.)', fontsize=14)
            ax.set_ylabel('Nº Respondentes', fontsize=10)
            ax.set_xlabel('Foi Internado?', fontsize=10)
        else:
            ax.text(0.5, 0.5, "Sem dados de internação", ha='center', va='center')
    else:
        ax.text(0.5, 0.5, "Sem dados para esta análise", ha='center', va='center')

def plot_situacao_trabalho(df_filtered, ax):
    contagem_trabalhou = df_filtered['Trabalhou_desc'].value_counts(dropna=False)
    if not contagem_trabalhou.empty:
        ax.pie(contagem_trabalhou, labels=contagem_trabalhou.index, autopct='%1.1f%%', startangle=90,
               wedgeprops={"edgecolor":"black"}, textprops={'fontsize': 10})
        ax.set_title('Trabalhou na Semana de Referência', fontsize=14)
    else:
        ax.text(0.5, 0.5, "Sem dados de trabalho", ha='center', va='center')

def plot_auxilio_emergencial(df_filtered, ax):
    contagem_auxilio = df_filtered['AuxilioEmergencial_desc'].value_counts(dropna=False)
    if not contagem_auxilio.empty:
        sns.barplot(x=contagem_auxilio.index, y=contagem_auxilio.values, palette="YlGnBu", ax=ax)
        ax.set_title('Recebeu Auxílio Emergencial?', fontsize=14)
        ax.set_ylabel('Nº Respondentes', fontsize=10)
        ax.set_xlabel('')
    else:
        ax.text(0.5, 0.5, "Sem dados de auxílio", ha='center', va='center')


def plot_evolucao_temporal_sintomas(df_original, sintomas_para_temporal, ax):
    df_sintomas_temporal_list = []
    for nome_sintoma, coluna_sintoma in sintomas_para_temporal.items():
        if coluna_sintoma in df_original.columns:
            # Garantir que DataReferencia_Mes é datetime para ordenação correta
            df_copy = df_original.copy()
            df_copy['DataReferencia_Mes_dt'] = pd.to_datetime(df_copy['DataReferencia_Mes'], errors='coerce')
            
            percentual_sim_por_mes = df_copy.groupby('DataReferencia_Mes_dt')[coluna_sintoma].value_counts(normalize=True).mul(100).unstack(fill_value=0)
            if 'Sim' in percentual_sim_por_mes.columns:
                df_temp = percentual_sim_por_mes[['Sim']].copy()
                df_temp.rename(columns={'Sim': nome_sintoma}, inplace=True)
                df_sintomas_temporal_list.append(df_temp)
    
    if df_sintomas_temporal_list:
        df_sintomas_evolucao = pd.concat(df_sintomas_temporal_list, axis=1).fillna(0)
        df_sintomas_evolucao = df_sintomas_evolucao.sort_index() # Ordenar por data
        
        if not df_sintomas_evolucao.empty:
            df_sintomas_evolucao.plot(kind='line', marker='o', ax=ax)
            ax.set_title('Evolução % Sintomas "Sim"', fontsize=14)
            ax.set_ylabel('% Respondentes', fontsize=10)
            ax.set_xlabel('Mês de Referência', fontsize=10)
            ax.legend(title='Sintoma', fontsize=8)
            ax.grid(True, linestyle='--', alpha=0.7)
            ax.tick_params(axis='x', rotation=45)
            # Formatar eixo X para mostrar apenas Mês/Ano
            ax.xaxis.set_major_formatter(plt.FixedFormatter(df_sintomas_evolucao.index.strftime('%m/%Y')))

        else:
            ax.text(0.5, 0.5, "Sem dados para evolução de sintomas", ha='center', va='center')
    else:
        ax.text(0.5, 0.5, "Não foi possível gerar dados para evolução", ha='center', va='center')


def plot_evolucao_temporal_eco(df_original, ax):
    df_copy = df_original.copy()
    df_copy['DataReferencia_Mes_dt'] = pd.to_datetime(df_copy['DataReferencia_Mes'], errors='coerce')

    evolucao_trabalhou = df_copy.groupby('DataReferencia_Mes_dt')['Trabalhou_desc'].value_counts(normalize=True).mul(100).unstack(fill_value=0)
    evolucao_auxilio = df_copy.groupby('DataReferencia_Mes_dt')['AuxilioEmergencial_desc'].value_counts(normalize=True).mul(100).unstack(fill_value=0)

    df_evolucao_eco = pd.DataFrame(index=evolucao_trabalhou.index if not evolucao_trabalhou.empty else (evolucao_auxilio.index if not evolucao_auxilio.empty else None))
    if df_evolucao_eco.index is None: # Nenhum dado
        ax.text(0.5, 0.5, "Sem dados para evolução econômica", ha='center', va='center')
        return

    if 'Sim' in evolucao_trabalhou.columns: df_evolucao_eco['% Trabalhou (Sim)'] = evolucao_trabalhou['Sim']
    else: df_evolucao_eco['% Trabalhou (Sim)'] = 0
    
    if 'Sim' in evolucao_auxilio.columns: df_evolucao_eco['% Recebeu Auxílio (Sim)'] = evolucao_auxilio['Sim']
    else: df_evolucao_eco['% Recebeu Auxílio (Sim)'] = 0
    
    df_evolucao_eco = df_evolucao_eco.sort_index()

    if not df_evolucao_eco.empty:
        ax.plot(df_evolucao_eco.index, df_evolucao_eco['% Trabalhou (Sim)'], marker='o', color='blue', label='% Trabalhou (Sim)')
        ax.set_ylabel('% Respondentes (Trabalho)', fontsize=10, color='blue')
        ax.tick_params(axis='y', labelcolor='blue')
        
        ax2 = ax.twinx()
        ax2.plot(df_evolucao_eco.index, df_evolucao_eco['% Recebeu Auxílio (Sim)'], marker='x', color='red', label='% Recebeu Auxílio (Sim)')
        ax2.set_ylabel('% Respondentes (Auxílio)', fontsize=10, color='red')
        ax2.tick_params(axis='y', labelcolor='red')

        ax.set_title('Evolução Trabalho e Auxílio', fontsize=14)
        ax.set_xlabel('Mês de Referência', fontsize=10)
        
        # Legendas combinadas
        lines, labels = ax.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax2.legend(lines + lines2, labels + labels2, loc='best', fontsize=8)
        
        ax.grid(True, linestyle='--', alpha=0.7)
        ax.tick_params(axis='x', rotation=45)
        ax.xaxis.set_major_formatter(plt.FixedFormatter(df_evolucao_eco.index.strftime('%m/%Y')))

    else:
        ax.text(0.5, 0.5, "Sem dados para evolução econômica", ha='center', va='center')


# --- Interface Streamlit ---
st.title("Dashboard Analítico da PNAD COVID-19")
st.markdown("""
Esta aplicação apresenta uma análise interativa dos microdados da pesquisa PNAD COVID-19,
referentes aos meses de Maio, Julho e Setembro de 2020.
O objetivo é entender o comportamento da população durante a pandemia, identificando
características clínicas, socioeconômicas e comportamentais relevantes.
""")

# --- Barra Lateral para Filtros ---
st.sidebar.header("Filtros")

# Obter opções de filtro do DataFrame original para garantir que todos os meses estejam disponíveis
# independentemente de outros filtros que possam esvaziar df_filtrado temporariamente
# Assegurar que 'DataReferencia_Mes' seja string aqui também
df_pnad['DataReferencia_Mes'] = df_pnad['DataReferencia_Mes'].astype(str)
mes_map = {
    "2020-05-01": "Maio/2020",
    "2020-07-01": "Julho/2020",
    "2020-09-01": "Setembro/2020"
}
# Usar os valores mapeados se existirem, senão os originais
available_raw_months = sorted(df_pnad['DataReferencia_Mes'].unique())
month_options_display = ["Todos"] + [mes_map.get(m, m) for m in available_raw_months]
month_options_actual = ["Todos"] + available_raw_months

selected_month_display = st.sidebar.selectbox("Mês de Referência:", options=month_options_display)

# Mapear de volta para o valor real para filtragem
selected_month_actual = "Todos"
if selected_month_display != "Todos":
    for actual, display in zip(month_options_actual[1:], month_options_display[1:]): # Pular "Todos"
        if display == selected_month_display:
            selected_month_actual = actual
            break

# Filtros opcionais
all_ufs = ["Todos"] + sorted(df_pnad['uf_desc'].unique().tolist())
selected_uf = st.sidebar.selectbox("UF:", options=all_ufs)

all_sexos = ["Todos"] + sorted(df_pnad['sexo_desc'].unique().tolist())
selected_sexo = st.sidebar.selectbox("Sexo:", options=all_sexos)


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
    
    # Prevalência de Febre (Exemplo)
    if 'Febre_desc' in df_filtrado.columns:
        febre_sim = df_filtrado[df_filtrado['Febre_desc'] == 'Sim'].shape[0]
        prevalencia_febre = (febre_sim / df_filtrado.shape[0]) * 100 if df_filtrado.shape[0] > 0 else 0
        col2.metric("Prevalência de Febre ('Sim')", f"{prevalencia_febre:.1f}%")
    else:
        col2.metric("Prevalência de Febre ('Sim')", "N/A")

    # % Recebeu Auxílio (Exemplo)
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
    
    # Usar plt.subplots para melhor controle e evitar problemas com estado global do pyplot
    fig_demografico1, axes_demografico1 = plt.subplots(1, 2, figsize=(15, 5))
    plot_distribuicao_uf(df_filtrado, axes_demografico1[0])
    plot_distribuicao_idade(df_filtrado, axes_demografico1[1])
    st.pyplot(fig_demografico1)
    plt.clf() # Limpar figura

    fig_demografico2, axes_demografico2 = plt.subplots(1, 3, figsize=(20, 5)) # Aumentado para 3
    plot_distribuicao_sexo(df_filtrado, axes_demografico2[0])
    plot_distribuicao_escolaridade(df_filtrado, axes_demografico2[1])
    plot_distribuicao_rendimento(df_filtrado, axes_demografico2[2])
    st.pyplot(fig_demografico2)
    plt.clf()

    st.markdown("---")
    st.header("Análise Clínica dos Sintomas e Procura por Atendimento")
    
    sintomas_principais_map = {
        'Febre': 'Febre_desc',
        'Tosse': 'Tosse_desc',
        'Dificuldade para Respirar': 'DificuldadeRespirar_desc',
        'Perda de Olfato/Paladar': 'PerdaOlfatoPaladar_desc'
    }
    fig_sintomas, axes_sintomas = plt.subplots(2, 2, figsize=(12, 10))
    plot_prevalencia_sintomas(df_filtrado, sintomas_principais_map, axes_sintomas)
    fig_sintomas.suptitle('Prevalência dos Principais Sintomas Reportados', fontsize=16, y=1.02)
    plt.tight_layout(rect=[0, 0, 1, 0.98]) # Ajustar para o suptitle
    st.pyplot(fig_sintomas)
    plt.clf()

    fig_clinico2, axes_clinico2 = plt.subplots(1, 2, figsize=(15, 5))
    plot_procura_atendimento_sintomaticos(df_filtrado, axes_clinico2[0])
    plot_internacao_sintomaticos_atendimento(df_filtrado, axes_clinico2[1])
    st.pyplot(fig_clinico2)
    plt.clf()

    st.markdown("---")
    st.header("Impacto Econômico e Auxílios")
    fig_economico, axes_economico = plt.subplots(1, 2, figsize=(15, 6))
    plot_situacao_trabalho(df_filtrado, axes_economico[0])
    plot_auxilio_emergencial(df_filtrado, axes_economico[1])
    st.pyplot(fig_economico)
    plt.clf()

    # --- Análise Temporal (Sempre usa dados não filtrados por mês, mas respeita outros filtros) ---
    st.markdown("---")
    st.header("Análise Temporal (Evolução Mensal)")
    st.markdown("*Nota: Gráficos temporais abaixo consideram 'Todos os Meses', mas respeitam filtros de UF e Sexo, se aplicados.*")

    # Para gráficos temporais, usamos uma versão do df_pnad filtrada por UF e Sexo, mas não por mês
    df_temporal = df_pnad.copy()
    if selected_uf != "Todos":
        df_temporal = df_temporal[df_temporal['uf_desc'] == selected_uf]
    if selected_sexo != "Todos":
        df_temporal = df_temporal[df_temporal['sexo_desc'] == selected_sexo]
    
    if not df_temporal.empty:
        fig_temporal, axes_temporal = plt.subplots(1, 2, figsize=(20, 6))
        plot_evolucao_temporal_sintomas(df_temporal, sintomas_principais_map, axes_temporal[0])
        plot_evolucao_temporal_eco(df_temporal, axes_temporal[1])
        plt.tight_layout()
        st.pyplot(fig_temporal)
        plt.clf()
    else:
        st.info("Não há dados para exibir gráficos temporais com os filtros de UF/Sexo aplicados.")

else: # df_filtrado está vazio
    if client_bq: # Se a conexão BQ está ok, mas não há dados para os filtros
        st.info("Nenhum dado encontrado para os filtros selecionados. Tente uma combinação diferente.")

# --- Rodapé ---
st.markdown("---")
st.markdown("""
**Fonte dos Dados:** PNAD COVID-19, IBGE (Maio, Julho, Setembro 2020).
**Autores:** Rosicleia C. Mota, Guillermo J. C. Privat, Kelly P. M. Campos.
""")
st.sidebar.markdown("---")
st.sidebar.markdown("Desenvolvido por: Rosicleia Mota, Guillermo Privat, Kelly Campos.")
