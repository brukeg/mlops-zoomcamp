LOCAL_TAG:=$(shell date +"%Y-%m-%d-%H-%M")
LOCAL_IMAGE_NAME:=ride-duration:${LOCAL_TAG}

test:
	cd 06-best-practices/code && pipenv run pytest tests/

integration_test:
	cd 06-best-practices/code && pipenv run pytest tests/integration/

quality_checks:
	cd 06-best-practices/code && pipenv run isort .
	cd 06-best-practices/code && pipenv run black .
	cd 06-best-practices/code && pipenv run pylint --recursive=y .

build: quality_checks test
	docker build -t ${LOCAL_IMAGE_NAME} 06-best-practices/code/

setup:
	cd 06-best-practices/code && pipenv install --dev
	cd 06-best-practices/code && pipenv run pre-commit install
