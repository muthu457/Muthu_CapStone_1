"""
Prompt Engineering for Tone-Matched Responses
Handles prompt construction, tone matching, and template selection
"""
from typing import Optional, Dict, List
from models import TicketCategory


class ToneAnalyzer:
    """Analyze customer tone from text"""
    
    FRUSTRATED_KEYWORDS = ["angry", "frustrated", "upset", "terrible", "awful", "horrible", "ridiculous"]
    URGENT_KEYWORDS = ["urgent", "asap", "immediately", "emergency", "critical", "broken"]
    NEUTRAL_KEYWORDS = ["please", "thank you", "appreciate", "help", "need"]
    
    @staticmethod
    def detect_tone(text: str) -> str:
        """Detect customer tone from ticket description"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ToneAnalyzer.FRUSTRATED_KEYWORDS):
            return "frustrated"
        elif any(word in text_lower for word in ToneAnalyzer.URGENT_KEYWORDS):
            return "urgent"
        elif any(word in text_lower for word in ToneAnalyzer.NEUTRAL_KEYWORDS):
            return "polite"
        else:
            return "neutral"


class ResponseTemplate:
    """Response template with tone variation"""
    
    def __init__(self, base_template: str, tone_variants: Dict[str, str]):
        self.base_template = base_template
        self.tone_variants = tone_variants
    
    def render(self, tone: str, **kwargs) -> str:
        """Render template with tone variant"""
        template = self.tone_variants.get(tone, self.base_template)
        return template.format(**kwargs) if kwargs else template


class PromptEngineer:
    """
    Prompt engineering for tone-matched responses
    Manages templates and prompt construction
    """
    
    def __init__(self):
        self.templates = self._initialize_templates()
    
    def _initialize_templates(self) -> Dict[str, ResponseTemplate]:
        """Initialize response templates by category"""
        
        templates = {
            "billing": ResponseTemplate(
                base_template="Thank you for reaching out about your billing inquiry.",
                tone_variants={
                    "frustrated": "We sincerely apologize for the billing issue you're experiencing. We're here to help resolve this quickly.",
                    "urgent": "We understand this needs immediate attention. Let me help you right away.",
                    "polite": "Thank you for your inquiry. We're happy to assist with your billing question.",
                    "neutral": "We can help you with your billing question."
                }
            ),
            "password_reset": ResponseTemplate(
                base_template="I'll help you reset your password securely.",
                tone_variants={
                    "frustrated": "I understand how frustrating account lockouts can be. Let me get you back in quickly.",
                    "urgent": "No problem, I can help you regain access immediately.",
                    "polite": "I'd be happy to help you reset your password safely.",
                    "neutral": "Here's how to reset your password."
                }
            ),
            "plan_change": ResponseTemplate(
                base_template="I can help you modify your plan.",
                tone_variants={
                    "frustrated": "Let's find a plan that works better for you. I'm here to help make this right.",
                    "urgent": "I can make that plan change for you right now.",
                    "polite": "I'd be delighted to help you find the right plan for your needs.",
                    "neutral": "Here are your plan options."
                }
            ),
            "other": ResponseTemplate(
                base_template="Thank you for contacting us.",
                tone_variants={
                    "frustrated": "We understand your concern and are committed to resolving this for you.",
                    "urgent": "We're prioritizing your request and will help you right away.",
                    "polite": "Thank you for reaching out. We're here to help.",
                    "neutral": "We'll assist you with your inquiry."
                }
            )
        }
        
        return templates
    
    def get_system_prompt(self, tone: str, category: str) -> str:
        """Get system prompt for LLM with tone instructions"""
        
        tone_instructions = {
            "frustrated": "Be empathetic and apologetic. Acknowledge their frustration. Show urgency in resolution. Offer concrete solutions quickly.",
            "urgent": "Be concise and action-oriented. Prioritize speed. Provide immediate next steps. Show you understand the urgency.",
            "polite": "Be warm and appreciative. Thank them for their patience. Provide thorough, detailed assistance.",
            "neutral": "Be professional and helpful. Provide clear, accurate information. Offer next steps for resolution."
        }
        
        category_context = {
            "billing": "This is a billing-related inquiry. Provide accurate financial information and clear explanations of charges.",
            "password_reset": "This is a security-related issue. Prioritize account security and provide clear, simple steps.",
            "plan_change": "This is a plan modification request. Help the customer choose the right plan for their needs.",
            "other": "This is a general support inquiry. Provide helpful, accurate information."
        }
        
        system_prompt = f"""You are a helpful support agent. {tone_instructions.get(tone, 'Be professional and helpful.')} 
{category_context.get(category, '')}
Keep responses concise (2-3 sentences). Be specific and actionable."""
        
        return system_prompt
    
    def get_response_template(self, category: str, tone: str) -> str:
        """Get the tone-matched opening for a response"""
        category_str = category if isinstance(category, str) else category.value
        template = self.templates.get(category_str)
        
        if template:
            return template.render(tone)
        return "Thank you for contacting us. We're here to help."
    
    def construct_prompt(self, 
                        ticket_subject: str,
                        ticket_description: str,
                        category: str,
                        tone: str,
                        rag_context: Optional[List[str]] = None) -> str:
        """
        Construct a full prompt for response generation
        Includes tone, category context, and RAG context
        """
        
        prompt_parts = []
        
        # Add customer question
        prompt_parts.append(f"Customer Question: {ticket_subject}\n{ticket_description}")
        
        # Add RAG context if available
        if rag_context:
            prompt_parts.append(f"\nRelevant Knowledge Base Articles:\n" + "\n".join(rag_context))
        
        # Add instruction
        prompt_parts.append(f"\nTone: {tone}")
        prompt_parts.append(f"Category: {category}")
        prompt_parts.append("\nProvide a helpful, concise response.")
        
        return "\n".join(prompt_parts)
    
    def get_confidence_boost(self, tone: str, rag_context_count: int) -> float:
        """
        Calculate confidence boost based on:
        - Certainty that response matches tone
        - Amount of RAG context available
        """
        
        # RAG context adds 0.1 per article (up to 0.3)
        rag_boost = min(0.3, rag_context_count * 0.1)
        
        # Tone certainty: harder to match frustrated/urgent tones correctly
        tone_certainty = {
            "frustrated": 0.05,  # Harder to get tone right
            "urgent": 0.05,
            "polite": 0.10,
            "neutral": 0.15  # Easier with neutral tone
        }.get(tone, 0.10)
        
        return rag_boost + tone_certainty


# Global instance
_engineer = None


def get_prompt_engineer() -> PromptEngineer:
    """Get or create the global prompt engineer instance"""
    global _engineer
    if _engineer is None:
        _engineer = PromptEngineer()
    return _engineer
