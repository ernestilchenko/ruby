from django.urls import path

from .views import *

urlpatterns = [
    path('search-parcel/', search_parcel_by_id, name='search_parcel_by_id'),
    path('search-building/', search_building_by_id, name='search_building_by_id'),
]
