import streamlit as st
import requests

# URL base de la API de FastAPI
API_BASE_URL = "http://127.0.0.1:8000"

# Estado de sesión para mantener el usuario y la conversación
if "user_email" not in st.session_state:
    st.session_state.user_email = None
if "id_meeting" not in st.session_state:
    st.session_state.id_meeting = None
if "messages" not in st.session_state:
    st.session_state.messages = []

# Página de inicio de sesión
st.title("🔵 ReuniCheck - Chat Inteligente para Optimizar Reuniones")

if st.session_state.user_email is None:
    st.subheader("🔑 Inicia sesión con tu correo")
    email_input = st.text_input("Correo electrónico", key="email")

    if st.button("Iniciar sesión"):
        response = requests.post(f"{API_BASE_URL}/chat/start", json={"user_email": email_input})
        if response.status_code == 200:
            data = response.json()
            st.write(data)  # Muestra el contenido del diccionario
            st.session_state.user_email = email_input
            st.session_state.id_user = data["id_user"]

        else:
            st.error("⚠️ Usuario no encontrado. Verifica tu correo.")

# Si el usuario ha iniciado sesión, mostrar reuniones disponibles
if st.session_state.user_email:
    st.subheader(f"📅 Reuniones disponibles para {st.session_state.user_email}")

    response = requests.post(f"{API_BASE_URL}/chat/start", json={"user_email": st.session_state.user_email})
    if response.status_code == 200:
        meetings = response.json()["meetings"]
        meeting_options = {m["topic"]: m["id_meeting"] for m in meetings}

        selected_meeting = st.selectbox("Selecciona una reunión", list(meeting_options.keys()))
        if st.button("Continuar con la reunión"):
            st.session_state.id_meeting = meeting_options[selected_meeting]

    else:
        st.error("⚠️ No tienes reuniones asignadas.")

# Si hay una reunión seleccionada, iniciar el chat
if st.session_state.id_meeting:
    st.subheader("Preguntas de la Reunión")

    # 1. Llamamos al endpoint /questions/pending para obtener la lista de preguntas
    pending_resp = requests.post(
        f"{API_BASE_URL}/questions/pending",
        json={
            "id_user": st.session_state.id_user,
            "id_meeting": st.session_state.id_meeting
        }
    )

    if pending_resp.status_code == 200:
        data = pending_resp.json()
        questions_list = data["questions"]

        # 2. Filtramos las no respondidas
        unanswered = [q for q in questions_list if not q["answered"]]

        if unanswered:
            st.warning("Tienes preguntas pendientes por responder.")
            # Mostrar un formulario para cada pregunta pendiente
            for question in unanswered:
                # Un text_input único por pregunta
                response_key = f"resp_{question['id_question']}"
                user_answer = st.text_input(
                    f"Pregunta: {question['content']}",
                    key=response_key
                )

            if st.button("Guardar Respuestas"):
                for question in unanswered:
                    user_answer = st.session_state.get(f"resp_{question['id_question']}", "")
                    if user_answer:
                        answer_data = {
                            "id_question": question["id_question"],
                            "id_user": st.session_state.id_user,
                            "id_meeting": st.session_state.id_meeting,
                            "content": user_answer
                        }
                        st.write("Enviando a /answers/create:", answer_data)  # <--- Depuración
                        resp = requests.post(f"{API_BASE_URL}/answers/create", json=answer_data)
                        st.write("Respuesta del servidor /answers/create:", resp.status_code, resp.text)
                st.success("¡Respuestas guardadas!")



        else:
            st.info("No hay preguntas pendientes. Puedes iniciar el chat con GPT.")
            # Aquí mostramos la sección de "chat interactivo"
            st.subheader("Chat Interactivo con GPT")
            # Muestra todos los mensajes previos (si quieres un historial)
            # Por ejemplo, si guardas los mensajes en st.session_state.messages
            for msg in st.session_state.messages:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
            # Nuevo input para el usuario
            user_input = st.chat_input("Escribe tu mensaje...")
            if user_input:
                # Guardar el mensaje del usuario en la lista de mensajes
                st.session_state.messages.append({"role": "user", "content": user_input})
                # Muestra el mensaje en la interfaz
                with st.chat_message("user"):
                    st.markdown(user_input)
                # Llamar al endpoint /chat/conversation de FastAPI
                payload = {
                    "id_user": st.session_state.id_user,  # string (UUID del usuario)
                    "id_meeting": st.session_state.id_meeting,  # string (UUID de la reunión)
                    "user_response": user_input
                }
                response = requests.post(f"{API_BASE_URL}/chat/conversation", json=payload)
                if response.status_code == 200:
                    data = response.json()
                    # Se asume que data = { "message": "...", "ai_response": "..." }
                    ai_msg = data["ai_response"]
                    # Agrega el mensaje de GPT al historial
                    st.session_state.messages.append({"role": "assistant", "content": ai_msg})
                    # Muestra la respuesta de GPT
                    with st.chat_message("assistant"):
                        st.markdown(ai_msg)
            else:
                st.error("Error al interactuar con GPT. Por favor, intenta de nuevo.")
    else:
        st.error("Error al obtener preguntas pendientes.")


# Módulo 3 - Análisis de reuniones
if "analysis_requested" in st.session_state and st.session_state.analysis_requested:
    st.subheader("📊 Análisis de Reunión")

    analysis_response = requests.post(
        f"{API_BASE_URL}/analysis/analyze",
        json={"id_user": st.session_state.id_user, "id_meeting": st.session_state.id_meeting}
    )

    if analysis_response.status_code == 200:
        result = analysis_response.json()
        st.markdown(f"**Conclusión:** {result['conclusions']}")
        st.markdown(f"**¿Es necesaria la reunión?** {'✅ Sí' if result['is_meeting_needed'] else '❌ No'}")

    else:
        st.error("⚠️ No se pudo analizar la reunión.")
