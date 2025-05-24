#!/usr/bin/env python3
"""
Servidor healthcheck standalone para testar containers
"""

from flask import Flask, jsonify
from datetime import datetime
import threading
import time
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HealthCheckServer:
    def __init__(self):
        self.app = Flask(__name__)
        self.healthy = True
        self.startup_time = datetime.now()
        self.last_activity = datetime.now()
        
        self.setup_routes()
    
    def setup_routes(self):
        @self.app.route('/health')
        def health_check():
            """Endpoint de healthcheck para container"""
            try:
                current_time = datetime.now()
                uptime = (current_time - self.startup_time).total_seconds()
                time_since_activity = (current_time - self.last_activity).total_seconds()
                
                status = {
                    'status': 'healthy' if self.healthy else 'unhealthy',
                    'uptime_seconds': uptime,
                    'last_activity_seconds_ago': time_since_activity,
                    'timestamp': current_time.isoformat(),
                    'service': 'Bot LoL V3 Healthcheck',
                    'version': '1.0.0'
                }
                
                # Simular verificação de saúde
                is_healthy = (
                    self.healthy and 
                    time_since_activity < 300  # 5 minutos
                )
                
                if is_healthy:
                    return jsonify(status), 200
                else:
                    return jsonify(status), 503
                    
            except Exception as e:
                return jsonify({
                    'status': 'error',
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500
        
        @self.app.route('/status')
        def status_check():
            """Endpoint de status detalhado"""
            return jsonify({
                'service_name': 'Bot LoL V3 Ultra Avançado - Healthcheck',
                'version': '1.0.0',
                'healthy': self.healthy,
                'uptime': (datetime.now() - self.startup_time).total_seconds(),
                'last_activity': self.last_activity.isoformat(),
                'startup_time': self.startup_time.isoformat(),
                'endpoints': ['/health', '/status'],
                'container_ready': True
            })
    
    def update_activity(self):
        """Simula atividade do bot"""
        self.last_activity = datetime.now()
    
    def run(self):
        """Executa o servidor healthcheck"""
        logger.info("🚀 Iniciando Healthcheck Server...")
        
        # Thread para simular atividade
        def simulate_activity():
            while True:
                time.sleep(30)  # Atualizar a cada 30 segundos
                self.update_activity()
                logger.info("📊 Atividade simulada atualizada")
        
        activity_thread = threading.Thread(target=simulate_activity, daemon=True)
        activity_thread.start()
        
        # Rodar Flask
        try:
            logger.info("✅ Healthcheck server rodando na porta 5000")
            self.app.run(host='0.0.0.0', port=5000, debug=False)
        except Exception as e:
            logger.error(f"❌ Erro no healthcheck server: {e}")
            self.healthy = False

def main():
    server = HealthCheckServer()
    server.run()

if __name__ == "__main__":
    print("🩺 HEALTHCHECK SERVER STANDALONE")
    print("Acesse: http://localhost:5000/health")
    print("Status: http://localhost:5000/status")
    main() 