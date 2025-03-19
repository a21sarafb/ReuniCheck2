# Usa la imagen oficial de Python 3.12
FROM python:3.12-slim

# Establece el directorio de trabajo en /app
WORKDIR /app

# Copia los archivos de requisitos
COPY requirements.txt ./

# Instala las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copia el código de la aplicación al contenedor
COPY . /app
#COPY . .

# Establece las variables de entorno necesarias (se pasarán en el `docker run`)
ENV PORT=8080
ENV API_BASE_URL=https://reunicheck-service-48606537894.us-central1.run.app
ARG SUPABASE_URL
ARG SUPABASE_SERVICE_ROLE_KEY
ARG OPENAI_API_KEY

# Expone el puerto en el que correrá FastAPI
EXPOSE 8080
EXPOSE 8501

# Comando para ejecutar la aplicación con Uvicorn
# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
# CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
#CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port 8080 & streamlit run app.py --server.port 8501 --server.address 0.0.0.0"]
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port 8080 & sleep 5 && streamlit run app.py --server.port 8501 --server.address 0.0.0.0"]