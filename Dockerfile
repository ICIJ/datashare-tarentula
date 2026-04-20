FROM python:3.12-bookworm

ENV POETRY_VERSION=2.1.1
ENV POETRY_HOME="/opt/poetry"
ENV POETRY_VIRTUALENVS_IN_PROJECT=true
ENV POETRY_NO_INTERACTION=1
ENV PATH="$POETRY_HOME/bin:$PATH"

# Fail the build if any command in a RUN pipeline fails (not just the last one).
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN apt-get update \
    && apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/* \
    && curl -sSL https://install.python-poetry.org | python3 - -y --version "$POETRY_VERSION"

# Python 3 surrogate unicode handling
# @see https://click.palletsprojects.com/en/7.x/python3/
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

WORKDIR /opt/app

COPY . .
RUN poetry install

ENTRYPOINT ["poetry", "run"]
CMD ["tarentula", "--help"]
