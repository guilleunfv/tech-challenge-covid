import streamlit as st
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account
import json
import matplotlib.pyplot as plt
import seaborn as sns
import os 
import matplotlib.ticker 

# Configuração da página
st.set_page_config(layout="wide", page_title="Tech Challenge FIAP - PNAD COVID-19")

# --- Autenticação e Carregamento de Dados ---

@st.cache_resource 
def connect_to_bigquery():
    """Conecta-se ao BigQuery usando credenciais do Streamlit Secrets ou arquivo local."""
    credentials = None 
    try:
        key_info_dict = st.secrets["gcp_service_account_key"] 
        if not isinstance(key_info_dict, dict): 
            key_info_dict = dict(key_info_dict)
        credentials = service_account.Credentials.from_service_account_info(key_info_dict)
    except FileNotFoundError: 
        local_key_path = "gcp_service_account_key.json" # Para desenvolvimento local
        if os.path.exists(local_key_path):
            try:
                with open(local_key_path, 'r') as f:
                    key_dict_local_json = json.load(f) 
                credentials = service_account.Credentials.from_service_account_info(key_dict_local_json)
            except Exception as e_local_file: 
                st.error(f"Erro ao carregar chave local '{local_key_path}': {e_local_file}") 
                st.stop()
        else:
            st.error(f"Credenciais GCP não encontradas para deploy (st.secrets) nem localmente ('{local_key_path}').")
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
    # Selecionar colunas explícitamente para otimizar e garantir que temos o que precisamos
    sql_query = """
    SELECT 
        uf_desc, Idade, sexo_desc, cor_raca_desc, escolaridade_desc, 
        Febre_desc, Tosse_desc, DificuldadeRespirar_desc, PerdaOlfatoPaladar_desc,
        ProcurouAtendimento_desc, InternadoHospital_desc, PlanoSaude_desc,
        Trabalhou_desc, AfastadoTrabalho_desc, PosicaoOcupacao_desc,
        FaixaRendimento_desc, RendimentoHabitual_Valor, AuxilioEmergencial_desc, 
        DataReferencia_Mes, Peso_Amostral, Ano, Mes_cod, UF_cod
        -- Adicione outras se forem estritamente necessárias para algum gráfico ou KPI futuro
    FROM `tech-chalenge-covid.pnad_covid_processed.pnad_covid_analitica_consolidada`
    """
    try:
        df = _client.query(sql_query).to_dataframe(create_bqstorage_client=True) # Tenta usar BQ Storage
        if 'DataReferencia_Mes' in df.columns and df['DataReferencia_Mes'].notna().any(): # Verifica se há não-nulos
            # A conversão para string é importante para consistência com mes_map
            df['DataReferencia_Mes'] = df['DataReferencia_Mes'].astype(str) 
        return df
    except Exception as e: 
        st.error(f"Erro ao carregar dados do BigQuery: {e}")
        return pd.DataFrame()

# --- Funções Auxiliares de Plotagem ---

def safe_plot(plot_func, df_filtered, ax, **kwargs):
    """Wrapper para executar funções de ploteo de forma segura."""
    try:
        plot_func(df_filtered, ax, **kwargs)
    except Exception as e:
        ax.text(0.5, 0.5, f"Erro ao gerar gráfico:\n{plot_func.__name__}\nVerifique os dados.", 
                ha='center', va='center', transform=ax.transAxes, fontsize=8, color='red')
        st.warning(f"Aviso no gráfico '{plot_func.__name__}': {e}")


def plot_distribuicao_uf(df_filtered, ax):
    if 'uf_desc' not in df_filtered.columns:
        ax.text(0.5,0.5,"Col 'uf_desc' ausente",transform=ax.transAxes,ha='center',va='center'); return
    counts = df_filtered['uf_desc'].value_counts(dropna=False).head(15)
    if counts.empty: ax.text(0.5,0.5,"Sem dados UF",transform=ax.transAxes,ha='center',va='center'); return
    sns.barplot(x=counts.index, y=counts.values, hue=counts.index, palette="viridis", ax=ax, legend=False)
    ax.set_title('Respondentes por UF (Top 15)', fontsize=11) 
    ax.set_xlabel('UF', fontsize=9); ax.set_ylabel('Nº', fontsize=9)
    ax.tick_params(axis='x', rotation=45, labelsize=8); plt.setp(ax.get_xticklabels(),ha="right",rotation_mode="anchor")

