from app.database.supabase_api import insert_data

def create_user(name: str, email: str):
    """ Función para insertar un usuario en la base de datos """
    data = {"name": name, "email": email, "rol": "participant"}
    response = insert_data("user", data)
    return response
