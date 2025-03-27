from fastapi import APIRouter, HTTPException
from app.modules.question_generator import QuestionGenerator
from app.modules.open_ai import GeneradorPreguntas
from app.database.supabase_api import insert_data, select_data
from app.models.schemas import QuestionCreate, MeetingCreate, UserCreate, PendingQuestionsRequest
from app.config import OPENAI_API_KEY
from typing import List

router = APIRouter(prefix="/questions", tags=["Questions"])

@router.post("/")
def generate_questions(request: QuestionCreate):
    generator = QuestionGenerator()

    result = generator.create_questions(request)
    if not result:
        raise HTTPException(status_code=400, detail="No se pudieron generar preguntas")
    return {"topic": request.content, "questions": result}

@router.post("/users/")
def create_new_user(user: UserCreate):  # 📌 Se usa `UserCreate` para recibir JSON en el body
    """ Endpoint para crear un nuevo usuario con Request Body """
    user_data = {"name": user.name, "email": user.email, "rol": "participant"}
    response = insert_data("user", user_data)

    if hasattr(response, "error") and response.error:
        raise HTTPException(status_code=400, detail=str(response.error))

    return {
        "message": "Usuario creado exitosamente",
        "user": user_data
    }
@router.get("/all_users")
def get_all_users():
    resp = select_data("user")
    users = resp.data if resp.data else []
    return {"users": users}  # Siempre devolver JSON

@router.post("/meetings/")
def create_meeting(meeting: MeetingCreate):
    """
    Crea una reunión con el mismo `topic` para cada usuario de la lista `users`.
    Cada usuario tendrá su propia fila en la tabla `meetings` y sus preguntas asignadas.
    """

    assigned_meetings = []  # Lista para guardar reuniones creadas

    for email in meeting.users:
        print(f"Intentando crear reunión para: {email}") #debug
        # Buscar usuario por email
        user_response = select_data("user", {"email": email})

        # Verificar si la respuesta tiene `data`
        user_data_list = user_response.data if (user_response and user_response.data) else []

        if not user_data_list:
            print(f"⚠️ Usuario con email {email} no encontrado. Se omitirá.")
            continue

        id_user = user_data_list[0]["id_user"]
        print(f"   - id_user: {id_user}") #debug
        # **Crear una reunión por cada usuario**
        meeting_data = {"topic": meeting.topic, "state": True, "id_user": id_user}
        meeting_response = insert_data("meetings", meeting_data)
        # Revisa si hay error
        if hasattr(meeting_response, "error") and meeting_response.error:
            print("⚠️ Error al insertar meeting:", meeting_response.error)
            raise HTTPException(status_code=400, detail=str(meeting_response.error))
        # Verifica si se creó efectivamente
        if not meeting_response.data or not meeting_response.data[0].get("id_meeting"):
            print("⚠️ No se devolvió id_meeting al insertar.")
            raise HTTPException(status_code=500, detail="Error al obtener el ID de la reunión")
        id_meeting = meeting_response.data[0]["id_meeting"] if meeting_response.data else None
        if not id_meeting:
            raise HTTPException(status_code=500, detail="Error al obtener el ID de la reunión")

        assigned_meetings.append({
            "id_meeting": id_meeting,
            "topic": meeting.topic,
            "email": email,
            "id_user": id_user
        })

        # **Generar preguntas con ChatGPT**
        print(f"🔄 Generando preguntas para {email} en la reunión {id_meeting}...")
        gpt = GeneradorPreguntas(api_key=OPENAI_API_KEY)  # 📌 Pasamos el `api_key`
        preguntas = gpt.generar_preguntas(meeting.topic)

        if not preguntas:
            print(f"❌ No se generaron preguntas para {email}.")
            continue

        # **Guardar las preguntas en la base de datos**
        print(f"✅ Guardando preguntas en la base de datos para {email}...")
        for pregunta in preguntas:
            insert_data("questions", {
                "id_meeting": id_meeting,
                "id_user": id_user,
                "content": pregunta
            })

    if not assigned_meetings:
        raise HTTPException(status_code=400, detail="No se pudieron crear reuniones para los usuarios proporcionados.")

    return {
        "message": "Reuniones creadas con éxito",
        "meetings": assigned_meetings
    }

