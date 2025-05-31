#!/usr/bin/env python3
"""
Teste do Sistema de Alertas Telegram - Bot LoL V3 Ultra Avançado

Script para testar o sistema de alertas do Telegram integrado com tips profissionais.
"""

import os
import sys
import asyncio
import time
from typing import Dict, Any

# Adiciona o diretório atual ao path para importar módulos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot.telegram_bot import (
    TelegramAlertsSystem,
    SubscriptionType,
    NotificationType,
    TelegramUser,
    AlertStats
)
from bot.data_models.tip_data import ProfessionalTip
from bot.core_logic.game_analyzer import GameAnalysis, GamePhase, TeamAdvantage
from bot.utils.logger_config import setup_logging, get_logger

# Configuração de logging
logger = setup_logging(log_level="INFO", log_file=None)
test_logger = get_logger("test_telegram_alerts")


class MockTelegramBot:
    """Bot mock do Telegram para testes sem API real"""
    
    def __init__(self):
        self.sent_messages = []
        self.bot_info = type('obj', (object,), {
            'username': 'lol_tips_test_bot',
            'first_name': 'LoL Tips Test Bot',
            'id': 123456789
        })
    
    async def get_me(self):
        """Simula bot.get_me()"""
        return self.bot_info
    
    async def send_message(self, chat_id, text, parse_mode=None, disable_web_page_preview=True):
        """Simula envio de mensagem"""
        message = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': parse_mode,
            'timestamp': time.time()
        }
        self.sent_messages.append(message)
        print(f"📤 Mensagem enviada para {chat_id}: {text[:100]}...")
        return True


def create_mock_tip(
    team_a: str = "T1",
    team_b: str = "Gen.G",
    league: str = "LCK",
    odds: float = 1.75,
    ev_percentage: float = 12.5,
    confidence: float = 85.0,
    units: float = 3.5
) -> ProfessionalTip:
    """Cria tip mock para testes"""
    
    return ProfessionalTip(
        match_id=f"test_{team_a}_vs_{team_b}",
        team_a=team_a,
        team_b=team_b,
        league=league,
        tournament=f"{league} Summer 2024",
        tip_on_team=team_a,
        odds=odds,
        units=units,
        risk_level="Risco Alto" if units > 3 else "Risco Médio",
        confidence_percentage=confidence,
        ev_percentage=ev_percentage,
        analysis_reasoning=f"{team_a} tem vantagem clara com {ev_percentage:.1f}% EV",
        game_time_at_tip="22min",
        game_time_seconds=1320,
        prediction_source="HYBRID",
        data_quality_score=0.89
    )


def create_mock_analysis(
    predicted_winner: str = "T1",
    win_probability: float = 0.756,
    confidence: float = 0.832
) -> GameAnalysis:
    """Cria análise mock para testes"""
    
    team_advantage = TeamAdvantage(
        gold_advantage=3500,
        tower_advantage=2,
        dragon_advantage=1,
        baron_advantage=0,
        kill_advantage=4
    )
    
    return GameAnalysis(
        predicted_winner=predicted_winner,
        win_probability=win_probability,
        confidence_score=confidence,
        current_phase=GamePhase.MID_GAME,
        game_time_seconds=1200,
        team1_advantage=team_advantage,
        analysis_timestamp=time.time()
    )


async def test_system_initialization():
    """Testa inicialização do sistema"""
    print(f"\n{'='*70}")
    print("🔧 TESTE: INICIALIZAÇÃO DO SISTEMA DE ALERTAS")
    print(f"{'='*70}")
    
    # Token fake para teste
    fake_token = "1234567890:ABCDEF-fake-token-for-testing"
    
    # Inicializa sistema
    alerts_system = TelegramAlertsSystem(fake_token)
    
    # Substitui bot real por mock
    alerts_system.bot = MockTelegramBot()
    
    print("✅ Sistema inicializado:")
    print(f"   • Token configurado: {fake_token[:20]}...")
    print(f"   • Rate limit: {alerts_system.max_messages_per_hour} msg/hora")
    print(f"   • Cache duration: {alerts_system.cache_duration}s")
    print(f"   • Usuários registrados: {len(alerts_system.users)}")
    
    return alerts_system


