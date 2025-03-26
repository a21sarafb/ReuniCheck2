# ReuniCheck - Manual de Usuario y Despliegue

## Descripción general

ReuniCheck es un sistema que ayuda a determinar si una reunión es realmente necesaria y, en caso afirmativo, organiza la reunión de manera eficiente. El sistema se compone de una interfaz web construida con Streamlit y un backend API desarrollado con FastAPI, utilizando Supabase como base de datos.

## Características principales

- **Creación de usuarios** para participar en reuniones
- **Generación automática de reuniones** con preguntas relevantes basadas en el tema
- **Respuesta a preguntas** asociadas a reuniones
- **Chat con IA** para profundizar en las respuestas
- **Análisis automático** para determinar si una reunión es necesaria

## Estructura del proyecto

```
/
├── app/                    # Código del backend API (FastAPI)
│   ├── database/           # Configuración y controladores de la base de datos
│   ├── models/             # Modelos de datos
│   ├── modules/            # Módulos funcionales
│   ├── routers/            # Endpoints de la API
│   ├── app.py              # Punto de entrada del backend
│   └── main.py             # Configuración principal de FastAPI
├── img/                    # Imágenes para documentación
├── app.py                  # Aplicación frontend (Streamlit)
├── requirements.txt        # Dependencias del proyecto
├── Dockerfile              # Para despliegue en contenedor
├── Dockerfile.backend      # Para despliegue separado del backend
├── Dockerfile.frontend     # Para despliegue separado del frontend
└── .env                    # Variables de entorno (no incluir en control de versiones)
```

## Requisitos previos

- Python 3.12 o superior
- Cuenta en [Supabase](https://supabase.com) para la base de datos
- Clave de API de OpenAI (para las funcionalidades de IA)
- Git (opcional, para clonar el repositorio)

## Configuración del entorno

1. Clona el repositorio:
   ```bash
   git clone <url-del-repositorio>
   cd ReuniCheck
   ```

2. Crea un entorno virtual:
   ```bash
   python -m venv venv
   ```

3. Activa el entorno virtual:
   - En Windows:
     ```bash
     venv\Scripts\activate
     ```
   - En macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

4. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```

5. Crea un archivo `.env` en la raíz del proyecto con las siguientes variables:
   ```
   OPENAI_API_KEY=tu_clave_de_api_de_openai
   SUPABASE_URL=tu_url_de_supabase
   SUPABASE_SERVICE_ROLE_KEY=tu_clave_de_servicio_de_supabase
   ```

## Despliegue local

### Opción 1: Ejecución separada (recomendada para desarrollo)

1. Inicia el backend (FastAPI):
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
   ```

2. En una terminal separada, inicia el frontend (Streamlit):
   ```bash
   streamlit run app.py
   ```

3. Accede a:
   - Frontend (Streamlit): http://localhost:8501
   - API (Swagger UI): http://localhost:8080/docs

### Opción 2: Ejecución con Docker

1. Construye la imagen:
   ```bash
   docker build -t reunicheck:latest .
   ```

2. Ejecuta el contenedor:
   ```bash
   docker run -p 8501:8501 -p 8080:8080 \
     -e OPENAI_API_KEY=tu_clave_de_api_de_openai \
     -e SUPABASE_URL=tu_url_de_supabase \
     -e SUPABASE_SERVICE_ROLE_KEY=tu_clave_de_servicio_de_supabase \
     reunicheck:latest
   ```

3. Accede a:
   - Frontend (Streamlit): http://localhost:8501
   - API (Swagger): http://localhost:8080/docs

## Uso básico

1. **Crear un usuario**: 
   - Ve a la pestaña "Crear usuario" 
   - Completa tu nombre y correo electrónico

2. **Crear una reunión**:
   - Ve a la pestaña "Crear reunión"
   - Define el tema de la reunión
   - Selecciona los participantes
   - Haz clic en "Crear reunión"

3. **Responder preguntas**:
   - Ve a la pestaña "Contestar preguntas"
   - Ingresa tu correo electrónico
   - Selecciona una reunión
   - Responde a las preguntas pendientes

4. **Usar el chat**:
   - Ve a la pestaña "Chat"
   - Ingresa tu correo electrónico
   - Selecciona una reunión con preguntas respondidas
   - Interactúa con la IA para profundizar en tus respuestas

5. **Obtener análisis**:
   - Ve a la pestaña "Obtener análisis"
   - Selecciona la reunión para analizar
   - Revisa las conclusiones sobre si la reunión es necesaria

## Solución de problemas

- **Error de conexión a Supabase**: Verifica que las credenciales en el archivo `.env` sean correctas.
- **Error al instalar dependencias**: Asegúrate de tener Python 3.12 o superior.
- **El frontend no puede conectar con el backend**: Verifica que ambos servicios estén ejecutándose y que el puerto 8080 esté accesible.

## Estructura de la base de datos en Supabase

La aplicación utiliza las siguientes tablas en Supabase:
- `users`: Almacena información de los usuarios
- `meetings`: Reuniones creadas en el sistema
- `questions`: Preguntas generadas para cada reunión
- `answers`: Respuestas proporcionadas por los usuarios
- `meeting_users`: Relación entre reuniones y usuarios

## Contribuir al proyecto

1. Crea un fork del repositorio
2. Crea una rama para tu funcionalidad (`git checkout -b feature/nueva-funcionalidad`)
3. Haz commit de tus cambios (`git commit -am 'Añade nueva funcionalidad'`)
4. Haz push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crea un Pull Request

## Tecnologías utilizadas

- **Frontend**: Streamlit
- **Backend**: FastAPI
- **Base de datos**: Supabase (PostgreSQL)
- **IA**: OpenAI API
- **Contenedorización**: Docker

[![Made with Supabase](https://supabase.com/badge-made-with-supabase-dark.svg)](https://supabase.com) 