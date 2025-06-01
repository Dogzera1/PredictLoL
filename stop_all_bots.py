#!/usr/bin/env python3
"""
Script para parar TODAS as instâncias do bot e limpar conflitos
"""
import subprocess
import asyncio
import aiohttp
import time
import sys
import os
import signal

BOT_TOKEN = "7584060058:AAFTZcmirun47zLiCCm48Trre6c3oXnM-Cg"

def kill_all_python_processes():
    """Mata todos os processos Python relacionados ao bot"""
    print("🔪 Parando TODOS os processos Python...")
    
    try:
        import psutil
        print("📋 Usando psutil para finalizar processos...")
        
        killed_count = 0
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                # Verifica se é processo Python
                if proc.info['name'] and 'python' in proc.info['name'].lower():
                    # Verifica se está executando scripts relacionados ao bot
                    cmdline = proc.info['cmdline'] or []
                    cmdline_str = ' '.join(cmdline).lower()
                    
                    # Lista de termos que indicam processos do bot
                    bot_terms = ['main.py', 'bot_interface', 'telegram', 'lol', 'schedule']
                    
                    if any(term in cmdline_str for term in bot_terms):
                        print(f"  🎯 Finalizando processo bot: PID {proc.info['pid']}")
                        proc.terminate()
                        killed_count += 1
                    elif 'python' in cmdline_str and len(cmdline) > 1:
                        # Se for python genérico mas tem argumentos, também finaliza
                        print(f"  ⚠️ Finalizando processo Python: PID {proc.info['pid']}")
                        proc.terminate()
                        killed_count += 1
                        
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        # Aguarda finalização
        if killed_count > 0:
            print(f"⏳ Aguardando finalização de {killed_count} processos...")
            time.sleep(3)
            
            # Força kill se ainda estiverem rodando
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if proc.info['name'] and 'python' in proc.info['name'].lower():
                        print(f"  💀 Forçando kill: PID {proc.info['pid']}")
                        proc.kill()
                except:
                    continue
        
        print(f"✅ {killed_count} processos Python finalizados")
        
    except ImportError:
        # Fallback para comandos do sistema se psutil não disponível
        print("⚠️ psutil não disponível, usando comandos do sistema...")
        
        # Windows
        commands = [
            ["taskkill", "/F", "/T", "/FI", "IMAGENAME eq python.exe"],
            ["taskkill", "/F", "/T", "/FI", "IMAGENAME eq pythonw.exe"],
            ["taskkill", "/F", "/T", "/FI", "WINDOWTITLE eq *python*"]
        ]
        
        for cmd in commands:
            try:
                result = subprocess.run(cmd, capture_output=True, check=False, timeout=15)
                if result.returncode == 0:
                    print(f"✅ Comando executado: {' '.join(cmd)}")
                elif "not found" not in result.stderr.decode().lower():
                    print(f"⚠️ Comando sem processos: {' '.join(cmd)}")
            except subprocess.TimeoutExpired:
                print(f"⏰ Timeout no comando: {' '.join(cmd)}")
            except Exception as e:
                print(f"❌ Erro no comando {' '.join(cmd)}: {e}")
        
        print("✅ Comandos de finalização executados")
        
    except Exception as e:
        print(f"❌ Erro ao finalizar processos: {e}")

