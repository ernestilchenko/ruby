FROM python:3.11-slim-bookworm

ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    wget \
    gnupg \
    software-properties-common \
    libproj-dev \
    proj-data \
    proj-bin \
    lsb-release \
    grep \
    python3-pyqt5 \
    python3-sip \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip setuptools wheel

RUN wget -qO - https://qgis.org/downloads/qgis-2022.gpg.key | gpg --no-default-keyring --keyring gnupg-ring:/etc/apt/trusted.gpg.d/qgis-archive.gpg --import
RUN chmod a+r /etc/apt/trusted.gpg.d/qgis-archive.gpg
RUN apt-key adv --keyserver hkps://keyserver.ubuntu.com --recv-keys D155B8E6A419C5BE
RUN add-apt-repository "deb https://qgis.org/debian `lsb_release -c -s` main"
RUN echo deb https://qgis.org/debian bookworm main >> /etc/apt/sources.list
RUN echo deb-src https://qgis.org/debian bookworm main >> /etc/apt/sources.list
RUN apt-get update && apt-get install -y --no-install-recommends \
    qgis \
    python3-qgis \
    gdal-bin \
    libgdal-dev \
    python3-gdal \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

ENV GDAL_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu/libgdal.so
ENV GDAL_DATA=/usr/share/gdal
ENV PROJ_LIB=/usr/share/proj
ENV PYTHONPATH=/usr/share/qgis/python:/usr/lib/python3/dist-packages
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal
ENV QT_QPA_PLATFORM=offscreen

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir docopt==0.6.2 --use-pep517
RUN grep -v -E '^(PyQt5|PyQt5-Qt5|PyQt5-stubs|PyQt5_sip)' requirements.txt > requirements_no_pyqt.txt
RUN pip install --no-cache-dir -r requirements_no_pyqt.txt

ENV DJANGO_SETTINGS_MODULE=ruby.settings

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]