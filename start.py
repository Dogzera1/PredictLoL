#!/usr/bin/env python3
"""
Script de inicialização explícito para Railway
"""
import os
import sys
import subprocess

def main():
    print("🚂 Railway Start Script")
    print(f"🐍 Python: {sys.version}")
    print(f"📁 Working Dir: {os.getcwd()}")
    print(f"🔧 Port: {os.environ.get('PORT', '8080')}")
    
    # Verificar se main.py existe
    if not os.path.exists('main.py'):
        print("❌ main.py não encontrado!")
        sys.exit(1)
    
    print("🚀 Iniciando main.py...")
    
    # Executar main.py
    try:
        subprocess.run([sys.executable, 'main.py'], check=True)
    except Exception as e:
        print(f"❌ Erro ao executar main.py: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 