from fastapi import APIRouter, HTTPException
from app.modules.analysis import get_meeting_analysis, analyze_meeting
from app.database.supabase_api import select_data, insert_data
from app.models.schemas import AnalysisRequest, AnalysisResponse

router = APIRouter(prefix="/analysis", tags=["Analysis"])

@router.post("/start")
def start_analysis(user_email: str):
    """
    Inicia el análisis verificando qué reuniones 'abiertas' tiene el usuario y permite seleccionar una.
    """

    # Verificar usuario en la base de datos
    user_response = select_data("user", {"email": user_email})

    if not user_response.data:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    user_id = user_response.data[0]["id_user"]

    # Obtener reuniones abiertas asignadas al usuario
    meetings_response = select_data("meetings", {"id_user": user_id, "state": True})

    if not meetings_response.data:
        raise HTTPException(status_code=404, detail="No tienes reuniones abiertas.")

    meetings = [{"id_meeting": m["id_meeting"], "topic": m["topic"]} for m in meetings_response.data]

    return {"message": "Reuniones abiertas disponibles", "meetings": meetings}

@router.post("/analyze")
def analyze_meeting_api(request: AnalysisRequest):
    """
    Analiza una reunión, verifica si todas las preguntas tienen respuesta,
    y luego usa ChatGPT para evaluar si la reunión es necesaria.
    """

    user_id = request.user_id
    meeting_id = request.meeting_id

    # Obtener preguntas y respuestas de la reunión
    questions_response = select_data("questions", {"id_meeting": meeting_id})
    answers_response = select_data("answers", {"id_meeting": meeting_id})

    if not questions_response.data:
        raise HTTPException(status_code=400, detail="No hay preguntas para esta reunión.")

    if not answers_response.data:
        raise HTTPException(status_code=400, detail="No hay respuestas en esta reunión.")

    # Verificar si todas las preguntas tienen respuesta
    answered_questions = {a["id_question"] for a in answers_response.data}
    missing_questions = [
        q for q in questions_response.data if q["id_question"] not in answered_questions
    ]

    if missing_questions:
        missing_info = [
            {"question": q["content"], "user_id": q["id_user"]} for q in missing_questions
        ]
        return {"message": "Faltan preguntas por responder", "missing_questions": missing_info}

    # Obtener contexto de la reunión
    meeting_context = get_meeting_analysis(meeting_id)
    if not meeting_context:
        raise HTTPException(status_code=500, detail="No se pudo generar el contexto de la reunión.")

    # 🔍 Enviar a GPT-4 para análisis
    analysis_result = analyze_meeting(meeting_context, meeting_id)

    return AnalysisResponse(
        message="Análisis completado",
        conclusions=analysis_result["conclusions"],
        is_meeting_needed=analysis_result["analysis"]
    )
