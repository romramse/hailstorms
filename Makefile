SHELL:=/bin/bash # Use bash syntax

virtualenv:
	pip install virtualenv
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
