# Tech Challenge - Fase 03: Análise de Dados da PNAD COVID-19

## Autores
Guillermo Jesus Camahuali Privat
Kelly Priscilla Matos Campos
Rosicleia Cavalcante Mota

## Visão Geral do Projeto
Este projeto analisa os microdados da pesquisa PNAD COVID-19 do IBGE para os meses de Maio, Julho e Setembro de 2020. O objetivo é entender o comportamento da população durante a pandemia, identificar características clínicas, socioeconômicas e comportamentais relevantes e, por fim, propor indicadores e ações que possam auxiliar um hospital no planejamento para futuros surtos de doenças infecciosas. A análise foca em aproximadamente 20 variáveis chave da pesquisa.

## Objetivos Principais
1.  Identificar indicadores para planejamento hospitalar em caso de novo surto.
2.  Analisar características clínicas, comportamento populacional e aspectos econômicos.
3.  Estruturar e processar a base de dados utilizando Google Cloud Platform.
4.  Desenvolver um dashboard interativo para visualização dos resultados, implantado no Google Cloud Run.

## Tecnologias Utilizadas
- **Google Cloud Platform (GCP)**
  - **Google Cloud Storage (GCS):** Armazenamento inicial dos arquivos CSV.
    - Bucket: `tech-chalenge-covid-dados`
  - **Google BigQuery:** Data Warehouse para armazenamento, processamento, transformação e análise dos dados.
    - ID do Projeto GCP: `` `tech-chalenge-covid` ``
    - Localização dos Conjuntos de Dados: `southamerica-east1`
    - Conjuntos de Dados: `pnad_covid_raw`, `pnad_covid_dominios`, `pnad_covid_processed`.
    - Tabela Analítica Principal: `` `tech-chalenge-covid`.pnad_covid_processed.pnad_covid_analitica_consolidada ``
  - **Vertex AI Workbench (JupyterLab):** Ambiente para análise exploratória de dados (AED) com Python.
  - **Artifact Registry (ou Google Container Registry - GCR):** Para armazenamento das imagens Docker da aplicação Streamlit.
  - **Google Cloud Build:** Para automatizar o build das imagens Docker.
  - **Google Cloud Run:** Para implantar e servir a aplicação Streamlit de forma serverless.
    - Conta de Serviço da Aplicação: `streamlit-pnad-sa@tech-chalenge-covid.iam.gserviceaccount.com`
- **Python 3:** Linguagem principal para análise e desenvolvimento da aplicação Streamlit.
  - **Bibliotecas Principais (ver `app_streamlit/requirements.txt` para versões exatas):** Pandas, NumPy, google-cloud-bigquery, Streamlit, Matplotlib, Seaborn, PyArrow, db-dtypes, Statsmodels, pmdarima, Prophet.
- **SQL (GoogleSQL):** Para manipulação e transformação de dados no BigQuery.
- **Docker:** Para conteinerizar a aplicação Streamlit para deploy no Cloud Run.

## Estrutura do Repositório
- `README.md`: Este arquivo.
- `/notebooks/AnalisePNADCovid.ipynb`: Notebook Jupyter com a análise exploratória de dados detalhada.
- `/scripts_sql/`: Scripts SQL para criar a estrutura e processar os dados no BigQuery.
  - `01_criacao_datasets_raw_dominios.sql`
  - `02_criacao_tabelas_dominio.sql`
  - `03_criacao_tabelas_processadas.sql`
  - `04_criacao_tabela_consolidada.sql`
- `/app_streamlit/`: Contém os arquivos da aplicação Streamlit.
  - `app.py`: O script principal da aplicação Streamlit.
  - `requirements.txt`: As dependências Python para a aplicação Streamlit.
  - `Dockerfile`: Instruções para construir a imagem Docker da aplicação.
- `(Opcional) /imagens_relatorio/`: Imagens estáticas de gráficos para este README.

