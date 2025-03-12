# chat_generator.py - Mejorado para conversaciones continuas y generación dinámica de preguntas


from app.database.supabase_api import insert_data, select_data
from langchain_openai import ChatOpenAI
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables import RunnableWithMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


import os

# Configurar modelo de chat (GPT-4)
chat = ChatOpenAI(model_name="gpt-4", temperature=0.7)

# Configurar prompt con memoria
prompt = ChatPromptTemplate.from_messages([
    ("system", "Eres un asistente especializado en optimización de reuniones. Mantén la conversación abierta hasta que el usuario indique que quiere finalizar."),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{input}"),
])

# Configurar la cadena de conversación con historial
chain = prompt | chat
session_histories = {}

# Obtener historial de conversación por usuario
def get_session_history(session_id: str) -> ChatMessageHistory:
    if session_id not in session_histories:
        session_histories[session_id] = ChatMessageHistory()
    return session_histories[session_id]

chat = ChatOpenAI(model_name="gpt-4", temperature=0.7)

prompt = ChatPromptTemplate.from_messages([
    ("system", """Eres un asistente especializado en optimización de reuniones.
Lee el contexto proporcionado y los turnos de conversación previos, y 
profundiza en lo que el usuario haya respondido. Si hay contradicciones, 
haz preguntas adicionales. Evita decir "no tengo acceso" a menos que 
realmente falte contexto. Sigue el hilo usando la memoria."""),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{input}"),
])

chain = prompt | chat

conversation = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="input",
    history_messages_key="history",
)
# Chatbot en consola con memoria y conversación continua
def chatbot_with_gpt():
    print("\n🟢 Bienvenido al Chatbot de ReuniCheck con IA y memoria 🟢")

    # Obtener el correo del usuario
    email = input("Ingresa tu correo: ").strip()

    # Verificar usuario en la base de datos
    try:
        user_response = select_data("user", {"email": email})
    except Exception as e:
        print(f"⚠️ Error al consultar el usuario: {e}")
        return

    if not user_response.data:
        print("❌ Usuario no encontrado. Verifica tu correo.")
        return

    user_id = user_response.data[0]["id_user"]

    # Obtener reuniones del usuario
    try:
        meetings_response = select_data("meetings", {"id_user": user_id})
    except Exception as e:
        print(f"⚠️ Error al consultar reuniones: {e}")
        return

    if not meetings_response.data:
        print("❌ No tienes reuniones asignadas.")
        return

    # Mostrar reuniones
    print("\n📅 Reuniones asignadas:")
    for idx, meeting in enumerate(meetings_response.data, start=1):
        print(f"{idx}. {meeting['topic']} (ID: {meeting['id_meeting']})")

    # Seleccionar reunión
    while True:
        try:
            choice = int(input("\nSelecciona el número de la reunión: "))
            if 1 <= choice <= len(meetings_response.data):
                selected_meeting = meetings_response.data[choice - 1]
                break
            else:
                print("⚠️ Número fuera de rango. Inténtalo de nuevo.")
        except ValueError:
            print(" Entrada inválida. Ingresa un número válido.")

    meeting_id = selected_meeting["id_meeting"]
    topic = selected_meeting["topic"]

    # Obtener preguntas de la reunión
    try:
        questions_response = select_data("questions", {"id_meeting": meeting_id, "id_user": user_id})
    except Exception as e:
        print(f"⚠️ Error al consultar preguntas: {e}")
        return

    if not questions_response.data:
        print(" No hay preguntas para esta reunión.")
        return

    questions = [{"id_question": q["id_question"], "content": q["content"]} for q in questions_response.data]
    asked_questions = set()  # Para evitar repetir preguntas

    # Iniciar conversación con IA
    print("\n🤖 Chatbot Iniciado...")
    print(f"Eres un asistente de reuniones. Este es el usuario {email}, tiene una reunión sobre '{topic}'.\n")

    session_id = f"user_{user_id}_meeting_{meeting_id}"  # ID de sesión único

    for q in questions:
        if q["content"] in asked_questions:
            continue  # Evitar repetir preguntas

        print(f"\n: {q['content']}")
        asked_questions.add(q["content"])
        user_response = input("👤: ")

        # Guardar respuesta en la base de datos
        answer_data = {
            "id_question": q["id_question"],
            "id_user": user_id,
            "id_meeting": meeting_id,
            "content": user_response
        }
        try:
            insert_data("answers", answer_data)
        except Exception as e:
            print(f" Error al guardar respuesta: {e}")
            return

    # 🔄 Conversación Adicional
    while True:
        user_input = input("\n👤 ¿Tienes más dudas o comentarios? (escribe 'salir' para terminar): ").strip()

        if user_input.lower() in ["salir", "no", "nada más"]:
            print("\n Chatbot finalizado. ¡Gracias por tu participación!\n")
            break  # Terminar conversación si el usuario dice que quiere salir

        # Guardar nueva pregunta en `questions`
        new_question_data = {
            "id_meeting": meeting_id,
            "id_user": user_id,
            "content": user_input
        }
        try:
            insert_data("questions", new_question_data)
        except Exception as e:
            print(f" Error al guardar la nueva pregunta: {e}")

        # Obtener respuesta de IA
        ai_response = conversation.invoke(
            {"input": user_input},
            config={"configurable": {"session_id": session_id}}
        )

        print(f"\n (IA): {ai_response.content}")

        # Guardar respuesta en `answers`
        new_answer_data = {
            "id_question": None,
            "id_user": user_id,
            "id_meeting": meeting_id,
            "content": ai_response.content
        }
        try:
            insert_data("answers", new_answer_data)
        except Exception as e:
            print(f"⚠️ Error al guardar la respuesta de la IA: {e}")

    print("\n Conversación guardada en la base de datos.\n")


if __name__ == "__main__":
    chatbot_with_gpt()