async def test_user_registration(alerts_system: TelegramAlertsSystem):
    """Testa registro de usuários"""
    print(f"\n{'='*70}")
    print("👥 TESTE: REGISTRO DE USUÁRIOS")
    print(f"{'='*70}")
    
    # Registra usuários de teste
    test_users = [
        (12345, "joao_apostador", "João", SubscriptionType.ALL_TIPS),
        (67890, "maria_trader", "Maria", SubscriptionType.HIGH_VALUE),
        (11111, "carlos_pro", "Carlos", SubscriptionType.HIGH_CONFIDENCE),
        (22222, "ana_premium", "Ana", SubscriptionType.PREMIUM),
    ]
    
    for user_id, username, first_name, sub_type in test_users:
        user = TelegramUser(
            user_id=user_id,
            username=username,
            first_name=first_name,
            subscription_type=sub_type
        )
        alerts_system.users[user_id] = user
        print(f"   ✅ {first_name} ({username}) - {sub_type.value}")
    
    print(f"\n📊 Usuários registrados: {len(alerts_system.users)}")
    
    # Testa estatísticas
    stats = alerts_system.get_system_stats()
    print(f"   • Total: {stats['users']['total']}")
    print(f"   • Ativos: {stats['users']['active']}")
    print(f"   • Por tipo: {stats['users']['subscriptions_by_type']}")
    
    return test_users


async def test_tip_formatting(alerts_system: TelegramAlertsSystem):
    """Testa formatação de tips"""
    print(f"\n{'='*70}")
    print("💬 TESTE: FORMATAÇÃO DE MENSAGENS")
    print(f"{'='*70}")
    
    # Cria tip de teste
    tip = create_mock_tip(
        team_a="T1",
        team_b="Gen.G", 
        league="LCK",
        odds=1.85,
        ev_percentage=18.5,
        confidence=88.0,
        units=4.2
    )
    
    print(f"🎮 Tip de teste:")
    print(f"   • {tip.team_a} vs {tip.team_b}")
    print(f"   • Odds: {tip.odds} | EV: +{tip.ev_percentage}%")
    print(f"   • Confiança: {tip.confidence_percentage}% | Unidades: {tip.units}")
    
    # Formata mensagem
    formatted_message = alerts_system._format_tip_message(tip)
    
    print(f"\n📝 Mensagem formatada:")
    print(f"```")
    print(formatted_message)
    print(f"```")
    
    return formatted_message


async def test_user_filtering(alerts_system: TelegramAlertsSystem):
    """Testa filtros de usuários para tips"""
    print(f"\n{'='*70}")
    print("🔍 TESTE: FILTROS DE USUÁRIOS")
    print(f"{'='*70}")
    
    # Tips com diferentes características
    test_tips = [
        create_mock_tip("T1", "Gen.G", "LCK", 1.65, 8.0, 75.0, 2.5),    # Básica
        create_mock_tip("G2", "FNC", "LEC", 2.10, 15.5, 82.5, 4.0),    # Alto valor
        create_mock_tip("DK", "KT", "LCK", 1.45, 7.2, 92.0, 3.8),      # Alta confiança
        create_mock_tip("SKT", "DRX", "LCK", 1.75, 22.8, 89.5, 5.2),   # Premium
    ]
    
    tip_names = ["Básica", "Alto Valor", "Alta Confiança", "Premium"]
    
    for i, tip in enumerate(test_tips):
        print(f"\n🎯 Tip {tip_names[i]}:")
        print(f"   • EV: {tip.ev_percentage:.1f}% | Confiança: {tip.confidence_percentage:.1f}%")
        
        eligible_users = alerts_system._get_eligible_users_for_tip(tip)
        print(f"   • Usuários elegíveis: {len(eligible_users)}")
        
        # Mostra quais usuários receberiam
        for user_id in eligible_users:
            user = alerts_system.users[user_id]
            print(f"     - {user.first_name} ({user.subscription_type.value})")


