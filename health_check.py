#!/usr/bin/env python3
"""
Health Check Endpoint para Railway - Bot LoL V3

Endpoint simples para Railway verificar se o bot está funcionando.
"""

import os
import time
import json
import psutil
from flask import Flask, jsonify, render_template_string, send_from_directory
import threading
import asyncio
from datetime import datetime
from pathlib import Path

app = Flask(__name__)

# Status global do bot
bot_status = {
    "is_running": False,
    "start_time": time.time(),
    "last_heartbeat": time.time(),
    "version": "3.0.0",
    "environment": os.getenv("ENVIRONMENT", "development"),
    "total_requests": 0,
    "errors_count": 0
}

def update_heartbeat():
    """Atualiza heartbeat do bot"""
    global bot_status
    bot_status["last_heartbeat"] = time.time()

def set_bot_running(status: bool):
    """Define status do bot"""
    global bot_status
    bot_status["is_running"] = status
    update_heartbeat()

def increment_request_counter():
    """Incrementa contador de requests"""
    global bot_status
    bot_status["total_requests"] += 1

def increment_error_counter():
    """Incrementa contador de erros"""
    global bot_status
    bot_status["errors_count"] += 1

@app.route('/favicon.ico')
def favicon():
    """Favicon endpoint"""
    try:
        return send_from_directory(
            os.path.join(app.root_path, 'static'),
            'favicon.ico',
            mimetype='image/vnd.microsoft.icon'
        )
    except:
        # Retorna 204 No Content se não encontrar favicon
        return '', 204

