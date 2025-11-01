# Ruby API 🗺️

<div align="center">

![Django](https://img.shields.io/badge/Django-5.2-092E20?style=for-the-badge&logo=django&logoColor=white)
![QGIS](https://img.shields.io/badge/QGIS-3.x-589632?style=for-the-badge&logo=qgis&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-enabled-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-7.0-DC382D?style=for-the-badge&logo=redis&logoColor=white)

**Polish Cadastral Data API - Access parcels, buildings, and administrative boundaries**

[Features](#-features) • [Quick Start](#-quick-start) • [API Documentation](#-api-documentation) • [Deployment](#-deployment)

</div>

---

## 📋 Overview

Ruby API is a Django REST API that provides programmatic access to Polish cadastral and administrative data from GUGiK (Główny Urząd Geodezji i Kartografii) services. It uses QGIS for geospatial processing and supports queries for parcels, buildings, and administrative boundaries by ID or coordinates.

## ✨ Features

- **Parcel Search** - Find land parcels by ID or coordinates (TERYT format)
- **Building Search** - Retrieve building data with geometry
- **Administrative Boundaries** - Query voivodeships, counties, communes, and cadastral regions
- **Multiple Coordinate Systems** - Support for EPSG:2180, EPSG:4326, and more
- **Automatic Caching** - Redis-based caching for improved performance
- **OpenAPI Documentation** - Interactive Swagger UI for API exploration
- **Geospatial Processing** - QGIS integration for WFS data handling
- **Async Task Queue** - Celery for background processing

## 🛠️ Tech Stack

- **Backend**: Django 5.2 + Django REST Framework
- **Geospatial**: QGIS 3.x + GDAL + PyProj
- **Database**: SQLite (development) / PostgreSQL (production)
- **Cache & Queue**: Redis 7.0 + Celery
- **Containerization**: Docker + Docker Compose
- **Documentation**: drf-spectacular (OpenAPI 3.0)
- **Deployment**: Railway / Gunicorn + WhiteNoise

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- OR Python 3.11+ with QGIS libraries

### Using Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/ernestilchenko/ruby.git
cd ruby

# Create environment file
cp .env.example .env

# Start services
docker-compose up --build

# API will be available at http://localhost:8000
```

## 📚 API Documentation

Interactive API documentation is available at:
- **Swagger UI**: `http://localhost:8000/api/docs/`
- **OpenAPI Schema**: `http://localhost:8000/api/schema/`

### Endpoints

#### Parcels (Działki)

```http
GET /api/search-parcel/?parcel_id=1206_1.0001.123/1
GET /api/search-parcel-xy/?x=500000&y=250000&epsg=2180
```

#### Buildings (Budynki)

```http
GET /api/search-building/?building_id=1206010101.123.456
GET /api/search-building-xy/?x=500000&y=250000&epsg=2180
```

#### Administrative Boundaries

```http
GET /api/region/?region_id=126301_1.0001
GET /api/region-search/?query=Krowodrza
GET /api/commune/?commune_id=126301_1
GET /api/county/?county_id=1206
GET /api/voivodeship/?voivodeship_id=12

GET /api/region-xy/?x=500000&y=250000&epsg=2180
GET /api/commune-xy/?x=500000&y=250000&epsg=2180
GET /api/county-xy/?x=500000&y=250000&epsg=2180
GET /api/voivodeship-xy/?x=500000&y=250000&epsg=2180
```

### Example Response

```json
{
  "parcel_id": "1206_1.0001.123/1",
  "service": {
    "id": "PL.PZGiK.1",
    "organization": "Starosta Powiatu Krakowskiego",
    "teryt": "1206",
    "url": "https://wms.powiat.krakow.pl:1518/iip/ows"
  },
  "attributes": {
    "ID_DZIALKI": "1206_1.0001.123/1",
    "POWIERZCHNIA": 1234.56,
    "NUMER": "123/1"
  },
  "geometry": "POLYGON((...))"
}
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Django secret key | - |
| `DEBUG` | Enable debug mode | `False` |
| `ALLOWED_HOSTS` | Comma-separated allowed hosts | `*` |
| `REDIS_URL` | Redis connection URL | `redis://redis:6379/0` |
| `CELERY_BROKER_URL` | Celery broker URL | Uses `REDIS_URL` |

### Cache Settings

The API uses Redis for caching with different TTLs:
- Parcel/Building by ID: 1 hour
- Parcel/Building by XY: 30 minutes
- Administrative boundaries: 1 hour

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -am 'Add new feature'`
4. Push to the branch: `git push origin feature/your-feature`
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **GUGiK** - Polish cadastral data provider
- **QGIS** - Geospatial processing engine
- **Django** - Web framework
- Data sources: PRG (Państwowy Rejestr Granic), KrajowaIntegracjaEwidencjiGruntow

## 📧 Contact

For questions or support, please open an issue on GitHub.

---