def plot_distribuicao_idade(df_filtered, ax):
    if 'Idade' not in df_filtered.columns or df_filtered['Idade'].dropna().empty:
        ax.text(0.5,0.5,"Sem dados Idade",transform=ax.transAxes,ha='center',va='center'); return
    sns.histplot(df_filtered['Idade'].dropna().astype(float), bins=20, kde=True, color="skyblue", ax=ax) 
    ax.set_title('Distribuição de Idade', fontsize=11)
    ax.set_xlabel('Idade', fontsize=9); ax.set_ylabel('Frequência', fontsize=9)
    ax.grid(True,ls='--',alpha=0.7); ax.tick_params(labelsize=8)

def plot_distribuicao_sexo(df_filtered, ax):
    if 'sexo_desc' not in df_filtered.columns:
        ax.text(0.5,0.5,"Col 'sexo_desc' ausente",transform=ax.transAxes,ha='center',va='center'); return
    counts = df_filtered['sexo_desc'].value_counts(dropna=False)
    if not counts.empty:
        ax.pie(counts,labels=counts.index,autopct='%1.1f%%',startangle=90,colors=['lightcoral','lightskyblue'],
               wedgeprops={"edgecolor":"black"},textprops={'fontsize':8})
        ax.set_title('Distribuição por Sexo', fontsize=11)
    else: ax.text(0.5,0.5,"Sem dados Sexo",transform=ax.transAxes,ha='center',va='center')

def plot_distribuicao_escolaridade(df_filtered, ax):
    if 'escolaridade_desc' not in df_filtered.columns:
        ax.text(0.5,0.5,"Col 'escol_desc' ausente",transform=ax.transAxes,ha='center',va='center'); return
    ordem=['Sem instrução','Fundamental incompleto','Fundamental completa','Médio incompleto','Médio completo','Superior incompleto','Superior completo','Pós-graduação, mestrado ou doutorado','Não Informado']
    cats=df_filtered['escolaridade_desc'].unique(); ord_pres=[c for c in ordem if c in cats]
    counts=df_filtered['escolaridade_desc'].value_counts(dropna=False).reindex(ord_pres if ord_pres else list(cats)).fillna(0)
    if counts.sum()>0:
        sns.barplot(x=counts.index,y=counts.values,hue=counts.index,palette='Spectral',ax=ax,legend=False)
        ax.set_title('Escolaridade',fontsize=11); ax.set_xlabel('',fontsize=9); ax.set_ylabel('Nº',fontsize=9)
        ax.tick_params(axis='x',rotation=45,labelsize=8); plt.setp(ax.get_xticklabels(),ha="right",rotation_mode="anchor")
    else: ax.text(0.5,0.5,"Sem dados Escolaridade",transform=ax.transAxes,ha='center',va='center')

def plot_distribuicao_rendimento(df_filtered, ax):
    if 'FaixaRendimento_desc' not in df_filtered.columns:
        ax.text(0.5,0.5,"Col 'FaixaRend_desc' ausente",transform=ax.transAxes,ha='center',va='center'); return
    ordem=['0 - 100','101 - 300','301 - 600','601 - 800','801 - 1.600','1.601 - 3.000','3.001 - 10.000','10.001 - 50.000','50.001 - 100.000','Mais de 100.000','Não Informado']
    cats=df_filtered['FaixaRendimento_desc'].unique(); ord_pres=[c for c in ordem if c in cats]
    counts=df_filtered['FaixaRendimento_desc'].value_counts(dropna=False).reindex(ord_pres if ord_pres else list(cats)).fillna(0)
    if counts.sum()>0:
        sns.barplot(x=counts.index,y=counts.values,hue=counts.index,palette='magma',ax=ax,legend=False)
        ax.set_title('Faixa de Rendimento',fontsize=11); ax.set_xlabel('',fontsize=9); ax.set_ylabel('Nº',fontsize=9)
        ax.tick_params(axis='x',rotation=45,labelsize=8); plt.setp(ax.get_xticklabels(),ha="right",rotation_mode="anchor")
    else: ax.text(0.5,0.5,"Sem dados Rendimento",transform=ax.transAxes,ha='center',va='center')

