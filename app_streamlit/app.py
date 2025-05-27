import streamlit as st
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account
import json
import matplotlib.pyplot as plt
import seaborn as sns
import os # Para verificar arquivo local de credenciais
import matplotlib.ticker # Para FixedFormatter

# Configuração da página
st.set_page_config(layout="wide", page_title="Tech Challenge FIAP - PNAD COVID-19")

# --- Autenticação e Carregamento de Dados ---

@st.cache_resource # Cacheia o recurso (cliente BigQuery)
def connect_to_bigquery():
    """Conecta-se ao BigQuery usando credenciais do Streamlit Secrets ou arquivo local."""
    credentials = None 
    try:
        key_info_dict = st.secrets["gcp_service_account_key"] 
        if not isinstance(key_info_dict, dict): # Garantir que seja um dict para from_service_account_info
            key_info_dict = dict(key_info_dict)
        credentials = service_account.Credentials.from_service_account_info(key_info_dict)
        # Removido st.sidebar.success daqui para evitar output antes da UI principal
    except FileNotFoundError: 
        local_key_path = "gcp_service_account_key.json"
        if os.path.exists(local_key_path):
            try:
                with open(local_key_path, 'r') as f:
                    key_dict_local_json = json.load(f) 
                credentials = service_account.Credentials.from_service_account_info(key_dict_local_json)
                # Removido st.sidebar.info daqui
            except Exception as e_local_file: 
                st.error(f"Erro ao carregar chave local: {e_local_file}") # Mostrar erro na UI principal
                st.stop()
        else:
            st.error("Credenciais GCP não encontradas (nem st.secrets, nem gcp_service_account_key.json).")
            st.stop() 
    except Exception as e: 
        st.error(f"Erro ao carregar credenciais do st.secrets: {e}")
        st.stop()

    if credentials is None:
        st.error("Falha crítica na obtenção de credenciais.")
        st.stop()
        
    client = bigquery.Client(project='tech-chalenge-covid', credentials=credentials)
    return client

@st.cache_data(ttl=3600) 
def load_data(_client):
    sql_query = "SELECT * FROM `tech-chalenge-covid.pnad_covid_processed.pnad_covid_analitica_consolidada`"
    try:
        df = _client.query(sql_query).to_dataframe()
        if 'DataReferencia_Mes' in df.columns:
            df['DataReferencia_Mes'] = df['DataReferencia_Mes'].astype(str)
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados do BigQuery: {e}")
        return pd.DataFrame()

# --- Funções Auxiliares de Plotagem ---

def plot_distribuicao_uf(df_filtered, ax):
    if 'uf_desc' not in df_filtered.columns:
        ax.text(0.5, 0.5, "Coluna 'uf_desc' ausente", ha='center', va='center', transform=ax.transAxes); return
    contagem_uf = df_filtered['uf_desc'].value_counts(dropna=False).head(15)
    sns.barplot(x=contagem_uf.index, y=contagem_uf.values, palette="viridis", ax=ax)
    ax.set_title('Respondentes por UF (Top 15)', fontsize=14)
    ax.set_xlabel('UF', fontsize=10)
    ax.set_ylabel('Nº Respondentes', fontsize=10)
    ax.tick_params(axis='x', rotation=45) 
    plt.setp(ax.get_xticklabels(), ha="right", rotation_mode="anchor")

def plot_distribuicao_idade(df_filtered, ax):
    if 'Idade' not in df_filtered.columns or df_filtered['Idade'].dropna().empty:
        ax.text(0.5, 0.5, "Sem dados de idade", ha='center', va='center', transform=ax.transAxes); return
    idade_para_plot = df_filtered['Idade'].dropna().astype(float)
    sns.histplot(idade_para_plot, bins=30, kde=True, color="skyblue", ax=ax)
    ax.set_title('Distribuição de Idade', fontsize=14)
    ax.set_xlabel('Idade (anos)', fontsize=10)
    ax.set_ylabel('Frequência', fontsize=10)
    ax.grid(axis='y', alpha=0.75)

