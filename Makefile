# Makefile for managing the local streaming setup

# Use bash as the shell
SHELL := /bin/bash

# --- Variables ---
COMPOSE_FILE := docker-compose.yml

# --- Targets ---

.PHONY: all up down logs status clean help

all: up ## Build and start all services

up: ## Build and start all services in detached mode
	@echo "--- Building and starting services... ---"
	docker-compose -f $(COMPOSE_FILE) up --build -d
	@echo "--- Services are starting up. Use 'make logs' to see progress. ---"
	@echo "Kafdrop UI: http://localhost:9000"
	@echo "Python Service (via NGINX): http://localhost:8080/python/"

down: ## Stop and remove all services
	@echo "--- Stopping and removing all services... ---"
	docker-compose -f $(COMPOSE_FILE) down

logs: ## Follow logs for all services
	@echo "--- Following logs (Ctrl+C to stop)... ---"
	docker-compose -f $(COMPOSE_FILE) logs -f

status: ## Show the status of running services
	@echo "--- Current service status: ---"
	docker-compose -f $(COMPOSE_FILE) ps

clean: down ## Stop services and remove all Docker volumes and networks
	@echo "--- Cleaning up Docker resources (volumes, networks)... ---"
	docker-compose -f $(COMPOSE_FILE) down -v --remove-orphans
	@echo "--- Cleanup complete. ---"

help: ## Display this help message
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

# Default target
.DEFAULT_GOAL := help
