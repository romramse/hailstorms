SHELL:=/bin/bash # Use bash syntax

virtualenv:
	@echo "Please ensure install pip3 and virtualenv: $ sudo apt-get install python3-pip virtualenv";
	pip3 install virtualenv
	rm -rf venv
	( \
		virtualenv -p python3 venv; \
		source venv/bin/activate; \
		venv/bin/pip3 install -U -r framework/requirements.txt; \
	)

feeder:
	@( \
		if [ ! -d venv ]; then \
			echo "A python virtualenvironment is expected!"; \
			echo "Please run: make virtualenv"; \
		else \
			. venv/bin/activate; framework/core/feeder.py; \
		fi \
	)

pdf:
	mkdir -p docs
	cat readme.md | markdown | wkhtmltopdf - docs/readme.pdf

build:
	docker build -t romram/hailstorms .

push: build
	docker push romram/hailstorms

docker_hub_deploy: push

pypi:
	python3 setup.py sdist bdist_wheel

pypi_deploy: pypi
	twine upload --repository-url https://upload.pypi.org/legacy/ dist/*

