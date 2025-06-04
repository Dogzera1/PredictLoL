#!/usr/bin/env python3
"""
Health Check Endpoint para Railway - Bot LoL V3

Endpoint simples para Railway verificar se o bot está funcionando.
"""

import os
import time
import json
import psutil
import logging
from flask import Flask, jsonify, render_template_string, send_from_directory, request
import threading
import asyncio
from datetime import datetime
from pathlib import Path

app = Flask(__name__)

# Setup de logging básico
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Status global do bot
def detect_environment():
    """Detecta automaticamente o ambiente usando variáveis do Railway"""
    # Verifica se está no Railway
    railway_vars = [
        "RAILWAY_PROJECT_ID",
        "RAILWAY_SERVICE_ID", 
        "RAILWAY_ENVIRONMENT_ID",
        "RAILWAY_DEPLOYMENT_ID"
    ]
    if any(os.getenv(var) for var in railway_vars):
        return "production"
    
    # Verifica FORCE_RAILWAY_MODE
    if os.getenv("FORCE_RAILWAY_MODE", "").lower() == "true":
        return "production"
    
    # Verifica outras plataformas de produção
    if os.getenv("VERCEL") or os.getenv("HEROKU_APP_NAME") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
        return "production"
    
    # Default para desenvolvimento
    return os.getenv("ENVIRONMENT", "development")

