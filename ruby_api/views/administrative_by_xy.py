from rest_framework.decorators import api_view
from rest_framework.response import Response
import requests
from xml.etree import ElementTree as ET


def parse_prg_feature_info(xml_content):
    try:
        root = ET.fromstring(xml_content)
        features = []

        for feature_member in root.findall('.//{http://www.opengis.net/gml}featureMember'):
            feature_data = {}
            for layer in feature_member:
                for attribute in layer:
                    name = attribute.get('Name', '')
                    text = attribute.text or ''
                    text = text.strip()
                    if text and not text.startswith('<') and not text.startswith('http'):
                        feature_data[name] = text

            if feature_data:
                features.append(feature_data)

        return features
    except Exception as e:
        return []


def get_administrative_unit(x, y, epsg, layer_name):
    buffer = 50
    width = 101
    height = 101
    bbox = f"{x - buffer},{y - buffer},{x + buffer},{y + buffer}"

    params = {
        'VERSION': '1.3.0',
        'SERVICE': 'WMS',
        'REQUEST': 'GetFeatureInfo',
        'LAYERS': layer_name,
        'QUERY_LAYERS': layer_name,
        'CRS': f'EPSG:{epsg}',
        'WIDTH': str(width),
        'HEIGHT': str(height),
        'I': str(width // 2),
        'J': str(height // 2),
        'INFO_FORMAT': 'text/xml',
        'BBOX': bbox
    }

    url = 'https://integracja.gugik.gov.pl/cgi-bin/KrajowaIntegracjaEwidencjiGruntow'

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()

        features = parse_prg_feature_info(response.content)

        if features:
            return features[0]
        return None

    except Exception as e:
        return None


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

    obreby_data = get_administrative_unit(x, y, epsg, 'obreby')

    if not obreby_data:
        return Response({
            'error': 'Commune not found at coordinates',
            'coordinates': {'x': x, 'y': y, 'epsg': epsg}
        }, status=404)

    return Response({
        'coordinates': {'x': x, 'y': y, 'epsg': epsg},
        'commune': {
            'name': obreby_data.get('Gmina', ''),
            'obreb': obreby_data.get('Obręb', ''),
            'wojewodztwo': obreby_data.get('Województwo', ''),
            'powiat': obreby_data.get('Powiat', '')
        },
        'source': 'PRG'
    })


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

    dzialki_data = get_administrative_unit(x, y, epsg, 'dzialki')

    if not dzialki_data:
        return Response({
            'error': 'County not found at coordinates',
            'coordinates': {'x': x, 'y': y, 'epsg': epsg}
        }, status=404)

    return Response({
        'coordinates': {'x': x, 'y': y, 'epsg': epsg},
        'county': {
            'name': dzialki_data.get('Powiat', ''),
            'wojewodztwo': dzialki_data.get('Województwo', '')
        },
        'source': 'PRG'
    })


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

    dzialki_data = get_administrative_unit(x, y, epsg, 'dzialki')

    if not dzialki_data:
        return Response({
            'error': 'Voivodeship not found at coordinates',
            'coordinates': {'x': x, 'y': y, 'epsg': epsg}
        }, status=404)

    return Response({
        'coordinates': {'x': x, 'y': y, 'epsg': epsg},
        'voivodeship': {
            'name': dzialki_data.get('Województwo', '')
        },
        'source': 'PRG'
    })