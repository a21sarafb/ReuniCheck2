from pydantic import BaseModel, Field
from typing import List, Optional

# Esquema para la creación de preguntas
class QuestionCreate(BaseModel):
    id_meeting: str = Field(..., description="ID de la reunión")
    id_user: str = Field(..., description="ID del usuario que crea la pregunta")
    content: str = Field(..., min_length=5, description="Contenido de la pregunta")

# Esquema para la creación de respuestas
class AnswerCreate(BaseModel):
    id_question: str = Field(..., description="ID de la pregunta")
    id_user: str = Field(..., description="ID del usuario que responde")
    content: str = Field(..., min_length=2, description="Contenido de la respuesta")
    id_meeting: str = Field(..., description="ID de la reunión")

# Esquema para la creación de un usuario
class UserCreate(BaseModel):
    name: str = Field(..., min_length=3, description="Nombre del usuario")
    email: str = Field(..., description="Correo electrónico del usuario")

# Esquema para la creación de una reunión
class MeetingCreate(BaseModel):
    topic: str = Field(..., min_length=3, description="Tema de la reunión")
    users: List[str] = Field(..., description="Lista de correos electrónicos de los participantes")

# Esquema para devolver información de una reunión
class Meeting(BaseModel):
    id_meeting: Optional[int] = Field(None, description="ID de la reunión (generado automáticamente)")
    topic: str = Field(..., min_length=3, description="Tema de la reunión")
    state: bool = Field(default=True, description="Estado de la reunión (True por defecto)")
    users: List[str] = Field(..., description="Lista de correos electrónicos de los participantes")

class ChatStartRequest(BaseModel):
    user_email: str = Field(..., description="Correo del usuario para iniciar sesión en el chat")

class ChatRequest(BaseModel):
    id_user: str = Field(..., description="ID del usuario")
    id_meeting: str = Field(..., description="ID de la reunión")
    user_response: str = Field(..., description="Respuesta del usuario a la pregunta")

class ChatResponse(BaseModel):
    message: str = Field(..., description="Mensaje del sistema")
    ai_response: str = Field(..., description="Respuesta de la IA")
    debug: dict = Field(None, description="Información de diagnóstico para depuración")

class AnalysisRequest(BaseModel):
    id_user: str = Field(..., description="ID del usuario que solicita el análisis")
    id_meeting: str = Field(..., description="ID de la reunión a analizar")

class AnalysisResponse(BaseModel):
    message: str = Field(..., description="Estado del análisis")
    conclusions: str = Field(..., description="Análisis de ChatGPT")
    is_meeting_needed: bool = Field(..., description="Indica si la reunión es necesaria")

class PendingQuestionsRequest(BaseModel):
    id_user: str
    id_meeting: str