"""
Gerador de Dashboard HTML - Semana 4
Gera dashboard interativo em tempo real para monitoramento do Bot LoL V3

Funcionalidades:
- Dashboard HTML responsivo
- Gráficos interativos com Chart.js
- Métricas em tempo real
- Alertas visuais
- Relatórios exportáveis
"""

from __future__ import annotations

import json
import time
from typing import Dict, Any, List
from datetime import datetime, timedelta
from pathlib import Path

from ..utils.logger_config import get_logger

logger = get_logger(__name__)


class DashboardGenerator:
    """
    Gerador de Dashboard para Bot LoL V3 Ultra Avançado
    
    Funcionalidades:
    - HTML responsivo com Bootstrap
    - Gráficos interativos com Chart.js
    - Auto-refresh em tempo real
    - Exportação de relatórios
    - Design profissional
    """

    def __init__(self):
        """Inicializa o gerador de dashboard"""
        self.template_cache = {}
        logger.info("DashboardGenerator inicializado para Semana 4")

    def generate_html_dashboard(self, dashboard_data: Dict[str, Any]) -> str:
        """
        Gera dashboard completo em HTML
        
        Args:
            dashboard_data: Dados do PerformanceMonitor
            
        Returns:
            HTML completo do dashboard
        """
        try:
            # Valida e sanitiza dados de entrada
            dashboard_data = self._validate_dashboard_data(dashboard_data)
            
            # Extrai métricas principais
            current_metrics = dashboard_data.get("current_metrics", {})
            last_24h = dashboard_data.get("last_24h", {})
            method_performance = dashboard_data.get("method_performance", {})
            active_alerts = dashboard_data.get("active_alerts", [])
            analysis_usage = dashboard_data.get("analysis_usage", {})
            trend = dashboard_data.get("trend", {})
            
            # Gera HTML completo
            html = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bot LoL V3 Ultra Avançado - Dashboard</title>
    
    <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    
    <!-- Chart.js -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    
    <style>
        {self._get_custom_css()}
    </style>
