from qgis.core import QgsVectorLayer, QgsDataSourceUri
from rest_framework.decorators import api_view
from rest_framework.response import Response

from ruby.qgis_manager import QGISManager
from ruby_api.utils import qvariant_to_python


@api_view(['GET'])
def get_region_by_id(request):
    region_id = request.query_params.get('region_id')

    if not region_id:
        return Response({'error': 'region_id required'}, status=400)

    parts = region_id.split('_')
    if len(parts) != 2 or '.' not in parts[1]:
        return Response({'error': 'Invalid region_id format. Expected format: WWPPGG_R.OOOO'}, status=400)

    try:
        qgs = QGISManager.get_application()

        uri = QgsDataSourceUri()
        uri.setParam('url', 'https://mapy.geoportal.gov.pl/wss/service/PZGIK/PRG/WFS/AdministrativeBoundaries')
        uri.setParam('typename', 'A06_Granice_obrebow_ewidencyjnych')
        uri.setParam('version', '2.0.0')
        uri.setParam('filter', f"JPT_KOD_JE='{region_id}'")

        layer = QgsVectorLayer(uri.uri(), "region", "WFS")

        if layer.isValid():
            features = list(layer.getFeatures())

            if features:
                first_feature = features[0]
                attributes = {field.name(): qvariant_to_python(value) for field, value in
                              zip(layer.fields(), first_feature.attributes())}

                del layer
                return Response({
                    'region_id': region_id,
                    'region': {
                        'name': attributes.get('JPT_NAZWA_', ''),
                        'teryt': attributes.get('JPT_KOD_JE', ''),
                        'regon': attributes.get('REGON', '')
                    },
                    'source': 'PRG'
                })

        del layer
        return Response({'error': 'Region not found'}, status=404)

    except Exception as e:
        return Response({'error': f'Error: {str(e)}'}, status=500)


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

    try:
        qgs = QGISManager.get_application()

        uri = QgsDataSourceUri()
        uri.setParam('url', 'https://mapy.geoportal.gov.pl/wss/service/PZGIK/PRG/WFS/AdministrativeBoundaries')
        uri.setParam('typename', 'A06_Granice_obrebow_ewidencyjnych')
        uri.setParam('version', '2.0.0')
        uri.setParam('filter', f"JPT_NAZWA_ LIKE '%{query}%'")

        layer = QgsVectorLayer(uri.uri(), "regions", "WFS")

        if layer.isValid():
            features = list(layer.getFeatures())

            results = []
            for feature in features[:10]:
                attributes = {field.name(): qvariant_to_python(value) for field, value in
                              zip(layer.fields(), feature.attributes())}

                results.append({
                    'name': attributes.get('JPT_NAZWA_', ''),
                    'teryt': attributes.get('JPT_KOD_JE', ''),
                    'regon': attributes.get('REGON', '')
                })

            del layer

            if not results:
                return Response({'error': 'No regions found'}, status=404)

            return Response({
                'query': query,
                'regions': results,
                'source': 'PRG'
            })

        del layer
        return Response({'error': 'Service error'}, status=500)

    except Exception as e:
        return Response({'error': f'Error: {str(e)}'}, status=500)


@api_view(['GET'])
def get_commune_by_id(request):
    commune_id = request.query_params.get('commune_id')

    if not commune_id:
        return Response({'error': 'commune_id required'}, status=400)

    if '_' not in commune_id:
        return Response({'error': 'Invalid commune_id format. Expected format: WWPPGG_R'}, status=400)

    try:
        qgs = QGISManager.get_application()

        uri = QgsDataSourceUri()
        uri.setParam('url', 'https://mapy.geoportal.gov.pl/wss/service/PZGIK/PRG/WFS/AdministrativeBoundaries')
        uri.setParam('typename', 'A03_Granice_gmin')
        uri.setParam('version', '2.0.0')
        uri.setParam('filter', f"JPT_KOD_JE='{commune_id}'")

        layer = QgsVectorLayer(uri.uri(), "commune", "WFS")

        if layer.isValid():
            features = list(layer.getFeatures())

            if features:
                first_feature = features[0]
                attributes = {field.name(): qvariant_to_python(value) for field, value in
                              zip(layer.fields(), first_feature.attributes())}

                del layer
                return Response({
                    'commune_id': commune_id,
                    'commune': {
                        'name': attributes.get('JPT_NAZWA_', ''),
                        'teryt': attributes.get('JPT_KOD_JE', ''),
                        'type': attributes.get('JPT_SJR_KO', ''),
                        'regon': attributes.get('REGON', '')
                    },
                    'source': 'PRG'
                })

        del layer
        return Response({'error': 'Commune not found'}, status=404)

    except Exception as e:
        return Response({'error': f'Error: {str(e)}'}, status=500)


