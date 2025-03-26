import streamlit as st
import requests
import json
import os
from datetime import datetime

# URL del API
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

# Configuración de la página
st.set_page_config(
    page_title="ReuniCheck", 
    page_icon="🔵", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado con soporte para modo oscuro
st.markdown("""
<style>
    /* Estilos generales */
    .block-container {
        padding-top: 2rem;
    }
    .main-header {
        background: linear-gradient(90deg, #1e3c72, #2a5298);
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white !important;
        text-align: center;
    }
    
    /* Estilos para contenedores en modo claro/oscuro */
    .st-emotion-cache-1r6slb0, .st-emotion-cache-keje6w {
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
    }
    
    /* Modo claro */
    [data-theme="light"] .st-emotion-cache-1r6slb0, 
    [data-theme="light"] .st-emotion-cache-keje6w,
    [data-theme="light"] .stTabs [data-baseweb="tab-panel"] {
        background-color: white;
        color: #31333F;
    }
    
    /* Modo oscuro */
    [data-theme="dark"] .st-emotion-cache-1r6slb0, 
    [data-theme="dark"] .st-emotion-cache-keje6w,
    [data-theme="dark"] .stTabs [data-baseweb="tab-panel"] {
        background-color: #262730;
        color: white;
    }
    
    /* Estilo para las pestañas - compatible con modo oscuro */
    .stTabs [data-baseweb="tab-panel"] {
        padding: 1.5rem;
        border-radius: 0 0 10px 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    /* Cajas de mensajes */
    .success-box {
        padding: 1rem;
        border-radius: 5px;
        background-color: rgba(40, 167, 69, 0.2);
        border-left: 5px solid #28a745;
    }
    .warning-box {
        padding: 1rem;
        border-radius: 5px;
        background-color: rgba(255, 193, 7, 0.2);
        border-left: 5px solid #ffc107;
    }
    .error-box {
        padding: 1rem;
        border-radius: 5px;
        background-color: rgba(220, 53, 69, 0.2);
        border-left: 5px solid #dc3545;
    }
    .info-box {
        padding: 1rem;
        border-radius: 5px;
        background-color: rgba(23, 162, 184, 0.2);
        border-left: 5px solid #17a2b8;
    }
    
    /* Estilos para texto en las cajas de alerta */
    [data-theme="dark"] .success-box, 
    [data-theme="dark"] .warning-box, 
    [data-theme="dark"] .error-box, 
    [data-theme="dark"] .info-box {
        color: white;
    }
    
    /* Botones - compatibles con modo oscuro */
    .stButton>button {
        background-color: #1e3c72;
        color: white !important;
        border-radius: 5px;
        border: none;
        margin-top: 2%;
        transition: background-color 0.3s ease, transform 0.3s ease, box-shadow 0.3s ease;
    }

    .stButton>button:hover {
        background-color: #2a5298;
        transform: translateY(-3px);
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2);
    }

    .stButton>button:active {
        background-color: #1e3c72;
        transform: translateY(0);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }

    /* Mejora de los efectos hover en tarjetas */
    .custom-card {
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    /* Modo claro */
    [data-theme="light"] .custom-card {
        background-color: white;
    }
    
    /* Modo oscuro */
    [data-theme="dark"] .custom-card {
        background-color: #262730;
    }

    .custom-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 20px rgba(0, 0, 0, 0.15);
    }

    /* Estilos para pestañas */
    /* Modo claro */
    [data-theme="light"] .stTabs [data-baseweb="tab"] {
        background-color: #f0f2f6;
        color: #31333F;
    }
    
    /* Modo oscuro */
    [data-theme="dark"] .stTabs [data-baseweb="tab"] {
        background-color: #1E1E1E;
        color: #FAFAFA;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px 10px 0 0;
        padding: 10px 16px;
        margin-right: 4px;
        transition: background-color 0.3s ease, color 0.3s ease;
    }

    .stTabs [aria-selected="true"] {
        background-color: #1e3c72 !important;
        color: white !important;
    }

    .stTabs [data-baseweb="tab"]:hover {
        background-color: #d1e0f5;
        cursor: pointer;
    }
    
    /* Modo oscuro - hover de pestañas */
    [data-theme="dark"] .stTabs [data-baseweb="tab"]:hover {
        background-color: #3A3A3A;
    }

    /* Alineación vertical para botones */
    .v-align-middle {
        display: flex;
        align-items: flex-end;
        height: 100%;
    }
    .v-align-middle button {
        margin-bottom: 0.2rem;
    }
    
    /* Tarjetas de análisis en modo oscuro */
    [data-theme="dark"] div[style*="background-color: #ffdddd"] {
        background-color: rgba(178, 34, 34, 0.3) !important;
    }
    
    [data-theme="dark"] div[style*="background-color: #ddffdd"] {
        background-color: rgba(34, 139, 34, 0.3) !important;
    }
    
    /* Asegurar que el texto siempre sea legible */
    [data-theme="dark"] h2[style*="color: #b22222"],
    [data-theme="dark"] p[style*="color: #800000"] {
        color: #ff6666 !important;
    }
    
    [data-theme="dark"] h2[style*="color: #228B22"],
    [data-theme="dark"] p[style*="color: #006400"] {
        color: #66ff66 !important;
    }
    
    /* Footer en modo oscuro */
    [data-theme="dark"] div[style*="background-color: #f0f2f6"] {
        background-color: #1E1E1E !important;
    }
    
    /* Enlaces en el footer para modo oscuro */
    [data-theme="dark"] a[style*="color: #1e3c72"] {
        color: #77a1ff !important;
    }
    
    /* Texto del footer en modo oscuro */
    [data-theme="dark"] div[style*="background-color: #f0f2f6"] p,
    [data-theme="dark"] div[style*="background-color: #f0f2f6"] span,
    [data-theme="dark"] div[style*="background-color: #f0f2f6"] strong {
        color: white !important;
    }

    /* Footer personalizado */
    .custom-footer {
        text-align: center;
        margin-top: 2rem;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 -2px 5px rgba(0,0,0,0.05);
    }
    
    /* Modo claro */
    [data-theme="light"] .custom-footer {
        background-color: #f0f2f6;
        color: #31333F;
    }
    
    /* Modo oscuro */
    [data-theme="dark"] .custom-footer {
        background-color: #1E1E1E;
        color: #FAFAFA;
    }
    
    /* Enlaces en footer */
    .custom-footer a {
        text-decoration: none;
        margin: 0 10px;
    }
    
    [data-theme="light"] .custom-footer a {
        color: #1e3c72;
    }
    
    [data-theme="dark"] .custom-footer a {
        color: #77a1ff;
    }
</style>
""", unsafe_allow_html=True)

# Cabecera principal
st.markdown('<div class="main-header"><h1>🔵 ReuniCheck</h1><p style="font-size: 1.2rem; margin: 0;">Optimiza tus reuniones • Maximiza la productividad</p></div>', unsafe_allow_html=True)

# Tabs principales
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "👤 Crear usuario", 
    "📅 Crear reunión", 
    "❓ Contestar preguntas", 
    "🤖 Chat", 
    "📊 Obtener análisis"
])

