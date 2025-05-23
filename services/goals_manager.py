#!/usr/bin/env python3
"""
Sistema de Definição e Tracking de Metas
Fase 1: Definição de Metas para Melhoria do Modelo LoL
"""

import json
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum

class MetricType(Enum):
    AUC_ROC = "auc_roc"
    LOG_LOSS = "log_loss"
    ACCURACY = "accuracy"
    INFERENCE_TIME = "inference_time_ms"
    CONFIDENT_ACCURACY = "confident_accuracy"
    BRIER_SCORE = "brier_score"
    ECE = "ece"
    PROFIT_RATE = "profit_rate"

class Priority(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

@dataclass
class Goal:
    """Classe para representar uma meta específica"""
    metric: MetricType
    current_value: float
    target_value: float
    priority: Priority
    deadline: str  # ISO format
    description: str
    business_impact: str
    success_criteria: str
    
    @property
    def improvement_needed(self) -> float:
        """Calcula melhoria necessária (valor absoluto)"""
        return abs(self.target_value - self.current_value)
    
    @property
    def improvement_percentage(self) -> float:
        """Calcula melhoria necessária em %"""
        if self.current_value == 0:
            return float('inf')
        return (abs(self.target_value - self.current_value) / abs(self.current_value)) * 100
    
    @property
    def is_minimization_metric(self) -> bool:
        """True se a métrica deve ser minimizada"""
        return self.metric in [MetricType.LOG_LOSS, MetricType.INFERENCE_TIME, 
                              MetricType.BRIER_SCORE, MetricType.ECE]
    
    def progress_score(self, new_value: float) -> float:
        """Calcula score de progresso (0-100%)"""
        if self.is_minimization_metric:
            if self.current_value <= self.target_value:
                return 100.0  # Meta já atingida
            
            improvement = self.current_value - new_value
            total_needed = self.current_value - self.target_value
            
            if total_needed <= 0:
                return 100.0
            
            return min(100.0, max(0.0, (improvement / total_needed) * 100))
        else:
            if self.current_value >= self.target_value:
                return 100.0  # Meta já atingida
            
            improvement = new_value - self.current_value
            total_needed = self.target_value - self.current_value
            
            if total_needed <= 0:
                return 100.0
            
            return min(100.0, max(0.0, (improvement / total_needed) * 100))

class GoalsManager:
    """Sistema de gerenciamento de metas para melhoria do modelo"""
    
    def __init__(self, goals_file: str = "data/model_goals.json"):
        self.goals_file = goals_file
        self.goals: List[Goal] = []
        self.load_goals()
    
    def define_baseline_goals(self, current_metrics: Dict[str, float]) -> List[Goal]:
        """Define metas baseline baseadas nas métricas atuais"""
        
        goals = []
        
        # Meta de AUC-ROC
        current_auc = current_metrics.get('auc_roc', 0.5)
        if current_auc < 0.75:
            target_auc = 0.85
            priority = Priority.CRITICAL
        elif current_auc < 0.85:
            target_auc = 0.90
            priority = Priority.HIGH
        else:
            target_auc = min(0.95, current_auc + 0.03)
            priority = Priority.MEDIUM
        
        goals.append(Goal(
            metric=MetricType.AUC_ROC,
            current_value=current_auc,
            target_value=target_auc,
            priority=priority,
            deadline=(datetime.now() + timedelta(weeks=4)).isoformat(),
            description=f"Elevar AUC-ROC de {current_auc:.3f} para {target_auc:.3f}",
            business_impact="Melhoria na precisão das predições aumenta ROI das apostas",
            success_criteria="AUC-ROC consistente >= target em teste holdout"
        ))
        
        # Meta de Log-Loss
        current_logloss = current_metrics.get('log_loss', 1.0)
        if current_logloss > 0.6:
            target_logloss = 0.45
            priority = Priority.CRITICAL
        elif current_logloss > 0.45:
            target_logloss = 0.35
            priority = Priority.HIGH
        else:
            target_logloss = max(0.25, current_logloss - 0.05)
            priority = Priority.MEDIUM
        
        goals.append(Goal(
            metric=MetricType.LOG_LOSS,
            current_value=current_logloss,
            target_value=target_logloss,
            priority=priority,
            deadline=(datetime.now() + timedelta(weeks=4)).isoformat(),
            description=f"Reduzir Log-Loss de {current_logloss:.3f} para {target_logloss:.3f}",
            business_impact="Melhor calibração reduz perdas em apostas com alta confiança",
            success_criteria="Log-Loss consistente <= target em validação cruzada"
        ))
        
        # Meta de Tempo de Inferência
        current_time = current_metrics.get('inference_time_ms', 1000)
        target_time = min(100, current_time * 0.8) if current_time > 100 else current_time
        
        if current_time > 200:
            priority = Priority.HIGH
        elif current_time > 100:
            priority = Priority.MEDIUM
        else:
            priority = Priority.LOW
        
        goals.append(Goal(
            metric=MetricType.INFERENCE_TIME,
            current_value=current_time,
            target_value=target_time,
            priority=priority,
            deadline=(datetime.now() + timedelta(weeks=2)).isoformat(),
            description=f"Reduzir tempo de inferência de {current_time:.1f}ms para {target_time:.1f}ms",
            business_impact="Resposta mais rápida permite apostas em tempo real",
            success_criteria="99% das inferências <= target em produção"
        ))
        
        # Meta de Acurácia Confiante
        current_conf_acc = current_metrics.get('confident_accuracy_0.8', 0.5)
        target_conf_acc = min(0.95, current_conf_acc + 0.1)
        
        goals.append(Goal(
            metric=MetricType.CONFIDENT_ACCURACY,
            current_value=current_conf_acc,
            target_value=target_conf_acc,
            priority=Priority.HIGH,
            deadline=(datetime.now() + timedelta(weeks=6)).isoformat(),
            description=f"Elevar acurácia confiante de {current_conf_acc:.3f} para {target_conf_acc:.3f}",
            business_impact="Maior precisão em apostas de alta confiança aumenta lucro",
            success_criteria="Acurácia >= target para predições com confiança > 80%"
        ))
        
        return goals
    
    def define_advanced_goals(self, current_metrics: Dict[str, float], 
                            business_kpis: Optional[Dict[str, float]] = None) -> List[Goal]:
        """Define metas avançadas incluindo KPIs de negócio"""
        
        goals = self.define_baseline_goals(current_metrics)
        
        # Meta de Brier Score (calibração)
        current_brier = current_metrics.get('brier_score', 0.5)
        target_brier = max(0.15, current_brier - 0.05)
        
        goals.append(Goal(
            metric=MetricType.BRIER_SCORE,
            current_value=current_brier,
            target_value=target_brier,
            priority=Priority.MEDIUM,
            deadline=(datetime.now() + timedelta(weeks=3)).isoformat(),
            description=f"Reduzir Brier Score de {current_brier:.3f} para {target_brier:.3f}",
            business_impact="Melhor calibração aumenta confiança em apostas variadas",
            success_criteria="Brier Score <= target em dados holdout"
        ))
        
        # Meta de ECE (Expected Calibration Error)
        current_ece = current_metrics.get('ece', 0.2)
        target_ece = max(0.05, current_ece - 0.03)
        
        goals.append(Goal(
            metric=MetricType.ECE,
            current_value=current_ece,
            target_value=target_ece,
            priority=Priority.MEDIUM,
            deadline=(datetime.now() + timedelta(weeks=3)).isoformat(),
            description=f"Reduzir ECE de {current_ece:.3f} para {target_ece:.3f}",
            business_impact="Calibração precisa permite sizing otimizado de apostas",
            success_criteria="ECE <= target com intervalo de confiança 95%"
        ))
        
        # Meta de ROI (se dados de negócio disponíveis)
        if business_kpis and 'current_roi' in business_kpis:
            current_roi = business_kpis['current_roi']
            target_roi = current_roi * 1.3  # 30% de melhoria
            
            goals.append(Goal(
                metric=MetricType.PROFIT_RATE,
                current_value=current_roi,
                target_value=target_roi,
                priority=Priority.CRITICAL,
                deadline=(datetime.now() + timedelta(weeks=8)).isoformat(),
                description=f"Elevar ROI de {current_roi:.2f} para {target_roi:.2f}",
                business_impact="Objetivo final: maximizar retorno das apostas",
                success_criteria="ROI >= target em período de 30 dias de apostas reais"
            ))
        
        return goals
    
    def prioritize_goals(self, goals: List[Goal]) -> List[Goal]:
        """Prioriza metas baseado em impacto e dificuldade"""
        
        def priority_score(goal: Goal) -> tuple:
            # Ordem: Priority enum value, improvement needed (menor = mais fácil)
            priority_order = {
                Priority.CRITICAL: 0,
                Priority.HIGH: 1,
                Priority.MEDIUM: 2,
                Priority.LOW: 3
            }
            
            return (priority_order[goal.priority], goal.improvement_percentage)
        
        return sorted(goals, key=priority_score)
    
    def _goal_to_dict(self, goal: Goal) -> Dict[str, Any]:
        """Converte Goal para dicionário serializável"""
        return {
            'metric': goal.metric.value,
            'current_value': goal.current_value,
            'target_value': goal.target_value,
            'priority': goal.priority.value,
            'deadline': goal.deadline,
            'description': goal.description,
            'business_impact': goal.business_impact,
            'success_criteria': goal.success_criteria
        }
    
    def _dict_to_goal(self, data: Dict[str, Any]) -> Goal:
        """Converte dicionário para Goal"""
        return Goal(
            metric=MetricType(data['metric']),
            current_value=data['current_value'],
            target_value=data['target_value'],
            priority=Priority(data['priority']),
            deadline=data['deadline'],
            description=data['description'],
            business_impact=data['business_impact'],
            success_criteria=data['success_criteria']
        )
    
    def set_goals(self, goals: List[Goal]):
        """Define nova lista de metas"""
        self.goals = goals
        self.save_goals()
        print(f"✅ {len(goals)} metas definidas")
    
    def update_progress(self, new_metrics: Dict[str, float]) -> Dict[str, Any]:
        """Atualiza progresso das metas com novas métricas"""
        
        progress_report = {
            'timestamp': datetime.now().isoformat(),
            'goals_progress': [],
            'summary': {
                'total_goals': len(self.goals),
                'completed': 0,
                'on_track': 0,
                'at_risk': 0,
                'failed': 0
            }
        }
        
        for goal in self.goals:
            metric_key = goal.metric.value
            
            # Mapear nomes de métricas se necessário
            if metric_key == 'confident_accuracy':
                metric_key = 'confident_accuracy_0.8'
            
            if metric_key in new_metrics:
                new_value = new_metrics[metric_key]
                progress = goal.progress_score(new_value)
                
                # Determinar status
                if progress >= 100:
                    status = "completed"
                    progress_report['summary']['completed'] += 1
                elif progress >= 75:
                    status = "on_track"
                    progress_report['summary']['on_track'] += 1
                elif progress >= 25:
                    status = "at_risk"
                    progress_report['summary']['at_risk'] += 1
                else:
                    status = "failed"
                    progress_report['summary']['failed'] += 1
                
                goal_progress = {
                    'metric': goal.metric.value,
                    'description': goal.description,
                    'current_value': goal.current_value,
                    'new_value': new_value,
                    'target_value': goal.target_value,
                    'progress_percentage': progress,
                    'status': status,
                    'deadline': goal.deadline,
                    'priority': goal.priority.value
                }
                
                progress_report['goals_progress'].append(goal_progress)
        
        return progress_report
    
    def generate_action_plan(self, progress_report: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Gera plano de ação baseado no progresso das metas"""
        
        actions = []
        
        # Análise por status
        for goal_progress in progress_report['goals_progress']:
            metric = goal_progress['metric']
            status = goal_progress['status']
            progress = goal_progress['progress_percentage']
            
            if status == "failed" or (status == "at_risk" and progress < 50):
                if metric == "auc_roc":
                    actions.append({
                        'priority': 'HIGH',
                        'action': 'Feature Engineering Intensivo',
                        'description': 'Adicionar features de interação entre champions e meta-patch',
                        'estimated_effort': '2-3 semanas',
                        'expected_impact': 'AUC +0.03-0.05'
                    })
                elif metric == "log_loss":
                    actions.append({
                        'priority': 'HIGH',
                        'action': 'Calibração de Modelo',
                        'description': 'Implementar Platt Scaling ou Isotonic Regression',
                        'estimated_effort': '1 semana',
                        'expected_impact': 'Log-Loss -0.05-0.1'
                    })
                elif metric == "inference_time_ms":
                    actions.append({
                        'priority': 'MEDIUM',
                        'action': 'Otimização de Performance',
                        'description': 'Model quantization e feature selection',
                        'estimated_effort': '1-2 semanas',
                        'expected_impact': 'Tempo -50-70%'
                    })
        
        # Ações gerais baseadas no resumo
        summary = progress_report['summary']
        if summary['failed'] > summary['completed']:
            actions.append({
                'priority': 'CRITICAL',
                'action': 'Revisão Arquitetural',
                'description': 'Considerar mudança de algoritmo (e.g., LightGBM -> Neural Network)',
                'estimated_effort': '3-4 semanas',
                'expected_impact': 'Melhoria geral de 10-20%'
            })
        
        return actions
    
    def save_goals(self, filepath: str = "data/goals.json"):
        """Salva metas em arquivo"""
        goals_data = {
            'goals': [self._goal_to_dict(goal) for goal in self.goals],
            'updated_at': datetime.now().isoformat()
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(goals_data, f, indent=2, ensure_ascii=False)
        print(f"💾 Metas salvas em: {filepath}")
    
    def load_goals(self, filepath: str = "data/goals.json") -> List[Goal]:
        """Carrega metas de arquivo"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            goals = [self._dict_to_goal(goal_data) for goal_data in data['goals']]
            print(f"✅ {len(goals)} metas carregadas")
            return goals
        except FileNotFoundError:
            print(f"⚠️ Arquivo {filepath} não encontrado")
            return []
        except Exception as e:
            print(f"❌ Erro ao carregar metas: {e}")
            return []
    
    def print_goals_summary(self):
        """Imprime resumo das metas"""
        print("\n" + "="*70)
        print("🎯 METAS DEFINIDAS PARA MELHORIA DO MODELO")
        print("="*70)
        
        for i, goal in enumerate(self.goals, 1):
            print(f"\n{i}. {goal.description}")
            print(f"   📊 Métrica: {goal.metric.value}")
            print(f"   📈 Atual → Alvo: {goal.current_value:.3f} → {goal.target_value:.3f}")
            print(f"   🚨 Prioridade: {goal.priority.value.upper()}")
            print(f"   📅 Prazo: {goal.deadline[:10]}")
            print(f"   💰 Impacto: {goal.business_impact}")
            print(f"   ✅ Critério: {goal.success_criteria}")

# Exemplo de uso
if __name__ == "__main__":
    # Métricas atuais exemplo
    current_metrics = {
        'auc_roc': 0.78,
        'log_loss': 0.52,
        'accuracy': 0.73,
        'inference_time_ms': 150,
        'confident_accuracy_0.8': 0.81,
        'brier_score': 0.28,
        'ece': 0.12
    }
    
    # Criar gerenciador de metas
    goals_manager = GoalsManager()
    
    # Definir metas baseadas nas métricas atuais
    goals = goals_manager.define_advanced_goals(current_metrics)
    goals_manager.set_goals(goals)
    
    # Imprimir resumo
    goals_manager.print_goals_summary()
    
    print(f"\n📄 Metas salvas em: {goals_manager.goals_file}") 