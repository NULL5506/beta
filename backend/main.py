# backend/app/main.py

from fastapi import FastAPI
# CORREÇÃO 1: Importar de 'app.api.router'
from app.api.router import api_router 


app = FastAPI(
    title="S-I-P API",
    description="APIs do projeto S-I-P.",
    version="1.0.0"
)

# CORREÇÃO 2: Aplicar apenas o prefixo geral '/api'
app.include_router(api_router, prefix="/api")

# Endpoint de verificação de saúde
@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "message": "API is healthy"}

# Endpoint raiz (opcional, mas bom para testes)
@app.get("/", include_in_schema=False)
def read_root():
    return {"message": "Bem-vindo à API do S-I-P. Vá para /docs para a documentação."}