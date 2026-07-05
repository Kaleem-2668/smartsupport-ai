#!/usr/bin/env bash
# SmartSupport AI — Production Startup Script
# Usage: ./infra/startup.sh [command]

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
INFRA_DIR="$ROOT_DIR/infra"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log()  { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
err()  { echo -e "${RED}[✗]${NC} $1"; }

validate_env() {
    local missing=0
    local required_vars=(
        "SECRET_KEY"
        "POSTGRES_PASSWORD"
        "AI_API_KEY"
    )

    for var in "${required_vars[@]}"; do
        if [ -z "${!var:-}" ]; then
            err "Missing required env var: $var"
            missing=1
        fi
    done

    # Check optional but recommended
    if [ -z "${NEXT_PUBLIC_API_URL:-}" ]; then
        warn "NEXT_PUBLIC_API_URL not set — API calls will default to localhost"
    fi

    if [ "$missing" -eq 1 ]; then
        err "Please set all required environment variables before starting."
        echo ""
        echo "Required variables:"
        printf "  %s\n" "${required_vars[@]}"
        echo ""
        echo "Copy .env.example and fill in values:"
        echo "  cp apps/backend/.env.example apps/backend/.env"
        exit 1
    fi

    log "All required environment variables are set."
}

start_production() {
    log "Starting SmartSupport AI in production mode..."
    validate_env

    cd "$INFRA_DIR"
    docker compose -f docker-compose.prod.yml up --build -d
    log "SmartSupport AI is running!"
    echo ""
    echo "  Frontend:  http://localhost"
    echo "  Backend:   http://localhost/api/"
    echo "  Docs:      http://localhost/docs"
    echo ""
}

start_development() {
    log "Starting SmartSupport AI in development mode..."
    cd "$INFRA_DIR"
    docker compose up --build -d
    log "SmartSupport AI is running in development mode!"
    echo ""
    echo "  Frontend:  http://localhost:3000"
    echo "  Backend:   http://localhost:8000"
    echo "  Docs:      http://localhost:8000/docs"
    echo ""
}

stop_services() {
    log "Stopping SmartSupport AI..."
    cd "$INFRA_DIR"
    docker compose down
    log "All services stopped."
}

show_logs() {
    cd "$INFRA_DIR"
    docker compose logs -f "$@"
}

show_status() {
    cd "$INFRA_DIR"
    docker compose ps
}

backup_database() {
    local backup_dir="${1:-./backups}"
    mkdir -p "$backup_dir"
    local filename="smartsupport-$(date +%Y%m%d_%H%M%S).sql"
    docker compose exec -T postgres pg_dump -U smartsupport smartsupport > "$backup_dir/$filename"
    log "Database backed up to: $backup_dir/$filename"
}

case "${1:-dev}" in
    prod|production)
        start_production
        ;;
    dev|development)
        start_development
        ;;
    stop)
        stop_services
        ;;
    logs)
        shift
        show_logs "$@"
        ;;
    status)
        show_status
        ;;
    backup)
        shift
        backup_database "$@"
        ;;
    validate)
        validate_env
        ;;
    *)
        echo "SmartSupport AI — Production Startup Script"
        echo ""
        echo "Usage: $0 <command>"
        echo ""
        echo "Commands:"
        echo "  prod         Start in production mode"
        echo "  dev          Start in development mode"
        echo "  stop         Stop all services"
        echo "  logs         View logs"
        echo "  status       Show service status"
        echo "  backup       Backup database"
        echo "  validate     Validate environment variables"
        echo ""
        ;;
esac
