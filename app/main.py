
import os
import uvicorn
from app.config.db import SessionLocal, create_all_tables
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.router import routes

try:
    create_all_tables()
except Exception as e:
    raise HTTPException(status_code=500, detail=f"Error al crear tablas: {e}")

app = FastAPI()


app.include_router(routes)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
