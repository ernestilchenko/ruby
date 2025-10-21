from xml.etree import ElementTree as ET

import requests
from django.core.cache import cache
from qgis.core import QgsVectorLayer, QgsDataSourceUri
from rest_framework.decorators import api_view
from rest_framework.response import Response

from data.wfs_data import WFS_SERVICES
from ruby.qgis_manager import QGISManager
from ruby_api.utils import qvariant_to_python


def parse_gugik_feature_info(xml_content):
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


@api_view(['GET'])
def search_building_by_xy(request):
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

    cache_key = f'building_xy_{x}_{y}_{epsg}'
    cached_data = cache.get(cache_key)
    if cached_data:
        return Response(cached_data)

    buffer = 50
    width = 101
    height = 101
    bbox = f"{x - buffer},{y - buffer},{x + buffer},{y + buffer}"

    params = {
        'VERSION': '1.3.0',
        'SERVICE': 'WMS',
        'REQUEST': 'GetFeatureInfo',
        'LAYERS': 'budynki',
        'QUERY_LAYERS': 'budynki',
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

        features = parse_gugik_feature_info(response.content)

        if not features:
            result = {
                'error': 'No features found at coordinates',
                'coordinates': {'x': x, 'y': y, 'epsg': epsg}
            }
            return Response(result, status=404)

        building_id = features[0].get('Identyfikator budynku', '')
        if not building_id:
            result = {
                'coordinates': {'x': x, 'y': y, 'epsg': epsg},
                'features': features,
                'source': 'KrajowaIntegracjaEwidencjiGruntow'
            }
            cache.set(cache_key, result, timeout=1800)
            return Response(result)

        teryt = building_id[:4]
        service = WFS_SERVICES.get(teryt)

        if not service:
            result = {
                'coordinates': {'x': x, 'y': y, 'epsg': epsg},
                'teryt': teryt,
                'features': features,
                'source': 'KrajowaIntegracjaEwidencjiGruntow',
                'note': 'WFS service not available for geometry'
            }
            cache.set(cache_key, result, timeout=1800)
            return Response(result)

        qgs = QGISManager.get_application()
        layer_names = ['ms:budynki', 'ewns:budynki', 'wfs:budynki']

        for layer_name in layer_names:
            uri = QgsDataSourceUri()
            uri.setParam('url', service['url'])
            uri.setParam('version', 'auto')
            uri.setParam('typename', layer_name)
            uri.setParam('filter', f"ID_BUDYNKU='{building_id}'")
            uri.setParam('ssl_verify', 'false')

            layer = QgsVectorLayer(uri.uri(), f"building_{layer_name}", "WFS")

            if layer.isValid():
                layer_features = list(layer.getFeatures())

                if layer_features:
                    feature = layer_features[0]
                    attributes = {field.name(): qvariant_to_python(value)
                                  for field, value in zip(layer.fields(), feature.attributes())}

                    result = {
                        'coordinates': {'x': x, 'y': y, 'epsg': epsg},
                        'teryt': teryt,
                        'service': service,
                        'building_id': building_id,
                        'attributes': attributes,
                        'geometry': feature.geometry().asWkt()
                    }

                    cache.set(cache_key, result, timeout=3600)

                    del layer
                    return Response(result)

            del layer

        result = {
            'coordinates': {'x': x, 'y': y, 'epsg': epsg},
            'teryt': teryt,
            'features': features,
            'source': 'KrajowaIntegracjaEwidencjiGruntow',
            'note': 'Geometry not available from WFS'
        }
        cache.set(cache_key, result, timeout=1800)
        return Response(result)

    except requests.RequestException as e:
        return Response({'error': f'Request failed: {str(e)}'}, status=500)
    except Exception as e:
        return Response({'error': f'Error: {str(e)}'}, status=500)
