#!/usr/bin/env python3
"""
Health Check Simplificado para Railway - Bot LoL V3
Versão robusta sem dependências complexas
"""

import os
import time
import json
from datetime import datetime
from flask import Flask, jsonify

app = Flask(__name__)

# Status simplificado do bot
start_time = time.time()
request_count = 0

def get_uptime():
    """Calcula uptime em segundos"""
    return time.time() - start_time

def increment_requests():
    """Incrementa contador de requests"""
    global request_count
    request_count += 1

@app.route('/health', methods=['GET'])
def health_check():
    """Health check principal para Railway"""
    increment_requests()
    
    uptime = get_uptime()
    
    # Sempre retorna 200 OK - Railway apenas quer saber se o serviço responde
    response = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "uptime_seconds": round(uptime, 2),
        "uptime_hours": round(uptime / 3600, 2),
        "service": "Bot LoL V3 Ultra Avançado",
        "version": "3.0.0",
        "environment": os.getenv("ENVIRONMENT", "production"),
        "railway": True,
        "requests": request_count
    }
    
    return jsonify(response), 200

@app.route('/', methods=['GET'])
def root():
    """Endpoint raiz"""
    increment_requests()
    
    uptime = get_uptime()
    
    return jsonify({
        "service": "Bot LoL V3 Ultra Avançado",
        "status": "online",
        "message": "Serviço funcionando no Railway",
        "uptime_hours": round(uptime / 3600, 2),
        "endpoints": {
            "/": "Página inicial",
            "/health": "Health check para Railway",
            "/status": "Status detalhado",
            "/ping": "Teste de conectividade"
        },
        "telegram_bot": "@BETLOLGPT_bot",
        "version": "3.0.0"
    })

@app.route('/status', methods=['GET'])
def status():
    """Status detalhado"""
    increment_requests()
    
    uptime = get_uptime()
    
    # Verifica variáveis de ambiente essenciais
    env_status = {
        "TELEGRAM_BOT_TOKEN": "✅" if os.getenv("TELEGRAM_BOT_TOKEN") else "❌",
        "TELEGRAM_ADMIN_USER_IDS": "✅" if os.getenv("TELEGRAM_ADMIN_USER_IDS") else "❌",
        "PORT": os.getenv("PORT", "8080"),
        "ENVIRONMENT": os.getenv("ENVIRONMENT", "production")
    }
    
    return jsonify({
        "service": "Bot LoL V3 Ultra Avançado",
        "uptime": {
            "seconds": round(uptime, 2),
            "minutes": round(uptime / 60, 2),
            "hours": round(uptime / 3600, 2)
        },
        "environment": env_status,
        "system": {
            "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}",
            "platform": os.name,
            "requests_served": request_count
        },
        "telegram": {
            "bot_username": "@BETLOLGPT_bot",
            "token_configured": bool(os.getenv("TELEGRAM_BOT_TOKEN")),
            "admin_configured": bool(os.getenv("TELEGRAM_ADMIN_USER_IDS"))
        },
        "railway": {
            "deployment": "active",
            "service_id": os.getenv("RAILWAY_SERVICE_ID", "unknown"),
            "environment_id": os.getenv("RAILWAY_ENVIRONMENT_ID", "unknown")
        }
    })

@app.route('/ping', methods=['GET'])
def ping():
    """Teste simples de conectividade"""
    increment_requests()
    
    return jsonify({
        "pong": True,
        "timestamp": datetime.now().isoformat(),
        "uptime_seconds": round(get_uptime(), 2)
    })

@app.errorhandler(404)
def not_found(error):
    """Handler para 404"""
    return jsonify({
        "error": "Endpoint não encontrado",
        "available_endpoints": ["/", "/health", "/status", "/ping"],
        "service": "Bot LoL V3 Ultra Avançado"
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handler para erros internos"""
    return jsonify({
        "error": "Erro interno do servidor",
        "message": "O serviço está funcionando, mas houve um erro na requisição",
        "service": "Bot LoL V3 Ultra Avançado"
    }), 500

def run_server():
    """Executa o servidor"""
    port = int(os.getenv("PORT", 8080))
    host = "0.0.0.0"
    
    print(f"🏥 Health Check Server iniciando...")
    print(f"   📡 Host: {host}")
    print(f"   🔌 Porta: {port}")
    print(f"   🌐 Environment: {os.getenv('ENVIRONMENT', 'production')}")
    print(f"   🤖 Bot: @BETLOLGPT_bot")
    
    app.run(
        host=host,
        port=port,
        debug=False,
        use_reloader=False,
        threaded=True
    )

if __name__ == "__main__":
    print("🚀 Iniciando Health Check Server para Railway...")
    run_server() 