@app.route('/dashboard')
def dashboard():
    """Dashboard web interativo com dados reais"""
    increment_request_counter()
    
    current_time = time.time()
    uptime = current_time - bot_status["start_time"]
    
    # Dados reais do sistema
    dashboard_data = get_real_dashboard_data(uptime)
    
    # Template HTML do dashboard
    dashboard_html = '''
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
        .metric-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 15px;
            color: white;
            padding: 1.5rem;
            margin-bottom: 1rem;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }
        
        .metric-card:hover {
            transform: translateY(-5px);
        }
        
        .metric-card.profit {
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        }
        
        .metric-card.profit.negative {
            background: linear-gradient(135deg, #ff5f6d 0%, #ffc371 100%);
        }
        
        .metric-card.predictions {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        
        .metric-card.win-rate {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }
        
        .metric-card.win-rate.high {
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        }
        
        .metric-card.roi {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        }
        
        .metric-card.roi.negative {
            background: linear-gradient(135deg, #ff5f6d 0%, #ffc371 100%);
        }
        
        .dashboard-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            border-radius: 15px;
            margin-bottom: 2rem;
            text-align: center;
        }
        
        .status-online {
            color: #28a745;
        }
        
        .status-offline {
            color: #dc3545;
        }
        
        .chart-container {
            background: white;
            border-radius: 15px;
            padding: 1.5rem;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            margin-bottom: 1rem;
        }
        
        .data-source {
            font-size: 0.8em;
            color: #6c757d;
            font-style: italic;
        }
    </style>
</head>
<body class="bg-light">
    <div class="container-fluid">
        <!-- Header -->
        <div class="row mb-4">
            <div class="col-12">
                <div class="dashboard-header">
                    <h1><i class="fas fa-robot"></i> {{ service }}</h1>
                    <p class="lead">Dashboard de Monitoramento em Tempo Real</p>
                    <div class="status-indicator">
                        <span class="badge bg-{% if running %}success{% else %}danger{% endif %} fs-6">
                            <i class="fas fa-circle"></i> {% if running %}Online{% else %}Offline{% endif %} - {{ uptime_hours }}h uptime
                        </span>
                        <span class="text-light">Última atualização: {{ current_time }}</span>
                    </div>
                    <div class="data-source mt-2">
                        <small>📊 Dados: {{ data_source }}</small>
                    </div>
                </div>
            </div>
        </div>

        <!-- Métricas Principais -->
        <div class="row mb-4">
            <div class="col-md-3">
                <div class="metric-card win-rate {% if win_rate >= 70 %}high{% endif %}">
                    <div class="text-center">
                        <i class="fas fa-trophy fa-2x mb-2"></i>
                        <h3>{{ win_rate }}%</h3>
                        <p class="mb-0">Win Rate</p>
                        <small class="data-source">{{ total_predictions }} predições</small>
                    </div>
                </div>
            </div>
            
            <div class="col-md-3">
                <div class="metric-card roi {% if roi < 0 %}negative{% endif %}">
                    <div class="text-center">
                        <i class="fas fa-chart-line fa-2x mb-2"></i>
                        <h3>{{ roi }}%</h3>
                        <p class="mb-0">ROI</p>
                        <small class="data-source">Return on Investment</small>
                    </div>
                </div>
            </div>
            
            <div class="col-md-3">
                <div class="metric-card profit {% if profit < 0 %}negative{% endif %}">
                    <div class="text-center">
                        <i class="fas fa-dollar-sign fa-2x mb-2"></i>
                        <h3>{{ profit_display }}</h3>
                        <p class="mb-0">{{ profit_label }}</p>
                        <small class="data-source">Total acumulado</small>
                    </div>
                </div>
            </div>
            
            <div class="col-md-3">
                <div class="metric-card predictions">
                    <div class="text-center">
                        <i class="fas fa-brain fa-2x mb-2"></i>
                        <h3>{{ total_predictions }}</h3>
                        <p class="mb-0">Predições</p>
                        <small class="data-source">{{ tips_generated }} tips geradas</small>
                    </div>
                </div>
            </div>
        </div>

        <!-- Status do Sistema -->
        <div class="row mb-4">
            <div class="col-md-6">
                <div class="chart-container">
                    <h5><i class="fas fa-heartbeat"></i> Status do Sistema</h5>
                    <div class="table-responsive">
                        <table class="table table-sm">
                            <tr>
                                <td><strong>Versão:</strong></td>
                                <td>{{ version }}</td>
                            </tr>
                            <tr>
                                <td><strong>Uptime:</strong></td>
                                <td>{{ uptime_hours }} horas</td>
                            </tr>
                            <tr>
                                <td><strong>Status:</strong></td>
                                <td><span class="{% if running %}status-online{% else %}status-offline{% endif %}">
                                    {% if running %}🟢 Online{% else %}🔴 Offline{% endif %}
                                </span></td>
                            </tr>
                            <tr>
                                <td><strong>Predições Corretas:</strong></td>
                                <td>{{ correct_predictions }}/{{ total_predictions }}</td>
                            </tr>
                            <tr>
                                <td><strong>Componentes:</strong></td>
                                <td><span class="{% if components_available %}status-online{% else %}status-offline{% endif %}">
                                    {% if components_available %}✅ Carregados{% else %}⚠️ Limitados{% endif %}
                                </span></td>
                            </tr>
                            <tr>
                                <td><strong>Tips Sistema:</strong></td>
                                <td>{{ tips_status }}</td>
                            </tr>
                        </table>
                    </div>
                </div>
            </div>
            
            <div class="col-md-6">
                <div class="chart-container">
                    <h5><i class="fas fa-chart-pie"></i> Performance</h5>
                    <canvas id="performanceChart" width="400" height="200"></canvas>
                </div>
            </div>
        </div>

        <!-- Métricas Detalhadas -->
        <div class="row mb-4">
            <div class="col-md-4">
                <div class="chart-container">
                    <h5><i class="fas fa-cogs"></i> Estatísticas do Sistema</h5>
                    <div class="table-responsive">
                        <table class="table table-sm">
                            <tr>
                                <td><strong>Requests:</strong></td>
                                <td>{{ total_requests }}</td>
                            </tr>
                            <tr>
                                <td><strong>Errors:</strong></td>
                                <td>{{ errors_count }}</td>
                            </tr>
                            <tr>
                                <td><strong>Success Rate:</strong></td>
                                <td>{{ success_rate }}%</td>
                            </tr>
                            <tr>
                                <td><strong>Análises Composições:</strong></td>
                                <td>{{ composition_analyses }}</td>
                            </tr>
                            <tr>
                                <td><strong>Análises Patches:</strong></td>
                                <td>{{ patch_analyses }}</td>
                            </tr>
                        </table>
                    </div>
                </div>
            </div>
            
            <div class="col-md-4">
                <div class="chart-container">
                    <h5><i class="fas fa-memory"></i> Recursos do Sistema</h5>
                    <div class="table-responsive">
                        <table class="table table-sm">
                            <tr>
                                <td><strong>CPU:</strong></td>
                                <td>{{ cpu_percent }}%</td>
                            </tr>
                            <tr>
                                <td><strong>Memória:</strong></td>
                                <td>{{ memory_percent }}%</td>
                            </tr>
                            <tr>
                                <td><strong>Disco:</strong></td>
                                <td>{{ disk_percent }}%</td>
                            </tr>
                            <tr>
                                <td><strong>Processos:</strong></td>
                                <td>{{ process_count }}</td>
                            </tr>
                        </table>
                    </div>
                </div>
            </div>
            
            <div class="col-md-4">
                <div class="chart-container">
                    <h5><i class="fas fa-clock"></i> Métricas de Tempo</h5>
                    <div class="table-responsive">
                        <table class="table table-sm">
                            <tr>
                                <td><strong>Última Predição:</strong></td>
                                <td>{{ last_prediction_time }}</td>
                            </tr>
                            <tr>
                                <td><strong>Última Tip:</strong></td>
                                <td>{{ last_tip_time }}</td>
                            </tr>
                            <tr>
                                <td><strong>Requests/hora:</strong></td>
                                <td>{{ requests_per_hour }}</td>
                            </tr>
                            <tr>
                                <td><strong>Ambiente:</strong></td>
                                <td>{{ environment }}</td>
                            </tr>
                        </table>
                    </div>
                </div>
            </div>
        </div>

        <!-- Links Úteis -->
        <div class="row mb-4">
            <div class="col-12">
                <div class="chart-container">
                    <h5><i class="fas fa-link"></i> API Endpoints</h5>
                    <div class="row">
                        <div class="col-md-3">
                            <a href="/health" class="btn btn-outline-success w-100 mb-2">
                                <i class="fas fa-heartbeat"></i> Health Check
                            </a>
                        </div>
                        <div class="col-md-3">
                            <a href="/status" class="btn btn-outline-info w-100 mb-2">
                                <i class="fas fa-info-circle"></i> Status Detalhado
                            </a>
                        </div>
                        <div class="col-md-3">
                            <a href="/metrics" class="btn btn-outline-warning w-100 mb-2">
                                <i class="fas fa-chart-bar"></i> Métricas
                            </a>
                        </div>
                        <div class="col-md-3">
                            <button onclick="location.reload()" class="btn btn-outline-primary w-100 mb-2">
                                <i class="fas fa-sync-alt"></i> Atualizar
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Footer -->
        <div class="row">
            <div class="col-12">
                <div class="chart-container bg-dark text-white text-center">
                    <p class="mb-0">
                        <i class="fas fa-robot"></i> Bot LoL V3 Ultra Avançado | Sistema de Monitoramento Railway
                        | Última atualização: {{ current_time }}
                    </p>
                </div>
            </div>
        </div>
    </div>

    <!-- Scripts -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // Gráfico de Performance
        const ctx = document.getElementById('performanceChart').getContext('2d');
        const performanceChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Predições Corretas', 'Predições Incorretas'],
                datasets: [{
                    data: [{{ correct_predictions }}, {{ total_predictions - correct_predictions }}],
                    backgroundColor: ['#28a745', '#dc3545'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const percentage = ((context.parsed / {{ total_predictions }}) * 100).toFixed(1);
                                return context.label + ': ' + context.parsed + ' (' + percentage + '%)';
                            }
                        }
                    }
                }
            }
        });
        
        // Auto-refresh a cada 30 segundos
        setTimeout(function() {
            location.reload();
        }, 30000);
        
        console.log('🚀 Dashboard Bot LoL V3 carregado com dados reais!');
    </script>
</body>
</html>
    '''
    
    # Renderiza template com dados reais
    try:
        from jinja2 import Template
        template = Template(dashboard_html)
        return template.render(**dashboard_data)
    except ImportError:
        # Fallback sem Jinja2 - substitui manualmente
        return render_dashboard_fallback(dashboard_html, dashboard_data)

