"""
Enhanced API Routes for Advanced Features
Includes RAG, confidence routing, FMEA, quality metrics, and trust configuration
"""
from fastapi import FastAPI, HTTPException, Query
from typing import Optional, List, Dict
from datetime import datetime

from models import (
    TicketCategory, FeedbackType, ConfidenceLevel, ResponseQuality,
    TrustArchitectureConfig
)
from knowledge_base import get_knowledge_base
from confidence_router import get_confidence_router
from fmea_tracker import get_fmea_tracker
from quality_metrics import get_quality_evaluator
from prompt_manager import get_prompt_engineer


def setup_advanced_routes(app: FastAPI):
    """Setup advanced API routes for the enhanced features"""
    
    kb = get_knowledge_base()
    router = get_confidence_router()
    fmea = get_fmea_tracker()
    evaluator = get_quality_evaluator()
    prompt_eng = get_prompt_engineer()
    
    # ============ KNOWLEDGE BASE ENDPOINTS ============
    
    @app.get("/knowledge-base/articles", tags=["Knowledge Base"])
    def list_articles(category: Optional[str] = None, skip: int = 0, limit: int = 50):
        """List all knowledge base articles"""
        articles = list(kb.articles.values())
        
        if category:
            articles = [a for a in articles if a.get("category") == category]
        
        return {
            "total": len(articles),
            "articles": articles[skip:skip+limit]
        }
    
    @app.post("/knowledge-base/articles", tags=["Knowledge Base"])
    def create_article(title: str, content: str, category: str, tags: List[str] = None):
        """Create a new knowledge base article"""
        article_id = f"{category}_{len(kb.articles)+1:03d}"
        
        article = kb.add_article(
            article_id=article_id,
            title=title,
            content=content,
            category=category,
            tags=tags or []
        )
        
        return {"status": "created", "article_id": article_id, "article": article}
    
    @app.get("/knowledge-base/search", tags=["Knowledge Base"])
    def search_knowledge_base(query: str, category: Optional[str] = None, top_k: int = 3):
        """Search knowledge base with RAG retrieval"""
        results = kb.retrieve(query, top_k=top_k, category_filter=category)
        
        return {
            "query": query,
            "results": [
                {
                    "source_id": r.source_id,
                    "source_title": r.source_title,
                    "source_content": r.source_content[:300],
                    "relevance_score": r.relevance_score
                }
                for r in results
            ]
        }
    
    @app.get("/knowledge-base/article/{article_id}", tags=["Knowledge Base"])
    def get_article(article_id: str):
        """Get a specific article"""
        article = kb.get_article(article_id)
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")
        return article
    
    @app.put("/knowledge-base/article/{article_id}", tags=["Knowledge Base"])
    def update_article(article_id: str, title: Optional[str] = None, 
                      content: Optional[str] = None, tags: Optional[List[str]] = None):
        """Update an article"""
        updates = {}
        if title:
            updates["title"] = title
        if content:
            updates["content"] = content
        if tags is not None:
            updates["tags"] = tags
        
        article = kb.update_article(article_id, **updates)
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")
        return article
    
    @app.delete("/knowledge-base/article/{article_id}", tags=["Knowledge Base"])
    def delete_article(article_id: str):
        """Delete an article"""
        if not kb.delete_article(article_id):
            raise HTTPException(status_code=404, detail="Article not found")
        return {"status": "deleted"}
    
    @app.get("/knowledge-base/stats", tags=["Knowledge Base"])
    def get_kb_stats():
        """Get knowledge base statistics"""
        return kb.get_stats()
    
    # ============ CONFIDENCE ROUTING ENDPOINTS ============
    
    @app.get("/confidence-routing/stats", tags=["Confidence Routing"])
    def get_routing_stats():
        """Get confidence routing statistics"""
        return router.get_routing_stats()
    
    @app.get("/trust-config", tags=["Trust Configuration"])
    def get_trust_config():
        """Get current trust architecture configuration"""
        return router.get_config()
    
    @app.put("/trust-config", tags=["Trust Configuration"])
    def update_trust_config(
        high_confidence_threshold: Optional[float] = None,
        medium_confidence_threshold: Optional[float] = None,
        auto_send_high_confidence: Optional[bool] = None,
        require_review_medium: Optional[bool] = None,
        escalate_low_confidence: Optional[bool] = None,
        min_quality_score_for_send: Optional[float] = None,
        max_model_age_days: Optional[int] = None,
        max_knowledge_base_age_days: Optional[int] = None
    ):
        """Update trust configuration"""
        updates = {}
        
        if high_confidence_threshold is not None:
            updates["high_confidence_threshold"] = high_confidence_threshold
        if medium_confidence_threshold is not None:
            updates["medium_confidence_threshold"] = medium_confidence_threshold
        if auto_send_high_confidence is not None:
            updates["auto_send_high_confidence"] = auto_send_high_confidence
        if require_review_medium is not None:
            updates["require_review_medium"] = require_review_medium
        if escalate_low_confidence is not None:
            updates["escalate_low_confidence"] = escalate_low_confidence
        if min_quality_score_for_send is not None:
            updates["min_quality_score_for_send"] = min_quality_score_for_send
        if max_model_age_days is not None:
            updates["max_model_age_days"] = max_model_age_days
        if max_knowledge_base_age_days is not None:
            updates["max_knowledge_base_age_days"] = max_knowledge_base_age_days
        
        router.update_config(**updates)
        return router.get_config()
    
    # ============ FMEA ENDPOINTS ============
    
    @app.get("/fmea/analysis", tags=["FMEA"])
    def get_fmea_analysis(days: int = 30):
        """Get FMEA analysis for recent failures"""
        return fmea.get_failure_analysis(time_window_days=days)
    
    @app.get("/fmea/trends", tags=["FMEA"])
    def get_fmea_trends(mode: Optional[str] = None):
        """Get failure trends over time"""
        trends = fmea.get_failure_trends(mode=mode)
        return {"trends": trends}
    
    @app.get("/fmea/high-risk-tickets", tags=["FMEA"])
    def get_high_risk_tickets(threshold: float = 0.80):
        """Get high-confidence tickets with failures"""
        return {"high_risk_tickets": fmea.get_high_risk_tickets(threshold)}
    
    @app.post("/fmea/log-failure", tags=["FMEA"])
    def log_failure(
        ticket_id: str,
        failure_mode: str,
        confidence: float,
        feedback_type: str,
        severity: str,
        root_cause: Optional[str] = None,
        mitigation: Optional[str] = None
    ):
        """Log a failure event"""
        entry = fmea.log_failure(
            ticket_id=ticket_id,
            failure_mode=failure_mode,
            confidence_at_time=confidence,
            agent_feedback=FeedbackType(feedback_type),
            severity=severity,
            root_cause=root_cause,
            mitigation=mitigation
        )
        
        return {
            "status": "logged",
            "entry": {
                "ticket_id": entry.ticket_id,
                "failure_mode": entry.failure_mode,
                "severity": entry.severity,
                "detected_at": entry.detected_at.isoformat()
            }
        }
    
    # ============ QUALITY METRICS ENDPOINTS ============
    
    @app.post("/quality-metrics/evaluate", tags=["Quality Metrics"])
    def evaluate_quality(
        response: str,
        question: str,
        category: str,
        rag_context: List[str] = None
    ):
        """Evaluate response quality using RAGAS metrics"""
        # For demo - using empty RAG results since they come from KB
        rag_sources = []
        
        metrics = evaluator.evaluate_response(
            response=response,
            ticket_description=question,
            ticket_category=category,
            rag_sources=rag_sources
        )
        
        return {
            "quality_level": metrics.quality_level.value,
            "overall_score": metrics.overall_score,
            "faithfulness": metrics.faithfulness,
            "answer_relevance": metrics.answer_relevance,
            "context_precision": metrics.context_precision,
            "context_recall": metrics.context_recall
        }
    
    # ============ PROMPT ENGINEERING ENDPOINTS ============
    
    @app.get("/prompt-templates/{category}", tags=["Prompt Engineering"])
    def get_prompt_template(category: str, tone: str = "neutral"):
        """Get prompt template for a category and tone"""
        template = prompt_eng.get_response_template(category, tone)
        system_prompt = prompt_eng.get_system_prompt(tone, category)
        
        return {
            "category": category,
            "tone": tone,
            "template": template,
            "system_prompt": system_prompt
        }
    
    @app.post("/prompt-engineering/construct", tags=["Prompt Engineering"])
    def construct_prompt(
        subject: str,
        description: str,
        category: str,
        tone: str = "neutral",
        rag_context: List[str] = None
    ):
        """Construct a full prompt with tone and RAG context"""
        prompt = prompt_eng.construct_prompt(
            subject, description, category, tone, rag_context
        )
        
        return {
            "constructed_prompt": prompt,
            "tone": tone,
            "category": category,
            "rag_context_count": len(rag_context) if rag_context else 0
        }
    
    # ============ ADVANCED STATISTICS ENDPOINTS ============
    
    @app.get("/advanced-stats", tags=["Statistics"])
    def get_advanced_stats():
        """Get comprehensive advanced statistics"""
        return {
            "knowledge_base": kb.get_stats(),
            "routing": router.get_routing_stats(),
            "fmea": fmea.get_failure_analysis(days=30),
            "timestamp": datetime.now().isoformat()
        }
