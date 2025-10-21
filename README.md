# Ruby API - Polish Cadastral Data API

API для доступа к польским кадастровым данным (земельные участки, здания, административные границы).

## Описание

Ruby API предоставляет REST API для работы с польскими геопространственными данными:
- Поиск земельных участков (działki) по ID и координатам
- Поиск зданий (budynki) по ID и координатам
- Получение административных границ (gminy, powiaty, województwa, obręby)
- Интеграция с государственными WMS/WFS сервисами GUGiK

## Технологии

- **Backend**: Django 5.2.7 + Django REST Framework
- **Геопространственные библиотеки**: QGIS, GDAL, GeoPandas, Shapely
- **Кэширование**: Redis
- **Задачи**: Celery (опционально)
- **Документация API**: OpenAPI/Swagger (drf-spectacular)
- **Контейнеризация**: Docker + Docker Compose

## Быстрый старт

### Локальная разработка с Docker Compose

1. Клонируйте репозиторий:
```bash
git clone <your-repo-url>
cd ruby
```

2. Создайте файл `.env` на основе `.env.example`:
```bash
cp .env.example .env
# Отредактируйте .env и добавьте SECRET_KEY
```

3. Запустите с помощью Docker Compose:
```bash
docker-compose up --build
```

4. API будет доступен по адресу: `http://localhost:8000`

### Без Docker (локальная установка)

Требования:
- Python 3.11
- QGIS 3.x
- Redis

```bash
# Установите зависимости
pip install -r requirements.txt

# Запустите Redis
redis-server

# Примените миграции
python manage.py migrate

# Соберите статические файлы
python manage.py collectstatic

# Запустите сервер
python manage.py runserver
```

## Документация API

После запуска сервера:

- **Swagger UI**: http://localhost:8000/api/docs/
- **OpenAPI Schema**: http://localhost:8000/api/schema/

## Примеры использования

### Поиск участка по координатам
```bash
curl "http://localhost:8000/api/search-parcel-xy/?x=500000&y=250000&epsg=2180"
```

### Поиск участка по ID
```bash
curl "http://localhost:8000/api/search-parcel/?parcel_id=1206_1.0001.123"
```

### Поиск здания по координатам
```bash
curl "http://localhost:8000/api/search-building-xy/?x=500000&y=250000&epsg=2180"
```

### Получение информации о commune (gmina)
```bash
curl "http://localhost:8000/api/commune-xy/?x=500000&y=250000&epsg=2180"
```

## API Endpoints

### Земельные участки (Parcels)
- `GET /api/search-parcel/` - Поиск по cadastral ID
- `GET /api/search-parcel-xy/` - Поиск по координатам

### Здания (Buildings)
- `GET /api/search-building/` - Поиск по ID
- `GET /api/search-building-xy/` - Поиск по координатам

### Административные границы
- `GET /api/commune-xy/` - Получить commune по координатам
- `GET /api/county-xy/` - Получить county по координатам
- `GET /api/voivodeship-xy/` - Получить voivodeship по координатам
- `GET /api/region-xy/` - Получить cadastral region по координатам
- `GET /api/commune/` - Получить commune по ID
- `GET /api/county/` - Получить county по ID
- `GET /api/voivodeship/` - Получить voivodeship по ID
- `GET /api/region/` - Получить region по ID
- `GET /api/region-search/` - Поиск region по названию

## Деплой на Railway

Подробная инструкция по развертыванию на Railway: [RAILWAY_DEPLOYMENT.md](RAILWAY_DEPLOYMENT.md)

Краткая версия:
1. Создайте проект на Railway
2. Подключите GitHub репозиторий
3. Добавьте Redis сервис
4. Настройте переменные окружения (SECRET_KEY, DEBUG=False)
5. Railway автоматически задеплоит приложение

## Структура проекта

```
ruby/
├── ruby/                      # Django project configuration
│   ├── settings.py           # Основные настройки
│   ├── urls.py               # URL routing
│   ├── wsgi.py               # WSGI entry point
│   └── qgis_manager.py       # QGIS integration
├── ruby_api/                  # Основное приложение
│   ├── views/                # API endpoints
│   ├── serializers.py        # DRF serializers
│   └── urls.py               # App URLs
├── data/
│   └── wfs_data.py           # 384 WFS service configurations
├── static/                    # Статические файлы
├── Dockerfile                 # Docker configuration
├── docker-compose.yml         # Multi-container setup
├── requirements.txt           # Python dependencies
├── railway.json               # Railway configuration
├── Procfile                   # Process configuration
└── manage.py                  # Django CLI
```

## Переменные окружения

### Обязательные
- `SECRET_KEY` - Django secret key (генерируется при установке)

### Опциональные
- `DEBUG` - Debug режим (default: False)
- `ALLOWED_HOSTS` - Разрешенные хосты (default: *)
- `REDIS_URL` - Redis connection URL (default: redis://redis:6379/0)
- `CACHE_URL` - Cache Redis URL (default: REDIS_URL/1)
- `CELERY_BROKER_URL` - Celery broker URL (default: REDIS_URL)
- `CELERY_RESULT_BACKEND` - Celery results backend (default: REDIS_URL)

## Разработка

### Генерация SECRET_KEY
```python
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

### Запуск тестов
```bash
pytest
# или
python manage.py test
```

### Запуск Celery worker (опционально)
```bash
celery -A ruby worker -l info
```

## Источники данных

- **GUGiK WMS**: Кадастровые данные по координатам
- **Regional WFS Services**: 384 региональных WFS сервиса
- **PRG WFS**: Данные об административных границах

## Координатные системы

Поддерживаемые EPSG коды:
- `EPSG:2180` - Польская система координат (по умолчанию)
- `EPSG:4326` - WGS84 (широта/долгота)

## Лицензия

[Укажите вашу лицензию]

## Поддержка

- Issues: https://github.com/your-username/ruby/issues
- Email: your-email@example.com

## TODO

- [ ] Добавить тесты (pytest)
- [ ] Улучшить error handling и logging
- [ ] Добавить rate limiting
- [ ] Реализовать batch queries
- [ ] Добавить health check endpoint
- [ ] Добавить мониторинг и metrics
- [ ] Оптимизировать кэширование административных границ
- [ ] Документация на английском языке
