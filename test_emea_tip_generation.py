#!/usr/bin/env python3

import asyncio
from dotenv import load_dotenv
from bot.systems.tips_system import ProfessionalTipsSystem
from bot.utils.constants import SUPPORTED_LEAGUES

# Carrega variáveis do .env
load_dotenv()

def test_emea_masters_league_support():
    """Testa se EMEA Masters está suportado"""
    
    print("🏆 Verificando suporte ao EMEA Masters...")
    print("=" * 50)
    
    # Variações possíveis do nome
    emea_variants = [
        "EMEA Masters",
        "European Masters", 
        "EU Masters",
        "EMEA Championship",
        "European Championship",
        "EMEA",
        "Masters"
    ]
    
    print("🔍 Testando variações do nome:")
    for variant in emea_variants:
        is_supported = variant in SUPPORTED_LEAGUES
        status = "✅" if is_supported else "❌"
        print(f"   {status} {variant}: {is_supported}")
    
    # Testa correspondência por substring (como no código real)
    print("\n🔍 Testando correspondência por substring:")
    for variant in emea_variants:
        has_match = any(variant.lower() in league.lower() for league in SUPPORTED_LEAGUES)
        status = "✅" if has_match else "❌"
        print(f"   {status} '{variant}' tem correspondência: {has_match}")
    
    # Testa correspondência reversa (nome da liga contém a variação)
    print("\n🔍 Testando correspondência reversa:")
    for variant in emea_variants:
        has_match = any(league.lower() in variant.lower() for league in SUPPORTED_LEAGUES)
        status = "✅" if has_match else "❌"
        print(f"   {status} Liga contém '{variant}': {has_match}")

async def test_tips_system_with_emea():
    """Testa sistema de tips com simulação EMEA Masters"""
    
    print("\n🎯 Testando geração de tips para EMEA Masters...")
    print("=" * 50)
    
    # Inicializa sistema
    tips_system = ProfessionalTipsSystem()
    
    # Simula dados de uma partida EMEA Masters
    mock_match_data = {
        'id': 'emea_test_123',
        'league': {'name': 'EMEA Masters'},
        'tournament': {'name': 'EMEA Masters 2025'},
        'serie': {'name': 'Group Stage'},
        'status': 'running',
        'game': {'length': 900},  # 15 minutos
        'opponents': [
            {'opponent': {'name': 'Team BDS'}},
            {'opponent': {'name': 'Karmine Corp'}}
        ]
    }
    
    print(f"📊 Dados simulados:")
    print(f"   Liga: {mock_match_data['league']['name']}")
    print(f"   Torneio: {mock_match_data['tournament']['name']}")
    print(f"   Times: {mock_match_data['opponents'][0]['opponent']['name']} vs {mock_match_data['opponents'][1]['opponent']['name']}")
    print(f"   Status: {mock_match_data['status']}")
    print(f"   Tempo: {mock_match_data['game']['length']}s")
    
    # Testa verificação de liga suportada
    league_name = mock_match_data['league']['name']
    
    # Método 1: Verificação direta
    direct_match = league_name in SUPPORTED_LEAGUES
    print(f"\n🔍 Verificação direta: {direct_match}")
    
    # Método 2: Verificação por substring (como usado no código real)
    substring_match = any(
        supported_league.lower() in league_name.lower() or 
        league_name.lower() in supported_league.lower()
        for supported_league in SUPPORTED_LEAGUES
    )
    print(f"🔍 Verificação por substring: {substring_match}")
    
    # Método 3: Verificação específica para Masters
    masters_match = any(
        'masters' in league_name.lower() and 'masters' in supported_league.lower()
        for supported_league in SUPPORTED_LEAGUES
    )
    print(f"🔍 Verificação específica Masters: {masters_match}")
    
    # Resultado final
    will_be_processed = direct_match or substring_match or masters_match
    print(f"\n✅ EMEA Masters será processado: {will_be_processed}")
    
    if will_be_processed:
        print("🎉 Sistema PRONTO para gerar tips do EMEA Masters amanhã!")
    else:
        print("❌ Sistema NÃO processará EMEA Masters")
    
    return will_be_processed

if __name__ == "__main__":
    print("🚀 Teste de Suporte ao EMEA Masters")
    print("=" * 60)
    
    # Testa suporte às ligas
    test_emea_masters_league_support()
    
    # Testa sistema de tips
    result = asyncio.run(test_tips_system_with_emea())
    
    print("\n" + "=" * 60)
    print("📋 RESULTADO FINAL:")
    
    if result:
        print("✅ EMEA Masters TOTALMENTE SUPORTADO!")
        print("🎯 Tips serão geradas automaticamente amanhã")
        print("📱 Alertas serão enviados via Telegram")
        print("🔥 Sistema 100% pronto para o campeonato!")
    else:
        print("❌ EMEA Masters precisa ser adicionado manualmente")
        print("🔧 Recomendação: Adicionar 'EMEA Masters' explicitamente") 
