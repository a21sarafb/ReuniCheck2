import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Cargar variables de entorno desde el archivo .env
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise ValueError("Missing Supabase URL or Service Role Key in environment variables.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

def insert_data(table: str, data: dict):
    """Insertar un registro en una tabla de Supabase."""
    return supabase.table(table).insert(data).execute()

def update_data(table: str, filters: dict, updates: dict):
    """Actualizar registros en una tabla de Supabase."""
    query = supabase.table(table).update(updates)
    for key, value in filters.items():
        query = query.eq(key, value)
    return query.execute()

def select_data(table: str, filters: dict = None):
    """Seleccionar registros de una tabla de Supabase."""
    query = supabase.table(table).select("*")

    if filters:
        for key, value in filters.items():
            if isinstance(value, list):
                query = query.in_(key, value)
            else:
                query = query.eq(key, value)

    return query.execute()
