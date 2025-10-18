from qgis.core import QgsApplication
import threading


class QGISManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    QgsApplication.setPrefixPath('/usr', True)
                    cls._instance.qgs = QgsApplication([], False)
                    cls._instance.qgs.initQgis()
        return cls._instance

    @classmethod
    def get_application(cls):
        return cls().qgs