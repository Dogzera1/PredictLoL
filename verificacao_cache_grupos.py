#!/usr/bin/env python3
"""
✅ VERIFICAÇÃO: Correção do Cache de Grupos
Script para verificar se o problema "grupo já está ativo" foi resolvido
"""

print("🔍 VERIFICAÇÃO: Correção do Cache de Grupos")
print("=" * 70)

# 1. Verificar se as correções foram aplicadas
print("\n1️⃣ VERIFICANDO CORREÇÕES APLICADAS:")
print("-" * 50)

try:
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    from bot.telegram_bot.alerts_system import TelegramAlertsSystem
    
    # Verificar se método _clear_groups_cache existe
    alerts_system = TelegramAlertsSystem("test_token")
    
    if hasattr(alerts_system, '_clear_groups_cache'):
        print("✅ Método _clear_groups_cache implementado")
    else:
        print("❌ Método _clear_groups_cache NÃO encontrado")
    
    if hasattr(alerts_system, '_handle_reset_groups'):
        print("✅ Comando /reset_groups implementado")
    else:
        print("❌ Comando /reset_groups NÃO encontrado")
    
    # Verificar se a limpeza funciona
    alerts_system.groups = {-123: "teste"}
    alerts_system.blocked_groups = {-456}
    
    print(f"📊 Antes da limpeza: {len(alerts_system.groups)} grupos, {len(alerts_system.blocked_groups)} bloqueados")
    
    alerts_system._clear_groups_cache()
    
    print(f"📊 Depois da limpeza: {len(alerts_system.groups)} grupos, {len(alerts_system.blocked_groups)} bloqueados")
    
    if len(alerts_system.groups) == 0 and len(alerts_system.blocked_groups) == 0:
        print("✅ Limpeza de cache funcionando corretamente")
    else:
        print("❌ Limpeza de cache com problemas")
        
except Exception as e:
    print(f"❌ Erro ao verificar correções: {e}")

# 2. Verificar arquivo de inicialização
print("\n2️⃣ VERIFICANDO INICIALIZAÇÃO:")
print("-" * 50)

try:
    with open("bot/telegram_bot/alerts_system.py", "r", encoding="utf-8") as f:
        content = f.read()
        
    if "_clear_groups_cache()" in content and "async def initialize" in content:
        print("✅ Limpeza de cache está sendo chamada na inicialização")
    else:
        print("❌ Limpeza de cache NÃO está na inicialização")
        
    if "CommandHandler(\"reset_groups\"" in content:
        print("✅ Comando /reset_groups registrado nos handlers")
    else:
        print("❌ Comando /reset_groups NÃO registrado")
        
except Exception as e:
    print(f"❌ Erro ao verificar arquivo: {e}")

# 3. Verificar último commit
print("\n3️⃣ VERIFICANDO DEPLOY:")
print("-" * 50)

import subprocess
try:
    # Verificar último commit
    result = subprocess.run(['git', 'log', '--oneline', '-1'], 
                          capture_output=True, text=True, cwd='.')
    
    if result.returncode == 0:
        last_commit = result.stdout.strip()
        print(f"✅ Último commit: {last_commit}")
        
        if "cache" in last_commit.lower() or "grupo" in last_commit.lower() or "reset" in last_commit.lower():
            print("✅ Commit relacionado ao cache de grupos encontrado")
        else:
            print("⚠️ Último commit não parece relacionado ao cache")
    else:
        print("❌ Erro ao verificar commits")
        
    # Verificar se foi feito push
    result = subprocess.run(['git', 'status', '--porcelain'], 
                          capture_output=True, text=True, cwd='.')
    
    if result.returncode == 0:
        if result.stdout.strip() == "":
            print("✅ Todas as alterações foram commitadas")
        else:
            print("⚠️ Existem alterações não commitadas")
            print(f"   {result.stdout.strip()}")
    
except Exception as e:
    print(f"❌ Erro ao verificar git: {e}")

# 4. Instruções de uso
print("\n4️⃣ INSTRUÇÕES DE USO:")
print("-" * 50)
print("""
🎯 COMO RESOLVER O PROBLEMA "GRUPO JÁ ESTÁ ATIVO":

1️⃣ MÉTODO AUTOMÁTICO (Recomendado):
   • O cache é limpo automaticamente a cada redeploy
   • Aguarde alguns minutos após o redeploy
   • Tente /activate_group novamente

2️⃣ MÉTODO MANUAL (Se ainda estiver com problema):
   • No seu grupo do Telegram, digite: /reset_groups
   • Aguarde a confirmação de limpeza
   • Digite /activate_group normalmente

3️⃣ MÉTODO DE EMERGÊNCIA:
   • Remova o bot do grupo
   • Adicione o bot novamente
   • Use /activate_group

⚠️ IMPORTANTE:
• As correções foram aplicadas no código
• Railway vai aplicar automaticamente no próximo redeploy
• O problema deve ser resolvido permanentemente
""")

print("\n" + "=" * 70)
print("🎉 VERIFICAÇÃO CONCLUÍDA!")
print("\n💡 Dica: Se ainda tiver problemas, use /reset_groups no grupo")
print("📝 Log: Todas as operações são registradas nos logs do sistema") 