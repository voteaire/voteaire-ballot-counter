FROM tiangolo/uwsgi-nginx:python3.9

# libmemcached-dev and zlib1g-dev required for pylibmc (see https://stackoverflow.com/a/56841805)
RUN apt-get update && apt-get install -y \
  gcc
#   libmemcached-dev  \
#   zlib1g-dev

WORKDIR /app
COPY ./requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY ./src/uwsgi.ini ./uwsgi.ini

WORKDIR /app/src
RUN chmod 100 ./wait-for-it.sh