def get_real_dashboard_data(uptime):
    """Coleta dados reais do sistema"""
    try:
        # Tenta importar e acessar componentes reais
        real_data = collect_system_metrics()
        data_source = "Sistema em Tempo Real"
        components_available = True
    except Exception as e:
        # Fallback para dados básicos se componentes não estão disponíveis
        real_data = get_fallback_metrics()
        data_source = "Dados Básicos (Componentes não carregados)"
        components_available = False
    
    # Processa dados para exibição
    profit = real_data.get('net_profit', 0.0)
    roi = real_data.get('roi_percentage', 0.0)
    
    # Formata valores monetários
    if profit >= 0:
        profit_display = f"R$ {profit:.1f}"
        profit_label = "Lucro Total"
    else:
        profit_display = f"R$ {abs(profit):.1f}"
        profit_label = "Prejuízo Total"
    
    # Calcula métricas de sistema
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        process_count = len(psutil.pids())
    except:
        cpu_percent = 0
        memory = type('obj', (object,), {'percent': 0})()
        disk = type('obj', (object,), {'used': 0, 'total': 1})()
        process_count = 0
    
    return {
        "service": "Bot LoL V3 Ultra Avançado",
        "version": bot_status["version"],
        "uptime_hours": round(uptime / 3600, 2),
        "total_predictions": real_data.get('total_predictions', 0),
        "correct_predictions": real_data.get('correct_predictions', 0),
        "win_rate": real_data.get('win_rate_percentage', 0.0),
        "roi": roi,
        "profit": profit,
        "profit_display": profit_display,
        "profit_label": profit_label,
        "tips_generated": real_data.get('tips_generated', 0),
        "running": bot_status["is_running"],
        "components_available": components_available,
        "current_time": datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
        "data_source": data_source,
        "tips_status": "✅ Ativo" if real_data.get('tips_system_active', False) else "⚠️ Inativo",
        "total_requests": bot_status["total_requests"],
        "errors_count": bot_status["errors_count"],
        "success_rate": round((bot_status["total_requests"] - bot_status["errors_count"]) / max(bot_status["total_requests"], 1) * 100, 2),
        "composition_analyses": real_data.get('composition_analyses', 0),
        "patch_analyses": real_data.get('patch_analyses', 0),
        "cpu_percent": round(cpu_percent, 1),
        "memory_percent": round(memory.percent, 1),
        "disk_percent": round((disk.used / disk.total) * 100, 1),
        "process_count": process_count,
        "last_prediction_time": real_data.get('last_prediction_time', 'Nunca'),
        "last_tip_time": real_data.get('last_tip_time', 'Nunca'),
        "requests_per_hour": round(bot_status["total_requests"] / max(uptime / 3600, 1), 1),
        "environment": bot_status["environment"]
    }