def plot_prevalencia_sintomas(df_filtered, sintomas_map, axes):
    flat_axes = axes.flatten()
    for i, (nome_sint, col_sint) in enumerate(sintomas_map.items()):
        ax = flat_axes[i]
        if col_sint in df_filtered:
            counts = df_filtered[col_sint].value_counts(dropna=False)
            if not counts.empty:
                sns.barplot(x=counts.index,y=counts.values,hue=counts.index,ax=ax,palette="pastel",legend=False)
                ax.set_title(nome_sint,fontsize=10); ax.set_ylabel('Nº',fontsize=8)
                ax.tick_params(axis='x',rotation=30,labelsize=7,ha="right") # Rotação menor
            else: ax.text(0.5,0.5,"Sem dados",transform=ax.transAxes,ha='center',va='center')
        else: ax.text(0.5,0.5,f"Col {col_sint}\nausente",transform=ax.transAxes,ha='center',va='center')

def plot_procura_atendimento_sintomaticos(df_filtered, ax):
    req=['Febre_desc','Tosse_desc','DificuldadeRespirar_desc','PerdaOlfatoPaladar_desc','ProcurouAtendimento_desc']
    if not all(c in df_filtered for c in req): ax.text(0.5,0.5,"Cols. ausentes",transform=ax.transAxes); return
    df_c=df_filtered.copy(); df_c['Sintoma']=((df_c['Febre_desc']=='Sim')|(df_c['Tosse_desc']=='Sim')|
    (df_c['DificuldadeRespirar_desc']=='Sim')|(df_c['PerdaOlfatoPaladar_desc']=='Sim'))
    df_s=df_c[df_c['Sintoma']==True]
    if not df_s.empty:
        cts=df_s['ProcurouAtendimento_desc'].value_counts(dropna=False)
        if not cts.empty: sns.barplot(x=cts.index,y=cts.values,hue=cts.index,palette="Set2",ax=ax,legend=False); ax.set_title('Procura Atend. (Sintom.)',fontsize=11)
        else: ax.text(0.5,0.5,"Sem dados procura",transform=ax.transAxes,ha='center',va='center')
    else: ax.text(0.5,0.5,"Sem sintomáticos",transform=ax.transAxes,ha='center',va='center')

def plot_internacao_sintomaticos_atendimento(df_filtered, ax):
    req=['Febre_desc','Tosse_desc','DificuldadeRespirar_desc','PerdaOlfatoPaladar_desc','ProcurouAtendimento_desc','InternadoHospital_desc']
    if not all(c in df_filtered for c in req): ax.text(0.5,0.5,"Cols. ausentes",transform=ax.transAxes); return
    df_c=df_filtered.copy(); df_c['Sintoma']=((df_c['Febre_desc']=='Sim')|(df_c['Tosse_desc']=='Sim')|
    (df_c['DificuldadeRespirar_desc']=='Sim')|(df_c['PerdaOlfatoPaladar_desc']=='Sim'))
    df_sa=df_c[(df_c['Sintoma']==True)&(df_c['ProcurouAtendimento_desc']=='Sim')]
    if not df_sa.empty:
        cts=df_sa['InternadoHospital_desc'].value_counts(dropna=False)
        if not cts.empty: sns.barplot(x=cts.index,y=cts.values,hue=cts.index,palette="coolwarm",ax=ax,legend=False); ax.set_title('Internação (Sintom. c/ Atend.)',fontsize=11)
        else: ax.text(0.5,0.5,"Sem dados internação",transform=ax.transAxes,ha='center',va='center')
    else: ax.text(0.5,0.5,"Sem dados p/ análise",transform=ax.transAxes,ha='center',va='center')

def plot_situacao_trabalho(df_filtered, ax):
    if 'Trabalhou_desc' not in df_filtered: ax.text(0.5,0.5,"'Trab_desc' ausente",transform=ax.transAxes); return
    cts=df_filtered['Trabalhou_desc'].value_counts(dropna=False)
    if not cts.empty: ax.pie(cts,labels=cts.index,autopct='%1.1f%%',startangle=90,wedgeprops={"edgecolor":"black"},textprops={'fontsize':8}); ax.set_title('Trabalhou na Semana?',fontsize=11)
    else: ax.text(0.5,0.5,"Sem dados trabalho",transform=ax.transAxes,ha='center',va='center')

def plot_auxilio_emergencial(df_filtered, ax):
    if 'AuxilioEmergencial_desc' not in df_filtered: ax.text(0.5,0.5,"'Auxilio_desc' ausente",transform=ax.transAxes); return
    cts=df_filtered['AuxilioEmergencial_desc'].value_counts(dropna=False)
    if not cts.empty: sns.barplot(x=cts.index,y=cts.values,hue=cts.index,palette="YlGnBu",ax=ax,legend=False); ax.set_title('Recebeu Auxílio?',fontsize=11)
    else: ax.text(0.5,0.5,"Sem dados auxílio",transform=ax.transAxes,ha='center',va='center')

