# tech-challenge-covid

---

## 📦 Archivos grandes con Git LFS

Este repositorio utiliza [Git LFS](https://git-lfs.github.com/) para manejar archivos `.csv` grandes provenientes de la base PNAD COVID-19.

Asegúrate de tener Git LFS instalado antes de clonar o hacer pull del repositorio, usando los siguientes comandos:

```bash
git lfs install
git clone https://github.com/guilleunfv/tech-challenge-covid.git

Si no tienes Git LFS instalado, los archivos .csv no se descargarán correctamente.

Los archivos grandes están ubicados en la carpeta:
/data/raw/

Incluyen:

PNAD_COVID_052020.csv

PNAD_COVID_072020.csv

PNAD_COVID_092020.csv

## ✅ PASO 3: Guarda el archivo

Simplemente **guarda** los cambios en el editor.

---

## ✅ PASO 4: Haz commit y push a GitHub

Abre Git Bash en la carpeta del repositorio y ejecuta:

```bash
cd ~/OneDrive/Documentos/GitHub/tech-challenge-covid

git add README.md
git commit -m "Actualiza README con instrucciones de Git LFS"
git push origin main

