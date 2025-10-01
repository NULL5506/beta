from pydantic import BaseModel, Field
from typing import List

class PontoGPS(BaseModel):
    lat: float = Field(..., example=-10.9472, description="Latitude do ponto")
    lon: float = Field(..., example=-37.0731, description="Longitude do ponto")

class AnaliseRequest(BaseModel):
    pontos: List[PontoGPS] = Field(..., min_items=3, description="Pelo menos 3 pontos GPS para definir a área do estacionamento.")

