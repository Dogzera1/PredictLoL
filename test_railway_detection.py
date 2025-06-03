#!/usr/bin/env python3
"""
Teste simples para verificar detecção do Railway
"""
import os

def is_running_on_railway() -> bool:
    """Detecta se está executando no Railway com múltiplas verificações"""
    
    # 1. Variáveis específicas do Railway
    railway_vars = [
        "RAILWAY_PROJECT_ID",
        "RAILWAY_SERVICE_ID", 
        "RAILWAY_ENVIRONMENT_ID",
        "RAILWAY_DEPLOYMENT_ID"
    ]
    
    # 2. Verifica se alguma variável Railway está presente
    if any(os.getenv(var) for var in railway_vars):
        return True
    
    # 3. Variável de força manual (fallback)
    if os.getenv("FORCE_RAILWAY_MODE", "").lower() in ["true", "1", "yes"]:
        return True
    
    # 4. Detecção por PORT específica + presença de webhook configs
    port = os.getenv("PORT")
    has_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    
    # Railway tipicamente usa PORT diferente de 8080 + bot token configurado
    if port and port != "8080" and has_bot_token:
        # Se PORT não é 8080 E tem bot token, provavelmente é Railway
        return True
    
    # 5. Detecção por padrão de URL (se a URL contém railway)
    railway_url = os.getenv("RAILWAY_PUBLIC_DOMAIN", "").lower()
    if "railway" in railway_url:
        return True
    
    return False

if __name__ == "__main__":
    print("🔍 Testando detecção do Railway...")
    
    print("\n📋 Variáveis disponíveis:")
    test_vars = [
        "PORT", "TELEGRAM_BOT_TOKEN", "FORCE_RAILWAY_MODE",
        "RAILWAY_PROJECT_ID", "RAILWAY_SERVICE_ID", 
        "RAILWAY_ENVIRONMENT_ID", "RAILWAY_DEPLOYMENT_ID",
        "RAILWAY_PUBLIC_DOMAIN"
    ]
    
    for var in test_vars:
        value = os.getenv(var, "❌ Não definida")
        print(f"  {var}: {value}")
    
    print(f"\n✅ Resultado: is_running_on_railway() = {is_running_on_railway()}")
    
    # Teste com FORCE_RAILWAY_MODE
    print("\n🧪 Testando com FORCE_RAILWAY_MODE=true...")
    os.environ["FORCE_RAILWAY_MODE"] = "true"
    print(f"✅ Com FORCE_RAILWAY_MODE: is_running_on_railway() = {is_running_on_railway()}")
    
    # Teste com PORT + TOKEN
    print("\n🧪 Testando com PORT=5000 + TELEGRAM_BOT_TOKEN...")
    os.environ["PORT"] = "5000"
    os.environ["TELEGRAM_BOT_TOKEN"] = "test_token"
    print(f"✅ Com PORT+TOKEN: is_running_on_railway() = {is_running_on_railway()}") 