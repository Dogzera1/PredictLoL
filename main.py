#!/usr/bin/env python3
"""
Versão ultra-simplificada para testar deploy
Com logs detalhados para debug
"""

import os
import sys
from flask import Flask

def main():
    print("🚂 Iniciando aplicação...")
    print(f"🐍 Python version: {sys.version}")
    print(f"📁 Working directory: {os.getcwd()}")
    print(f"🌍 Environment variables:")
    print(f"  PORT = {os.environ.get('PORT', 'NOT SET')}")
    print(f"  PYTHONPATH = {os.environ.get('PYTHONPATH', 'NOT SET')}")
    
    app = Flask(__name__)
    
    @app.route('/')
    def home():
        return """
        <h1>🤖 Bot LoL - FUNCIONANDO!</h1>
        <p>✅ Deploy realizado com sucesso!</p>
        <p>🐳 Dockerfile funcionou perfeitamente!</p>
        <p>🔥 Container started successfully!</p>
        """
    
    @app.route('/health')
    def health():
        return {
            "status": "success", 
            "platform": "container",
            "method": "dockerfile",
            "message": "Bot está funcionando!"
        }
    
    @app.route('/webhook')
    def webhook():
        return "Webhook ativo! Bot funcionando via Dockerfile!"
    
    try:
        port = int(os.environ.get("PORT", 8080))
        print(f"🚀 Iniciando servidor Flask na porta {port}")
        print(f"🌐 Host: 0.0.0.0:{port}")
        print("🎯 Servidor iniciando...")
        
        app.run(
            host="0.0.0.0", 
            port=port, 
            debug=False,
            threaded=True
        )
    except Exception as e:
        print(f"❌ ERRO FATAL: {e}")
        print(f"❌ Tipo do erro: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    print("🟢 main.py executado como script principal")
    main()
else:
    print("🟡 main.py importado como módulo") 