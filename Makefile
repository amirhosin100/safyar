run-dev:
	docker compose --file docker/docker-compose-dev.yml --env-file .env up -d

stop-dev:
	docker compose --file docker/docker-compose-dev.yml --env-file .env stop

run-prod:
	docker compose --file docker/docker-compose-prod.yml --env-file .env up -d

stop-prod:
	docker compose --file docker/docker-compose-prod.yml --env-file .env stop
