#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Log file
LOG_DIR="./logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/services_$(date +%Y%m%d_%H%M%S).log"

# Function to log messages
log_message() {
  local level=$1
  local message=$2
  local timestamp=$(date +"%Y-%m-%d %H:%M:%S")
  echo -e "[$timestamp] [$level] $message" | tee -a "$LOG_FILE"
}

# Function to check service health
check_health() {
  local service=$1
  log_message "INFO" "Checking health for $service..."
  
  # Check if service is running
  if docker-compose ps "$service" | grep -q "Up"; then
    case "$service" in
      "db")
        # Check if PostgreSQL is accepting connections
        if docker-compose exec -T db pg_isready -U "${DB_USER:-agroman}" > /dev/null 2>&1; then
          log_message "INFO" "${GREEN}Service $service is healthy${NC}"
          return 0
        else
          log_message "ERROR" "${RED}Service $service is running but not healthy${NC}"
          return 1
        fi
        ;;
      "app" | "bot")
        # Simple check - just see if container logs have any errors
        if docker-compose logs --tail=20 "$service" | grep -i "error\|exception\|fail" > /dev/null; then
          log_message "ERROR" "${RED}Service $service has errors in logs${NC}"
          return 1
        else
          log_message "INFO" "${GREEN}Service $service appears healthy${NC}"
          return 0
        fi
        ;;
      "metabase")
        # Check if metabase is responding on its port
        if curl -s http://localhost:3000 > /dev/null 2>&1; then
          log_message "INFO" "${GREEN}Service $service is healthy${NC}"
          return 0
        else
          log_message "ERROR" "${RED}Service $service is running but not responding${NC}"
          return 1
        fi
        ;;
      *)
        log_message "INFO" "${YELLOW}No specific health check for $service, assuming healthy if running${NC}"
        return 0
        ;;
    esac
  else
    log_message "ERROR" "${RED}Service $service is not running${NC}"
    return 1
  fi
}

# Build and start services
build_and_start() {
  log_message "INFO" "Building and starting services..."
  docker-compose build 2>&1 | tee -a "$LOG_FILE"
  if [ ${PIPESTATUS[0]} -ne 0 ]; then
    log_message "ERROR" "${RED}Failed to build services${NC}"
    return 1
  fi

  docker-compose up -d 2>&1 | tee -a "$LOG_FILE"
  if [ ${PIPESTATUS[0]} -ne 0 ]; then
    log_message "ERROR" "${RED}Failed to start services${NC}"
    return 1
  fi

  log_message "INFO" "${GREEN}Services built and started successfully${NC}"
  return 0
}

# Check health of all services
check_all_health() {
  log_message "INFO" "Checking health of all services..."
  local all_healthy=true

  for service in app bot db metabase; do
    if ! check_health "$service"; then
      all_healthy=false
    fi
  done

  if $all_healthy; then
    log_message "INFO" "${GREEN}All services are healthy${NC}"
    return 0
  else
    log_message "ERROR" "${RED}Some services are not healthy${NC}"
    return 1
  fi
}

# Show logs for a service
show_logs() {
  local service=$1
  local lines=${2:-100}
  log_message "INFO" "Showing last $lines lines of logs for $service..."
  docker-compose logs --tail="$lines" "$service" 2>&1 | tee -a "$LOG_FILE"
}

# Show errors for a service
show_errors() {
  local service=$1
  local lines=${2:-100}
  log_message "INFO" "Showing errors in logs for $service..."
  docker-compose logs --tail="$lines" "$service" 2>&1 | grep -i "error\|exception\|fail" | tee -a "$LOG_FILE"
}

# Main execution
case "$1" in
  "build")
    build_and_start
    ;;
  "start")
    docker-compose up -d 2>&1 | tee -a "$LOG_FILE"
    ;;
  "stop")
    log_message "INFO" "Stopping services..."
    docker-compose down 2>&1 | tee -a "$LOG_FILE"
    ;;
  "restart")
    log_message "INFO" "Restarting services..."
    docker-compose restart 2>&1 | tee -a "$LOG_FILE"
    ;;
  "health")
    check_all_health
    ;;
  "logs")
    if [ "$2" ]; then
      show_logs "$2" "$3"
    else
      log_message "ERROR" "Please specify a service name"
      exit 1
    fi
    ;;
  "errors")
    if [ "$2" ]; then
      show_errors "$2" "$3"
    else
      log_message "INFO" "Showing errors for all services..."
      for service in app bot db metabase; do
        echo -e "\n${YELLOW}=== Errors for $service ===${NC}"
        show_errors "$service" "$3"
      done
    fi
    ;;
  *)
    echo "Usage: $0 {build|start|stop|restart|health|logs <service> [lines]|errors [service] [lines]}"
    echo "  build    - Build and start all services"
    echo "  start    - Start all services"
    echo "  stop     - Stop all services"
    echo "  restart  - Restart all services"
    echo "  health   - Check health of all services"
    echo "  logs     - Show logs for a specific service"
    echo "  errors   - Show errors for all or a specific service"
    ;;
esac 