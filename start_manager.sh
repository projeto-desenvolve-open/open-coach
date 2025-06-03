#!/bin/bash

# ========================================================
# Gerenciador de Serviços Django + Celery
# Autor: Cosme Alves
# Descrição: Start | Stop | Restart | Status dos serviços
# ========================================================

APP_DIR="$(dirname "$(realpath "$0")")"
LOG_DIR="$APP_DIR/logs"
DJANGO_LOG="$LOG_DIR/django.log"
CELERY_WORKER_LOG="$LOG_DIR/celery_worker.log"
CELERY_BEAT_LOG="$LOG_DIR/celery_beat.log"
DJANGO_PORT=8001

# Comandos
CELERY_WORKER_CMD="celery -A core worker --loglevel=info"
CELERY_BEAT_CMD="celery -A core beat --loglevel=info"

# Cores
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # Sem cor

# Criar diretório de logs, se necessário
mkdir -p "$LOG_DIR"

start() {
    echo -e "${GREEN}Iniciando Django e Celery...${NC}"
    cd "$APP_DIR" || { echo -e "${RED}Erro ao acessar $APP_DIR${NC}"; exit 1; }

    # Django
    if pgrep -f "manage.py runserver" > /dev/null; then
        echo "Django já está rodando."
    else
        nohup python3 manage.py runserver 0.0.0.0:$DJANGO_PORT >> "$DJANGO_LOG" 2>&1 &
        echo "Django iniciado na porta $DJANGO_PORT. Log: $DJANGO_LOG"
    fi

    # Celery Worker
    if pgrep -f "celery.*worker" > /dev/null; then
        echo "Celery Worker já está rodando."
    else
        nohup $CELERY_WORKER_CMD >> "$CELERY_WORKER_LOG" 2>&1 &
        echo "Celery Worker iniciado. Log: $CELERY_WORKER_LOG"
    fi

    # Celery Beat
    if pgrep -f "celery.*beat" > /dev/null; then
        echo "Celery Beat já está rodando."
    else
        # Remove possível arquivo corrompido do scheduler
        SCHEDULE_FILE="$APP_DIR/celerybeat-schedule"
        [[ -f "$SCHEDULE_FILE" ]] && rm -f "$SCHEDULE_FILE"
        nohup $CELERY_BEAT_CMD >> "$CELERY_BEAT_LOG" 2>&1 &
        echo "Celery Beat iniciado. Log: $CELERY_BEAT_LOG"
    fi
}

stop() {
    echo -e "${RED}Parando Django e Celery...${NC}"
    pkill -f "manage.py runserver" && echo "Django parado." || echo "Django já estava parado."
    pkill -f "celery.*worker" && echo "Celery Worker parado." || echo "Celery Worker já estava parado."
    pkill -f "celery.*beat" && echo "Celery Beat parado." || echo "Celery Beat já estava parado."
}

restart() {
    echo "Reiniciando tudo..."
    stop
    sleep 2
    start
}

status() {
    echo "Status dos serviços:"
    pgrep -f "manage.py runserver" > /dev/null && echo "Django: Rodando" || echo "Django: Parado"
    pgrep -f "celery.*worker" > /dev/null && echo "Celery Worker: Rodando" || echo "Celery Worker: Parado"
    pgrep -f "celery.*beat" > /dev/null && echo "Celery Beat: Rodando" || echo "Celery Beat: Parado"
}

case "$1" in
    start) start ;;
    stop) stop ;;
    restart) restart ;;
    status) status ;;
    *)
        echo -e "${RED}Uso: $0 {start|stop|restart|status}${NC}"
        exit 1
        ;;
esac
