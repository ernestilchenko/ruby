from xml.etree import ElementTree as ET

import requests
from django.core.cache import cache
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse, OpenApiExample
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


@extend_schema(
    summary="Pobierz gminę po współrzędnych",
    description="Zwraca informacje o gminie na podstawie współrzędnych XY z usługi PRG (Państwowy Rejestr Granic).",
    parameters=[
        OpenApiParameter(
            name='x',
            type=float,
            location=OpenApiParameter.QUERY,
            required=True,
            description='Współrzędna X',
            examples=[
                OpenApiExample('EPSG:2180', value=500000.0),
                OpenApiExample('EPSG:4326', value=19.9449799),
            ]
        ),
        OpenApiParameter(
            name='y',
            type=float,
            location=OpenApiParameter.QUERY,
            required=True,
            description='Współrzędna Y',
            examples=[
                OpenApiExample('EPSG:2180', value=250000.0),
                OpenApiExample('EPSG:4326', value=50.0646501),
            ]
        ),
        OpenApiParameter(
            name='epsg',
            type=str,
            location=OpenApiParameter.QUERY,
            required=False,
            description='Kod EPSG układu współrzędnych',
            default='2180',
            examples=[
                OpenApiExample('EPSG:2180 (domyślny)', value='2180'),
                OpenApiExample('EPSG:4326 (WGS84)', value='4326'),
            ]
        )
    ],
    responses={
        200: OpenApiResponse(
            description='Dane gminy',
            examples=[
                OpenApiExample(
                    'Sukces',
                    value={
                        'coordinates': {'x': 500000.0, 'y': 250000.0, 'epsg': '2180'},
                        'commune': {
                            'name': 'Kraków',
                            'teryt': '126301_1',
                            'type': '1',
                            'regon': '12345678901234'
                        },
                        'source': 'PRG'
                    }
                )
            ]
        ),
        400: OpenApiResponse(description='Nieprawidłowe współrzędne'),
        404: OpenApiResponse(description='Gmina nie znaleziona w podanych współrzędnych'),
    },
    tags=['Podziały administracyjne']
)
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


@extend_schema(
    summary="Pobierz powiat po współrzędnych",
    description="Zwraca informacje o powiecie na podstawie współrzędnych XY z usługi PRG (Państwowy Rejestr Granic).",
    parameters=[
        OpenApiParameter(
            name='x',
            type=float,
            location=OpenApiParameter.QUERY,
            required=True,
            description='Współrzędna X',
            examples=[
                OpenApiExample('EPSG:2180', value=500000.0),
                OpenApiExample('EPSG:4326', value=19.9449799),
            ]
        ),
        OpenApiParameter(
            name='y',
            type=float,
            location=OpenApiParameter.QUERY,
            required=True,
            description='Współrzędna Y',
            examples=[
                OpenApiExample('EPSG:2180', value=250000.0),
                OpenApiExample('EPSG:4326', value=50.0646501),
            ]
        ),
        OpenApiParameter(
            name='epsg',
            type=str,
            location=OpenApiParameter.QUERY,
            required=False,
            description='Kod EPSG układu współrzędnych',
            default='2180',
            examples=[
                OpenApiExample('EPSG:2180 (domyślny)', value='2180'),
                OpenApiExample('EPSG:4326 (WGS84)', value='4326'),
            ]
        )
    ],
    responses={
        200: OpenApiResponse(
            description='Dane powiatu',
            examples=[
                OpenApiExample(
                    'Sukces',
                    value={
                        'coordinates': {'x': 500000.0, 'y': 250000.0, 'epsg': '2180'},
                        'county': {
                            'name': 'krakowski',
                            'teryt': '1206',
                            'regon': '12345678901234'
                        },
                        'source': 'PRG'
                    }
                )
            ]
        ),
        400: OpenApiResponse(description='Nieprawidłowe współrzędne'),
        404: OpenApiResponse(description='Powiat nie znaleziony w podanych współrzędnych'),
    },
    tags=['Podziały administracyjne']
)
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


