import streamlit as st
import requests
import json

#API_BASE_URL = "http://localhost:8080"
import os

# Si está en Cloud Run, usa la URL pública, de lo contrario usa localhost
#API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8080")
#API_BASE_URL = "https://reunicheck2-app-48606537894.us-central1.run.app"
API_BASE_URL = "https://reunicheck-backend-48606537894.us-central1.run.app"




# Estado de sesión
if "user_email" not in st.session_state:
    st.session_state.user_email = None
if "id_user" not in st.session_state:
    st.session_state.id_user = None
if "id_meeting" not in st.session_state:
    st.session_state.id_meeting = None
if "messages" not in st.session_state:
    st.session_state.messages = []

st.set_page_config(page_title="ReuniCheckACTUALIZADO", page_icon="🔵", layout="wide")

st.markdown("<h1 style='text-align: center;'>🔵 ReuniCheck - Optimización de Reuniones</h1>", unsafe_allow_html=True)
st.markdown("---")

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["👤 Crear Usuario", "📅 Crear Reunión", "❓ Contestar Preguntas", "📊 Obtener Análisis", "🤖 Chat GPT"]
)

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
    #@st.cache_data(ttl=60)
    def load_users():
        users_resp = requests.get(f"{API_BASE_URL}/questions/all_users")

        print("DEBUG status code:", users_resp.status_code)
        print("DEBUG headers:", users_resp.headers)
        print("DEBUG text:", repr(users_resp.text))  # Mostrar contenido exacto de la respuesta

        if users_resp.status_code == 200 and users_resp.text.strip():  # Asegurar que no está vacío
            try:
                return users_resp.json().get("users", [])
            except requests.exceptions.JSONDecodeError as e:
                print("ERROR decodificando JSON:", e)
                return []
        else:
            print("ERROR en la API: Código", users_resp.status_code, "Respuesta vacía")
            return []
      #  return users_resp.json().get("users", []) if users_resp.status_code == 200 else []

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
                    st.info("No hay preguntas pendientes.")
    else:
            st.error("Error al obtener preguntas pendientes.")