@api_view(['GET'])
def get_county_by_id(request):
    county_id = request.query_params.get('county_id')

    if not county_id:
        return Response({'error': 'county_id required'}, status=400)

    if len(county_id) != 4:
        return Response({'error': 'Invalid county_id format. Expected format: WWPP'}, status=400)

    try:
        qgs = QGISManager.get_application()

        uri = QgsDataSourceUri()
        uri.setParam('url', 'https://mapy.geoportal.gov.pl/wss/service/PZGIK/PRG/WFS/AdministrativeBoundaries')
        uri.setParam('typename', 'A02_Granice_powiatow')
        uri.setParam('version', '2.0.0')
        uri.setParam('filter', f"JPT_KOD_JE LIKE '{county_id}%'")

        layer = QgsVectorLayer(uri.uri(), "county", "WFS")

        if layer.isValid():
            features = list(layer.getFeatures())

            if features:
                first_feature = features[0]
                attributes = {field.name(): qvariant_to_python(value) for field, value in
                              zip(layer.fields(), first_feature.attributes())}

                del layer
                return Response({
                    'county_id': county_id,
                    'county': {
                        'name': attributes.get('JPT_NAZWA_', ''),
                        'teryt': attributes.get('JPT_KOD_JE', ''),
                        'regon': attributes.get('REGON', '')
                    },
                    'source': 'PRG'
                })

        del layer
        return Response({'error': 'County not found'}, status=404)

    except Exception as e:
        return Response({'error': f'Error: {str(e)}'}, status=500)


@api_view(['GET'])
def get_voivodeship_by_id(request):
    voivodeship_id = request.query_params.get('voivodeship_id')

    if not voivodeship_id:
        return Response({'error': 'voivodeship_id required'}, status=400)

    if len(voivodeship_id) != 2:
        return Response({'error': 'Invalid voivodeship_id format. Expected format: WW'}, status=400)

    try:
        qgs = QGISManager.get_application()

        uri = QgsDataSourceUri()
        uri.setParam('url', 'https://mapy.geoportal.gov.pl/wss/service/PZGIK/PRG/WFS/AdministrativeBoundaries')
        uri.setParam('typename', 'A01_Granice_wojewodztw')
        uri.setParam('version', '2.0.0')
        uri.setParam('filter', f"JPT_KOD_JE LIKE '{voivodeship_id}%'")

        layer = QgsVectorLayer(uri.uri(), "voivodeship", "WFS")

        if layer.isValid():
            features = list(layer.getFeatures())

            if features:
                first_feature = features[0]
                attributes = {field.name(): qvariant_to_python(value) for field, value in
                              zip(layer.fields(), first_feature.attributes())}

                del layer
                return Response({
                    'voivodeship_id': voivodeship_id,
                    'voivodeship': {
                        'name': attributes.get('JPT_NAZWA_', ''),
                        'teryt': attributes.get('JPT_KOD_JE', ''),
                        'regon': attributes.get('REGON', '')
                    },
                    'source': 'PRG'
                })

        del layer
        return Response({'error': 'Voivodeship not found'}, status=404)

    except Exception as e:
        return Response({'error': f'Error: {str(e)}'}, status=500)
