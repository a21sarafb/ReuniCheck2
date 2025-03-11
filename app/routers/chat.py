from fastapi import APIRouter, HTTPException
from app.modules.chat_generator import conversation
from app.database.supabase_api import select_data, insert_data
from app.models.schemas import ChatRequest, ChatResponse, ChatStartRequest
from typing import List

router = APIRouter(prefix="/chat", tags=["Chat"])
def build_context_from_db(id_user: str, id_meeting: str) -> str:
    """
    Retorna un string que contiene:
    - El tema de la reunión.
    - Las preguntas oficiales y las respuestas que dio el usuario.
    - (Opcional) Un breve resumen o instructivo para GPT.
    """

    # 1. Obtener el tema de la reunión
    meeting_resp = select_data("meetings", {"id_meeting": id_meeting})
    meeting_data = meeting_resp.data if meeting_resp and meeting_resp.data else []
    topic = meeting_data[0]["topic"] if meeting_data else "Tema desconocido"

    # 2. Obtener las preguntas
    questions_resp = select_data("questions", {"id_meeting": id_meeting, "id_user": id_user})
    questions_data = questions_resp.data if questions_resp and questions_resp.data else []

    # 3. Obtener las respuestas
    answers_resp = select_data("answers", {"id_meeting": id_meeting, "id_user": id_user})
    answers_data = answers_resp.data if answers_resp and answers_resp.data else []

    # Crear un mapa id_question -> [respuestas...]
    from collections import defaultdict
    answer_map = defaultdict(list)
    for ans in answers_data:
        qid = ans["id_question"]
        # Podrías concatenar si hay múltiples respuestas para la misma pregunta
        answer_map[qid].append(ans["content"])

    # Armar un “contexto” en texto.
    context = f"=== CONTEXTO DE LA REUNIÓN ===\nTema: {topic}\n\n"
    for q in questions_data:
        qid = q["id_question"]
        context += f"Pregunta: {q['content']}\n"
        if qid in answer_map:
            for idx, ans_txt in enumerate(answer_map[qid], start=1):
                context += f"   Respuesta #{idx}: {ans_txt}\n"
        else:
            context += "   (Sin respuesta)\n"
        context += "\n"
    context += (
        "=== FIN DEL CONTEXTO ===\n\n"
        "Basándote en este contexto, profundiza en posibles inconsistencias, mejoras, "
        "o información adicional que el usuario podría aportar.\n"
    )

    return context

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

    id_user = user_response.data[0]["id_user"]

    # Obtener reuniones asignadas al usuario
    meetings_response = select_data("meetings", {"id_user": id_user})

    if not meetings_response.data:
        raise HTTPException(status_code=404, detail="No tienes reuniones asignadas.")

    meetings = [{"id_meeting": m["id_meeting"], "topic": m["topic"]} for m in meetings_response.data]

    return {
        "message": "Reuniones disponibles",
        "meetings": meetings,  # la lista de reuniones
        "id_user": id_user  #  id_user
    }


@router.post("/conversation", response_model=ChatResponse)

def chat_with_bot(request: ChatRequest):
    id_user = request.id_user
    id_meeting = request.id_meeting
    user_message = request.user_response
    session_id = f"user_{id_user}_meeting_{id_meeting}"

    if user_message == "INICIO_AUTOMATICO_PROFUNDIZAR":
        # 1) Construir el contexto con las respuestas antiguas
        context_text = build_context_from_db(id_user, id_meeting)

        # 2) Llamar a la cadena con ese contexto: GPT empezará la conversación
        ai_response = conversation.invoke(
            {
                "input": f"""{context_text}

El usuario ya completó las preguntas oficiales. Inicia la conversación 
profundizando y pidiendo aclaraciones donde veas huecos o áreas de mejora.
""",
            },
            config={"configurable": {"session_id": session_id}}
        )

        return ChatResponse(
            message="Chat iniciado con contexto",
            ai_response=ai_response.content
        )

    # ---- CASO NORMAL: el usuario está en plena conversación ---
    #    1) Registrar la respuesta que acaba de dar en 'answers' (opcional).
    #    2) GPT responde en base al historial (si usas la memoria).

    # EJEMPLO: guardamos la respuesta del usuario (input del chat) como "answers"
    new_answer_data = {
        "id_question": None,  # si es diálogo libre, no asignamos question
        "id_user": id_user,
        "id_meeting": id_meeting,
        "content": user_message
    }
    insert_data("answers", new_answer_data)

    # 3) GPT: conversation
    #    Pongamos que la “memoria” de la cadena retiene los turnos previos
    #    (sólo si tu chat_generator.py está configurado con ChatMessageHistory).
    #    De lo contrario, habría que inyectar el contexto en cada turno.

    ai_response = conversation.invoke(
        {"input": user_message},
        config={"configurable": {"session_id": session_id}}
    )

    # Ejemplo: guardar lo que GPT dice en la tabla `questions` (o en un log)
    new_question_data = {
        "id_meeting": id_meeting,
        "id_user": id_user,
        "content": ai_response.content
    }
    insert_data("questions", new_question_data)

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
