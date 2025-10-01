import io
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response
from app.schemas.parking_schema import AnaliseRequest
from app.services import geo_service, map_service, ai_service

router = APIRouter()

@router.post("/analisar-estacionamento", summary="Analisa uma área de estacionamento")
async def analisar_estacionamento(request: AnaliseRequest):
    # ... seu código de análise completo aqui, sem alterações ...
    try:
        bbox_gps = geo_service.calcular_bounding_box(request.pontos)
        img_width, img_height = 1280, 1280
        imagem = map_service.obter_imagem_satelite(bbox_gps, width=img_width, height=img_height)
        vagas_pixels = ai_service.analisar_imagem_com_ia(imagem)
        vagas_com_gps = []
        for vaga in vagas_pixels:
            coords_gps = geo_service.pixel_para_gps(vaga['box_pixels'], bbox_gps, img_width, img_height)
            vagas_com_gps.append({"tipo": vaga['tipo'], "coords_gps": coords_gps})
        geojson_result = geo_service.criar_geojson(vagas_com_gps)
        total_vagas = len(vagas_com_gps)
        tipos_vagas = {vaga['tipo'] for vaga in vagas_com_gps}
        contagem_tipos = {tipo: sum(1 for v in vagas_com_gps if v['tipo'] == tipo) for tipo in tipos_vagas}
        return {
            "sumario": {
                "total_de_vagas_identificadas": total_vagas,
                "tipos_de_vagas": list(tipos_vagas),
                "contagem_por_tipo": contagem_tipos
            },
            "vagas_geojson": geojson_result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/satellite-image/", summary="Obter Imagem de Satélite")
async def get_satellite_image(
    lat: float = Query(..., description="Latitude do ponto central. Ex: -10.9472"),
    lon: float = Query(..., description="Longitude do ponto central. Ex: -37.0731")
):
    bbox = {"center_lon": lon, "center_lat": lat}
    pil_image = map_service.obter_imagem_satelite(bbox)
    buffer = io.BytesIO()
    pil_image.save(buffer, format="JPEG", quality=95)
    image_bytes = buffer.getvalue()
    return Response(content=image_bytes, media_type="image/jpeg")