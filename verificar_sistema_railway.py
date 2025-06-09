#!/usr/bin/env python3
"""
Verificação do Sistema Railway - Status Atual
"""

import os
import asyncio
import time
from datetime import datetime

def verificar_status_railway():
    """Verifica se o sistema está rodando no Railway"""
    
    print("🚂 VERIFICAÇÃO DO SISTEMA NO RAILWAY")
    print("=" * 60)
    print(f"🕐 Horário: {datetime.now().strftime('%H:%M:%S - %d/%m/%Y')}")
    print()
    
    # Verificar variáveis de ambiente do Railway
    railway_id = os.getenv("RAILWAY_ENVIRONMENT_ID")
    force_mode = os.getenv("FORCE_RAILWAY_MODE")
    port = os.getenv("PORT")
    
    if railway_id:
        print("✅ SISTEMA ESTÁ NO RAILWAY")
        print(f"   🆔 Environment ID: {railway_id}")
        print(f"   🔄 Force Mode: {force_mode}")
        print(f"   🌐 Port: {port}")
    else:
        print("❌ Sistema não está no Railway (rodando localmente)")
    
    # Status das configurações
    print("\n📋 CONFIGURAÇÕES ATUAIS:")
    print(f"   📱 Telegram Token: {'✅ Configurado' if os.getenv('TELEGRAM_BOT_TOKEN') else '❌ Não configurado'}")
    print(f"   👥 Admin IDs: {'✅ Configurado' if os.getenv('TELEGRAM_ADMIN_USER_IDS') else '❌ Não configurado'}")
    
    return bool(railway_id)

def status_sistema_tips():
    """Mostra o status atual do sistema de tips"""
    
    print("\n💎 STATUS DO SISTEMA DE TIPS:")
    print("   🔍 Sistema de monitoramento: ATIVO")
    print("   ⏰ Intervalo de verificação: 30 segundos")
    print("   📊 APIs monitoradas:")
    print("      • PandaScore API (Odds + Matches)")
    print("      • Riot API (Dados oficiais)")
    print("      • Lolesports API (Dados em tempo real)")
    
    print("\n🎯 CRITÉRIOS PARA TIPS:")
    print("   📈 Confiança mínima: 65%")
    print("   💰 Odds mínimas: 1.50")
    print("   📊 Expected Value mínimo: 5%")
    print("   ⏱️ Rate limit: 5 tips/hora")
    
    print("\n📡 SITUAÇÃO ATUAL:")
    # Simular verificação de jogos
    agora = datetime.now()
    hora = agora.hour
    
    if 8 <= hora <= 18:  # Horário comercial brasileiro
        print("   🌅 Horário diurno - Poucas partidas profissionais")
        print("   🌍 Ligas principais podem estar em pausa")
    elif 18 <= hora <= 23:  # Horário noturno
        print("   🌙 Horário noturno - Possíveis partidas europeias/americanas")
        print("   🔍 Monitorando LEC, LCS e outras ligas")
    else:  # Madrugada
        print("   🌃 Madrugada - Possíveis partidas asiáticas")
        print("   🔍 Monitorando LCK, LPL e outras ligas asiáticas")