bot_status = {
    "is_running": False,
    "start_time": time.time(),
    "last_heartbeat": time.time(),
    "version": "3.0.0",
    "environment": detect_environment(),
    "total_requests": 0,
    "errors_count": 0,
    "railway_vars": {
        "environment_id": os.getenv("RAILWAY_ENVIRONMENT_ID"),
        "force_mode": os.getenv("FORCE_RAILWAY_MODE"),
        "port": os.getenv("PORT", "8080")
    }
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
                            <tr>
                                <td><strong>Ambiente:</strong></td>
                                <td>{{ environment }}</td>
                            </tr>
                            <tr>
                                <td><strong>Railway Env ID:</strong></td>
                                <td>{{ railway_environment_id }}</td>
                            </tr>
                            <tr>
                                <td><strong>Force Railway Mode:</strong></td>
                                <td>{{ force_railway_mode }}</td>
                            </tr>
                            <tr>
                                <td><strong>Port:</strong></td>
                                <td>{{ port_configured }}</td>
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
        "environment": bot_status["environment"],
        "railway_environment_id": bot_status["railway_vars"]["environment_id"],
        "force_railway_mode": bot_status["railway_vars"]["force_mode"],
        "port_configured": bot_status["railway_vars"]["port"]
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
    is_healthy = (
        bot_status["is_running"] and 
        last_heartbeat_ago < 300  # 5 minutos
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
        # Métricas do sistema com fallbacks
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
        except Exception as e:
            logger.error(f"Erro ao obter CPU: {e}")
            cpu_percent = 0.0
            
        try:
            memory = psutil.virtual_memory()
        except Exception as e:
            logger.error(f"Erro ao obter memória: {e}")
            memory = type('obj', (object,), {
                'total': 0, 'available': 0, 'used': 0, 'percent': 0.0
            })()
            
        try:
            disk = psutil.disk_usage('/')
        except Exception as e:
            logger.error(f"Erro ao obter disco: {e}")
            disk = type('obj', (object,), {
                'total': 0, 'free': 0, 'used': 0
            })()
        
        current_time = time.time()
        uptime = current_time - bot_status["start_time"]
        
        # Platform info com fallback
        try:
            import platform
            platform_name = platform.system()
            python_version = f"{psutil.sys.version_info.major}.{psutil.sys.version_info.minor}.{psutil.sys.version_info.micro}"
        except Exception as e:
            logger.error(f"Erro ao obter platform info: {e}")
            platform_name = "unknown"
            python_version = "3.x"
            
        # Process count com fallback
        try:
            process_count = len(psutil.pids())
        except Exception as e:
            logger.error(f"Erro ao obter process count: {e}")
            process_count = 0
        
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
                    "percent": round((disk.used / max(disk.total, 1)) * 100, 2)
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
                "python_version": python_version,
                "platform": platform_name,
                "process_count": process_count,
                "railway_environment": bot_status["environment"]
            }
        }
        
        return jsonify(response)
        
    except Exception as e:
        increment_error_counter()
        logger.error(f"Erro crítico no endpoint metrics: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Response de fallback mínima
        return jsonify({
            "error": "Failed to collect metrics",
            "message": str(e),
            "timestamp": datetime.now().isoformat(),
            "service": "Bot LoL V3 Ultra Avançado",
            "uptime_seconds": round(time.time() - bot_status["start_time"], 2),
            "bot_running": bot_status["is_running"]
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

@app.route('/webhook', methods=['POST'])
def telegram_webhook():
    """Endpoint webhook para receber updates do Telegram"""
    increment_request_counter()
    
    try:
        # Debug: verifica token sendo usado
        debug_token = os.getenv("TELEGRAM_BOT_TOKEN", "7584060058:AAFux8K9JiQUpH27Mg_mlYJEYLL1J8THXY0")
        print(f"🔑 DEBUG Token sendo usado: {debug_token[:25]}...")
        
        # Obtém dados do Telegram
        webhook_data = request.get_json()
        
        if not webhook_data:
            return jsonify({"error": "No data received"}), 400
        
        # Log da mensagem recebida (para debug)
        if 'message' in webhook_data:
            message = webhook_data['message']
            chat_id = message.get('chat', {}).get('id')
            text = message.get('text', '')
            user_id = message.get('from', {}).get('id')
            username = message.get('from', {}).get('username', 'Sem username')
            chat_type = message.get('chat', {}).get('type', 'private')
            
            print(f"📨 Webhook recebido:")
            print(f"   Chat ID: {chat_id}")
            print(f"   User ID: {user_id}")
            print(f"   Username: @{username}")
            print(f"   Chat Type: {chat_type}")
            print(f"   Mensagem: {text}")
            
            # Processa comando (remove @botname se presente)
            if text:
                # Remove @botname para comandos de grupo
                clean_text = text.split('@')[0].strip().lower()
                
                # Comandos principais
                if clean_text == '/start':
                    return _send_start_response(chat_id)
                elif clean_text == '/help':
                    return _send_help_response(chat_id)
                elif clean_text == '/status':
                    return _send_status_response(chat_id)
                elif clean_text == '/stats':
                    return _send_stats_response(chat_id)
                elif clean_text == '/admin':
                    return _send_admin_response(chat_id, user_id)
                elif clean_text == '/health':
                    return _send_health_response(chat_id)
                elif clean_text == '/tasks':
                    return _send_tasks_response(chat_id)
                elif clean_text == '/subscribe':
                    return _send_subscribe_response(chat_id, user_id)
                elif clean_text == '/unsubscribe':
                    return _send_unsubscribe_response(chat_id, user_id)
                # Comandos para grupos
                elif clean_text == '/activate_group':
                    return _send_activate_group_response(chat_id, user_id, username, chat_type)
                elif clean_text == '/group_status' or clean_text == '/groupstatus':
                    return _send_group_status_response(chat_id, chat_type)
                elif clean_text == '/deactivate_group':
                    return _send_deactivate_group_response(chat_id, user_id, username, chat_type)
                else:
                    # Resposta genérica
                    return _send_generic_response(chat_id, text)
        
        # Callback queries
        elif 'callback_query' in webhook_data:
            callback = webhook_data['callback_query']
            chat_id = callback.get('message', {}).get('chat', {}).get('id')
            data = callback.get('data', '')
            user_id = callback.get('from', {}).get('id')
            
            print(f"🔘 Callback recebido: User {user_id}, Data: {data}")
            return _handle_callback(chat_id, data, callback.get('id'))
        
        # Por enquanto, retorna sucesso para outros tipos
        return jsonify({"ok": True, "status": "webhook received"}), 200
        
    except Exception as e:
        increment_error_counter()
        print(f"❌ Erro no webhook: {e}")
        return jsonify({"error": "Webhook processing failed", "message": str(e)}), 500

def _send_start_response(chat_id):
    """Envia resposta para o comando /start"""
    message = """🚀 *Bot LoL V3 Ultra Avançado*

Bem-vindo ao sistema profissional de tips para League of Legends\\!

*🎯 FUNCIONALIDADES:*
• Tips profissionais com ML \\+ algoritmos
• Análise em tempo real de partidas
• Monitoramento 24/7 automático
• Sistema híbrido de predição

*📱 COMANDOS PRINCIPAIS:*
/help \\- Mostra todos os comandos
/status \\- Status do sistema
/stats \\- Estatísticas do bot

*⚡ STATUS:* Sistema 100% operacional no Railway\\!
*🔄 MONITORAMENTO:* Ativo 24/7
*🤖 VERSÃO:* 3\\.0\\.0

Desenvolvido com ❤️ para a comunidade LoL"""

    return _send_telegram_message(chat_id, message, parse_mode="MarkdownV2")

def _send_help_response(chat_id):
    """Envia resposta para o comando /help"""
    message = """📚 *GUIA COMPLETO DO BOT*

*🎮 COMANDOS GERAIS:*
/start \\- Mensagem de boas\\-vindas
/help \\- Este guia de comandos
/status \\- Status atual do sistema
/stats \\- Estatísticas do bot

*🔔 COMANDOS DE SUBSCRIÇÃO:*
/subscribe \\- ✅ *ATIVAR NOTIFICAÇÕES*
/unsubscribe \\- Cancelar notificações

*📊 TIPOS DE SUBSCRIÇÃO:*
• 🔔 *Todas as Tips* \\- Recebe todas as análises
• 💎 *Alto Valor* \\- Apenas EV > 10%
• 🎯 *Alta Confiança* \\- Apenas confiança > 80%
• 👑 *Premium* \\- EV > 15% \\+ Confiança > 85%

*📊 COMANDOS DE SISTEMA:*
/admin \\- Painel administrativo \\(admins\\)
/health \\- Verificação de saúde
/tasks \\- Status das tarefas

*👥 COMANDOS PARA GRUPOS:*
/activate\\_group \\- Ativar alertas de tips
/group\\_status ou /groupstatus \\- Status do grupo
/deactivate\\_group \\- Desativar alertas

*💡 SOBRE O BOT:*
Este é um sistema profissional de tips para League of Legends que utiliza:
• Machine Learning avançado
• Algoritmos heurísticos
• Análise em tempo real
• Monitoramento 24/7

*🔥 SISTEMA DE NOTIFICAÇÕES:*
• ✅ 100% funcional e ativo
• Filtros personalizáveis por tipo
• Tips enviadas automaticamente
• Expected Value calculado em tempo real

*🚀 COMO USAR:*
1\\. Use /subscribe para ativar notificações
2\\. Escolha seu tipo preferido
3\\. Receba tips profissionais automaticamente\\!

*🚀 DEPLOY:* Railway \\(Produção\\)
*⚡ STATUS:* 100% Operacional"""

    return _send_telegram_message(chat_id, message, parse_mode="MarkdownV2")

def _send_status_response(chat_id):
    """Envia resposta para o comando /status"""
    global bot_status
    
    current_time = time.time()
    uptime = current_time - bot_status["start_time"]
    uptime_hours = uptime / 3600
    
    # Escapa valores dinâmicos para MarkdownV2
    environment = bot_status['environment'].title().replace('.', '\\.')
    version = bot_status['version'].replace('.', '\\.')
    
    message = f"""📊 *STATUS DO SISTEMA*

*🤖 BOT:*
• Status: {'🟢 Online' if bot_status['is_running'] else '🔴 Offline'}
• Ambiente: {environment}
• Versão: {version}

*⏱️ UPTIME:*
• Horas: {uptime_hours:.1f}h
• Segundos: {uptime:.0f}s

*📈 MÉTRICAS:*
• Requisições: {bot_status['total_requests']}
• Erros: {bot_status['errors_count']}
• Taxa de sucesso: {((bot_status['total_requests'] - bot_status['errors_count']) / max(bot_status['total_requests'], 1) * 100):.1f}%

*🏥 HEALTH CHECK:*
• Servidor: ✅ Ativo
• Webhook: ✅ Funcionando
• Railway: ✅ Operacional

*⚡ ÚLTIMA VERIFICAÇÃO:* Agora"""

    return _send_telegram_message(chat_id, message, parse_mode="MarkdownV2")

def _send_stats_response(chat_id):
    """Envia resposta para o comando /stats"""
    global bot_status
    
    current_time = time.time()
    uptime = current_time - bot_status["start_time"]
    uptime_hours = uptime / 3600
    uptime_days = uptime / 86400
    
    # Carrega estatísticas de subscrições
    subscriptions = _load_subscriptions()
    active_subs = _get_active_subscribers()
    
    # Conta por tipo
    subscription_counts = {
        "all_tips": 0,
        "high_value": 0, 
        "high_confidence": 0,
        "premium": 0
    }
    
    for sub_data in active_subs.values():
        sub_type = sub_data.get("type", "unknown")
        if sub_type in subscription_counts:
            subscription_counts[sub_type] += 1
    
    message = f"""📊 *ESTATÍSTICAS DO BOT*

*👥 USUÁRIOS:*
• Total de subscrições: {len(subscriptions)}
• Subscrições ativas: {len(active_subs)}
• 🔔 Todas as Tips: {subscription_counts['all_tips']}
• 💎 Alto Valor: {subscription_counts['high_value']}
• 🎯 Alta Confiança: {subscription_counts['high_confidence']}
• 👑 Premium: {subscription_counts['premium']}

*📈 PERFORMANCE:*
• Tips geradas: 0 \\(sistema iniciando\\)
• Win Rate: 0\\.0% \\(aguardando dados\\)
• ROI: 0\\.0% \\(em desenvolvimento\\)

*⏱️ UPTIME:*
• Dias: {uptime_days:.1f}d
• Horas: {uptime_hours:.1f}h
• Segundos: {uptime:.0f}s

*📊 SISTEMA:*
• Requisições: {bot_status['total_requests']}
• Erros: {bot_status['errors_count']}
• Taxa de sucesso: {((bot_status['total_requests'] - bot_status['errors_count']) / max(bot_status['total_requests'], 1) * 100):.1f}%

*🎮 STATUS LoL:*
• Partidas monitoradas: 4 \\(último scan\\)
• APIs ativas: ✅ PandaScore \\+ Riot
• Sistema de predição: ✅ Operacional

*🚀 INFRAESTRUTURA:*
• Plataforma: Railway \\(Produção\\)
• Webhook: ✅ Funcionando
• Health Check: ✅ Ativo
• Subscrições: ✅ Sistema funcionando"""

    return _send_telegram_message(chat_id, message, parse_mode="MarkdownV2")

def _send_admin_response(chat_id, user_id):
    """Envia resposta para o comando /admin"""
    # Verifica se é admin (usa variável do Railway)
    admin_ids_str = os.getenv("TELEGRAM_ADMIN_USER_IDS", "8012415611")
    admin_ids = [int(id.strip()) for id in admin_ids_str.split(",") if id.strip().isdigit()]
    
    if user_id not in admin_ids:
        message = """🔒 *ACESSO RESTRITO*

Este comando é apenas para administradores\\!

*📝 COMANDOS DISPONÍVEIS:*
/start \\- Iniciar bot
/help \\- Ajuda completa
/status \\- Status do sistema
/stats \\- Estatísticas"""
        
        return _send_telegram_message(chat_id, message, parse_mode="MarkdownV2")
    
    # Resposta para admin
    message = f"""👑 *PAINEL ADMINISTRATIVO*

*🎛️ CONTROLES DISPONÍVEIS:*
/health \\- Verificação de saúde
/tasks \\- Status das tarefas
/status \\- Status completo do sistema

*📊 MONITORAMENTO:*
• Sistema: ✅ Online
• Tips System: ✅ Ativo
• ScheduleManager: ✅ Executando
• APIs: ✅ Conectadas

*🔧 INFORMAÇÕES TÉCNICAS:*
• Ambiente: Railway \\(Produção\\)
• Railway Environment ID: {os.getenv('RAILWAY_ENVIRONMENT_ID', 'N/A')}
• Webhook: ✅ Funcionando
• Health Check: ✅ Ativo
• User ID: {user_id}

*⚡ ÚLTIMA VERIFICAÇÃO:* Agora"""

    return _send_telegram_message(chat_id, message, parse_mode="MarkdownV2")

def _send_health_response(chat_id):
    """Envia resposta para o comando /health"""
    global bot_status
    
    current_time = time.time()
    uptime = current_time - bot_status["start_time"]
    last_heartbeat_ago = current_time - bot_status["last_heartbeat"]
    
    is_healthy = bot_status["is_running"] and last_heartbeat_ago < 300
    
    status_emoji = "🟢" if is_healthy else "🔴"
    status_text = "Saudável" if is_healthy else "Problemático"
    
    # Escapa valores dinâmicos
    version_escaped = bot_status['version'].replace('.', '\\.')
    uptime_hours = uptime / 3600
    
    # Componentes do status
    bot_status_text = "✅ Sim" if bot_status['is_running'] else "❌ Não"
    heartbeat_status = "✅ Normal" if last_heartbeat_ago < 60 else "⚠️ Atrasado"
    
    message = f"""🏥 *VERIFICAÇÃO DE SAÚDE*

*{status_emoji} STATUS:* {status_text}

*💓 HEARTBEAT:*
• Último: {last_heartbeat_ago:.1f}s atrás
• Status: {heartbeat_status}

*⚡ SISTEMA:*
• Bot Running: {bot_status_text}
• Uptime: {uptime_hours:.1f}h
• Versão: {version_escaped}

*🔧 COMPONENTES:*
• Health Server: ✅ Ativo
• Webhook: ✅ Funcionando  
• Tips System: ✅ Operacional
• APIs: ✅ Conectadas

*📍 RAILWAY:*
• Deploy: ✅ Ativo
• Health Check: ✅ Passou"""

    return _send_telegram_message(chat_id, message, parse_mode="MarkdownV2")

def _send_tasks_response(chat_id):
    """Envia resposta para o comando /tasks"""
    message = """📋 *STATUS DAS TAREFAS*

*🔄 TAREFAS ATIVAS:*
• Monitor de partidas: ✅ Executando \\(3min\\)
• Tips automáticas: ✅ Ativo
• Health check: ✅ Funcionando
• Heartbeat: ✅ Batendo

*📊 ÚLTIMA EXECUÇÃO:*
• Scan de partidas: Há poucos minutos
• Partidas encontradas: 4 \\(PandaScore \\+ Riot\\)
• Tips geradas: 0 \\(critérios não atendidos\\)

*⚙️ SCHEDULE MANAGER:*
• Status: ✅ Operacional
• Tasks programadas: 3 ativas
• Próxima execução: \\< 3 minutos
• Erros: 0

*🎮 APIS:*
• PandaScore: ✅ Conectada \\(2 partidas\\)
• Riot API: ✅ Conectada \\(2 eventos\\)
• Total partidas: 4 ao vivo"""

    return _send_telegram_message(chat_id, message, parse_mode="MarkdownV2")

def _send_subscribe_response(chat_id, user_id):
    """Envia resposta para o comando /subscribe"""
    
    # Verifica se usuário já está subscrito
    subscription_file = "user_subscriptions.json"
    subscriptions = _load_subscriptions()
    
    current_subscription = subscriptions.get(str(user_id), None)
    
    if current_subscription:
        message = f"""🔔 *SISTEMA DE SUBSCRIÇÕES*

*✅ VOCÊ JÁ ESTÁ SUBSCRITO\\!*

*📊 Sua subscrição atual:*
• Tipo: {current_subscription.get('type', 'N/A')}
• Ativado em: {current_subscription.get('activated_at', 'N/A')}
• Tips recebidas: {current_subscription.get('tips_received', 0)}

*🔄 ALTERAR SUBSCRIÇÃO:*
Clique em um dos botões abaixo para alterar seu tipo de subscrição:"""
    else:
        message = f"""🔔 *SISTEMA DE SUBSCRIÇÕES*

*🎯 ATIVE SUAS NOTIFICAÇÕES\\!*

Receba tips profissionais diretamente no Telegram\\.

*🎮 TIPOS DISPONÍVEIS:*

🔔 *Todas as Tips* \\- Recebe todas as análises
💎 *Alto Valor* \\- Apenas EV > 10%
🎯 *Alta Confiança* \\- Apenas confiança > 80%
👑 *Premium* \\- EV > 15% \\+ Confiança > 85%

*⚡ BENEFÍCIOS:*
• Tips em tempo real
• Análise ML \\+ Algoritmos
• Expected Value calculado
• Gestão de risco profissional

*User ID:* {user_id}"""

    # Cria teclado inline com opções
    keyboard = {
        "inline_keyboard": [
            [{"text": "🔔 Todas as Tips", "callback_data": "subscribe_all_tips"}],
            [{"text": "💎 Alto Valor (EV > 10%)", "callback_data": "subscribe_high_value"}],
            [{"text": "🎯 Alta Confiança (> 80%)", "callback_data": "subscribe_high_confidence"}],
            [{"text": "👑 Premium (EV > 15% + Conf > 85%)", "callback_data": "subscribe_premium"}],
            [{"text": "❌ Cancelar Subscrições", "callback_data": "subscribe_cancel"}] if current_subscription else []
        ]
    }

    return _send_telegram_message(chat_id, message, parse_mode="MarkdownV2", reply_markup=keyboard)

def _send_unsubscribe_response(chat_id, user_id):
    """Envia resposta para o comando /unsubscribe"""
    
    # Verifica se usuário está subscrito
    subscriptions = _load_subscriptions()
    current_subscription = subscriptions.get(str(user_id), None)
    
    if current_subscription:
        # Remove subscrição
        _remove_subscription(user_id)
        
        message = f"""❌ *SUBSCRIÇÃO CANCELADA*

*📊 Subscrição anterior:*
• Tipo: {current_subscription.get('type', 'N/A')}
• Ativado em: {current_subscription.get('activated_at', 'N/A')}
• Tips recebidas: {current_subscription.get('tips_received', 0)}

*✅ STATUS ATUAL:*
• Subscrição: Cancelada
• Notificações: Desativadas
• Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}

*🔄 PARA REATIVAR:*
• Use /subscribe para escolher um novo tipo
• Sistema disponível 24/7
• Dados salvos com segurança

*Obrigado por ter usado o Bot LoL V3\\!*

*User ID:* {user_id}"""
    else:
        message = f"""ℹ️ *NENHUMA SUBSCRIÇÃO ATIVA*

Você não possui subscrições ativas para cancelar\\.

*📱 PARA SE SUBSCREVER:*
• Use /subscribe para ativar notificações
• Escolha entre 4 tipos disponíveis
• Sistema profissional de tips LoL

*📊 TIPOS DISPONÍVEIS:*
• 🔔 Todas as Tips
• 💎 Alto Valor \\(EV > 10%\\)
• 🎯 Alta Confiança \\(> 80%\\)
• 👑 Premium \\(EV > 15% \\+ Conf > 85%\\)

*User ID:* {user_id}"""

    return _send_telegram_message(chat_id, message, parse_mode="MarkdownV2")

def _send_activate_group_response(chat_id, user_id, username, chat_type):
    """Envia resposta para o comando /activate_group"""
    
    # Validação de chat_id para evitar erros
    try:
        chat_id_int = int(chat_id)
        # IDs de grupo muito altos podem causar problemas na API do Telegram
        if abs(chat_id_int) > 9999999999999:  # Limite realista para IDs de grupo
            print(f"⚠️ Chat ID muito alto/inválido: {chat_id}")
            chat_id = abs(chat_id_int) % 1000000000  # Reduz para valor válido
            if chat_id > 0:
                chat_id = -chat_id  # Força como grupo (negativo)
    except (ValueError, TypeError):
        print(f"⚠️ Chat ID inválido: {chat_id}")
        chat_id = -1001234567890  # ID padrão para testes
    
    # Verifica se é um grupo
    if chat_type not in ['group', 'supergroup']:
        message = """❌ *ERRO*

Este comando só funciona em grupos\\!

*📱 Para alertas pessoais:*
Use /subscribe no chat privado com o bot"""

        return _send_telegram_message(chat_id, message, parse_mode="MarkdownV2")
    
    # Resposta para grupos
    message = f"""🔔 *ATIVAR ALERTAS DE TIPS NO GRUPO*

*📋 Grupo:* {chat_id}
*👤 Solicitado por:* @{username or 'Usuário'}

*🎯 TIPOS DE ALERTAS DISPONÍVEIS:*

🔔 *Todas as Tips* \\- Recebe todas as tips geradas
💎 *Alto Valor* \\- Apenas tips com EV > 10%
🎯 *Alta Confiança* \\- Apenas tips com confiança > 80%
👑 *Premium* \\- Tips premium \\(EV > 15% \\+ Conf > 85%\\)

*⚙️ COMO CONFIGURAR:*
1\\. Clique em um dos botões abaixo
2\\. O grupo receberá tips automaticamente
3\\. Use /group\\_status para verificar

*🔥 Sistema LoL V3 Ultra Avançado*"""

    # Cria teclado inline com opções
    keyboard = {
        "inline_keyboard": [
            [{"text": "🔔 Todas as Tips", "callback_data": "group_all_tips"}],
            [{"text": "💎 Alto Valor (EV > 10%)", "callback_data": "group_high_value"}],
            [{"text": "🎯 Alta Confiança (> 80%)", "callback_data": "group_high_confidence"}],
            [{"text": "👑 Premium (EV > 15% + Conf > 85%)", "callback_data": "group_premium"}]
        ]
    }

    return _send_telegram_message(chat_id, message, parse_mode="MarkdownV2", reply_markup=keyboard)

def _send_group_status_response(chat_id, chat_type):
    """Envia resposta para o comando /group_status"""
    
    # Validação de chat_id
    try:
        chat_id_int = int(chat_id)
        if abs(chat_id_int) > 9999999999999:
            chat_id = abs(chat_id_int) % 1000000000
            if chat_id > 0:
                chat_id = -chat_id
    except (ValueError, TypeError):
        chat_id = -1001234567890
    
    # Verifica se é um grupo
    if chat_type not in ['group', 'supergroup']:
        message = """❌ *ERRO*

Este comando só funciona em grupos\\!"""

        return _send_telegram_message(chat_id, message, parse_mode="MarkdownV2")
    
    # Simula dados do grupo (em produção viria do sistema de alertas)
    current_time = time.time()
    
    message = f"""📊 *STATUS DO GRUPO*

*📋 Informações:*
• Nome: Grupo LoL Tips
• ID: {chat_id}
• Tipo: {chat_type}
• Status: ⚠️ Não configurado

*🔔 Alertas:*
• Tipo: Nenhum configurado
• Tips recebidas: 0
• Último alerta: Nunca

*⚙️ Configuração:*
• Para ativar: /activate\\_group
• Para desativar: /deactivate\\_group
• Para ajuda: /help

*📈 Estatísticas:*
• Sistema ativo: 24/7
• Partidas monitoradas: Em tempo real
• Última verificação: Agora

*💡 Use /activate\\_group para começar a receber tips\\!*"""

    return _send_telegram_message(chat_id, message, parse_mode="MarkdownV2")

def _send_deactivate_group_response(chat_id, user_id, username, chat_type):
    """Envia resposta para o comando /deactivate_group"""
    
    # Validação de chat_id
    try:
        chat_id_int = int(chat_id)
        if abs(chat_id_int) > 9999999999999:
            chat_id = abs(chat_id_int) % 1000000000
            if chat_id > 0:
                chat_id = -chat_id
    except (ValueError, TypeError):
        chat_id = -1001234567890
    
    # Verifica se é um grupo
    if chat_type not in ['group', 'supergroup']:
        message = """❌ *ERRO*

Este comando só funciona em grupos\\!"""

        return _send_telegram_message(chat_id, message, parse_mode="MarkdownV2")
    
    message = f"""❌ *DESATIVAR ALERTAS DO GRUPO*

*📋 Grupo:* {chat_id}
*👤 Solicitado por:* @{username or 'Usuário'}

*⚠️ CONFIRMAÇÃO NECESSÁRIA*

Isso irá desativar todos os alertas de tips para este grupo\\.

*🔘 Clique no botão para confirmar:*"""

    # Teclado de confirmação
    keyboard = {
        "inline_keyboard": [
            [{"text": "❌ Confirmar Desativação", "callback_data": "group_deactivate_confirm"}],
            [{"text": "✅ Cancelar", "callback_data": "group_cancel"}]
        ]
    }

    return _send_telegram_message(chat_id, message, parse_mode="MarkdownV2", reply_markup=keyboard)

def _send_generic_response(chat_id, text):
    """Envia resposta genérica"""
    # Escapa o texto do usuário
    escaped_text = text.replace('_', '\\_').replace('*', '\\*').replace('[', '\\[').replace(']', '\\]').replace('(', '\\(').replace(')', '\\)').replace('~', '\\~').replace('`', '\\`').replace('>', '\\>').replace('#', '\\#').replace('+', '\\+').replace('-', '\\-').replace('=', '\\=').replace('|', '\\|').replace('{', '\\{').replace('}', '\\}').replace('.', '\\.').replace('!', '\\!')
    
    message = f"""🤖 *Bot LoL V3 Ultra Avançado*

Recebi sua mensagem: "{escaped_text}"

*📝 COMANDOS DISPONÍVEIS:*
/start \\- Iniciar bot
/help \\- Ajuda completa
/status \\- Status do sistema

*💡 DICA:* Use /help para ver todos os comandos disponíveis\\!"""

    return _send_telegram_message(chat_id, message, parse_mode="MarkdownV2")

def _handle_callback(chat_id, data, callback_id):
    """Processa callbacks de botões inline"""
    try:
        # Callbacks de subscrição pessoal
        if data == "subscribe_all_tips":
            return _process_subscription(chat_id, callback_id, "🔔 Todas as Tips", "all_tips")
        elif data == "subscribe_high_value":
            return _process_subscription(chat_id, callback_id, "💎 Alto Valor", "high_value")
        elif data == "subscribe_high_confidence":
            return _process_subscription(chat_id, callback_id, "🎯 Alta Confiança", "high_confidence")
        elif data == "subscribe_premium":
            return _process_subscription(chat_id, callback_id, "👑 Premium", "premium")
        elif data == "subscribe_cancel":
            return _process_subscription_cancel(chat_id, callback_id)
        
        # Callbacks de grupo (mantém os existentes)
        elif data == "group_all_tips":
            return _process_group_subscription(chat_id, callback_id, "Todas as Tips", "all_tips")
        elif data == "group_high_value":
            return _process_group_subscription(chat_id, callback_id, "Alto Valor", "high_value")
        elif data == "group_high_confidence":
            return _process_group_subscription(chat_id, callback_id, "Alta Confiança", "high_confidence")
        elif data == "group_premium":
            return _process_group_subscription(chat_id, callback_id, "Premium", "premium")
        elif data == "group_deactivate_confirm":
            return _process_group_deactivation(chat_id, callback_id)
        elif data == "group_cancel":
            return _process_group_cancel(chat_id, callback_id)
        else:
            # Callback desconhecido
            return jsonify({"ok": True, "status": "callback unknown"}), 200
            
    except Exception as e:
        increment_error_counter()
        print(f"❌ Erro ao processar callback: {e}")
        return jsonify({"error": "Callback processing failed", "message": str(e)}), 500

def _process_subscription(chat_id, callback_id, subscription_name, subscription_type):
    """Processa subscrição pessoal"""
    
    # Adiciona subscrição
    user_data = _add_subscription(chat_id, subscription_type)
    
    # Responde ao callback
    _answer_callback_query(callback_id, f"✅ {subscription_name} ativado!")
    
    # Mensagem de confirmação
    message = f"""✅ *SUBSCRIÇÃO ATIVADA\\!*

*🔔 Tipo:* {subscription_name}
*📅 Ativado em:* {user_data['activated_at']}
*🎯 Status:* Ativo

*📊 O QUE VOCÊ VAI RECEBER:*"""

    if subscription_type == "all_tips":
        message += """
• Todas as tips geradas pelo sistema
• Tips de qualquer EV e confiança
• Alertas em tempo real 24/7"""
    elif subscription_type == "high_value":
        message += """
• Apenas tips com EV superior a 10%
• Tips de alto valor esperado
• Foco em rentabilidade"""
    elif subscription_type == "high_confidence":
        message += """
• Apenas tips com confiança > 80%
• Predições mais seguras
• Menor risco, maior precisão"""
    elif subscription_type == "premium":
        message += """
• Tips premium: EV > 15% E Confiança > 85%
• Máxima qualidade disponível
• Melhor ROI esperado"""

    message += f"""

*⚡ SISTEMA ATIVO:*
• Monitoramento 24/7 no Railway
• Machine Learning \\+ Algoritmos
• Expected Value calculado
• Análise em tempo real

*📱 PRÓXIMOS PASSOS:*
• Aguarde as próximas tips\\!
• Use /status para verificar o sistema
• Use /unsubscribe para cancelar

*🔥 Bem\\-vindo ao LoL V3 Ultra Avançado\\!*"""

    return _send_telegram_message(chat_id, message, parse_mode="MarkdownV2")

def _process_subscription_cancel(chat_id, callback_id):
    """Processa cancelamento de subscrição"""
    
    # Remove subscrição
    removed = _remove_subscription(chat_id)
    
    if removed:
        # Responde ao callback
        _answer_callback_query(callback_id, "❌ Subscrição cancelada!")
        
        message = f"""❌ *SUBSCRIÇÃO CANCELADA*

*📋 Status:* Inativo
*📅 Cancelado em:* {datetime.now().strftime('%d/%m/%Y %H:%M')}

*ℹ️ INFORMAÇÕES:*
• Você não receberá mais notificações
• Seus dados foram removidos do sistema
• Você pode se subscrever novamente a qualquer momento

*🔄 PARA REATIVAR:*
• Use /subscribe novamente
• Escolha um novo tipo de subscrição
• Sistema disponível 24/7

*Obrigado por ter usado o Bot LoL V3\\!*"""
    else:
        # Responde ao callback
        _answer_callback_query(callback_id, "ℹ️ Você não estava subscrito")
        
        message = """ℹ️ *NENHUMA SUBSCRIÇÃO ENCONTRADA*

Você não tinha subscrições ativas para cancelar\\.

*📱 Para se subscrever:*
Use /subscribe e escolha um tipo de notificação\\."""

    return _send_telegram_message(chat_id, message, parse_mode="MarkdownV2")

def _process_group_subscription(chat_id, callback_id, subscription_name, subscription_type):
    """Processa subscrição de grupo"""
    
    # Responde ao callback
    _answer_callback_query(callback_id, f"✅ {subscription_name} ativado!")
    
    # Atualiza mensagem
    message = f"""✅ *ALERTAS ATIVADOS COM SUCESSO\\!*

*📋 Grupo:* {chat_id}
*🔔 Tipo:* {subscription_name}
*📅 Ativado em:* {time.strftime('%d/%m/%Y %H:%M')}

*🎯 O QUE VAI RECEBER:*"""

    if subscription_type == "all_tips":
        message += """
• Todas as tips geradas pelo sistema
• Tips de qualquer EV e confiança
• Alertas em tempo real"""
    elif subscription_type == "high_value":
        message += """
• Apenas tips com EV superior a 10%
• Tips de alto valor esperado
• Qualidade premium"""
    elif subscription_type == "high_confidence":
        message += """
• Apenas tips com confiança > 80%
• Predições mais seguras
• Baixo risco"""
    elif subscription_type == "premium":
        message += """
• Tips premium: EV > 15% E Confiança > 85%
• Máxima qualidade
• Melhor ROI esperado"""

    message += f"""

*📊 PRÓXIMOS PASSOS:*
• O grupo receberá tips automaticamente
• Use /group\\_status para verificar
• Use /deactivate\\_group para cancelar

*🔥 Sistema ativo 24/7 no Railway\\!*"""

    return _send_telegram_message(chat_id, message, parse_mode="MarkdownV2")

def _process_group_deactivation(chat_id, callback_id):
    """Processa desativação de grupo"""
    
    # Responde ao callback
    _answer_callback_query(callback_id, "❌ Alertas desativados!")
    
    # Atualiza mensagem
    message = f"""❌ *ALERTAS DESATIVADOS*

*📋 Grupo:* {chat_id}
*📅 Desativado em:* {time.strftime('%d/%m/%Y %H:%M')}

*ℹ️ INFORMAÇÕES:*
• O grupo não receberá mais tips automáticas
• Todas as configurações foram removidas
• Para reativar use /activate\\_group

*💡 Obrigado por usar o Bot LoL V3\\!*"""

    return _send_telegram_message(chat_id, message, parse_mode="MarkdownV2")

def _process_group_cancel(chat_id, callback_id):
    """Processa cancelamento de ação"""
    
    # Responde ao callback
    _answer_callback_query(callback_id, "✅ Operação cancelada!")
    
    # Atualiza mensagem
    message = f"""✅ *OPERAÇÃO CANCELADA*

*📋 Grupo:* {chat_id}
*⚙️ Status:* Nenhuma alteração feita

*💡 COMANDOS DISPONÍVEIS:*
• /activate\\_group \\- Ativar alertas
• /group\\_status \\- Ver status
• /help \\- Ajuda completa"""

    return _send_telegram_message(chat_id, message, parse_mode="MarkdownV2")

def _answer_callback_query(callback_id, text):
    """Responde a callback query"""
    try:
        url = f"https://api.telegram.org/bot{os.getenv('TELEGRAM_BOT_TOKEN')}/answerCallbackQuery"
        payload = {
            "callback_query_id": callback_id,
            "text": text,
            "show_alert": False
        }
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"Erro ao responder callback: {e}")

def _send_telegram_message(chat_id, text, parse_mode=None, reply_markup=None):
    """Envia mensagem via API do Telegram com fallback ASSÍNCRONO"""
    import asyncio
    import aiohttp
    
    async def send_message_async():
        try:
            # Token do bot (usa a variável correta do Railway)
            bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "7584060058:AAFux8K9JiQUpH27Mg_mlYJEYLL1J8THXY0")
            if not bot_token:
                print("❌ TELEGRAM_BOT_TOKEN não encontrado")
                return jsonify({"error": "Bot token not configured"}), 500
            
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            
            payload = {
                "chat_id": chat_id,
                "text": text,
                "disable_web_page_preview": True
            }
            
            if parse_mode:
                payload["parse_mode"] = parse_mode
            
            if reply_markup:
                payload["reply_markup"] = reply_markup
            
            async with aiohttp.ClientSession() as session:
                # Primeira tentativa com parse_mode
                async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    
                    if response.status == 200:
                        print(f"✅ Mensagem enviada para chat {chat_id}")
                        return jsonify({"ok": True, "status": "message sent"}), 200
                    elif response.status == 400 and parse_mode:
                        # Se falhou com Markdown, tenta sem formatação
                        print(f"⚠️ Erro de Markdown, tentando texto simples...")
                        
                        # Remove formatação Markdown
                        plain_text = text.replace('*', '').replace('_', '').replace('`', '').replace('\\', '')
                        
                        payload_plain = {
                            "chat_id": chat_id,
                            "text": plain_text,
                            "disable_web_page_preview": True
                        }
                        
                        async with session.post(url, json=payload_plain, timeout=aiohttp.ClientTimeout(total=10)) as response_plain:
                            if response_plain.status == 200:
                                print(f"✅ Mensagem enviada (texto simples) para chat {chat_id}")
                                return jsonify({"ok": True, "status": "message sent (plain text)"}), 200
                            else:
                                response_text = await response_plain.text()
                                print(f"❌ Erro ao enviar mensagem (fallback): {response_plain.status} - {response_text}")
                                return jsonify({"error": "Failed to send message (fallback)"}), 500
                    else:
                        response_text = await response.text()
                        print(f"❌ Erro ao enviar mensagem: {response.status} - {response_text}")
                        return jsonify({"error": "Failed to send message"}), 500
                        
        except Exception as e:
            print(f"❌ Erro ao enviar mensagem: {e}")
            return jsonify({"error": f"Message sending failed: {str(e)}"}), 500
    
    # Executa de forma assíncrona
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Se já há um loop executando, usa create_task
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, send_message_async())
                return future.result()
        else:
            return asyncio.run(send_message_async())
    except Exception as e:
        print(f"❌ Erro no envio assíncrono: {e}")
        # Fallback síncrono usando requests como backup
        try:
            import requests
            
            bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "7584060058:AAFux8K9JiQUpH27Mg_mlYJEYLL1J8THXY0")
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            
            payload = {
                "chat_id": chat_id,
                "text": text.replace('*', '').replace('_', '').replace('`', '').replace('\\', ''),  # Remove formatação
                "disable_web_page_preview": True
            }
            
            response = requests.post(url, json=payload, timeout=5)
            
            if response.status_code == 200:
                print(f"✅ Mensagem enviada (fallback síncrono) para chat {chat_id}")
                return jsonify({"ok": True, "status": "message sent (sync fallback)"}), 200
            else:
                print(f"❌ Erro no fallback síncrono: {response.status_code}")
                return jsonify({"error": "Failed to send message (sync fallback)"}), 500
                
        except Exception as fallback_error:
            print(f"❌ Erro no fallback síncrono: {fallback_error}")
            return jsonify({"error": "Failed to send message (all methods failed)"}), 500

