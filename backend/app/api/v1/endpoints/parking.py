import io
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response
from app.schemas.parking_schema import AnaliseRequest
from app.services import geo_service, map_service, ai_service
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/analisar-estacionamento", summary="Analisa uma área de estacionamento")
async def analisar_estacionamento(request: AnaliseRequest):
    """
    Analisa uma área de estacionamento a partir de pontos GPS.
    
    - Obtém imagem de satélite via web scraping do Google Maps
    - Detecta vagas de estacionamento usando IA
    - Retorna GeoJSON com as vagas identificadas
    """
    try:
        logger.info(f"Iniciando análise com {len(request.pontos)} pontos")
        
        # Calcular bounding box
        bbox_gps = geo_service.calcular_bounding_box(request.pontos)
        logger.info(f"Bounding box calculado: {bbox_gps}")
        
        # Obter imagem de satélite via scraping (com retry)
        img_width, img_height = 1280, 1280
        logger.info("Obtendo imagem de satélite do Google Maps...")
        imagem = map_service.obter_imagem_satelite_com_retry(
            bbox_gps, 
            width=img_width, 
            height=img_height,
            max_retries=2
        )
        logger.info("Imagem obtida com sucesso")
        
        # Analisar imagem com IA
        logger.info("Analisando imagem com IA...")
        vagas_pixels = ai_service.analisar_imagem_com_ia(imagem)
        logger.info(f"{len(vagas_pixels)} vagas detectadas")
        
        # Converter coordenadas de pixels para GPS
        vagas_com_gps = []
        for vaga in vagas_pixels:
            coords_gps = geo_service.pixel_para_gps(
                vaga['box_pixels'], 
                bbox_gps, 
                img_width, 
                img_height
            )
            vagas_com_gps.append({
                "tipo": vaga['tipo'], 
                "coords_gps": coords_gps
            })
        
        # Criar GeoJSON
        geojson_result = geo_service.criar_geojson(vagas_com_gps)
        
        # Calcular estatísticas
        total_vagas = len(vagas_com_gps)
        tipos_vagas = {vaga['tipo'] for vaga in vagas_com_gps}
        contagem_tipos = {
            tipo: sum(1 for v in vagas_com_gps if v['tipo'] == tipo) 
            for tipo in tipos_vagas
        }
        
        logger.info(f"Análise concluída: {total_vagas} vagas encontradas")
        
        return {
            "sumario": {
                "total_de_vagas_identificadas": total_vagas,
                "tipos_de_vagas": list(tipos_vagas),
                "contagem_por_tipo": contagem_tipos
            },
            "vagas_geojson": geojson_result
        }
        
    except Exception as e:
        logger.error(f"Erro na análise: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/satellite-image/",
    summary="Obter Imagem de Satélite via Scraping",
    response_class=Response,
    responses={
        200: {
            "content": {"image/jpeg": {}},
            "description": "Imagem de satélite em formato JPEG"
        }
    }
)
async def get_satellite_image(
    lat: float = Query(..., description="Latitude do ponto central. Ex: -10.9472"),
    lon: float = Query(..., description="Longitude do ponto central. Ex: -37.0731"),
    width: int = Query(1280, description="Largura da imagem em pixels", ge=640, le=2560),
    height: int = Query(1280, description="Altura da imagem em pixels", ge=640, le=2560)
):
    """
    Obtém uma imagem de satélite do Google Maps via web scraping.
    
    **⚠️ IMPORTANTE**: Este endpoint retorna uma imagem JPEG. 
    Para visualizar no navegador, copie a URL abaixo e abra em uma nova aba.
    
 
    **Nota**: Este endpoint faz scraping do Google Maps, o que pode demorar 6-10 segundos.
    
    **Parâmetros**:
    - **lat**: Latitude do centro da área
    - **lon**: Longitude do centro da área  
    - **width**: Largura desejada (640-2560 pixels)
    - **height**: Altura desejada (640-2560 pixels)
    
    **Retorna**: Imagem JPEG em alta qualidade
    """
    try:
        logger.info(f"Requisição de imagem: lat={lat}, lon={lon}, size={width}x{height}")
        
        bbox = {"center_lon": lon, "center_lat": lat}
        
        # Usar versão com retry para maior confiabilidade
        pil_image = map_service.obter_imagem_satelite_com_retry(
            bbox, 
            width=width, 
            height=height,
            max_retries=2
        )
        
        # Converter para JPEG de alta qualidade
        buffer = io.BytesIO()
        pil_image.save(buffer, format="JPEG", quality=95)
        image_bytes = buffer.getvalue()
        
        logger.info(f"Imagem gerada: {len(image_bytes)} bytes")
        
        return Response(
            content=image_bytes, 
            media_type="image/jpeg",
            headers={
                "Content-Disposition": f"inline; filename=satellite_{lat}_{lon}.jpg",
                "Cache-Control": "public, max-age=3600"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao obter imagem: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao processar imagem de satélite: {str(e)}"
        )


@router.get("/test-scraping", summary="Testar Sistema de Scraping")
async def test_scraping():
    """
    Endpoint de teste para verificar se o sistema de scraping está funcionando.
    Retorna informações sobre a configuração do Selenium.
    """
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from webdriver_manager.chrome import ChromeDriverManager
        
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        
        driver = webdriver.Chrome(
            service=webdriver.chrome.service.Service(ChromeDriverManager().install()),
            options=options
        )
        
        driver.get("https://www.google.com")
        title = driver.title
        driver.quit()
        
        return {
            "status": "ok",
            "message": "Sistema de scraping funcionando corretamente",
            "test_page_title": title,
            "selenium_version": webdriver.__version__
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "help": "Verifique se o Chrome e ChromeDriver estão instalados corretamente"
        }


