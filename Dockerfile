FROM python:3.8-buster

RUN pip3 install poetry

# Python 3 surrogate unicode handling
# @see https://click.palletsprojects.com/en/7.x/python3/
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

WORKDIR /opt/app

COPY . .
RUN poetry install

ENTRYPOINT ["poetry", "run"]
CMD ["tarentula", "--help"]
