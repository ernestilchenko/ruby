web: gunicorn ruby.wsgi:application --bind 0.0.0.0:$PORT --workers 4 --timeout 120
worker: celery -A ruby worker -l info