# =========================================================
# 📊 Pestaña 4: Obtener análisis
# =========================================================
with tab4:
    st.markdown("## 📊 Análisis de Reuniones")
    st.write("Ingresa un correo y selecciona una reunión para ver su análisis.")

    user_email_analysis = st.text_input("Correo electrónico para análisis", key="email_analysis")

    if st.button("🔍 Buscar reuniones completadas", use_container_width=True):
        resp = requests.post(f"{API_BASE_URL}/chat/start", json={"user_email": user_email_analysis})
        if resp.status_code != 200:
            st.error("No se pudo recuperar información de usuario. Revisa el correo.")
        else:
            data = resp.json()
            st.session_state.user_id = data["id_user"]  # Guardar user_id en sesión
            all_meetings = data["meetings"]

            # Filtrar reuniones con todas las preguntas respondidas
            completed_meetings = [
                m for m in all_meetings if all(q["answered"] for q in requests.post(
                    f"{API_BASE_URL}/questions/pending",
                    json={"id_user": st.session_state.user_id, "id_meeting": str(m["id_meeting"])}
                ).json().get("questions", []))
            ]

            if completed_meetings:
                st.success(f"Se encontraron {len(completed_meetings)} reuniones completadas.")
                completed_topics = {c["topic"]: c["id_meeting"] for c in completed_meetings}

                # Inicializar variable de sesión si no existe
                if "selected_meeting" not in st.session_state:
                    st.session_state.selected_meeting = list(completed_topics.values())[0]

                # Mostrar selectbox con la reunión seleccionada
                selected_analysis = st.selectbox(
                    "Selecciona reunión completada",
                    list(completed_topics.keys()),
                    index=list(completed_topics.values()).index(st.session_state.selected_meeting),
                    key="selected_meeting_box"
                )

                # Guardar la reunión seleccionada en sesión si cambia
                if selected_analysis and st.session_state.selected_meeting != completed_topics[selected_analysis]:
                    st.session_state.selected_meeting = completed_topics[selected_analysis]

    # Si hay una reunión seleccionada, mostrar análisis
    if "selected_meeting" in st.session_state and st.session_state.selected_meeting:
        meeting_to_analyze = st.session_state.selected_meeting
        st.write(f"📌 **Reunión seleccionada:** {meeting_to_analyze}")

        if st.button("📊 Analizar reunión", use_container_width=True):
            with st.spinner("🔄 Procesando análisis, por favor espera..."):
                payload = {"id_user": st.session_state.user_id, "id_meeting": meeting_to_analyze}
                analysis_resp = requests.post(f"{API_BASE_URL}/analysis/analyze", json=payload)

            if analysis_resp.status_code == 200:
                result_data = analysis_resp.json()
                st.markdown("### 🔍 Resultado del análisis")
                if result_data['is_meeting_needed']:
                    st.markdown(
                        """
                        <div style='padding: 20px; border-radius: 10px; background-color: #ffdddd; text-align: center;'>
                            <h2 style='color: #b22222;'>🚨 ¡Esta reunión es necesaria! 🚨</h2>
                            <p style='color: #800000; font-size: 18px;'>Se recomienda proceder con la reunión ya que se han detectado puntos críticos que requieren discusión en equipo.</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        """
                        <div style='padding: 20px; border-radius: 10px; background-color: #ddffdd; text-align: center;'>
                            <h2 style='color: #228B22;'>✅ No es necesaria la reunión ✅</h2>
                            <p style='color: #006400; font-size: 18px;'>Se ha determinado que la reunión no es necesaria y que se pueden tomar decisiones sin necesidad de agendarla.</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                st.markdown(f"**📌 Conclusiones:** {result_data['conclusions']}")

                st.markdown(f"**📢 ¿Hace falta la reunión?** {'✅ Sí' if result_data['is_meeting_needed'] else '❌ No'}")
            else:
                st.error("No se pudo obtener el análisis de la reunión.")

# ============================
# 🤖 Pestaña 5: Chat GPT
# ============================
with tab5:
    st.markdown("## 🤖 Profundizar con GPT")
    st.write("Aquí puedes profundizar más sobre tus respuestas ya dadas y mejorar el análisis posterior.")

    # (1) Pedir correo
    user_email_chat = st.text_input("Correo electrónico para Chat", key="chat_email_input")

    # Botón para buscar reuniones donde el usuario ya tenga respuestas
    if st.button("Buscar reuniones con respuestas ya dadas"):
        if not user_email_chat.strip():
            st.warning("Por favor, ingresa un correo válido.")
        else:
            # 1.a) Obtener id_user llamando a /chat/start
            resp_user = requests.post(
                f"{API_BASE_URL}/chat/start",
                json={"user_email": user_email_chat}
            )
            if resp_user.status_code == 200:
                data_user = resp_user.json()
                st.session_state.id_user = data_user["id_user"]

                # 1.b) Llamar al endpoint que devuelve las reuniones con respuestas
                url_meetings_responded = f"{API_BASE_URL}/answers/meetings_responded/{st.session_state.id_user}"
                resp_meetings = requests.get(url_meetings_responded)

                if resp_meetings.status_code == 200:
                    data_meet = resp_meetings.json()
                    meetings_responded = data_meet.get("meetings", [])

                    if not meetings_responded:
                        st.info("No tienes reuniones con respuestas todavía.")
                        st.session_state.meeting_options_list = []
                    else:
                        st.session_state.meeting_options_list = [
                            (m["id_meeting"], m["topic"]) for m in meetings_responded
                        ]
                        st.success(f"Se encontraron {len(meetings_responded)} reuniones. Selecciónalas abajo.")
                else:
                    st.error("Error al obtener reuniones con respuestas. Revisa tu backend.")
            else:
                st.error("No se encontró el usuario. Verifica el correo e inténtalo de nuevo.")

    # 2) Seleccionar la reunión a profundizar
    if "meeting_options_list" in st.session_state and st.session_state.meeting_options_list:
        combo_dict = {topic: mid for (mid, topic) in st.session_state.meeting_options_list}
        selected_topic = st.selectbox("Selecciona una reunión respondida", list(combo_dict.keys()))

        if selected_topic:
            st.session_state.id_meeting_chat = combo_dict[selected_topic]
            st.write(f"**Reunión seleccionada:** {selected_topic}")

    # 3) Iniciar Chat / Reiniciar Chat
    if st.button("Iniciar / Reiniciar Chat"):
        st.session_state.messages = []  # limpiamos historial
        if st.session_state.get("id_meeting_chat"):
            payload_init = {
                "id_user": st.session_state.id_user,
                "id_meeting": st.session_state.id_meeting_chat,
                "user_response": "INICIO_AUTOMATICO_PROFUNDIZAR"
            }
            init_res = requests.post(f"{API_BASE_URL}/chat/conversation", json=payload_init)
            if init_res.status_code == 200:
                data_init = init_res.json()
                ai_msg = data_init["ai_response"]
                # Guardamos la respuesta de GPT en el historial
                st.session_state.messages.append({"role": "assistant", "content": ai_msg})
                st.success("Chat iniciado automáticamente. GPT te hará preguntas adicionales.")
            else:
                st.error("No se pudo iniciar el chat. Revisa tu backend /chat/conversation.")
        else:
            st.warning("Primero selecciona una reunión de la lista de reuniones respondidas.")

    # 4) Mostrar historial de chat y permitir escribir
    if st.session_state.get("id_meeting_chat"):
        st.write("### Chat con GPT")
        # Mostrar los mensajes
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        # Input para enviar mensajes
        user_input_chat = st.chat_input("Tu mensaje...")
        if user_input_chat:
            st.session_state.messages.append({"role": "user", "content": user_input_chat})
            with st.chat_message("user"):
                st.markdown(user_input_chat)

            payload_user = {
                "id_user": st.session_state.id_user,
                "id_meeting": st.session_state.id_meeting_chat,
                "user_response": user_input_chat
            }
            resp_user_chat = requests.post(f"{API_BASE_URL}/chat/conversation", json=payload_user)
            if resp_user_chat.status_code == 200:
                data_ai = resp_user_chat.json()
                ai_msg = data_ai["ai_response"]
                st.session_state.messages.append({"role": "assistant", "content": ai_msg})
                with st.chat_message("assistant"):
                    st.markdown(ai_msg)
            else:
                st.error("No se pudo continuar la conversación. Revisa tu backend /chat/conversation.")
