from xml.etree import ElementTree as ET

import requests
from django.core.cache import cache
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse, OpenApiExample
from rest_framework.decorators import api_view
from rest_framework.response import Response


def parse_wfs_response(xml_content, layer_name):
    try:
        root = ET.fromstring(xml_content)
        namespaces = {
            'wfs': 'http://www.opengis.net/wfs/2.0',
            'ms': 'http://mapserver.gis.umn.edu/mapserver',
            'gml': 'http://www.opengis.net/gml/3.2'
        }

        features = root.findall(f'.//ms:{layer_name}', namespaces)

        if not features:
            return None

        feature = features[0]
        data = {}

        for child in feature:
            tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
            if child.text and tag not in ['GEOMETRY', 'SHAPE', 'geometry', 'boundedBy']:
                data[tag] = child.text.strip()

        return data
    except Exception:
        return None


def parse_wfs_multi_response(xml_content, layer_name):
    try:
        root = ET.fromstring(xml_content)
        namespaces = {
            'wfs': 'http://www.opengis.net/wfs/2.0',
            'ms': 'http://mapserver.gis.umn.edu/mapserver',
            'gml': 'http://www.opengis.net/gml/3.2'
        }

        features = root.findall(f'.//ms:{layer_name}', namespaces)

        results = []
        for feature in features:
            data = {}
            for child in feature:
                tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                if child.text and tag not in ['GEOMETRY', 'SHAPE', 'geometry', 'boundedBy']:
                    data[tag] = child.text.strip()
            if data:
                results.append(data)

        return results
    except Exception:
        return []


@extend_schema(
    summary="Pobierz obręb ewidencyjny po ID",
    description="Zwraca informacje o obrębie ewidencyjnym na podstawie identyfikatora TERYT z usługi PRG.",
    parameters=[
        OpenApiParameter(
            name='region_id',
            type=str,
            location=OpenApiParameter.QUERY,
            required=True,
            description='Identyfikator obrębu ewidencyjnego (format: WWPPGG_R.OOOO)',
            examples=[
                OpenApiExample('Przykład Kraków', value='126301_1.0001'),
                OpenApiExample('Przykład Warszawa', value='146501_1.0001'),
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
                        'region_id': '126301_1.0001',
                        'region': {
                            'name': 'Krowodrza',
                            'teryt': '126301_1.0001',
                            'regon': '12345678901234'
                        },
                        'source': 'PRG'
                    }
                )
            ]
        ),
        400: OpenApiResponse(description='Nieprawidłowy format region_id'),
        404: OpenApiResponse(description='Obręb nie znaleziony'),
        500: OpenApiResponse(description='Błąd serwera')
    },
    tags=['Podziały administracyjne']
)
@api_view(['GET'])
def get_region_by_id(request):
    region_id = request.query_params.get('region_id')

    if not region_id:
        return Response({'error': 'region_id required'}, status=400)

    parts = region_id.split('_')
    if len(parts) != 2 or '.' not in parts[1]:
        return Response({'error': 'Invalid region_id format. Expected format: WWPPGG_R.OOOO'}, status=400)

    cache_key = f'region_{region_id}'
    cached_data = cache.get(cache_key)
    if cached_data:
        return Response(cached_data)

    try:
        params = {
            'SERVICE': 'WFS',
            'VERSION': '2.0.0',
            'REQUEST': 'GetFeature',
            'TYPENAME': 'ms:A06_Granice_obrebow_ewidencyjnych',
            'FILTER': f"<Filter><PropertyIsEqualTo><PropertyName>JPT_KOD_JE</PropertyName><Literal>{region_id}</Literal></PropertyIsEqualTo></Filter>",
            'OUTPUTFORMAT': 'GML3'
        }

        url = 'https://mapy.geoportal.gov.pl/wss/service/PZGIK/PRG/WFS/AdministrativeBoundaries'

        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()

        data = parse_wfs_response(response.content, 'A06_Granice_obrebow_ewidencyjnych')

        if not data:
            return Response({'error': 'Region not found', 'region_id': region_id}, status=404)

        result = {
            'region_id': region_id,
            'region': {
                'name': data.get('JPT_NAZWA_', ''),
                'teryt': data.get('JPT_KOD_JE', ''),
                'regon': data.get('REGON', '')
            },
            'source': 'PRG'
        }

        cache.set(cache_key, result, timeout=3600)
        return Response(result)

    except requests.RequestException as e:
        return Response({'error': f'Request failed: {str(e)}', 'region_id': region_id}, status=500)
    except Exception as e:
        return Response({'error': f'Error: {str(e)}', 'region_id': region_id}, status=500)


