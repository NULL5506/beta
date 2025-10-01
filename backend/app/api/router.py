# backend/app/api/router.py
from fastapi import APIRouter

# O caminho correto para o import é DENTRO da pasta v1
from app.api.v1.endpoints import parking

api_router = APIRouter()

# O prefixo correto para a URL inclui o /v1
api_router.include_router(parking.router, prefix="/v1/parking", tags=["Parking Analysis"])