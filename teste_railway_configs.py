#!/usr/bin/env python3
"""
Teste das Configurações do Railway
Verifica se as variáveis de ambiente estão sendo usadas corretamente
"""

import os
import sys
import asyncio
from pathlib import Path

# Configuração do path
BOT_DIR = Path(__file__).parent
sys.path.insert(0, str(BOT_DIR))

def teste_variaveis_ambiente():
    """Testa se as variáveis de ambiente estão configuradas"""
    
    print("🔍 TESTE DAS VARIÁVEIS DE AMBIENTE DO RAILWAY")
    print("=" * 60)
    
    # Verificar variáveis principais
    variaveis = {
        "TELEGRAM_BOT_TOKEN": os.getenv("TELEGRAM_BOT_TOKEN", ""),
        "TELEGRAM_ADMIN_USER_IDS": os.getenv("TELEGRAM_ADMIN_USER_IDS", ""),
        "RAILWAY_ENVIRONMENT_ID": os.getenv("RAILWAY_ENVIRONMENT_ID", ""),
        "PORT": os.getenv("PORT", "5000"),
        "FORCE_RAILWAY_MODE": os.getenv("FORCE_RAILWAY_MODE", "false")
    }
    
    print("📋 Variáveis de Ambiente:")
    for nome, valor in variaveis.items():
        if valor:
            if "TOKEN" in nome:
                # Mascarar token por segurança
                valor_display = f"{valor[:10]}...{valor[-10:]}" if len(valor) > 20 else valor[:10] + "..."
            else:
                valor_display = valor
            print(f"   ✅ {nome}: {valor_display}")
        else:
            print(f"   ❌ {nome}: NÃO CONFIGURADA")
    
    return all(variaveis[v] for v in ["TELEGRAM_BOT_TOKEN", "TELEGRAM_ADMIN_USER_IDS"])

def teste_imports():
    """Testa se os imports estão funcionando"""
    
    print("\n📦 TESTE DOS IMPORTS:")
    
    try:
        from bot.utils.constants import TELEGRAM_CONFIG, TELEGRAM_ADMIN_USER_IDS
        print("   ✅ Constants importados com sucesso")
        
        print(f"   📱 Token configurado: {'✅ Sim' if TELEGRAM_CONFIG['bot_token'] else '❌ Não'}")
        print(f"   👥 Admin IDs: {TELEGRAM_ADMIN_USER_IDS}")
        
        return True
    except Exception as e:
        print(f"   ❌ Erro nos imports: {e}")
        return False

async def teste_telegram_basico():
    """Testa se o Telegram pode ser inicializado"""
    
    print("\n📱 TESTE DO TELEGRAM:")
    
    try:
        from bot.telegram_bot.alerts_system import TelegramAlertsSystem
        
        # Pegar token das variáveis
        token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        if not token:
            print("   ❌ Token não configurado")
            return False
            
        # Tentar criar o sistema
        alerts_system = TelegramAlertsSystem(bot_token=token)
        print("   ✅ TelegramAlertsSystem criado com sucesso")
        
        # Tentar inicializar (sem conectar)
        print("   🔄 Testando inicialização...")
        await alerts_system.initialize()
        print("   ✅ Sistema inicializado com sucesso")
        
        # Verificar se o bot pode ser criado
        if alerts_system.bot:
            print("   ✅ Bot do Telegram criado")
            
            # Teste básico de informações do bot
            try:
                bot_info = await alerts_system.bot.get_me()
                print(f"   🤖 Bot: @{bot_info.username}")
                print(f"   👤 Nome: {bot_info.first_name}")
            except Exception as e:
                print(f"   ⚠️ Não foi possível obter info do bot: {e}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erro no teste do Telegram: {e}")
        return False

