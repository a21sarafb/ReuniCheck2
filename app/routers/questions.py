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
    answered_ids = {a["id_question"] for a in answers_response.data} if answers_response.data else set()

    # Armar la lista de preguntas con su estado
    questions = []
    for q in questions_response.data:
        is_answered = (q["id_question"] in answered_ids)
        questions.append({
            "id_question": q["id_question"],
            "content": q["content"],
            "answered": is_answered
        })

    return {"questions": questions}