def plot_evolucao_temporal_sintomas(df_orig_temp, sintomas_map, ax):
    sint_list=[]
    for nome,col in sintomas_map.items():
        if col in df_orig_temp:
            df_c=df_orig_temp.copy()
            try: df_c['DataRef_dt']=pd.to_datetime(df_c['DataReferencia_Mes'],errors='coerce'); df_c.dropna(subset=['DataRef_dt'],inplace=True)
            except: continue
            if df_c.empty: continue
            perc=df_c.groupby('DataRef_dt')[col].value_counts(normalize=True).mul(100).unstack(fill_value=0)
            if 'Sim' in perc: sint_list.append(perc[['Sim']].rename(columns={'Sim':nome}))
    if sint_list:
        df_evo=pd.concat(sint_list,axis=1).fillna(0).sort_index()
        if not df_evo.empty:
            df_evo.plot(kind='line',marker='o',ax=ax,fontsize=7)
            ax.set_title('Evolução % Sintomas "Sim"',fontsize=11); ax.legend(title='Sintoma',fontsize=7,loc='upper left')
            ax.grid(True,ls='--',alpha=0.7); ax.tick_params(axis='x',rotation=30,labelsize=7,ha='right')
            ax.xaxis.set_major_formatter(matplotlib.ticker.FixedFormatter(df_evo.index.strftime('%m/%y'))) 
        else: ax.text(0.5,0.5,"Sem dados evol. sintomas",transform=ax.transAxes,ha='center',va='center')
    else: ax.text(0.5,0.5,"Não gerou dados evol.",transform=ax.transAxes,ha='center',va='center')

def plot_evolucao_temporal_eco(df_orig_temp, ax):
    df_c=df_orig_temp.copy()
    try: df_c['DataRef_dt']=pd.to_datetime(df_c['DataReferencia_Mes'],errors='coerce'); df_c.dropna(subset=['DataRef_dt'],inplace=True)
    except: ax.text(0.5,0.5,"Erro conv. datas",transform=ax.transAxes,ha='center',va='center'); return
    if df_c.empty: ax.text(0.5,0.5,"Sem datas válidas",transform=ax.transAxes,ha='center',va='center'); return

    evo_t=df_c.groupby('DataRef_dt')['Trabalhou_desc'].value_counts(normalize=True).mul(100).unstack(fill_value=0)
    evo_a=df_c.groupby('DataRef_dt')['AuxilioEmergencial_desc'].value_counts(normalize=True).mul(100).unstack(fill_value=0)
    idx=evo_t.index if not evo_t.empty else (evo_a.index if not evo_a.empty else pd.DatetimeIndex([]))
    if idx.empty: ax.text(0.5,0.5,"Sem dados evol. eco",transform=ax.transAxes,ha='center',va='center'); return
        
    df_ee=pd.DataFrame(index=idx)
    df_ee['% Trab (Sim)']=evo_t['Sim'] if 'Sim' in evo_t else 0
    df_ee['% Aux (Sim)']=evo_a['Sim'] if 'Sim' in evo_a else 0
    df_ee=df_ee.sort_index()

    if not df_ee.empty and isinstance(df_ee.index,pd.DatetimeIndex):
        l1,=ax.plot(df_ee.index,df_ee['% Trab (Sim)'],marker='o',c='b',label='% Trab (Sim)') # Adicionado vírgula
        ax.set_ylabel('% (Trab)',c='b',fontsize=8); ax.tick_params(axis='y',labelcolor='b',labelsize=7)
        ax2=ax.twinx()
        l2,=ax2.plot(df_ee.index,df_ee['% Aux (Sim)'],marker='x',c='r',label='% Aux (Sim)') # Adicionado vírgula
        ax2.set_ylabel('% (Aux)',c='r',fontsize=8); ax2.tick_params(axis='y',labelcolor='r',labelsize=7)
        ax.set_title('Evolução Trabalho e Auxílio',fontsize=11)
        lns=[l1,l2];labs=[l.get_label() for l in lns];ax.legend(lns,labs,loc='best',fontsize=7)
        ax.grid(True,ls='--',alpha=0.7);ax.tick_params(axis='x',rotation=30,labelsize=7,ha='right')
        ax.xaxis.set_major_formatter(matplotlib.ticker.FixedFormatter(df_ee.index.strftime('%m/%y')))
    else: ax.text(0.5,0.5,"Sem dados válidos evol. eco",transform=ax.transAxes,ha='center',va='center')

