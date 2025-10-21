from xml.etree import ElementTree as ET

import requests
from django.core.cache import cache
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
