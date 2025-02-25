from ..database.supabase_api import select_data
from langchain_openai import ChatOpenAI

chat = ChatOpenAI(model_name="gpt-4", temperature=0.7)

def chatbot_with_gpt(user_email, meeting_id):
    user_response = select_data("user", {"email": user_email})
    if not user_response.data:
        return "Usuario no encontrado"

    context = f"Reunión sobre: {meeting_id}"
    response = chat.invoke(context)
    return response.content
