from typing import List
from app.schemas.parking_schema import PontoGPS

def calcular_bounding_box(pontos: List[PontoGPS]):
    min_lat = min(p.lat for p in pontos)
    max_lat = max(p.lat for p in pontos)
    min_lon = min(p.lon for p in pontos)
    max_lon = max(p.lon for p in pontos)
    
    center_lat = (min_lat + max_lat) / 2
    center_lon = (min_lon + max_lon) / 2
    
    return {
        "min_lat": min_lat, "max_lat": max_lat,
        "min_lon": min_lon, "max_lon": max_lon,
        "center_lat": center_lat, "center_lon": center_lon
    }

def pixel_para_gps(box_pixels, bbox_gps, img_width, img_height):
    x_min, y_min, x_max, y_max = box_pixels
    centro_x_pixel = (x_min + x_max) / 2
    centro_y_pixel = (y_min + y_max) / 2
    
    lon_percent = centro_x_pixel / img_width
    lat_percent = centro_y_pixel / img_height
    
    lon_final = bbox_gps['min_lon'] + (bbox_gps['max_lon'] - bbox_gps['min_lon']) * lon_percent
    lat_final = bbox_gps['max_lat'] - (bbox_gps['max_lat'] - bbox_gps['min_lat']) * lat_percent
    
    return {"lat": lat_final, "lon": lon_final}

def criar_geojson(vagas_com_gps):
    features = []
    for i, vaga in enumerate(vagas_com_gps):
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [vaga['coords_gps']['lon'], vaga['coords_gps']['lat']]
            },
            "properties": {
                "id": i,
                "tipo_vaga": vaga['tipo']
            }
        }
        features.append(feature)
        
    return {"type": "FeatureCollection", "features": features}