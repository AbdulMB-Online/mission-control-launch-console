.PHONY: up down test logs

up:
	docker compose up --build -d --wait

down:
	docker compose down

test:
	docker compose --profile test run --build --rm --no-deps test

logs:
	docker compose logs --tail=100 api web
