# app/routers/analysis.py

from fastapi import APIRouter, HTTPException
from app.modules.analysis import get_meeting_analysis, analyze_meeting
from app.database.supabase_api import select_data
from app.models.schemas import AnalysisRequest, AnalysisResponse

router = APIRouter(prefix="/analysis", tags=["Analysis"])

@router.post("/analyze", response_model=AnalysisResponse)
def analyze_meeting_api(request: AnalysisRequest):
    """
    Endpoint que verifica si todas las preguntas de la reunión tienen respuesta
    y, si es así, llama a GPT para analizar la necesidad de la reunión.
    """
    id_user = request.id_user
    id_meeting = request.id_meeting

    # 1) Verificar si la reunión existe
    meeting_data = select_data("meetings", {"id_meeting": id_meeting})
    if not meeting_data.data:
        raise HTTPException(status_code=404, detail="No existe la reunión")

    # 2) Verificar si todas las preguntas tienen respuesta
    questions = select_data("questions", {"id_meeting": id_meeting}).data
    if not questions:
        raise HTTPException(status_code=400, detail="No hay preguntas en esta reunión")

    answers = select_data("answers", {"id_meeting": id_meeting}).data
    answered_ids = {a["id_question"] for a in answers} if answers else set()
    missing_questions = [q["id_question"] for q in questions if q["id_question"] not in answered_ids]
    if missing_questions:
        raise HTTPException(
            status_code=400,
            detail=f"Faltan respuestas para las preguntas: {missing_questions}"
        )

    # 3) Obtener contexto
    context = get_meeting_analysis(id_meeting)

    # 4) Analizar con GPT
    analysis_dict = analyze_meeting(context, id_meeting)
    # analysis_dict = {"conclusions": "...", "analysis": True/False}

    return AnalysisResponse(
        message="Análisis completado",
        conclusions=analysis_dict["conclusions"],
        is_meeting_needed=analysis_dict["analysis"]
    )
