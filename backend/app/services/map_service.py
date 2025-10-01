import requests
from PIL import Image
import io
from fastapi import HTTPException

MAPBOX_ACCESS_TOKEN = "pk.eyJ1IjoianZ2bWciLCJhIjoiY21nNnYwY3pvMGp2djJrcTV6aGUzdWF6ZSJ9.LR6vc_s86aA5cEc95OCOZg" 

def obter_imagem_satelite(bbox, width=1280, height=1280): # <-- MUDANÇA 1
    """
    Obtém uma imagem de satélite da Mapbox com base nas coordenadas do bounding box.
    """
    center_lon = bbox['center_lon']
    center_lat = bbox['center_lat']
    zoom = 19
    
    # URL da API com resolução maior e modificador @2x
    url = (
        f"https://api.mapbox.com/styles/v1/mapbox/satellite-v9/static/"
        f"{center_lon},{center_lat},{zoom}/{width}x{height}@2x" # <-- MUDANÇA 2
        f"?access_token={MAPBOX_ACCESS_TOKEN}"
    )
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            image = Image.open(io.BytesIO(response.content))
            return image
        else:
            raise HTTPException(
                status_code=response.status_code, 
                detail=f"Erro ao obter imagem da Mapbox: {response.text}"
            )
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=503, 
            detail=f"Não foi possível se conectar à API da Mapbox: {e}"
        )