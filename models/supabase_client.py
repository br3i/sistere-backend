from supabase import create_client
import os
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../.env")
load_dotenv(dotenv_path)

# Configuración de Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL", "Not found")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "Not found")

# Crear el cliente de Supabase
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
