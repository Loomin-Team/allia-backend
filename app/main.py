from fastapi import FastAPI, HTTPException
from app.config.db import create_all_tables
from app.auth.routes import auth  # Importamos las rutas de auth
from app.config.routes import prefix  # Importamos el prefijo desde la configuración

# Crea las tablas en la base de datos si no existen
try:
    create_all_tables()
except Exception as e:
    raise HTTPException(status_code=500, detail=f"Error al crear tablas: {e}")

# Inicializa la aplicación FastAPI
app = FastAPI()

# Incluye las rutas de auth en la aplicación con el prefijo adecuado
app.include_router(auth, prefix=prefix, tags=["Auth"])

#