## Metodologia e Fluxo de Trabalho
1.  **Configuração do Ambiente GCP:** Criação do projeto, bucket GCS.
2.  **Ingestão de Dados Brutos:** Upload dos CSVs da PNAD e dicionários para o GCS.
3.  **Criação da Camada Raw no BigQuery:** Carregamento dos CSVs para tabelas brutas.
4.  **Criação das Tabelas de Domínio:** Definição e população das tabelas de dimensão para decodificar variáveis.
5.  **Criação da Camada Processada:** Geração das tabelas mensais processadas, selecionando variáveis chave, juntando com domínios e tratando valores ausentes.
6.  **Consolidação dos Dados:** Criação da tabela analítica unificada `pnad_covid_analitica_consolidada`.
7.  **Análise Exploratória de Dados (AED):** Utilização do notebook Jupyter no Vertex AI Workbench para análises estatísticas e geração de visualizações.
8.  **Desenvolvimento da Aplicação Streamlit:** Criação do script `app.py` para apresentar os principais insights de forma interativa.
9.  **Conteinerização e Deploy:**
    - Criação de um `Dockerfile` para a aplicação Streamlit.
    - Build da imagem Docker usando Google Cloud Build e armazenamento no GCR/Artifact Registry.
    - Implantação (Deploy) da imagem no Google Cloud Run, configurando a conta de serviço para acesso ao BigQuery e permitindo acesso não autenticado.

## Dashboard Interativo Público (Streamlit no Cloud Run)
Acesse o dashboard interativo através do seguinte link:
https://streamlit-pnad-272178542851.southamerica-east1.run.app/

## Análise Detalhada no Notebook
Para visualizar o processo completo de análise exploratória de dados, o código Python, as explicações detalhadas e os gráficos gerados no ambiente de desenvolvimento, acesse o notebook Jupyter:
https://github.com/guilleunfv/tech-challenge-covid/blob/main/notebooks/AnalisePNADCovid.ipynb

## Instruções para Deploy (Resumido)
A aplicação Streamlit é implantada no Google Cloud Run. Os passos principais são:

1.  **`requirements.txt` para a aplicação Streamlit:**
    ```txt
    streamlit==1.36.0
    google-cloud-bigquery==3.22.0  # Ajuste a versão conforme seu requirements.txt final
    google-cloud-bigquery-storage>=2.24.0 # Ajuste
    pandas>=2.2,<3
    numpy>=1.26,<2 # Ajuste para compatibilidade com pandas 2.2
    pyarrow>=13.0.0
    db-dtypes>=1.2.0 # Ajuste
    matplotlib==3.9.0 # Ajuste
    seaborn==0.13.2 # Ajuste
    # Adicione statsmodels, pmdarima, prophet se usados no app.py
    ```
    *(Nota: Verifiquei as versões das bibliotecas que você listou e fiz pequenos ajustes para compatibilidade mais comum, como `numpy<2` com `pandas>=2.2`. Você deve usar as versões exatas do seu `requirements.txt` final que funcionaram para você).*

2.  **`Dockerfile` para a aplicação Streamlit:**
    ```dockerfile
    FROM python:3.11-slim # Ou a versão Python que você usou para desenvolver
    WORKDIR /app

    RUN pip install --upgrade pip setuptools wheel
    COPY requirements.txt .
    RUN pip install --no-cache-dir -r requirements.txt

    COPY ./app_streamlit /app # Copia o conteúdo da pasta app_streamlit para /app no contêiner

    ENV STREAMLIT_SERVER_PORT=8501 \
        STREAMLIT_SERVER_HEADLESS=true \
        STREAMLIT_BROWSER_GATHERUSAGESTATS=false

    EXPOSE 8501
    # Se app.py está na raiz da pasta app_streamlit que foi copiada para /app
    CMD ["streamlit", "run", "app.py"]
    ```
    *(Ajuste `COPY ./app_streamlit /app` se seu `app.py` estiver na raiz do repositório e não em uma subpasta `app_streamlit` no build context).*

3.  **Build da Imagem Docker (usando Cloud Build):**
    (Execute na pasta raiz do seu repositório local, onde o Dockerfile está)
    ```powershell
    gcloud builds submit --tag gcr.io/tech-chalenge-covid/streamlit-pnad-covid:vX # Substitua vX pela versão
    ```
    *(Se você colocou o Dockerfile e requirements.txt dentro da pasta `app_streamlit/`, você precisará executar o comando `gcloud builds submit` de dentro dessa pasta, ou ajustar o contexto do build).*

4.  **Deploy no Cloud Run:**
    ```powershell
    gcloud run deploy streamlit-pnad `
      --image gcr.io/tech-chalenge-covid/streamlit-pnad-covid:vX ` # Substitua vX
      --region southamerica-east1 `
      --memory 2Gi ` # Ajuste a memória conforme necessário
      --cpu 1 ` # Ajuste a CPU conforme necessário
      --port 8501 ` # Porta que o contêiner expõe
      --allow-unauthenticated `
      --service-account streamlit-pnad-sa@tech-chalenge-covid.iam.gserviceaccount.com
    ```

