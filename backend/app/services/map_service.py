import time
import io
import os
import math
import requests
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
from fastapi import HTTPException
import logging

# Configurar logger para o módulo
logger = logging.getLogger(__name__)

# Suprimir logs verbosos do Selenium e ChromeDriver
logging.getLogger('selenium').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('WDM').setLevel(logging.WARNING)

# Suprimir saída do ChromeDriver
os.environ['WDM_LOG_LEVEL'] = '0'
os.environ['WDM_PRINT_FIRST_LINE'] = 'False'


def obter_imagem_satelite_tiles(bbox, width=1280, height=1280):

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


def obter_imagem_satelite(bbox, width=1280, height=1280):
    """
    MÉTODO ALTERNATIVO (Selenium): Usa web scraping do Google Maps.
    Mais lento mas funciona como fallback.
    """
    center_lon = bbox['center_lon']
    center_lat = bbox['center_lat']
    zoom = 20
    
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument(f'--window-size={width + 100},{height + 100}')
    chrome_options.add_argument('--log-level=3')
    chrome_options.add_argument('--silent')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-automation', 'enable-logging'])
    
    driver = None
    try:
        service = Service(
            ChromeDriverManager().install(),
            log_path='NUL' if os.name == 'nt' else '/dev/null'
        )
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        url = f"https://www.google.com/maps/@{center_lat},{center_lon},{zoom}z/data=!3m1!1e3"
        logger.info(f"Acessando: {url}")
        driver.get(url)
        
        # Aguardar carregamento
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "canvas"))
        )
        time.sleep(15)  # Aguardar tiles
        
        # Remover UI
        driver.execute_script("""
            document.querySelectorAll('[class*="widget"], [class*="control"], button, a').forEach(el => el.remove());
        """)
        
        screenshot = driver.get_screenshot_as_png()
        image = Image.open(io.BytesIO(screenshot))
        
        # Crop centralizado
        left = (image.width - width) // 2
        top = (image.height - height) // 2
        image = image.crop((left, top, left + width, top + height))
        
        return image
        
    finally:
        if driver:
            driver.quit()


def obter_imagem_satelite_com_retry(bbox, width=1280, height=1280, max_retries=2):
    """
    Tenta obter imagem usando método de tiles (rápido e confiável).
    Se falhar, usa Selenium como fallback.
    """
    
    # MÉTODO 1: Tiles (preferido)
    try:
        logger.info("Usando método de tiles (rápido)")
        return obter_imagem_satelite_tiles(bbox, width, height)
    except Exception as e:
        logger.warning(f"Método de tiles falhou: {e}")
    
    # MÉTODO 2: Selenium (fallback)
    for attempt in range(max_retries):
        try:
            logger.info(f"Usando Selenium (tentativa {attempt + 1}/{max_retries})")
            return obter_imagem_satelite(bbox, width, height)
        except Exception as e:
            logger.warning(f"Selenium falhou: {e}")
            if attempt < max_retries - 1:
                time.sleep(3)
    
    # Se tudo falhar
    raise HTTPException(
        status_code=503,
        detail="Não foi possível obter imagem de satélite. Tente novamente."
    )