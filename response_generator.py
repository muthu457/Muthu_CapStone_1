"""
Enhanced Response Generator with RAG, Prompt Engineering, and Quality Metrics
"""
from typing import Dict, List, Optional
from datetime import datetime
import os

from models import ProposedResponse, ConfidenceLevel, ClassificationResult
from knowledge_base import get_knowledge_base
from prompt_manager import get_prompt_engineer, ToneAnalyzer
from quality_metrics import get_quality_evaluator
from confidence_router import get_confidence_router


class ResponseGenerator:
    """
    Generate support responses with:
    - Prompt engineering for tone-matching
    - RAG over knowledge base
    - Quality evaluation
    - Confidence scoring
    """
    
    def __init__(self, feedback_store=None):
        self.feedback_store = feedback_store
        self.kb = get_knowledge_base()
        self.prompt_engineer = get_prompt_engineer()
        self.quality_evaluator = get_quality_evaluator()
        self.confidence_router = get_confidence_router()
        
        os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
        
        # Response templates (fallback if no LLM available)
        self.templates = {
            "billing question": """You are a helpful billing support agent. Answer this billing question clearly and helpfully.

Question: {question}

Provide a concise response addressing the customer's billing concern.""",
            
            "password reset request": """You are a support agent helping with account access. Provide clear password reset instructions.

Request: {question}

Provide step-by-step instructions or next steps.""",
            
            "plan change request": """You are a sales support agent helping with plan changes. Explain the plan change process helpfully.

Request: {question}

Provide information about available plans and the change process.""",
            
            "other support issue": """You are a general support agent. Help address this customer issue.

Issue: {question}

Provide a helpful response."""
        }
        
        self.llm = None
    
    def generate_response(self,
                         ticket_id: str,
                         ticket_subject: str,
                         ticket_description: str,
                         category: str,
                         classification: Optional[ClassificationResult] = None,
                         learning_context: Dict = None) -> ProposedResponse:
        """
        Generate enhanced response with RAG and prompt engineering
        
        Args:
            ticket_id: Unique ticket identifier
            ticket_subject: Subject of the ticket
            ticket_description: Description/body of the ticket
            category: Classified category
            classification: Classification result with confidence
            learning_context: Context from accepted/edited responses
            
        Returns:
            ProposedResponse with confidence levels and quality metrics
        """
        
        # Detect tone
        tone = ToneAnalyzer.detect_tone(ticket_description)
        
        # Retrieve relevant knowledge base articles
        rag_results = self.kb.retrieve(
            f"{ticket_subject} {ticket_description}",
            top_k=3,
            category_filter=category
        )
        
        rag_context = [f"- {r.source_title}: {r.source_content}" for r in rag_results]
        
        # Get tone-matched template opening
        template_text = self.prompt_engineer.get_response_template(category, tone)
        
        # Construct full prompt with RAG context
        full_prompt = self.prompt_engineer.construct_prompt(
            ticket_subject,
            ticket_description,
            category,
            tone,
            rag_context
        )
        
        # Generate response (using template for now)
        if rag_results:
            # Include RAG context in response
            response_text = f"{template_text}\n\nBased on our knowledge base:\n" + "\n".join(rag_context[:2])
        else:
            response_text = self._generate_with_template(ticket_subject, ticket_description, category)
        
        # Calculate base confidence
        base_confidence = classification.confidence if classification else 0.7
        
        # Apply confidence boost from RAG and prompt engineering
        prompt_boost = self.prompt_engineer.get_confidence_boost(tone, len(rag_results))
        final_confidence = min(1.0, base_confidence + prompt_boost)
        
        # Determine confidence level
        if final_confidence > 0.8:
            confidence_level = ConfidenceLevel.HIGH
        elif final_confidence >= 0.6:
            confidence_level = ConfidenceLevel.MEDIUM
        else:
            confidence_level = ConfidenceLevel.LOW
        
        # Evaluate response quality
        quality_metrics = self.quality_evaluator.evaluate_response(
            response=response_text,
            ticket_description=ticket_description,
            ticket_category=category,
            rag_sources=rag_results
        )
        
        # Create response object
        proposed_response = ProposedResponse(
            ticket_id=ticket_id,
            proposed_response=response_text,
            confidence=final_confidence,
            confidence_level=confidence_level,
            generated_at=datetime.now(),
            tone=tone,
            template_used=f"{category}_template",
            retrieved_sources=rag_results,
            ragas_score=quality_metrics.overall_score,
            quality_level=quality_metrics.quality_level,
            knowledge_base_version=self.kb.version,
            response_model_version="2.0"  # Enhanced version
        )
        
        return proposed_response
    
    def _generate_with_template(self, subject: str, description: str, category: str) -> str:
        """Generate response using template (fallback)"""
        
        template_key = "other support issue"
        
        if "billing" in category.lower():
            template_key = "billing question"
        elif "password" in category.lower():
            template_key = "password reset request"
        elif "plan" in category.lower():
            template_key = "plan change request"
        
        template = self.templates.get(template_key, self.templates["other support issue"])
        return template.format(question=f"{subject}\n{description}")

