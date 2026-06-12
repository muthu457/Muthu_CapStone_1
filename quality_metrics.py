"""
Response Quality Metrics (RAGAS-inspired)
Evaluates response quality based on retrieval, relevance, and correctness
"""
from typing import List, Optional
from datetime import datetime
from models import ResponseQualityMetrics, ResponseQuality, RAGRetrievalResult


class QualityEvaluator:
    """Evaluate response quality using RAGAS-inspired metrics"""
    
    @staticmethod
    def evaluate_faithfulness(response: str, rag_sources: List[RAGRetrievalResult]) -> float:
        """
        Faithfulness: How well does the response align with retrieved sources?
        0 = completely contradicts sources
        1 = perfectly aligned with sources
        """
        if not rag_sources:
            # No sources to check against - neutral score
            return 0.5
        
        # Simple keyword overlap with sources
        response_lower = response.lower()
        source_texts = " ".join([s.source_content.lower() for s in rag_sources])
        
        response_words = set(response_lower.split())
        source_words = set(source_texts.split())
        
        # Calculate overlap
        overlap = len(response_words & source_words)
        total_response_words = len(response_words)
        
        if total_response_words == 0:
            return 0.0
        
        faithfulness = min(1.0, overlap / max(1, total_response_words * 0.5))
        return faithfulness
    
    @staticmethod
    def evaluate_answer_relevance(response: str, ticket_description: str) -> float:
        """
        Answer Relevance: How relevant is the response to the customer's question?
        0 = completely irrelevant
        1 = perfectly answers the question
        """
        if not response or not ticket_description:
            return 0.0
        
        response_lower = response.lower()
        ticket_lower = ticket_description.lower()
        
        # Extract key terms from ticket
        ticket_words = set(ticket_lower.split())
        response_words = set(response_lower.lower().split())
        
        # High overlap suggests relevant response
        overlap = len(ticket_words & response_words)
        total_ticket_words = max(1, len(ticket_words))
        
        relevance = min(1.0, overlap / total_ticket_words)
        
        # Boost if response contains actionable keywords
        actionable_keywords = ["here", "following", "click", "go to", "update", "reset", "change"]
        if any(kw in response_lower for kw in actionable_keywords):
            relevance = min(1.0, relevance + 0.15)
        
        return relevance
    
    @staticmethod
    def evaluate_context_precision(rag_sources: List[RAGRetrievalResult], 
                                   ticket_category: str) -> float:
        """
        Context Precision: How precise are the retrieved sources?
        Measures how many top sources are relevant to the category
        """
        if not rag_sources:
            return 0.0
        
        # Calculate relevance by score
        precision_sum = sum(s.relevance_score for s in rag_sources)
        avg_precision = precision_sum / len(rag_sources)
        
        return avg_precision
    
    @staticmethod
    def evaluate_context_recall(rag_sources: List[RAGRetrievalResult]) -> float:
        """
        Context Recall: Did we retrieve sufficient context?
        More sources = higher recall (up to a point)
        """
        if not rag_sources:
            return 0.0
        
        # 3+ sources = good recall (1.0)
        # 2 sources = 0.7
        # 1 source = 0.4
        recall_mapping = {
            0: 0.0,
            1: 0.4,
            2: 0.7,
            3: 0.85,
            4: 0.90,
            5: 1.0
        }
        
        source_count = min(5, len(rag_sources))
        return recall_mapping.get(source_count, 1.0)
    
    @staticmethod
    def evaluate_response(
        response: str,
        ticket_description: str,
        ticket_category: str,
        rag_sources: List[RAGRetrievalResult],
        agent_feedback: Optional[str] = None
    ) -> ResponseQualityMetrics:
        """
        Comprehensive response quality evaluation
        Returns metrics including individual RAGAS scores and overall quality
        """
        
        faithfulness = QualityEvaluator.evaluate_faithfulness(response, rag_sources)
        answer_relevance = QualityEvaluator.evaluate_answer_relevance(response, ticket_description)
        context_precision = QualityEvaluator.evaluate_context_precision(rag_sources, ticket_category)
        context_recall = QualityEvaluator.evaluate_context_recall(rag_sources)
        
        # Weighted average for overall score
        weights = {
            "faithfulness": 0.25,
            "answer_relevance": 0.35,
            "context_precision": 0.20,
            "context_recall": 0.20
        }
        
        overall_score = (
            faithfulness * weights["faithfulness"] +
            answer_relevance * weights["answer_relevance"] +
            context_precision * weights["context_precision"] +
            context_recall * weights["context_recall"]
        )
        
        # Determine quality level
        if overall_score >= 0.85:
            quality_level = ResponseQuality.EXCELLENT
        elif overall_score >= 0.70:
            quality_level = ResponseQuality.GOOD
        elif overall_score >= 0.55:
            quality_level = ResponseQuality.ACCEPTABLE
        else:
            quality_level = ResponseQuality.POOR
        
        # If we have agent feedback about quality, factor it in
        if agent_feedback:
            # Adjust overall score based on feedback
            feedback_lower = agent_feedback.lower()
            if any(w in feedback_lower for w in ["wrong", "incorrect", "bad", "terrible"]):
                overall_score = max(0.0, overall_score - 0.20)
                if overall_score < 0.55:
                    quality_level = ResponseQuality.POOR
        
        return ResponseQualityMetrics(
            ticket_id="",  # Will be set by caller
            proposed_response=response,
            faithfulness=faithfulness,
            answer_relevance=answer_relevance,
            context_precision=context_precision,
            context_recall=context_recall,
            overall_score=overall_score,
            quality_level=quality_level,
            evaluation_timestamp=datetime.now()
        )


# Global instance
_evaluator = None


def get_quality_evaluator() -> QualityEvaluator:
    """Get or create the global quality evaluator instance"""
    global _evaluator
    if _evaluator is None:
        _evaluator = QualityEvaluator()
    return _evaluator
