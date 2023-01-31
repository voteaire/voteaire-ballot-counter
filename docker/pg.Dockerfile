FROM postgres:14.1
COPY ./initialization/setup_db.sh /docker-entrypoint-initdb.d
