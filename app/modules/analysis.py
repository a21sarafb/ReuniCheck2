# app/modules/analysis.py
import os
from datetime import datetime
from dotenv import load_dotenv

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
    Debes analizar el tema y las respuestas para decidir si realmente se necesita o no la reunión:
    {context}

    1. Indica si la reunión es necesaria o no.
    2. Identifica puntos críticos o desacuerdos.
    3. Propón sugerencias para no tener una reunión innecesaria.
    """

    response = chat.invoke(prompt)

    # Definir si es necesaria
    is_needed = ("sí" in response.content.lower() or "necesaria" in response.content.lower())

    # Guardar en DB
    result_data = {
        "id_meeting": meeting_id,
        "conclusions": response.content,
        "analysis": is_needed,
        "created_at": datetime.utcnow().isoformat(),
    }
    insert_data("results", result_data)

    return {
        "conclusions": response.content,
        "analysis": is_needed
    }
