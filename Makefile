.PHONY: up down test smoke logs

up:
	docker compose up --build -d --wait

down:
	docker compose down

test:
	docker compose --profile test run --build --rm --no-deps test

smoke:
	docker compose exec -T -e SMOKE_BASE_URL=http://web api python - < scripts/smoke.py

logs:
	docker compose logs --tail=100 api web
