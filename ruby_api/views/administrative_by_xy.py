from xml.etree import ElementTree as ET

import requests
from django.core.cache import cache
from rest_framework.decorators import api_view
from rest_framework.response import Response


def parse_gml_response(xml_content):
    try:
        root = ET.fromstring(xml_content)
        data = {}

        for elem in root.iter():
            tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag

            if elem.text and elem.text.strip() and tag not in ['FeatureCollection', 'featureMember', 'boundedBy', 'Box',
                                                               'coordinates']:
                data[tag] = elem.text.strip()

        return data
    except Exception:
        return {}


def get_administrative_info(x, y, epsg, layer_name):
    buffer = 100
    bbox = f"{x - buffer},{y - buffer},{x + buffer},{y + buffer}"

    params = {
        'VERSION': '1.3.0',
        'SERVICE': 'WMS',
        'REQUEST': 'GetFeatureInfo',
        'LAYERS': layer_name,
        'QUERY_LAYERS': layer_name,
        'CRS': f'EPSG:{epsg}',
        'WIDTH': '101',
        'HEIGHT': '101',
        'I': '50',
        'J': '50',
        'INFO_FORMAT': 'application/vnd.ogc.gml',
        'BBOX': bbox
    }

    url = 'https://mapy.geoportal.gov.pl/wss/service/PZGIK/PRG/WMS/AdministrativeBoundaries'

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        return parse_gml_response(response.content)
    except Exception:
        return {}


@api_view(['GET'])
def get_commune_by_xy(request):
    x = request.query_params.get('x')
    y = request.query_params.get('y')
    epsg = request.query_params.get('epsg', '2180')

    if not x or not y:
        return Response({'error': 'x and y coordinates required'}, status=400)

    try:
        x = float(x)
        y = float(y)
    except ValueError:
        return Response({'error': 'Invalid coordinates'}, status=400)

    cache_key = f'commune_xy_{x}_{y}_{epsg}'
    cached_data = cache.get(cache_key)
    if cached_data:
        return Response(cached_data)

    data = get_administrative_info(x, y, epsg, 'A03_Granice_gmin')

    if not data:
        result = {
            'error': 'Commune not found at coordinates',
            'coordinates': {'x': x, 'y': y, 'epsg': epsg}
        }
        return Response(result, status=404)

    result = {
        'coordinates': {'x': x, 'y': y, 'epsg': epsg},
        'commune': {
            'name': data.get('JPT_NAZWA_', ''),
            'teryt': data.get('JPT_KOD_JE', ''),
            'type': data.get('JPT_SJR_KO', ''),
            'regon': data.get('REGON', '')
        },
        'source': 'PRG'
    }

    cache.set(cache_key, result, timeout=3600)
    return Response(result)


@api_view(['GET'])
def get_county_by_xy(request):
    x = request.query_params.get('x')
    y = request.query_params.get('y')
    epsg = request.query_params.get('epsg', '2180')

    if not x or not y:
        return Response({'error': 'x and y coordinates required'}, status=400)

    try:
        x = float(x)
        y = float(y)
    except ValueError:
        return Response({'error': 'Invalid coordinates'}, status=400)

    cache_key = f'county_xy_{x}_{y}_{epsg}'
    cached_data = cache.get(cache_key)
    if cached_data:
        return Response(cached_data)

    data = get_administrative_info(x, y, epsg, 'A02_Granice_powiatow')

    if not data:
        result = {
            'error': 'County not found at coordinates',
            'coordinates': {'x': x, 'y': y, 'epsg': epsg}
        }
        return Response(result, status=404)

    result = {
        'coordinates': {'x': x, 'y': y, 'epsg': epsg},
        'county': {
            'name': data.get('JPT_NAZWA_', ''),
            'teryt': data.get('JPT_KOD_JE', ''),
            'regon': data.get('REGON', '')
        },
        'source': 'PRG'
    }

    cache.set(cache_key, result, timeout=3600)
    return Response(result)


@api_view(['GET'])
def get_voivodeship_by_xy(request):
    x = request.query_params.get('x')
    y = request.query_params.get('y')
    epsg = request.query_params.get('epsg', '2180')

    if not x or not y:
        return Response({'error': 'x and y coordinates required'}, status=400)

    try:
        x = float(x)
        y = float(y)
    except ValueError:
        return Response({'error': 'Invalid coordinates'}, status=400)

    cache_key = f'voivodeship_xy_{x}_{y}_{epsg}'
    cached_data = cache.get(cache_key)
    if cached_data:
        return Response(cached_data)

    data = get_administrative_info(x, y, epsg, 'A01_Granice_wojewodztw')

    if not data:
        result = {
            'error': 'Voivodeship not found at coordinates',
            'coordinates': {'x': x, 'y': y, 'epsg': epsg}
        }
        return Response(result, status=404)

    result = {
        'coordinates': {'x': x, 'y': y, 'epsg': epsg},
        'voivodeship': {
            'name': data.get('JPT_NAZWA_', ''),
            'teryt': data.get('JPT_KOD_JE', ''),
            'regon': data.get('REGON', '')
        },
        'source': 'PRG'
    }

    cache.set(cache_key, result, timeout=3600)
    return Response(result)


@api_view(['GET'])
def get_region_by_xy(request):
    x = request.query_params.get('x')
    y = request.query_params.get('y')
    epsg = request.query_params.get('epsg', '2180')

    if not x or not y:
        return Response({'error': 'x and y coordinates required'}, status=400)

    try:
        x = float(x)
        y = float(y)
    except ValueError:
        return Response({'error': 'Invalid coordinates'}, status=400)

    cache_key = f'region_xy_{x}_{y}_{epsg}'
    cached_data = cache.get(cache_key)
    if cached_data:
        return Response(cached_data)

    data = get_administrative_info(x, y, epsg, 'A06_Granice_obrebow_ewidencyjnych')

    if not data:
        result = {
            'error': 'Region not found at coordinates',
            'coordinates': {'x': x, 'y': y, 'epsg': epsg}
        }
        return Response(result, status=404)

    result = {
        'coordinates': {'x': x, 'y': y, 'epsg': epsg},
        'region': {
            'name': data.get('JPT_NAZWA_', ''),
            'teryt': data.get('JPT_KOD_JE', '')
        },
        'source': 'PRG'
    }

    cache.set(cache_key, result, timeout=3600)
    return Response(result)
