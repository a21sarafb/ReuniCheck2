import streamlit as st
import requests

API_BASE_URL = "http://127.0.0.1:8000"

# --- Estado de sesión ---
if "user_email" not in st.session_state:
    st.session_state.user_email = None
if "id_user" not in st.session_state:
    st.session_state.id_user = None
if "id_meeting" not in st.session_state:
    st.session_state.id_meeting = None
if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("🔵 ReuniCheck - Optimización de Reuniones")

# --- Navegación principal ---
option = st.radio(
    "¿Qué deseas hacer?",
    ("Crear usuario", "Crear reunión", "Contestar preguntas", "Obtener análisis")
)

# =========================================================
# Opción 1: Crear usuario
# =========================================================
if option == "Crear usuario":
    st.subheader("👤 Crear Usuario")
    name_input = st.text_input("Nombre completo")
    email_input = st.text_input("Correo electrónico")

    if st.button("Crear Usuario"):
        payload = {"name": name_input, "email": email_input}
        response = requests.post(f"{API_BASE_URL}/questions/users/", json=payload)
        if response.status_code == 200:
            st.success("✅ Usuario creado exitosamente.")
            st.session_state.user_email = email_input
        else:
            st.error("⚠️ No se pudo crear el usuario. Intenta de nuevo.")

# =========================================================
# Opción 2: Crear reunión
# =========================================================
elif option == "Crear reunión":
    st.subheader("📅 Crear Reunión")
    st.write("Bienvenido al asistente para crear nuevas reuniones en ReuniCheck.")
    with st.form("create_meeting_form"):
        st.caption("Completa la siguiente información para generar automáticamente las preguntas.")

        col1, col2 = st.columns(2)
        with col1:
            topic_input = st.text_input("Tema de la reunión", help="Ej: Revisión de hitos del proyecto X")
        with col2:
            st.write("Participantes")
            participants_input = st.text_area(
                "Ingresa los correos, uno por línea o separados por comas.",
                help="Ej: user1@empresa.com, user2@empresa.com"
            )
        st.markdown("---")
        create_button = st.form_submit_button("Crear Reunión")

    if create_button:
        emails = []
        if "," in participants_input:
            emails = [email.strip() for email in participants_input.split(",")]
        else:
            emails = [line.strip() for line in participants_input.splitlines()]

        payload = {"topic": topic_input, "users": emails}
        with st.spinner("Creando reunión..."):
            response = requests.post(f"{API_BASE_URL}/questions/meetings/", json=payload)
            if response.status_code == 200:
                st.success("✅ Reunión creada y preguntas generadas exitosamente.")
                st.balloons()
            else:
                st.error("⚠️ Error al crear la reunión. Por favor, revisa los datos.")

