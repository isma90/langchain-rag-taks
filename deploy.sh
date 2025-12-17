#!/bin/bash

###############################################################################
# RAG API Deployment Script
#
# Este script automatiza el despliegue del proyecto RAG en Docker
#
# Uso:
#   ./deploy.sh [command] [options]
#
# Comandos:
#   build          Construir imagen Docker
#   up             Iniciar contenedores (docker-compose up)
#   down           Detener contenedores
#   logs           Ver logs de los contenedores
#   status         Ver estado de los contenedores
#   clean          Limpiar volúmenes y contenedores
#   restart        Reiniciar contenedores
#   deploy         Construir e iniciar todo (full deployment)
#
###############################################################################

set -euo pipefail

# ============================================================================
# Configuración
# ============================================================================

# Directorio del script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

# Nombres
PROJECT_NAME="rag-api"
IMAGE_NAME="${PROJECT_NAME}:latest"
DOCKER_COMPOSE_FILE="$PROJECT_ROOT/docker-compose.yml"
ENV_FILE="$PROJECT_ROOT/.env"
DEPLOY_LOG="$PROJECT_ROOT/deploy.log"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================================================
# Funciones auxiliares
# ============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$DEPLOY_LOG"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$DEPLOY_LOG"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$DEPLOY_LOG"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$DEPLOY_LOG"
}

# Verificar comandos requeridos
check_requirements() {
    local missing=0

    log_info "Verificando requisitos..."

    if ! command -v docker &> /dev/null; then
        log_error "Docker no está instalado"
        missing=1
    else
        log_success "Docker: $(docker --version)"
    fi

    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose no está instalado"
        missing=1
    else
        log_success "Docker Compose: $(docker-compose --version)"
    fi

    if [ $missing -eq 1 ]; then
        log_error "Por favor, instala los requisitos faltantes"
        exit 1
    fi
}

# Cargar archivo .env si existe
load_env() {
    if [ -f "$ENV_FILE" ]; then
        log_info "Cargando variables de entorno desde $ENV_FILE"
        export $(grep -v '^#' "$ENV_FILE" | grep -v '^$' | xargs)
    else
        log_warning "Archivo $ENV_FILE no encontrado. Usando valores por defecto."
        # Crear .env de ejemplo si no existe
        create_sample_env
    fi
}

# Crear archivo .env de ejemplo
create_sample_env() {
    log_info "Creando archivo .env de ejemplo..."
    cat > "$ENV_FILE" << 'EOF'
# ============================================================================
# OpenAI Configuration
# ============================================================================
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_MODEL=gpt-4o

# ============================================================================
# Qdrant Configuration
# ============================================================================
# Si usas Qdrant Cloud, proporciona la URL y API key
# Si usas Docker local, puedes dejar los valores por defecto
QDRANT_URL=http://qdrant:6333
QDRANT_API_KEY=
QDRANT_COLLECTION_NAME=rag_documents
QDRANT_PORT=6333
QDRANT_GRPC_PORT=6334

# ============================================================================
# Redis Configuration
# ============================================================================
REDIS_URL=redis://redis:6379
REDIS_PASSWORD=redis
REDIS_PORT=6379
CACHE_TTL=3600

# ============================================================================
# LangSmith Configuration (opcional)
# ============================================================================
LANGSMITH_API_KEY=
LANGSMITH_PROJECT=rag-project

# ============================================================================
# Server Configuration
# ============================================================================
API_PORT=8000
LANGSERVE_HOST=0.0.0.0
LANGSERVE_PORT=8000

# ============================================================================
# Logging
# ============================================================================
LOG_LEVEL=INFO
LOG_FORMAT=json

# ============================================================================
# Environment
# ============================================================================
ENVIRONMENT=production
DEBUG=false
EOF
    log_success "Archivo .env creado. Por favor, actualiza las variables sensibles (OPENAI_API_KEY, etc.)"
}

# Verificar que .env tenga las variables requeridas
validate_env() {
    log_info "Validando variables de entorno..."

    local required_vars=("OPENAI_API_KEY")
    local missing=0

    for var in "${required_vars[@]}"; do
        if [ -z "${!var:-}" ]; then
            log_error "Variable de entorno requerida no configurada: $var"
            missing=1
        fi
    done

    if [ $missing -eq 1 ]; then
        log_error "Por favor, configura todas las variables requeridas en $ENV_FILE"
        exit 1
    fi
}

# ============================================================================
# Comandos de despliegue
# ============================================================================

build_image() {
    log_info "Construyendo imagen Docker: $IMAGE_NAME"

    cd "$PROJECT_ROOT"
    docker build \
        -t "$IMAGE_NAME" \
        -f Dockerfile \
        --build-arg BUILDKIT_INLINE_CACHE=1 \
        .

    if [ $? -eq 0 ]; then
        log_success "Imagen construida exitosamente"
        docker images | grep "$PROJECT_NAME"
    else
        log_error "Error al construir la imagen"
        exit 1
    fi
}

start_containers() {
    log_info "Iniciando contenedores..."

    cd "$PROJECT_ROOT"
    docker-compose -f "$DOCKER_COMPOSE_FILE" up -d

    if [ $? -eq 0 ]; then
        log_success "Contenedores iniciados"
        sleep 5
        show_status
    else
        log_error "Error al iniciar contenedores"
        exit 1
    fi
}

