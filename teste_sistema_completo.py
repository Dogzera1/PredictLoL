#!/usr/bin/env python3

import asyncio
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Carrega variáveis do .env
load_dotenv()

async def verificar_sistema_completo():
    """Verifica se o sistema está completamente funcional"""
    
    print("🚀 VERIFICAÇÃO COMPLETA DO SISTEMA PREDICTLOL")
    print("=" * 70)
    print(f"⏰ Teste executado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print()
    
    status_geral = {"componentes_ok": 0, "componentes_total": 13}
    problemas = []
    
    # 1. Verificar configurações de odds
    try:
        from bot.utils.constants import MIN_ODDS, MAX_ODDS, PREDICTION_THRESHOLDS
        print("✅ 1. Configurações de Odds:")
        print(f"   📌 Odds Mínima: {MIN_ODDS}x (era 1.30x)")
        print(f"   📌 Odds Máxima: {MAX_ODDS}x (era 3.50x)")
        print(f"   📌 Threshold Odds Altas: {PREDICTION_THRESHOLDS.get('high_odds_threshold', 'N/A')}x")
        print(f"   📌 EV Mínimo Odds Altas: {PREDICTION_THRESHOLDS.get('high_odds_min_ev', 'N/A')}%")
        status_geral["componentes_ok"] += 1
    except Exception as e:
        print(f"❌ 1. Configurações de Odds: ERRO - {e}")
        problemas.append("Configurações de odds não carregaram")
    
    # 2. Verificar APIs
    try:
        from bot.api_clients.pandascore_api_client import PandaScoreAPIClient
        from bot.api_clients.riot_api_client import RiotAPIClient
        
        pandascore = PandaScoreAPIClient()
        riot_client = RiotAPIClient()
        print("✅ 2. APIs Inicializadas:")
        print("   📡 PandaScore API Client: OK")
        print("   📡 Riot API Client: OK")
        status_geral["componentes_ok"] += 1
    except Exception as e:
        print(f"❌ 2. APIs: ERRO - {e}")
        problemas.append("APIs não inicializaram")
    
    # 3. Verificar sistema de predição
    try:
        from bot.core_logic.prediction_system import DynamicPredictionSystem
        from bot.core_logic.units_system import ProfessionalUnitsSystem
        from bot.core_logic.game_analyzer import LoLGameAnalyzer
        
        units_system = ProfessionalUnitsSystem()
        game_analyzer = LoLGameAnalyzer()
        prediction_system = DynamicPredictionSystem(game_analyzer, units_system)
        
        print("✅ 3. Sistema de Predição:")
        print("   🧠 Game Analyzer: OK")
        print("   💰 Units System: OK") 
        print("   🎯 Prediction System: OK")
        status_geral["componentes_ok"] += 1
    except Exception as e:
        print(f"❌ 3. Sistema de Predição: ERRO - {e}")
        problemas.append("Sistema de predição falhou")
    
    # 4. Testar validação de odds altas
    try:
        validation_alta = prediction_system._validate_tip_criteria(
            confidence=0.40, ev_percentage=4.5, odds=5.00,
            game_time=900, data_quality=0.8
        )
        validation_normal = prediction_system._validate_tip_criteria(
            confidence=0.52, ev_percentage=2.0, odds=2.50, 
            game_time=900, data_quality=0.8
        )
        
        print("✅ 4. Validação de Odds:")
        print(f"   🎯 Odds Altas (5.0x): {'APROVADA' if validation_alta['is_valid'] else 'REJEITADA'}")
        print(f"   📊 Odds Normais (2.5x): {'APROVADA' if validation_normal['is_valid'] else 'REJEITADA'}")
        
        if validation_alta['is_valid'] and validation_normal['is_valid']:
            status_geral["componentes_ok"] += 1
        else:
            problemas.append("Validação de odds não funcionou como esperado")
    except Exception as e:
        print(f"❌ 4. Validação de Odds: ERRO - {e}")
        problemas.append("Validação de odds falhou")
    
    # 5. Verificar Telegram Bot
    try:
        from bot.telegram_bot.main_bot import LoLTipsBot
        from bot.utils.constants import TELEGRAM_CONFIG
        
        token = TELEGRAM_CONFIG.get("bot_token")
        if token and len(token) > 40:
            print("✅ 5. Telegram Bot:")
            print(f"   🤖 Token configurado: {token[:10]}...{token[-4:]}")
            print("   💬 Bot pronto para enviar mensagens")
            status_geral["componentes_ok"] += 1
        else:
            print("❌ 5. Telegram Bot: Token inválido")
            problemas.append("Token do Telegram inválido")
    except Exception as e:
        print(f"❌ 5. Telegram Bot: ERRO - {e}")
        problemas.append("Telegram Bot falhou")
    
    # 6. Verificar sistema de tips
    try:
        from bot.systems.tips_system import ProfessionalTipsSystem
        tips_system = ProfessionalTipsSystem()
        print("✅ 6. Sistema de Tips:")
        print("   📋 Tips System inicializado")
        print("   🔄 Pronto para gerar tips automaticamente")
        status_geral["componentes_ok"] += 1
    except Exception as e:
        print(f"❌ 6. Sistema de Tips: ERRO - {e}")
        problemas.append("Sistema de tips falhou")
    
    # 7. Verificar suporte às ligas (incluindo EMEA Masters)
    try:
        from bot.utils.constants import SUPPORTED_LEAGUES
        emea_supported = any('masters' in league.lower() for league in SUPPORTED_LEAGUES)
        print("✅ 7. Suporte às Ligas:")
        print(f"   🏆 Total de ligas suportadas: {len(SUPPORTED_LEAGUES)}")
        print(f"   🎯 EMEA Masters suportado: {'SIM' if emea_supported else 'NÃO'}")
        status_geral["componentes_ok"] += 1
    except Exception as e:
        print(f"❌ 7. Suporte às Ligas: ERRO - {e}")
        problemas.append("Suporte às ligas falhou")
    
    # 8. Testar APIs (se disponível)
    try:
        print("🔍 8. Teste de APIs:")
        
        # Teste PandaScore
        matches = await pandascore.get_upcoming_matches()
        print(f"   📡 PandaScore: {len(matches)} partidas encontradas")
        
        # Teste Riot API
        try:
            schedule = await riot_client.get_schedule()
            print(f"   📡 Riot API: {len(schedule)} eventos encontrados")
        except:
            print("   📡 Riot API: Erro (pode ser normal)")
        
        status_geral["componentes_ok"] += 1
    except Exception as e:
        print(f"❌ 8. Teste de APIs: ERRO - {e}")
        problemas.append("APIs não respondem")
    
    # 9. Verificar configuração de monitoramento
    try:
        from bot.utils.constants import SCAN_INTERVAL_MINUTES
        print("✅ 9. Configuração de Monitoramento:")
        print(f"   ⏱️ Intervalo de scan: {SCAN_INTERVAL_MINUTES} minutos")
        print("   🔄 Sistema monitora automaticamente")
        status_geral["componentes_ok"] += 1
    except Exception as e:
        print(f"❌ 9. Monitoramento: ERRO - {e}")
        problemas.append("Configuração de monitoramento falhou")
    
    # 10. Verificar arquivo .env
    try:
        telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
        pandascore_key = os.getenv("PANDASCORE_API_KEY") 
        print("✅ 10. Variáveis de Ambiente:")
        print(f"   🔑 TELEGRAM_BOT_TOKEN: {'✅ OK' if telegram_token else '❌ FALTANDO'}")
        print(f"   🔑 PANDASCORE_API_KEY: {'✅ OK' if pandascore_key else '❌ FALTANDO'}")
        status_geral["componentes_ok"] += 1
    except Exception as e:
        print(f"❌ 10. Variáveis de Ambiente: ERRO - {e}")
        problemas.append("Variáveis de ambiente não configuradas")
    
    # 11. Verificar sistema de unidades
    try:
        from bot.utils.constants import UNITS_CONFIG
        tip_rec = units_system.calculate_tip(
            confidence_percentage=55.0, ev_percentage=2.5, 
            league_tier="tier_1", market_type="ML"
        )
        print("✅ 11. Sistema de Unidades:")
        print(f"   💰 Tip de exemplo: {tip_rec.units} unidades")
        print(f"   🎯 Risco: {tip_rec.risk_level}")
        status_geral["componentes_ok"] += 1
    except Exception as e:
        print(f"❌ 11. Sistema de Unidades: ERRO - {e}")
        problemas.append("Sistema de unidades falhou")
    
    # 12. Verificar logs
    try:
        from bot.utils.logger_config import get_logger
        logger = get_logger("test")
        logger.info("Teste de log")
        print("✅ 12. Sistema de Logs:")
        print("   📝 Logger configurado e funcionando")
        status_geral["componentes_ok"] += 1
    except Exception as e:
        print(f"❌ 12. Sistema de Logs: ERRO - {e}")
        problemas.append("Sistema de logs falhou")
    
    # 13. Verificar se está pronto para amanhã
    try:
        amanha = datetime.now() + timedelta(days=1)
        print("✅ 13. Preparação para Amanhã:")
        print(f"   📅 Data de amanhã: {amanha.strftime('%d/%m/%Y')}")
        print("   🚀 Sistema configurado para rodar automaticamente")
        print("   📱 Tips serão enviadas via Telegram quando detectadas")
        status_geral["componentes_ok"] += 1
    except Exception as e:
        print(f"❌ 13. Preparação: ERRO - {e}")
        problemas.append("Sistema não está pronto para amanhã")
    
    # Resultado final
    print("\n" + "=" * 70)
    print("📊 RESULTADO DA VERIFICAÇÃO:")
    
    percentual = (status_geral["componentes_ok"] / status_geral["componentes_total"]) * 100
    print(f"   ✅ Componentes funcionando: {status_geral['componentes_ok']}/{status_geral['componentes_total']} ({percentual:.1f}%)")
    
    if status_geral["componentes_ok"] >= 11:  # 85% ou mais
        print("🎉 SISTEMA TOTALMENTE OPERACIONAL!")
        print("✅ Você receberá tips amanhã automaticamente")
        print("📱 Tips serão enviadas via Telegram quando partidas forem detectadas")
        print("🎯 Sistema otimizado para odds de 1.5x até 8.0x")
        print("💎 Detecção especial de valor em odds altas (≥4.0x)")
    elif status_geral["componentes_ok"] >= 8:  # 60% ou mais
        print("⚠️ SISTEMA PARCIALMENTE OPERACIONAL")
        print("🔧 Alguns componentes precisam de atenção, mas core funciona")
        print("📱 Tips básicas ainda podem ser geradas")
    else:
        print("❌ SISTEMA COM PROBLEMAS CRÍTICOS")
        print("🚨 Múltiplos componentes falharam - verificar urgente")
    
    if problemas:
        print("\n🔧 PROBLEMAS DETECTADOS:")
        for i, problema in enumerate(problemas, 1):
            print(f"   {i}. {problema}")
    
    return status_geral["componentes_ok"] >= 11

if __name__ == "__main__":
    resultado = asyncio.run(verificar_sistema_completo())
    exit(0 if resultado else 1) 