@extend_schema(
    summary="Pobierz województwo po współrzędnych",
    description="Zwraca informacje o województwie na podstawie współrzędnych XY z usługi PRG (Państwowy Rejestr Granic).",
    parameters=[
        OpenApiParameter(
            name='x',
            type=float,
            location=OpenApiParameter.QUERY,
            required=True,
            description='Współrzędna X',
            examples=[
                OpenApiExample('EPSG:2180', value=500000.0),
                OpenApiExample('EPSG:4326', value=19.9449799),
            ]
        ),
        OpenApiParameter(
            name='y',
            type=float,
            location=OpenApiParameter.QUERY,
            required=True,
            description='Współrzędna Y',
            examples=[
                OpenApiExample('EPSG:2180', value=250000.0),
                OpenApiExample('EPSG:4326', value=50.0646501),
            ]
        ),
        OpenApiParameter(
            name='epsg',
            type=str,
            location=OpenApiParameter.QUERY,
            required=False,
            description='Kod EPSG układu współrzędnych',
            default='2180',
            examples=[
                OpenApiExample('EPSG:2180 (domyślny)', value='2180'),
                OpenApiExample('EPSG:4326 (WGS84)', value='4326'),
            ]
        )
    ],
    responses={
        200: OpenApiResponse(
            description='Dane województwa',
            examples=[
                OpenApiExample(
                    'Sukces',
                    value={
                        'coordinates': {'x': 500000.0, 'y': 250000.0, 'epsg': '2180'},
                        'voivodeship': {
                            'name': 'małopolskie',
                            'teryt': '12',
                            'regon': '12345678901234'
                        },
                        'source': 'PRG'
                    }
                )
            ]
        ),
        400: OpenApiResponse(description='Nieprawidłowe współrzędne'),
        404: OpenApiResponse(description='Województwo nie znalezione w podanych współrzędnych'),
    },
    tags=['Podziały administracyjne']
)
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


@extend_schema(
    summary="Pobierz obręb ewidencyjny po współrzędnych",
    description="Zwraca informacje o obrębie ewidencyjnym na podstawie współrzędnych XY z usługi PRG (Państwowy Rejestr Granic).",
    parameters=[
        OpenApiParameter(
            name='x',
            type=float,
            location=OpenApiParameter.QUERY,
            required=True,
            description='Współrzędna X',
            examples=[
                OpenApiExample('EPSG:2180', value=500000.0),
                OpenApiExample('EPSG:4326', value=19.9449799),
            ]
        ),
        OpenApiParameter(
            name='y',
            type=float,
            location=OpenApiParameter.QUERY,
            required=True,
            description='Współrzędna Y',
            examples=[
                OpenApiExample('EPSG:2180', value=250000.0),
                OpenApiExample('EPSG:4326', value=50.0646501),
            ]
        ),
        OpenApiParameter(
            name='epsg',
            type=str,
            location=OpenApiParameter.QUERY,
            required=False,
            description='Kod EPSG układu współrzędnych',
            default='2180',
            examples=[
                OpenApiExample('EPSG:2180 (domyślny)', value='2180'),
                OpenApiExample('EPSG:4326 (WGS84)', value='4326'),
            ]
        )
    ],
    responses={
        200: OpenApiResponse(
            description='Dane obrębu ewidencyjnego',
            examples=[
                OpenApiExample(
                    'Sukces',
                    value={
                        'coordinates': {'x': 500000.0, 'y': 250000.0, 'epsg': '2180'},
                        'region': {
                            'name': 'Krowodrza',
                            'teryt': '126301_1.0001'
                        },
                        'source': 'PRG'
                    }
                )
            ]
        ),
        400: OpenApiResponse(description='Nieprawidłowe współrzędne'),
        404: OpenApiResponse(description='Obręb nie znaleziony w podanych współrzędnych'),
    },
    tags=['Podziały administracyjne']
)
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