@extend_schema(
    summary="Wyszukaj obręb ewidencyjny po nazwie lub ID",
    description="Zwraca listę obrębów ewidencyjnych pasujących do zapytania (po nazwie) lub pojedynczy obręb (po ID TERYT).",
    parameters=[
        OpenApiParameter(
            name='query',
            type=str,
            location=OpenApiParameter.QUERY,
            required=True,
            description='Nazwa obrębu (wyszukiwanie częściowe) lub ID TERYT (format: WWPPGG_R.OOOO)',
            examples=[
                OpenApiExample('Wyszukiwanie po nazwie', value='Krowodrza'),
                OpenApiExample('Wyszukiwanie po ID', value='126301_1.0001'),
            ]
        )
    ],
    responses={
        200: OpenApiResponse(
            description='Lista obrębów lub pojedynczy obręb',
            examples=[
                OpenApiExample(
                    'Wyniki wyszukiwania po nazwie',
                    value={
                        'query': 'Krowodrza',
                        'regions': [
                            {
                                'name': 'Krowodrza',
                                'teryt': '126301_1.0001',
                                'regon': '12345678901234'
                            }
                        ],
                        'source': 'PRG'
                    }
                ),
                OpenApiExample(
                    'Wynik wyszukiwania po ID',
                    value={
                        'region_id': '126301_1.0001',
                        'region': {
                            'name': 'Krowodrza',
                            'teryt': '126301_1.0001',
                            'regon': '12345678901234'
                        },
                        'source': 'PRG'
                    }
                )
            ]
        ),
        400: OpenApiResponse(description='Brak parametru query'),
        404: OpenApiResponse(description='Nie znaleziono obrębów'),
        500: OpenApiResponse(description='Błąd serwera')
    },
    tags=['Podziały administracyjne']
)
@api_view(['GET'])
def get_region_by_name_or_id(request):
    query = request.query_params.get('query')

    if not query:
        return Response({'error': 'query parameter required'}, status=400)

    if '_' in query and '.' in query:
        request.query_params._mutable = True
        request.query_params['region_id'] = query
        request.query_params._mutable = False
        return get_region_by_id(request)

    cache_key = f'region_search_{query}'
    cached_data = cache.get(cache_key)
    if cached_data:
        return Response(cached_data)

    try:
        params = {
            'SERVICE': 'WFS',
            'VERSION': '2.0.0',
            'REQUEST': 'GetFeature',
            'TYPENAME': 'ms:A06_Granice_obrebow_ewidencyjnych',
            'FILTER': f"<Filter><PropertyIsLike wildCard='*' singleChar='?' escapeChar='!'><PropertyName>JPT_NAZWA_</PropertyName><Literal>*{query}*</Literal></PropertyIsLike></Filter>",
            'OUTPUTFORMAT': 'GML3',
            'COUNT': '10'
        }

        url = 'https://mapy.geoportal.gov.pl/wss/service/PZGIK/PRG/WFS/AdministrativeBoundaries'

        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()

        results_data = parse_wfs_multi_response(response.content, 'A06_Granice_obrebow_ewidencyjnych')

        if not results_data:
            return Response({'error': 'No regions found', 'query': query}, status=404)

        results = []
        for data in results_data:
            results.append({
                'name': data.get('JPT_NAZWA_', ''),
                'teryt': data.get('JPT_KOD_JE', ''),
                'regon': data.get('REGON', '')
            })

        result = {
            'query': query,
            'regions': results,
            'source': 'PRG'
        }

        cache.set(cache_key, result, timeout=3600)
        return Response(result)

    except requests.RequestException as e:
        return Response({'error': f'Request failed: {str(e)}', 'query': query}, status=500)
    except Exception as e:
        return Response({'error': f'Error: {str(e)}', 'query': query}, status=500)