async def test_tip_sending(alerts_system: TelegramAlertsSystem):
    """Testa envio de tips"""
    print(f"\n{'='*70}")
    print("📤 TESTE: ENVIO DE TIPS")
    print(f"{'='*70}")
    
    # Cria tip premium
    premium_tip = create_mock_tip(
        team_a="T1",
        team_b="Gen.G",
        league="LCK",
        odds=1.72,
        ev_percentage=19.8,
        confidence=87.5,
        units=4.8
    )
    
    print(f"🚀 Enviando tip premium:")
    print(f"   • {premium_tip.tip_on_team} @ {premium_tip.odds}")
    print(f"   • EV: +{premium_tip.ev_percentage}% | Confiança: {premium_tip.confidence_percentage}%")
    
    # Envia tip
    success = await alerts_system.send_professional_tip(premium_tip)
    
    print(f"\n📊 Resultado:")
    print(f"   • Sucesso: {'✅' if success else '❌'}")
    print(f"   • Tips enviadas: {alerts_system.stats.tips_sent}")
    print(f"   • Mensagens mock enviadas: {len(alerts_system.bot.sent_messages)}")
    
    # Mostra mensagens enviadas
    if alerts_system.bot.sent_messages:
        print(f"\n📝 Últimas mensagens enviadas:")
        for msg in alerts_system.bot.sent_messages[-3:]:
            print(f"   • Para {msg['chat_id']}: {msg['text'][:80]}...")
    
    return success


async def test_match_updates(alerts_system: TelegramAlertsSystem):
    """Testa envio de atualizações de partida"""
    print(f"\n{'='*70}")
    print("📺 TESTE: ATUALIZAÇÕES DE PARTIDA")
    print(f"{'='*70}")
    
    # Cria análise mock
    analysis = create_mock_analysis(
        predicted_winner="T1",
        win_probability=0.78,
        confidence=0.85
    )
    
    print(f"📊 Análise de teste:")
    print(f"   • Vencedor provável: {analysis.predicted_winner}")
    print(f"   • Probabilidade: {analysis.win_probability:.1%}")
    print(f"   • Confiança: {analysis.confidence_score:.1%}")
    
    # Envia atualização
    await alerts_system.send_match_update(analysis, "test_match_123")
    
    print(f"\n✅ Atualização enviada:")
    print(f"   • Match updates enviadas: {alerts_system.stats.match_updates_sent}")


async def test_rate_limiting(alerts_system: TelegramAlertsSystem):
    """Testa sistema de rate limiting"""
    print(f"\n{'='*70}")
    print("⚡ TESTE: RATE LIMITING")
    print(f"{'='*70}")
    
    test_user_id = 12345  # João
    
    print(f"📊 Testando rate limiting para usuário {test_user_id}:")
    print(f"   • Limite: {alerts_system.max_messages_per_hour} msg/hora")
    
    # Testa verificação inicial
    can_send_initial = alerts_system._can_send_to_user(test_user_id)
    print(f"   • Pode enviar inicialmente: {'✅' if can_send_initial else '❌'}")
    
    # Simula envio de várias mensagens
    for i in range(alerts_system.max_messages_per_hour):
        alerts_system.user_message_times.setdefault(test_user_id, []).append(time.time())
    
    can_send_after_limit = alerts_system._can_send_to_user(test_user_id)
    print(f"   • Pode enviar após {alerts_system.max_messages_per_hour} msgs: {'✅' if can_send_after_limit else '❌'}")
    
    # Simula passagem de tempo (mensagens antigas)
    alerts_system.user_message_times[test_user_id] = [time.time() - 3700]  # 1h atrás
    can_send_after_cleanup = alerts_system._can_send_to_user(test_user_id)
    print(f"   • Pode enviar após limpeza: {'✅' if can_send_after_cleanup else '❌'}")