async def teste_sistema_completo():
    """Testa se o sistema completo pode ser inicializado"""
    
    print("\n🤖 TESTE DO SISTEMA COMPLETO:")
    
    try:
        # Importar componentes principais
        from bot.api_clients.pandascore_api_client import PandaScoreAPIClient
        from bot.api_clients.riot_api_client import RiotAPIClient
        from bot.systems.tips_system import ProfessionalTipsSystem
        from bot.core_logic.prediction_system import DynamicPredictionSystem
        from bot.core_logic.game_analyzer import LoLGameAnalyzer
        from bot.core_logic.units_system import ProfessionalUnitsSystem
        
        print("   ✅ Todos os imports principais funcionando")
        
        # Criar clientes de API
        pandascore = PandaScoreAPIClient()
        riot = RiotAPIClient()
        print("   ✅ Clientes de API criados")
        
        # Criar sistemas de análise
        analyzer = LoLGameAnalyzer()
        units = ProfessionalUnitsSystem()
        prediction = DynamicPredictionSystem(analyzer, units)
        print("   ✅ Sistemas de análise criados")
        
        # Criar sistema de tips
        tips_system = ProfessionalTipsSystem(
            pandascore_client=pandascore,
            riot_client=riot,
            prediction_system=prediction
        )
        print("   ✅ Sistema de Tips criado")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erro no teste do sistema: {e}")
        return False

async def main():
    """Função principal de teste"""
    
    print("🚀 INICIANDO TESTES DAS CONFIGURAÇÕES DO RAILWAY\n")
    
    # 1. Testar variáveis de ambiente
    vars_ok = teste_variaveis_ambiente()
    
    # 2. Testar imports
    imports_ok = teste_imports()
    
    # 3. Testar Telegram básico
    telegram_ok = await teste_telegram_basico()
    
    # 4. Testar sistema completo
    sistema_ok = await teste_sistema_completo()
    
    # Resumo final
    print("\n" + "=" * 60)
    print("📊 RESUMO DOS TESTES")
    print("=" * 60)
    
    testes = [
        ("Variáveis de Ambiente", vars_ok),
        ("Imports", imports_ok),
        ("Telegram", telegram_ok),
        ("Sistema Completo", sistema_ok)
    ]
    
    testes_passou = sum(1 for _, ok in testes if ok)
    total_testes = len(testes)
    
    for nome, ok in testes:
        print(f"   {'✅' if ok else '❌'} {nome}")
    
    print(f"\n🎯 Resultado: {testes_passou}/{total_testes} testes passaram")
    
    if testes_passou == total_testes:
        print("🎉 TODOS OS TESTES PASSARAM!")
        print("✅ Sistema está pronto para funcionar no Railway")
    else:
        print("⚠️ ALGUNS TESTES FALHARAM")
        print("🔧 Verifique as configurações antes do deploy")
    
    print("\n📋 PRÓXIMOS PASSOS:")
    if vars_ok and imports_ok:
        print("1. ✅ Configurações básicas OK")
        print("2. 🚂 Fazer deploy no Railway")
        print("3. 📱 Testar comandos do bot")
        print("4. ⏰ Aguardar jogos profissionais para tips")
    else:
        print("1. ❌ Corrigir configurações faltantes")
        print("2. 🔄 Executar testes novamente")
        print("3. 🚂 Deploy somente após todos os testes passarem")

if __name__ == "__main__":
    # Simular variáveis do Railway localmente para teste
    if not os.getenv("TELEGRAM_BOT_TOKEN"):
        os.environ["TELEGRAM_BOT_TOKEN"] = "8143188638:AAEJVEIo91k7nvkPZH6eGeet5ONnkH5jfzI"
    
    if not os.getenv("TELEGRAM_ADMIN_USER_IDS"):
        os.environ["TELEGRAM_ADMIN_USER_IDS"] = "8012415611"
    
    if not os.getenv("RAILWAY_ENVIRONMENT_ID"):
        os.environ["RAILWAY_ENVIRONMENT_ID"] = "be1cb85b-2d91-4eeb-aede-c22f425ce1ef"
    
    asyncio.run(main()) 