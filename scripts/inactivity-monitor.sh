#!/bin/bash
# Sovereign AI - Inactivity Monitor
# Auto-shuts down the stack after 10 minutes of inactivity
# 
# Activity is detected by:
# - HTTP requests to OpenWebUI (port 3000)
# - HTTP requests to MCPO (port 8000)
# - HTTP requests to Open Notebook (port 8502)
# - Ollama API calls (port 11434)

DIR="$(cd "$(dirname "$0")/.." && pwd)"
LOG_FILE="$DIR/logs/inactivity-monitor.log"
PID_FILE="$DIR/logs/inactivity-monitor.pid"
ACTIVITY_FILE="$DIR/logs/.last-activity"

# Default inactivity timeout in seconds (10 minutes)
DEFAULT_TIMEOUT=600
TIMEOUT=${INACTIVITY_TIMEOUT:-$DEFAULT_TIMEOUT}

# Check interval in seconds
CHECK_INTERVAL=30

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

get_activity_timestamp() {
    if [ -f "$ACTIVITY_FILE" ]; then
        cat "$ACTIVITY_FILE"
    else
        echo "0"
    fi
}

update_activity() {
    date +%s > "$ACTIVITY_FILE"
}

check_http_activity() {
    local port=$1
    # Check if there are recent connections to the port
    # Using netstat or ss to check established connections
    local connections=$(ss -tn state established "( sport = :$port )" 2>/dev/null | wc -l)
    
    # If there are active connections, that's activity
    if [ "$connections" -gt 0 ]; then
        return 0  # Activity detected
    fi
    
    # Check access logs for recent activity (last 60 seconds)
    case $port in
        3000)
            # OpenWebUI - check for recent log entries
            if docker logs openwebui --tail 100 2>&1 | grep -q "$(date '+%Y-%m-%d')"; then
                return 0
            fi
            ;;
        11434)
            # Ollama - check for recent API calls
            if docker logs ollama --tail 100 2>&1 | grep -q "$(date '+%Y-%m-%d\|%H:%M')"; then
                return 0
            fi
            ;;
    esac
    
    return 1  # No activity
}

check_ollama_activity() {
    # Check if Ollama has any active requests or recent completions
    local recent_logs=$(docker logs ollama --since 60s 2>&1)
    
    if echo "$recent_logs" | grep -qE "request|completion|generate|embed"; then
        return 0
    fi
    
    return 1
}

check_any_activity() {
    local current_time=$(date +%s)
    local last_activity=$(get_activity_timestamp)
    local elapsed=$((current_time - last_activity))
    
    # Check for HTTP activity on key ports
    for port in 3000 8000 8502 11434; do
        if check_http_activity $port; then
            log "Activity detected on port $port"
            update_activity
            return 0
        fi
    done
    
    # Check Ollama specifically
    if check_ollama_activity; then
        log "Ollama activity detected"
        update_activity
        return 0
    fi
    
    # Check if elapsed time is less than timeout
    if [ "$elapsed" -lt "$TIMEOUT" ]; then
        return 0
    fi
    
    return 1
}

shutdown_stack() {
    log "Inactivity timeout reached. Shutting down..."
    
    # Stop Docker services
    cd "$DIR"
    docker compose down 2>/dev/null
    
    log "Docker services stopped"
    
    # Stop Ollama (optional - comment out if you want to keep it running)
    # sudo systemctl stop ollama
    # log "Ollama stopped"
    
    # Clean up
    rm -f "$PID_FILE"
    
    # Send notification if possible
    if command -v notify-send &> /dev/null; then
        notify-send "Sovereign AI" "Auto-shutdown: 10 minutes of inactivity"
    fi
    
    log "Shutdown complete"
    exit 0
}

start_monitor() {
    # Check if already running
    if [ -f "$PID_FILE" ]; then
        local old_pid=$(cat "$PID_FILE")
        if kill -0 "$old_pid" 2>/dev/null; then
            echo "Inactivity monitor already running (PID: $old_pid)"
            exit 1
        fi
    fi
    
    # Create logs directory
    mkdir -p "$DIR/logs"
    
    # Initialize activity timestamp
    update_activity
    
    # Save PID
    echo $$ > "$PID_FILE"
    
    log "Inactivity monitor started (timeout: ${TIMEOUT}s)"
    
    # Main monitoring loop
    while true; do
        sleep $CHECK_INTERVAL
        
        if ! check_any_activity; then
            shutdown_stack
        fi
    done
}

stop_monitor() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid"
            log "Inactivity monitor stopped"
        fi
        rm -f "$PID_FILE"
    fi
}

status_monitor() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            local last_activity=$(get_activity_timestamp)
            local current_time=$(date +%s)
            local elapsed=$((current_time - last_activity))
            local remaining=$((TIMEOUT - elapsed))
            
            echo "Inactivity monitor: RUNNING (PID: $pid)"
            echo "Time until shutdown: ${remaining}s"
            exit 0
        fi
    fi
    echo "Inactivity monitor: NOT RUNNING"
    exit 1
}

case "${1:-start}" in
    start)
        start_monitor
        ;;
    stop)
        stop_monitor
        ;;
    status)
        status_monitor
        ;;
    restart)
        stop_monitor
        sleep 1
        start_monitor
        ;;
    *)
        echo "Usage: $0 {start|stop|status|restart}"
        exit 1
        ;;
esac