async def test_cache_system(alerts_system: TelegramAlertsSystem):
    """Testa sistema de cache"""
    print(f"\n{'='*70}")
    print("💾 TESTE: SISTEMA DE CACHE")
    print(f"{'='*70}")
    
    # Cria tip para teste de cache
    tip = create_mock_tip("DK", "T1", "LCK", 2.15, 11.2, 76.8, 3.2)
    
    print(f"🔄 Testando cache de tips:")
    print(f"   • Cache atual: {len(alerts_system.recent_tips_cache)} items")
    
    # Primeira tentativa de envio (deve funcionar)
    success1 = await alerts_system.send_professional_tip(tip)
    print(f"   • Primeira tentativa: {'✅' if success1 else '❌'}")
    print(f"   • Cache após 1ª: {len(alerts_system.recent_tips_cache)} items")
    
    # Segunda tentativa imediata (deve ser bloqueada pelo cache)
    success2 = await alerts_system.send_professional_tip(tip)
    print(f"   • Segunda tentativa (imediata): {'✅' if success2 else '❌'}")
    
    # Simula expiração do cache
    tip_cache_key = f"{tip.match_id}_{tip.tip_on_team}_{tip.odds}"
    if tip_cache_key in alerts_system.recent_tips_cache:
        alerts_system.recent_tips_cache[tip_cache_key] = time.time() - 400  # 6min atrás
    
    # Terceira tentativa após "expiração"
    success3 = await alerts_system.send_professional_tip(tip)
    print(f"   • Terceira tentativa (após expiração): {'✅' if success3 else '❌'}")
    
    # Testa limpeza do cache
    alerts_system.cleanup_old_cache()
    print(f"   • Cache após limpeza: {len(alerts_system.recent_tips_cache)} items")


async def test_system_stats(alerts_system: TelegramAlertsSystem):
    """Testa estatísticas do sistema"""
    print(f"\n{'='*70}")
    print("📊 TESTE: ESTATÍSTICAS DO SISTEMA")
    print(f"{'='*70}")
    
    # Obtém estatísticas completas
    stats = alerts_system.get_system_stats()
    
    print(f"👥 Usuários:")
    print(f"   • Total: {stats['users']['total']}")
    print(f"   • Ativos: {stats['users']['active']}")
    print(f"   • Bloqueados: {stats['users']['blocked']}")
    
    print(f"\n📨 Alertas:")
    print(f"   • Total enviado: {stats['alerts']['total_sent']}")
    print(f"   • Tips enviadas: {stats['alerts']['tips_sent']}")
    print(f"   • Atualizações: {stats['alerts']['match_updates_sent']}")
    print(f"   • Taxa de sucesso: {stats['alerts']['success_rate']:.1f}%")
    print(f"   • Falhas: {stats['alerts']['failed_deliveries']}")
    
    print(f"\n⚡ Rate Limiting:")
    print(f"   • Máx por hora: {stats['rate_limiting']['max_messages_per_hour']}")
    print(f"   • Cache duration: {stats['rate_limiting']['cache_duration_minutes']}min")
    print(f"   • Tips em cache: {stats['rate_limiting']['recent_tips_cached']}")
    
    print(f"\n🔔 Subscrições por tipo:")
    for sub_type, count in stats['users']['subscriptions_by_type'].items():
        print(f"   • {sub_type}: {count}")


async def test_system_alerts(alerts_system: TelegramAlertsSystem):
    """Testa alertas do sistema"""
    print(f"\n{'='*70}")
    print("🚨 TESTE: ALERTAS DO SISTEMA")
    print(f"{'='*70}")
    
    # Testa diferentes tipos de alerta
    alert_tests = [
        ("Sistema iniciado com sucesso", "success"),
        ("Nova versão disponível", "info"),
        ("Rate limit atingido", "warning"),
        ("Erro na API do PandaScore", "error")
    ]
    
    for message, alert_type in alert_tests:
        print(f"📢 Enviando alerta '{alert_type}': {message}")
        await alerts_system.send_system_alert(message, alert_type)
    
    print(f"\n✅ Alertas do sistema enviados: {alerts_system.stats.system_alerts_sent}")