def plot_distribuicao_sexo(df_filtered, ax):
    if 'sexo_desc' not in df_filtered.columns:
        ax.text(0.5, 0.5, "Coluna 'sexo_desc' ausente", ha='center', va='center', transform=ax.transAxes); return
    contagem_sexo = df_filtered['sexo_desc'].value_counts(dropna=False)
    if not contagem_sexo.empty:
        ax.pie(contagem_sexo, labels=contagem_sexo.index, autopct='%1.1f%%', startangle=90,
               colors=['lightcoral', 'lightskyblue'], wedgeprops={"edgecolor":"black"}, textprops={'fontsize': 10})
        ax.set_title('Distribuição por Sexo', fontsize=14)
    else:
        ax.text(0.5, 0.5, "Sem dados de sexo", ha='center', va='center', transform=ax.transAxes)

def plot_distribuicao_escolaridade(df_filtered, ax):
    if 'escolaridade_desc' not in df_filtered.columns:
        ax.text(0.5, 0.5, "Coluna 'escolaridade_desc' ausente", ha='center', va='center', transform=ax.transAxes); return
    ordem_escolaridade = ['Sem instrução', 'Fundamental incompleto', 'Fundamental completa', 'Médio incompleto', 'Médio completo', 'Superior incompleto', 'Superior completo', 'Pós-graduação, mestrado ou doutorado', 'Não Informado']
    categorias_presentes = df_filtered['escolaridade_desc'].unique()
    ordem_presente = [cat for cat in ordem_escolaridade if cat in categorias_presentes]
    contagem_escolaridade = df_filtered['escolaridade_desc'].value_counts(dropna=False).reindex(ordem_presente if ordem_presente else categorias_presentes).fillna(0)
    if contagem_escolaridade.sum() > 0:
        sns.barplot(x=contagem_escolaridade.index, y=contagem_escolaridade.values, palette='Spectral', ax=ax)
        ax.set_title('Distribuição por Escolaridade', fontsize=14)
        ax.set_xlabel('Escolaridade', fontsize=10)
        ax.set_ylabel('Nº Respondentes', fontsize=10)
        ax.tick_params(axis='x', rotation=45) 
        plt.setp(ax.get_xticklabels(), ha="right", rotation_mode="anchor")
    else:
        ax.text(0.5, 0.5, "Sem dados de escolaridade", ha='center', va='center', transform=ax.transAxes)

def plot_distribuicao_rendimento(df_filtered, ax):
    if 'FaixaRendimento_desc' not in df_filtered.columns:
        ax.text(0.5, 0.5, "Coluna 'FaixaRendimento_desc' ausente", ha='center', va='center', transform=ax.transAxes); return
    ordem_faixa_rendimento = ['0 - 100', '101 - 300', '301 - 600', '601 - 800', '801 - 1.600', '1.601 - 3.000', '3.001 - 10.000', '10.001 - 50.000', '50.001 - 100.000', 'Mais de 100.000', 'Não Informado']
    categorias_presentes = df_filtered['FaixaRendimento_desc'].unique()
    ordem_presente = [cat for cat in ordem_faixa_rendimento if cat in categorias_presentes]
    contagem_rend = df_filtered['FaixaRendimento_desc'].value_counts(dropna=False).reindex(ordem_presente if ordem_presente else categorias_presentes).fillna(0)
    if contagem_rend.sum() > 0:
        sns.barplot(x=contagem_rend.index, y=contagem_rend.values, palette='magma', ax=ax)
        ax.set_title('Distribuição por Faixa de Rendimento', fontsize=14)
        ax.set_xlabel('Faixa de Rendimento (R$)', fontsize=10)
        ax.set_ylabel('Nº Respondentes', fontsize=10)
        ax.tick_params(axis='x', rotation=45)
        plt.setp(ax.get_xticklabels(), ha="right", rotation_mode="anchor")
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
                ax.set_title(f'{nome_sintoma}', fontsize=12); ax.set_ylabel('Nº', fontsize=8)
                ax.tick_params(axis='x', rotation=45, labelsize=8)
            else: ax.text(0.5, 0.5, "Sem dados", ha='center', va='center', transform=ax.transAxes)
        else: ax.text(0.5, 0.5, f"Coluna {coluna_sintoma} ausente", ha='center', va='center', transform=ax.transAxes)