@extend_schema(
    summary="Pobierz gminę po ID",
    description="Zwraca informacje o gminie na podstawie identyfikatora TERYT z usługi PRG.",
    parameters=[
        OpenApiParameter(
            name='commune_id',
            type=str,
            location=OpenApiParameter.QUERY,
            required=True,
            description='Identyfikator gminy (format: WWPPGG_R)',
            examples=[
                OpenApiExample('Przykład Kraków', value='126301_1'),
                OpenApiExample('Przykład Warszawa', value='146501_1'),
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
                        'commune_id': '126301_1',
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
        400: OpenApiResponse(description='Nieprawidłowy format commune_id'),
        404: OpenApiResponse(description='Gmina nie znaleziona'),
        500: OpenApiResponse(description='Błąd serwera')
    },
    tags=['Podziały administracyjne']
)
@api_view(['GET'])
def get_commune_by_id(request):
    commune_id = request.query_params.get('commune_id')

    if not commune_id:
        return Response({'error': 'commune_id required'}, status=400)

    if '_' not in commune_id:
        return Response({'error': 'Invalid commune_id format. Expected format: WWPPGG_R'}, status=400)

    cache_key = f'commune_{commune_id}'
    cached_data = cache.get(cache_key)
    if cached_data:
        return Response(cached_data)

    try:
        params = {
            'SERVICE': 'WFS',
            'VERSION': '2.0.0',
            'REQUEST': 'GetFeature',
            'TYPENAME': 'ms:A03_Granice_gmin',
            'FILTER': f"<Filter><PropertyIsEqualTo><PropertyName>JPT_KOD_JE</PropertyName><Literal>{commune_id}</Literal></PropertyIsEqualTo></Filter>",
            'OUTPUTFORMAT': 'GML3'
        }

        url = 'https://mapy.geoportal.gov.pl/wss/service/PZGIK/PRG/WFS/AdministrativeBoundaries'

        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()

        data = parse_wfs_response(response.content, 'A03_Granice_gmin')

        if not data:
            return Response({'error': 'Commune not found', 'commune_id': commune_id}, status=404)

        result = {
            'commune_id': commune_id,
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

    except requests.RequestException as e:
        return Response({'error': f'Request failed: {str(e)}', 'commune_id': commune_id}, status=500)
    except Exception as e:
        return Response({'error': f'Error: {str(e)}', 'commune_id': commune_id}, status=500)


@extend_schema(
    summary="Pobierz powiat po ID",
    description="Zwraca informacje o powiecie na podstawie identyfikatora TERYT z usługi PRG.",
    parameters=[
        OpenApiParameter(
            name='county_id',
            type=str,
            location=OpenApiParameter.QUERY,
            required=True,
            description='Identyfikator powiatu (format: WWPP)',
            examples=[
                OpenApiExample('Przykład Kraków', value='1206'),
                OpenApiExample('Przykład Warszawa', value='1465'),
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
                        'county_id': '1206',
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
        400: OpenApiResponse(description='Nieprawidłowy format county_id'),
        404: OpenApiResponse(description='Powiat nie znaleziony'),
        500: OpenApiResponse(description='Błąd serwera')
    },
    tags=['Podziały administracyjne']
)
@api_view(['GET'])
def get_county_by_id(request):
    county_id = request.query_params.get('county_id')

    if not county_id:
        return Response({'error': 'county_id required'}, status=400)

    if len(county_id) != 4:
        return Response({'error': 'Invalid county_id format. Expected format: WWPP'}, status=400)

    cache_key = f'county_{county_id}'
    cached_data = cache.get(cache_key)
    if cached_data:
        return Response(cached_data)

    try:
        params = {
            'SERVICE': 'WFS',
            'VERSION': '2.0.0',
            'REQUEST': 'GetFeature',
            'TYPENAME': 'ms:A02_Granice_powiatow',
            'FILTER': f"<Filter><PropertyIsLike wildCard='*' singleChar='?' escapeChar='!'><PropertyName>JPT_KOD_JE</PropertyName><Literal>{county_id}*</Literal></PropertyIsLike></Filter>",
            'OUTPUTFORMAT': 'GML3'
        }

        url = 'https://mapy.geoportal.gov.pl/wss/service/PZGIK/PRG/WFS/AdministrativeBoundaries'

        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()

        data = parse_wfs_response(response.content, 'A02_Granice_powiatow')

        if not data:
            return Response({'error': 'County not found', 'county_id': county_id}, status=404)

        result = {
            'county_id': county_id,
            'county': {
                'name': data.get('JPT_NAZWA_', ''),
                'teryt': data.get('JPT_KOD_JE', ''),
                'regon': data.get('REGON', '')
            },
            'source': 'PRG'
        }

        cache.set(cache_key, result, timeout=3600)
        return Response(result)

    except requests.RequestException as e:
        return Response({'error': f'Request failed: {str(e)}', 'county_id': county_id}, status=500)
    except Exception as e:
        return Response({'error': f'Error: {str(e)}', 'county_id': county_id}, status=500)


@extend_schema(
    summary="Pobierz województwo po ID",
    description="Zwraca informacje o województwie na podstawie identyfikatora TERYT z usługi PRG.",
    parameters=[
        OpenApiParameter(
            name='voivodeship_id',
            type=str,
            location=OpenApiParameter.QUERY,
            required=True,
            description='Identyfikator województwa (format: WW)',
            examples=[
                OpenApiExample('Małopolskie', value='12'),
                OpenApiExample('Mazowieckie', value='14'),
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
                        'voivodeship_id': '12',
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
        400: OpenApiResponse(description='Nieprawidłowy format voivodeship_id'),
        404: OpenApiResponse(description='Województwo nie znalezione'),
        500: OpenApiResponse(description='Błąd serwera')
    },
    tags=['Podziały administracyjne']
)
@api_view(['GET'])
def get_voivodeship_by_id(request):
    voivodeship_id = request.query_params.get('voivodeship_id')

    if not voivodeship_id:
        return Response({'error': 'voivodeship_id required'}, status=400)

    if len(voivodeship_id) != 2:
        return Response({'error': 'Invalid voivodeship_id format. Expected format: WW'}, status=400)

    cache_key = f'voivodeship_{voivodeship_id}'
    cached_data = cache.get(cache_key)
    if cached_data:
        return Response(cached_data)

    try:
        params = {
            'SERVICE': 'WFS',
            'VERSION': '2.0.0',
            'REQUEST': 'GetFeature',
            'TYPENAME': 'ms:A01_Granice_wojewodztw',
            'FILTER': f"<Filter><PropertyIsLike wildCard='*' singleChar='?' escapeChar='!'><PropertyName>JPT_KOD_JE</PropertyName><Literal>{voivodeship_id}*</Literal></PropertyIsLike></Filter>",
            'OUTPUTFORMAT': 'GML3'
        }

        url = 'https://mapy.geoportal.gov.pl/wss/service/PZGIK/PRG/WFS/AdministrativeBoundaries'

        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()

        data = parse_wfs_response(response.content, 'A01_Granice_wojewodztw')

        if not data:
            return Response({'error': 'Voivodeship not found', 'voivodeship_id': voivodeship_id}, status=404)

        result = {
            'voivodeship_id': voivodeship_id,
            'voivodeship': {
                'name': data.get('JPT_NAZWA_', ''),
                'teryt': data.get('JPT_KOD_JE', ''),
                'regon': data.get('REGON', '')
            },
            'source': 'PRG'
        }

        cache.set(cache_key, result, timeout=3600)
        return Response(result)

    except requests.RequestException as e:
        return Response({'error': f'Request failed: {str(e)}', 'voivodeship_id': voivodeship_id}, status=500)
    except Exception as e:
        return Response({'error': f'Error: {str(e)}', 'voivodeship_id': voivodeship_id}, status=500)
