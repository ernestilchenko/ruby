from rest_framework import serializers


class BuildingSearchSerializer(serializers.Serializer):
    building_id = serializers.CharField(required=True)
    format = serializers.ChoiceField(choices=['json', 'csv', 'geojson'], default='json')
    epsg = serializers.CharField(required=False, default='4326')


class BuildingDataSerializer(serializers.Serializer):
    attributes = serializers.DictField()
    geometry = serializers.CharField()
    service_info = serializers.DictField(required=False)