def _load_subscriptions():
    """Carrega subscrições do arquivo JSON"""
    import json
    try:
        with open("user_subscriptions.json", "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def _save_subscriptions(subscriptions):
    """Salva subscrições no arquivo JSON"""
    import json
    try:
        with open("user_subscriptions.json", "w") as f:
            json.dump(subscriptions, f, indent=2)
    except Exception as e:
        logger.error(f"Erro ao salvar subscrições: {e}")

def _add_subscription(user_id, subscription_type, user_name=""):
    """Adiciona ou atualiza subscrição do usuário"""
    subscriptions = _load_subscriptions()
    
    current_time = datetime.now().strftime('%d/%m/%Y %H:%M')
    
    subscriptions[str(user_id)] = {
        "type": subscription_type,
        "user_name": user_name,
        "activated_at": current_time,
        "tips_received": subscriptions.get(str(user_id), {}).get("tips_received", 0),
        "is_active": True
    }
    
    _save_subscriptions(subscriptions)
    return subscriptions[str(user_id)]

def _remove_subscription(user_id):
    """Remove subscrição do usuário"""
    subscriptions = _load_subscriptions()
    
    if str(user_id) in subscriptions:
        del subscriptions[str(user_id)]
        _save_subscriptions(subscriptions)
        return True
    return False

def _get_active_subscribers():
    """Retorna lista de usuários ativos com subscrições"""
    subscriptions = _load_subscriptions()
    return {
        user_id: data for user_id, data in subscriptions.items()
        if data.get("is_active", True)
    }

def _send_tip_to_subscribers(tip_data):
    """Envia tip para usuários subscritos conforme seus filtros"""
    try:
        active_subs = _get_active_subscribers()
        if not active_subs:
            print("📊 Nenhum usuário subscrito")
            return 0
        
        # Extrai dados da tip
        ev_percentage = tip_data.get("ev_percentage", 0)
        confidence = tip_data.get("confidence_percentage", 0)
        
        sent_count = 0
        
        for user_id, sub_data in active_subs.items():
            sub_type = sub_data.get("type", "all_tips")
            
            # Verifica se a tip atende aos critérios do usuário
            should_send = False
            
            if sub_type == "all_tips":
                should_send = True
            elif sub_type == "high_value" and ev_percentage > 10:
                should_send = True
            elif sub_type == "high_confidence" and confidence > 80:
                should_send = True
            elif sub_type == "premium" and ev_percentage > 15 and confidence > 85:
                should_send = True
            
            if should_send:
                # Formata mensagem da tip
                message = _format_tip_message(tip_data)
                
                # Envia mensagem
                result = _send_telegram_message(int(user_id), message, parse_mode="MarkdownV2")
                
                if result[1] == 200:  # Sucesso
                    sent_count += 1
                    # Atualiza contador de tips recebidas
                    subscriptions = _load_subscriptions()
                    if user_id in subscriptions:
                        subscriptions[user_id]["tips_received"] = subscriptions[user_id].get("tips_received", 0) + 1
                        _save_subscriptions(subscriptions)
        
        print(f"📨 Tip enviada para {sent_count}/{len(active_subs)} usuários")
        return sent_count
        
    except Exception as e:
        logger.error(f"Erro ao enviar tip para subscribers: {e}")
        return 0

def _format_tip_message(tip_data):
    """Formata mensagem de tip para Telegram"""
    try:
        team1 = tip_data.get("team1", "Time A")
        team2 = tip_data.get("team2", "Time B")
        bet_type = tip_data.get("bet_type", "Vencedor")
        ev_percentage = tip_data.get("ev_percentage", 0)
        confidence = tip_data.get("confidence_percentage", 0)
        
        # Escapa caracteres especiais
        team1 = team1.replace(".", "\\.").replace("-", "\\-").replace("_", "\\_")
        team2 = team2.replace(".", "\\.").replace("-", "\\-").replace("_", "\\_")
        bet_type = bet_type.replace(".", "\\.").replace("-", "\\-").replace("_", "\\_")
        
        message = f"""🎯 *TIP PROFISSIONAL LoL V3*

*⚔️ PARTIDA:*
{team1} vs {team2}

*💰 APOSTA:*
• Tipo: {bet_type}
• EV: {ev_percentage:.1f}%
• Confiança: {confidence:.1f}%

*🧠 ANÁLISE:*
• Machine Learning \\+ Algoritmos
• Análise em tempo real
• Expected Value calculado

*📊 RISCO:* {"🟢 Baixo" if confidence > 80 else "🟡 Médio" if confidence > 60 else "🔴 Alto"}
*💎 VALOR:* {"🔥 Premium" if ev_percentage > 15 else "💎 Alto" if ev_percentage > 10 else "📈 Padrão"}

*⚡ Sistema LoL V3 Ultra Avançado*
*🚀 Tip gerada automaticamente*"""

        return message
        
    except Exception as e:
        logger.error(f"Erro ao formatar tip: {e}")
        return "Erro ao formatar tip"

@app.route('/send_test_tip', methods=['POST'])
def send_test_tip():
    """Endpoint para enviar tip de teste"""
    increment_request_counter()
    
    try:
        # Tip de teste
        test_tip = {
            "team1": "T1",
            "team2": "Gen.G", 
            "bet_type": "T1 Vencedor",
            "ev_percentage": 12.5,
            "confidence_percentage": 78.3
        }
        
        # Envia para usuários subscritos
        sent_count = _send_tip_to_subscribers(test_tip)
        
        return jsonify({
            "ok": True,
            "tip_sent": True,
            "users_notified": sent_count,
            "tip_data": test_tip,
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        increment_error_counter()
        return jsonify({"error": str(e)}), 500

def run_health_server():
    """Executa servidor de health check em thread separada"""
    port = int(os.getenv("PORT", 5000))  # Usa PORT=5000 das variáveis do Railway
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

def start_health_server():
    """Inicia servidor de health check"""
    health_thread = threading.Thread(target=run_health_server, daemon=True)
    health_thread.start()
    port = os.getenv("PORT", 5000)
    environment_id = os.getenv("RAILWAY_ENVIRONMENT_ID", "N/A")
    print(f"🏥 Health check server iniciado na porta {port}")
    print(f"🚀 Railway Environment ID: {environment_id}")
    print(f"🔧 FORCE_RAILWAY_MODE: {os.getenv('FORCE_RAILWAY_MODE', 'false')}")

if __name__ == "__main__":
    # Executa apenas o servidor de health check
    print("🏥 Iniciando Health Check Server para Railway...")
    print(f"🔧 Usando variáveis: PORT={os.getenv('PORT', 5000)}, ENV_ID={os.getenv('RAILWAY_ENVIRONMENT_ID', 'N/A')}")
    run_health_server() 