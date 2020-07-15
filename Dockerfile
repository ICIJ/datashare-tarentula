FROM python:3.8-buster

RUN apt-get update -qq && apt-get install -qq -y pipenv

# Python 3 surrogate unicode handling
# @see https://click.palletsprojects.com/en/7.x/python3/
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

WORKDIR /opt/app

COPY . .
RUN pipenv run python setup.py install

ENTRYPOINT ["pipenv", "run"]
CMD ["tarentula", "--help"]