def plot_procura_atendimento_sintomaticos(df_filtered, ax):
    required = ['Febre_desc', 'Tosse_desc', 'DificuldadeRespirar_desc', 'PerdaOlfatoPaladar_desc', 'ProcurouAtendimento_desc']
    if not all(c in df_filtered.columns for c in required): ax.text(0.5,0.5,"Col. ausentes",transform=ax.transAxes); return
    df_copy = df_filtered.copy()
    df_copy['Teve_Sintoma'] = ((df_copy['Febre_desc']=='Sim')|(df_copy['Tosse_desc']=='Sim')|
                               (df_copy['DificuldadeRespirar_desc']=='Sim')|(df_copy['PerdaOlfatoPaladar_desc']=='Sim'))
    df_sint = df_copy[df_copy['Teve_Sintoma']==True]
    if not df_sint.empty:
        counts = df_sint['ProcurouAtendimento_desc'].value_counts(dropna=False)
        if not counts.empty:
            sns.barplot(x=counts.index, y=counts.values, palette="Set2", ax=ax)
            ax.set_title('Procura Atendimento (Sintomáticos)', fontsize=14)
        else: ax.text(0.5,0.5,"Sem dados procura",transform=ax.transAxes)
    else: ax.text(0.5,0.5,"Sem sintomáticos",transform=ax.transAxes)

def plot_internacao_sintomaticos_atendimento(df_filtered, ax):
    required = ['Febre_desc', 'Tosse_desc', 'DificuldadeRespirar_desc', 'PerdaOlfatoPaladar_desc', 'ProcurouAtendimento_desc', 'InternadoHospital_desc']
    if not all(c in df_filtered.columns for c in required): ax.text(0.5,0.5,"Col. ausentes",transform=ax.transAxes); return
    df_copy = df_filtered.copy()
    df_copy['Teve_Sintoma'] = ((df_copy['Febre_desc']=='Sim')|(df_copy['Tosse_desc']=='Sim')|
                               (df_copy['DificuldadeRespirar_desc']=='Sim')|(df_copy['PerdaOlfatoPaladar_desc']=='Sim'))
    df_sint_atend = df_copy[(df_copy['Teve_Sintoma']==True) & (df_copy['ProcurouAtendimento_desc']=='Sim')]
    if not df_sint_atend.empty:
        counts = df_sint_atend['InternadoHospital_desc'].value_counts(dropna=False)
        if not counts.empty:
            sns.barplot(x=counts.index, y=counts.values, palette="coolwarm", ax=ax)
            ax.set_title('Internação (Sintom. c/ Atend.)', fontsize=14)
        else: ax.text(0.5,0.5,"Sem dados internação",transform=ax.transAxes)
    else: ax.text(0.5,0.5,"Sem dados para análise",transform=ax.transAxes)

def plot_situacao_trabalho(df_filtered, ax):
    if 'Trabalhou_desc' not in df_filtered.columns: ax.text(0.5,0.5,"'Trabalhou_desc' ausente",transform=ax.transAxes); return
    counts = df_filtered['Trabalhou_desc'].value_counts(dropna=False)
    if not counts.empty:
        ax.pie(counts, labels=counts.index, autopct='%1.1f%%', startangle=90,
               wedgeprops={"edgecolor":"black"}, textprops={'fontsize':10})
        ax.set_title('Trabalhou na Semana?', fontsize=14)
    else: ax.text(0.5,0.5,"Sem dados trabalho",transform=ax.transAxes)

def plot_auxilio_emergencial(df_filtered, ax):
    if 'AuxilioEmergencial_desc' not in df_filtered.columns: ax.text(0.5,0.5,"'AuxilioEmergencial_desc' ausente",transform=ax.transAxes); return
    counts = df_filtered['AuxilioEmergencial_desc'].value_counts(dropna=False)
    if not counts.empty:
        sns.barplot(x=counts.index, y=counts.values, palette="YlGnBu", ax=ax)
        ax.set_title('Recebeu Auxílio Emergencial?', fontsize=14)
    else: ax.text(0.5,0.5,"Sem dados auxílio",transform=ax.transAxes)

