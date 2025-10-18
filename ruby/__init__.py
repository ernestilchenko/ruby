from .celery import app as celery_app
from .qgis_manager import QGISManager

__all__ = ('celery_app',)

QGISManager()