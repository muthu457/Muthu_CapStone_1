"""
RAG (Retrieval Augmented Generation) Knowledge Base System
Manages support articles, retrieval, and version tracking
"""
import json
import os
from datetime import datetime
from typing import List, Dict, Optional
from models import RAGRetrievalResult


class KnowledgeBase:
    """RAG knowledge base with retrieval capabilities"""
    
    def __init__(self, storage_path: str = "./data/knowledge_base.json"):
        self.storage_path = storage_path
        self.articles = {}
        self.version = "1.0"
        self.last_updated = datetime.now()
        self.load_from_disk()
    
    def add_article(self, article_id: str, title: str, content: str, 
                    category: str, tags: List[str] = None) -> Dict:
        """Add a knowledge base article"""
        self.articles[article_id] = {
            "id": article_id,
            "title": title,
            "content": content,
            "category": category,
            "tags": tags or [],
            "created_at": datetime.now().isoformat(),
            "last_modified": datetime.now().isoformat(),
            "access_count": 0
        }
        self.last_updated = datetime.now()
        self.save_to_disk()
        return self.articles[article_id]
    
    def retrieve(self, query: str, top_k: int = 3, 
                 category_filter: Optional[str] = None) -> List[RAGRetrievalResult]:
        """
        Retrieve relevant articles based on query
        Uses simple keyword matching + tag matching
        """
        results = []
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        for article_id, article in self.articles.items():
            # Apply category filter if provided
            if category_filter and article.get("category") != category_filter:
                continue
            
            # Calculate relevance score
            score = 0.0
            title_lower = article["title"].lower()
            content_lower = article["content"].lower()
            
            # Title matches are worth more
            for word in query_words:
                if word in title_lower:
                    score += 0.3
                if word in content_lower:
                    score += 0.1
            
            # Tag matches
            for tag in article.get("tags", []):
                if tag.lower() in query_lower:
                    score += 0.2
            
            # Normalize by content length
            score = min(1.0, score)
            
            if score > 0.0:
                results.append({
                    "article_id": article_id,
                    "title": article["title"],
                    "content": article["content"][:500],  # Truncate for efficiency
                    "score": score,
                    "category": article["category"],
                    "tags": article.get("tags", [])
                })
        
        # Sort by score and return top_k
        results.sort(key=lambda x: x["score"], reverse=True)
        
        # Track access
        for result in results[:top_k]:
            if result["article_id"] in self.articles:
                self.articles[result["article_id"]]["access_count"] += 1
        
        # Convert to RAGRetrievalResult format
        rag_results = [
            RAGRetrievalResult(
                source_id=r["article_id"],
                source_title=r["title"],
                source_content=r["content"],
                relevance_score=r["score"]
            )
            for r in results[:top_k]
        ]
        
        return rag_results
    
    def get_article(self, article_id: str) -> Optional[Dict]:
        """Get a specific article"""
        if article_id in self.articles:
            self.articles[article_id]["access_count"] += 1
            return self.articles[article_id]
        return None
    
    def update_article(self, article_id: str, **updates) -> Optional[Dict]:
        """Update article fields"""
        if article_id not in self.articles:
            return None
        
        for key, value in updates.items():
            if key not in ["id", "created_at"]:  # Can't change ID or creation time
                self.articles[article_id][key] = value
        
        self.articles[article_id]["last_modified"] = datetime.now().isoformat()
        self.last_updated = datetime.now()
        self.save_to_disk()
        return self.articles[article_id]
    
    def delete_article(self, article_id: str) -> bool:
        """Delete an article"""
        if article_id in self.articles:
            del self.articles[article_id]
            self.last_updated = datetime.now()
            self.save_to_disk()
            return True
        return False
    
    def get_stats(self) -> Dict:
        """Get knowledge base statistics"""
        total_articles = len(self.articles)
        total_accesses = sum(a.get("access_count", 0) for a in self.articles.values())
        
        categories = {}
        for article in self.articles.values():
            cat = article.get("category", "uncategorized")
            categories[cat] = categories.get(cat, 0) + 1
        
        return {
            "total_articles": total_articles,
            "total_accesses": total_accesses,
            "categories": categories,
            "version": self.version,
            "last_updated": self.last_updated.isoformat()
        }
    
    def save_to_disk(self):
        """Persist knowledge base to disk"""
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        data = {
            "version": self.version,
            "last_updated": self.last_updated.isoformat(),
            "articles": self.articles
        }
        with open(self.storage_path, "w") as f:
            json.dump(data, f, indent=2)
    
    def load_from_disk(self):
        """Load knowledge base from disk"""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r") as f:
                    data = json.load(f)
                    self.articles = data.get("articles", {})
                    self.version = data.get("version", "1.0")
                    self.last_updated = datetime.fromisoformat(data.get("last_updated", datetime.now().isoformat()))
            except Exception as e:
                print(f"Error loading knowledge base: {e}")
    
    def bootstrap_sample_articles(self):
        """Initialize with sample articles for demo"""
        samples = [
            {
                "article_id": "billing_001",
                "title": "How to Update Your Billing Information",
                "content": "You can update your billing information anytime from your account settings. Go to Settings > Billing > Update Payment Method. We accept all major credit cards.",
                "category": "billing",
                "tags": ["billing", "payment", "credit card"]
            },
            {
                "article_id": "billing_002",
                "title": "Invoice and Payment History",
                "content": "Your invoice history is available in the Billing section. You can download invoices as PDF and see all past payments. Invoices are sent automatically at the start of each billing cycle.",
                "category": "billing",
                "tags": ["billing", "invoice", "payment history"]
            },
            {
                "article_id": "password_001",
                "title": "Reset Your Password",
                "content": "If you forgot your password, click 'Forgot Password' on the login page. We'll send you a secure link via email. Click the link and create a new password within 24 hours.",
                "category": "password_reset",
                "tags": ["password", "security", "login"]
            },
            {
                "article_id": "password_002",
                "title": "Change Your Password Securely",
                "content": "To change your password while logged in, go to Settings > Security > Change Password. Ensure your new password is at least 12 characters long.",
                "category": "password_reset",
                "tags": ["password", "security", "account"]
            },
            {
                "article_id": "plan_001",
                "title": "Upgrading Your Plan",
                "content": "You can upgrade your plan anytime from Settings > Plan. Choose the plan that fits your needs. Upgrades take effect immediately and are prorated.",
                "category": "plan_change",
                "tags": ["plan", "upgrade", "billing"]
            },
            {
                "article_id": "plan_002",
                "title": "Downgrading Your Plan",
                "content": "To downgrade, go to Settings > Plan > Downgrade. Your downgrade takes effect on your next billing cycle. You won't lose any data.",
                "category": "plan_change",
                "tags": ["plan", "downgrade", "billing"]
            }
        ]
        
        for article in samples:
            self.add_article(**article)


# Global instance
_kb = None


def get_knowledge_base() -> KnowledgeBase:
    """Get or create the global knowledge base instance"""
    global _kb
    if _kb is None:
        _kb = KnowledgeBase()
        # Bootstrap if empty
        if len(_kb.articles) == 0:
            _kb.bootstrap_sample_articles()
    return _kb
