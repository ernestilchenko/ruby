from django.urls import path

from .views import *

urlpatterns = [
    path('search-parcel/', search_parcel_by_id, name='search_parcel_by_id'),
    path('search-parcel-xy/', search_parcel_by_xy, name='search_parcel_by_xy'),
    path('search-building/', search_building_by_id, name='search_building_by_id'),
    path('search-building-xy/', search_building_by_xy, name='search_building_by_xy'),
    path('commune-xy/', get_commune_by_xy, name='get_commune_by_xy'),
    path('county-xy/', get_county_by_xy, name='get_county_by_xy'),
    path('voivodeship-xy/', get_voivodeship_by_xy, name='get_voivodeship_by_xy'),
    path('region-xy/', get_region_by_xy, name='get_region_by_xy'),
    path('region/', get_region_by_id, name='get_region_by_id'),
    path('region-search/', get_region_by_name_or_id, name='get_region_by_name_or_id'),
    path('commune/', get_commune_by_id, name='get_commune_by_id'),
    path('county/', get_county_by_id, name='get_county_by_id'),
    path('voivodeship/', get_voivodeship_by_id, name='get_voivodeship_by_id'),
]