def collect_system_metrics():
    """Coleta métricas reais do sistema quando componentes estão disponíveis"""
    try:
        # Importa componentes do sistema
        from bot.core_logic.prediction_system import DynamicPredictionSystem
        from bot.systems.tips_system import ProfessionalTipsSystem
        from bot.monitoring.performance_monitor import PerformanceMonitor
        
        metrics = {}
        
        # Verifica se existe instância do sistema de predição
        # (Em produção, isso seria injetado ou acessado via singleton)
        
        # Por enquanto, simula busca de arquivos de dados/logs
        metrics_data = load_metrics_from_files()
        
        if metrics_data:
            return metrics_data
        else:
            # Se não há dados salvos, retorna métricas iniciais
            return {
                'total_predictions': 0,
                'correct_predictions': 0,
                'win_rate_percentage': 0.0,
                'roi_percentage': 0.0,
                'net_profit': 0.0,
                'tips_generated': 0,
                'tips_system_active': True,
                'composition_analyses': 0,
                'patch_analyses': 0,
                'last_prediction_time': 'Sistema iniciando...',
                'last_tip_time': 'Sistema iniciando...'
            }
    
    except ImportError as e:
        # Componentes não estão disponíveis
        raise Exception(f"Componentes não carregados: {e}")

def load_metrics_from_files():
    """Carrega métricas de arquivos de dados se existirem"""
    try:
        metrics_files = [
            'bot/data/monitoring/performance_metrics.json',
            'bot/data/monitoring/tips_metrics.json',
            'bot/data/monitoring/prediction_stats.json'
        ]
        
        combined_metrics = {}
        
        for file_path in metrics_files:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    combined_metrics.update(data)
        
        if combined_metrics:
            # Calcula métricas derivadas
            total_preds = combined_metrics.get('total_predictions', 0)
            correct_preds = combined_metrics.get('correct_predictions', 0)
            
            if total_preds > 0:
                combined_metrics['win_rate_percentage'] = round((correct_preds / total_preds) * 100, 1)
            else:
                combined_metrics['win_rate_percentage'] = 0.0
                
            return combined_metrics
            
        return None
        
    except Exception as e:
        print(f"Erro ao carregar métricas de arquivos: {e}")
        return None

