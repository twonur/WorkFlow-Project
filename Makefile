.PHONY: local local-d build-local down-local logs-local ps-local shell-local migrate-local createsuperuser-local prod prod-d build-prod down-prod logs-prod ps-prod shell-prod migrate-prod createsuperuser-prod psql-prod

# Local commands (debug on but production-like structure)
local:
	docker-compose up

local-d:
	docker-compose up -d

build-local:
	docker-compose build

down-local:
	docker-compose down

logs-local:
	docker-compose logs -f web-local

nginx-logs-local:
	docker-compose logs -f nginx-local

ps-local:
	docker-compose ps

shell-local:
	docker-compose exec web-local python manage.py shell

migrate-local:
	docker-compose exec web-local python manage.py migrate

createsuperuser-local:
	docker-compose exec web-local python manage.py createsuperuser

psql-local:
	docker-compose exec db-local psql -U postgres

# Production commands
prod:
	docker-compose -f docker-compose.prod.yml -p workflow-prod up -d

build-prod:
	docker-compose -f docker-compose.prod.yml -p workflow-prod build

down-prod:
	docker-compose -f docker-compose.prod.yml -p workflow-prod down

logs-prod:
	docker-compose -f docker-compose.prod.yml -p workflow-prod logs -f

ps-prod:
	docker-compose -f docker-compose.prod.yml -p workflow-prod ps

shell-prod:
	docker-compose -f docker-compose.prod.yml -p workflow-prod exec web-prod python manage.py shell

migrate-prod:
	docker-compose -f docker-compose.prod.yml -p workflow-prod exec web-prod python manage.py migrate

createsuperuser-prod:
	docker-compose -f docker-compose.prod.yml -p workflow-prod exec web-prod python manage.py createsuperuser

psql-prod:
	docker-compose -f docker-compose.prod.yml -p workflow-prod exec db-prod psql -U postgres

# Restart server
restart-server:
	docker-compose -f docker-compose.prod.yml restart web-prod

# Cleanup - remove all containers (use carefully)
clean:
	docker-compose down --remove-orphans
	docker-compose -f docker-compose.prod.yml down --remove-orphans
	docker system prune -f 