def plot_evolucao_temporal_sintomas(df_original_temporal, sintomas_para_temporal, ax):
    df_sintomas_temporal_list = []
    for nome_sintoma, coluna_sintoma in sintomas_para_temporal.items():
        if coluna_sintoma in df_original_temporal.columns:
            df_copy = df_original_temporal.copy()
            try: 
                df_copy['DataReferencia_Mes_dt'] = pd.to_datetime(df_copy['DataReferencia_Mes'], errors='coerce')
                df_copy.dropna(subset=['DataReferencia_Mes_dt'], inplace=True) 
                if df_copy.empty: continue
            except Exception: continue # Silenciosamente ignora se conversão falhar
            
            percentual_sim_por_mes = df_copy.groupby('DataReferencia_Mes_dt')[coluna_sintoma].value_counts(normalize=True).mul(100).unstack(fill_value=0)
            if 'Sim' in percentual_sim_por_mes.columns:
                df_sintomas_temporal_list.append(percentual_sim_por_mes[['Sim']].rename(columns={'Sim': nome_sintoma}))
    
    if df_sintomas_temporal_list:
        df_sintomas_evolucao = pd.concat(df_sintomas_temporal_list, axis=1).fillna(0).sort_index()
        if not df_sintomas_evolucao.empty:
            df_sintomas_evolucao.plot(kind='line', marker='o', ax=ax)
            ax.set_title('Evolução % Sintomas "Sim"', fontsize=14)
            ax.legend(title='Sintoma', fontsize=8); ax.grid(True, linestyle='--', alpha=0.7)
            ax.tick_params(axis='x', rotation=45)
            ax.xaxis.set_major_formatter(matplotlib.ticker.FixedFormatter(df_sintomas_evolucao.index.strftime('%m/%Y')))
        else: ax.text(0.5, 0.5, "Sem dados evol. sintomas",transform=ax.transAxes)
    else: ax.text(0.5, 0.5, "Não gerou dados evol.",transform=ax.transAxes)

def plot_evolucao_temporal_eco(df_original_temporal, ax):
    df_copy = df_original_temporal.copy()
    try:
        df_copy['DataReferencia_Mes_dt'] = pd.to_datetime(df_copy['DataReferencia_Mes'], errors='coerce')
        df_copy.dropna(subset=['DataReferencia_Mes_dt'], inplace=True)
        if df_copy.empty: ax.text(0.5,0.5,"Sem datas válidas",transform=ax.transAxes); return
    except Exception: ax.text(0.5,0.5,"Erro conversão datas",transform=ax.transAxes); return

    evo_trab = df_copy.groupby('DataReferencia_Mes_dt')['Trabalhou_desc'].value_counts(normalize=True).mul(100).unstack(fill_value=0)
    evo_aux = df_copy.groupby('DataReferencia_Mes_dt')['AuxilioEmergencial_desc'].value_counts(normalize=True).mul(100).unstack(fill_value=0)
    idx = evo_trab.index if not evo_trab.empty else (evo_aux.index if not evo_aux.empty else pd.DatetimeIndex([]))
    if idx.empty: ax.text(0.5,0.5,"Sem dados evol. eco",transform=ax.transAxes); return
        
    df_evo_eco = pd.DataFrame(index=idx)
    df_evo_eco['% Trab (Sim)'] = evo_trab['Sim'] if 'Sim' in evo_trab else 0
    df_evo_eco['% Aux (Sim)'] = evo_aux['Sim'] if 'Sim' in evo_aux else 0
    df_evo_eco = df_evo_eco.sort_index()

    if not df_evo_eco.empty and isinstance(df_evo_eco.index, pd.DatetimeIndex):
        l1=ax.plot(df_evo_eco.index, df_evo_eco['% Trab (Sim)'], marker='o',c='b',label='% Trab (Sim)')
        ax.set_ylabel('% (Trabalho)',c='b',fontsize=10); ax.tick_params(axis='y',labelcolor='b')
        ax2=ax.twinx()
        l2=ax2.plot(df_evo_eco.index, df_evo_eco['% Aux (Sim)'],marker='x',c='r',label='% Aux (Sim)')
        ax2.set_ylabel('% (Auxílio)',c='r',fontsize=10); ax2.tick_params(axis='y',labelcolor='r')
        ax.set_title('Evolução Trabalho e Auxílio', fontsize=14)
        lns=l1+l2; labs=[l.get_label() for l in lns]; ax.legend(lns,labs,loc='best',fontsize=8)
        ax.grid(True,ls='--',alpha=0.7); ax.tick_params(axis='x',rotation=45)
        ax.xaxis.set_major_formatter(matplotlib.ticker.FixedFormatter(df_evo_eco.index.strftime('%m/%Y')))
    else: ax.text(0.5,0.5,"Sem dados válidos evol. eco",transform=ax.transAxes)