# --- Inicialização da UI ---
auth_status_placeholder = st.sidebar.empty()
client_bq = connect_to_bigquery()

if client_bq: 
    auth_status_placeholder.success("Autenticado!")
    df_pnad_original = load_data(client_bq)
    if df_pnad_original.empty:
        st.error("Falha ao carregar dados da PNAD COVID-19.")
        st.stop()
else: 
    auth_status_placeholder.error("Falha na autenticação.")
    st.stop() 

# --- Interface Streamlit ---
st.image("https://www.fiap.com.br/wp-content/uploads/2022/08/logo-fiap.svg", width=130) 
st.title("Tech Challenge: Análise PNAD COVID-19")
st.subheader("Data Analytics - Planejamento Hospitalar")
st.markdown("Análise interativa dos microdados da PNAD COVID-19 (Maio, Julho, Setembro 2020) para identificar características relevantes ao planejamento hospitalar.")

st.sidebar.image("https://www.fiap.com.br/wp-content/uploads/2022/08/logo-fiap.svg", width=80)
st.sidebar.title("Filtros")

df_pnad_para_filtros = df_pnad_original.copy() 

# Assegurar que 'DataReferencia_Mes' é string para a lógica de filtro
if 'DataReferencia_Mes' in df_pnad_para_filtros.columns and df_pnad_para_filtros['DataReferencia_Mes'].notna().any():
    df_pnad_para_filtros['DataReferencia_Mes'] = df_pnad_para_filtros['DataReferencia_Mes'].astype(str)
else: # Fallback se a coluna estiver ausente ou toda nula
    st.sidebar.warning("Coluna 'DataReferencia_Mes' ausente ou vazia para filtros.")
    df_pnad_para_filtros['DataReferencia_Mes'] = pd.Series(dtype='str')


mes_map = {"2020-05-01": "Maio/2020", "2020-07-01": "Julho/2020", "2020-09-01": "Setembro/2020"}
available_raw_months = sorted(list(df_pnad_para_filtros['DataReferencia_Mes'].unique()))
month_options_display = ["Todos"] + [mes_map.get(m, m) for m in available_raw_months if m] # Ignorar None/NaN

selected_month_display = st.sidebar.selectbox("Mês:", options=month_options_display, index=0)
selected_month_actual = "Todos"
if selected_month_display != "Todos":
    for actual_val, display_val_map in mes_map.items():
        if display_val_map == selected_month_display:
            selected_month_actual = actual_val; break 
    if selected_month_actual == "Todos" and selected_month_display in available_raw_months:
             selected_month_actual = selected_month_display

# Gerar opções de UF e Sexo a partir do DataFrame que já tem DataReferencia_Mes como string
# Isso evita problemas se essas colunas tiverem NaNs que causam erro com .unique().tolist() diretamente
all_ufs = ["Todos"] + sorted(list(df_pnad_para_filtros['uf_desc'].dropna().unique()))
selected_uf = st.sidebar.selectbox("UF:", options=all_ufs, index=0)

all_sexos = ["Todos"] + sorted(list(df_pnad_para_filtros['sexo_desc'].dropna().unique()))
selected_sexo = st.sidebar.selectbox("Sexo:", options=all_sexos, index=0)

# Aplicar Filtros
df_filtrado = df_pnad_original.copy() # Começar com o original para cada re-filtragem
# Garantir que DataReferencia_Mes seja string também em df_filtrado antes de comparar
if 'DataReferencia_Mes' in df_filtrado.columns and df_filtrado['DataReferencia_Mes'].notna().any():
    df_filtrado['DataReferencia_Mes'] = df_filtrado['DataReferencia_Mes'].astype(str)

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
    fp_txt="N/A"; ap_txt="N/A"
    if 'Febre_desc' in df_filtrado.columns and df_filtrado.shape[0]>0: fp_txt=f"{(df_filtrado[df_filtrado['Febre_desc']=='Sim'].shape[0]/df_filtrado.shape[0])*100:.1f}%"
    c2.metric("Prev. Febre ('Sim')", fp_txt)
    if 'AuxilioEmergencial_desc' in df_filtrado.columns and df_filtrado.shape[0]>0: ap_txt=f"{(df_filtrado[df_filtrado['AuxilioEmergencial_desc']=='Sim'].shape[0]/df_filtrado.shape[0])*100:.1f}%"
    c3.metric("% c/ Auxílio ('Sim')", ap_txt)
