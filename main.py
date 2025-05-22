#!/usr/bin/env python3
"""
Versão ultra-simplificada para testar deploy Railway
Se esta versão não funcionar, o problema é da plataforma
"""

import os
import sys
from flask import Flask

print("🚂 Iniciando bot simples no Railway...")
print(f"🐍 Python version: {sys.version}")
print(f"📁 Working directory: {os.getcwd()}")

app = Flask(__name__)

@app.route('/')
def home():
    return """
    <h1>🤖 Bot LoL - Railway FUNCIONANDO!</h1>
    <p>✅ Deploy realizado com sucesso!</p>
    <p>🚂 Dockerfile funcionou perfeitamente!</p>
    <p>🔥 Nixpacks foi bypassado!</p>
    """

@app.route('/health')
def health():
    return {
        "status": "success", 
        "platform": "railway",
        "method": "dockerfile",
        "message": "Bot está funcionando!"
    }

@app.route('/webhook')
def webhook():
    return "Webhook ativo! Bot funcionando no Railway via Dockerfile!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    
    print(f"🚀 Iniciando servidor Flask na porta {port}")
    print(f"🌐 Acesse: http://localhost:{port}")
    print("🎯 Se você está vendo isto, o deploy funcionou!")
    
    try:
        app.run(host="0.0.0.0", port=port, debug=False)
    except Exception as e:
        print(f"❌ ERRO: {e}")
        sys.exit(1) 