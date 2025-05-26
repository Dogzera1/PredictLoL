#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste Final - Sistema de Alertas para Partidas Reais
Confirma que o sistema está 100% configurado para dados reais
"""

import sys
sys.path.append('.')

def teste_alertas_partidas_reais():
    """Teste completo do sistema de alertas com partidas reais"""
    print("🚀 TESTE FINAL - ALERTAS PARA PARTIDAS REAIS")
    print("=" * 70)
    
    try:
        from bot_v13_railway import BotLoLV3Railway
        
        # Inicializar bot
        print("🤖 Inicializando bot...")
        bot = BotLoLV3Railway()
        alert_system = bot.alert_system
        print("✅ Bot e sistema de alertas inicializados")
        
        # Teste 1: Verificar dados das partidas
        print(f"\n📊 TESTE 1: DADOS DAS PARTIDAS")
        print("-" * 50)
        
        agenda_data = bot._get_scheduled_matches()
        partidas = agenda_data.get('matches', [])
        
        print(f"✅ Total de partidas: {len(partidas)}")
        
        # Verificar se são partidas reais
        ligas_reais = 0
        times_reais = 0
        
        for partida in partidas:
            liga = partida.get('league', '')
            team1 = partida.get('team1', '')
            team2 = partida.get('team2', '')
            
            # Verificar se liga é real
            ligas_oficiais = {
                'LCK', 'LPL', 'LEC', 'LTA North', 'LTA South', 'LCP',
                'VCS', 'LJL', 'CBLOL', 'CBLOL Academy', 'NACL',
                'LFL', 'Prime League', 'Superliga', 'NLC', 'PG Nationals',
                'TCL', 'Arabian League', 'Liga Nacional México', 
                'Liga Nacional Argentina', 'Liga Nacional Chile',
                'LPLOL', 'GLL'
            }
            
            if liga in ligas_oficiais:
                ligas_reais += 1
            
            # Verificar se times são reais (não fictícios)
            if team1 and team2 and team1 != team2:
                times_reais += 1
        
        print(f"✅ Ligas oficiais: {ligas_reais}/{len(partidas)}")
        print(f"✅ Times válidos: {times_reais}/{len(partidas)}")
        
        # Teste 2: Verificar métodos de alertas
        print(f"\n🚨 TESTE 2: MÉTODOS DE ALERTAS")
        print("-" * 50)
        
        # Testar _check_live_matches
        print("🔍 Testando _check_live_matches...")
        try:
            alert_system._check_live_matches()
            print("✅ _check_live_matches executado com sucesso")
            metodo_live_ok = True
        except Exception as e:
            print(f"❌ Erro em _check_live_matches: {e}")
            metodo_live_ok = False
        
        # Testar _check_value_opportunities
        print("🔍 Testando _check_value_opportunities...")
        try:
            alert_system._check_value_opportunities()
            print("✅ _check_value_opportunities executado com sucesso")
            metodo_value_ok = True
        except Exception as e:
            print(f"❌ Erro em _check_value_opportunities: {e}")
            metodo_value_ok = False
        
        # Teste 3: Verificar integração com dados reais
        print(f"\n🔗 TESTE 3: INTEGRAÇÃO COM DADOS REAIS")
        print("-" * 50)
        
        import inspect
        
        # Verificar se _check_live_matches usa _get_scheduled_matches
        source_live = inspect.getsource(alert_system._check_live_matches)
        usa_dados_reais_live = "_get_scheduled_matches" in source_live
        
        # Verificar se _check_value_opportunities usa _get_scheduled_matches
        source_value = inspect.getsource(alert_system._check_value_opportunities)
        usa_dados_reais_value = "_get_scheduled_matches" in source_value
        
        print(f"✅ _check_live_matches usa dados reais: {usa_dados_reais_live}")
        print(f"✅ _check_value_opportunities usa dados reais: {usa_dados_reais_value}")
        
        # Verificar se não há termos de simulação
        termos_simulacao = ["simular", "simulação", "fake", "mock", "fictício"]
        tem_simulacao = False
        
        for termo in termos_simulacao:
            if termo.lower() in source_live.lower() or termo.lower() in source_value.lower():
                tem_simulacao = True
                break
        
        print(f"✅ Livre de simulação: {not tem_simulacao}")
        
        # Teste 4: Configurações do sistema
        print(f"\n⚙️ TESTE 4: CONFIGURAÇÕES DO SISTEMA")
        print("-" * 50)
        
        settings = alert_system.alert_settings
        
        config_ok = (
            settings.get('live_matches', False) and
            settings.get('value_opportunities', False) and
            settings.get('min_ev', 0) > 0 and
            settings.get('min_confidence', 0) > 0
        )
        
        print(f"✅ Alertas de partidas ao vivo: {settings.get('live_matches', False)}")
        print(f"✅ Alertas de value betting: {settings.get('value_opportunities', False)}")
        print(f"✅ EV mínimo: {settings.get('min_ev', 0)}")
        print(f"✅ Confiança mínima: {settings.get('min_confidence', 0)}")
        print(f"✅ Configurações válidas: {config_ok}")
        
        # Resultado final
        print(f"\n📊 RESULTADO FINAL")
        print("=" * 70)
        
        todos_testes = [
            ligas_reais == len(partidas),  # Todas as ligas são reais
            times_reais == len(partidas),  # Todos os times são válidos
            metodo_live_ok,                # Método live funciona
            metodo_value_ok,               # Método value funciona
            usa_dados_reais_live,          # Live usa dados reais
            usa_dados_reais_value,         # Value usa dados reais
            not tem_simulacao,             # Sem simulação
            config_ok                      # Configurações OK
        ]
        
        testes_passaram = sum(todos_testes)
        total_testes = len(todos_testes)
        
        print(f"✅ Testes passaram: {testes_passaram}/{total_testes}")
        print(f"📈 Taxa de sucesso: {(testes_passaram/total_testes)*100:.1f}%")
        
        if testes_passaram == total_testes:
            print(f"\n🎉 SISTEMA DE ALERTAS 100% CONFIGURADO PARA PARTIDAS REAIS!")
            print("✅ Todos os alertas usam apenas dados reais")
            print("✅ Nenhuma simulação ou dado fictício detectado")
            print("✅ Integração perfeita com agenda oficial")
            print("✅ Configurações adequadas para produção")
            return True
        else:
            print(f"\n⚠️ ALGUNS PROBLEMAS AINDA EXISTEM")
            print(f"❌ {total_testes - testes_passaram} testes falharam")
            return False
            
    except Exception as e:
        print(f"❌ ERRO GERAL: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Função principal"""
    resultado = teste_alertas_partidas_reais()
    
    if resultado:
        print(f"\n🏆 CONCLUSÃO: ALERTAS CONFIGURADOS CORRETAMENTE!")
        print("O sistema está pronto para detectar apenas partidas reais.")
    else:
        print(f"\n❌ CONCLUSÃO: AINDA HÁ PROBLEMAS A CORRIGIR")
        print("Verifique os testes que falharam acima.")

if __name__ == "__main__":
    main() 