# --- Inicialização da UI ---
st.sidebar.image("https://fiap.com.br/wp-content/themes/fiap2020/img/logo-fiap.svg", width=100)
st.sidebar.title("Filtros")

# Mensagem de status da autenticação na sidebar
auth_status_placeholder = st.sidebar.empty()

# Tentar conectar e carregar dados
client_bq = connect_to_bigquery() # Chamada movida para depois do placeholder

if client_bq: # Se a conexão foi bem sucedida (credentials obtidas)
    auth_status_placeholder.success("Autenticado via Streamlit Secrets.")
    df_pnad = load_data(client_bq)
else: # Se connect_to_bigquery() parou a app devido a erro de credencial
    auth_status_placeholder.error("Falha na autenticação.")
    st.stop() # Garante que a app pare se client_bq não for criado

if df_pnad.empty:
    st.warning("Não foi possível carregar os dados da PNAD COVID-19.")
    st.stop()

# --- Interface Streamlit ---
st.image("https://fiap.com.br/wp-content/themes/fiap2020/img/logo-fiap.svg", width=150) 
st.title("Tech Challenge: Análise PNAD COVID-19")
st.subheader("Data Analytics - Planejamento Hospitalar")
st.markdown("""
Esta aplicação apresenta uma análise interativa dos microdados da pesquisa PNAD COVID-19,
referentes aos meses de Maio, Julho e Setembro de 2020.
O objetivo é entender o comportamento da população durante a pandemia, identificando
características clínicas, socioeconômicas e comportamentais relevantes para o planejamento hospitalar.
""")

# --- Barra Lateral para Filtros (continuação) ---
df_pnad['DataReferencia_Mes'] = df_pnad['DataReferencia_Mes'].astype(str)
mes_map = {"2020-05-01": "Maio/2020", "2020-07-01": "Julho/2020", "2020-09-01": "Setembro/2020"}
available_raw_months = sorted(df_pnad['DataReferencia_Mes'].unique())
month_options_display = ["Todos"] + [mes_map.get(m, m) for m in available_raw_months]
selected_month_display = st.sidebar.selectbox("Mês:", options=month_options_display, index=0)

selected_month_actual = "Todos"
if selected_month_display != "Todos":
    for actual_val, display_val in mes_map.items():
        if display_val == selected_month_display:
            selected_month_actual = actual_val
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
st.header("Métricas Chave")
if not df_filtrado.empty:
    c1,c2,c3=st.columns(3)
    c1.metric("Respondentes",f"{df_filtrado.shape[0]:,}")
    if 'Febre_desc' in df_filtrado: c2.metric("Prev. Febre ('Sim')",f"{(df_filtrado[df_filtrado['Febre_desc']=='Sim'].shape[0]/df_filtrado.shape[0])*100 if df_filtrado.shape[0]>0 else 0:.1f}%")
    else: c2.metric("Prev. Febre ('Sim')", "N/A")
    if 'AuxilioEmergencial_desc' in df_filtrado: c3.metric("% c/ Auxílio ('Sim')",f"{(df_filtrado[df_filtrado['AuxilioEmergencial_desc']=='Sim'].shape[0]/df_filtrado.shape[0])*100 if df_filtrado.shape[0]>0 else 0:.1f}%")
    else: c3.metric("% c/ Auxílio ('Sim')", "N/A")
