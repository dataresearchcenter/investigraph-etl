FROM ghcr.io/dataresearchcenter/ftmq:latest

LABEL org.opencontainers.image.title="Investigraph"
LABEL org.opencontainers.image.licenses=MIT
LABEL org.opencontainers.image.source=https://github.com/dataresearchcenter/investigraph

RUN apt-get update && apt-get -y upgrade
RUN apt-get install -y git
RUN pip install -q -U pip setuptools

RUN apt-get install -y pkg-config libicu-dev
RUN apt-get install -y libleveldb-dev
RUN pip install -q --no-binary=:pyicu: pyicu
RUN pip install -q psycopg2-binary

COPY investigraph /investigraph/investigraph
COPY setup.py /investigraph/
COPY pyproject.toml /investigraph/
COPY VERSION /investigraph/
COPY README.md /investigraph/

RUN pip install -q plyvel
RUN pip install -q /investigraph

RUN mkdir -p /data
RUN chown -R 1000:1000 /data

ENV INVESTIGRAPH_DATA_ROOT=/data
ENV INVESTIGRAPH_STORE_URI=leveldb:///data/store.db
ENV DEBUG=0

USER 1000
WORKDIR /data
ENTRYPOINT ["investigraph"]
