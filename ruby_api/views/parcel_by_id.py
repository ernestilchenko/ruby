from django.core.cache import cache
from qgis.core import QgsVectorLayer, QgsDataSourceUri
from rest_framework.decorators import api_view
from rest_framework.response import Response

from data.wfs_data import WFS_SERVICES
from ruby.qgis_manager import QGISManager
from ruby_api.utils import qvariant_to_python


@api_view(['GET'])
def search_parcel_by_id(request):
    parcel_id = request.query_params.get('parcel_id')

    if not parcel_id:
        return Response({'error': 'parcel_id required'}, status=400)

    if '_' not in parcel_id or len(parcel_id) < 4:
        return Response({'error': 'Invalid parcel_id format'}, status=400)

    cache_key = f'parcel_{parcel_id}'
    cached_data = cache.get(cache_key)
    if cached_data:
        return Response(cached_data)

    try:
        qgs = QGISManager.get_application()
        teryt = parcel_id[:4]
        service = WFS_SERVICES.get(teryt)

        if not service:
            return Response({'error': f'Service not found for TERYT: {teryt}'}, status=404)

        layer_names = ['ms:dzialki', 'ewns:dzialki', 'wfs:dzialki']

        for layer_name in layer_names:
            uri = QgsDataSourceUri()
            uri.setParam('url', service['url'])
            uri.setParam('version', 'auto')
            uri.setParam('typename', layer_name)
            uri.setParam('filter', f"ID_DZIALKI='{parcel_id}'")
            uri.setParam('ssl_verify', 'false')

            layer = QgsVectorLayer(uri.uri(), f"parcel_{layer_name}", "WFS")

            if layer.isValid():
                features = list(layer.getFeatures())

                if features:
                    first_feature = features[0]
                    attributes = {field.name(): qvariant_to_python(value) for field, value in
                                  zip(layer.fields(), first_feature.attributes())}
                    geometry = first_feature.geometry().asWkt()

                    result = {
                        'parcel_id': parcel_id,
                        'service': service,
                        'layer_name': layer_name,
                        'attributes': attributes,
                        'geometry': geometry
                    }

                    cache.set(cache_key, result, timeout=3600)

                    del layer
                    return Response(result)
            del layer

        return Response({'error': 'Parcel not found'}, status=404)
    except Exception as e:
        return Response({'error': f'Error: {str(e)}'}, status=500)