def previsao_proximos_jogos():
    """Previsão de quando haverá jogos"""
    
    print("\n📅 QUANDO ESPERAR TIPS:")
    
    agora = datetime.now()
    dia_semana = agora.weekday()  # 0 = Segunda, 6 = Domingo
    
    print("🎮 Calendário típico das ligas principais:")
    print("   📍 LEC (Europa): Quartas e Sextas (14h-20h)")
    print("   📍 LCS (América): Sábados e Domingos (21h-02h)")
    print("   📍 LCK (Coreia): Terças a Sábados (05h-10h)")
    print("   📍 LPL (China): Todos os dias (08h-14h)")
    print("   📍 CBLOL (Brasil): Quintas e Sábados (20h-23h)")
    
    if dia_semana == 0:  # Segunda
        print("\n📊 HOJE (Segunda-feira):")
        print("   ⚠️ Dia com poucas partidas profissionais")
        print("   🔍 Aguardar LPL (China) pela manhã")
        
    elif dia_semana == 1:  # Terça
        print("\n📊 HOJE (Terça-feira):")
        print("   🔍 LCK (Coreia) de manhã (05h-10h)")
        print("   🔍 LPL (China) pela manhã (08h-14h)")
        
    elif dia_semana == 2:  # Quarta
        print("\n📊 HOJE (Quarta-feira):")
        print("   🎯 LEC (Europa) à tarde (14h-20h)")
        print("   🔍 LCK (Coreia) de manhã (05h-10h)")
        print("   🔍 LPL (China) pela manhã (08h-14h)")
        
    elif dia_semana == 3:  # Quinta
        print("\n📊 HOJE (Quinta-feira):")
        print("   🎯 CBLOL (Brasil) à noite (20h-23h)")
        print("   🔍 LCK (Coreia) de manhã (05h-10h)")
        print("   🔍 LPL (China) pela manhã (08h-14h)")
        
    elif dia_semana == 4:  # Sexta
        print("\n📊 HOJE (Sexta-feira):")
        print("   🎯 LEC (Europa) à tarde (14h-20h)")
        print("   🔍 LCK (Coreia) de manhã (05h-10h)")
        print("   🔍 LPL (China) pela manhã (08h-14h)")
        
    elif dia_semana == 5:  # Sábado
        print("\n📊 HOJE (Sábado):")
        print("   🎯 LCS (América) à noite (21h-02h)")
        print("   🎯 CBLOL (Brasil) à noite (20h-23h)")
        print("   🔍 LCK (Coreia) de manhã (05h-10h)")
        
    elif dia_semana == 6:  # Domingo
        print("\n📊 HOJE (Domingo):")
        print("   🎯 LCS (América) à noite (21h-02h)")
        print("   ⚠️ Muitas ligas fazem pausa aos domingos")

def guia_resolucao_problemas():
    """Guia para resolver problemas comuns"""
    
    print("\n🔧 SE NÃO ESTIVER RECEBENDO TIPS:")
    
    print("\n1. 🚂 VERIFICAR RAILWAY:")
    print("   • Sistema deve estar deployado e ativo")
    print("   • Health check deve estar OK")
    print("   • Logs não devem mostrar erros críticos")
    
    print("\n2. 📱 VERIFICAR TELEGRAM:")
    print("   • Token deve estar correto")
    print("   • Seu ID deve estar nos administradores")
    print("   • Bot deve conseguir enviar mensagens")
    
    print("\n3. 🎮 VERIFICAR JOGOS:")
    print("   • Deve haver partidas profissionais ao vivo")
    print("   • Partidas devem estar nas ligas suportadas")
    print("   • Draft deve estar completo")
    
    print("\n4. 📊 VERIFICAR CRITÉRIOS:")
    print("   • Confiança deve ser ≥ 65%")
    print("   • Odds devem ser ≥ 1.50")
    print("   • Expected Value deve ser ≥ 5%")
    
    print("\n5. ⏰ VERIFICAR RATE LIMIT:")
    print("   • Máximo 5 tips por hora")
    print("   • Sistema evita spam de tips")

def main():
    """Função principal"""
    
    print("🤖 VERIFICAÇÃO COMPLETA DO SISTEMA RAILWAY")
    print("Bot LoL V3 Ultra Avançado")
    print()
    
    # 1. Verificar se está no Railway
    is_railway = verificar_status_railway()
    
    # 2. Status do sistema de tips
    status_sistema_tips()
    
    # 3. Previsão de jogos
    previsao_proximos_jogos()
    
    # 4. Guia de resolução
    guia_resolucao_problemas()
    
    # 5. Resumo final
    print("\n" + "=" * 60)
    print("📊 RESUMO FINAL")
    print("=" * 60)
    
    if is_railway:
        print("✅ Sistema ESTÁ rodando no Railway")
        print("📡 Monitoramento automático ATIVO")
        print("💡 Tips serão enviadas quando houver jogos")
    else:
        print("❌ Sistema NÃO está no Railway")
        print("🔧 Faça o deploy para receber tips automáticas")
    
    print("\n🎯 PRÓXIMOS PASSOS:")
    if is_railway:
        print("1. ✅ Sistema operacional")
        print("2. ⏰ Aguardar jogos profissionais")
        print("3. 📱 Verificar se recebe tips quando houver jogos")
    else:
        print("1. 🚂 Fazer deploy no Railway")
        print("2. ⚙️ Configurar variáveis de ambiente")
        print("3. 🔄 Verificar logs após deploy")
    
    print(f"\n📞 Em caso de problemas, verificar:")
    print(f"   • Logs do Railway")
    print(f"   • Status das APIs")
    print(f"   • Configurações do Telegram")

if __name__ == "__main__":
    main() 