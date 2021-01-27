DOCKER_USER := icij
DOCKER_NAME := datashare-tarentula
CURRENT_VERSION ?= `pipenv run python setup.py --version`

clean:
		find . -name "*.pyc" -exec rm -rf {} \;
		rm -rf dist *.egg-info __pycache__

install: install_pip

install_pip:
		pipenv install -d

test:
		pipenv run python setup.py test

minor:
		pipenv run bumpversion --commit --tag --current-version ${CURRENT_VERSION} minor tarentula/__init__.py

major:
		pipenv run bumpversion --commit --tag --current-version ${CURRENT_VERSION} major tarentula/__init__.py

patch:
		pipenv run bumpversion --commit --tag --current-version ${CURRENT_VERSION} patch tarentula/__init__.py

distribute:
		pipenv run python setup.py sdist bdist_wheel
		pipenv run twine upload dist/*

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