def get_fallback_metrics():
    """Métricas básicas quando sistema completo não está disponível"""
    return {
        'total_predictions': 0,
        'correct_predictions': 0,
        'win_rate_percentage': 0.0,
        'roi_percentage': 0.0,
        'net_profit': 0.0,
        'tips_generated': 0,
        'tips_system_active': False,
        'composition_analyses': 0,
        'patch_analyses': 0,
        'last_prediction_time': 'Sistema não carregado',
        'last_tip_time': 'Sistema não carregado'
    }

def render_dashboard_fallback(dashboard_html, dashboard_data):
    """Renderiza dashboard sem Jinja2"""
    # Substitui variáveis simples
    for key, value in dashboard_data.items():
        dashboard_html = dashboard_html.replace('{{ ' + key + ' }}', str(value))
    
    # Condicionais para status
    if dashboard_data['running']:
        dashboard_html = dashboard_html.replace('{% if running %}success{% else %}danger{% endif %}', 'success')
        dashboard_html = dashboard_html.replace('{% if running %}Online{% else %}Offline{% endif %}', 'Online')
        dashboard_html = dashboard_html.replace('{% if running %}status-online{% else %}status-offline{% endif %}', 'status-online')
        dashboard_html = dashboard_html.replace('{% if running %}🟢 Online{% else %}🔴 Offline{% endif %}', '🟢 Online')
    else:
        dashboard_html = dashboard_html.replace('{% if running %}success{% else %}danger{% endif %}', 'danger')
        dashboard_html = dashboard_html.replace('{% if running %}Online{% else %}Offline{% endif %}', 'Offline')
        dashboard_html = dashboard_html.replace('{% if running %}status-online{% else %}status-offline{% endif %}', 'status-offline')
        dashboard_html = dashboard_html.replace('{% if running %}🟢 Online{% else %}🔴 Offline{% endif %}', '🔴 Offline')
    
    # Condicionais para componentes
    if dashboard_data['components_available']:
        dashboard_html = dashboard_html.replace('{% if components_available %}status-online{% else %}status-offline{% endif %}', 'status-online')
        dashboard_html = dashboard_html.replace('{% if components_available %}✅ Carregados{% else %}⚠️ Limitados{% endif %}', '✅ Carregados')
    else:
        dashboard_html = dashboard_html.replace('{% if components_available %}status-online{% else %}status-offline{% endif %}', 'status-offline')
        dashboard_html = dashboard_html.replace('{% if components_available %}✅ Carregados{% else %}⚠️ Limitados{% endif %}', '⚠️ Limitados')
    
    # Condicionais para win rate
    if dashboard_data['win_rate'] >= 70:
        dashboard_html = dashboard_html.replace('{% if win_rate >= 70 %}high{% endif %}', 'high')
    else:
        dashboard_html = dashboard_html.replace('{% if win_rate >= 70 %}high{% endif %}', '')
    
    # Condicionais para ROI
    if dashboard_data['roi'] < 0:
        dashboard_html = dashboard_html.replace('{% if roi < 0 %}negative{% endif %}', 'negative')
    else:
        dashboard_html = dashboard_html.replace('{% if roi < 0 %}negative{% endif %}', '')
    
    # Condicionais para profit
    if dashboard_data['profit'] < 0:
        dashboard_html = dashboard_html.replace('{% if profit < 0 %}negative{% endif %}', 'negative')
    else:
        dashboard_html = dashboard_html.replace('{% if profit < 0 %}negative{% endif %}', '')
    
    return dashboard_html