# =========================================================
# 🟢 Opción 1: Crear usuario
# =========================================================
with tab1:
    st.markdown("## 👤 Crear usuario")
    st.markdown("Registra un nuevo usuario para participar en reuniones. Completa los siguientes datos:")
    
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            name_input = st.text_input("Nombre completo", key="name_user", placeholder="Ej: Juan Pérez")
        with col2:
            email_input = st.text_input("Correo electrónico", key="email_user", placeholder="Ej: juan.perez@empresa.com")
        
        submit_button = st.button("✅ Crear usuario", use_container_width=True)
        
        if submit_button:
            if not name_input or not email_input:
                st.markdown('<div class="warning-box">⚠️ Por favor completa todos los campos.</div>', unsafe_allow_html=True)
            else:
                with st.spinner("Procesando..."):
                    payload = {"name": name_input, "email": email_input}
                    response = requests.post(f"{API_BASE_URL}/questions/users/", json=payload)
                
                if response.status_code == 200:
                    st.markdown('<div class="success-box">✅ Usuario creado exitosamente.</div>', unsafe_allow_html=True)
                    st.balloons()
                    st.session_state.user_email = email_input
                else:
                    st.markdown('<div class="error-box">⚠️ No se pudo crear el usuario. Intenta de nuevo.</div>', unsafe_allow_html=True)

