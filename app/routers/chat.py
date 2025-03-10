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
    user_response = select_data("user", {"email": user_email})

    if not user_response.data:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    id_user = user_response.data[0]["id_user"]
    meetings_response = select_data("meetings", {"id_user": id_user})

    if not meetings_response.data:
        raise HTTPException(status_code=404, detail="No tienes reuniones asignadas.")

    meetings = [{"id_meeting": m["id_meeting"], "topic": m["topic"]} for m in meetings_response.data]

    return {"message": "Reuniones disponibles", "meetings": meetings, "id_user": id_user}


@router.post("/conversation")
def chat_with_bot(request: ChatRequest):
    """
    Maneja la conversación del usuario con el chatbot de manera más resolutiva.
    """
    id_user = request.id_user
    id_meeting = request.id_meeting

    questions_response = select_data("questions", {"id_meeting": id_meeting, "id_user": id_user})
    answers_response = select_data("answers", {"id_meeting": id_meeting, "id_user": id_user})

    answered_questions = {a["id_question"] for a in answers_response.data}
    pending_questions = [{"id_question": q["id_question"], "content": q["content"]} for q in questions_response.data if
                         q["id_question"] not in answered_questions]

    if not pending_questions:
        return {"message": "No hay preguntas pendientes en esta reunión."}

    session_id = f"user_{id_user}_meeting_{id_meeting}"
    responses = []

    for q in pending_questions:
        user_answer = request.user_response if request.user_response else conversation.invoke(
            {"input": q["content"]}).content
        responses.append({"question": q["content"], "answer": user_answer})

        insert_data("answers", {"id_question": q["id_question"], "id_user": id_user, "id_meeting": id_meeting,
                                "content": user_answer})

    ai_summary = conversation.invoke({"input": "Resumen hasta ahora y próximos pasos."},
                                     config={"configurable": {"session_id": session_id}})

    return ChatResponse(message="Conversación en curso", ai_response=ai_summary.content, responses=responses)


@router.post("/context")
def get_chat_context(id_user: str, id_meeting: str):
    """
    Devuelve todas las preguntas y respuestas de la reunión para que GPT tenga contexto.
    """
    questions = select_data("questions", {"id_meeting": id_meeting, "id_user": id_user}).data
    answers = select_data("answers", {"id_meeting": id_meeting, "id_user": id_user}).data

    q_dict = {q["id_question"]: q["content"] for q in questions}
    pairs = [{"question": q_dict.get(a["id_question"], "ChatGPT Pregunta espontánea"), "answer": a["content"]} for a in
             answers]

    return {"pairs": pairs}
