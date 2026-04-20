DOCKER_USER := icij
DOCKER_NAME := datashare-tarentula
CURRENT_VERSION ?= `poetry version -s`
SEMVERS := major minor patch

.PHONY: help install test lint clean tag_version set_version \
        $(SEMVERS) bump-patch bump-minor bump-major _bump-success \
        distribute docker-setup-multiarch docker-publish docker-run

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

tag_version: ## Commit pyproject.toml bump and tag the version
	git commit -m "build: bump to ${CURRENT_VERSION}" pyproject.toml
	git tag ${CURRENT_VERSION}

set_version: ## Set version to $CURRENT_VERSION and tag
	poetry version ${CURRENT_VERSION}
	$(MAKE) tag_version

$(SEMVERS): ## Bump major|minor|patch and tag
	poetry version $@
	$(MAKE) tag_version

bump-patch: ## Bump patch version, commit and tag
	@poetry version patch
	@$(MAKE) --no-print-directory tag_version
	@$(MAKE) --no-print-directory _bump-success

bump-minor: ## Bump minor version, commit and tag
	@poetry version minor
	@$(MAKE) --no-print-directory tag_version
	@$(MAKE) --no-print-directory _bump-success

bump-major: ## Bump major version, commit and tag
	@poetry version major
	@$(MAKE) --no-print-directory tag_version
	@$(MAKE) --no-print-directory _bump-success

_bump-success:
	@NEW_TAG=$$(git describe --tags --abbrev=0); \
	echo ""; \
	echo "Version bumped to $$NEW_TAG"; \
	echo ""; \
	echo "Next steps:"; \
	echo "  1. Push the commit and tag:"; \
	echo "       git push --follow-tags"; \
	echo "  2. Create a GitHub release for $$NEW_TAG:"; \
	echo "       gh release create $$NEW_TAG --generate-notes"; \
	echo "     or open: https://github.com/ICIJ/datashare-tarentula/releases/new?tag=$$NEW_TAG"

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
