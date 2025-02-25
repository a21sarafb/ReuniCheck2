from ..database.supabase_api import select_data
from langchain_openai import ChatOpenAI

chat = ChatOpenAI(model_name="gpt-4", temperature=0.5)

def analyze_meeting(meeting_id):
    questions = select_data("questions", {"id_meeting": meeting_id}).data
    responses = select_data("answers", {"id_meeting": meeting_id}).data

    context = f"Análisis de reunión ID {meeting_id}: {questions}, {responses}"
    result = chat.invoke(context)

    return result.content
