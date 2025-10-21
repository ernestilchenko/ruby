from rest_framework import serializers


class ParcelSearchSerializer(serializers.Serializer):
    parcel_id = serializers.CharField(required=True, help_text="ID działki (np. 1206_1.0001.123)")


class CoordinateSearchSerializer(serializers.Serializer):
    x = serializers.FloatField(required=True, help_text="Współrzędna X")
    y = serializers.FloatField(required=True, help_text="Współrzędna Y")
    epsg = serializers.CharField(default='2180', help_text="Kod EPSG układu współrzędnych")


class BuildingSearchSerializer(serializers.Serializer):
    building_id = serializers.CharField(required=True)
    format = serializers.ChoiceField(choices=['json', 'csv', 'geojson'], default='json')
    epsg = serializers.CharField(required=False, default='4326')


class BuildingDataSerializer(serializers.Serializer):
    attributes = serializers.DictField()
    geometry = serializers.CharField()
    service_info = serializers.DictField(required=False)
