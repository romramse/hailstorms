


build:
	docker build -t romram/hailstorms .

push: build
	docker push romram/hailstorms

docker: push
