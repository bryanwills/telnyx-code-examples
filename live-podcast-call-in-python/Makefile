.PHONY: setup run test docker-build docker-run

setup:
	cp -n .env.example .env 2>/dev/null || true
	pip install -r requirements.txt

run:
	python app.py

test:
	python -m py_compile app.py && echo "Syntax OK"

docker-build:
	docker build -t live-podcast-call-in-python .

docker-run:
	docker run --env-file .env -p 5000:5000 live-podcast-call-in-python
