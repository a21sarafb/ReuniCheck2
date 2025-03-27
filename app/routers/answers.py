# app/routers/answers.py
from fastapi import APIRouter, HTTPException
from app.database.supabase_api import select_data, insert_data
from app.models.schemas import AnswerCreate

router = APIRouter(prefix="/answers", tags=["Answers"])

@router.post("/create")
def create_answer(answer: AnswerCreate):
    data_to_insert = answer.dict()
    print("Insertando en 'answers':", data_to_insert)  # Depuración
    response = insert_data("answers", data_to_insert)
    print("Respuesta de Supabase al insertar 'answers':", response)  # Depuración

    if hasattr(response, "error") and response.error:
        print("⚠️ Error de Supabase:", response.error)  # Mas info
        raise HTTPException(status_code=400, detail=str(response.error))
    return {"message": "Respuesta creada con éxito"}

@router.get("/meetings_responded/{id_user}")
def get_meetings_responded(id_user: str):
    """
    Devuelve todas las reuniones (id_meeting, topic) en las que
    el usuario (id_user) tenga al menos una respuesta registrada.
    """

    # 1) Obtener todas las respuestas del usuario en 'answers'
    answers_resp = select_data("answers", {"id_user": id_user})
    if hasattr(answers_resp, "error") and answers_resp.error:
        # Manejo de error si supabase da error
        raise HTTPException(status_code=400, detail=str(answers_resp.error))

    answers_data = answers_resp.data if answers_resp and answers_resp.data else []
    if not answers_data:
        # El usuario no tiene ni una respuesta
        return {"meetings": []}

    # 2) Reunir los ids de reuniones en los que ha respondido
    meeting_ids = list({ans["id_meeting"] for ans in answers_data})

    # 3) Consultar la tabla 'meetings' para obtener sus datos
    meeting_resp = select_data("meetings", {"id_meeting": meeting_ids})
    if hasattr(meeting_resp, "error") and meeting_resp.error:
        raise HTTPException(status_code=400, detail=str(meeting_resp.error))

    meeting_data = meeting_resp.data if meeting_resp and meeting_resp.data else []
    # 4) Estructurar la respuesta en forma de lista de diccionarios {id_meeting, topic}
    result = []
    for m in meeting_data:
        result.append({
            "id_meeting": m["id_meeting"],
            "topic": m["topic"]
        })

    return {"meetings": result}

@router.get("/user_meeting/{id_user}/{id_meeting}")
def get_user_meeting_answers(id_user: str, id_meeting: str):
    """
    Devuelve todas las respuestas de un usuario específico para una reunión específica.
    """
    # Obtener todas las respuestas del usuario para la reunión dada
    answers_resp = select_data("answers", {"id_user": id_user, "id_meeting": id_meeting})
    if hasattr(answers_resp, "error") and answers_resp.error:
        # Manejo de error si supabase da error
        raise HTTPException(status_code=400, detail=str(answers_resp.error))

    answers_data = answers_resp.data if answers_resp and answers_resp.data else []
    return {"answers": answers_data}