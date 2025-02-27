# app/modules/analysis.py
import os
from datetime import datetime
from dotenv import load_dotenv
import json

from langchain_openai import ChatOpenAI
from app.database.supabase_api import insert_data, select_data

def load_environment():
    """Carga las variables de entorno desde el archivo .env"""
    dotenv_path = os.path.join(os.path.dirname(__file__), "../../../.env")
    load_dotenv(dotenv_path)

    if not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_SERVICE_ROLE_KEY"):
        raise ValueError("Missing Supabase URL or Service Role Key in environment variables.")

# Cargar las variables
load_environment()

# Configuramos el modelo GPT-4
chat = ChatOpenAI(model_name="gpt-4", temperature=0.5)

def get_completed_meetings(email: str):
    """
    Obtiene las reuniones donde un usuario con 'email' ya respondió al menos una pregunta.
    (Opcionalmente puedes filtrar solo las completadas si lo deseas).
    """
    user_data = select_data("user", {"email": email})
    if not user_data.data:
        return None

    user_id = user_data.data[0]["id_user"]

    # Buscar answers por ese usuario
    answers_response = select_data("answers", {"id_user": user_id})
    if not answers_response.data:
        return None

    # Reuniones en las que ha respondido
    meeting_ids = list({a["id_meeting"] for a in answers_response.data})
    meetings_response = select_data("meetings", {"id_meeting": meeting_ids})
    if not meetings_response.data:
        return None

    return meetings_response.data

def get_meeting_analysis(meeting_id: str) -> str:
    """
    Construye el contexto con:
    - El tema de la reunión
    - Las preguntas y sus respuestas
    Retorna un texto largo (string) que se le pasará a GPT.
    """
    questions_response = select_data("questions", {"id_meeting": meeting_id})
    answers_response   = select_data("answers",   {"id_meeting": meeting_id})
    users_response     = select_data("user")
    meeting_info       = select_data("meetings",  {"id_meeting": meeting_id}).data

    if (not questions_response.data or
        not answers_response.data or
        not meeting_info):
        # Falta info o no hay nada
        return ""

    topic = meeting_info[0]["topic"]

    # Construimos el texto
    context = f"""
    Tema de la reunión: {topic}

    Preguntas y respuestas de los asistentes:
    """

    # Mapeo id_user -> email
    user_map = {u["id_user"]: u["email"] for u in users_response.data} if users_response.data else {}

    for q in questions_response.data:
        context += f"\nPregunta: {q['content']}\n"
        # Filtrar answers
        q_answers = [a for a in answers_response.data if a["id_question"] == q["id_question"]]
        if q_answers:
            for ans in q_answers:
                user_email = user_map.get(ans["id_user"], "Usuario desconocido")
                context += f"Respuesta de {user_email}: {ans['content']}\n"
        else:
            context += "Sin respuesta registrada.\n"

    return context

def analyze_meeting(context: str, meeting_id: str):
    """
    Llama a GPT-4 con 'context' para ver si la reunión es necesaria.
    Guarda en 'results' la conclusión completa (campo 'conclusions') y un boolean en 'analysis'.
    """
    if not context:
        return {
            "conclusions": "No hay suficiente información para analizar esta reunión.",
            "analysis": False
        }

    prompt = f"""
    Eres un asistente especializado en optimización de reuniones.
    Se te proporciona el contexto de una reunión, incluyendo su tema, preguntas y respuestas de los participantes:
    {context}
    Tu tarea es analizar la información y decidir si la reunión es realmente necesaria. Para ello:
    1. Indica explícitamente si la reunión es necesaria con `"is_meeting_needed": "Sí"` o `"is_meeting_needed": "No"`.
    2. Proporciona un análisis detallado en `"conclusions"`, explicando los motivos de tu decisión.
    3. Identifica puntos críticos o desacuerdos si existen.
    4. Sugiere alternativas si la reunión no es necesaria.

    Devuelve la respuesta en **estricto formato JSON** con la siguiente estructura:
    ```json
    {{
        "is_meeting_needed": "Sí" o "No",
        "conclusions": "Explicación detallada aquí"
    }}
    """


    response = chat.invoke(prompt)

    try:
        # Intentar convertir la respuesta en JSON
        response_json = json.loads(response.content)

        # Extraer valores del JSON
        is_needed = response_json.get("is_meeting_needed", "No") == "Sí"  # Convertir "Sí"/"No" en True/False
        conclusions = response_json.get("conclusions", "No se pudo generar una conclusión.")

    except json.JSONDecodeError:
        # Si hay un error en el formato JSON, asumimos que la reunión NO es necesaria
        is_needed = False
        conclusions = "Error en el análisis de la reunión. Intenta de nuevo."

        # Guardar en DB
    result_data = {
        "id_meeting": meeting_id,
        "conclusions": conclusions,  # Guardamos la conclusión exacta
        "analysis": is_needed,  # Guardamos el booleano correcto
        "created_at": datetime.utcnow().isoformat(),
    }
    insert_data("results", result_data)

    return {
        "conclusions": conclusions,
        "analysis": is_needed
    }