@router.post("/pending")
def get_pending_questions(request: PendingQuestionsRequest):
    """
    Devuelve la lista de preguntas de la reunión y el estado de sus respuestas.
    """
    id_user = request.id_user
    id_meeting = request.id_meeting

    # Obtener todas las preguntas de la reunión
    questions_response = select_data("questions", {"id_meeting": id_meeting, "id_user": id_user})
    if not questions_response.data:
        return {"questions": []}

    # Obtener todas las respuestas de la reunión
    answers_response = select_data("answers", {"id_meeting": id_meeting, "id_user": id_user})
    
    # Crear un mapa de id_question -> respuesta
    answer_map = {}
    if answers_response.data:
        for answer in answers_response.data:
            if answer["id_question"]:  # Solo si la respuesta tiene id_question
                answer_map[answer["id_question"]] = answer["content"]
    
    # Determinar las preguntas respondidas
    answered_ids = set(answer_map.keys())

    # Armar la lista de preguntas con su estado y respuesta
    questions = []
    for q in questions_response.data:
        q_id = q["id_question"]
        is_answered = (q_id in answered_ids)
        
        question_data = {
            "id_question": q_id,
            "content": q["content"],
            "answered": is_answered,
        }
        
        # Incluir la respuesta si la pregunta ha sido respondida
        if is_answered:
            question_data["answer"] = answer_map[q_id]
        
        questions.append(question_data)

    return {"questions": questions}

@router.get("/recent/{id_user}/{id_meeting}")
def get_recent_questions(id_user: str, id_meeting: str):
    """
    Devuelve las preguntas más recientes de un usuario en una reunión específica,
    ordenadas por fecha de creación (más reciente primero).
    """
    # Obtener todas las preguntas de la reunión para ese usuario
    questions_response = select_data(
        "questions", 
        {"id_meeting": id_meeting, "id_user": id_user},
        order_by="created_at",
        ascending=False,
        limit=10  # Limitamos a las 10 más recientes
    )
    
    if not questions_response.data:
        return {"questions": []}
    
    # Obtener respuestas para estas preguntas
    all_question_ids = [q["id_question"] for q in questions_response.data]
    answers_response = select_data(
        "answers",
        {"id_meeting": id_meeting, "id_user": id_user, "id_question": all_question_ids}
    )
    
    # Crear un mapa de id_question -> respuesta
    answered_map = {}
    if answers_response.data:
        for answer in answers_response.data:
            answered_map[answer["id_question"]] = answer["content"]
    
    # Devolver las preguntas ordenadas con información de respuestas
    questions = []
    for q in questions_response.data:
        question_id = q["id_question"]
        questions.append({
            "id_question": question_id,
            "content": q["content"],
            "created_at": q["created_at"],
            "answered": question_id in answered_map,
            "answer": answered_map.get(question_id, "")
        })
    
    return {"questions": questions}

@router.get("/debug/{id_meeting}/{id_user}")
def debug_questions_answers(id_meeting: str, id_user: str):
    """
    Endpoint de diagnóstico para ver todas las preguntas y respuestas
    de un usuario en una reunión específica.
    """
    # Obtener información sobre la estructura de las tablas
    questions_resp = select_data(
        "questions", 
        {"id_meeting": id_meeting, "id_user": id_user},
        order_by="created_at",
        ascending=False
    )
    
    answers_resp = select_data(
        "answers",
        {"id_meeting": id_meeting, "id_user": id_user},
        order_by="created_at",
        ascending=False
    )
    
    # Analizar la estructura de las preguntas
    question_fields = {}
    if questions_resp.data and len(questions_resp.data) > 0:
        question_fields = {key: type(value).__name__ for key, value in questions_resp.data[0].items()}
    
    # Analizar la estructura de las respuestas
    answer_fields = {}
    if answers_resp.data and len(answers_resp.data) > 0:
        answer_fields = {key: type(value).__name__ for key, value in answers_resp.data[0].items()}
    
    # Lista de preguntas y respuestas para análisis
    questions = []
    for q in questions_resp.data[:5]:  # Solo las 5 más recientes para no sobrecargar
        question_item = {
            "id_question": q["id_question"],
            "content": q["content"][:100] + "..." if len(q["content"]) > 100 else q["content"],
            "created_at": q["created_at"]
        }
        questions.append(question_item)
    
    answers = []
    for a in answers_resp.data[:5]:  # Solo las 5 más recientes
        answer_item = {
            "id_answer": a["id_answer"],
            "id_question": a["id_question"],
            "content": a["content"][:100] + "..." if len(a["content"]) > 100 else a["content"],
            "created_at": a["created_at"]
        }
        answers.append(answer_item)
    
    return {
        "questions_structure": question_fields,
        "answers_structure": answer_fields,
        "recent_questions": questions,
        "recent_answers": answers,
        "questions_count": len(questions_resp.data),
        "answers_count": len(answers_resp.data)
    }

