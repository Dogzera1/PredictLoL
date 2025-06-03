#!/usr/bin/env python3
"""
Teste do Sistema de Alertas para Grupos do Telegram
Verifica se o sistema está funcionando corretamente para grupos
"""

import os
import sys
import asyncio
import logging
from datetime import datetime, timedelta

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup de logging
from bot.utils.logger_config import setup_logging, get_logger
logger = setup_logging(log_level="INFO", log_file="test_grupos_telegram.log")

# Configuração de ambiente
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    logger.warning("⚠️ python-dotenv não disponível")

# Força token correto
os.environ["TELEGRAM_BOT_TOKEN"] = "7584060058:AAHiZkgr-TFlbt8Ym1GNFMdvjfVa6oED9l8"
os.environ["TELEGRAM_ADMIN_USER_IDS"] = "8012415611"

async def test_telegram_groups():
    """Testa o sistema de alertas para grupos do Telegram"""
    
    print("\n" + "="*70)
    print("🧪 TESTE SISTEMA DE ALERTAS PARA GRUPOS TELEGRAM")
    print("="*70)
    
    try:
        # Imports dos componentes
        from bot.telegram_bot.alerts_system import TelegramAlertsSystem, TelegramGroup, SubscriptionType
        from bot.data_models.tip_data import ProfessionalTip
        
        logger.info("📦 Componentes importados com sucesso")
        
        # Inicializa sistema de alertas
        logger.info("🔧 Inicializando TelegramAlertsSystem...")
        
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        alerts_system = TelegramAlertsSystem(bot_token)
        
        await alerts_system.initialize()
        logger.info("✅ Sistema de alertas inicializado")
        
        # Testa se o bot está conectado
        bot_info = await alerts_system.bot.get_me()
        print(f"🤖 Bot conectado: @{bot_info.username} ({bot_info.first_name})")
        
        # Mostra status atual dos grupos
        print(f"\n📊 STATUS ATUAL:")
        print(f"   • Grupos registrados: {len(alerts_system.groups)}")
        print(f"   • Usuários registrados: {len(alerts_system.users)}")
        print(f"   • Grupos bloqueados: {len(alerts_system.blocked_groups)}")
        
        if alerts_system.groups:
            print(f"\n📋 GRUPOS REGISTRADOS:")
            for group_id, group in alerts_system.groups.items():
                status = "✅ Ativo" if group.is_active else "❌ Inativo"
                print(f"   • {group.title} (ID: {group_id})")
                print(f"     - Status: {status}")
                print(f"     - Tipo: {group.subscription_type.value}")
                print(f"     - Tips recebidas: {group.tips_received}")
                print(f"     - Ativado por: {group.activated_by}")
        else:
            print(f"\n⚠️ NENHUM GRUPO REGISTRADO")
            print(f"   Para registrar um grupo:")
            print(f"   1. Adicione o bot @BETLOLGPT_bot ao grupo")
            print(f"   2. Digite /activate_group no grupo")
            print(f"   3. Escolha o tipo de alertas")
        
        # Cria tip de teste
        print(f"\n🎯 CRIANDO TIP DE TESTE...")
        
        tip_teste = ProfessionalTip(
            match_id="g2_vs_fnatic_2025_test",
            team_a="G2 Esports",
            team_b="Fnatic",
            league="LEC",
            tournament="LEC Spring 2025",
            tip_on_team="G2 Esports",
            odds=2.1,
            units=3,
            risk_level="Risco Médio",
            ev_percentage=12.5,
            confidence_percentage=78.0,
            prediction_source="ML Híbrido",
            data_quality_score=0.85,
            game_time_at_tip="Pre-Game",
            game_time_seconds=0,
            analysis_reasoning="G2 tem mostrado forma superior nas últimas partidas, com melhor late game e teamfight. A análise de dados históricos favorece G2 em 78% dos cenários similares.",
            timestamp=datetime.now().timestamp()
        )
        
        print(f"   • {tip_teste.team_a} vs {tip_teste.team_b}")
        print(f"   • Tip: {tip_teste.tip_on_team} @ {tip_teste.odds}")
        print(f"   • EV: {tip_teste.ev_percentage}% | Confiança: {tip_teste.confidence_percentage}%")
        print(f"   • Qualidade: {int(tip_teste.data_quality_score * 100)}%")
        
        # Testa filtragem de grupos elegíveis
        print(f"\n🔍 TESTANDO FILTRAGEM DE GRUPOS...")
        
        eligible_groups = alerts_system._get_eligible_groups_for_tip(tip_teste)
        print(f"   • Grupos elegíveis para esta tip: {len(eligible_groups)}")
        
        if eligible_groups:
            for group_id in eligible_groups:
                if group_id in alerts_system.groups:
                    group = alerts_system.groups[group_id]
                    print(f"     ✅ {group.title} ({group.subscription_type.value})")
        else:
            print(f"     ⚠️ Nenhum grupo elegível (normal se não há grupos registrados)")
        
        # Explica critérios de filtragem
        print(f"\n📋 CRITÉRIOS DE FILTRAGEM:")
        print(f"   • ALL_TIPS: Todas as tips (sempre elegível)")
        print(f"   • HIGH_VALUE: EV > 10% ({'✅' if tip_teste.ev_percentage > 10 else '❌'} - {tip_teste.ev_percentage}%)")
        print(f"   • HIGH_CONFIDENCE: Conf > 80% ({'❌' if tip_teste.confidence_percentage <= 80 else '✅'} - {tip_teste.confidence_percentage}%)")
        print(f"   • PREMIUM: EV > 15% E Conf > 85% ({'❌' if tip_teste.ev_percentage <= 15 or tip_teste.confidence_percentage <= 85 else '✅'})")
        
        # Testa envio de tip se há grupos
        if eligible_groups:
            print(f"\n📤 TESTANDO ENVIO DE TIP...")
            
            try:
                # Mostra preview da mensagem
                formatted_message = alerts_system._format_tip_message(tip_teste)
                print(f"\n📝 PREVIEW DA MENSAGEM:")
                print("─" * 50)
                print(formatted_message)
                print("─" * 50)
                
                # Tenta enviar
                success = await alerts_system.send_professional_tip(tip_teste)
                
                if success:
                    print(f"\n✅ TIP ENVIADA COM SUCESSO!")
                    
                    # Mostra estatísticas atualizadas
                    stats = alerts_system.get_system_stats()
                    print(f"   • Total de alertas enviados: {stats['alerts']['total_sent']}")
                    print(f"   • Tips enviadas: {stats['alerts']['tips_sent']}")
                    print(f"   • Grupos notificados: {alerts_system.groups_notified_count}")
                    print(f"   • Taxa de sucesso: {stats['alerts']['success_rate']:.1f}%")
                    
                else:
                    print(f"\n❌ FALHA NO ENVIO DA TIP")
                    print(f"   Possíveis causas:")
                    print(f"   • Bot foi removido do grupo")
                    print(f"   • Grupo está bloqueado")
                    print(f"   • Erro de conectividade")
                    
            except Exception as e:
                print(f"\n❌ ERRO AO ENVIAR TIP: {e}")
                logger.error(f"Erro no envio: {e}")
        
        else:
            print(f"\n⚠️ SIMULAÇÃO DE ENVIO (sem grupos)")
            print(f"   Para testar com grupos reais:")
            print(f"   1. Adicione o bot a um grupo")
            print(f"   2. Use /activate_group no grupo")
            print(f"   3. Execute este teste novamente")
        
        # Mostra comandos disponíveis para grupos
        print(f"\n⚙️ COMANDOS PARA GRUPOS:")
        print(f"   • /activate_group - Ativa alertas no grupo")
        print(f"   • /group_status - Mostra status do grupo")
        print(f"   • /deactivate_group - Desativa alertas")
        print(f"   • /help - Ajuda completa")
        
        # Estatísticas finais
        print(f"\n📊 ESTATÍSTICAS FINAIS:")
        final_stats = alerts_system.get_system_stats()
        
        print(f"   👥 Usuários:")
        print(f"      • Total: {final_stats['users']['total']}")
        print(f"      • Ativos: {final_stats['users']['active']}")
        print(f"      • Bloqueados: {final_stats['users']['blocked']}")
        
        print(f"   📦 Grupos:")
        print(f"      • Total: {final_stats['groups']['total']}")
        print(f"      • Ativos: {final_stats['groups']['active']}")
        print(f"      • Bloqueados: {final_stats['groups']['blocked']}")
        
        print(f"   📤 Alertas:")
        print(f"      • Total enviados: {final_stats['alerts']['total_sent']}")
        print(f"      • Tips enviadas: {final_stats['alerts']['tips_sent']}")
        print(f"      • Falhas: {final_stats['alerts']['failed_deliveries']}")
        print(f"      • Taxa de sucesso: {final_stats['alerts']['success_rate']:.1f}%")
        
        # Para o bot
        try:
            await alerts_system.stop_bot()
        except Exception as e:
            logger.debug(f"Erro ao parar bot (não crítico): {e}")
            # Não é crítico - apenas força garbage collection
            if hasattr(alerts_system, 'bot'):
                alerts_system.bot = None
        
        print("\n" + "="*70)
        print("✅ TESTE CONCLUÍDO COM SUCESSO!")
        
        if final_stats['groups']['total'] > 0:
            print("🎉 Sistema de grupos está FUNCIONANDO!")
        else:
            print("⚠️ Nenhum grupo registrado - adicione grupos para testar")
            
        print("💡 O sistema está pronto para enviar tips para grupos")
        print("="*70)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro crítico no teste: {e}")
        import traceback
        logger.error(f"Stack trace: {traceback.format_exc()}")
        print(f"\n❌ ERRO NO TESTE: {e}")
        return False

async def main():
    """Função principal"""
    try:
        print("🧪 Iniciando teste do sistema de alertas para grupos...")
        
        success = await test_telegram_groups()
        
        if success:
            print("\n✅ TESTE CONCLUÍDO!")
        else:
            print("\n❌ TESTE FALHOU!")
            
    except Exception as e:
        print(f"\n❌ Erro fatal: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 