#!/usr/bin/env python3
"""
Teste dos comandos de grupo - Bot LoL V3 Ultra Avançado
"""
import asyncio
import sys
import os

# Adiciona o diretório do projeto ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot.telegram_bot.alerts_system import TelegramAlertsSystem, TelegramGroup, SubscriptionType
from bot.data_models.tip_data import ProfessionalTip

async def test_group_functionality():
    """Testa funcionalidades de grupo"""
    print("🧪 Testando funcionalidades de grupo...")
    
    # Simula dados do sistema
    BOT_TOKEN = "7584060058:AAFux8K9JiQUpH27Mg_mlYJEYLL1J8THXY0"
    
    try:
        # Inicializa sistema de alertas
        alerts_system = TelegramAlertsSystem(BOT_TOKEN)
        
        # Simula um grupo registrado
        test_group = TelegramGroup(
            group_id=-1001234567890,
            title="Grupo Teste LoL Tips",
            subscription_type=SubscriptionType.HIGH_VALUE,
            activated_by=123456789
        )
        
        alerts_system.groups[-1001234567890] = test_group
        
        print("✅ Sistema de alertas inicializado")
        print(f"📋 Grupo de teste criado: {test_group.title}")
        
        # Testa filtro de grupos elegíveis
        mock_tip = ProfessionalTip(
            match_id="test_match_1",
            team_name="T1",
            opposing_team="GenG",
            league="LCK",
            prediction_type="moneyline",
            odds=2.15,
            confidence=0.75,
            expected_value=0.12,  # 12% - qualifica para HIGH_VALUE
            units=2.5,
            reasoning="Teste de tip para grupo",
            data_quality_score=0.85,
            timestamp=1234567890
        )
        
        eligible_groups = alerts_system._get_eligible_groups_for_tip(mock_tip)
        print(f"🎯 Grupos elegíveis para tip: {len(eligible_groups)}")
        
        if eligible_groups:
            print("✅ Filtro de grupos funcionando!")
            for group_id in eligible_groups:
                group = alerts_system.groups[group_id]
                print(f"  📋 {group.title} - {group.subscription_type.value}")
        else:
            print("⚠️ Nenhum grupo elegível (normal se não há grupos ativos)")
        
        # Testa estatísticas
        stats = alerts_system.get_system_stats()
        print(f"\n📊 Estatísticas:")
        print(f"  👥 Usuários: {stats['users']['total']} total, {stats['users']['active']} ativos")
        print(f"  👥 Grupos: {stats['groups']['total']} total, {stats['groups']['active']} ativos")
        
        print(f"\n🔔 Subscrições por tipo:")
        for sub_type, counts in stats['combined_subscriptions'].items():
            print(f"  • {sub_type}: {counts['users']} usuários + {counts['groups']} grupos = {counts['total']} total")
        
        print("\n✅ Teste de grupos concluído com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()

def print_group_commands_help():
    """Imprime ajuda dos comandos de grupo"""
    print("""
📋 COMANDOS DE GRUPO IMPLEMENTADOS:

👥 /activate_group
   • Ativa alertas de tips no grupo atual
   • Apenas administradores podem usar
   • Mostra opções de subscrição (Todas, Alto Valor, Alta Confiança, Premium)

📊 /group_status  
   • Exibe status e estatísticas do grupo
   • Mostra tipo de subscrição ativa
   • Histórico de tips recebidas
   • Data de ativação e configurações

❌ /deactivate_group
   • Desativa alertas no grupo
   • Apenas administradores podem usar
   • Grupo para de receber tips automáticas

🔧 FUNCIONALIDADES:
   • Verificação automática de permissões de admin
   • Suporte a grupos e supergrupos
   • Filtros por tipo de subscrição
   • Tratamento de erros (bot removido, etc.)
   • Estatísticas separadas por usuários e grupos
   • Rate limiting e anti-spam

⚡ COMO USAR:
   1. Adicione o bot ao seu grupo
   2. Dê permissões de admin ao bot
   3. Admin do grupo usa /activate_group
   4. Escolhe tipo de subscrição
   5. Grupo começa a receber tips!
""")

async def main():
    """Função principal"""
    print("🚀 Bot LoL V3 Ultra Avançado - Teste de Grupos")
    print("=" * 50)
    
    print_group_commands_help()
    
    await test_group_functionality()
    
    print("\n" + "=" * 50)
    print("🎉 Funcionalidades de grupo prontas para uso!")

if __name__ == "__main__":
    asyncio.run(main()) 
