#!/bin/bash

###############################################################################
# Remote RAG API Deployment Script
#
# Script para desplegar RAG API en servidor remoto via SSH
#
# Uso:
#   ./remote-deploy.sh -h <host> -u <usuario> [-p <puerto>] [command]
#
# Ejemplo:
#   ./remote-deploy.sh -h 89.116.74.16 -u root deploy
#   ./remote-deploy.sh -h 89.116.74.16 -u root status
#
###############################################################################

set -euo pipefail

# ============================================================================
# Configuración
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Variables remotas
REMOTE_HOST=""
REMOTE_USER=""
REMOTE_PORT=22
REMOTE_DIR="/opt/rag-api"

# ============================================================================
# Funciones
# ============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

show_usage() {
    cat << EOF
Uso: $0 -h <host> -u <usuario> [-p <puerto>] [command]

Opciones:
  -h, --host       Host remoto (requerido)
  -u, --user       Usuario remoto (requerido)
  -p, --port       Puerto SSH (por defecto: 22)
  -k, --key        Ruta a SSH key (opcional)
  --help           Mostrar esta ayuda

Comandos:
  deploy           Despliegue completo
  build            Solo construir imagen
  up               Iniciar contenedores
  down             Detener contenedores
  logs             Ver logs
  status           Ver estado
  restart          Reiniciar
  clean            Limpiar recursos

Ejemplos:
  $0 -h 89.116.74.16 -u root deploy
  $0 -h 89.116.74.16 -u root -p 2222 status
  $0 -h 89.116.74.16 -u root -k ~/.ssh/id_rsa logs
EOF
}

check_ssh_key() {
    local ssh_key="$1"
    if [ ! -f "$ssh_key" ]; then
        log_error "SSH key no encontrada: $ssh_key"
        return 1
    fi
    log_success "SSH key encontrada: $ssh_key"
    return 0
}

# ============================================================================
# SSH Commands
# ============================================================================

execute_remote() {
    local cmd="$1"
    local ssh_opts="-o StrictHostKeyChecking=no -o ConnectTimeout=10"

    if [ -n "${SSH_KEY:-}" ]; then
        ssh_opts="$ssh_opts -i $SSH_KEY"
    fi

    ssh $ssh_opts -p "$REMOTE_PORT" "$REMOTE_USER@$REMOTE_HOST" "$cmd"
}

upload_project() {
    log_info "Sincronizando proyecto a servidor remoto..."

    local rsync_opts="-avz --delete --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' --exclude='.env' --exclude='logs' --exclude='.venv' --exclude='venv'"

    if [ -n "${SSH_KEY:-}" ]; then
        rsync_opts="$rsync_opts -e 'ssh -i $SSH_KEY'"
    fi

    rsync $rsync_opts "$PROJECT_ROOT/" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/"

    if [ $? -eq 0 ]; then
        log_success "Proyecto sincronizado"
    else
        log_error "Error al sincronizar proyecto"
        return 1
    fi
}

setup_remote_env() {
    log_info "Configurando entorno remoto..."

    execute_remote << 'REMOTE_SCRIPT'
        set -e

        # Crear directorio si no existe
        mkdir -p /opt/rag-api
        cd /opt/rag-api

        # Verificar Docker
        if ! command -v docker &> /dev/null; then
            echo "[ERROR] Docker no está instalado"
            exit 1
        fi

        # Verificar Docker Compose
        if ! command -v docker-compose &> /dev/null; then
            echo "[ERROR] Docker Compose no está instalado"
            exit 1
        fi

        echo "[SUCCESS] Entorno remoto configurado"
REMOTE_SCRIPT
}

remote_deploy() {
    log_info "Iniciando despliegue remoto en $REMOTE_USER@$REMOTE_HOST"

    # 1. Upload proyecto
    upload_project || return 1

    # 2. Setup
    setup_remote_env || return 1

    # 3. Deploy
    log_info "Ejecutando deploy.sh en servidor remoto..."
    execute_remote "cd $REMOTE_DIR && bash deploy.sh deploy" || return 1

    log_success "Despliegue remoto completado"
}

remote_build() {
    log_info "Construyendo imagen en servidor remoto..."
    execute_remote "cd $REMOTE_DIR && bash deploy.sh build"
}

remote_up() {
    log_info "Iniciando contenedores en servidor remoto..."
    execute_remote "cd $REMOTE_DIR && bash deploy.sh up"
}

remote_down() {
    log_info "Deteniendo contenedores en servidor remoto..."
    execute_remote "cd $REMOTE_DIR && bash deploy.sh down"
}

remote_logs() {
    log_info "Mostrando logs del servidor remoto (presiona Ctrl+C para salir)..."
    execute_remote "cd $REMOTE_DIR && bash deploy.sh logs"
}

remote_status() {
    log_info "Estado en servidor remoto:"
    execute_remote "cd $REMOTE_DIR && bash deploy.sh status"
}

remote_restart() {
    log_info "Reiniciando en servidor remoto..."
    execute_remote "cd $REMOTE_DIR && bash deploy.sh restart"
}

remote_clean() {
    log_warning "Limpiando recursos en servidor remoto..."
    execute_remote "cd $REMOTE_DIR && bash deploy.sh clean"
}

# ============================================================================
# Main
# ============================================================================

main() {
    # Parsear argumentos
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--host)
                REMOTE_HOST="$2"
                shift 2
                ;;
            -u|--user)
                REMOTE_USER="$2"
                shift 2
                ;;
            -p|--port)
                REMOTE_PORT="$2"
                shift 2
                ;;
            -k|--key)
                SSH_KEY="$2"
                shift 2
                ;;
            --help)
                show_usage
                exit 0
                ;;
            *)
                COMMAND="$1"
                shift
                ;;
        esac
    done

    # Validar argumentos requeridos
    if [ -z "$REMOTE_HOST" ] || [ -z "$REMOTE_USER" ]; then
        log_error "Host y usuario son requeridos"
        show_usage
        exit 1
    fi

    # Verificar SSH key si se proporciona
    if [ -n "${SSH_KEY:-}" ]; then
        check_ssh_key "$SSH_KEY" || exit 1
    fi

    # Banner
    echo -e "${BLUE}"
    echo "╔════════════════════════════════════════╗"
    echo "║  Remote RAG API Deployment             ║"
    echo "║  Host: $REMOTE_HOST"
    echo "║  User: $REMOTE_USER"
    echo "╚════════════════════════════════════════╝"
    echo -e "${NC}"

    # Comando por defecto
    COMMAND="${COMMAND:-deploy}"

    # Ejecutar comando
    case "$COMMAND" in
        deploy)
            remote_deploy
            ;;
        build)
            upload_project
            setup_remote_env
            remote_build
            ;;
        up)
            remote_up
            ;;
        down)
            remote_down
            ;;
        logs)
            remote_logs
            ;;
        status)
            remote_status
            ;;
        restart)
            remote_restart
            ;;
        clean)
            remote_clean
            ;;
        *)
            log_error "Comando desconocido: $COMMAND"
            show_usage
            exit 1
            ;;
    esac

    if [ $? -eq 0 ]; then
        log_success "Operación completada"
    else
        log_error "Operación falló"
        exit 1
    fi
}

main "$@"
