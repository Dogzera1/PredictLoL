#!/usr/bin/env python3
"""
Script para parar TODAS as instâncias do bot LoL V3
Use antes de fazer deploy ou quando houver conflitos
"""

import os
import sys
import psutil
import subprocess
import time

def stop_python_processes():
    """Para todos os processos Python relacionados ao bot"""
    print("🛑 Parando processos Python...")
    
    killed_processes = []
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            # Verifica se é um processo Python
            if proc.info['name'] and 'python' in proc.info['name'].lower():
                cmdline = proc.info['cmdline']
                if cmdline:
                    cmdline_str = ' '.join(cmdline)
                    
                    # Verifica se está rodando main.py ou bot relacionado
                    if any(keyword in cmdline_str.lower() for keyword in [
                        'main.py', 'bot', 'telegram', 'lol', 'predictlol'
                    ]):
                        print(f"   🎯 Matando processo: PID {proc.info['pid']} - {cmdline_str[:100]}...")
                        proc.terminate()
                        killed_processes.append(proc.info['pid'])
                        
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    # Aguarda término gracioso
    time.sleep(2)
    
    # Força término se necessário
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if proc.info['pid'] in killed_processes:
                if proc.is_running():
                    proc.kill()
                    print(f"   💀 Força término: PID {proc.info['pid']}")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    return len(killed_processes)

def stop_ports():
    """Para processos usando portas do bot"""
    print("\n🔌 Verificando portas...")
    
    ports_to_check = [8080, 5000, 3000, 8000]
    
    for port in ports_to_check:
        try:
            # Windows
            if os.name == 'nt':
                result = subprocess.run(
                    ['netstat', '-ano'], 
                    capture_output=True, 
                    text=True
                )
                
                for line in result.stdout.split('\n'):
                    if f':{port}' in line and 'LISTENING' in line:
                        parts = line.split()
                        if len(parts) >= 5:
                            pid = parts[-1]
                            print(f"   🎯 Porta {port} usada por PID {pid}")
                            try:
                                subprocess.run(['taskkill', '/F', '/PID', pid])
                                print(f"   ✅ Processo PID {pid} terminado")
                            except:
                                print(f"   ❌ Erro ao terminar PID {pid}")
            
        except Exception as e:
            print(f"   ⚠️  Erro verificando porta {port}: {e}")

def main():
    """Função principal"""
    print("🛑 PARANDO TODAS AS INSTÂNCIAS DO BOT LoL V3")
    print("=" * 50)
    
    # Para processos Python
    killed = stop_python_processes()
    
    # Para processos em portas específicas
    stop_ports()
    
    print(f"\n✅ CONCLUÍDO!")
    print(f"   📊 Processos terminados: {killed}")
    print(f"   🎯 Todas as instâncias locais foram paradas")
    print(f"\n💡 Agora você pode:")
    print(f"   1. Fazer deploy no Railway sem conflitos")
    print(f"   2. Rodar apenas uma instância local se necessário")
    print(f"   3. Verificar se o bot Railway está funcionando")

if __name__ == "__main__":
    main()
