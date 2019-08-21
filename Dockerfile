FROM ubuntu:18.04

RUN apt-get update -qq && apt-get install -qq -y lsb-release wget python3 \
  python3-pip python3-virtualenv dpkg-dev fakeroot lintian

# Configure python to use our virtual env
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m virtualenv --python=/usr/bin/python3 $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Python 3 surrogate unicode handling
# @see https://click.palletsprojects.com/en/7.x/python3/
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

WORKDIR /opt/app

COPY setup.py .
RUN pip install --editable .

COPY . .

CMD ["tarentula", "--help"]
