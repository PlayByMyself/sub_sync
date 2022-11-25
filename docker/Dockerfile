FROM python:3.8.15-slim as python-base
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    PYSETUP_PATH="/opt/pysetup" \
    VENV_PATH="/opt/pysetup/.venv"
ENV PATH="$VENV_PATH/bin:$PATH"
RUN apt-get update
RUN apt-get install --no-install-recommends -y build-essential ffmpeg

FROM python-base as build-base
ENV POETRY_VERSION=1.1.15
RUN pip install poetry==$POETRY_VERSION
WORKDIR $PYSETUP_PATH
COPY . .
RUN poetry install
RUN poetry build

FROM python-base as install-base
WORKDIR $PYSETUP_PATH/dist
COPY --from=build-base $PYSETUP_PATH/dist/*.whl .
RUN python -m venv $VENV_PATH
RUN $VENV_PATH/bin/python -m pip install $(ls *.whl)


FROM python-base as prod
COPY --from=install-base $VENV_PATH $VENV_PATH
ENTRYPOINT ["sub_sync"]
