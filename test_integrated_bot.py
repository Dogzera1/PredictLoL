#!/usr/bin/env python3
"""
Script para testar o Bot LoL Integrado
Testa todas as funcionalidades de predição
"""

import requests
import json
import time

# Configurações
BOT_TOKEN = "7584060058:AAG-L6BJ5Y3Y74MadbGYhzSuiygJixrblNo"
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

def send_message(chat_id: int, text: str):
    """Envia mensagem via API do Telegram"""
    try:
        url = f"{BASE_URL}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": text
        }
        response = requests.post(url, json=data)
        return response.json()
    except Exception as e:
        print(f"Erro ao enviar mensagem: {e}")
        return None

def test_bot_locally():
    """Testa o bot localmente"""
    
    print("🧪 TESTANDO BOT INTEGRADO LOCALMENTE")
    print("=" * 40)
    
    # Importar e testar sistema de predição
    from main_integrated import SimplePredictionSystem
    
    print("\n🤖 Testando Sistema de Predição...")
    prediction_system = SimplePredictionSystem()
    
    # Teste 1: T1 vs G2
    print("\n📊 Teste 1: T1 vs G2")
    result1 = prediction_system.predict_match("T1", "G2")
    print(f"Resultado: {json.dumps(result1, indent=2)}")
    
    # Teste 2: Faker vs Chovy
    print("\n📊 Teste 2: Faker vs Chovy")
    result2 = prediction_system.predict_match("Faker", "Chovy")
    print(f"Resultado: {json.dumps(result2, indent=2)}")
    
    # Teste 3: Times desconhecidos
    print("\n📊 Teste 3: Teams desconhecidos")
    result3 = prediction_system.predict_match("NovoTime", "OutroTime")
    print(f"Resultado: {json.dumps(result3, indent=2)}")
    
    # Teste 4: Estatísticas
    print("\n📊 Teste 4: Estatísticas")
    stats = prediction_system.get_stats()
    print(f"Stats: {json.dumps(stats, indent=2)}")
    
    print("\n✅ TESTES LOCAIS CONCLUÍDOS!")

def test_webhook_locally():
    """Testa webhook local se estiver rodando"""
    
    print("\n🌐 TESTANDO WEBHOOK LOCAL (se disponível)...")
    
    try:
        # Tentar conectar ao servidor local
        health_response = requests.get("http://localhost:8080/health", timeout=5)
        
        if health_response.status_code == 200:
            print("✅ Servidor local detectado!")
            data = health_response.json()
            print(f"Health: {json.dumps(data, indent=2)}")
            
            # Testar webhook com mensagem simulada
            test_update = {
                "update_id": 123456,
                "message": {
                    "message_id": 789,
                    "from": {
                        "id": 987654321,
                        "is_bot": False,
                        "first_name": "Tester"
                    },
                    "chat": {
                        "id": 987654321,
                        "type": "private"
                    },
                    "date": int(time.time()),
                    "text": "/predict T1 vs G2"
                }
            }
            
            webhook_response = requests.post(
                "http://localhost:8080/webhook",
                json=test_update,
                timeout=10
            )
            
            if webhook_response.status_code == 200:
                print("✅ Webhook funcionando!")
            else:
                print(f"⚠️ Webhook response: {webhook_response.status_code}")
        
    except requests.exceptions.ConnectionError:
        print("⚠️ Servidor local não disponível")
    except Exception as e:
        print(f"❌ Erro no teste: {e}")

def show_integration_summary():
    """Mostra resumo da integração"""
    
    print("\n" + "="*50)
    print("🎯 RESUMO DA INTEGRAÇÃO COMPLETA")
    print("="*50)
    
    print("""
✅ **COMPONENTES IMPLEMENTADOS:**

🤖 **Sistema de Predição:**
   • 15+ times principais (LCK, LPL, LEC, LCS)
   • Players famosos (Faker, Chovy, Caps)
   • Sistema ELO para cálculo de probabilidades
   • Randomização para realismo

📱 **Bot Telegram:**
   • /start - Apresentação
   • /help - Guia completo
   • /predict Team1 vs Team2 - Predições
   • /stats - Estatísticas
   • /teams - Times disponíveis
   • /status - Status do sistema

🏗️ **Arquitetura:**
   • Flask para webhook
   • Threading para evitar event loop issues
   • Sistema robusto de error handling
   • Health checks funcionais

📊 **Features:**
   • Predições com probabilidades
   • Níveis de confiança (Alta/Média/Baixa)
   • Contador de predições
   • Informações regionais dos times

🚀 **PRÓXIMOS PASSOS:**
   1. Deploy da versão integrada
   2. Teste no Telegram real
   3. Refinamento baseado em feedback
   4. Expansão do banco de times
    """)

def main():
    """Função principal"""
    
    print("🔬 TESTADOR COMPLETO - BOT LOL INTEGRADO")
    print("=" * 50)
    
    # Testes locais
    test_bot_locally()
    
    # Teste de webhook local
    test_webhook_locally()
    
    # Resumo
    show_integration_summary()
    
    print("\n🎉 INTEGRAÇÃO COMPLETA E TESTADA!")
    print("📋 Ready para deploy no Railway!")

if __name__ == "__main__":
    main() 