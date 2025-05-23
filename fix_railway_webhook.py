#!/usr/bin/env python3
"""
Script para corrigir webhook após resolver problemas no Railway
"""

import requests
import time

def clear_pending_updates():
    """Remove updates pendentes"""
    print("🧹 Limpando updates pendentes...")
    
    token = "7584060058:AAG-L6BJ5Y3Y74MadbGYhzSuiygJixrblNo"
    
    try:
        # Usar getUpdates com offset alto para limpar
        response = requests.get(
            f"https://api.telegram.org/bot{token}/getUpdates?offset=-1",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data['ok']:
                print("✅ Updates pendentes limpos!")
                return True
            else:
                print(f"❌ Erro: {data.get('description')}")
                return False
        else:
            print(f"❌ Erro HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def reset_webhook():
    """Remove e redefine o webhook"""
    print("🔄 Resetando webhook...")
    
    token = "7584060058:AAG-L6BJ5Y3Y74MadbGYhzSuiygJixrblNo"
    railway_url = "https://spectacular-wonder-production-4fb2.up.railway.app/webhook"
    
    try:
        # 1. Remover webhook atual
        print("   📤 Removendo webhook atual...")
        delete_response = requests.post(
            f"https://api.telegram.org/bot{token}/deleteWebhook",
            timeout=10
        )
        
        if delete_response.status_code == 200:
            print("   ✅ Webhook removido")
        else:
            print("   ⚠️ Falha ao remover webhook")
        
        # Aguardar um pouco
        time.sleep(2)
        
        # 2. Configurar novo webhook
        print("   📥 Configurando novo webhook...")
        set_response = requests.post(
            f"https://api.telegram.org/bot{token}/setWebhook",
            json={"url": railway_url},
            timeout=10
        )
        
        if set_response.status_code == 200:
            data = set_response.json()
            if data['ok']:
                print(f"   ✅ Webhook configurado: {railway_url}")
                return True
            else:
                print(f"   ❌ Erro: {data.get('description')}")
                return False
        else:
            print(f"   ❌ Erro HTTP {set_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def test_webhook_after_fix():
    """Testa webhook após correção"""
    print("🧪 Testando webhook após correção...")
    
    token = "7584060058:AAG-L6BJ5Y3Y74MadbGYhzSuiygJixrblNo"
    
    try:
        response = requests.get(
            f"https://api.telegram.org/bot{token}/getWebhookInfo",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data['ok']:
                webhook_info = data['result']
                print(f"   📡 URL: {webhook_info.get('url', 'Não configurado')}")
                print(f"   📊 Updates pendentes: {webhook_info.get('pending_update_count', 0)}")
                
                last_error = webhook_info.get('last_error_message')
                if last_error:
                    print(f"   ⚠️ Último erro: {last_error}")
                    return False
                else:
                    print("   ✅ Sem erros!")
                    return True
            else:
                print(f"   ❌ Erro: {data.get('description')}")
                return False
        else:
            print(f"   ❌ Erro HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def test_railway_health():
    """Testa se o Railway está saudável após correção"""
    print("🏥 Testando saúde do Railway...")
    
    railway_url = "https://spectacular-wonder-production-4fb2.up.railway.app"
    
    try:
        response = requests.get(f"{railway_url}/health", timeout=15)
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"   📊 Status: {data.get('status', 'unknown')}")
                print(f"   🤖 Bot: {data.get('bot', 'unknown')}")
                print(f"   🔧 Token: {data.get('token', 'unknown')}")
                
                if data.get('status') == 'healthy' and data.get('bot') == 'active':
                    print("   ✅ Railway está saudável!")
                    return True
                else:
                    print("   ❌ Railway não está saudável")
                    return False
            except:
                print("   ❌ Resposta não é JSON válido")
                return False
        else:
            print(f"   ❌ Erro HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def main():
    print("🛠️ CORREÇÃO DO WEBHOOK RAILWAY")
    print("=" * 50)
    
    print("\n⚠️ ANTES DE CONTINUAR:")
    print("   1. Configure TELEGRAM_TOKEN no Railway dashboard")
    print("   2. Faça redeploy do projeto")
    print("   3. Aguarde alguns minutos")
    print("\n🤔 Já fez isso? (s/n): ", end="")
    
    # Para automação, vamos assumir que sim
    response = "s"  # input().lower()
    
    if response != 's':
        print("\n💡 Faça isso primeiro e execute o script novamente!")
        return False
    
    print("\n🚀 Iniciando correção automática...")
    
    # 1. Testar saúde do Railway primeiro
    if not test_railway_health():
        print("\n❌ Railway ainda não está saudável!")
        print("💡 Aguarde mais alguns minutos e tente novamente")
        return False
    
    # 2. Limpar updates pendentes
    if not clear_pending_updates():
        print("\n❌ Falha ao limpar updates pendentes")
        # Não é crítico, pode continuar
    
    # 3. Resetar webhook
    if not reset_webhook():
        print("\n❌ Falha ao resetar webhook")
        return False
    
    # 4. Aguardar e testar
    print("\n⏳ Aguardando 5 segundos...")
    time.sleep(5)
    
    if test_webhook_after_fix():
        print("\n🎉 WEBHOOK CORRIGIDO COM SUCESSO!")
        print("✅ O bot deveria estar funcionando agora")
        print("💡 Teste enviando /start no @BETLOLGPT_bot")
        return True
    else:
        print("\n❌ Ainda há problemas com o webhook")
        print("💡 Verifique os logs do Railway")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 