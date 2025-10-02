import io
import math
import requests
from PIL import Image
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)


def obter_imagem_satelite_tiles(bbox, width=1280, height=1280):
    """
    Obtém imagem de satélite usando tiles do Google Maps.
    Método compatível com Vercel serverless.
    """
    center_lat = bbox['center_lat']
    center_lon = bbox['center_lon']
    zoom = 20  # Zoom máximo
    
    def lat_lon_to_tile(lat, lon, zoom):
        """Converte coordenadas lat/lon para tile x/y"""
        lat_rad = math.radians(lat)
        n = 2.0 ** zoom
        x = int((lon + 180.0) / 360.0 * n)
        y = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
        return x, y
    
    # Calcular tile central
    tile_x, tile_y = lat_lon_to_tile(center_lat, center_lon, zoom)
    
    # Calcular quantos tiles precisamos
    tile_size = 256  # Tamanho padrão dos tiles do Google Maps
    tiles_x = math.ceil(width / tile_size) + 2  # +2 para margem
    tiles_y = math.ceil(height / tile_size) + 2
    
    # Criar imagem grande
    full_width = tiles_x * tile_size
    full_height = tiles_y * tile_size
    full_image = Image.new('RGB', (full_width, full_height))
    
    logger.info(f"Montando imagem com {tiles_x}x{tiles_y} tiles")
    
    # Calcular tile inicial (canto superior esquerdo)
    start_x = tile_x - tiles_x // 2
    start_y = tile_y - tiles_y // 2
    
    # Baixar e montar tiles
    tiles_downloaded = 0
    for dx in range(tiles_x):
        for dy in range(tiles_y):
            tx = start_x + dx
            ty = start_y + dy
            
            # URL do tile - Google Maps satellite imagery
            # lyrs=s significa satélite
            tile_url = f"https://mt1.google.com/vt/lyrs=s&x={tx}&y={ty}&z={zoom}"
            
            try:
                response = requests.get(tile_url, timeout=10)
                if response.status_code == 200:
                    tile_image = Image.open(io.BytesIO(response.content))
                    full_image.paste(tile_image, (dx * tile_size, dy * tile_size))
                    tiles_downloaded += 1
                else:
                    logger.warning(f"Tile ({tx},{ty}) retornou status {response.status_code}")
            except Exception as e:
                logger.warning(f"Erro ao baixar tile ({tx},{ty}): {e}")
    
    logger.info(f"Tiles baixados: {tiles_downloaded}/{tiles_x * tiles_y}")
    
    if tiles_downloaded == 0:
        raise HTTPException(
            status_code=503,
            detail="Não foi possível baixar nenhum tile do Google Maps"
        )
    
    # Crop para tamanho exato desejado (centralizado)
    left = (full_image.width - width) // 2
    top = (full_image.height - height) // 2
    final_image = full_image.crop((left, top, left + width, top + height))
    
    logger.info(f"Imagem final: {final_image.size}")
    
    return final_image


def obter_imagem_satelite_com_retry(bbox, width=1280, height=1280, max_retries=2):
    """
    Obtém imagem usando método de tiles (único método disponível na Vercel).
    """
    for attempt in range(max_retries):
        try:
            logger.info(f"Obtendo imagem via tiles (tentativa {attempt + 1}/{max_retries})")
            return obter_imagem_satelite_tiles(bbox, width, height)
        except Exception as e:
            logger.warning(f"Tentativa {attempt + 1} falhou: {e}")
            if attempt < max_retries - 1:
                continue
    
    # Se tudo falhar
    raise HTTPException(
        status_code=503,
        detail="Não foi possível obter imagem de satélite. Tente novamente."
    )