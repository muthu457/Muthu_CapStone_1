import json
import os
from datetime import datetime
from typing import List, Optional

class FeedbackStore:
    """Store and retrieve agent feedback for learning (simplified in-memory version)"""
    
    def __init__(self, persist_dir: str = "./feedback_db"):
        self.persist_dir = persist_dir
        os.makedirs(persist_dir, exist_ok=True)
        
        # In-memory storage
        self.accepted_responses = []
        self.edited_responses = []
        self.rejected_responses = []
        
        # File-based persistence
        self.accepted_file = os.path.join(persist_dir, "accepted.json")
        self.edited_file = os.path.join(persist_dir, "edited.json")
        self.rejected_file = os.path.join(persist_dir, "rejected.json")
        
        self._load_from_disk()
    
    def _load_from_disk(self):
        """Load feedback from disk if exists"""
        try:
            if os.path.exists(self.accepted_file):
                with open(self.accepted_file, 'r') as f:
                    self.accepted_responses = json.load(f)
            if os.path.exists(self.edited_file):
                with open(self.edited_file, 'r') as f:
                    self.edited_responses = json.load(f)
            if os.path.exists(self.rejected_file):
                with open(self.rejected_file, 'r') as f:
                    self.rejected_responses = json.load(f)
        except Exception as e:
            print(f"Could not load feedback from disk: {e}")
    
    def _save_to_disk(self):
        """Save feedback to disk"""
        try:
            with open(self.accepted_file, 'w') as f:
                json.dump(self.accepted_responses, f)
            with open(self.edited_file, 'w') as f:
                json.dump(self.edited_responses, f)
            with open(self.rejected_file, 'w') as f:
                json.dump(self.rejected_responses, f)
        except Exception as e:
            print(f"Could not save feedback to disk: {e}")
    
    def store_accepted_feedback(self, ticket_id: str, category: str, 
                               original_ticket: str, response: str, 
                               metadata: dict = None):
        """Store accepted response for learning"""
        feedback = {
            "ticket_id": ticket_id,
            "category": category,
            "ticket": original_ticket,
            "response": response,
            "timestamp": datetime.now().isoformat()
        }
        if metadata:
            feedback.update(metadata)
        
        self.accepted_responses.append(feedback)
        self._save_to_disk()
    
    def store_edited_feedback(self, ticket_id: str, category: str,
                             original_ticket: str, proposed_response: str,
                             edited_response: str, metadata: dict = None):
        """Store edited response to learn from agent improvements"""
        feedback = {
            "ticket_id": ticket_id,
            "category": category,
            "ticket": original_ticket,
            "proposed": proposed_response,
            "improved": edited_response,
            "timestamp": datetime.now().isoformat()
        }
        if metadata:
            feedback.update(metadata)
        
        self.edited_responses.append(feedback)
        self._save_to_disk()
    
    def store_rejected_feedback(self, ticket_id: str, category: str,
                               original_ticket: str, rejected_response: str,
                               metadata: dict = None):
        """Store rejected response to avoid similar mistakes"""
        feedback = {
            "ticket_id": ticket_id,
            "category": category,
            "ticket": original_ticket,
            "response": rejected_response,
            "timestamp": datetime.now().isoformat()
        }
        if metadata:
            feedback.update(metadata)
        
        self.rejected_responses.append(feedback)
        self._save_to_disk()
    
    def get_similar_accepted_responses(self, query: str, category: str = None, k: int = 3):
        """Retrieve similar accepted responses for context"""
        results = [r for r in self.accepted_responses if not category or r.get("category") == category][:k]
        return {
            "documents": [r["response"] for r in results],
            "metadatas": [{"category": r.get("category"), "timestamp": r.get("timestamp")} for r in results]
        }
    
    def get_similar_edited_responses(self, query: str, category: str = None, k: int = 3):
        """Retrieve similar edited responses to learn from improvements"""
        results = [r for r in self.edited_responses if not category or r.get("category") == category][:k]
        return {
            "documents": [f"Original: {r['proposed']}\n\nImproved: {r['improved']}" for r in results],
            "metadatas": [{"category": r.get("category"), "timestamp": r.get("timestamp")} for r in results]
        }
    
    def get_similar_rejected_responses(self, query: str, category: str = None, k: int = 3):
        """Retrieve rejected responses to avoid similar issues"""
        results = [r for r in self.rejected_responses if not category or r.get("category") == category][:k]
        return {
            "documents": [r["response"] for r in results],
            "metadatas": [{"category": r.get("category"), "timestamp": r.get("timestamp")} for r in results]
        }
    
    def get_learning_context(self, query: str, category: str = None, k: int = 2):
        """Get comprehensive learning context: accepted, edited, and rejected responses"""
        context = {
            "accepted": self.get_similar_accepted_responses(query, category, k),
            "edited": self.get_similar_edited_responses(query, category, k),
            "rejected": self.get_similar_rejected_responses(query, category, k)
        }
        return context
    
    def get_feedback_stats(self) -> dict:
        """Get statistics on feedback collected"""
        return {
            "accepted_count": len(self.accepted_responses),
            "edited_count": len(self.edited_responses),
            "rejected_count": len(self.rejected_responses)
        }
