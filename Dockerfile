FROM python
ENV BOT_NAME=$BOT_NAME

ENV PYTHONFAULTHANDLER=1 \
  PYTHONUNBUFFERED=1 \
  PIP_NO_CACHE_DIR=off \
  PIP_DISABLE_PIP_VERSION_CHECK=on \
  PIP_DEFAULT_TIMEOUT=100 \
  BABEL_CACHE=0

RUN export DEBIAN_FRONTEND=noninteractive && \
    apt-get update && \
    apt-get install -y gdal-bin libgdal-dev && \
    python -m pip install -U pip poetry

COPY poetry.lock pyproject.toml ./
RUN poetry config virtualenvs.create false && \
  poetry install --no-interaction --no-root --no-dev && \
  rm -rf ~/.cache/pypoetry && \
  rm -rf ~/.config/pypoetry

COPY ./ /app/

EXPOSE 8000
ENV PORT 8000

CMD ["python", "/app/app.py"]
WORKDIR /app