# =========================================================
# 🔵 Opción 2: Crear reunión
# =========================================================
with tab2:
    st.markdown("## 📅 Crear reunión")
    st.markdown("Configura una nueva reunión definiendo el tema y seleccionando los participantes.")
    
    with st.container():
        # Cargar lista de usuarios 
        def load_users():
            users_resp = requests.get(f"{API_BASE_URL}/questions/all_users")
            if users_resp.status_code == 200 and users_resp.text.strip():
                try:
                    return users_resp.json().get("users", [])
                except requests.exceptions.JSONDecodeError:
                    return []
            else:
                return []

        all_users = load_users()
        email_options = [u["email"] for u in all_users]

        with st.form("create_meeting_form"):
            st.markdown("### Detalles de la reunión")
            
            topic_input = st.text_input(
                "Tema de la reunión", 
                help="Define el tema principal que se abordará",
                placeholder="Ej: Revisión de hitos del proyecto X"
            )
            
            st.markdown("### Participantes")
            selected_emails = st.multiselect(
                "Selecciona los correos de los participantes",
                options=email_options,
                default=[]
            )
            
            st.markdown("---")
            create_button = st.form_submit_button("🚀 Crear reunión", use_container_width=True)

        if create_button:
            if not topic_input:
                st.markdown('<div class="warning-box">⚠️ Por favor, ingresa el tema de la reunión.</div>', unsafe_allow_html=True)
            elif not selected_emails:
                st.markdown('<div class="warning-box">⚠️ Debes seleccionar al menos un participante.</div>', unsafe_allow_html=True)
            else:
                normalized_emails = [email.strip().lower() for email in selected_emails]
                payload = {"topic": topic_input.strip(), "users": normalized_emails}

                with st.spinner("⏱️ Creando reunión y generando preguntas..."):
                    response = requests.post(f"{API_BASE_URL}/questions/meetings/", json=payload)

                if response.status_code == 200:
                    st.markdown('<div class="success-box">✅ Reunión creada y preguntas generadas exitosamente.</div>', unsafe_allow_html=True)
                    st.balloons()
                else:
                    st.markdown(f'<div class="error-box">⚠️ Error al crear la reunión (código {response.status_code}).</div>', unsafe_allow_html=True)
                    st.error("Respuesta del servidor: " + response.text)

