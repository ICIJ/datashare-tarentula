DOCKER_USER := icij
DOCKER_NAME := datashare-tarentula
CURRENT_VERSION ?= `poetry version -s`

clean:
		find . -name "*.pyc" -exec rm -rf {} \;
		rm -rf dist *.egg-info __pycache__

install: install_poetry

install_poetry:
		poetry install --with dev

test:
		poetry run nosetests

minor:
		poetry version minor

major:
		poetry version major

patch:
		poetry version patch

distribute:
		poetry publish --build 

docker-publish: docker-build docker-tag docker-push

docker-run:
		docker run -it $(DOCKER_NAME)

docker-build:
		docker build -t $(DOCKER_NAME) .

docker-tag:
		docker tag $(DOCKER_NAME) $(DOCKER_USER)/$(DOCKER_NAME):${CURRENT_VERSION}
		docker tag $(DOCKER_NAME) $(DOCKER_USER)/$(DOCKER_NAME):latest

docker-push:
		docker push $(DOCKER_USER)/$(DOCKER_NAME):${CURRENT_VERSION}
		docker push $(DOCKER_USER)/$(DOCKER_NAME):latest