</head>
<body>
    <div class="container-fluid">
        <!-- Header -->
        <div class="row mb-4">
            <div class="col-12">
                <div class="dashboard-header">
                    <h1><i class="fas fa-robot"></i> Bot LoL V3 Ultra Avançado</h1>
                    <p class="lead">Dashboard de Monitoramento em Tempo Real - Semana 4</p>
                    <div class="status-indicator">
                        <span class="badge bg-success fs-6">
                            <i class="fas fa-circle"></i> Online - {dashboard_data.get('uptime_hours', 0):.1f}h uptime
                        </span>
                        <span class="text-muted">Última atualização: {datetime.now().strftime('%H:%M:%S')}</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- Métricas Principais -->
        <div class="row mb-4">
            <div class="col-md-3">
                <div class="metric-card win-rate">
                    <div class="metric-icon">
                        <i class="fas fa-trophy"></i>
                    </div>
                    <div class="metric-content">
                        <h3>{current_metrics.get('win_rate', 0):.1f}%</h3>
                        <p>Win Rate</p>
                        <small class="metric-change">
                            {self._format_trend_indicator(trend.get('win_rate_trend', []))}
                        </small>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="metric-card roi">
                    <div class="metric-icon">
                        <i class="fas fa-chart-line"></i>
                    </div>
                    <div class="metric-content">
                        <h3>{current_metrics.get('roi', 0):.1f}%</h3>
                        <p>ROI</p>
                        <small class="metric-change">
                            {self._format_trend_indicator(trend.get('roi_trend', []))}
                        </small>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="metric-card profit">
                    <div class="metric-icon">
                        <i class="fas fa-dollar-sign"></i>
                    </div>
                    <div class="metric-content">
                        <h3>R$ {current_metrics.get('net_profit', 0):.2f}</h3>
                        <p>Lucro Líquido</p>
                        <small class="metric-change">
                            24h: R$ {last_24h.get('profit', 0):.2f}
                        </small>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="metric-card predictions">
                    <div class="metric-icon">
                        <i class="fas fa-brain"></i>
                    </div>
                    <div class="metric-content">
                        <h3>{current_metrics.get('total_predictions', 0)}</h3>
                        <p>Predições Total</p>
                        <small class="metric-change">
                            24h: {last_24h.get('predictions', 0)} | Pendentes: {last_24h.get('pending', 0)}
                        </small>
                    </div>
                </div>
            </div>
        </div>

        <!-- Alertas Ativos -->
        {self._generate_alerts_section(active_alerts)}

        <!-- Gráficos e Análises -->
        <div class="row mb-4">
            <div class="col-md-8">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-chart-area"></i> Performance Temporal</h5>
                    </div>
                    <div class="card-body">
                        <canvas id="performanceChart" height="100"></canvas>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-cogs"></i> Performance por Método</h5>
                    </div>
                    <div class="card-body">
                        <canvas id="methodChart"></canvas>
                    </div>
                </div>
            </div>
        </div>

        <!-- Análises Avançadas -->
        <div class="row mb-4">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-puzzle-piece"></i> Análises de Composição & Patch</h5>
                    </div>
                    <div class="card-body">
                        <div class="analysis-stats">
                            <div class="stat-item">
                                <span class="stat-label">Análises de Composição:</span>
                                <span class="stat-value">{analysis_usage.get('composition_analyses', 0)}</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-label">Análises de Patch:</span>
                                <span class="stat-value">{analysis_usage.get('patch_analyses', 0)}</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-label">Tempo Médio de Processamento:</span>
                                <span class="stat-value">{analysis_usage.get('avg_processing_time', 0):.0f}ms</span>
                            </div>
                        </div>
                        <div class="progress mt-3">
                            <div class="progress-bar bg-info" role="progressbar" 
                                 style="width: {min(100, analysis_usage.get('avg_processing_time', 0) / 50)}%"
                                 aria-valuenow="{analysis_usage.get('avg_processing_time', 0)}" 
                                 aria-valuemin="0" aria-valuemax="5000">
                                Performance
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-list"></i> Resumo Últimas 24h</h5>
                    </div>
                    <div class="card-body">
                        <ul class="list-group list-group-flush">
                            <li class="list-group-item d-flex justify-content-between">
                                <span>Predições Geradas</span>
                                <strong>{last_24h.get('predictions', 0)}</strong>
                            </li>
                            <li class="list-group-item d-flex justify-content-between">
                                <span>Predições Resolvidas</span>
                                <strong>{last_24h.get('resolved', 0)}</strong>
                            </li>
                            <li class="list-group-item d-flex justify-content-between">
                                <span>Pendentes</span>
                                <strong class="text-warning">{last_24h.get('pending', 0)}</strong>
                            </li>
                            <li class="list-group-item d-flex justify-content-between">
                                <span>Lucro/Prejuízo</span>
                                <strong class="{'text-success' if last_24h.get('profit', 0) >= 0 else 'text-danger'}">
                                    R$ {last_24h.get('profit', 0):+.2f}
                                </strong>
                            </li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>

        <!-- Detalhes de Performance por Método -->
        <div class="row mb-4">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-microscope"></i> Performance Detalhada por Método</h5>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            {self._generate_method_details(method_performance)}
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Footer -->
        <div class="row">
            <div class="col-12">
                <div class="card bg-dark text-white">
                    <div class="card-body text-center">
                        <p class="mb-0">
                            <i class="fas fa-robot"></i> Bot LoL V3 Ultra Avançado - Semana 4
                            | Sistema de Monitoramento em Produção
                            | Última atualização: {dashboard_data.get('timestamp', '')}
                        </p>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Scripts -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        {self._generate_chart_scripts(trend, method_performance)}
        
        // Controle de scroll e auto-refresh melhorado
        let isScrolling = false;
        let scrollTimeout = null;
        let refreshTimer = null;
        
        // Detecta quando o usuário está fazendo scroll
        window.addEventListener('scroll', function() {{
            isScrolling = true;
            
            // Cancela refresh se usuário estiver scrollando
            if (refreshTimer) {{
                clearTimeout(refreshTimer);
            }}
            
            // Reseta scroll detector após 3 segundos
            clearTimeout(scrollTimeout);
            scrollTimeout = setTimeout(function() {{
                isScrolling = false;
                // Reagenda refresh apenas se não estiver scrollando
                scheduleRefresh();
            }}, 3000);
        }});
        
        // Função para agendar refresh inteligente
        function scheduleRefresh() {{
            if (refreshTimer) clearTimeout(refreshTimer);
            
            refreshTimer = setTimeout(function() {{
                // Só faz refresh se não estiver scrollando
                if (!isScrolling) {{
                    // Salva posição do scroll antes de recarregar
                    sessionStorage.setItem('dashboardScrollPos', window.scrollY);
                    location.reload();
                }} else {{
                    // Reagenda para mais tarde se estiver scrollando
                    scheduleRefresh();
                }}
            }}, 30000);
        }}
        
        // Restaura posição do scroll após carregamento
        window.addEventListener('load', function() {{
            const savedScrollPos = sessionStorage.getItem('dashboardScrollPos');
            if (savedScrollPos) {{
                window.scrollTo(0, parseInt(savedScrollPos));
                sessionStorage.removeItem('dashboardScrollPos');
            }}
        }});
        
        // Inicia agendamento inicial
        scheduleRefresh();
    </script>
