from fastapi import APIRouter, HTTPException
from app.modules.chat_generator import conversation
from app.database.supabase_api import select_data, insert_data
from app.models.schemas import ChatRequest, ChatResponse, ChatStartRequest
from typing import List

router = APIRouter(prefix="/chat", tags=["Chat"])

@router.post("/start")
def start_chat(request: ChatStartRequest):
    """
    Inicia el chat verificando qué reuniones tiene el usuario y permite seleccionar una.
    """

    user_email = request.user_email

    # Verificar usuario en la base de datos
    user_response = select_data("user", {"email": user_email})

    if not user_response.data:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    user_id = user_response.data[0]["id_user"]

    # Obtener reuniones asignadas al usuario
    meetings_response = select_data("meetings", {"id_user": user_id})

    if not meetings_response.data:
        raise HTTPException(status_code=404, detail="No tienes reuniones asignadas.")

    meetings = [{"id_meeting": m["id_meeting"], "topic": m["topic"]} for m in meetings_response.data]

    return {
        "message": "Reuniones disponibles",
        "meetings": meetings,  # la lista de reuniones
        "user_id": user_id  #  user_id
    }

@router.post("/conversation")
def chat_with_bot(request: ChatRequest):
    """
    Maneja la conversación del usuario con el chatbot.
    - Pregunta las preguntas pendientes de la reunión seleccionada.
    - Guarda las respuestas en la base de datos.
    - Continúa la conversación con GPT hasta que el usuario quiera finalizar.
    """

    id_user = request.id_user
    id_meeting = request.id_meeting

    # Obtener preguntas pendientes
    questions_response = select_data("questions", {"id_meeting": id_meeting, "id_user": id_user})

    if not questions_response.data:
        return {"message": "No hay preguntas asignadas a esta reunión."}

    questions = [{"id_question": q["id_question"], "content": q["content"]} for q in questions_response.data]

    # Iniciar conversación en memoria
    session_id = f"user_{id_user}_meeting_{id_meeting}"
    responses = []

    for q in questions:
        responses.append({"question": q["content"], "answer": request.user_response})

        # Guardar respuesta en la base de datos
        answer_data = {
            "id_question": q["id_question"],
            "id_user": id_user,
            "id_meeting": id_meeting,
            "content": request.user_response
        }
        insert_data("answers", answer_data)

    # 🔄 Conversación Continua con GPT
    ai_response = conversation.invoke(
        {"input": "¿Tienes más comentarios o preguntas sobre la reunión?"},
        config={"configurable": {"session_id": session_id}}
    )

    # Guardar nueva pregunta en `questions`
    new_question_data = {
        "id_meeting": id_meeting,
        "id_user": id_user,
        "content": ai_response.content
    }
    insert_data("questions", new_question_data)

    # Guardar respuesta en `answers`
    new_answer_data = {
        "id_question": None,  # No hay pregunta previa porque es una conversación espontánea
        "id_user": id_user,
        "id_meeting": id_meeting,
        "content": request.user_response
    }
    insert_data("answers", new_answer_data)

    return ChatResponse(
        message="Conversación en curso",
        ai_response=ai_response.content
    )
@router.post("/context")
def get_chat_context(id_user: str, id_meeting: str):
    """
    Devuelve todas las preguntas y respuestas de la reunión para que GPT tenga contexto.
    """
    # Obtener preguntas y respuestas de la DB
    questions = select_data("questions", {"id_meeting": id_meeting, "id_user": id_user}).data
    answers   = select_data("answers",   {"id_meeting": id_meeting, "id_user": id_user}).data

    q_dict = {q["id_question"]: q["content"] for q in questions}
    # Armar lista de pares (pregunta -> respuesta)
    pairs = []
    for ans in answers:
        qid = ans["id_question"]
        question_text = q_dict[qid] if qid else "ChatGPT Pregunta espontánea"
        answer_text = ans["content"]
        pairs.append({"question": question_text, "answer": answer_text})

    return {"pairs": pairs}
