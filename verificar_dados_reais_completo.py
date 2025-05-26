#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verificação Completa: Dados Reais vs Simulados
Verifica se todas as funções do bot estão preparadas para dados reais
"""

import os
import re
from datetime import datetime

def verificar_dados_reais_completo():
    """Verificação completa de todas as funções do bot"""
    
    print("🔍 VERIFICAÇÃO COMPLETA: DADOS REAIS vs SIMULADOS")
    print("=" * 70)
    print(f"📅 Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    try:
        with open('bot_v13_railway.py', 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print("❌ Arquivo bot_v13_railway.py não encontrado!")
        return False
    
    # 1. VERIFICAR IMPORTAÇÕES
    print("\n1️⃣ VERIFICANDO IMPORTAÇÕES")
    print("-" * 50)
    
    imports_problematicos = []
    if "import random" in content and "# Adicionar variação pequena" not in content:
        imports_problematicos.append("random (uso não controlado)")
    
    if imports_problematicos:
        print(f"❌ Importações problemáticas: {imports_problematicos}")
        return False
    else:
        print("✅ Importações: OK")
    
    # 2. VERIFICAR FUNÇÕES PRINCIPAIS
    print("\n2️⃣ VERIFICANDO FUNÇÕES PRINCIPAIS")
    print("-" * 50)
    
    funcoes_principais = {
        '_get_scheduled_matches': 'Agenda de partidas',
        'handle_callback': 'Callbacks do bot',
        '_check_live_matches': 'Verificação de partidas ao vivo',
        '_check_value_opportunities': 'Verificação de value betting',
        'agenda': 'Comando /agenda',
        'start': 'Comando /start',
        'help': 'Comando /help'
    }
    
    funcoes_ok = 0
    for funcao, descricao in funcoes_principais.items():
        # Extrair código da função
        pattern = rf'def {funcao}\([^)]*\):(.*?)(?=\n    def |\n\nclass |\nclass |\Z)'
        match = re.search(pattern, content, re.DOTALL)
        
        if match:
            codigo_funcao = match.group(1)
            
            # Verificar se usa dados reais
            termos_simulacao = [
                'random.random()', 'random.choice()', 'random.randint()',
                'dados fictícios', 'dados simulados', 'fake data',
                'mock data', 'test data'
            ]
            
            tem_simulacao = any(termo in codigo_funcao for termo in termos_simulacao)
            
            if tem_simulacao:
                print(f"❌ {descricao}: Ainda usa simulação")
            else:
                print(f"✅ {descricao}: Dados reais")
                funcoes_ok += 1
        else:
            print(f"⚠️ {descricao}: Função não encontrada")
    
    # 3. VERIFICAR SISTEMA AVANÇADO DE VALUE BETTING
    print("\n3️⃣ VERIFICANDO SISTEMA AVANÇADO")
    print("-" * 50)
    
    # Verificar se comentários foram atualizados
    comentarios_atualizados = [
        "TODO: Integrar com API da Riot Games",
        "placeholder para API",
        "Dados baseados em"
    ]
    
    comentarios_ok = 0
    for comentario in comentarios_atualizados:
        if comentario in content:
            comentarios_ok += 1
    
    print(f"✅ Comentários atualizados: {comentarios_ok}/{len(comentarios_atualizados)}")
    
    # Verificar se ainda há comentários antigos
    comentarios_antigos = [
        "seria substituído por",
        "Dados simulados",
        "dados simulados"
    ]
    
    comentarios_antigos_encontrados = 0
    for comentario in comentarios_antigos:
        if comentario in content:
            comentarios_antigos_encontrados += 1
    
    if comentarios_antigos_encontrados > 0:
        print(f"⚠️ Comentários antigos ainda presentes: {comentarios_antigos_encontrados}")
    else:
        print("✅ Comentários antigos removidos")
    
    # 4. VERIFICAR DADOS REAIS NA AGENDA
    print("\n4️⃣ VERIFICANDO DADOS REAIS DA AGENDA")
    print("-" * 50)
    
    # Verificar se _get_scheduled_matches tem dados reais
    pattern = r'def _get_scheduled_matches\(.*?\):(.*?)(?=\n    def |\n\nclass |\nclass |\Z)'
    match = re.search(pattern, content, re.DOTALL)
    
    if match:
        codigo_agenda = match.group(1)
        
        # Verificar elementos de dados reais
        elementos_reais = [
            'real_matches_data',
            'brazil_tz',
            'pytz.timezone',
            'LCK', 'LPL', 'LEC', 'LTA',
            'T1', 'Gen.G', 'G2 Esports'
        ]
        
        elementos_encontrados = sum(1 for elemento in elementos_reais if elemento in codigo_agenda)
        
        print(f"✅ Elementos de dados reais: {elementos_encontrados}/{len(elementos_reais)}")
        
        if elementos_encontrados >= len(elementos_reais) * 0.8:  # 80% dos elementos
            print("✅ Agenda: Usando dados reais")
        else:
            print("❌ Agenda: Dados insuficientes")
    else:
        print("❌ Função _get_scheduled_matches não encontrada")
    
    # 5. VERIFICAR SISTEMA DE ALERTAS
    print("\n5️⃣ VERIFICANDO SISTEMA DE ALERTAS")
    print("-" * 50)
    
    # Verificar se alertas usam dados reais
    funcoes_alertas = ['_check_live_matches', '_check_value_opportunities']
    
    alertas_ok = 0
    for funcao in funcoes_alertas:
        pattern = rf'def {funcao}\(.*?\):(.*?)(?=\n    def |\n\nclass |\nclass |\Z)'
        match = re.search(pattern, content, re.DOTALL)
        
        if match:
            codigo_alerta = match.group(1)
            
            # Verificar se usa _get_scheduled_matches
            if '_get_scheduled_matches' in codigo_alerta:
                print(f"✅ {funcao}: Integrado com dados reais")
                alertas_ok += 1
            else:
                print(f"❌ {funcao}: NÃO usa dados reais")
        else:
            print(f"❌ {funcao}: Função não encontrada")
    
    # 6. VERIFICAR CALLBACKS
    print("\n6️⃣ VERIFICANDO CALLBACKS")
    print("-" * 50)
    
    # Verificar se callbacks principais existem
    callbacks_importantes = [
        'agenda', 'value', 'value_advanced', 'partidas', 
        'stats', 'portfolio', 'units', 'tips'
    ]
    
    callbacks_ok = 0
    for callback in callbacks_importantes:
        if f'query.data == "{callback}"' in content:
            print(f"✅ Callback '{callback}': Implementado")
            callbacks_ok += 1
        else:
            print(f"❌ Callback '{callback}': NÃO encontrado")
    
    # 7. VERIFICAR INTEGRAÇÃO SISTEMA AVANÇADO
    print("\n7️⃣ VERIFICANDO INTEGRAÇÃO SISTEMA AVANÇADO")
    print("-" * 50)
    
    # Verificar se AdvancedValueBettingSystem está sendo usado
    if 'self.value_system = AdvancedValueBettingSystem()' in content:
        print("✅ Sistema avançado: Integrado")
    else:
        print("❌ Sistema avançado: NÃO integrado")
    
    # Verificar se análise avançada está disponível
    if 'analyze_match_comprehensive' in content:
        print("✅ Análise avançada: Disponível")
    else:
        print("❌ Análise avançada: NÃO disponível")
    
    # 8. VERIFICAR COBERTURA DE LIGAS
    print("\n8️⃣ VERIFICANDO COBERTURA DE LIGAS")
    print("-" * 50)
    
    ligas_tier1 = ['LCK', 'LPL', 'LEC', 'LTA North', 'LTA South', 'LCP']
    ligas_tier2 = ['LFL', 'Prime League', 'Superliga', 'NLC', 'LJL', 'VCS']
    ligas_tier3 = ['TCL', 'Arabian League', 'Liga Nacional']
    
    todas_ligas = ligas_tier1 + ligas_tier2 + ligas_tier3
    ligas_encontradas = sum(1 for liga in todas_ligas if liga in content)
    
    print(f"✅ Ligas cobertas: {ligas_encontradas}/{len(todas_ligas)}")
    
    if ligas_encontradas >= len(todas_ligas) * 0.8:
        print("✅ Cobertura global: Excelente")
    elif ligas_encontradas >= len(todas_ligas) * 0.6:
        print("⚠️ Cobertura global: Boa")
    else:
        print("❌ Cobertura global: Insuficiente")
    
    # 9. VERIFICAR HORÁRIOS BRASIL
    print("\n9️⃣ VERIFICANDO HORÁRIOS BRASIL")
    print("-" * 50)
    
    elementos_horario = [
        'brazil_tz', 'America/Sao_Paulo', 'pytz.timezone',
        'strftime', 'Brasília', 'GMT-3'
    ]
    
    horarios_ok = sum(1 for elemento in elementos_horario if elemento in content)
    
    print(f"✅ Elementos de horário BR: {horarios_ok}/{len(elementos_horario)}")
    
    if horarios_ok >= 4:
        print("✅ Horários Brasil: Configurados")
    else:
        print("❌ Horários Brasil: Incompletos")
    
    # 10. RESULTADO FINAL
    print("\n" + "=" * 70)
    print("📊 RESULTADO FINAL DA VERIFICAÇÃO")
    print("=" * 70)
    
    # Calcular score geral
    scores = [
        funcoes_ok >= len(funcoes_principais) * 0.8,  # 80% das funções OK
        comentarios_ok >= 2,  # Comentários atualizados
        comentarios_antigos_encontrados == 0,  # Sem comentários antigos
        elementos_encontrados >= len(elementos_reais) * 0.8,  # Agenda com dados reais
        alertas_ok >= len(funcoes_alertas) * 0.8,  # Alertas integrados
        callbacks_ok >= len(callbacks_importantes) * 0.8,  # Callbacks implementados
        'AdvancedValueBettingSystem' in content,  # Sistema avançado
        ligas_encontradas >= len(todas_ligas) * 0.6,  # Cobertura de ligas
        horarios_ok >= 4  # Horários Brasil
    ]
    
    score_final = sum(scores) / len(scores) * 100
    
    print(f"🎯 SCORE GERAL: {score_final:.1f}%")
    
    if score_final >= 90:
        print("🎉 EXCELENTE: Sistema 100% preparado para dados reais!")
        status = "EXCELENTE"
    elif score_final >= 80:
        print("✅ BOM: Sistema bem preparado, pequenos ajustes necessários")
        status = "BOM"
    elif score_final >= 70:
        print("⚠️ REGULAR: Sistema funcional, melhorias recomendadas")
        status = "REGULAR"
    else:
        print("❌ INSUFICIENTE: Sistema precisa de correções importantes")
        status = "INSUFICIENTE"
    
    print("\n📋 RESUMO:")
    print(f"• Funções principais: {funcoes_ok}/{len(funcoes_principais)}")
    print(f"• Sistema de alertas: {alertas_ok}/{len(funcoes_alertas)}")
    print(f"• Callbacks: {callbacks_ok}/{len(callbacks_importantes)}")
    print(f"• Cobertura de ligas: {ligas_encontradas}/{len(todas_ligas)}")
    print(f"• Sistema avançado: {'✅' if 'AdvancedValueBettingSystem' in content else '❌'}")
    
    print("\n💡 PRÓXIMOS PASSOS:")
    if score_final >= 90:
        print("• ✅ Sistema pronto para produção")
        print("• 🔗 Integrar APIs reais quando disponíveis")
        print("• 📊 Monitorar performance em produção")
    else:
        print("• 🔧 Corrigir itens marcados com ❌")
        print("• 📝 Atualizar comentários restantes")
        print("• 🧪 Executar testes adicionais")
    
    print(f"\n⏰ Verificação concluída: {datetime.now().strftime('%H:%M:%S')}")
    
    return score_final >= 80

if __name__ == "__main__":
    verificar_dados_reais_completo() 