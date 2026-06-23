.PHONY: help pull up down restart logs shell hugo-version build clean convert media-map media-copy migrate

DOCKER_COMPOSE ?= docker compose
HUGO_SERVICE ?= hugo

help:
	@echo "Zemelaar Hugo workflow"
	@echo ""
	@echo "Targets:"
	@echo "  make pull          Pull Docker images"
	@echo "  make up            Start Hugo dev server at http://localhost:1313"
	@echo "  make down          Stop Hugo dev server"
	@echo "  make restart       Restart Hugo dev server"
	@echo "  make logs          Follow Hugo logs"
	@echo "  make shell         Open shell inside Hugo container"
	@echo "  make hugo-version  Show Hugo version inside container"
	@echo "  make build         Build static site into site/public"
	@echo "  make clean         Remove generated Hugo public/resources output"
	@echo "  make convert       Convert WordPress posts to Hugo Markdown"
	@echo "  make media-map     Rebuild media rewrite map"
	@echo "  make media-copy    Copy media into Hugo static directory"
	@echo "  make migrate       Run media-map, convert, and media-copy"

pull:
	$(DOCKER_COMPOSE) pull

up:
	$(DOCKER_COMPOSE) up

down:
	$(DOCKER_COMPOSE) down

restart:
	$(DOCKER_COMPOSE) down
	$(DOCKER_COMPOSE) up

logs:
	$(DOCKER_COMPOSE) logs -f $(HUGO_SERVICE)

shell:
	$(DOCKER_COMPOSE) run --rm --entrypoint sh $(HUGO_SERVICE)

hugo-version:
	$(DOCKER_COMPOSE) run --rm $(HUGO_SERVICE) version

build:
	$(DOCKER_COMPOSE) run --rm $(HUGO_SERVICE) --minify

clean:
	rm -rf site/public site/resources

convert:
	python3 tools/convert-to-hugo.py

media-map:
	python3 tools/build-media-rewrite-map.py

media-copy:
	python3 tools/copy-media-to-hugo.py --overwrite

migrate: media-map convert media-copy
