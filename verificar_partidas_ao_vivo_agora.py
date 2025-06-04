#!/usr/bin/env python3
"""
VERIFICAÇÃO DE PARTIDAS AO VIVO - SISTEMA COMPLETO
Verifica se o sistema está funcionando com as partidas que estão acontecendo AGORA
"""
import asyncio
import logging
import os
import sys
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Adicionar path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def verificar_sistema_completo():
    """Verifica o funcionamento completo do sistema com partidas ao vivo"""
    print("🎮 VERIFICAÇÃO DE PARTIDAS AO VIVO - SISTEMA COMPLETO")
    print("=" * 70)
    print(f"🕐 Horário atual: {datetime.now().strftime('%H:%M:%S')}")
    print(f"📅 Data: {datetime.now().strftime('%d/%m/%Y')}")
    print()
    
    try:
        # Importar sistema
        from bot.systems.tips_system import ProfessionalTipsSystem
        from bot.api_clients.pandascore_api_client import PandaScoreAPIClient
        from bot.api_clients.riot_api_client import RiotAPIClient
        from bot.core_logic import DynamicPredictionSystem, LoLGameAnalyzer, ProfessionalUnitsSystem
        from bot.utils.constants import PANDASCORE_API_KEY
        
        print("✅ Módulos importados com sucesso")
        
        # Inicializar componentes
        pandascore_client = PandaScoreAPIClient(PANDASCORE_API_KEY)
        riot_client = RiotAPIClient()
        units_system = ProfessionalUnitsSystem()
        game_analyzer = LoLGameAnalyzer()
        prediction_system = DynamicPredictionSystem(
            game_analyzer=game_analyzer,
            units_system=units_system
        )
        tips_system = ProfessionalTipsSystem(
            pandascore_client=pandascore_client,
            riot_client=riot_client,
            prediction_system=prediction_system
        )
        
        print("✅ Sistema inicializado")
        print()
        
        # 1. VERIFICAR PARTIDAS AO VIVO
        print("🔍 ETAPA 1: VERIFICANDO PARTIDAS AO VIVO")
        print("-" * 50)
        
        # PandaScore
        try:
            partidas_pandas = await pandascore_client.get_lol_live_matches()
            print(f"📊 PandaScore: {len(partidas_pandas)} partidas encontradas")
            for i, match in enumerate(partidas_pandas[:3], 1):
                team1 = match.get('opponents', [{}])[0].get('opponent', {}).get('name', 'Team1')
                team2 = match.get('opponents', [{}])[1].get('opponent', {}).get('name', 'Team2') if len(match.get('opponents', [])) > 1 else 'Team2'
                league = match.get('league', {}).get('name', 'Liga desconhecida')
                status = match.get('status', 'unknown')
                print(f"   {i}. {team1} vs {team2} ({league})")
                print(f"      Status: {status}")
        except Exception as e:
            print(f"❌ PandaScore Error: {e}")
            partidas_pandas = []
        
        # Riot API
        try:
            partidas_riot = await riot_client.get_live_matches()
            print(f"📊 Riot API: {len(partidas_riot)} eventos encontrados")
            for i, match in enumerate(partidas_riot[:3], 1):
                # Extrair dados do formato Riot API
                if isinstance(match, dict):
                    event = match.get('event', {})
                    teams = event.get('match', {}).get('teams', [])
                    team1 = teams[0].get('name', 'Team1') if len(teams) > 0 else 'Team1'
                    team2 = teams[1].get('name', 'Team2') if len(teams) > 1 else 'Team2'
                    league = event.get('league', {}).get('name', 'Liga desconhecida')
                    status = event.get('state', 'unknown')
                    print(f"   {i}. {team1} vs {team2} ({league})")
                    print(f"      Status: {status}")
        except Exception as e:
            print(f"❌ Riot API Error: {e}")
            partidas_riot = []
        
        total_partidas = len(partidas_pandas) + len(partidas_riot)
        print(f"\n🎯 Total de partidas detectadas: {total_partidas}")
        
        if total_partidas == 0:
            print("⚠️ NENHUMA PARTIDA AO VIVO DETECTADA")
            print("   Isso pode significar:")
            print("   - Não há jogos profissionais no momento")
            print("   - APIs estão com problemas")
            print("   - Horário sem partidas das ligas principais")
            return False
        
        print()
        
        # 2. TESTAR GERAÇÃO DE TIP
        print("🎯 ETAPA 2: TESTANDO GERAÇÃO DE TIPS")
        print("-" * 50)
        
        # Forçar scan do sistema
        try:
            print("🔄 Executando scan forçado do sistema...")
            resultado_scan = await tips_system.force_scan()
            
            print(f"📊 Resultado do scan:")
            print(f"   🎮 Partidas encontradas: {resultado_scan.get('matches_found', 0)}")
            print(f"   📋 Partidas analisadas: {resultado_scan.get('matches_analyzed', 0)}")
            print(f"   🎯 Tips geradas: {resultado_scan.get('tips_generated', 0)}")
            print(f"   ❌ Tips rejeitadas: {resultado_scan.get('tips_rejected', 0)}")
            
            # Verificar reasons de rejeição
            if resultado_scan.get('rejection_reasons'):
                print(f"   📝 Motivos de rejeição:")
                for reason in resultado_scan['rejection_reasons'][:5]:
                    print(f"      • {reason}")
            
        except Exception as e:
            print(f"❌ Erro no scan: {e}")
            resultado_scan = {}
        
        # 3. VERIFICAR TIPS RECENTES
        print(f"\n📋 ETAPA 3: VERIFICANDO TIPS GERADAS")
        print("-" * 50)
        
        try:
            tips_recentes = tips_system.get_recent_tips(limit=5)
            
            if tips_recentes:
                print(f"✅ {len(tips_recentes)} tip(s) encontrada(s):")
                
                for i, tip in enumerate(tips_recentes, 1):
                    print(f"\n   🎯 TIP #{i}:")
                    print(f"      🎮 Match: {tip.get('match_info', 'N/A')}")
                    print(f"      🏆 Liga: {tip.get('league', 'N/A')}")
                    print(f"      💡 Recomendação: {tip.get('recommendation', 'N/A')}")
                    print(f"      💰 Odds: {tip.get('odds', 'N/A')}")
                    print(f"      📊 Confiança: {tip.get('confidence', 0):.1f}%")
                    print(f"      💵 Expected Value: +{tip.get('expected_value', 0):.2f}%")
                    print(f"      🎲 Units: {tip.get('units', 'N/A')}")
                    print(f"      ⏰ Timestamp: {tip.get('timestamp', 'N/A')}")
                    
            else:
                print("❌ Nenhuma tip encontrada")
                print("   Possíveis motivos:")
                print("   - Critérios de qualidade muito rigorosos")
                print("   - Partidas não atendem aos requisitos")
                print("   - Sistema ainda não processou as partidas")
                
        except Exception as e:
            print(f"❌ Erro ao verificar tips: {e}")
            tips_recentes = []
        
        # 4. TESTE DE TELEGRAM
        print(f"\n📱 ETAPA 4: TESTANDO SISTEMA TELEGRAM")
        print("-" * 50)
        
        try:
            from bot.telegram_bot.alerts_system import TelegramAlertsSystem
            
            bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
            if bot_token:
                telegram_alerts = TelegramAlertsSystem(bot_token=bot_token)
                print(f"✅ Sistema Telegram inicializado")
                print(f"   Token: {bot_token[:10]}...")
                
                # Teste de envio (se houver tips)
                if tips_recentes:
                    admin_id = os.getenv("TELEGRAM_ADMIN_USER_IDS", "8012415611")
                    
                    mensagem_teste = f"""🧪 **VERIFICAÇÃO SISTEMA - {datetime.now().strftime('%H:%M:%S')}**

🎮 **STATUS ATUAL:**
✅ {total_partidas} partidas ao vivo detectadas
✅ {len(tips_recentes)} tip(s) disponível(is)
✅ Sistema de análise funcionando
✅ APIs operacionais

🔥 **ÚLTIMA TIP GERADA:**
{tips_recentes[0].get('match_info', 'N/A')}
Recomendação: {tips_recentes[0].get('recommendation', 'N/A')}
Odds: {tips_recentes[0].get('odds', 'N/A')} | Units: {tips_recentes[0].get('units', 'N/A')}

🚀 **SISTEMA FUNCIONANDO NORMALMENTE!**"""
                    
                    try:
                        sucesso = await telegram_alerts.send_message_to_user(
                            user_id=int(admin_id),
                            message=mensagem_teste
                        )
                        
                        if sucesso:
                            print(f"   ✅ Mensagem de teste enviada com sucesso!")
                        else:
                            print(f"   ⚠️ Falha no envio - token inválido ou bot bloqueado")
                            
                    except Exception as e:
                        print(f"   ⚠️ Erro no envio: {e}")
                else:
                    print(f"   ℹ️ Sem tips para enviar no momento")
                    
            else:
                print(f"⚠️ TELEGRAM_BOT_TOKEN não configurado")
                print(f"   Configure para receber alertas automáticos")
                
        except Exception as e:
            print(f"❌ Erro no sistema Telegram: {e}")
        
        # 5. ANÁLISE GERAL
        print(f"\n📊 ETAPA 5: ANÁLISE GERAL DO SISTEMA")
        print("-" * 50)
        
        # Calcular status
        partidas_ok = total_partidas > 0
        scan_ok = resultado_scan.get('matches_found', 0) > 0
        tips_ok = len(tips_recentes) > 0
        apis_ok = len(partidas_pandas) > 0 or len(partidas_riot) > 0
        
        print(f"🔍 Detecção de partidas: {'✅' if partidas_ok else '❌'}")
        print(f"🔄 Sistema de scan: {'✅' if scan_ok else '❌'}")
        print(f"🎯 Geração de tips: {'✅' if tips_ok else '⚠️'}")
        print(f"📡 APIs funcionando: {'✅' if apis_ok else '❌'}")
        
        # VEREDICTO FINAL
        print(f"\n" + "=" * 70)
        print(f"🏆 VEREDICTO FINAL")
        print(f"=" * 70)
        
        if partidas_ok and apis_ok:
            if tips_ok:
                print(f"🎉 **SISTEMA 100% OPERACIONAL!**")
                print(f"   ✅ Detectando partidas ao vivo")
                print(f"   ✅ Gerando tips automaticamente")
                print(f"   ✅ Pronto para alertas Telegram")
                print(f"   🚀 Funcionando perfeitamente!")
                status = "PERFEITO"
            else:
                print(f"⚠️ **SISTEMA OPERACIONAL - AGUARDANDO TIPS**")
                print(f"   ✅ APIs funcionando")
                print(f"   ✅ Partidas sendo detectadas")
                print(f"   ⏳ Aguardando critérios para tips")
                print(f"   💡 Sistema normal - pode não haver tips boas no momento")
                status = "NORMAL"
        else:
            print(f"❌ **SISTEMA COM PROBLEMAS**")
            print(f"   🔧 Necessária correção antes do uso")
            status = "PROBLEMA"
        
        # Informações adicionais
        print(f"\n💡 **INFORMAÇÕES ADICIONAIS:**")
        print(f"   🕐 Verificação realizada: {datetime.now().strftime('%H:%M:%S')}")
        print(f"   🎮 Total de partidas detectadas: {total_partidas}")
        print(f"   🎯 Tips disponíveis: {len(tips_recentes)}")
        print(f"   📊 Status geral: {status}")
        
        return status == "PERFEITO" or status == "NORMAL"
        
    except Exception as e:
        print(f"\n❌ ERRO CRÍTICO: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Função principal"""
    print(f"🎮 INICIANDO VERIFICAÇÃO COMPLETA DO SISTEMA")
    print(f"📅 {datetime.now().strftime('%d/%m/%Y - %H:%M:%S')}")
    print()
    
    resultado = await verificar_sistema_completo()
    
    print(f"\n" + "=" * 70)
    if resultado:
        print(f"🎉 **VERIFICAÇÃO CONCLUÍDA: SISTEMA APROVADO!**")
        print(f"🚀 O bot está funcionando corretamente com as partidas ao vivo")
    else:
        print(f"⚠️ **VERIFICAÇÃO CONCLUÍDA: REQUER ATENÇÃO**")
        print(f"🔧 Verificar questões identificadas")
    
    print(f"\n📋 **PRÓXIMAS AÇÕES RECOMENDADAS:**")
    if resultado:
        print(f"   1. ✅ Continuar monitoramento automático")
        print(f"   2. 📱 Configurar grupos do Telegram se necessário")
        print(f"   3. 📊 Aguardar tips de qualidade aparecerem")
    else:
        print(f"   1. 🔧 Corrigir problemas identificados")
        print(f"   2. 🔄 Executar nova verificação")

if __name__ == "__main__":
    asyncio.run(main()) 
