from app.database.supabase_api import insert_data, select_data
from app.modules.open_ai import GeneradorPreguntas

class QuestionGenerator:
    def __init__(self):
        self.generador = GeneradorPreguntas()

    def create_questions(self, topic: str, users: list[int]):
        """ Crea una reunión con múltiples usuarios y genera preguntas """

        # Insertar reunión en la base de datos
        meeting_data = {"topic": topic, "state": True}
        meeting_response = insert_data("meetings", meeting_data)

        if not meeting_response.data:
            return None

        meeting_id = meeting_response.data[0]["id_meeting"]

        # Asignar usuarios a la reunión
        for user_id in users:
            insert_data("meeting_users", {"id_meeting": meeting_id, "id_user": user_id})

        # Generar preguntas con OpenAI
        preguntas = self.generador.generar_preguntas(topic)
        if not preguntas:
            return None

        # Insertar preguntas en la base de datos
        for pregunta in preguntas:
            insert_data("questions", {"id_meeting": meeting_id, "content": pregunta})

        return {"topic": topic, "questions": preguntas}