# =========================================================
# ❓ Opción 3: Contestar preguntas
# =========================================================
with tab3:
    st.markdown("## ❓ Contestar preguntas")
    st.markdown("Responde a las preguntas de las reuniones en las que participas.")
    
    with st.container():
        if st.session_state.user_email is None:
            col1, col2 = st.columns([3, 1])
            with col1:
                email_input = st.text_input(
                    "Correo electrónico", 
                    key="email_login",
                    placeholder="Ingresa tu correo para iniciar sesión"
                )
            with col2:
                st.markdown('<div class="v-align-middle">', unsafe_allow_html=True)
                login_button = st.button("🔑 Iniciar sesión", use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            if login_button:
                if not email_input:
                    st.markdown('<div class="warning-box">⚠️ Por favor, ingresa tu correo electrónico.</div>', unsafe_allow_html=True)
                else:
                    with st.spinner("Verificando usuario..."):
                        response = requests.post(f"{API_BASE_URL}/chat/start", json={"user_email": email_input})
                    
                    if response.status_code == 200:
                        data = response.json()
                        st.session_state.user_email = str(email_input)
                        st.session_state.id_user = str(data["id_user"])
                    else:
                        st.markdown('<div class="error-box">⚠️ Usuario no encontrado. Verifica tu correo.</div>', unsafe_allow_html=True)
        
        if st.session_state.user_email:
            st.markdown(f'<div class="info-box">👋 Bienvenido/a, <strong>{st.session_state.user_email}</strong></div>', unsafe_allow_html=True)
            st.markdown("### 📅 Reuniones disponibles")
            
            with st.spinner("Cargando reuniones..."):
                response = requests.post(f"{API_BASE_URL}/chat/start", json={"user_email": st.session_state.user_email})
            
            if response.status_code == 200:
                data = response.json()
                meetings = data.get("meetings", [])
                
                if meetings:
                    meeting_options = {m["topic"]: m["id_meeting"] for m in meetings}
                    
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        selected_meeting = st.selectbox(
                            "Selecciona una reunión para responder preguntas",
                            list(meeting_options.keys())
                        )
                    with col2:
                        st.markdown('<div class="v-align-middle">', unsafe_allow_html=True)
                        continue_button = st.button("▶️ Continuar", use_container_width=True)
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    if continue_button:
                        st.session_state.id_meeting = str(meeting_options[selected_meeting])
                else:
                    st.markdown('<div class="info-box">🔹 No tienes reuniones asignadas. Contacta al administrador.</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="error-box">⚠️ No se pudieron recuperar las reuniones.</div>', unsafe_allow_html=True)
        
        if st.session_state.id_meeting:
            st.markdown("### Preguntas pendientes")
            
            with st.spinner("Cargando preguntas..."):
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
                    with st.form("answer_questions_form"):
                        st.markdown('<div class="warning-box">⚠️ Tienes preguntas pendientes por responder.</div>', unsafe_allow_html=True)
                        
                        for i, question in enumerate(unanswered):
                            response_key = f"resp_{question['id_question']}"
                            st.markdown(f"**Pregunta:** {question['content']}")
                            st.text_area("Tu respuesta:", key=response_key, height=100)
                            st.markdown("---")
                        
                        submit_answers = st.form_submit_button("💾 Guardar respuestas", use_container_width=True)
                    
                    if submit_answers:
                        with st.spinner("Guardando respuestas..."):
                            success_count = 0
                            for question in unanswered:
                                user_answer = st.session_state.get(f"resp_{question['id_question']}", "").strip()
                                if user_answer:
                                    answer_data = {
                                        "id_question": question["id_question"],
                                        "id_user": st.session_state.id_user,
                                        "id_meeting": st.session_state.id_meeting,
                                        "content": user_answer
                                    }
                                    resp = requests.post(f"{API_BASE_URL}/answers/create", json=answer_data)
                                    if resp.status_code == 200:
                                        success_count += 1
                        
                        if success_count > 0:
                            st.markdown('<div class="success-box">✅ ¡Respuestas guardadas correctamente!</div>', unsafe_allow_html=True)
                            # Limpiar el estado de la reunión para actualizar las preguntas
                            st.session_state.id_meeting = None
                        else:
                            st.markdown('<div class="error-box">⚠️ No se guardaron respuestas. Asegúrate de completar al menos una.</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="success-box">✅ ¡Felicidades! No hay preguntas pendientes para esta reunión.</div>', unsafe_allow_html=True)
                    
                    # Mostrar las preguntas ya respondidas
                    answered_questions = [q for q in questions_list if q["answered"]]
                    if answered_questions:
                        with st.expander("Ver mis respuestas anteriores"):
                            for i, question in enumerate(answered_questions):
                                st.markdown(f"**Pregunta:** {question['content']}")
                                st.markdown(f"*Tu respuesta:* {question['answer']}")
                                st.markdown("---")
            else:
                st.markdown('<div class="error-box">⚠️ Error al obtener las preguntas de la reunión.</div>', unsafe_allow_html=True)

# ============================
# 🤖 Pestaña 4: Chat GPT
# ============================
with tab4:
    st.markdown("## 🤖 Profundiza más con GPT")
    st.markdown("Aquí puedes profundizar más sobre tus respuestas ya dadas y mejorar el análisis posterior.")
    
    with st.container():
        # Sección de inicio de sesión
        col1, col2 = st.columns([3, 1])
        with col1:
            user_email_chat = st.text_input(
                "Correo electrónico", 
                key="chat_email_input",
                placeholder="Ingresa tu correo para acceder al chat"
            )
        with col2:
            st.markdown('<div class="v-align-middle">', unsafe_allow_html=True)
            search_button = st.button("Buscar reuniones (con preguntas respondidas)", use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        if search_button:
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
        
        # Sección de selección de reunión
        if "meeting_options_list" in st.session_state and st.session_state.meeting_options_list:
            combo_dict = {topic: mid for (mid, topic) in st.session_state.meeting_options_list}
            selected_topic = st.selectbox("Selecciona una reunión de la lista", list(combo_dict.keys()))

            if selected_topic:
                st.session_state.id_meeting_chat = combo_dict[selected_topic]
                st.write(f"**Reunión seleccionada:** {selected_topic}")
                
                if st.button("Iniciar chat", use_container_width=True):
                    st.session_state.messages = []  # Limpiamos historial
                    
                    with st.spinner("Iniciando chat con IA..."):
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
                        st.success("Chat iniciado. GPT te hará preguntas adicionales.")
                    else:
                        st.error("No se pudo iniciar el chat.")
                else:
                    st.warning("Primero selecciona una reunión de la lista de reuniones.")
    
    # Mostrar historial de chat y permitir escribir
    if st.session_state.get("id_meeting_chat") and st.session_state.messages:
        st.markdown("### Chat")
        
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
            
            with st.spinner("La IA está procesando tu mensaje..."):
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
                st.error("No se pudo continuar la conversación")

# =========================================================
# 📊 Pestaña 5: Obtener análisis
# =========================================================
with tab5:
    st.markdown("## 📊 Análisis de reuniones")
    st.markdown("Determina si una reunión es necesaria basándose en las respuestas de los participantes.")
    
    with st.container():
        col1, col2 = st.columns([3, 1])
        with col1:
            user_email_analysis = st.text_input(
                "Correo electrónico", 
                key="email_analysis",
                placeholder="Ingresa tu correo para acceder a los análisis"
            )
        with col2:
            st.markdown('<div class="v-align-middle">', unsafe_allow_html=True)
            search_button = st.button("🔍 Buscar reuniones", key="search_analysis", use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        if search_button:
            if not user_email_analysis.strip():
                st.markdown('<div class="warning-box">⚠️ Por favor, ingresa un correo válido.</div>', unsafe_allow_html=True)
            else:
                with st.spinner("Buscando información del usuario..."):
                    resp = requests.post(f"{API_BASE_URL}/chat/start", json={"user_email": user_email_analysis})
                
                if resp.status_code != 200:
                    st.markdown('<div class="error-box">⚠️ No se pudo recuperar información de usuario. Revisa el correo.</div>', unsafe_allow_html=True)
                else:
                    data = resp.json()
                    st.session_state.user_id = data["id_user"]  # Guardar user_id en sesión
                    all_meetings = data["meetings"]
                    
                    # Filtrar reuniones con todas las preguntas respondidas
                    completed_meetings = []
                    
                    with st.spinner("Buscando reuniones completas..."):
                        for m in all_meetings:
                            pending_resp = requests.post(
                                f"{API_BASE_URL}/questions/pending",
                                json={"id_user": st.session_state.user_id, "id_meeting": str(m["id_meeting"])}
                            )
                            
                            if pending_resp.status_code == 200:
                                questions = pending_resp.json().get("questions", [])
                                if questions and all(q["answered"] for q in questions):
                                    completed_meetings.append(m)
                    
                    if completed_meetings:
                        st.markdown('<div class="success-box">✅ Se encontraron reuniones que pueden ser analizadas.</div>', unsafe_allow_html=True)
                        completed_topics = {c["topic"]: c["id_meeting"] for c in completed_meetings}
                        
                        # Inicializar variable de sesión si no existe
                        if "selected_meeting" not in st.session_state:
                            st.session_state.selected_meeting = list(completed_topics.values())[0]
                        
                        # Mostrar selectbox con la reunión seleccionada
                        selected_analysis = st.selectbox(
                            "Selecciona una reunión para analizar",
                            list(completed_topics.keys()),
                            index=list(completed_topics.values()).index(st.session_state.selected_meeting),
                            key="selected_meeting_box"
                        )
                        
                        # Guardar la reunión seleccionada en sesión si cambia
                        if selected_analysis and st.session_state.selected_meeting != completed_topics[selected_analysis]:
                            st.session_state.selected_meeting = completed_topics[selected_analysis]
                    else:
                        st.markdown('<div class="info-box">ℹ️ No se encontraron reuniones completas. Para realizar un análisis, todas las preguntas deben estar respondidas.</div>', unsafe_allow_html=True)
        
        # Si hay una reunión seleccionada, mostrar botón de análisis
        if "selected_meeting" in st.session_state and st.session_state.selected_meeting:
            meeting_to_analyze = st.session_state.selected_meeting
            
            analyze_button = st.button("📊 Analizar reunión", key="analyze_button", use_container_width=True)
            
            if analyze_button:
                with st.spinner("🔄 Procesando análisis, por favor espera..."):
                    payload = {"id_user": st.session_state.user_id, "id_meeting": meeting_to_analyze}
                    analysis_resp = requests.post(f"{API_BASE_URL}/analysis/analyze", json=payload)
                
                if analysis_resp.status_code == 200:
                    result_data = analysis_resp.json()
                    
                    # Mostrar resultados con mejor diseño
                    st.markdown("### 📋 Resultados del análisis")
                    
                    # Tarjeta de conclusión principal
                    if result_data['is_meeting_needed']:
                        st.markdown(
                            """
                            <div style='padding: 20px; border-radius: 10px; background-color: #ffdddd; text-align: center; margin-bottom: 20px;'>
                                <h2 style='color: #b22222;'>🚨 Esta reunión es necesaria</h2>
                                <p style='color: #800000; font-size: 18px;'>Se recomienda proceder con la reunión ya que se han detectado puntos críticos que requieren discusión en equipo.</p>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                    else:
                        st.markdown(
                            """
                            <div style='padding: 20px; border-radius: 10px; background-color: #ddffdd; text-align: center; margin-bottom: 20px;'>
                                <h2 style='color: #228B22;'>✅ La reunión NO es necesaria</h2>
                                <p style='color: #006400; font-size: 18px;'>Se ha determinado que los objetivos pueden alcanzarse sin necesidad de una reunión formal.</p>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                    
                    with st.container():
                        st.markdown("#### 🧠 Análisis detallado")
                        st.markdown(f"{result_data['conclusions']}")
                    
                    with st.container():
                        st.markdown("#### 💡 Recomendaciones")
                        if result_data['is_meeting_needed']:
                            st.markdown("""
                            * Programa la reunión lo antes posible
                            * Establece una agenda clara basada en los puntos identificados
                            * Limita la duración a lo estrictamente necesario
                            * Invita solo a los participantes esenciales
                            """)
                        else:
                            st.markdown("""
                            * Comunica las conclusiones por correo electrónico
                            * Establece tareas individuales para cada participante
                            * Programa un seguimiento asíncrono para verificar avances
                            * Considera una breve consulta individual con personas clave
                            """)
                    
                    # Añadir timestamp del análisis
                    now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                    st.markdown(f"<p style='text-align: right; color: #666; font-size: 0.8rem;'>Análisis generado el {now}</p>", unsafe_allow_html=True)
                else:
                    st.markdown('<div class="error-box">⚠️ No se pudo obtener el análisis de la reunión.</div>', unsafe_allow_html=True)

# Footer
current_year = datetime.now().year
st.markdown(f"""
<div class="custom-footer">
    <div>
        <strong>🔵 ReuniCheck</strong>
    </div>
    <p>Optimiza tus reuniones • Maximiza la productividad</p>
    <div>
        <span>© {current_year} ReuniCheck | Todos los derechos reservados</span>
        <div style="margin-top: 0.5rem;">
            <a href="#">Contacto</a> | 
            <a href="#">Ayuda</a> | 
            <a href="#">Términos</a>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