</body>
</html>
            """
            
            return html
            
        except Exception as e:
            logger.error(f"Erro ao gerar dashboard HTML: {e}")
            return self._generate_error_dashboard(str(e))

    def _get_custom_css(self) -> str:
        """CSS customizado para o dashboard"""
        return """
        body {
            background-color: #f8f9fa;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            overflow-x: hidden; /* Previne scroll horizontal */
            scroll-behavior: smooth; /* Scroll suave */
        }
        
        html, body {
            max-width: 100%;
            box-sizing: border-box;
        }
        
        *, *::before, *::after {
            box-sizing: inherit;
        }
        
        .container-fluid {
            max-width: 100%;
            padding-left: 1rem;
            padding-right: 1rem;
            margin: 0 auto;
        }
        
        .dashboard-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            border-radius: 10px;
            margin-bottom: 2rem;
            text-align: center;
            max-width: 100%;
            box-sizing: border-box;
        }
        
        .status-indicator {
            margin-top: 1rem;
        }
        
        .metric-card {
            background: white;
            border-radius: 15px;
            padding: 1.5rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            margin-bottom: 1rem;
            transition: transform 0.2s;
            height: 140px;
            display: flex;
            align-items: center;
            max-width: 100%;
            overflow: hidden; /* Previne overflow */
        }
        
        .metric-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 15px rgba(0, 0, 0, 0.15);
        }
        
        .metric-icon {
            font-size: 2.5rem;
            margin-right: 1rem;
            width: 60px;
            text-align: center;
            flex-shrink: 0; /* Previne encolhimento */
        }
        
        .metric-content {
            flex: 1;
            overflow: hidden; /* Previne overflow de texto */
        }
        
        .metric-content h3 {
            margin: 0;
            font-size: 2.2rem;
            font-weight: bold;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        
        .metric-content p {
            margin: 0;
            color: #6c757d;
            font-weight: 500;
        }
        
        .metric-change {
            font-size: 0.8rem;
        }
        
        .win-rate .metric-icon { color: #28a745; }
        .roi .metric-icon { color: #007bff; }
        .profit .metric-icon { color: #ffc107; }
        .predictions .metric-icon { color: #6f42c1; }
        
        .alert-section {
            margin-bottom: 2rem;
        }
        
        .card {
            border: none;
            border-radius: 15px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            margin-bottom: 1rem;
            max-width: 100%;
            overflow: hidden; /* Previne overflow */
        }
        
        .card-header {
            background-color: #f8f9fa;
            border-bottom: 1px solid #dee2e6;
            border-radius: 15px 15px 0 0 !important;
            font-weight: 600;
        }
        
        .card-body {
            max-width: 100%;
            overflow: hidden; /* Previne overflow */
        }
        
        /* Canvas dos gráficos */
        canvas {
            max-width: 100% !important;
            height: auto !important;
            box-sizing: border-box;
        }
        
        .analysis-stats .stat-item {
            display: flex;
            justify-content: space-between;
            padding: 0.5rem 0;
            border-bottom: 1px solid #f0f0f0;
            max-width: 100%;
            overflow: hidden;
        }
        
        .stat-label {
            color: #6c757d;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            flex: 1;
        }
        
        .stat-value {
            font-weight: bold;
            color: #495057;
            white-space: nowrap;
            margin-left: 1rem;
        }
        
        .method-detail {
            text-align: center;
            padding: 1rem;
            background: #f8f9fa;
            border-radius: 10px;
            margin-bottom: 1rem;
            max-width: 100%;
            overflow: hidden;
        }
        
        .method-detail h6 {
            color: #495057;
            margin-bottom: 0.5rem;
        }
        
        .method-stats {
            font-size: 0.9rem;
            color: #6c757d;
        }
        
        .trend-up { color: #28a745; }
        .trend-down { color: #dc3545; }
        .trend-neutral { color: #6c757d; }
        
        /* Responsividade melhorada */
        @media (max-width: 768px) {
            .metric-card {
                height: auto;
                flex-direction: column;
                text-align: center;
                padding: 1rem;
            }
            
            .metric-icon {
                margin-right: 0;
                margin-bottom: 1rem;
            }
            
            .container-fluid {
                padding-left: 0.5rem;
                padding-right: 0.5rem;
            }
            
            .dashboard-header {
                padding: 1.5rem;
            }
        }
        
        /* Previne problemas com row/col */
        .row {
            margin-left: -0.75rem;
            margin-right: -0.75rem;
        }
        
        .row > * {
            padding-left: 0.75rem;
            padding-right: 0.75rem;
        }
        
        /* Scroll customizado */
        ::-webkit-scrollbar {
            width: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: #f1f1f1;
            border-radius: 10px;
        }
        
        ::-webkit-scrollbar-thumb {
            background: #888;
            border-radius: 10px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: #555;
        }
        """

    def _generate_alerts_section(self, alerts: List[Dict]) -> str:
        """Gera seção de alertas"""
        if not alerts:
            return """
            <div class="row mb-4 alert-section">
                <div class="col-12">
                    <div class="alert alert-success" role="alert">
                        <i class="fas fa-check-circle"></i> Nenhum alerta ativo - Sistema funcionando normalmente
                    </div>
                </div>
            </div>
            """
        
        alerts_html = '<div class="row mb-4 alert-section"><div class="col-12">'
        
        for alert in alerts:
            level_classes = {
                "info": "alert-info",
                "warning": "alert-warning", 
                "error": "alert-danger",
                "critical": "alert-danger"
            }
            
            level_icons = {
                "info": "fa-info-circle",
                "warning": "fa-exclamation-triangle",
                "error": "fa-times-circle",
                "critical": "fa-skull-crossbones"
            }
            
            alert_class = level_classes.get(alert["level"], "alert-secondary")
            alert_icon = level_icons.get(alert["level"], "fa-bell")
            
            alerts_html += f"""
            <div class="alert {alert_class}" role="alert">
                <i class="fas {alert_icon}"></i> 
                <strong>{alert["level"].upper()}:</strong> {alert["message"]}
                <small class="float-end">{alert["category"]} - {alert["timestamp"]}</small>
            </div>
            """
        
        alerts_html += '</div></div>'
        return alerts_html

    def _generate_method_details(self, method_performance: Dict) -> str:
        """Gera detalhes de performance por método"""
        methods_html = ""
        
        method_configs = {
            "ml": {"name": "Machine Learning", "icon": "fa-brain", "color": "#007bff"},
            "algorithm": {"name": "Algoritmos", "icon": "fa-calculator", "color": "#28a745"},
            "hybrid": {"name": "Híbrido", "icon": "fa-cogs", "color": "#6f42c1"}
        }
        
        for method_key, config in method_configs.items():
            method_data = method_performance.get(method_key, {})
            predictions = method_data.get("predictions", 0)
            win_rate = method_data.get("win_rate", 0)
            
            methods_html += f"""
            <div class="col-md-4">
                <div class="method-detail">
                    <i class="fas {config['icon']}" style="color: {config['color']}; font-size: 2rem;"></i>
                    <h6>{config['name']}</h6>
                    <div class="method-stats">
                        <div><strong>{predictions}</strong> predições</div>
                        <div><strong>{win_rate:.1f}%</strong> win rate</div>
                    </div>
                </div>
            </div>
            """
        
        return methods_html

    def _format_trend_indicator(self, trend_data: List[float]) -> str:
        """Formata indicador de tendência"""
        if len(trend_data) < 2:
            return '<span class="trend-neutral"><i class="fas fa-minus"></i> Neutro</span>'
        
        recent = trend_data[-1]
        previous = trend_data[-2]
        
        if recent > previous:
            return '<span class="trend-up"><i class="fas fa-arrow-up"></i> Subindo</span>'
        elif recent < previous:
            return '<span class="trend-down"><i class="fas fa-arrow-down"></i> Descendo</span>'
        else:
            return '<span class="trend-neutral"><i class="fas fa-minus"></i> Estável</span>'

    def _generate_chart_scripts(self, trend: Dict, method_performance: Dict) -> str:
        """Gera scripts JavaScript para os gráficos"""
        win_rate_trend = trend.get("win_rate_trend", [])
        roi_trend = trend.get("roi_trend", [])
        
        # Dados para gráfico de métodos
        methods = ["ML", "Algoritmos", "Híbrido"]
        method_win_rates = [
            method_performance.get("ml", {}).get("win_rate", 0),
            method_performance.get("algorithm", {}).get("win_rate", 0),
            method_performance.get("hybrid", {}).get("win_rate", 0)
        ]
        method_predictions = [
            method_performance.get("ml", {}).get("predictions", 0),
            method_performance.get("algorithm", {}).get("predictions", 0),
            method_performance.get("hybrid", {}).get("predictions", 0)
        ]
        
        return f"""
        // Configurações globais do Chart.js para evitar problemas
        Chart.defaults.responsive = true;
        Chart.defaults.maintainAspectRatio = false;
        Chart.defaults.plugins.legend.display = true;
        Chart.defaults.animation.duration = 300; // Animação mais rápida
        
        // Aguarda o DOM estar pronto
        document.addEventListener('DOMContentLoaded', function() {{
            
            // Gráfico de Performance Temporal
            const performanceCanvas = document.getElementById('performanceChart');
            if (performanceCanvas) {{
                const performanceCtx = performanceCanvas.getContext('2d');
                
                // Define altura fixa para evitar problemas
                performanceCanvas.style.height = '400px';
                performanceCanvas.height = 400;
                
                new Chart(performanceCtx, {{
                    type: 'line',
                    data: {{
                        labels: {json.dumps([f"T-{i}" for i in range(len(win_rate_trend)-1, -1, -1)])},
                        datasets: [{{
                            label: 'Win Rate (%)',
                            data: {json.dumps(win_rate_trend)},
                            borderColor: '#28a745',
                            backgroundColor: 'rgba(40, 167, 69, 0.1)',
                            tension: 0.4,
                            yAxisID: 'y',
                            pointRadius: 3,
                            pointHoverRadius: 5
                        }}, {{
                            label: 'ROI (%)',
                            data: {json.dumps(roi_trend)},
                            borderColor: '#007bff',
                            backgroundColor: 'rgba(0, 123, 255, 0.1)',
                            tension: 0.4,
                            yAxisID: 'y1',
                            pointRadius: 3,
                            pointHoverRadius: 5
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        layout: {{
                            padding: {{
                                left: 10,
                                right: 10,
                                top: 10,
                                bottom: 10
                            }}
                        }},
                        interaction: {{
                            mode: 'index',
                            intersect: false,
                        }},
                        animation: {{
                            duration: 300
                        }},
                        scales: {{
                            y: {{
                                type: 'linear',
                                display: true,
                                position: 'left',
                                title: {{
                                    display: true,
                                    text: 'Win Rate (%)'
                                }},
                                grid: {{
                                    display: true,
                                    drawBorder: true
                                }}
                            }},
                            y1: {{
                                type: 'linear',
                                display: true,
                                position: 'right',
                                title: {{
                                    display: true,
                                    text: 'ROI (%)'
                                }},
                                grid: {{
                                    drawOnChartArea: false,
                                }},
                            }}
                        }},
                        plugins: {{
                            legend: {{
                                display: true,
                                position: 'top'
                            }}
                        }}
                    }}
                }});
            }}
            
            // Gráfico de Performance por Método
            const methodCanvas = document.getElementById('methodChart');
            if (methodCanvas) {{
                const methodCtx = methodCanvas.getContext('2d');
                
                // Define altura fixa para evitar problemas
                methodCanvas.style.height = '300px';
                methodCanvas.height = 300;
                
                new Chart(methodCtx, {{
                    type: 'doughnut',
                    data: {{
                        labels: {json.dumps(methods)},
                        datasets: [{{
                            label: 'Predições',
                            data: {json.dumps(method_predictions)},
                            backgroundColor: [
                                '#007bff',
                                '#28a745', 
                                '#6f42c1'
                            ],
                            borderWidth: 2,
                            borderColor: '#ffffff'
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        layout: {{
                            padding: 20
                        }},
                        animation: {{
                            duration: 300
                        }},
                        plugins: {{
                            legend: {{
                                position: 'bottom',
                                labels: {{
                                    padding: 20,
                                    usePointStyle: true
                                }}
                            }},
                            tooltip: {{
                                callbacks: {{
                                    afterLabel: function(context) {{
                                        const winRates = {json.dumps(method_win_rates)};
                                        return 'Win Rate: ' + winRates[context.dataIndex].toFixed(1) + '%';
                                    }}
                                }}
                            }}
                        }}
                    }}
                }});
            }}
        }});
        
        // Redimensiona gráficos quando necessário
        window.addEventListener('resize', function() {{
            Chart.instances.forEach(function(chart) {{
                chart.resize();
            }});
        }});
        """

    def _generate_error_dashboard(self, error_message: str) -> str:
        """Gera dashboard de erro"""
        return f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard - Erro</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <div class="container mt-5">
        <div class="alert alert-danger" role="alert">
            <h4 class="alert-heading">Erro no Dashboard</h4>
            <p>{error_message}</p>
            <hr>
            <p class="mb-0">Verifique os logs do sistema para mais detalhes.</p>
        </div>
    </div>
</body>
</html>
        """

    def export_dashboard_to_file(self, dashboard_data: Dict[str, Any], output_path: str = "dashboard.html") -> bool:
        """
        Exporta dashboard para arquivo HTML
        
        Args:
            dashboard_data: Dados do dashboard
            output_path: Caminho do arquivo de saída
            
        Returns:
            True se exportado com sucesso
        """
        try:
            html_content = self.generate_html_dashboard(dashboard_data)
            
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            
            logger.info(f"Dashboard exportado para: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao exportar dashboard: {e}")
            return False

    def generate_performance_report_html(self, report_data: Dict[str, Any]) -> str:
        """
        Gera relatório de performance em HTML
        
        Args:
            report_data: Dados do relatório do PerformanceMonitor
            
        Returns:
            HTML do relatório
        """
        try:
            overall = report_data.get("overall", {})
            by_method = report_data.get("by_method", {})
            by_confidence = report_data.get("by_confidence", {})
            daily_breakdown = report_data.get("daily_breakdown", [])
            
            html = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Relatório de Performance - Bot LoL V3</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {{ background-color: #f8f9fa; }}
        .report-header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 2rem; border-radius: 10px; margin-bottom: 2rem; }}
        .metric-highlight {{ font-size: 1.5rem; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container mt-4">
        <div class="report-header text-center">
            <h1>Relatório de Performance</h1>
            <p>Período: {report_data.get('period_start', '')} a {report_data.get('period_end', '')}</p>
            <p>({report_data.get('period_days', 0)} dias)</p>
        </div>
        
        <!-- Métricas Principais -->
        <div class="row mb-4">
            <div class="col-md-3">
                <div class="card text-center">
                    <div class="card-body">
                        <h5 class="card-title">Predições</h5>
                        <p class="metric-highlight text-primary">{overall.get('total_predictions', 0)}</p>
                        <small class="text-muted">{overall.get('correct_predictions', 0)} corretas</small>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card text-center">
                    <div class="card-body">
                        <h5 class="card-title">Win Rate</h5>
                        <p class="metric-highlight text-success">{overall.get('win_rate_percentage', 0):.1f}%</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card text-center">
                    <div class="card-body">
                        <h5 class="card-title">ROI</h5>
                        <p class="metric-highlight text-info">{overall.get('roi_percentage', 0):.1f}%</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card text-center">
                    <div class="card-body">
                        <h5 class="card-title">Lucro Líquido</h5>
                        <p class="metric-highlight {'text-success' if overall.get('net_profit', 0) >= 0 else 'text-danger'}">
                            R$ {overall.get('net_profit', 0):.2f}
                        </p>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Performance por Método -->
        <div class="card mb-4">
            <div class="card-header">
                <h5>Performance por Método</h5>
            </div>
            <div class="card-body">
                <div class="table-responsive">
                    <table class="table table-striped">
                        <thead>
                            <tr>
                                <th>Método</th>
                                <th>Predições</th>
                                <th>Corretas</th>
                                <th>Win Rate</th>
                                <th>Lucro</th>
                            </tr>
                        </thead>
                        <tbody>
            """
            
            for method, data in by_method.items():
                html += f"""
                            <tr>
                                <td><strong>{method.upper()}</strong></td>
                                <td>{data.get('predictions', 0)}</td>
                                <td>{data.get('correct', 0)}</td>
                                <td>{data.get('win_rate', 0):.1f}%</td>
                                <td class="{'text-success' if data.get('profit', 0) >= 0 else 'text-danger'}">
                                    R$ {data.get('profit', 0):.2f}
                                </td>
                            </tr>
                """
            
            html += """
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        
        <!-- Análise Diária -->
        <div class="card mb-4">
            <div class="card-header">
                <h5>Breakdown Diário</h5>
            </div>
            <div class="card-body">
                <div class="table-responsive">
                    <table class="table table-sm">
                        <thead>
                            <tr>
                                <th>Data</th>
                                <th>Predições</th>
                                <th>Win Rate</th>
                                <th>Lucro</th>
                            </tr>
                        </thead>
                        <tbody>
            """
            
            for day in daily_breakdown[:7]:  # Últimos 7 dias
                html += f"""
                            <tr>
                                <td>{day.get('date', '')}</td>
                                <td>{day.get('predictions', 0)}</td>
                                <td>{day.get('win_rate', 0):.1f}%</td>
                                <td class="{'text-success' if day.get('profit', 0) >= 0 else 'text-danger'}">
                                    R$ {day.get('profit', 0):.2f}
                                </td>
                            </tr>
                """
            
            html += f"""
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        
        <div class="text-center mb-4">
            <small class="text-muted">
                Relatório gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}
            </small>
        </div>
    </div>
</body>
</html>
            """
            
            return html
            
        except Exception as e:
            logger.error(f"Erro ao gerar relatório HTML: {e}")
            return f"<html><body><h1>Erro: {e}</h1></body></html>" 

    def _validate_dashboard_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valida e sanitiza dados do dashboard para evitar problemas de renderização
        
        Args:
            data: Dados originais do dashboard
            
        Returns:
            Dados validados e sanitizados
        """
        try:
            # Cria cópia dos dados para não modificar original
            validated_data = {}
            
            # Valida métricas principais
            current_metrics = data.get("current_metrics", {})
            validated_data["current_metrics"] = {
                "win_rate": self._safe_float(current_metrics.get("win_rate", 0), 0, 100),
                "roi": self._safe_float(current_metrics.get("roi", 0), -100, 1000),
                "net_profit": self._safe_float(current_metrics.get("net_profit", 0), -10000, 10000),
                "total_predictions": self._safe_int(current_metrics.get("total_predictions", 0), 0, 100000)
            }
            
            # Valida dados das últimas 24h
            last_24h = data.get("last_24h", {})
            validated_data["last_24h"] = {
                "predictions": self._safe_int(last_24h.get("predictions", 0), 0, 1000),
                "resolved": self._safe_int(last_24h.get("resolved", 0), 0, 1000),
                "pending": self._safe_int(last_24h.get("pending", 0), 0, 1000),
                "profit": self._safe_float(last_24h.get("profit", 0), -1000, 1000)
            }
            
            # Valida performance por método
            method_performance = data.get("method_performance", {})
            validated_data["method_performance"] = {}
            for method in ["ml", "algorithm", "hybrid"]:
                method_data = method_performance.get(method, {})
                validated_data["method_performance"][method] = {
                    "predictions": self._safe_int(method_data.get("predictions", 0), 0, 10000),
                    "win_rate": self._safe_float(method_data.get("win_rate", 0), 0, 100)
                }
            
            # Valida alertas (limita quantidade)
            active_alerts = data.get("active_alerts", [])
            if isinstance(active_alerts, list):
                validated_data["active_alerts"] = active_alerts[:10]  # Máximo 10 alertas
            else:
                validated_data["active_alerts"] = []
            
            # Valida dados de análise
            analysis_usage = data.get("analysis_usage", {})
            validated_data["analysis_usage"] = {
                "composition_analyses": self._safe_int(analysis_usage.get("composition_analyses", 0), 0, 10000),
                "patch_analyses": self._safe_int(analysis_usage.get("patch_analyses", 0), 0, 10000),
                "avg_processing_time": self._safe_float(analysis_usage.get("avg_processing_time", 0), 0, 10000)
            }
            
            # Valida dados de tendência (limita tamanho)
            trend = data.get("trend", {})
            validated_data["trend"] = {
                "win_rate_trend": self._safe_trend_array(trend.get("win_rate_trend", []), 0, 100),
                "roi_trend": self._safe_trend_array(trend.get("roi_trend", []), -100, 1000)
            }
            
            # Copia outros dados com validação básica
            validated_data["uptime_hours"] = self._safe_float(data.get("uptime_hours", 0), 0, 8760)  # Máx 1 ano
            validated_data["timestamp"] = str(data.get("timestamp", ""))[:50]  # Limita tamanho
            
            return validated_data
            
        except Exception as e:
            logger.error(f"Erro na validação de dados do dashboard: {e}")
            # Retorna dados padrão em caso de erro
            return self._get_default_dashboard_data()
    
    def _safe_float(self, value: Any, min_val: float = None, max_val: float = None) -> float:
        """Converte valor para float seguro"""
        try:
            result = float(value)
            
            # Verifica se é número válido
            if not isinstance(result, (int, float)) or result != result:  # NaN check
                return 0.0
            
            # Aplica limites se especificados
            if min_val is not None:
                result = max(result, min_val)
            if max_val is not None:
                result = min(result, max_val)
                
            return result
        except (ValueError, TypeError):
            return 0.0
    
    def _safe_int(self, value: Any, min_val: int = None, max_val: int = None) -> int:
        """Converte valor para int seguro"""
        try:
            result = int(float(value))
            
            # Aplica limites se especificados
            if min_val is not None:
                result = max(result, min_val)
            if max_val is not None:
                result = min(result, max_val)
                
            return result
        except (ValueError, TypeError):
            return 0
    
    def _safe_trend_array(self, arr: Any, min_val: float = None, max_val: float = None) -> List[float]:
        """Valida array de tendência"""
        try:
            if not isinstance(arr, list):
                return []
            
            # Limita tamanho do array para evitar problemas
            limited_arr = arr[-50:] if len(arr) > 50 else arr
            
            # Valida cada valor
            validated_arr = []
            for item in limited_arr:
                safe_val = self._safe_float(item, min_val, max_val)
                validated_arr.append(safe_val)
            
            return validated_arr
        except Exception:
            return []
    
    def _get_default_dashboard_data(self) -> Dict[str, Any]:
        """Retorna dados padrão do dashboard em caso de erro"""
        return {
            "current_metrics": {
                "win_rate": 0.0,
                "roi": 0.0,
                "net_profit": 0.0,
                "total_predictions": 0
            },
            "last_24h": {
                "predictions": 0,
                "resolved": 0,
                "pending": 0,
                "profit": 0.0
            },
            "method_performance": {
                "ml": {"predictions": 0, "win_rate": 0.0},
                "algorithm": {"predictions": 0, "win_rate": 0.0},
                "hybrid": {"predictions": 0, "win_rate": 0.0}
            },
            "active_alerts": [],
            "analysis_usage": {
                "composition_analyses": 0,
                "patch_analyses": 0,
                "avg_processing_time": 0.0
            },
            "trend": {
                "win_rate_trend": [],
                "roi_trend": []
            },
            "uptime_hours": 0.0,
            "timestamp": ""
        } 
