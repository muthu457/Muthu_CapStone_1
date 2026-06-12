import streamlit as st
import requests
import json
from datetime import datetime

# Page configuration
st.set_page_config(page_title="Support Triage Co-pilot", layout="wide")

# API endpoint
API_BASE_URL = "http://localhost:8000"

st.title("🎯 Support Triage Co-pilot")
st.markdown("*Agent interface for ticket triage and response proposal feedback*")

# Sidebar for navigation
page = st.sidebar.radio("Navigation", ["Process Tickets", "View Tickets", "View Stats", "Feedback History"])

if page == "Process Tickets":
    st.header("Process Support Tickets")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("New Ticket")
        customer_id = st.text_input("Customer ID", value="CUST_001")
        subject = st.text_input("Subject", placeholder="e.g., Billing question")
        description = st.text_area("Description", height=100, 
                                   placeholder="Describe the customer's issue...")
        
        if st.button("📬 Submit Ticket for Triage", use_container_width=True):
            with st.spinner("Classifying and generating response..."):
                try:
                    response = requests.post(
                        f"{API_BASE_URL}/tickets/ingest",
                        json={
                            "customer_id": customer_id,
                            "subject": subject,
                            "description": description
                        },
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        st.session_state.current_ticket = result
                        st.success("✅ Ticket processed!")
                    else:
                        st.error(f"Error: {response.text}")
                except requests.exceptions.ConnectionError:
                    st.error("❌ Cannot connect to API. Make sure the server is running on http://localhost:8000")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    with col2:
        if "current_ticket" in st.session_state:
            result = st.session_state.current_ticket
            
            st.subheader("Triage Result")
            st.metric("Category", result["category"])
            st.metric("Confidence", f"{result['category_confidence']:.1%}")
            
            st.markdown("---")
            st.subheader("Proposed Response")
            st.text_area(
                "Generated Response:",
                value=result["proposed_response"],
                height=150,
                disabled=True
            )
            
            st.metric("Response Confidence", f"{result['response_confidence']:.1%}")
            
            if result["used_feedback_context"]:
                st.info("💡 This response was informed by similar resolved tickets")
    
    # Feedback section
    if "current_ticket" in st.session_state:
        st.markdown("---")
        st.subheader("Agent Feedback")
        
        result = st.session_state.current_ticket
        ticket_id = result["ticket_id"]
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("✅ Accept Response", use_container_width=True):
                try:
                    response = requests.post(
                        f"{API_BASE_URL}/feedback",
                        json={
                            "ticket_id": ticket_id,
                            "feedback_type": "accepted"
                        }
                    )
                    if response.status_code == 200:
                        st.success("✅ Feedback recorded - response accepted!")
                        st.session_state.pop("current_ticket", None)
                    else:
                        st.error("Failed to record feedback")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        
        with col2:
            if st.button("✏️ Edit & Approve", use_container_width=True):
                st.session_state.show_edit = True
        
        with col3:
            if st.button("❌ Reject Response", use_container_width=True):
                try:
                    response = requests.post(
                        f"{API_BASE_URL}/feedback",
                        json={
                            "ticket_id": ticket_id,
                            "feedback_type": "rejected"
                        }
                    )
                    if response.status_code == 200:
                        st.warning("⚠️ Response rejected - system will learn from this")
                        st.session_state.pop("current_ticket", None)
                    else:
                        st.error("Failed to record feedback")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        
        # Edit form
        if st.session_state.get("show_edit", False):
            st.subheader("Edit Response")
            edited_response = st.text_area(
                "Improved Response:",
                value=result["proposed_response"],
                height=150
            )
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 Save & Approve", use_container_width=True):
                    try:
                        response = requests.post(
                            f"{API_BASE_URL}/feedback",
                            json={
                                "ticket_id": ticket_id,
                                "feedback_type": "edited",
                                "final_response": edited_response
                            }
                        )
                        if response.status_code == 200:
                            st.success("✅ Edited response saved - system learning improved responses!")
                            st.session_state.pop("current_ticket", None)
                            st.session_state.pop("show_edit", None)
                            st.rerun()
                        else:
                            st.error("Failed to save feedback")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
            
            with col2:
                if st.button("Cancel", use_container_width=True):
                    st.session_state.pop("show_edit", None)
                    st.rerun()

elif page == "View Tickets":
    st.header("📋 All Support Tickets")
    
    try:
        response = requests.get(f"{API_BASE_URL}/stats")
        if response.status_code == 200:
            stats = response.json()
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Tickets", stats["total_tickets_processed"])
            with col2:
                st.metric("Feedback Provided", stats["total_feedback_collected"])
            with col3:
                acceptance_rate = 0
                total_feedback = (
                    stats["accepted_responses"] + 
                    stats["edited_responses"] + 
                    stats["rejected_responses"]
                )
                if total_feedback > 0:
                    acceptance_rate = (
                        stats["accepted_responses"] + stats["edited_responses"]
                    ) / total_feedback * 100
                st.metric("Acceptance Rate", f"{acceptance_rate:.1f}%")
            
            st.markdown("---")
            
            if stats["total_tickets_processed"] > 0:
                # Fetch all tickets
                tickets_response = requests.get(f"{API_BASE_URL}/tickets/all")
                if tickets_response.status_code == 200:
                    tickets = tickets_response.json()
                    
                    st.subheader(f"📊 Tickets ({len(tickets)})")
                    
                    for idx, ticket in enumerate(tickets):
                        # Create expander for each ticket
                        with st.expander(
                            f"🎫 {ticket['subject']} | {ticket['category']} | {ticket['customer_id']}",
                            expanded=False
                        ):
                            col1, col2 = st.columns([1, 1])
                            
                            with col1:
                                st.markdown("**Ticket Details**")
                                st.markdown(f"- **ID**: `{ticket['ticket_id']}`")
                                st.markdown(f"- **Customer**: {ticket['customer_id']}")
                                st.markdown(f"- **Category**: {ticket['category']}")
                                st.markdown(f"- **Created**: {ticket['created_at']}")
                            
                            with col2:
                                st.markdown("**Response Quality**")
                                st.markdown(f"- **Confidence**: {ticket['response_confidence']:.0%}")
                                if ticket['feedback']:
                                    feedback_type = ticket['feedback'].get('feedback_type', 'N/A')
                                    status_emoji = {
                                        'accepted': '✅',
                                        'edited': '✏️',
                                        'rejected': '❌'
                                    }.get(feedback_type, '❓')
                                    st.markdown(f"- **Feedback**: {status_emoji} {feedback_type.upper()}")
                                else:
                                    st.markdown(f"- **Feedback**: ⏳ Pending")
                            
                            st.markdown("---")
                            st.markdown("**Issue Description**")
                            st.write(ticket['description'])
                            
                            st.markdown("**Proposed Response**")
                            st.info(ticket['proposed_response'])
                            
                            if ticket['feedback']:
                                st.markdown("**Agent Feedback**")
                                col1, col2 = st.columns([1, 2])
                                with col1:
                                    st.markdown(f"**Type**: {ticket['feedback'].get('feedback_type', 'N/A').upper()}")
                                if ticket['feedback'].get('final_response'):
                                    with col2:
                                        st.markdown("**Agent's Response**")
                                        st.success(ticket['feedback']['final_response'])
                else:
                    st.error("Failed to fetch ticket details")
            else:
                st.info("📭 No tickets processed yet. Go to 'Process Tickets' to get started!")
    except Exception as e:
        st.error(f"Error: {str(e)}")

elif page == "View Stats":
    st.header("System Statistics")
    
    try:
        response = requests.get(f"{API_BASE_URL}/stats")
        if response.status_code == 200:
            stats = response.json()
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Tickets Processed", stats["total_tickets_processed"])
            
            with col2:
                st.metric("Feedback Collected", stats["total_feedback_collected"])
            
            with col3:
                st.metric("Accepted", stats["accepted_responses"])
            
            with col4:
                st.metric("Edited", stats["edited_responses"])
            
            st.metric("Rejected", stats["rejected_responses"])
            
            # Calculate acceptance rate
            total_feedback = (
                stats["accepted_responses"] + 
                stats["edited_responses"] + 
                stats["rejected_responses"]
            )
            
            if total_feedback > 0:
                acceptance_rate = (
                    stats["accepted_responses"] + stats["edited_responses"]
                ) / total_feedback * 100
                st.success(f"Response Acceptance Rate: {acceptance_rate:.1f}%")
        else:
            st.error("Failed to fetch statistics")
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to API. Make sure the server is running.")
    except Exception as e:
        st.error(f"Error: {str(e)}")

elif page == "Feedback History":
    st.header("Feedback Learning History")
    
    st.info("💡 The system learns from all agent feedback:")
    st.markdown("""
    - **Accepted responses**: Stored as templates for similar tickets
    - **Edited responses**: Used to improve future suggestions  
    - **Rejected responses**: Avoided in similar future scenarios
    """)
    
    try:
        response = requests.get(f"{API_BASE_URL}/stats")
        if response.status_code == 200:
            stats = response.json()
            
            st.subheader("Learning Database Status")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "Quality Templates", 
                    stats["accepted_responses"],
                    delta="Used to improve responses"
                )
            
            with col2:
                st.metric(
                    "Improvement Examples",
                    stats["edited_responses"],
                    delta="Shows how to enhance responses"
                )
            
            with col3:
                st.metric(
                    "Patterns to Avoid",
                    stats["rejected_responses"],
                    delta="Prevents poor suggestions"
                )
            
            st.success("✅ System continuously improves with more feedback!")
    except Exception as e:
        st.error(f"Error: {str(e)}")

st.markdown("---")
st.caption("Support Triage Co-pilot • Powered by LLM + ChromaDB Learning")
