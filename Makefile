DOCKER_USER := icij
DOCKER_NAME := datashare-tarentula
CURRENT_VERSION ?= `poetry version -s`

.PHONY: help install test lint clean distribute \
        docker-setup-multiarch docker-publish docker-run

help: ## Show this help
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies with Poetry (including dev group)
	poetry install --with dev

test: ## Run the test suite
	poetry run pytest

lint: ## Run pylint across the tarentula package
	poetry run pylint tarentula

clean: ## Remove build artifacts and __pycache__
	find . -name "*.pyc" -exec rm -rf {} \;
	rm -rf dist *.egg-info __pycache__

distribute: ## Build and publish to PyPI
	poetry publish --build

docker-setup-multiarch: ## Configure Docker for multi-arch builds
	docker run --privileged --rm tonistiigi/binfmt --install all
	docker buildx create --use

docker-publish: ## Build and push multi-arch Docker images
	docker buildx build \
		--platform linux/amd64,linux/arm64 \
		-t $(DOCKER_USER)/$(DOCKER_NAME):${CURRENT_VERSION} \
		-t $(DOCKER_USER)/$(DOCKER_NAME):latest \
		--push .

docker-run: ## Run the Docker image locally
	docker run -it $(DOCKER_NAME)
