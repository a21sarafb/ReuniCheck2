import requests
from supabase import create_client, Client
from ..config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, OPENAI_API_KEY

# Inicializar cliente de Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

class GeneradorPreguntas:
    def __init__(self, api_key):
        self.api_key = api_key
        self.url = "https://api.openai.com/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def generar_preguntas(self, tema, num_preguntas=5):
        """Genera una lista de preguntas relevantes basadas en el tema dado."""
        prompt = (
            f"Genera {num_preguntas} preguntas clave para evaluar el estado actual y posibles soluciones "
            f"sobre el siguiente tema sin necesidad de reunión: \"{tema}\"."
        )

        messages = [
            {"role": "system", "content": "Eres un asistente especializado en optimización de reuniones."},
            {"role": "user", "content": prompt}
        ]

        payload = {
            "model": "gpt-3.5-turbo",
            "messages": messages,
            "max_tokens": 200,
            "temperature": 0.7
        }

        response = requests.post(self.url, headers=self.headers, json=payload)

        if response.status_code == 200:
            response_data = response.json()
            preguntas_generadas = response_data["choices"][0]["message"]["content"]

            # Obtener estadísticas de uso
            input_tokens = response_data["usage"]["prompt_tokens"]
            output_tokens = response_data["usage"]["completion_tokens"]
            total_tokens = response_data["usage"]["total_tokens"]
            cost = (input_tokens * 0.0005 + output_tokens * 0.0015)  # Cálculo del costo

            # Guardar en Supabase
            data = {
                "model": payload["model"],
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "cost": round(cost, 6)
            }
            supabase.table("openai_requests").insert(data).execute()
            return preguntas_generadas.split("\n")  # Retorna la lista de preguntas
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return None

class AnalizadorReunion:
    def analizar_necesidad_reunion(self, contexto):
        """Analiza la necesidad de una reunión basándose en el contexto proporcionado."""
        messages = [
            {"role": "system",
             "content": "Eres un asistente experto en gestión de reuniones. Se te proporcionará el contexto de una reunión con preguntas y respuestas. Debes analizar la información y determinar si la reunión es necesaria o si se pueden resolver los puntos sin reunión."},
            {"role": "user", "content": contexto}
        ]

        payload = {
            "model": "gpt-3.5-turbo",
            "messages": messages,
            "max_tokens": 500,
            "temperature": 0.5
        }

        response = requests.post(self.url, headers=self.headers, json=payload)

        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"].strip()
        else:
            print(f"Error en la solicitud a OpenAI: {response.status_code} - {response.text}")
            return None