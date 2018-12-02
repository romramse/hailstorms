SHELL:=/bin/bash # Use bash syntax

virtualenv:
	if [ -z $(which pip) ]; then
		echo "Please install pip3: $ sudo apt-get install python3-pip"
		exit 1
	fi
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
