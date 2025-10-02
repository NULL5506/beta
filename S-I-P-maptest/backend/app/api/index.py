import sys
import os

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.api.router import api_router
import logging

# Configurar logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="S-I-P API",
    description="APIs do projeto S-I-P - Sistema de Identificação de Vagas de Estacionamento",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir rotas da API
app.include_router(api_router, prefix="/api")

# Endpoint de verificação de saúde
@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "ok",
        "message": "API is healthy",
        "version": "1.0.0",
        "platform": "Vercel Serverless"
    }

# Endpoint raiz
@app.get("/", include_in_schema=False)
def read_root():
    return {
        "message": "Bem-vindo à API do S-I-P",
        "documentation": "/docs",
        "health": "/health"
    }

# Handler para Vercel
handler = app