else: st.info("Nenhum dado para os filtros selecionados.")

# --- Layout Principal com Seções ---
if not df_filtrado.empty:
    st.markdown("---"); st.header("Perfil Demográfico e Socioeconômico")
    # DESCOMENTE AS SEGUINTES SEÇÕES DE PLOTAGEM UMA POR UMA PARA TESTAR
    
    # SEÇÃO 1: Demográficos
    try:
        fig1,ax1=plt.subplots(1,2,figsize=(12,3.5)); 
        safe_plot(plot_distribuicao_uf, df_filtrado, ax1[0]); 
        safe_plot(plot_distribuicao_idade, df_filtrado, ax1[1])
        plt.tight_layout(pad=0.5); st.pyplot(fig1); plt.close(fig1)

        fig2,ax2=plt.subplots(1,3,figsize=(15,3.5)); 
        safe_plot(plot_distribuicao_sexo, df_filtrado, ax2[0]); 
        safe_plot(plot_distribuicao_escolaridade, df_filtrado, ax2[1]); 
        safe_plot(plot_distribuicao_rendimento, df_filtrado, ax2[2])
        plt.tight_layout(pad=0.5); st.pyplot(fig2); plt.close(fig2)
    except Exception as e: st.error(f"Erro ao renderizar gráficos demográficos: {e}")


    st.markdown("---"); st.header("Análise Clínica dos Sintomas e Procura por Atendimento")
    sint_map={'Febre':'Febre_desc','Tosse':'Tosse_desc','Dif.Respirar':'DificuldadeRespirar_desc','Olfato/Paladar':'PerdaOlfatoPaladar_desc'}
    # SEÇÃO 2: Clínicos
    try:
        fig3,ax3=plt.subplots(2,2,figsize=(10,7)); 
        safe_plot(plot_prevalencia_sintomas, df_filtrado, ax3, sintomas_map=sint_map, axes=ax3) # Passar axes para safe_plot
        # fig3.suptitle('Prevalência Sintomas',fontsize=16,y=1.02); # Suptitle pode causar problemas
        plt.tight_layout(pad=0.5, rect=[0,0,1,0.95]); st.pyplot(fig3); plt.close(fig3)

        fig4,ax4=plt.subplots(1,2,figsize=(12,3.5)); 
        safe_plot(plot_procura_atendimento_sintomaticos, df_filtrado, ax4[0]); 
        safe_plot(plot_internacao_sintomaticos_atendimento, df_filtrado, ax4[1])
        plt.tight_layout(pad=0.5); st.pyplot(fig4); plt.close(fig4)
    except Exception as e: st.error(f"Erro ao renderizar gráficos clínicos: {e}")


    st.markdown("---"); st.header("Impacto Econômico e Auxílios")
    # SEÇÃO 3: Econômicos
    try:
        fig5,ax5=plt.subplots(1,2,figsize=(12,4)); 
        safe_plot(plot_situacao_trabalho, df_filtrado, ax5[0]); 
        safe_plot(plot_auxilio_emergencial, df_filtered, ax5[1]) # df_filtered aqui
        plt.tight_layout(pad=0.5); st.pyplot(fig5); plt.close(fig5)
    except Exception as e: st.error(f"Erro ao renderizar gráficos econômicos: {e}")


    st.markdown("---"); st.header("Análise Temporal (Evolução Mensal)")
    st.markdown("*Filtros de UF/Sexo aplicados; Mês ignorado para estes gráficos.*")
    df_temp=df_pnad_original.copy() 
    if selected_uf!="Todos": df_temp=df_temp[df_temp['uf_desc']==selected_uf]
    if selected_sexo!="Todos": df_temp=df_temp[df_temp['sexo_desc']==selected_sexo]
    
    # SEÇÃO 4: Temporais
    if not df_temp.empty:
        try:
            fig6,ax6=plt.subplots(1,2,figsize=(15,4.5)); 
            safe_plot(plot_evolucao_temporal_sintomas, df_temp, ax6[0], sintomas_para_temporal=sint_map)
            safe_plot(plot_evolucao_temporal_eco, df_temp, ax6[1])
            plt.tight_layout(pad=0.5); st.pyplot(fig6); plt.close(fig6)
        except Exception as e: st.error(f"Erro ao renderizar gráficos temporais: {e}")
    else: st.info("Sem dados para gráficos temporais com filtros UF/Sexo aplicados.")

else:
    if client_bq: st.info("Nenhum dado para os filtros selecionados. Tente outra combinação.")

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