async def force_clear_telegram_conflicts():
    """Força limpeza de conflitos via API do Telegram"""
    print("🧹 Limpando conflitos do Telegram via API...")
    
    base_url = f"https://api.telegram.org/bot{BOT_TOKEN}"
    
    async with aiohttp.ClientSession() as session:
        try:
            # 1. Múltiplas tentativas de getUpdates para "roubar" controle
            print("📡 Fazendo requisições getUpdates para limpar conflitos...")
            for i in range(15):
                try:
                    async with session.post(f"{base_url}/getUpdates", 
                                          json={"timeout": 1, "limit": 100}) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            updates_count = len(data.get('result', []))
                            print(f"  📥 Tentativa {i+1}: {updates_count} updates limpos")
                        else:
                            print(f"  ⚠️ Tentativa {i+1}: Status {resp.status}")
                except Exception as e:
                    print(f"  ❌ Tentativa {i+1}: Erro {e}")
                
                await asyncio.sleep(1)
            
            # 2. deleteWebhook para garantir que não há webhook ativo
            print("🔗 Removendo webhook se existir...")
            try:
                async with session.post(f"{base_url}/deleteWebhook") as resp:
                    if resp.status == 200:
                        print("✅ Webhook removido")
                    else:
                        print(f"⚠️ Status webhook: {resp.status}")
            except Exception as e:
                print(f"❌ Erro ao remover webhook: {e}")
            
            # 3. getMe para verificar se bot está acessível
            print("🤖 Verificando acesso ao bot...")
            try:
                async with session.post(f"{base_url}/getMe") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        bot_info = data.get('result', {})
                        print(f"✅ Bot acessível: @{bot_info.get('username', 'unknown')}")
                    else:
                        print(f"❌ Bot inacessível: Status {resp.status}")
            except Exception as e:
                print(f"❌ Erro ao verificar bot: {e}")
            
            # 4. Aguarda estabilização
            print("⏳ Aguardando estabilização...")
            await asyncio.sleep(5)
            
            print("✅ Limpeza do Telegram concluída")
            
        except Exception as e:
            print(f"❌ Erro na limpeza do Telegram: {e}")

def cleanup_lock_files():
    """Remove arquivos de lock que podem estar impedindo execução"""
    print("🔒 Removendo arquivos de lock...")
    
    lock_patterns = [
        "bot.lock",
        "telegram.lock", 
        ".bot_running",
        "main.pid",
        "bot_interface.pid"
    ]
    
    for pattern in lock_patterns:
        try:
            if os.path.exists(pattern):
                os.remove(pattern)
                print(f"  🗑️ Removido: {pattern}")
        except Exception as e:
            print(f"  ❌ Erro ao remover {pattern}: {e}")

def cleanup_temp_files():
    """Limpa arquivos temporários"""
    print("🧹 Limpando arquivos temporários...")
    
    temp_patterns = [
        "*.pyc",
        "__pycache__",
        ".pytest_cache",
        "*.log"
    ]
    
    try:
        # Remove __pycache__ directories
        import shutil
        for root, dirs, files in os.walk("."):
            for dir_name in dirs:
                if dir_name == "__pycache__":
                    cache_path = os.path.join(root, dir_name)
                    try:
                        shutil.rmtree(cache_path)
                        print(f"  🗑️ Removido: {cache_path}")
                    except Exception as e:
                        print(f"  ❌ Erro ao remover {cache_path}: {e}")
        
        print("✅ Arquivos temporários limpos")
        
    except Exception as e:
        print(f"❌ Erro na limpeza: {e}")

async def main():
    """Função principal de limpeza"""
    print("🚀 STOP ALL BOTS - Limpeza Completa")
    print("=" * 50)
    
    # 1. Para todos os processos Python
    kill_all_python_processes()
    
    # 2. Aguarda um pouco
    print("⏳ Aguardando 3 segundos...")
    time.sleep(3)
    
    # 3. Limpa conflitos do Telegram
    await force_clear_telegram_conflicts()
    
    # 4. Limpa arquivos de lock
    cleanup_lock_files()
    
    # 5. Limpa arquivos temporários
    cleanup_temp_files()
    
    print("\n" + "=" * 50)
    print("✅ LIMPEZA COMPLETA CONCLUÍDA!")
    print("🎯 Agora você pode executar o bot sem conflitos")
    print("💡 Use: python main.py")
    print("=" * 50)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️ Interrompido pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro na execução: {e}")
        sys.exit(1) 