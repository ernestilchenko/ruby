from qgis.core import QgsVectorLayer, QgsDataSourceUri
from rest_framework.decorators import api_view
from rest_framework.response import Response

from data.wfs_data import WFS_SERVICES
from ruby.qgis_manager import QGISManager
from ruby_api.utils import qvariant_to_python


@api_view(['GET'])
def search_building_by_id(request):
    building_id = request.query_params.get('building_id')

    if not building_id:
        return Response({'error': 'building_id required'}, status=400)

    if len(building_id) < 4:
        return Response({'error': 'Invalid building_id format'}, status=400)

    try:
        qgs = QGISManager.get_application()
        teryt = building_id[:4]
        service = WFS_SERVICES.get(teryt)

        if not service:
            return Response({'error': f'Service not found for TERYT: {teryt}'}, status=404)

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
                features = list(layer.getFeatures())

                if features:
                    first_feature = features[0]
                    attributes = {field.name(): qvariant_to_python(value) for field, value in
                                  zip(layer.fields(), first_feature.attributes())}
                    geometry = first_feature.geometry().asWkt()

                    del layer
                    return Response({
                        'building_id': building_id,
                        'service': service,
                        'layer_name': layer_name,
                        'attributes': attributes,
                        'geometry': geometry
                    })
            del layer

        return Response({'error': 'Building not found'}, status=404)
    except Exception as e:
        return Response({'error': f'Error: {str(e)}'}, status=500)
