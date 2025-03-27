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

    # Armar un "contexto" en texto.
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
    
    # Valores por defecto para la información de debug
    debug_info = {
        "message": "Inicio de procesamiento",
        "recent_questions": [],
        "answered_questions": [],
        "selected_question": None
    }

    # Caso especial: Inicio automático
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
        
        # 3) Guardar lo que GPT dice en la tabla `questions`
        new_question_data = {
            "id_meeting": id_meeting,
            "id_user": id_user,
            "content": ai_response.content
        }
        question_resp = insert_data("questions", new_question_data)
        
        # Extraer el ID de la nueva pregunta para registro en debug
        new_question_id = None
        if question_resp.data and len(question_resp.data) > 0:
            new_question_id = question_resp.data[0].get("id_question")
        
        debug_info["message"] = "Inicio automático completado"
        debug_info["new_question"] = {
            "id": new_question_id,
            "content": ai_response.content[:100] + "..." if len(ai_response.content) > 100 else ai_response.content
        }

        return ChatResponse(
            message="Chat iniciado con contexto",
            ai_response=ai_response.content,
            debug=debug_info
        )

    # CASO NORMAL: El usuario está respondiendo en una conversación en curso
    
    # 1. Obtener todas las preguntas recientes para este usuario y reunión
    questions_resp = select_data(
        "questions", 
        {"id_meeting": id_meeting, "id_user": id_user},
        order_by="created_at",
        ascending=False,
        limit=10
    )
    
    # Extraer IDs de las preguntas recientes para debug
    recent_questions = []
    if questions_resp.data:
        for q in questions_resp.data[:3]:  # Solo mostramos las 3 más recientes en el debug
            recent_questions.append({
                "id": q.get("id_question"),
                "content": q.get("content", "")[:50] + "..." if q.get("content") and len(q.get("content")) > 50 else q.get("content", ""),
                "created_at": q.get("created_at")
            })
    debug_info["recent_questions"] = recent_questions
    
    # 2. Obtener las respuestas existentes
    answers_resp = select_data(
        "answers",
        {"id_meeting": id_meeting, "id_user": id_user}
    )
    
    # Crear un mapa de preguntas respondidas
    answered_question_ids = {}
    answered_questions_debug = []
    
    if answers_resp.data:
        for answer in answers_resp.data:
            q_id = answer.get("id_question")
            if q_id:  # Solo si tiene una pregunta asociada
                answered_question_ids[q_id] = True
                answered_questions_debug.append({
                    "id_question": q_id,
                    "id_answer": answer.get("id_answer"),
                    "content": answer.get("content", "")[:50] + "..." if answer.get("content") and len(answer.get("content")) > 50 else answer.get("content", "")
                })
    
    debug_info["answered_questions"] = answered_questions_debug[:3]  # Limitamos a 3 para el debug
    
    # 3. Encontrar la primera pregunta sin respuesta
    last_question_id = None
    for question in questions_resp.data:
        q_id = question.get("id_question")
        if q_id and q_id not in answered_question_ids:
            last_question_id = q_id
            debug_info["selected_question"] = {
                "id": q_id,
                "content": question.get("content", "")[:100] + "..." if question.get("content") and len(question.get("content")) > 100 else question.get("content", ""),
                "created_at": question.get("created_at")
            }
            break
    
    # Si no encontramos una pregunta sin respuesta, registramos ese hecho
    if not last_question_id:
        debug_info["message"] = "No se encontró ninguna pregunta sin responder"
    else:
        debug_info["message"] = "Se encontró una pregunta sin responder"
    
    # 4. Guardar la respuesta del usuario
    new_answer_data = {
        "id_question": last_question_id,  # Puede ser None si no encontramos una pregunta sin respuesta
        "id_user": id_user,
        "id_meeting": id_meeting,
        "content": user_message
    }
    answer_resp = insert_data("answers", new_answer_data)
    
    # 5. Obtener la respuesta de la IA
    ai_response = conversation.invoke(
        {"input": user_message},
        config={"configurable": {"session_id": session_id}}
    )
    
    # 6. Guardar la respuesta de la IA como una nueva pregunta
    new_question_data = {
        "id_meeting": id_meeting,
        "id_user": id_user,
        "content": ai_response.content
    }
    new_question_resp = insert_data("questions", new_question_data)
    
    # Actualizar el debug con información sobre la nueva pregunta
    if new_question_resp.data and len(new_question_resp.data) > 0:
        new_question_id = new_question_resp.data[0].get("id_question")
        debug_info["new_question"] = {
            "id": new_question_id,
            "content": ai_response.content[:100] + "..." if len(ai_response.content) > 100 else ai_response.content
        }
    
    return ChatResponse(
        message="Conversación en curso",
        ai_response=ai_response.content,
        debug=debug_info
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
