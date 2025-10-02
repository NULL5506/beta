from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.router import api_router
import logging
import os

# Configurar logs antes de iniciar a aplicação
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Suprimir logs verbosos
logging.getLogger('selenium').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('WDM').setLevel(logging.ERROR)

# Variáveis de ambiente para ChromeDriver
os.environ['WDM_LOG_LEVEL'] = '0'
os.environ['WDM_PRINT_FIRST_LINE'] = 'False'

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
    allow_origins=["*"],  # Em produção, especifique domínios permitidos
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
        "version": "1.0.0"
    }

# Endpoint raiz
@app.get("/", include_in_schema=False)
def read_root():
    return {
        "message": "Bem-vindo à API do S-I-P",
        "documentation": "/docs",
        "health": "/health"
    }

# Evento de startup
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Iniciando S-I-P API...")
    logger.info("📚 Documentação disponível em: /docs")
    logger.info("✅ API pronta para receber requisições")

# Evento de shutdown
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("👋 Encerrando S-I-P API...")