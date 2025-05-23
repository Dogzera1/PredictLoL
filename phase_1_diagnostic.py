#!/usr/bin/env python3
"""
FASE 1 - DIAGNÓSTICO E DEFINIÇÃO DE METAS
Script principal para executar diagnóstico completo e definir metas de melhoria
"""

import os
import sys
sys.path.append('.')

from services.model_evaluator import ModelEvaluator
from services.goals_manager import GoalsManager, Goal, MetricType, Priority
import json
from datetime import datetime, timedelta

def main():
    print("🚀 INICIANDO FASE 1 - DIAGNÓSTICO E DEFINIÇÃO DE METAS")
    print("="*70)
    
    # Verificar se os arquivos necessários existem
    required_files = [
        "data/model.pkl",
        "data/scaler.pkl", 
        "data/processed_match_data.json"
    ]
    
    missing_files = [f for f in required_files if not os.path.exists(f)]
    if missing_files:
        print("❌ Arquivos necessários não encontrados:")
        for file in missing_files:
            print(f"   • {file}")
        print("\n💡 Execute primeiro o treinamento do modelo ou verifique os caminhos dos arquivos.")
        return
    
    print("✅ Todos os arquivos necessários encontrados\n")
    
    # Etapa 1: Diagnóstico Completo
    print("📋 ETAPA 1: DIAGNÓSTICO COMPLETO DO MODELO")
    print("-" * 50)
    
    evaluator = ModelEvaluator()
    df = evaluator.load_test_data()
    
    if df.empty:
        print("❌ Não foi possível carregar os dados de teste")
        return
    
    # Gerar relatório de diagnóstico
    report = evaluator.generate_report(df)
    
    # Salvar relatório
    report_file = f"data/diagnostic_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    evaluator.save_report(report, report_file)
    
    # Exibir resumo do diagnóstico
    print("\n📊 RESUMO DO DIAGNÓSTICO:")
    print("-" * 30)
    metrics = report['performance_metrics']
    print(f"🎯 AUC-ROC: {metrics['auc_roc']:.4f}")
    print(f"📉 Log-Loss: {metrics['log_loss']:.4f}")  
    print(f"✅ Acurácia: {metrics['accuracy']:.4f}")
    print(f"⚡ Tempo inferência: {metrics['inference_time_ms']:.2f}ms")
    print(f"🎯 Amostras totais: {metrics['total_samples']:,}")
    
    # Análise contextual
    if 'context_analysis' in report and report['context_analysis']:
        print("\n🔍 ANÁLISE CONTEXTUAL:")
        context = report['context_analysis']
        
        if 'by_patch' in context:
            patches = list(context['by_patch'].keys())
            print(f"   📊 Patches analisados: {len(patches)}")
            if patches:
                worst_patch = min(context['by_patch'].items(), 
                                key=lambda x: x[1]['auc_roc'])
                print(f"   ⚠️ Pior patch: {worst_patch[0]} (AUC: {worst_patch[1]['auc_roc']:.3f})")
        
        if 'by_duration' in context:
            durations = list(context['by_duration'].keys())
            print(f"   ⏱️ Durações analisadas: {len(durations)}")
            if durations:
                worst_duration = min(context['by_duration'].items(),
                                   key=lambda x: x[1]['auc_roc'])
                print(f"   ⚠️ Pior duração: {worst_duration[0]} (AUC: {worst_duration[1]['auc_roc']:.3f})")
    
    # Cenários problemáticos
    if 'worst_scenarios' in report:
        worst = report['worst_scenarios']
        if worst['worst_predictions']:
            print(f"\n⚠️ CENÁRIOS PROBLEMÁTICOS:")
            print(f"   🔍 {len(worst['worst_predictions'])} piores predições identificadas")
            
            # Mostrar padrões comuns
            if 'common_patterns' in worst:
                patterns = worst['common_patterns']
                if 'problematic_patches' in patterns:
                    print("   📊 Patches mais problemáticos:")
                    for patch, count in list(patterns['problematic_patches'].items())[:3]:
                        print(f"      • {patch}: {count} casos")
    
    # Recomendações
    print(f"\n💡 RECOMENDAÇÕES ({len(report['recommendations'])}):")
    for i, rec in enumerate(report['recommendations'], 1):
        print(f"   {i}. {rec}")
    
    # Etapa 2: Definição de Metas
    print("\n" + "="*70)
    print("📋 ETAPA 2: DEFINIÇÃO DE METAS")
    print("-" * 50)
    
    goals_manager = GoalsManager()
    
    # Definir metas baseadas na performance atual
    current_auc = report['performance_metrics']['auc_roc']
    current_log_loss = report['performance_metrics']['log_loss']
    current_accuracy = report['performance_metrics']['accuracy']
    current_inference_time = report['performance_metrics']['inference_time_ms']
    
    # Criar metas ambiciosas mas realistas
    goals = [
        Goal(
            metric=MetricType.AUC_ROC,
            current_value=current_auc,
            target_value=min(0.95, current_auc + 0.03),  # +3% ou máximo 95%
            priority=Priority.HIGH,
            deadline=(datetime.now() + timedelta(weeks=4)).isoformat(),
            description="Melhorar AUC-ROC através de feature engineering avançada",
            business_impact="Aumentar taxa de acerto das apostas em 5-10%",
            success_criteria="AUC-ROC >= 0.95 em dados de validação"
        ),
        Goal(
            metric=MetricType.LOG_LOSS,
            current_value=current_log_loss,
            target_value=max(0.25, current_log_loss - 0.05),  # -0.05 ou mínimo 0.25
            priority=Priority.HIGH,
            deadline=(datetime.now() + timedelta(weeks=4)).isoformat(),
            description="Reduzir log-loss através de calibração de modelo",
            business_impact="Melhorar calibração das probabilidades para apostas mais seguras",
            success_criteria="Log-loss <= 0.35 com boa calibração"
        ),
        Goal(
            metric=MetricType.ACCURACY,
            current_value=current_accuracy,
            target_value=min(0.92, current_accuracy + 0.02),  # +2% ou máximo 92%
            priority=Priority.MEDIUM,
            deadline=(datetime.now() + timedelta(weeks=6)).isoformat(),
            description="Aumentar acurácia geral do modelo",
            business_impact="Reduzir número de apostas perdidas",
            success_criteria="Acurácia >= 85% consistente em diferentes cenários"
        ),
        Goal(
            metric=MetricType.INFERENCE_TIME,
            current_value=current_inference_time,
            target_value=min(50.0, current_inference_time * 0.8),  # -20% ou máximo 50ms
            priority=Priority.MEDIUM,
            deadline=(datetime.now() + timedelta(weeks=8)).isoformat(),
            description="Otimizar tempo de inferência para produção",
            business_impact="Permitir análise em tempo real durante partidas",
            success_criteria="Tempo de inferência <= 100ms por predição"
        ),
        Goal(
            metric=MetricType.CONFIDENT_ACCURACY,
            current_value=report['performance_metrics'].get('confident_accuracy_0.8', 0.85),
            target_value=0.95,  # 95% de acurácia em predições confiantes
            priority=Priority.HIGH,
            deadline=(datetime.now() + timedelta(weeks=6)).isoformat(),
            description="Melhorar acurácia em predições de alta confiança",
            business_impact="Identificar apostas de maior probabilidade de sucesso",
            success_criteria="95% de acurácia em predições com confiança >= 80%"
        )
    ]
    
    goals_manager.set_goals(goals)
    
    # Exibir metas definidas
    goals_manager.print_goals_summary()
    
    # Etapa 3: Análise de Prioridades
    print("\n" + "="*70)
    print("📋 ETAPA 3: ANÁLISE DE PRIORIDADES")
    print("-" * 50)
    
    # Calcular esforço estimado por meta
    priority_analysis = {
        'critical': [],
        'high': [],
        'medium': [],
        'low': []
    }
    
    for goal in goals_manager.goals:
        priority_analysis[goal.priority.value].append({
            'description': goal.description,
            'improvement': f"{goal.improvement_percentage:.1f}%",
            'deadline': goal.deadline[:10]
        })
    
    print("🚨 PRIORIDADES DE IMPLEMENTAÇÃO:")
    for priority, goals_list in priority_analysis.items():
        if goals_list:
            print(f"\n   {priority.upper()} ({len(goals_list)} metas):")
            for goal in goals_list:
                print(f"      • {goal['description']}")
                print(f"        Melhoria necessária: {goal['improvement']}")
                print(f"        Prazo: {goal['deadline']}")
    
    # 4. Próximos passos baseados na análise
    print("\n" + "="*70)
    print("📋 PRÓXIMOS PASSOS RECOMENDADOS")
    print("-"*50)
    
    # Usar metrics do report em vez de current_metrics
    current_auc = report['performance_metrics']['auc_roc']
    current_log_loss = report['performance_metrics']['log_loss']
    current_accuracy = report['performance_metrics']['accuracy']
    
    # Determinar foco principal baseado na performance
    if current_auc < 0.80:
        focus = "🚨 CRÍTICO: Foco em feature engineering e seleção de modelo"
        phase_priority = "Fase 2 e 3 em paralelo"
    elif current_log_loss > 0.6:
        focus = "⚡ URGENTE: Foco em calibração e regularização"
        phase_priority = "Fase 2 (features) seguida da Fase 4 (modelos)"
    elif current_accuracy < 0.75:
        focus = "📊 IMPORTANTE: Foco em dados e features"
        phase_priority = "Fase 2 completa, depois Fase 4"
    else:
        focus = "✨ OTIMIZAÇÃO: Foco em refinamento e produção"
        phase_priority = "Fase 3, 4 e 5 sequenciais"
    
    print(f"\n🎯 FOCO RECOMENDADO: {focus}")
    print(f"📋 SEQUÊNCIA DE FASES: {phase_priority}")
    
    print("\n📋 PRÓXIMAS AÇÕES ESPECÍFICAS:")
    print("1. 🔧 FASE 2 - ENRIQUECIMENTO DE DADOS:")
    print("   • Integrar APIs de visão de mapa e controle de objetivos")
    print("   • Adicionar estatísticas de partidas profissionais (LCS, LEC)")
    print("   • Criar features temporais avançadas (deltas por minuto)")
    print("   • Implementar features de meta-patch e counter-picks")
    
    print("\n2. 🧠 FASE 3 - FEATURE ENGINEERING AVANÇADO:")
    print("   • Criar interações entre champions e composições")
    print("   • Implementar embeddings de similaridade de comps")
    print("   • Adicionar encoding contextual (patch, região, tier)")
    print("   • Features de performance recente de jogadores/times")
    
    print("\n3. 🤖 FASE 4 - OTIMIZAÇÃO DE MODELOS:")
    print("   • Testar arquitecturas avançadas (Transformers, GNNs)")
    print("   • Implementar ensemble methods e stacking")
    print("   • Calibração de probabilidades (Platt scaling)")
    print("   • Hyperparameter optimization (Optuna)")
    
    print("\n4. 🚀 FASE 5 - DEPLOY E MONITORAMENTO:")
    print("   • Pipeline CI/CD automatizado")
    print("   • Monitoramento de drift de dados")
    print("   • Sistema de re-treinamento automático")
    print("   • Métricas de negócio e A/B testing")
    
    # Resumo final
    print("\n" + "="*70)
    print("📊 RESUMO DA FASE 1")
    print("-" * 50)
    print(f"✅ Diagnóstico completo realizado")
    print(f"📊 {len(goals_manager.goals)} metas definidas")
    print(f"🎯 Próxima fase recomendada: {phase_priority}")
    print(f"📄 Relatório salvo em: {report_file}")
    print(f"📄 Metas salvas em: {goals_manager.goals_file}")
    
    # Estimativa de timeline
    total_weeks = sum([4, 4, 2, 6, 3, 3])  # Baseado nos prazos das metas
    print(f"⏱️ Timeline estimado: {total_weeks} semanas para todas as metas")
    
    print("\n🚀 FASE 1 CONCLUÍDA COM SUCESSO!")
    print("🎯 Execute as próximas fases seguindo as prioridades definidas.")
    
    return {
        'report': report,
        'goals': goals_manager.goals,
        'next_steps': [],
        'files_generated': [report_file, goals_manager.goals_file]
    }

if __name__ == "__main__":
    try:
        result = main()
        print(f"\n✅ Execução concluída com sucesso!")
    except Exception as e:
        print(f"\n❌ Erro durante execução: {e}")
        import traceback
        traceback.print_exc() 