@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint de health check para Railway"""
    global bot_status
    
    increment_request_counter()
    
    current_time = time.time()
    uptime = current_time - bot_status["start_time"]
    last_heartbeat_ago = current_time - bot_status["last_heartbeat"]
    
    # Considera saudável se heartbeat foi há menos de 5 minutos
    # OU se é um shutdown graceful recente (menos de 2 minutos)
    is_healthy = (
        bot_status["is_running"] and 
        last_heartbeat_ago < 300  # 5 minutos
    ) or (
        not bot_status["is_running"] and 
        last_heartbeat_ago < 120  # 2 minutos - shutdown graceful
    )
    
    status_code = 200 if is_healthy else 503
    
    response = {
        "status": "healthy" if is_healthy else "unhealthy",
        "timestamp": datetime.now().isoformat(),
        "uptime_seconds": round(uptime, 2),
        "uptime_hours": round(uptime / 3600, 2),
        "bot_running": bot_status["is_running"],
        "last_heartbeat_ago": round(last_heartbeat_ago, 2),
        "version": bot_status["version"],
        "environment": bot_status["environment"],
        "service": "Bot LoL V3 Ultra Avançado"
    }
    
    return jsonify(response), status_code

@app.route('/status', methods=['GET'])
def detailed_status():
    """Status detalhado do bot"""
    global bot_status
    
    increment_request_counter()
    
    current_time = time.time()
    uptime = current_time - bot_status["start_time"]
    
    try:
        # Tenta importar e verificar componentes
        from bot.systems.schedule_manager import ScheduleManager
        components_available = True
    except ImportError:
        components_available = False
    
    response = {
        "service": "Bot LoL V3 Ultra Avançado",
        "version": bot_status["version"],
        "environment": bot_status["environment"],
        "status": {
            "bot_running": bot_status["is_running"],
            "components_available": components_available,
            "uptime_seconds": round(uptime, 2),
            "uptime_hours": round(uptime / 3600, 2)
        },
        "timestamps": {
            "start_time": datetime.fromtimestamp(bot_status["start_time"]).isoformat(),
            "last_heartbeat": datetime.fromtimestamp(bot_status["last_heartbeat"]).isoformat(),
            "current_time": datetime.now().isoformat()
        },
        "metrics": {
            "total_requests": bot_status["total_requests"],
            "errors_count": bot_status["errors_count"],
            "success_rate": round((bot_status["total_requests"] - bot_status["errors_count"]) / max(bot_status["total_requests"], 1) * 100, 2)
        },
        "railway": {
            "deployment": "active",
            "region": os.getenv("RAILWAY_REGION", "unknown"),
            "service_id": os.getenv("RAILWAY_SERVICE_ID", "unknown")
        }
    }
    
    return jsonify(response)

@app.route('/metrics', methods=['GET'])
def system_metrics():
    """Métricas detalhadas do sistema para Railway"""
    increment_request_counter()
    
    try:
        # Métricas do sistema
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        current_time = time.time()
        uptime = current_time - bot_status["start_time"]
        
        response = {
            "service": "Bot LoL V3 Ultra Avançado",
            "timestamp": datetime.now().isoformat(),
            "uptime": {
                "seconds": round(uptime, 2),
                "hours": round(uptime / 3600, 2),
                "days": round(uptime / 86400, 2)
            },
            "system": {
                "cpu_percent": round(cpu_percent, 2),
                "memory": {
                    "total_mb": round(memory.total / 1024 / 1024, 2),
                    "available_mb": round(memory.available / 1024 / 1024, 2),
                    "used_mb": round(memory.used / 1024 / 1024, 2),
                    "percent": round(memory.percent, 2)
                },
                "disk": {
                    "total_gb": round(disk.total / 1024 / 1024 / 1024, 2),
                    "free_gb": round(disk.free / 1024 / 1024 / 1024, 2),
                    "used_gb": round(disk.used / 1024 / 1024 / 1024, 2),
                    "percent": round((disk.used / disk.total) * 100, 2)
                }
            },
            "bot": {
                "running": bot_status["is_running"],
                "total_requests": bot_status["total_requests"],
                "errors_count": bot_status["errors_count"],
                "error_rate": round(bot_status["errors_count"] / max(bot_status["total_requests"], 1) * 100, 2),
                "requests_per_hour": round(bot_status["total_requests"] / max(uptime / 3600, 1), 2)
            },
            "environment": {
                "python_version": f"{psutil.sys.version_info.major}.{psutil.sys.version_info.minor}.{psutil.sys.version_info.micro}",
                "platform": psutil.platform.system(),
                "process_count": len(psutil.pids())
            }
        }
        
        return jsonify(response)
        
    except Exception as e:
        increment_error_counter()
        return jsonify({
            "error": "Failed to collect metrics",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/', methods=['GET'])
def root():
    """Endpoint raiz"""
    increment_request_counter()
    
    return jsonify({
        "service": "Bot LoL V3 Ultra Avançado",
        "status": "online",
        "message": "Bot está executando no Railway",
        "version": bot_status["version"],
        "uptime_hours": round((time.time() - bot_status["start_time"]) / 3600, 2),
        "endpoints": {
            "/": "This endpoint",
            "/dashboard": "Dashboard web interativo",
            "/health": "Health check endpoint (Railway monitoring)",
            "/status": "Detailed bot status", 
            "/metrics": "System metrics and performance",
            "/favicon.ico": "Site favicon"
        },
        "quick_links": {
            "dashboard": "/dashboard",
            "health_check": "/health",
            "system_status": "/status",
            "metrics": "/metrics"
        }
    })

def run_health_server():
    """Executa servidor de health check em thread separada"""
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

def start_health_server():
    """Inicia servidor de health check"""
    health_thread = threading.Thread(target=run_health_server, daemon=True)
    health_thread.start()
    print(f"🏥 Health check server iniciado na porta {os.getenv('PORT', 8080)}")

if __name__ == "__main__":
    # Executa apenas o servidor de health check
    print("🏥 Iniciando Health Check Server para Railway...")
    run_health_server() 
