#!/usr/bin/env python3
"""Script para parar todas as instâncias do bot"""

import os
import sys
import tempfile
import subprocess

def stop_all_bots():
    """Para todas as instâncias do bot"""
    print("🛑 Parando todas as instâncias do bot...")
    
    # Parar por processo
    try:
        if os.name == 'nt':  # Windows
            result = subprocess.run(['taskkill', '/F', '/IM', 'python.exe'], 
                                  capture_output=True, text=True)
            print(f"✅ Processos Python finalizados")
        else:  # Unix/Linux
            result = subprocess.run(['pkill', '-f', 'bot_v13_railway'], 
                                  capture_output=True, text=True)
            print(f"✅ Processos do bot finalizados")
    except Exception as e:
        print(f"⚠️ Erro ao finalizar processos: {e}")
    
    # Remover arquivos de lock
    lock_files = [
        'bot_lol_v3.lock',
        'bot_lol_v3_simples.lock'
    ]
    
    for lock_file in lock_files:
        lock_path = os.path.join(tempfile.gettempdir(), lock_file)
        if os.path.exists(lock_path):
            try:
                os.remove(lock_path)
                print(f"🧹 Lock removido: {lock_file}")
            except Exception as e:
                print(f"⚠️ Erro ao remover lock {lock_file}: {e}")
    
    print("✅ Todas as instâncias foram finalizadas!")

if __name__ == "__main__":
    stop_all_bots() 