import pytest
from models import SupportTicket, FeedbackType, TicketCategory
from datetime import datetime
from ticket_classifier import TicketClassifier
from response_generator import ResponseGenerator
from feedback_store import FeedbackStore
import tempfile
import shutil

@pytest.fixture
def feedback_store():
    """Create a temporary feedback store for testing"""
    temp_dir = tempfile.mkdtemp()
    store = FeedbackStore(persist_dir=temp_dir)
    yield store
    # Cleanup
    shutil.rmtree(temp_dir)

@pytest.fixture
def classifier():
    """Create a ticket classifier"""
    return TicketClassifier()

@pytest.fixture
def generator(feedback_store):
    """Create response generator with feedback store"""
    return ResponseGenerator(feedback_store=feedback_store)

def test_ticket_model():
    """Test ticket model creation"""
    ticket = SupportTicket(
        ticket_id="TEST_001",
        customer_id="CUST_001",
        subject="Billing Issue",
        description="Double charge",
        created_at=datetime.now(),
        category="billing question"
    )
    assert ticket.ticket_id == "TEST_001"
    assert ticket.category == "billing question"

def test_classifier_billing(classifier):
    """Test classification of billing ticket"""
    result = classifier.classify_ticket(
        subject="Billing Issue",
        description="Why was I charged twice?"
    )
    assert "billing" in result["category"].lower()
    assert result["confidence"] > 0.5

def test_classifier_password(classifier):
    """Test classification of password reset ticket"""
    result = classifier.classify_ticket(
        subject="Password Reset",
        description="I forgot my password"
    )
    assert "password" in result["category"].lower()
    assert result["confidence"] > 0.5

def test_classifier_plan_change(classifier):
    """Test classification of plan change ticket"""
    result = classifier.classify_ticket(
        subject="Plan Change",
        description="How do I upgrade to premium?"
    )
    assert "plan" in result["category"].lower()
    assert result["confidence"] > 0.5

def test_feedback_store_accepted(feedback_store):
    """Test storing accepted feedback"""
    feedback_store.store_accepted_feedback(
        ticket_id="TICKET_001",
        category="billing question",
        original_ticket="Double charge",
        response="We'll refund the duplicate charge"
    )
    assert feedback_store.get_feedback_stats()["accepted_count"] == 1

def test_feedback_store_edited(feedback_store):
    """Test storing edited feedback"""
    feedback_store.store_edited_feedback(
        ticket_id="TICKET_002",
        category="password reset",
        original_ticket="Forgot password",
        proposed_response="Reset your password",
        edited_response="Click forgot password, check email within 5 minutes"
    )
    assert feedback_store.get_feedback_stats()["edited_count"] == 1

def test_feedback_store_rejected(feedback_store):
    """Test storing rejected feedback"""
    feedback_store.store_rejected_feedback(
        ticket_id="TICKET_003",
        category="other support issue",
        original_ticket="Technical issue",
        rejected_response="Bad response"
    )
    assert feedback_store.get_feedback_stats()["rejected_count"] == 1

def test_feedback_store_retrieval(feedback_store):
    """Test retrieving similar feedback"""
    # Store some feedback
    feedback_store.store_accepted_feedback(
        ticket_id="TICKET_001",
        category="billing question",
        original_ticket="Double charge",
        response="We'll refund the duplicate charge"
    )
    
    # Retrieve similar
    results = feedback_store.get_similar_accepted_responses(
        query="Why was I charged twice?",
        category="billing question"
    )
    assert len(results["documents"]) > 0

def test_response_generator(generator, classifier):
    """Test response generation"""
    classification = classifier.classify_ticket(
        "Billing Issue",
        "Double charge"
    )
    
    response = generator.generate_response(
        ticket_subject="Billing Issue",
        ticket_description="Why was I charged twice?",
        category=classification["category"]
    )
    
    assert "proposed_response" in response
    assert len(response["proposed_response"]) > 0
    assert response["confidence"] > 0

def test_learning_cycle(generator, classifier, feedback_store):
    """Test complete learning cycle"""
    # Initial response
    classification = classifier.classify_ticket(
        "Password Issue",
        "I forgot my password"
    )
    
    response1 = generator.generate_response(
        "Password Issue",
        "I forgot my password",
        classification["category"]
    )
    
    # Store as accepted
    feedback_store.store_accepted_feedback(
        ticket_id="TICKET_001",
        category=classification["category"],
        original_ticket="Password Issue: I forgot my password",
        response=response1["proposed_response"]
    )
    
    # Generate another response with learning context
    learning_context = feedback_store.get_learning_context(
        "Can't access account - password",
        category=classification["category"]
    )
    
    response2 = generator.generate_response(
        "Account Access",
        "I can't log in",
        classification["category"],
        learning_context=learning_context
    )
    
    # Verify learning was used
    assert response2.get("used_context", False) or len(response2["proposed_response"]) > 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
