#!/usr/bin/env python3
import os
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return """
    <h1>🤖 Bot LoL - Railway</h1>
    <p>✅ Aplicação funcionando!</p>
    <p>🚂 Deploy realizado com sucesso</p>
    """

@app.route('/health')
def health():
    return {"status": "ok", "platform": "railway"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"🚂 Iniciando aplicação simples na porta {port}")
    app.run(host="0.0.0.0", port=port, debug=False) 