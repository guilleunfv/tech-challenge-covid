## Despliegue rápido – Dashboard Streamlit / Cloud Run

> Proyecto **tech-chalenge-covid** · Región **southamerica‑east1**
>
> Cuenta de servicio: `streamlit-pnad-sa@tech-chalenge-covid.iam.gserviceaccount.com`

---

### 1. `requirements.txt`

```txt
streamlit==1.36.0

google-cloud-bigquery==3.33.0
google-cloud-bigquery-storage>=2.24

pandas>=2.2,<3
numpy>=2.0,<3
pyarrow>=13.0.0
db-dtypes==1.4.3

matplotlib==3.9.0
seaborn==0.13.2
```

### 2. `Dockerfile`

```dockerfile
FROM python:3.11-slim
WORKDIR /app

RUN pip install --upgrade pip setuptools wheel
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHERUSAGESTATS=false

EXPOSE 8501
CMD ["streamlit", "run", "app.py"]
```

### 3. Build de la imagen

```powershell
gcloud builds submit --tag gcr.io/tech-chalenge-covid/streamlit-pnad-covid:v3
```

### 4. Deploy en Cloud Run  (PowerShell)

```powershell
gcloud run deploy streamlit-pnad `
  --image gcr.io/tech-chalenge-covid/streamlit-pnad-covid:v3 `
  --region southamerica-east1 `
  --memory 2Gi `
  --port 8501 `
  --allow-unauthenticated `
  --service-account streamlit-pnad-sa@tech-chalenge-covid.iam.gserviceaccount.com
```

### 5. URL

El comando mostrará algo como:

```
Service URL: [https://streamlit-pnad-<hash>.run.app](https://streamlit-pnad-272178542851.southamerica-east1.run.app/)
```

¡Abre esa URL y listo!
