import streamlit as st
import requests

API_BASE_URL = "http://127.0.0.1:8000"

# Estado de sesión
if "user_email" not in st.session_state:
    st.session_state.user_email = None
if "id_user" not in st.session_state:
    st.session_state.id_user = None
if "id_meeting" not in st.session_state:
    st.session_state.id_meeting = None
if "messages" not in st.session_state:
    st.session_state.messages = []

st.set_page_config(page_title="ReuniCheck", page_icon="🔵", layout="wide")

st.markdown("<h1 style='text-align: center;'>🔵 ReuniCheck - Optimización de Reuniones</h1>", unsafe_allow_html=True)
st.markdown("---")

# navegación con pestañas
tab1, tab2, tab3, tab4 = st.tabs(["👤 Crear Usuario", "📅 Crear Reunión", "❓ Contestar Preguntas", "📊 Obtener Análisis"])

# =========================================================
# 🟢 Opción 1: Crear usuario
# =========================================================
with tab1:
    st.markdown("## 👤 Crear Usuario")
    st.write("Registra un nuevo usuario para participar en reuniones.")

    name_input = st.text_input("Nombre completo", key="name_user")
    email_input = st.text_input("Correo electrónico", key="email_user")

    if st.button("Crear Usuario", use_container_width=True):
        payload = {"name": name_input, "email": email_input}
        response = requests.post(f"{API_BASE_URL}/questions/users/", json=payload)
        if response.status_code == 200:
            st.toast("✅  Usuario creado exitosamente.")
            st.session_state.user_email = email_input
        else:
            st.error("⚠️ No se pudo crear el usuario. Intenta de nuevo.")

# =========================================================
# 🔵 Opción 2: Crear reunión
# =========================================================
with tab2:
    st.markdown("## 📅 Crear Reunión")
    st.write("Selecciona el tema y los participantes para generar una nueva reunión.")

    # Cargar lista de usuarios automáticamente
    @st.cache_data
    def load_users():
        users_resp = requests.get(f"{API_BASE_URL}/questions/all_users")
        return users_resp.json().get("users", []) if users_resp.status_code == 200 else []

    all_users = load_users()
    email_options = [u["email"] for u in all_users]

    with st.form("create_meeting_form"):
        col1, col2 = st.columns(2)
        with col1:
            topic_input = st.text_input("Tema de la reunión", help="Ej: Revisión de hitos del proyecto X")
        with col2:
            selected_emails = st.multiselect("Participantes", options=email_options, default=[])

        st.markdown("---")
        create_button = st.form_submit_button("📌 Crear Reunión")

    if create_button:
        normalized_emails = [email.strip().lower() for email in selected_emails]
        payload = {"topic": topic_input.strip(), "users": normalized_emails}

        with st.spinner("Creando reunión..."):
            response = requests.post(f"{API_BASE_URL}/questions/meetings/", json=payload)

            if response.status_code == 200:
                st.success("✅ Reunión creada y preguntas generadas exitosamente.")
                st.balloons()
            else:
                st.error(f"⚠️ Error al crear la reunión (código {response.status_code}).")
                st.write("Respuesta del servidor:", response.text)

# =========================================================
# ❓ Opción 3: Contestar preguntas
# =========================================================
with tab3:
    st.markdown("## ❓ Contestar Preguntas")
    st.write("Responde a las preguntas de una reunión en la que participas.")

    if st.session_state.user_email is None:
        email_input = st.text_input("Correo electrónico", key="email_login")
        if st.button("Iniciar sesión", use_container_width=True):
            response = requests.post(f"{API_BASE_URL}/chat/start", json={"user_email": email_input})
            if response.status_code == 200:
                data = response.json()
                st.session_state.user_email = str(email_input)
                st.session_state.id_user = str(data["id_user"])
            else:
                st.error("⚠️ Usuario no encontrado. Verifica tu correo.")

    if st.session_state.user_email:
        st.subheader(f"📅 Reuniones disponibles para {st.session_state.user_email}")
        response = requests.post(f"{API_BASE_URL}/chat/start", json={"user_email": st.session_state.user_email})
        if response.status_code == 200:
            data = response.json()
            meetings = data.get("meetings", [])
            if meetings:
                meeting_options = {m["topic"]: m["id_meeting"] for m in meetings}
                selected_meeting = st.selectbox("Selecciona una reunión", list(meeting_options.keys()))
                if st.button("Continuar con la reunión", use_container_width=True):
                    st.session_state.id_meeting = str(meeting_options[selected_meeting])
            else:
                st.info("🔹 No tienes reuniones asignadas.")
        else:
            st.error("⚠️ No se pudieron recuperar las reuniones.")

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
# 📊 Opción 4: Obtener análisis
# =========================================================
with tab4:
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
                if st.button("📊 Analizar reunión"):
                    meeting_to_analyze = completed_topics[selected_analysis]
                    # 4) Llamar al endpoint
                    payload = {
                        "id_user": user_id,
                        "id_meeting": meeting_to_analyze
                    }
                    analysis_resp = requests.post(f"{API_BASE_URL}/analysis/analyze", json=payload)
                    if analysis_resp.status_code == 200:
                        result_data = analysis_resp.json()
                        # 5) Mostrar resultado
                        st.markdown(f"### 🔍 Resultado del análisis")
                        st.markdown(f"**📌 Conclusiones:** {result_data['conclusions']}")
                        st.markdown(f"**📢 ¿Hace falta la reunión?** {'✅ Sí' if result_data['is_meeting_needed'] else '❌ No'}")
                    else:
                        st.error("No se pudo obtener el análisis de la reunión.")
            else:
                st.info("No hay reuniones completadas para este usuario.")
    else:
        st.info("Ingrese un correo y presione 'Buscar reuniones completadas'.")