stop_containers() {
    log_info "Deteniendo contenedores..."

    cd "$PROJECT_ROOT"
    docker-compose -f "$DOCKER_COMPOSE_FILE" down

    if [ $? -eq 0 ]; then
        log_success "Contenedores detenidos"
    else
        log_error "Error al detener contenedores"
        exit 1
    fi
}

show_logs() {
    log_info "Mostrando logs en vivo (presiona Ctrl+C para salir)..."

    cd "$PROJECT_ROOT"
    docker-compose -f "$DOCKER_COMPOSE_FILE" logs -f
}

show_status() {
    log_info "Estado de los contenedores:"

    cd "$PROJECT_ROOT"
    docker-compose -f "$DOCKER_COMPOSE_FILE" ps

    echo ""
    log_info "URLs de acceso:"
    echo -e "  ${BLUE}API Docs:${NC} http://localhost:${API_PORT:-8000}/docs"
    echo -e "  ${BLUE}ReDoc:${NC} http://localhost:${API_PORT:-8000}/redoc"
    echo -e "  ${BLUE}Health:${NC} http://localhost:${API_PORT:-8000}/health"
}

restart_containers() {
    log_info "Reiniciando contenedores..."

    cd "$PROJECT_ROOT"
    docker-compose -f "$DOCKER_COMPOSE_FILE" restart

    if [ $? -eq 0 ]; then
        log_success "Contenedores reiniciados"
        sleep 5
        show_status
    else
        log_error "Error al reiniciar contenedores"
        exit 1
    fi
}

clean_resources() {
    log_warning "Limpiando recursos (volúmenes y contenedores)..."

    read -p "¿Estás seguro? Esto eliminará todos los volúmenes (datos). (s/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Ss]$ ]]; then
        cd "$PROJECT_ROOT"
        docker-compose -f "$DOCKER_COMPOSE_FILE" down -v
        log_success "Recursos limpiados"
    else
        log_info "Operación cancelada"
    fi
}

test_api() {
    log_info "Probando API..."

    local api_url="http://localhost:${API_PORT:-8000}"

    # Esperar a que API esté lista
    log_info "Esperando a que API esté lista..."
    local max_attempts=30
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "$api_url/health" > /dev/null 2>&1; then
            log_success "API está lista"
            break
        fi
        log_info "Intento $attempt/$max_attempts..."
        sleep 2
        ((attempt++))
    done

    if [ $attempt -gt $max_attempts ]; then
        log_error "API no está respondiendo después de $max_attempts intentos"
        return 1
    fi

    # Test health endpoint
    log_info "Probando endpoint /health..."
    curl -s "$api_url/health" | python3 -m json.tool
    echo ""

    log_success "API está funcionando correctamente"
}

full_deploy() {
    log_info "========================================"
    log_info "Iniciando despliegue completo"
    log_info "========================================"

    check_requirements
    load_env
    validate_env

    log_info "Paso 1: Construyendo imagen..."
    build_image

    log_info "Paso 2: Iniciando contenedores..."
    start_containers

    log_info "Paso 3: Probando API..."
    if test_api; then
        log_success "========================================"
        log_success "Despliegue completado exitosamente"
        log_success "========================================"
        show_status
    else
        log_error "La prueba de API falló"
        show_logs
        exit 1
    fi
}

# ============================================================================
# Main
# ============================================================================

main() {
    # Inicializar log
    touch "$DEPLOY_LOG"
    log_info "Iniciando script de despliegue"

    # Mostrar banner
    echo -e "${BLUE}"
    echo "╔════════════════════════════════════════╗"
    echo "║     RAG API Deployment Script           ║"
    echo "║     Version 1.0.0                       ║"
    echo "╚════════════════════════════════════════╝"
    echo -e "${NC}"

    # Procesar comando
    local command="${1:-deploy}"

    case "$command" in
        build)
            check_requirements
            load_env
            build_image
            ;;
        up|start)
            check_requirements
            load_env
            start_containers
            ;;
        down|stop)
            check_requirements
            stop_containers
            ;;
        logs)
            check_requirements
            show_logs
            ;;
        status)
            check_requirements
            show_status
            ;;
        restart)
            check_requirements
            load_env
            restart_containers
            ;;
        clean)
            check_requirements
            clean_resources
            ;;
        test)
            check_requirements
            test_api
            ;;
        deploy)
            full_deploy
            ;;
        *)
            echo -e "${YELLOW}Uso: $0 [command] [options]${NC}"
            echo ""
            echo "Comandos disponibles:"
            echo "  build       - Construir imagen Docker"
            echo "  up/start    - Iniciar contenedores"
            echo "  down/stop   - Detener contenedores"
            echo "  logs        - Ver logs"
            echo "  status      - Ver estado"
            echo "  restart     - Reiniciar contenedores"
            echo "  clean       - Limpiar recursos"
            echo "  test        - Probar API"
            echo "  deploy      - Despliegue completo (por defecto)"
            echo ""
            exit 1
            ;;
    esac

    log_info "Script completado"
}

# Ejecutar main
main "$@"
