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
RUN apt-get update \
    && apt-get install --no-install-recommends -y ffmpeg \
    && apt-get clean \
    && apt-get autoclean \
    && apt-get autoremove

FROM python-base as build-base
RUN apt-get install --no-install-recommends -y build-essential

FROM build-base as build-whl
ENV POETRY_VERSION=1.2.2
RUN pip install poetry==$POETRY_VERSION
WORKDIR $PYSETUP_PATH
COPY . .
RUN poetry install
RUN poetry run pytest
RUN poetry build

FROM build-base as install-whl
WORKDIR $PYSETUP_PATH/dist
COPY --from=build-whl $PYSETUP_PATH/dist/*.whl .
RUN python -m venv $VENV_PATH
RUN python -m pip install $(ls *.whl | tail -n 1)


FROM python-base as prod
COPY --from=install-whl $VENV_PATH $VENV_PATH
ENTRYPOINT ["sub_sync"]
