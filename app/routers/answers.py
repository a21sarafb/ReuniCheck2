# app/routers/answers.py
from fastapi import APIRouter, HTTPException
from app.database.supabase_api import insert_data
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
