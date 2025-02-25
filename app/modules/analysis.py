# /modules/analysis.py
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from app.database.supabase_api import insert_data, select_data

import os
from datetime import datetime

def load_environment():
    """Carga las variables de entorno desde el archivo .env"""
    dotenv_path = os.path.join(os.path.dirname(__file__), "../../../.env")
    load_dotenv(dotenv_path)

    if not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_SERVICE_ROLE_KEY"):
        raise ValueError("Missing Supabase URL or Service Role Key in environment variables.")

# Cargar variables de entorno
load_environment()

# Configurar el modelo de análisis con GPT-4
chat = ChatOpenAI(model_name="gpt-4", temperature=0.5)

def get_completed_meetings(email):
    """Obtiene las reuniones en las que el usuario ya ha respondido preguntas."""
    user_data = select_data("user", {"email": email})
    if not user_data.data:
        print("❌ Usuario no encontrado.")
        return None
    user_id = user_data.data[0]["id_user"]

    # Obtener reuniones donde el usuario tiene respuestas registradas
    answers_response = select_data("answers", {"id_user": user_id})
    if not answers_response.data:
        print("❌ No hay reuniones con respuestas para este usuario.")
        return None

    # Obtener información de las reuniones usando una consulta "in"
    meeting_ids = list({a["id_meeting"] for a in answers_response.data})
    meetings_response = select_data("meetings", {"id_meeting": meeting_ids})
    if not meetings_response.data:
        print("❌ No se encontraron detalles de las reuniones.")
        return None

    return meetings_response.data

def get_meeting_analysis(meeting_id):
    """Obtiene todas las respuestas de una reunión para su análisis."""
    questions_response = select_data("questions", {"id_meeting": meeting_id})
    answers_response = select_data("answers", {"id_meeting": meeting_id})
    users_response = select_data("user")

    if not questions_response.data or not answers_response.data:
        print("❌ No hay suficientes datos para analizar esta reunión.")
        return None

    topic = select_data("meetings", {"id_meeting": meeting_id}).data[0]["topic"]

    # Construir contexto para GPT-4
    context = f"""
    Tema de la reunión: {topic}

    Preguntas y respuestas de los asistentes:
    """

    user_names = {user["id_user"]: user["email"] for user in users_response.data}

    for question in questions_response.data:
        context += f"\nPregunta: {question['content']}\n"
        related_answers = [a for a in answers_response.data if a["id_question"] == question["id_question"]]

        if related_answers:
            for ans in related_answers:
                user_email = user_names.get(ans['id_user'], 'Usuario desconocido')
                context += f"Respuesta de {user_email}: {ans['content']}\n"
        else:
            context += "Sin respuesta registrada.\n"

    return context

def analyze_meeting(context, meeting_id):
    """Envía el contexto a GPT-4 y obtiene un análisis sobre la necesidad de la reunión."""
    prompt = f"""
    Eres un asistente especializado en la optimización de reuniones. Se te proporciona información de una reunión con preguntas y respuestas recopiladas de los asistentes.
    Tu tarea es analizar la información y determinar:
    1. Si la reunión es necesaria o si ya hay consenso suficiente.
    2. Identificar puntos críticos o desacuerdos que justifiquen la reunión.
    3. Sugerencias para mejorar la toma de decisiones sin una reunión innecesaria.

    Información de la reunión:
    {context}

    Proporciona tu análisis detallado.
    """
    response = chat.invoke(prompt)

    # Determinar si la reunión es necesaria
    is_meeting_needed = "sí" in response.content.lower() or "necesaria" in response.content.lower()

    # Guardar el análisis en la base de datos
    result_data = {
        "id_meeting": meeting_id,
        "conclusions": response.content,
        "created_at": datetime.utcnow().isoformat(),
        "analysis": is_meeting_needed
    }
    insert_data("results", result_data)

    return response.content

def run_analysis():
    """Ejecuta el análisis del módulo 3."""
    print("\n🟢 Bienvenido al Módulo 3: Análisis de Reuniones con IA 🟢")
    email = input("Ingresa tu correo: ").strip()

    meetings = get_completed_meetings(email)
    if not meetings:
        return

    print("\n📅 Reuniones en las que has respondido:")
    for idx, meeting in enumerate(meetings, start=1):
        print(f"{idx}. {meeting['topic']} (ID: {meeting['id_meeting']})")

    while True:
        try:
            choice = int(input("\nSelecciona el número de la reunión para analizar: "))
            if 1 <= choice <= len(meetings):
                selected_meeting = meetings[choice - 1]
                break
            else:
                print("⚠️ Número fuera de rango. Inténtalo de nuevo.")
        except ValueError:
            print("⚠️ Entrada inválida. Ingresa un número válido.")

    meeting_context = get_meeting_analysis(selected_meeting["id_meeting"])
    if not meeting_context:
        return

    print("\n🔍 Enviando información a GPT-4 para análisis...")
    analysis_result = analyze_meeting(meeting_context, selected_meeting["id_meeting"])

    print("\n📊 Análisis de GPT-4:")
    print(analysis_result)

if __name__ == "__main__":
    run_analysis()
