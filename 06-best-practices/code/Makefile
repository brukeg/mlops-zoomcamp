LOCAL_TAG:=$(shell date +"%Y-%m-%d-%H-%M")
LOCAL_IMAGE_NAME:=ride-duration:${LOCAL_TAG}

test:
	cd /Users/brukegetachew/git_repos/mlops-zoomcamp/06-best-practices/code && pipenv run pytest tests/

quality_checks:
	cd /Users/brukegetachew/git_repos/mlops-zoomcamp/06-best-practices/code && pipenv run isort .
	cd /Users/brukegetachew/git_repos/mlops-zoomcamp/06-best-practices/code && pipenv run black .
	cd /Users/brukegetachew/git_repos/mlops-zoomcamp/06-best-practices/code && pipenv run pylint --recursive=y .

build: quality_checks test
	docker build -t ${LOCAL_IMAGE_NAME} 06-best-practices/code/

setup:
	cd /Users/brukegetachew/git_repos/mlops-zoomcamp/06-best-practices/code && pipenv install --dev
	cd /Users/brukegetachew/git_repos/mlops-zoomcamp/06-best-practices/code && pipenv run pre-commit install
