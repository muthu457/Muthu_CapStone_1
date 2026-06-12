"""
Demo script showing the support triage co-pilot in action
"""

from ticket_classifier import TicketClassifier
from response_generator import ResponseGenerator
from feedback_store import FeedbackStore
import json

def demo():
    print("=" * 70)
    print("SUPPORT TRIAGE CO-PILOT DEMO")
    print("=" * 70)
    
    # Initialize components
    classifier = TicketClassifier()
    feedback_store = FeedbackStore()
    generator = ResponseGenerator(feedback_store=feedback_store)
    
    # Sample tickets
    tickets = [
        {
            "customer_id": "CUST_001",
            "subject": "Billing Issue",
            "description": "Why was I charged twice this month for my subscription?"
        },
        {
            "customer_id": "CUST_002",
            "subject": "Account Access",
            "description": "I forgot my password and I can't log into my account"
        },
        {
            "customer_id": "CUST_003",
            "subject": "Plan Upgrade",
            "description": "How do I upgrade from the basic plan to premium?"
        },
        {
            "customer_id": "CUST_004",
            "subject": "Technical Issue",
            "description": "The dashboard is loading very slowly and timing out"
        }
    ]
    
    for i, ticket in enumerate(tickets, 1):
        print(f"\n{'-' * 70}")
        print(f"TICKET {i}: {ticket['subject']}")
        print(f"{'-' * 70}")
        print(f"Customer: {ticket['customer_id']}")
        print(f"Description: {ticket['description']}\n")
        
        # Classify
        print("[1] CLASSIFICATION")
        classification = classifier.classify_ticket(ticket['subject'], ticket['description'])
        print(f"    Category: {classification['category']}")
        print(f"    Confidence: {classification['confidence']:.1%}")
        
        # Generate response
        print("\n[2] RESPONSE GENERATION")
        learning_context = feedback_store.get_learning_context(
            f"{ticket['subject']} {ticket['description']}",
            category=classification['category']
        )
        
        response_data = generator.generate_response(
            ticket['subject'],
            ticket['description'],
            classification['category'],
            learning_context=learning_context
        )
        
        print(f"    Proposed Response:")
        print(f"    {response_data['proposed_response'][:200]}...")
        print(f"    Confidence: {response_data['confidence']:.1%}")
        
        # Simulate feedback
        print("\n[3] AGENT FEEDBACK SCENARIOS")
        
        if i == 1:
            print("    ✅ Agent accepts response")
            feedback_store.store_accepted_feedback(
                ticket_id=f"TICKET_{i}",
                category=classification['category'],
                original_ticket=f"{ticket['subject']}: {ticket['description']}",
                response=response_data['proposed_response']
            )
        elif i == 2:
            print("    ✏️ Agent edits and approves response")
            edited = "Try resetting your password using the 'Forgot Password' link on the login page. If you don't receive the email within 5 minutes, check your spam folder or contact support."
            print(f"    Edited: {edited}")
            feedback_store.store_edited_feedback(
                ticket_id=f"TICKET_{i}",
                category=classification['category'],
                original_ticket=f"{ticket['subject']}: {ticket['description']}",
                proposed_response=response_data['proposed_response'],
                edited_response=edited
            )
        elif i == 3:
            print("    ❌ Agent rejects response")
            feedback_store.store_rejected_feedback(
                ticket_id=f"TICKET_{i}",
                category=classification['category'],
                original_ticket=f"{ticket['subject']}: {ticket['description']}",
                rejected_response=response_data['proposed_response']
            )
    
    # Show learning progress
    print(f"\n\n{'=' * 70}")
    print("LEARNING PROGRESS")
    print(f"{'=' * 70}")
    
    stats = feedback_store.get_feedback_stats()
    print(f"\nAccepted Responses (became templates): {stats['accepted_count']}")
    print(f"Edited Responses (improvement patterns): {stats['edited_count']}")
    print(f"Rejected Responses (patterns to avoid): {stats['rejected_count']}")
    
    print(f"\n💡 The system will now use this feedback to improve responses for similar tickets!")
    print(f"{'=' * 70}\n")

if __name__ == "__main__":
    demo()