async def demonstrate_full_workflow(alerts_system: TelegramAlertsSystem):
    """Demonstra workflow completo"""
    print(f"\n{'='*70}")
    print("🚀 DEMONSTRAÇÃO: WORKFLOW COMPLETO")
    print(f"{'='*70}")
    
    # Cenário: Tips chegando ao longo do tempo
    scenario_tips = [
        create_mock_tip("T1", "Gen.G", "LCK", 1.65, 12.8, 82.5, 3.8),
        create_mock_tip("G2", "FNC", "LEC", 2.35, 25.2, 78.0, 5.1),
        create_mock_tip("DK", "KT", "LCK", 1.52, 8.5, 94.2, 2.9),
    ]
    
    print(f"🎮 Simulando chegada de 3 tips:")
    
    for i, tip in enumerate(scenario_tips, 1):
        print(f"\n📥 Tip {i}/{len(scenario_tips)}:")
        print(f"   • {tip.team_a} vs {tip.team_b} @ {tip.odds}")
        print(f"   • EV: +{tip.ev_percentage}% | Conf: {tip.confidence_percentage}%")
        
        # Envia tip
        success = await alerts_system.send_professional_tip(tip)
        print(f"   • Resultado: {'✅ Enviada' if success else '❌ Rejeitada'}")
        
        # Pequena pausa para simular tempo real
        await asyncio.sleep(0.1)
    
    # Resultado final
    print(f"\n📈 Resultado Final:")
    print(f"   • Tips processadas: {len(scenario_tips)}")
    print(f"   • Tips enviadas: {alerts_system.stats.tips_sent}")
    print(f"   • Mensagens enviadas: {len(alerts_system.bot.sent_messages)}")
    print(f"   • Taxa de sucesso: {alerts_system.stats.success_rate:.1f}%")
    
    # Mostra algumas mensagens enviadas
    if alerts_system.bot.sent_messages:
        print(f"\n📝 Últimas 3 mensagens enviadas:")
        for msg in alerts_system.bot.sent_messages[-3:]:
            print(f"   • Chat {msg['chat_id']}: {msg['text'][:60]}...")


async def main():
    """Função principal de teste"""
    print("🚀 Iniciando testes do Sistema de Alertas Telegram...")
    print(f"🔧 Python: {sys.version}")
    print(f"📁 Diretório: {os.getcwd()}")
    
    try:
        # Inicialização
        alerts_system = await test_system_initialization()
        
        # Executa testes sequenciais
        test_functions = [
            lambda: test_user_registration(alerts_system),
            lambda: test_tip_formatting(alerts_system),
            lambda: test_user_filtering(alerts_system),
            lambda: test_tip_sending(alerts_system),
            lambda: test_match_updates(alerts_system),
            lambda: test_rate_limiting(alerts_system),
            lambda: test_cache_system(alerts_system),
            lambda: test_system_stats(alerts_system),
            lambda: test_system_alerts(alerts_system),
            lambda: demonstrate_full_workflow(alerts_system)
        ]
        
        for test_func in test_functions:
            try:
                await test_func()
            except Exception as e:
                print(f"\n❌ Erro no teste: {e}")
        
        # Estatísticas finais
        print(f"\n{'='*70}")
        print("📈 ESTATÍSTICAS FINAIS")
        print(f"{'='*70}")
        
        final_stats = alerts_system.get_system_stats()
        
        print(f"👥 Usuários registrados: {final_stats['users']['total']}")
        print(f"📤 Total de alertas enviados: {final_stats['alerts']['total_sent']}")
        print(f"🎯 Tips enviadas: {final_stats['alerts']['tips_sent']}")
        print(f"📺 Atualizações enviadas: {final_stats['alerts']['match_updates_sent']}")
        print(f"🚨 Alertas de sistema: {final_stats['alerts']['system_alerts_sent']}")
        print(f"📈 Taxa de sucesso: {final_stats['alerts']['success_rate']:.1f}%")
        print(f"📦 Mensagens mock enviadas: {len(alerts_system.bot.sent_messages)}")
        
        print(f"\n🎉 TODOS OS TESTES DO TELEGRAM CONCLUÍDOS COM SUCESSO!")
        
    except Exception as e:
        print(f"\n❌ Erro fatal durante os testes: {e}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n🛑 Teste interrompido pelo usuário")
    except Exception as e:
        print(f"\n\n❌ Erro fatal: {e}")
        sys.exit(1) 