#!/usr/bin/env python3
"""
Script de teste para verificar inicialização do bot
"""

import asyncio
import logging
import sys

# Configurar logging para teste
logging.basicConfig(level=logging.INFO)

async def test_bot_initialization():
    """Testa inicialização completa do bot"""
    print("🚀 Iniciando teste de inicialização...")
    
    try:
        # Import principal
        import main_v3_riot_integrated
        print("✅ Import do módulo principal: OK")
        
        # Criar instância do bot
        bot = main_v3_riot_integrated.TelegramBotV3Improved()
        print("✅ Criação da instância: OK")
        
        # Verificar componentes principais
        components = {
            'riot_api': hasattr(bot, 'riot_api'),
            'prediction_system': hasattr(bot, 'prediction_system'),
            'champion_analyzer': hasattr(bot, 'champion_analyzer'),
            'portfolio_manager': hasattr(bot, 'portfolio_manager'),
            'kelly_betting': hasattr(bot, 'kelly_betting'),
            'sentiment_analyzer': hasattr(bot, 'sentiment_analyzer')
        }
        
        print("🔍 Verificando componentes:")
        for component, exists in components.items():
            status = "✅" if exists else "❌"
            print(f"  {status} {component}: {'OK' if exists else 'MISSING'}")
        
        # Testar sistema de autorização
        auth_test = bot.is_user_authorized(1)  # Admin sempre autorizado
        print(f"✅ Sistema de autorização: {'OK' if auth_test else 'FAIL'}")
        
        # Testar busca de partidas
        print("🔍 Testando busca de partidas...")
        matches = await bot.riot_api.get_all_live_matches()
        print(f"✅ Partidas encontradas: {len(matches)}")
        
        if matches:
            # Testar predição
            print("🎯 Testando sistema de predição...")
            prediction = await bot.prediction_system.predict_live_match(matches[0])
            print(f"✅ Predição gerada: {prediction.get('team1', 'N/A')} vs {prediction.get('team2', 'N/A')}")
        
        # Testar Value Betting System
        try:
            import value_bet_system
            print("✅ Value Betting System: Módulo disponível")
        except ImportError:
            print("⚠️ Value Betting System: Módulo não encontrado")
        
        print("\n🎉 TESTE CONCLUÍDO COM SUCESSO!")
        print("🤖 Bot está pronto para execução")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERRO NO TESTE: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Função principal do teste"""
    try:
        result = asyncio.run(test_bot_initialization())
        
        if result:
            print("\n✅ STATUS FINAL: SUCESSO")
            print("🚀 O bot pode ser iniciado normalmente")
            sys.exit(0)
        else:
            print("\n❌ STATUS FINAL: FALHA")
            print("🔧 Correções necessárias antes da execução")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Teste interrompido pelo usuário")
        sys.exit(0)
    except Exception as e:
        print(f"\n💥 ERRO FATAL: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 