# =========================================================
# Opción 3: Contestar preguntas
# =========================================================
elif option == "Contestar preguntas":
    st.title("🔵 ReuniCheck - Chat Inteligente para Optimizar Reuniones")

    if st.session_state.user_email is None:
        st.subheader("🔑 Inicia sesión con tu correo")
        email_input = st.text_input("Correo electrónico")

        if st.button("Iniciar sesión"):
            response = requests.post(f"{API_BASE_URL}/chat/start", json={"user_email": email_input})
            if response.status_code == 200:
                data = response.json()
                st.write(data)
                st.session_state.user_email = str(email_input)
                st.session_state.id_user = str(data["id_user"])
            else:
                st.error("⚠️ Usuario no encontrado. Verifica tu correo.")

    # Mostrar reuniones disponibles
    if st.session_state.user_email:
        st.subheader(f"📅 Reuniones disponibles para {st.session_state.user_email}")
        response = requests.post(f"{API_BASE_URL}/chat/start", json={"user_email": st.session_state.user_email})
        if response.status_code == 200:
            data = response.json()
            meetings = data.get("meetings", [])
            if meetings:
                meeting_options = {m["topic"]: m["id_meeting"] for m in meetings}
                selected_meeting = st.selectbox("Selecciona una reunión", list(meeting_options.keys()))
                if st.button("Continuar con la reunión"):
                    st.session_state.id_meeting = str(meeting_options[selected_meeting])
            else:
                st.info("🔹 No tienes reuniones asignadas.")
        else:
            st.error("⚠️ No se pudieron recuperar las reuniones.")

    # Si hay una reunión seleccionada, iniciar el chat / preguntas pendientes
    if st.session_state.id_meeting:
        st.subheader("Preguntas de la Reunión")
        pending_resp = requests.post(
            f"{API_BASE_URL}/questions/pending",
            json={
                "id_user": st.session_state.id_user,
                "id_meeting": st.session_state.id_meeting
            }
        )
        if pending_resp.status_code == 200:
            data = pending_resp.json()
            questions_list = data.get("questions", [])

            unanswered = [q for q in questions_list if not q["answered"]]

            if unanswered:
                st.warning("Tienes preguntas pendientes por responder.")
                for question in unanswered:
                    response_key = f"resp_{question['id_question']}"
                    st.text_input(f"Pregunta: {question['content']}", key=response_key)
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
                            st.write("Enviando a /answers/create:", answer_data)
                            resp = requests.post(f"{API_BASE_URL}/answers/create", json=answer_data)
                            st.write("Respuesta del servidor /answers/create:", resp.status_code, resp.text)
                    st.success("¡Respuestas guardadas!")
            else:
                st.info("No hay preguntas pendientes. Puedes iniciar el chat con GPT.")
                st.subheader("Chat Interactivo con GPT")
                for msg in st.session_state.messages:
                    with st.chat_message(msg["role"]):
                        st.markdown(msg["content"])
                user_input = st.chat_input("Escribe tu mensaje...")
                if user_input:
                    st.session_state.messages.append({"role": "user", "content": user_input})
                    with st.chat_message("user"):
                        st.markdown(user_input)
                    payload = {
                        "id_user": st.session_state.id_user,
                        "id_meeting": st.session_state.id_meeting,
                        "user_response": user_input
                    }
                    response = requests.post(f"{API_BASE_URL}/chat/conversation", json=payload)
                    if response.status_code == 200:
                        data = response.json()
                        ai_msg = data["ai_response"]
                        st.session_state.messages.append({"role": "assistant", "content": ai_msg})
                        with st.chat_message("assistant"):
                            st.markdown(ai_msg)
                else:
                    st.error("Error al interactuar con GPT. Por favor, intenta de nuevo.")
        else:
            st.error("Error al obtener preguntas pendientes.")

# =========================================================
# Opción 4: Obtener análisis
# =========================================================
else:  # Obtener análisis
    st.subheader("📊 Análisis de Reuniones")
    st.write("Ingresa el correo del usuario y selecciona una reunión completada para ver la evaluación final.")

    user_email_analysis = st.text_input("Correo electrónico para análisis")

    if st.button("Buscar reuniones completadas"):
        # 1) Llamar a /chat/start para obtener las reuniones del usuario
        resp = requests.post(f"{API_BASE_URL}/chat/start", json={"user_email": user_email_analysis})
        if resp.status_code != 200:
            st.error("No se pudo recuperar información de usuario. Revisa el correo.")
        else:
            data = resp.json()
            user_id = data["id_user"]
            all_meetings = data["meetings"]

            # 2) Filtrar sólo las reuniones completadas (todas sus preguntas respondidas)
            completed_meetings = []
            for m in all_meetings:
                meet_id = str(m["id_meeting"])
                pending = requests.post(
                    f"{API_BASE_URL}/questions/pending",
                    json={"id_user": user_id, "id_meeting": meet_id}
                )
                if pending.status_code == 200:
                    questions_info = pending.json()["questions"]
                    # Si no hay unanswered => completada
                    if all(q["answered"] for q in questions_info):
                        completed_meetings.append(m)

            if completed_meetings:
                st.success(f"Se encontraron {len(completed_meetings)} reuniones completadas.")
                # 3) Seleccionar la reunión para analizar
                completed_topics = {c["topic"]: c["id_meeting"] for c in completed_meetings}
                selected_analysis = st.selectbox("Selecciona reunión completada", list(completed_topics.keys()))
                if st.button("Analizar reunión"):
                    meeting_to_analyze = completed_topics[selected_analysis]
                    # 4) Llamar al endpoint /analysis/analyze 
                    payload = {
                        "id_user": user_id,
                        "id_meeting": meeting_to_analyze
                    }
                    analysis_resp = requests.post(f"{API_BASE_URL}/analysis/analyze", json=payload)
                    if analysis_resp.status_code == 200:
                        result_data = analysis_resp.json()
                        # 5) Mostrar resultado
                        st.markdown(f"### Resultado del análisis\n**Conclusiones:** {result_data['conclusions']}")
                        st.markdown(
                            f"**¿Hace falta la reunión?** {'✅ Sí' if result_data['is_meeting_needed'] else '❌ No'}"
                        )
                    else:
                        st.error("No se pudo obtener el análisis de la reunión.")
            else:
                st.info("No hay reuniones completadas para este usuario.")
    else:
        st.info("Ingrese un correo y presione 'Buscar reuniones completadas'.")

