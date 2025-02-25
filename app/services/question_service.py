from ..database.supabase_api import insert_data, select_data
from ..config import OPENAI_API_KEY
from openai import OpenAI

class QuestionGenerator:
    def __init__(self):
        self.client = openai.ChatCompletion.create  # Corrección del método

    def create_questions(self, request):
        messages = [
            {"role": "system", "content": "Genera preguntas clave sobre el tema indicado."},
            {"role": "user", "content": f"Genera 5 preguntas clave para evaluar '{request.topic}'."}
        ]
        try:
            response = self.client(model="gpt-3.5-turbo", messages=messages)
            questions = response["choices"][0]["message"]["content"].strip().split("\n")

            meeting_data = {"topic": request.topic, "state": True}
            meeting_result = insert_data("meetings", meeting_data)

            if not meeting_result.data:
                return None

            meeting_id = meeting_result.data[0]["id_meeting"]
            for question in questions:
                insert_data("questions", {"id_meeting": meeting_id, "content": question})

            return {"topic": request.topic, "questions": questions}
        except Exception as e:
            return {"error": str(e)}

