#!/usr/bin/env python3
"""
Live Sentiment Analyzer - Sistema de Análise de Sentimento em Tempo Real
Funcionalidades:
- Análise de sentimento de redes sociais
- Monitoramento de notícias esportivas
- Sentimento em tempo real de jogadores/times
- Alertas de mudanças de sentimento
"""

import logging
import asyncio
import aiohttp
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import json
import re
from dataclasses import dataclass
from collections import defaultdict
import time

logger = logging.getLogger(__name__)

@dataclass
class SentimentData:
    """Dados de sentimento para um time/jogador"""
    entity: str
    sentiment_score: float  # -1.0 (muito negativo) a +1.0 (muito positivo)
    confidence: float       # 0.0 a 1.0
    source: str            # twitter, reddit, news, etc.
    text: str              # Texto original
    timestamp: datetime
    impact_level: str      # low, medium, high
    category: str          # injury, performance, transfer, etc.

@dataclass
class SentimentAlert:
    """Alerta de mudança de sentimento"""
    entity: str
    old_sentiment: float
    new_sentiment: float
    change_magnitude: float
    trigger_reason: str
    timestamp: datetime
    sources_count: int
    confidence: float

class SentimentAnalyzer:
    """Analisador de sentimento em tempo real para apostas esportivas"""
    
    def __init__(self):
        self.sentiment_history: Dict[str, List[SentimentData]] = defaultdict(list)
        self.current_sentiment: Dict[str, float] = {}
        self.alert_thresholds = {
            'major_change': 0.3,    # Mudança de 0.3+ no score
            'minor_change': 0.15,   # Mudança de 0.15+ no score
            'time_window': 30       # Janela de 30 minutos para detecção
        }
        
        # Keywords para diferentes categorias
        self.category_keywords = {
            'injury': ['injured', 'hurt', 'pain', 'hospital', 'medical', 'lesão', 'machucado', 'contusão'],
            'performance': ['goal', 'assist', 'save', 'miss', 'error', 'gol', 'assistência', 'defesa', 'erro'],
            'transfer': ['transfer', 'move', 'sign', 'deal', 'contract', 'transferência', 'contrato', 'acordo'],
            'suspension': ['suspended', 'ban', 'card', 'red', 'yellow', 'suspenso', 'cartão', 'expulso'],
            'form': ['win', 'loss', 'streak', 'form', 'vitória', 'derrota', 'sequência', 'forma']
        }
        
        # Sentiment keywords
        self.positive_keywords = [
            'excellent', 'amazing', 'best', 'great', 'fantastic', 'outstanding', 'brilliant',
            'excelente', 'incrível', 'melhor', 'ótimo', 'fantástico', 'brilhante'
        ]
        
        self.negative_keywords = [
            'terrible', 'worst', 'awful', 'bad', 'horrible', 'disappointing', 'poor',
            'terrível', 'pior', 'horrível', 'ruim', 'decepcionante', 'fraco'
        ]
        
        logger.info("🎭 Sentiment Analyzer inicializado")
    
    async def analyze_text_sentiment(self, text: str) -> Tuple[float, float, str]:
        """
        Analisa sentimento de um texto
        
        Returns:
            (sentiment_score, confidence, category)
        """
        try:
            text_lower = text.lower()
            
            # Calcular score de sentimento básico
            positive_count = sum(1 for word in self.positive_keywords if word in text_lower)
            negative_count = sum(1 for word in self.negative_keywords if word in text_lower)
            
            # Score básico baseado em palavras-chave
            if positive_count > negative_count:
                base_score = 0.6 + (positive_count - negative_count) * 0.1
            elif negative_count > positive_count:
                base_score = -0.6 - (negative_count - positive_count) * 0.1
            else:
                base_score = 0.0
            
            # Limitar score entre -1 e 1
            sentiment_score = max(-1.0, min(1.0, base_score))
            
            # Calcular confiança baseada na quantidade de indicadores
            total_indicators = positive_count + negative_count
            confidence = min(0.9, 0.3 + total_indicators * 0.15)
            
            # Determinar categoria
            category = self._determine_category(text_lower)
            
            return sentiment_score, confidence, category
            
        except Exception as e:
            logger.error(f"❌ Erro na análise de sentimento: {e}")
            return 0.0, 0.0, "unknown"
    
    def _determine_category(self, text: str) -> str:
        """Determina categoria do texto baseado em palavras-chave"""
        category_scores = {}
        
        for category, keywords in self.category_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text)
            if score > 0:
                category_scores[category] = score
        
        if category_scores:
            return max(category_scores, key=category_scores.get)
        return "general"
    
    async def monitor_social_media(self, entities: List[str], sources: List[str] = None) -> List[SentimentData]:
        """
        Monitora redes sociais para sentimento sobre entidades
        
        Args:
            entities: Lista de times/jogadores para monitorar
            sources: Lista de fontes (twitter, reddit, etc.)
        """
        if sources is None:
            sources = ['twitter', 'reddit']
        
        sentiment_data = []
        
        try:
            for entity in entities:
                for source in sources:
                    # Simular coleta de dados de redes sociais
                    # Em implementação real, usar APIs do Twitter, Reddit, etc.
                    posts = await self._simulate_social_media_posts(entity, source)
                    
                    for post in posts:
                        sentiment_score, confidence, category = await self.analyze_text_sentiment(post['text'])
                        
                        data = SentimentData(
                            entity=entity,
                            sentiment_score=sentiment_score,
                            confidence=confidence,
                            source=source,
                            text=post['text'][:200],  # Limitar tamanho
                            timestamp=datetime.now(),
                            impact_level=self._calculate_impact_level(sentiment_score, confidence),
                            category=category
                        )
                        
                        sentiment_data.append(data)
                        
                        # Adicionar ao histórico
                        self.sentiment_history[entity].append(data)
            
            logger.info(f"📱 Coletados {len(sentiment_data)} posts de sentimento")
            return sentiment_data
            
        except Exception as e:
            logger.error(f"❌ Erro no monitoramento de redes sociais: {e}")
            return []
    
    async def _simulate_social_media_posts(self, entity: str, source: str) -> List[Dict]:
        """Simula posts de redes sociais (substituir por API real)"""
        # Esta é uma simulação - em produção, usar APIs reais
        sample_posts = [
            {"text": f"{entity} is playing amazing football today! Best performance this season!", "engagement": 150},
            {"text": f"Disappointed with {entity}'s performance. They need to step up.", "engagement": 89},
            {"text": f"{entity} scored an incredible goal! What a player!", "engagement": 203},
            {"text": f"Worried about {entity}'s injury. Hope it's not serious.", "engagement": 76},
            {"text": f"{entity} looking in great form recently. Could be a great betting opportunity.", "engagement": 112}
        ]
        
        # Retornar 2-5 posts aleatórios
        import random
        return random.sample(sample_posts, random.randint(2, min(5, len(sample_posts))))
    
    def _calculate_impact_level(self, sentiment_score: float, confidence: float) -> str:
        """Calcula nível de impacto baseado no score e confiança"""
        impact_value = abs(sentiment_score) * confidence
        
        if impact_value >= 0.7:
            return "high"
        elif impact_value >= 0.4:
            return "medium"
        else:
            return "low"
    
    async def analyze_news_sentiment(self, entities: List[str]) -> List[SentimentData]:
        """Analisa sentimento de notícias esportivas"""
        sentiment_data = []
        
        try:
            for entity in entities:
                # Simular busca de notícias (substituir por API real)
                news_articles = await self._simulate_news_articles(entity)
                
                for article in news_articles:
                    sentiment_score, confidence, category = await self.analyze_text_sentiment(
                        article['title'] + " " + article['content']
                    )
                    
                    data = SentimentData(
                        entity=entity,
                        sentiment_score=sentiment_score,
                        confidence=confidence,
                        source="news",
                        text=article['title'],
                        timestamp=datetime.now(),
                        impact_level=self._calculate_impact_level(sentiment_score, confidence),
                        category=category
                    )
                    
                    sentiment_data.append(data)
                    self.sentiment_history[entity].append(data)
            
            logger.info(f"📰 Analisadas {len(sentiment_data)} notícias")
            return sentiment_data
            
        except Exception as e:
            logger.error(f"❌ Erro na análise de notícias: {e}")
            return []
    
    async def _simulate_news_articles(self, entity: str) -> List[Dict]:
        """Simula artigos de notícias (substituir por API real)"""
        sample_articles = [
            {
                "title": f"{entity} Signs New Contract Extension",
                "content": f"{entity} has agreed to a new long-term contract, showing commitment to the club."
            },
            {
                "title": f"Injury Update: {entity} Expected to Return Soon", 
                "content": f"Medical staff optimistic about {entity}'s recovery timeline."
            },
            {
                "title": f"{entity} Breaks Goal-Scoring Record",
                "content": f"Outstanding performance from {entity} in yesterday's match."
            }
        ]
        
        import random
        return random.sample(sample_articles, random.randint(1, len(sample_articles)))
    
    def calculate_entity_sentiment(self, entity: str, time_window_minutes: int = 60) -> Dict:
        """
        Calcula sentimento agregado para uma entidade
        
        Args:
            entity: Nome do time/jogador
            time_window_minutes: Janela de tempo para considerar (em minutos)
        """
        try:
            cutoff_time = datetime.now() - timedelta(minutes=time_window_minutes)
            
            # Filtrar dados recentes
            recent_data = [
                data for data in self.sentiment_history[entity]
                if data.timestamp >= cutoff_time
            ]
            
            if not recent_data:
                return {
                    'entity': entity,
                    'sentiment_score': 0.0,
                    'confidence': 0.0,
                    'data_points': 0,
                    'sources': [],
                    'categories': {},
                    'impact_levels': {},
                    'trend': 'neutral'
                }
            
            # Calcular métricas agregadas
            total_sentiment = sum(data.sentiment_score * data.confidence for data in recent_data)
            total_confidence = sum(data.confidence for data in recent_data)
            
            avg_sentiment = total_sentiment / total_confidence if total_confidence > 0 else 0.0
            avg_confidence = total_confidence / len(recent_data)
            
            # Análise por fonte
            sources = list(set(data.source for data in recent_data))
            
            # Análise por categoria
            categories = defaultdict(list)
            for data in recent_data:
                categories[data.category].append(data.sentiment_score)
            
            category_avg = {
                cat: sum(scores) / len(scores) 
                for cat, scores in categories.items()
            }
            
            # Análise por nível de impacto
            impact_levels = defaultdict(int)
            for data in recent_data:
                impact_levels[data.impact_level] += 1
            
            # Determinar tendência
            trend = self._calculate_trend(entity, time_window_minutes)
            
            # Atualizar sentimento atual
            self.current_sentiment[entity] = avg_sentiment
            
            return {
                'entity': entity,
                'sentiment_score': round(avg_sentiment, 3),
                'confidence': round(avg_confidence, 3),
                'data_points': len(recent_data),
                'sources': sources,
                'categories': category_avg,
                'impact_levels': dict(impact_levels),
                'trend': trend,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Erro no cálculo de sentimento: {e}")
            return {}
    
    def _calculate_trend(self, entity: str, time_window_minutes: int) -> str:
        """Calcula tendência de sentimento"""
        try:
            cutoff_time = datetime.now() - timedelta(minutes=time_window_minutes)
            recent_data = [
                data for data in self.sentiment_history[entity]
                if data.timestamp >= cutoff_time
            ]
            
            if len(recent_data) < 3:
                return "neutral"
            
            # Dividir em primeira e segunda metade
            mid_point = len(recent_data) // 2
            first_half = recent_data[:mid_point]
            second_half = recent_data[mid_point:]
            
            avg_first = sum(d.sentiment_score for d in first_half) / len(first_half)
            avg_second = sum(d.sentiment_score for d in second_half) / len(second_half)
            
            difference = avg_second - avg_first
            
            if difference > 0.1:
                return "improving"
            elif difference < -0.1:
                return "declining"
            else:
                return "stable"
                
        except Exception:
            return "neutral"
    
    def detect_sentiment_alerts(self, entities: List[str]) -> List[SentimentAlert]:
        """Detecta alertas de mudanças significativas de sentimento"""
        alerts = []
        
        try:
            for entity in entities:
                current_sentiment = self.current_sentiment.get(entity, 0.0)
                
                # Verificar histórico recente para mudanças
                cutoff_time = datetime.now() - timedelta(minutes=self.alert_thresholds['time_window'])
                recent_data = [
                    data for data in self.sentiment_history[entity]
                    if data.timestamp >= cutoff_time
                ]
                
                if len(recent_data) < 3:
                    continue
                
                # Calcular sentimento anterior (primeira metade da janela)
                mid_time = cutoff_time + timedelta(minutes=self.alert_thresholds['time_window'] // 2)
                old_data = [d for d in recent_data if d.timestamp < mid_time]
                new_data = [d for d in recent_data if d.timestamp >= mid_time]
                
                if not old_data or not new_data:
                    continue
                
                old_sentiment = sum(d.sentiment_score * d.confidence for d in old_data) / sum(d.confidence for d in old_data)
                new_sentiment = sum(d.sentiment_score * d.confidence for d in new_data) / sum(d.confidence for d in new_data)
                
                change_magnitude = abs(new_sentiment - old_sentiment)
                
                # Verificar se mudança é significativa
                if change_magnitude >= self.alert_thresholds['major_change']:
                    alert_type = "major"
                elif change_magnitude >= self.alert_thresholds['minor_change']:
                    alert_type = "minor"
                else:
                    continue
                
                # Determinar razão da mudança
                recent_categories = [d.category for d in new_data]
                most_common_category = max(set(recent_categories), key=recent_categories.count)
                
                trigger_reason = f"{alert_type.title()} sentiment change detected - likely due to {most_common_category} related news"
                
                alert = SentimentAlert(
                    entity=entity,
                    old_sentiment=round(old_sentiment, 3),
                    new_sentiment=round(new_sentiment, 3),
                    change_magnitude=round(change_magnitude, 3),
                    trigger_reason=trigger_reason,
                    timestamp=datetime.now(),
                    sources_count=len(set(d.source for d in new_data)),
                    confidence=sum(d.confidence for d in new_data) / len(new_data)
                )
                
                alerts.append(alert)
                logger.info(f"🚨 Alerta de sentimento: {entity} - Mudança de {old_sentiment:.3f} para {new_sentiment:.3f}")
            
            return alerts
            
        except Exception as e:
            logger.error(f"❌ Erro na detecção de alertas: {e}")
            return []
    
    async def get_sentiment_report(self, entities: List[str]) -> Dict:
        """Gera relatório completo de sentimento"""
        try:
            # Coletar dados recentes
            social_data = await self.monitor_social_media(entities)
            news_data = await self.analyze_news_sentiment(entities)
            
            # Calcular sentimentos por entidade
            entity_sentiments = {}
            for entity in entities:
                entity_sentiments[entity] = self.calculate_entity_sentiment(entity)
            
            # Detectar alertas
            alerts = self.detect_sentiment_alerts(entities)
            
            # Análise geral
            all_scores = [sentiment['sentiment_score'] for sentiment in entity_sentiments.values() if sentiment.get('sentiment_score')]
            
            overall_sentiment = sum(all_scores) / len(all_scores) if all_scores else 0.0
            
            return {
                'timestamp': datetime.now().isoformat(),
                'overall_sentiment': round(overall_sentiment, 3),
                'entity_sentiments': entity_sentiments,
                'alerts': [
                    {
                        'entity': alert.entity,
                        'change': f"{alert.old_sentiment:.3f} → {alert.new_sentiment:.3f}",
                        'magnitude': alert.change_magnitude,
                        'reason': alert.trigger_reason,
                        'confidence': alert.confidence
                    } for alert in alerts
                ],
                'data_summary': {
                    'social_media_posts': len(social_data),
                    'news_articles': len(news_data),
                    'total_entities': len(entities),
                    'entities_with_alerts': len(set(alert.entity for alert in alerts))
                },
                'recommendations': self._generate_sentiment_recommendations(entity_sentiments, alerts)
            }
            
        except Exception as e:
            logger.error(f"❌ Erro no relatório de sentimento: {e}")
            return {}
    
    def _generate_sentiment_recommendations(self, entity_sentiments: Dict, alerts: List[SentimentAlert]) -> List[str]:
        """Gera recomendações baseadas na análise de sentimento"""
        recommendations = []
        
        try:
            # Análise por entidade
            for entity, sentiment_data in entity_sentiments.items():
                if not sentiment_data:
                    continue
                
                score = sentiment_data.get('sentiment_score', 0.0)
                confidence = sentiment_data.get('confidence', 0.0)
                trend = sentiment_data.get('trend', 'neutral')
                
                if score > 0.5 and confidence > 0.7:
                    recommendations.append(f"🟢 {entity}: Sentimento muito positivo. Considere apostas favoráveis.")
                elif score < -0.5 and confidence > 0.7:
                    recommendations.append(f"🔴 {entity}: Sentimento muito negativo. Evite apostas favoráveis.")
                elif trend == "improving":
                    recommendations.append(f"📈 {entity}: Sentimento melhorando. Oportunidade emergente.")
                elif trend == "declining":
                    recommendations.append(f"📉 {entity}: Sentimento declinando. Cautela recomendada.")
            
            # Análise de alertas
            for alert in alerts:
                if alert.change_magnitude > 0.4:
                    recommendations.append(f"🚨 {alert.entity}: Mudança drástica de sentimento! Revisar apostas.")
                elif alert.new_sentiment > alert.old_sentiment:
                    recommendations.append(f"⬆️ {alert.entity}: Sentimento melhorando rapidamente.")
                else:
                    recommendations.append(f"⬇️ {alert.entity}: Sentimento deteriorando rapidamente.")
            
            if not recommendations:
                recommendations.append("✅ Sentimentos estáveis. Nenhuma ação imediata necessária.")
                
        except Exception as e:
            logger.error(f"❌ Erro nas recomendações: {e}")
            recommendations.append("❌ Erro na análise de sentimento.")
        
        return recommendations
    
    def export_sentiment_data(self, entity: str = None, hours: int = 24) -> Dict:
        """Exporta dados de sentimento para análise"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            if entity:
                entities_to_export = [entity]
            else:
                entities_to_export = list(self.sentiment_history.keys())
            
            export_data = {}
            
            for ent in entities_to_export:
                filtered_data = [
                    {
                        'sentiment_score': d.sentiment_score,
                        'confidence': d.confidence,
                        'source': d.source,
                        'category': d.category,
                        'impact_level': d.impact_level,
                        'timestamp': d.timestamp.isoformat(),
                        'text_snippet': d.text[:100]
                    }
                    for d in self.sentiment_history[ent]
                    if d.timestamp >= cutoff_time
                ]
                
                export_data[ent] = {
                    'data_points': filtered_data,
                    'summary': self.calculate_entity_sentiment(ent, hours * 60)
                }
            
            return {
                'export_timestamp': datetime.now().isoformat(),
                'time_range_hours': hours,
                'entities': export_data
            }
            
        except Exception as e:
            logger.error(f"❌ Erro na exportação: {e}")
            return {}


# Exemplo de uso
if __name__ == "__main__":
    async def main():
        # Inicializar analisador
        analyzer = SentimentAnalyzer()
        
        # Entidades para monitorar
        entities = ["Manchester City", "Liverpool", "Cristiano Ronaldo", "Messi"]
        
        # Gerar relatório de sentimento
        report = await analyzer.get_sentiment_report(entities)
        
        print("🎭 RELATÓRIO DE SENTIMENTO")
        print(f"Sentimento Geral: {report['overall_sentiment']:.3f}")
        print(f"Alertas Detectados: {len(report['alerts'])}")
        
        for entity, sentiment in report['entity_sentiments'].items():
            if sentiment:
                print(f"\n{entity}:")
                print(f"  Score: {sentiment['sentiment_score']:.3f}")
                print(f"  Confiança: {sentiment['confidence']:.3f}")
                print(f"  Tendência: {sentiment['trend']}")
        
        print("\n📋 RECOMENDAÇÕES:")
        for rec in report['recommendations']:
            print(f"  {rec}")
    
    asyncio.run(main()) 