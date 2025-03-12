from fastapi.testclient import TestClient
from app.main import app
import pytest

client = TestClient(app)

# Test de conexión básica
def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hola Mundo"}

# Test de obtención de preguntas
def test_get_questions():
    response = client.get("/questions/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)  # Suponiendo que devuelve una lista de preguntas

# Test de envío de mensaje al chat
def test_chat_message():
    message_data = {"question": "¿Cómo funciona el sistema?"}
    response = client.post("/chat/", json=message_data)
    assert response.status_code == 200
    assert "response" in response.json()  # Verificar que hay una respuesta en el JSON

# Test de análisis de reunión
def test_analysis():
    analysis_data = {"meeting_id": 1}
    response = client.get("/analysis/1")
    assert response.status_code == 200
    assert "summary" in response.json()  # Suponiendo que devuelve un resumen de la reunión

# Test de respuestas registradas
def test_answers():
    response = client.get("/answers/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@pytest.fixture(autouse=True)
def cleanup_db():
    # Aquí podrías agregar código para limpiar la base de datos si fuera necesario
    yield  # Ejecutar el test
    # Aquí se ejecutaría la limpieza después de cada test

def test_e2e_flow():
    # 1️⃣ Enviar una pregunta
    question_data = {"question": "¿Qué es FastAPI?"}
    response_question = client.post("/chat/", json=question_data)
    assert response_question.status_code == 200

    # 2️⃣ Obtener análisis de la reunión
    response_analysis = client.get("/analysis/1")
    assert response_analysis.status_code == 200

    # 3️⃣ Verificar respuestas almacenadas
    response_answers = client.get("/answers/")
    assert response_answers.status_code == 200