else: st.info("Nenhum dado para os filtros.")

# --- Layout Principal com Seções ---
if not df_filtrado.empty:
    st.markdown("---"); st.header("Perfil Demográfico e Socioeconômico")
    try:
        fig1,ax1=plt.subplots(1,2,figsize=(15,5)); plot_distribuicao_uf(df_filtrado,ax1[0]); plot_distribuicao_idade(df_filtrado,ax1[1])
        plt.tight_layout(); st.pyplot(fig1); plt.clf()
        fig2,ax2=plt.subplots(1,3,figsize=(20,5)); plot_distribuicao_sexo(df_filtrado,ax2[0]); plot_distribuicao_escolaridade(df_filtrado,ax2[1]); plot_distribuicao_rendimento(df_filtrado,ax2[2])
        plt.tight_layout(); st.pyplot(fig2); plt.clf()
    except Exception as e: st.error(f"Erro gráficos demográficos: {e}")

    st.markdown("---"); st.header("Análise Clínica dos Sintomas e Procura por Atendimento")
    sint_map={'Febre':'Febre_desc','Tosse':'Tosse_desc','Dif.Respirar':'DificuldadeRespirar_desc','Perda Olfato/Paladar':'PerdaOlfatoPaladar_desc'}
    try:
        fig3,ax3=plt.subplots(2,2,figsize=(12,10)); plot_prevalencia_sintomas(df_filtrado,sint_map,ax3)
        fig3.suptitle('Prevalência Sintomas',fontsize=16,y=1.02); plt.tight_layout(rect=[0,0,1,0.98]); st.pyplot(fig3); plt.clf()
        fig4,ax4=plt.subplots(1,2,figsize=(15,5)); plot_procura_atendimento_sintomaticos(df_filtrado,ax4[0]); plot_internacao_sintomaticos_atendimento(df_filtrado,ax4[1])
        plt.tight_layout(); st.pyplot(fig4); plt.clf()
    except Exception as e: st.error(f"Erro gráficos clínicos: {e}")

    st.markdown("---"); st.header("Impacto Econômico e Auxílios")
    try:
        fig5,ax5=plt.subplots(1,2,figsize=(15,6)); plot_situacao_trabalho(df_filtrado,ax5[0]); plot_auxilio_emergencial(df_filtrado,ax5[1])
        plt.tight_layout(); st.pyplot(fig5); plt.clf()
    except Exception as e: st.error(f"Erro gráficos econômicos: {e}")

    st.markdown("---"); st.header("Análise Temporal (Evolução Mensal)")
    st.markdown("*Filtros de UF/Sexo aplicados; Mês ignorado.*")
    df_temp=df_pnad.copy()
    if selected_uf!="Todos": df_temp=df_temp[df_temp['uf_desc']==selected_uf]
    if selected_sexo!="Todos": df_temp=df_temp[df_temp['sexo_desc']==selected_sexo]
    if not df_temp.empty:
        try:
            fig6,ax6=plt.subplots(1,2,figsize=(20,6)); plot_evolucao_temporal_sintomas(df_temp,sint_map,ax6[0]); plot_evolucao_temporal_eco(df_temp,ax6[1])
            plt.tight_layout(); st.pyplot(fig6); plt.clf()
        except Exception as e: st.error(f"Erro gráficos temporais: {e}")
    else: st.info("Sem dados para gráficos temporais com filtros UF/Sexo.")
else:
    if client_bq: st.info("Nenhum dado para os filtros. Tente outra combinação.")

# --- Rodapé ---
st.markdown("---")
st.markdown("""
**Fonte:** PNAD COVID-19, IBGE (Mai, Jul, Set 2020).  
**Tech Challenge FIAP - Data Analytics**  
**Autores:** Rosicleia C. Mota, Guillermo J. C. Privat, Kelly P. M. Campos.
""")
st.sidebar.markdown("---")
st.sidebar.markdown("Desenvolvido para o Tech Challenge FIAP por:")
st.sidebar.markdown("- Rosicleia C. Mota")
st.sidebar.markdown("- Guillermo J. C. Privat")
st.sidebar.markdown("- Kelly P. M. Campos")
