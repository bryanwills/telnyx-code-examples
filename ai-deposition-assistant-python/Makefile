.PHONY: setup run test docker-build docker-run
setup:
	cp .env.example .env
	pip install -r requirements.txt
run:
	python app.py
test:
	curl -s http://localhost:5000/health | python -m json.tool
docker-build:
	docker build -t ai-deposition-assistant-python .
docker-run:
	docker run --env-file .env -p 5000:5000 ai-deposition-assistant-python
