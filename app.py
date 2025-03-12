import streamlit as st
import requests
import os

# Configuración de la API
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8080")

# Inicializar estado de sesión
for key in ["user_email", "id_user", "id_meeting", "messages"]:
    st.session_state.setdefault(key, None if key != "messages" else [])

st.set_page_config(page_title="ReuniCheck", page_icon="🔵", layout="wide")
st.markdown("<h1 style='text-align: center;'>🔵 ReuniCheck - Optimización de Reuniones</h1>", unsafe_allow_html=True)
st.markdown("---")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "👤 Crear Usuario", "📅 Crear Reunión", "❓ Contestar Preguntas", "📊 Obtener Análisis", "🤖 Chat GPT"
])

# ================================================
# 🟢 Crear usuario
# ================================================
with tab1:
    st.markdown("## 👤 Crear Usuario")
    name_input, email_input = st.text_input("Nombre completo"), st.text_input("Correo electrónico")

    if st.button("Crear Usuario", use_container_width=True):
        response = requests.post(f"{API_BASE_URL}/questions/users/", json={"name": name_input, "email": email_input})
        if response.status_code == 200:
            st.toast("✅ Usuario creado exitosamente.")
            st.session_state.user_email = email_input
        else:
            st.error("⚠️ No se pudo crear el usuario. Intenta de nuevo.")


# ================================================
# 🔵 Crear reunión
# ================================================
@st.cache_data
def load_users():
    response = requests.get(f"{API_BASE_URL}/questions/all_users")
    return response.json().get("users", []) if response.status_code == 200 else []


with tab2:
    st.markdown("## 📅 Crear Reunión")
    all_users = load_users()
    email_options = [u["email"] for u in all_users]

    with st.form("create_meeting_form"):
        topic_input = st.text_input("Tema de la reunión")
        selected_emails = st.multiselect("Participantes", options=email_options, default=[])
        create_button = st.form_submit_button("📌 Crear Reunión")

    if create_button:
        response = requests.post(f"{API_BASE_URL}/questions/meetings/",
                                 json={"topic": topic_input.strip(), "users": selected_emails})
        if response.status_code == 200:
            st.success("✅ Reunión creada exitosamente.")
            st.balloons()
        else:
            st.error(f"⚠️ Error al crear la reunión ({response.status_code}).")

# ================================================
# ❓ Contestar preguntas
# ================================================
with tab3:
    st.markdown("## ❓ Contestar Preguntas")
    if st.session_state.user_email is None:
        email_input = st.text_input("Correo electrónico")
        if st.button("Iniciar sesión", use_container_width=True):
            response = requests.post(f"{API_BASE_URL}/chat/start", json={"user_email": email_input})
            if response.status_code == 200:
                data = response.json()
                st.session_state.user_email = email_input
                st.session_state.id_user = data["id_user"]
            else:
                st.error("⚠️ Usuario no encontrado. Verifica tu correo.")

    if st.session_state.user_email:
        response = requests.post(f"{API_BASE_URL}/chat/start", json={"user_email": st.session_state.user_email})
        if response.status_code == 200:
            meetings = response.json().get("meetings", [])
            if meetings:
                meeting_options = {m["topic"]: m["id_meeting"] for m in meetings}
                selected_meeting = st.selectbox("Selecciona una reunión", list(meeting_options.keys()))
                if st.button("Continuar con la reunión", use_container_width=True):
                    st.session_state.id_meeting = meeting_options[selected_meeting]
            else:
                st.info("🔹 No tienes reuniones asignadas.")
        else:
            st.error("⚠️ No se pudieron recuperar las reuniones.")

    if st.session_state.id_meeting:
        pending_resp = requests.post(
            f"{API_BASE_URL}/questions/pending",
            json={"id_user": st.session_state.id_user, "id_meeting": st.session_state.id_meeting}
        )
        if pending_resp.status_code == 200:
            questions = pending_resp.json().get("questions", [])
            unanswered = [q for q in questions if not q["answered"]]

            if unanswered:
                for q in unanswered:
                    st.text_input(f"{q['content']}", key=f"resp_{q['id_question']}")
                if st.button("Guardar Respuestas"):
                    for q in unanswered:
                        answer_data = {
                            "id_question": q["id_question"],
                            "id_user": st.session_state.id_user,
                            "id_meeting": st.session_state.id_meeting,
                            "content": st.session_state.get(f"resp_{q['id_question']}", "")
                        }
                        requests.post(f"{API_BASE_URL}/answers/create", json=answer_data)
                    st.success("¡Respuestas guardadas!")
            else:
                st.info("No hay preguntas pendientes.")
        else:
            st.error("Error al obtener preguntas.")

# ================================================
# 📊 Obtener análisis
# ================================================
with tab4:
    st.markdown("## 📊 Análisis de Reuniones")
    user_email_analysis = st.text_input("Correo electrónico para análisis")

    if st.button("🔍 Buscar reuniones completadas", use_container_width=True):
        resp = requests.post(f"{API_BASE_URL}/chat/start", json={"user_email": user_email_analysis})
        if resp.status_code == 200:
            data = resp.json()
            st.session_state.user_id = data["id_user"]
            meetings = [m for m in data["meetings"] if all(q["answered"] for q in requests.post(
                f"{API_BASE_URL}/questions/pending", json={"id_user": data["id_user"], "id_meeting": m["id_meeting"]}
            ).json().get("questions", []))]

            if meetings:
                selected_analysis = st.selectbox("Selecciona reunión", [m["topic"] for m in meetings])
                if st.button("📊 Analizar reunión", use_container_width=True):
                    analysis_resp = requests.post(f"{API_BASE_URL}/analysis/analyze",
                                                  json={"id_user": st.session_state.user_id,
                                                        "id_meeting": selected_analysis})
                    if analysis_resp.status_code == 200:
                        result_data = analysis_resp.json()
                        st.markdown(f"**📌 Conclusiones:** {result_data['conclusions']}")
                    else:
                        st.error("⚠️ No se pudo obtener el análisis.")
