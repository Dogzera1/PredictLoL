#!/usr/bin/env python3
"""
Health Check Endpoint para Railway - Bot LoL V3

Endpoint simples para Railway verificar se o bot está funcionando.
"""

import os
import time
import json
import psutil
from flask import Flask, jsonify
import threading
import asyncio
from datetime import datetime

app = Flask(__name__)

# Status global do bot
bot_status = {
    "is_running": False,
    "start_time": time.time(),
    "last_heartbeat": time.time(),
    "version": "3.0.0",
    "environment": os.getenv("ENVIRONMENT", "development"),
    "total_requests": 0,
    "errors_count": 0
}

def update_heartbeat():
    """Atualiza heartbeat do bot"""
    global bot_status
    bot_status["last_heartbeat"] = time.time()

def set_bot_running(status: bool):
    """Define status do bot"""
    global bot_status
    bot_status["is_running"] = status
    update_heartbeat()

def increment_request_counter():
    """Incrementa contador de requests"""
    global bot_status
    bot_status["total_requests"] += 1

def increment_error_counter():
    """Incrementa contador de erros"""
    global bot_status
    bot_status["errors_count"] += 1

@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint de health check para Railway"""
    global bot_status
    
    increment_request_counter()
    
    current_time = time.time()
    uptime = current_time - bot_status["start_time"]
    last_heartbeat_ago = current_time - bot_status["last_heartbeat"]
    
    # Considera saudável se heartbeat foi há menos de 5 minutos
    is_healthy = (
        bot_status["is_running"] and 
        last_heartbeat_ago < 300  # 5 minutos
    )
    
    status_code = 200 if is_healthy else 503
    
    response = {
        "status": "healthy" if is_healthy else "unhealthy",
        "timestamp": datetime.now().isoformat(),
        "uptime_seconds": round(uptime, 2),
        "uptime_hours": round(uptime / 3600, 2),
        "bot_running": bot_status["is_running"],
        "last_heartbeat_ago": round(last_heartbeat_ago, 2),
        "version": bot_status["version"],
        "environment": bot_status["environment"],
        "service": "Bot LoL V3 Ultra Avançado"
    }
    
    return jsonify(response), status_code

@app.route('/status', methods=['GET'])
def detailed_status():
    """Status detalhado do bot"""
    global bot_status
    
    increment_request_counter()
    
    current_time = time.time()
    uptime = current_time - bot_status["start_time"]
    
    try:
        # Tenta importar e verificar componentes
        from bot.systems.schedule_manager import ScheduleManager
        components_available = True
    except ImportError:
        components_available = False
    
    response = {
        "service": "Bot LoL V3 Ultra Avançado",
        "version": bot_status["version"],
        "environment": bot_status["environment"],
        "status": {
            "bot_running": bot_status["is_running"],
            "components_available": components_available,
            "uptime_seconds": round(uptime, 2),
            "uptime_hours": round(uptime / 3600, 2)
        },
        "timestamps": {
            "start_time": datetime.fromtimestamp(bot_status["start_time"]).isoformat(),
            "last_heartbeat": datetime.fromtimestamp(bot_status["last_heartbeat"]).isoformat(),
            "current_time": datetime.now().isoformat()
        },
        "metrics": {
            "total_requests": bot_status["total_requests"],
            "errors_count": bot_status["errors_count"],
            "success_rate": round((bot_status["total_requests"] - bot_status["errors_count"]) / max(bot_status["total_requests"], 1) * 100, 2)
        },
        "railway": {
            "deployment": "active",
            "region": os.getenv("RAILWAY_REGION", "unknown"),
            "service_id": os.getenv("RAILWAY_SERVICE_ID", "unknown")
        }
    }
    
    return jsonify(response)

@app.route('/metrics', methods=['GET'])
def system_metrics():
    """Métricas detalhadas do sistema para Railway"""
    increment_request_counter()
    
    try:
        # Métricas do sistema
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        current_time = time.time()
        uptime = current_time - bot_status["start_time"]
        
        response = {
            "service": "Bot LoL V3 Ultra Avançado",
            "timestamp": datetime.now().isoformat(),
            "uptime": {
                "seconds": round(uptime, 2),
                "hours": round(uptime / 3600, 2),
                "days": round(uptime / 86400, 2)
            },
            "system": {
                "cpu_percent": round(cpu_percent, 2),
                "memory": {
                    "total_mb": round(memory.total / 1024 / 1024, 2),
                    "available_mb": round(memory.available / 1024 / 1024, 2),
                    "used_mb": round(memory.used / 1024 / 1024, 2),
                    "percent": round(memory.percent, 2)
                },
                "disk": {
                    "total_gb": round(disk.total / 1024 / 1024 / 1024, 2),
                    "free_gb": round(disk.free / 1024 / 1024 / 1024, 2),
                    "used_gb": round(disk.used / 1024 / 1024 / 1024, 2),
                    "percent": round((disk.used / disk.total) * 100, 2)
                }
            },
            "bot": {
                "running": bot_status["is_running"],
                "total_requests": bot_status["total_requests"],
                "errors_count": bot_status["errors_count"],
                "error_rate": round(bot_status["errors_count"] / max(bot_status["total_requests"], 1) * 100, 2),
                "requests_per_hour": round(bot_status["total_requests"] / max(uptime / 3600, 1), 2)
            },
            "environment": {
                "python_version": f"{psutil.sys.version_info.major}.{psutil.sys.version_info.minor}.{psutil.sys.version_info.micro}",
                "platform": psutil.platform.system(),
                "process_count": len(psutil.pids())
            }
        }
        
        return jsonify(response)
        
    except Exception as e:
        increment_error_counter()
        return jsonify({
            "error": "Failed to collect metrics",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/', methods=['GET'])
def root():
    """Endpoint raiz"""
    increment_request_counter()
    
    return jsonify({
        "service": "Bot LoL V3 Ultra Avançado",
        "status": "online",
        "message": "Bot está executando no Railway",
        "version": bot_status["version"],
        "uptime_hours": round((time.time() - bot_status["start_time"]) / 3600, 2),
        "endpoints": {
            "/health": "Health check endpoint (Railway monitoring)",
            "/status": "Detailed bot status",
            "/metrics": "System metrics and performance",
            "/": "This endpoint"
        }
    })

def run_health_server():
    """Executa servidor de health check em thread separada"""
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

def start_health_server():
    """Inicia servidor de health check"""
    health_thread = threading.Thread(target=run_health_server, daemon=True)
    health_thread.start()
    print(f"🏥 Health check server iniciado na porta {os.getenv('PORT', 8080)}")

if __name__ == "__main__":
    # Executa apenas o servidor de health check
    print("🏥 Iniciando Health Check Server para Railway...")
    run_health_server() 