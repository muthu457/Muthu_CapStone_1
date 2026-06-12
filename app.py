import streamlit as st
import requests
import json
from datetime import datetime

# Page configuration
try:
    st.set_page_config(page_title="Support Triage Co-pilot", layout="wide", initial_sidebar_state="expanded")
except:
    pass

# Custom CSS styling
st.markdown("""
<style>
    /* Main background and text */
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Title styling */
    h1 {
        background: linear-gradient(90deg, #667eea, #764ba2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 800;
        font-size: 3em;
        margin-bottom: 0.5em;
    }
    
    /* Header styling */
    h2 {
        color: #667eea;
        border-bottom: 3px solid #764ba2;
        padding-bottom: 0.5em;
        font-weight: 700;
    }
    
    h3 {
        color: #764ba2;
        font-weight: 600;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(90deg, #667eea, #764ba2);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75em 1.5em;
        font-weight: 600;
        font-size: 1em;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
    }
    
    /* Metric styling */
    .metric-container {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1));
        border-left: 4px solid #667eea;
        border-radius: 8px;
        padding: 1em;
    }
    
    /* Alert colors */
    .stSuccess {
        background: linear-gradient(90deg, rgba(34, 197, 94, 0.1), rgba(34, 197, 94, 0.05));
        border-left: 4px solid #22c55e;
    }
    
    .stError {
        background: linear-gradient(90deg, rgba(239, 68, 68, 0.1), rgba(239, 68, 68, 0.05));
        border-left: 4px solid #ef4444;
    }
    
    .stWarning {
        background: linear-gradient(90deg, rgba(245, 158, 11, 0.1), rgba(245, 158, 11, 0.05));
        border-left: 4px solid #f59e0b;
    }
    
    .stInfo {
        background: linear-gradient(90deg, rgba(59, 130, 246, 0.1), rgba(59, 130, 246, 0.05));
        border-left: 4px solid #3b82f6;
    }
    
    /* Text area styling */
    .stTextArea textarea {
        background: #f8f9fa;
        border: 2px solid #e0e7ff;
        border-radius: 8px;
        color: #333;
    }
    
    .stTextInput input {
        background: #f8f9fa;
        border: 2px solid #e0e7ff;
        border-radius: 8px;
        color: #333;
    }
    
    /* Sidebar styling */
    .stSidebar {
        background: linear-gradient(180deg, #667eea, #764ba2);
    }
    
    .stSidebar > div > div > div > div {
        color: white;
    }
    
    /* Card styling */
    .card {
        background: white;
        border-radius: 12px;
        padding: 1.5em;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        border: 1px solid #e0e7ff;
        margin-bottom: 1em;
    }
</style>
""", unsafe_allow_html=True)

# API endpoint
API_BASE_URL = "http://localhost:8000"

st.markdown("""
<div style="text-align: center; margin-bottom: 2em;">
    <h1>🎯 Support Triage Co-pilot</h1>
    <p style="font-size: 1.1em; color: #667eea; font-weight: 500;">Intelligent ticket triage with AI-powered response generation</p>
</div>
""", unsafe_allow_html=True)

# Sidebar for navigation
page = st.sidebar.radio("📍 Navigation", ["🎫 Process Tickets", "📋 View Tickets", "📊 View Stats", "📈 Drift Dashboard", "🔄 Feedback History", "🔗 Causal Loop"])



try:
    if page == "🎫 Process Tickets":
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 2em; border-radius: 12px; color: white; margin-bottom: 2em;">
            <h2 style="color: white; border: none; margin-top: 0;">🎯 Process Support Tickets</h2>
            <p>Submit customer issues for intelligent triage and AI-powered response generation</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("""
            <div style="background: white; border-radius: 12px; padding: 1.5em; box-shadow: 0 4px 12px rgba(0,0,0,0.1); border-left: 4px solid #667eea;">
                <h3 style="color: #667eea; margin-top: 0;">📝 New Ticket</h3>
            </div>
            """, unsafe_allow_html=True)
            customer_id = st.text_input("Customer ID", value="CUST_001")
            subject = st.text_input("Subject", placeholder="e.g., Billing question")
            description = st.text_area("Description", height=100, 
                                       placeholder="Describe the customer's issue...")
            
            if st.button("🚀 Submit Ticket for Triage", use_container_width=True):
                with st.spinner("🤖 Classifying and generating response..."):
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
                        
                        if response.status_code in [200, 201]:
                            result = response.json()
                            st.session_state.current_ticket = result
                            st.success("Ticket processed!")
                        else:
                            st.error(f"Error: {response.text}")
                    except requests.exceptions.ConnectionError:
                        st.error("Cannot connect to API. Make sure the server is running on http://localhost:8000")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
        
        with col2:
            if "current_ticket" in st.session_state and st.session_state.current_ticket is not None:
                result = st.session_state.current_ticket
                
                st.subheader("Triage Result")
                st.metric("Category", result.get("category", "N/A"))
                st.metric("Confidence", f"{result.get('category_confidence', 0):.1%}")
                
                st.markdown("---")
                st.subheader("Proposed Response")
                st.text_area(
                    "Generated Response:",
                    value=result.get("proposed_response", ""),
                    height=150,
                    disabled=True
                )
                
                st.metric("Response Confidence", f"{result.get('response_confidence', 0):.1%}")
                
                if result.get("used_feedback_context"):
                    st.info("This response was informed by similar resolved tickets")
        
        # Feedback section
        if "current_ticket" in st.session_state and st.session_state.current_ticket is not None:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 1em; border-radius: 12px; color: white; margin: 2em 0 1em 0;">
                <h3 style="color: white; margin: 0;">💬 Agent Feedback</h3>
            </div>
            """, unsafe_allow_html=True)
            
            feedback_col1, feedback_col2, feedback_col3 = st.columns(3)
            
            with feedback_col1:
                if st.button("✅ Accept Response", use_container_width=True, key="accept"):
                    if st.session_state.current_ticket and "ticket_id" in st.session_state.current_ticket:
                        try:
                            requests.post(
                                f"{API_BASE_URL}/feedback",
                                json={
                                    "ticket_id": st.session_state.current_ticket["ticket_id"],
                                    "feedback_type": "accepted",
                                    "final_response": None
                                },
                                timeout=10
                            )
                            st.success("✨ Feedback recorded!")
                            st.session_state.current_ticket = None
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error recording feedback: {str(e)}")
                    else:
                        st.error("⚠️ Ticket data missing")
            
            with feedback_col2:
                if st.button("✏️ Edit & Accept", use_container_width=True, key="edit"):
                    st.session_state.show_edit_box = True
            
            with feedback_col3:
                if st.button("❌ Reject Response", use_container_width=True, key="reject"):
                    if st.session_state.current_ticket and "ticket_id" in st.session_state.current_ticket:
                        try:
                            requests.post(
                                f"{API_BASE_URL}/feedback",
                                json={
                                    "ticket_id": st.session_state.current_ticket["ticket_id"],
                                    "feedback_type": "rejected",
                                    "final_response": None
                                },
                                timeout=10
                            )
                            st.success("Feedback recorded!")
                            st.session_state.current_ticket = None
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error recording feedback: {str(e)}")
                    else:
                        st.error("Ticket data missing")
            
            if st.session_state.get("show_edit_box", False):
                if st.session_state.current_ticket and "proposed_response" in st.session_state.current_ticket:
                    edited_response = st.text_area("Edit Response:", 
                                                   value=st.session_state.current_ticket["proposed_response"],
                                                   height=150)
                    if st.button("Save Edited Response", use_container_width=True):
                        if st.session_state.current_ticket and "ticket_id" in st.session_state.current_ticket:
                            try:
                                requests.post(
                                    f"{API_BASE_URL}/feedback",
                                    json={
                                        "ticket_id": st.session_state.current_ticket["ticket_id"],
                                        "feedback_type": "edited",
                                        "final_response": edited_response
                                    },
                                    timeout=10
                                )
                                st.success("Edited response saved!")
                                st.session_state.current_ticket = None
                                st.session_state.show_edit_box = False
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error saving feedback: {str(e)}")
                        else:
                            st.error("Ticket data missing")
                else:
                    st.error("Response data missing")

    elif page == "📋 View Tickets":
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 2em; border-radius: 12px; color: white; margin-bottom: 2em;">
            <h2 style="color: white; border: none; margin-top: 0;">📋 All Support Tickets</h2>
            <p>Browse submitted tickets and their triage results</p>
        </div>
        """, unsafe_allow_html=True)
        
        try:
            response = requests.get(f"{API_BASE_URL}/stats")
            if response.status_code == 200:
                stats = response.json()
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("🎫 Total Tickets", stats.get("total_tickets_processed", 0))
                with col2:
                    st.metric("💬 Feedback Provided", stats.get("total_feedback_collected", 0))
                with col3:
                    acceptance_rate = 0
                    total_feedback = (
                        stats.get("accepted_responses", 0) + 
                        stats.get("edited_responses", 0) + 
                        stats.get("rejected_responses", 0)
                    )
                    if total_feedback > 0:
                        acceptance_rate = (
                            stats.get("accepted_responses", 0) + stats.get("edited_responses", 0)
                        ) / total_feedback * 100
                    st.metric("Acceptance Rate", f"{acceptance_rate:.1f}%")
                
                st.markdown("---")
                
                if stats.get("total_tickets_processed", 0) > 0:
                    tickets_response = requests.get(f"{API_BASE_URL}/tickets/all")
                    if tickets_response.status_code == 200:
                        tickets = tickets_response.json()
                        
                        st.subheader(f"Tickets ({len(tickets)})")
                        
                        for idx, ticket in enumerate(tickets):
                            with st.expander(f"{ticket['subject']} | {ticket['category']} | {ticket['customer_id']}"):
                                st.write(f"**Ticket ID:** {ticket['ticket_id']}")
                                st.write(f"**Created:** {ticket['created_at']}")
                                st.write(f"**Customer:** {ticket['customer_id']}")
                                st.write(f"**Category:** {ticket['category']}")
                                st.write(f"**Confidence:** {ticket.get('category_confidence', 0):.1%}")
                                
                                st.markdown("---")
                                st.subheader("Issue Description")
                                st.write(ticket['description'])
                                
                                st.markdown("---")
                                st.subheader("Proposed Response")
                                st.write(ticket.get('proposed_response', 'N/A'))
                                
                                st.markdown("---")
                                st.write(f"**Feedback Type:** {ticket.get('feedback_type', 'No feedback yet')}")
                    else:
                        st.error("Error fetching tickets")
                else:
                    st.info("No tickets processed yet")
            else:
                st.error("Error fetching stats")
        except Exception as e:
            st.error(f"Error: {str(e)}")

    elif page == "📊 View Stats":
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 2em; border-radius: 12px; color: white; margin-bottom: 2em;">
            <h2 style="color: white; border: none; margin-top: 0;">📊 System Statistics</h2>
            <p>Real-time performance metrics and feedback analytics</p>
        </div>
        """, unsafe_allow_html=True)
        
        try:
            response = requests.get(f"{API_BASE_URL}/stats")
            if response.status_code == 200:
                stats = response.json()
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("🎫 Total Tickets", stats.get("total_tickets_processed", 0))
                with col2:
                    st.metric("💬 Feedback Collected", stats.get("total_feedback_collected", 0))
                with col3:
                    st.metric("✅ Accepted", stats.get("accepted_responses", 0))
                with col4:
                    st.metric("✏️ Edited", stats.get("edited_responses", 0))
                
                st.metric("❌ Rejected", stats.get("rejected_responses", 0))
                
                col1, col2 = st.columns(2)
                with col1:
                    total_fb = (stats.get("accepted_responses", 0) + 
                               stats.get("edited_responses", 0) + 
                               stats.get("rejected_responses", 0))
                    if total_fb > 0:
                        acceptance = (stats.get("accepted_responses", 0) + 
                                    stats.get("edited_responses", 0)) / total_fb * 100
                        st.metric("Acceptance Rate", f"{acceptance:.1f}%")
                
                with col2:
                    if total_fb > 0:
                        pure_acceptance = stats.get("accepted_responses", 0) / total_fb * 100
                        st.metric("Pure Acceptance", f"{pure_acceptance:.1f}%")
            else:
                st.error("Error fetching stats")
        except Exception as e:
            st.error(f"Error: {str(e)}")


    elif page == "📈 Drift Dashboard":
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 2em; border-radius: 12px; color: white; margin-bottom: 2em;">
            <h2 style="color: white; border: none; margin-top: 0;">📈 Acceptance Rate Drift Dashboard</h2>
            <p>Real-time anomaly detection and acceptance rate trends</p>
        </div>
        """, unsafe_allow_html=True)
        
        try:
            # Auto-regenerate dashboard from real data
            import subprocess
            import os
            
            dashboard_path = "data/drift_dashboard.html"
            
            # Regenerate dashboard to ensure real-time data
            st.info("Regenerating dashboard with latest data...")
            result = subprocess.run([".venv\\Scripts\\python.exe", "generate_dashboard.py"], 
                                  capture_output=True, text=True, cwd=os.getcwd())
            
            if os.path.exists(dashboard_path):
                with open(dashboard_path, "r", encoding="utf-8") as f:
                    html_content = f.read()
                
                st.components.v1.html(html_content, height=1200, scrolling=True)
                
                # Also show the JSON data
                with open("data/drift_dashboard.json", "r", encoding="utf-8") as f:
                    dashboard_data = json.load(f)
                
                st.subheader("Current Metrics")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Acceptance Rate", f"{dashboard_data['current_metrics']['acceptance_rate']:.1%}")
                with col2:
                    st.metric("Rejection Rate", f"{dashboard_data['current_metrics']['rejection_rate']:.1%}")
                with col3:
                    st.metric("Edit Rate", f"{dashboard_data['current_metrics']['edit_rate']:.1%}")
                with col4:
                    st.metric("Total Tickets", dashboard_data['current_metrics']['total_tickets'])
                
                st.subheader("Alerts")
                alerts = dashboard_data['drift_analysis'].get('alerts', [])
                if alerts:
                    for alert in alerts:
                        if alert['severity'] == 'critical':
                            st.error(f"🔴 {alert['message']}")
                        else:
                            st.warning(f"🟡 {alert['message']}")
                else:
                    st.success("✓ No alerts - system performing normally")
            else:
                st.error("Dashboard file not found. Please run generate_dashboard.py first.")
        except Exception as e:
            st.error(f"Error loading dashboard: {str(e)}")

    elif page == "🔄 Feedback History":

        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 2em; border-radius: 12px; color: white; margin-bottom: 2em;">
            <h2 style="color: white; border: none; margin-top: 0;">🔄 Learning Database Status</h2>
            <p>System learning and feedback analytics</p>
        </div>
        """, unsafe_allow_html=True)
        
        try:
            response = requests.get(f"{API_BASE_URL}/stats")
            if response.status_code == 200:
                stats = response.json()
                
                st.subheader("📊 Feedback Summary")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Accepted Responses", stats.get("accepted_responses", 0))
                with col2:
                    st.metric("Edited Responses", stats.get("edited_responses", 0))
                with col3:
                    st.metric("Rejected Responses", stats.get("rejected_responses", 0))
                
                st.info("The system learns from agent feedback to improve response generation.")
            else:
                st.error("Error fetching stats")
        except Exception as e:
            st.error(f"Error: {str(e)}")

    elif page == "🔗 Causal Loop":
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 2em; border-radius: 12px; color: white; margin-bottom: 2em;">
            <h2 style="color: white; border: none; margin-top: 0;">🔗 System Causal Loop Diagram</h2>
            <p>Understanding how feedback signals close the quality improvement loop</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Create tabs for different views
        tab1, tab2, tab3 = st.tabs(["📊 Main Diagram", "🔄 Feedback Flow", "📚 Key Insights"])
        
        with tab1:
            st.subheader("Quality Feedback Loop System")
            st.markdown("""
### System Dynamics Overview

This diagram shows how feedback signals close the loop on quality and continuous improvement in the support triage system.

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        QUALITY FEEDBACK LOOP SYSTEM                              │
└─────────────────────────────────────────────────────────────────────────────────┘


                           ┌──────────────────────┐
                           │   NEW TICKET ARRIVES │
                           └──────────┬───────────┘
                                      │
                                      ▼
                    ┌─────────────────────────────────┐
                    │  CLASSIFIER EVALUATES TICKET    │
                    │  (Rule-based with keywords)     │
                    └──────────────┬──────────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │  CONFIDENCE SCORE ASSIGNED  │  ◄──────┐
                    │  (0.0 - 1.0)                │         │
                    └──────────────┬──────────────┘         │
                                   │                        │
                    ┌──────────────▼──────────────┐         │
                    │  RAG RETRIEVES KNOWLEDGE    │         │
                    │  BASE ARTICLES              │         │
                    └──────────────┬──────────────┘         │
                                   │                        │
                    ┌──────────────▼──────────────┐         │
                    │  TONE-MATCHED RESPONSE      │         │
                    │  GENERATION                 │         │
                    └──────────────┬──────────────┘         │
                                   │                        │
                    ┌──────────────▼──────────────┐         │
                    │  RAGAS QUALITY SCORING      │         │
                    │  (Faithfulness,Relevance)   │         │
                    └──────────────┬──────────────┘         │
                                   │                        │
                    ┌──────────────▼──────────────┐         │
                    │  CONFIDENCE ROUTING DECISION│         │
                    │  - AUTO_SEND                │         │
                    │  - REVIEW                   │         │
                    │  - ESCALATE                 │         │
                    └──────────────┬──────────────┘         │
                                   │                        │
                ┌──────────────────┼──────────────────┐     │
                │                  │                  │     │
                ▼                  ▼                  ▼     │
        ┌────────────────┐  ┌────────────────┐ ┌─────────┐ │
        │ AUTO-SENT TO   │  │  HUMAN REVIEW  │ │ESCALATED│ │
        │ CUSTOMER       │  │   BY AGENT     │ │  TO VIP │ │
        │ (ROUTING=AUTO) │  │(ROUTING=REVIEW)│ │ SUPPORT │ │
        └────────┬───────┘  └────────┬───────┘ └────┬────┘ │
                 │                  │                │      │
                 │                  │     ┌─────────┘      │
                 │                  │     │                │
                 ▼                  ▼     ▼                │
        ┌────────────────────────────────────┐              │
        │  AGENT PROVIDES FEEDBACK           │              │
        │  ✓ ACCEPTED - Response was perfect │              │
        │  ✎ EDITED - Agent improved it      │              │
        │  ✗ REJECTED - Response was wrong   │              │
        └────────────────┬───────────────────┘              │
                         │                                   │
          ┌──────────────┼──────────────┐                   │
          │              │              │                   │
          ▼              ▼              ▼                   │
    [ACCEPTED]     [EDITED]         [REJECTED]             │
          │              │              │                   │
          │         ┌─────┴────┐        │                   │
          │         │          │        │                   │
          ▼         ▼          ▼        ▼                   │
    ┌─────────────────────────────────────┐                │
    │ FMEA FAILURE DETECTION              │                │
    │ (If Conf≥0.75 & (Edited|Rejected))  │                │
    │ → Log high-confidence failures      │                │
    └──────────────┬──────────────────────┘                │
                   │                                        │
                   ▼                                        │
    ┌──────────────────────────────────────┐              │
    │ QUALITY METRICS UPDATED              │              │
    │ - Acceptance rate by confidence      │              │
    │ - Rejection rate by category         │              │
    │ - Edit patterns by tone              │              │
    │ - RAGAS correlation                  │              │
    └──────────────┬───────────────────────┘              │
                   │                                       │
                   ▼                                       │
    ┌──────────────────────────────────────┐             │
    │ CALIBRATION ANALYSIS DETECTS ISSUES  │             │
    │ - Over-confident ranges              │             │
    │ - Under-confident ranges             │             │
    │ - Quality-confidence correlation     │             │
    └──────────────┬───────────────────────┘             │
                   │                                      │
          ┌────────┴───────────┐                         │
          │                    │                         │
          ▼                    ▼                         │
    [OVER-CONFIDENT]    [UNDER-CONFIDENT]               │
          │                    │                         │
          ▼                    ▼                         │
    - Lower            - Raise routing                   │
      confidence         thresholds                      │
      thresholds    - Auto-send more                     │
    - More human          responses                      │
      reviews        - Trust confidence                  │
    - Improve           more                            │
      classifier                                         │
          │                    │                         │
          └────────┬───────────┘                         │
                   │                                     │
                   ▼                                     │
    ┌──────────────────────────────────────┐            │
    │ TRUST ARCHITECTURE ADJUSTED           │            │
    │ (tunable_config.json)                │            │
    │ - Confidence thresholds updated      │            │
    │ - Quality gates modified              │            │
    │ - Routing policies refined            │            │
    │ - Auto-send % adjusted                │            │
    └──────────────┬───────────────────────┘            │
                   │                                     │
                   │  ◄─────────────────────────────────┘
                   │  (Loop closes: Next batch uses improved thresholds)
                   │
                   ▼
    ┌──────────────────────────────────────┐
    │ IMPROVED PERFORMANCE METRICS         │
    │ - Higher acceptance rate             │
    │ - Fewer escalations                  │
    │ - Better customer satisfaction       │
    │ - Smarter routing decisions          │
    └──────────────────────────────────────┘
```
            """)
        
        with tab2:
            st.subheader("Feedback Data Flow")
            st.markdown("""
```
┌─────────────────────────────────────┐
│ Agent Feedback                      │
└────────────────┬────────────────────┘
                 │
      ┌──────────┼──────────┐
      │          │          │
      ▼          ▼          ▼
  Accepted    Edited     Rejected
      │          │          │
      └──────────┼──────────┘
                 │
      ┌──────────▼──────────┐
      │ Store in feedback.  │
      │ json with:          │
      │ - ticket_id         │
      │ - feedback_type     │
      │ - original_response │
      │ - final_response    │
      │ - timestamp         │
      └──────────┬──────────┘
                 │
      ┌──────────▼──────────┐
      │ Trigger FMEA        │
      │ Analysis if:        │
      │ conf ≥ 0.75 &&      │
      │ (edited|rejected)   │
      └──────────┬──────────┘
                 │
      ┌──────────▼──────────┐
      │ Update Metrics:     │
      │ - Confidence bucket │
      │ - Category accuracy │
      │ - Tone effectiveness│
      │ - Quality score     │
      └──────────┬──────────┘
                 │
      ┌──────────▼──────────┐
      │ Recalculate         │
      │ Calibration Curve   │
      └──────────┬──────────┘
                 │
      ┌──────────▼──────────┐
      │ Generate            │
      │ Recommendations:    │
      │ - Threshold changes │
      │ - Process improvements
      │ - Training focus    │
      └──────────┬──────────┘
                 │
      ┌──────────▼──────────┐
      │ Apply Changes to    │
      │ trust_config.json   │
      │ (Automatic or       │
      │  Manual approval)   │
      └──────────┬──────────┘
                 │
      ┌──────────▼──────────┐
      │ Next Batch Uses     │
      │ Improved Thresholds │
      │ (Loop Closes!)      │
      └─────────────────────┘
```

**Key Signals:**

| Feedback | Signal | Action | Weight |
|----------|--------|--------|--------|
| ✓ ACCEPTED | Classifier/Generator working well | Maintain/increase confidence | +1.0 |
| ✎ EDITED | Close but not perfect | Review templates, tone matching | +0.5 |
| ✗ REJECTED | Major failure | Lower confidence, escalate similar | -1.0 |
            """)
        
        with tab3:
            st.subheader("Key Insights & Equilibrium")
            st.markdown("""
### Reinforcing Loops (Positive Feedback)

**Loop 1: Quality Virtuous Cycle**
- Better Quality → More Accepted → Higher Confidence Warranted
- → Better Calibration → Better Routing → Better Quality

**Loop 2: Learning Feedback**
- More Feedback Data → Better Calibration → Better Thresholds
- → More Aligned Routing → Better Feedback Quality

### Balancing Loops (Corrective)

**Loop 1: Over-Confidence Correction**
- Over-Confident → High Rejections → Lower Thresholds
- → More Review Required → Fewer False Auto-Sends

**Loop 2: Under-Confidence Correction**
- Under-Confident → Low Rejections → Raise Thresholds
- → More Auto-Sends → Optimal Throughput

### System Equilibrium Point

The system naturally settles to:
- ✓ **Acceptance Rate**: 75-85% for high-confidence responses
- ✎ **Edit Rate**: 5-10% (close misses)
- ✗ **Rejection Rate**: 5-10% (failures caught before customer)
- ↑ **Escalation Rate**: 10-15% (uncertain cases handled by humans)
- ◆ **Auto-Send Rate**: 60-70% (balancing speed and safety)

### Key Properties

| Property | Characteristic |
|----------|---|
| Stability | Stable with proper dampening |
| Response Time | Fast for immediate feedback, slower for trends |
| Learning | Continuous, incremental, data-driven |
| Robustness | Multiple feedback channels reduce failure |
| Transparency | All decisions logged and explainable |

### Real Example: How One Feedback Closes the Loop

**Scenario: Mid-confidence billing response gets rejected**

1. **9:15 AM** - Ticket arrives (Subject: "Double billing issue", Confidence: 0.72)
2. **9:15:30 AM** - Routing decision: REVIEW (confidence in MEDIUM band)
3. **9:20 AM** - Agent reviews and REJECTS (response doesn't address refund)
4. **9:20:30 AM** - Feedback recorded in feedback.json
5. **9:21 AM** - Batch calibration detects: Billing category 0.65-0.75 confidence has 20% rejection (expected: 70%)
6. **9:22 AM** - Recommendation: Lower confidence for billing from 0.72 → 0.65
7. **9:25 AM** - Config updated (future billing tickets use new threshold)
8. **9:30 AM** - Next similar ticket routes to REVIEW (not AUTO) → Better outcome

**Loop Time**: ~15 minutes | **Impact**: Prevents similar failures in future billing tickets

### System Benefits

✅ **No Batch Retraining** - Real-time threshold adjustments  
✅ **Explainability** - Know WHY each ticket routes where  
✅ **Self-Correcting** - Over-confidence automatically triggers review  
✅ **Scale** - Learn from 1000s of tickets/week  
✅ **No Divergence** - Calibration loop prevents failures  
            """)

except Exception as e:
    st.error(f"Application Error: {str(e)}")
    import traceback
    st.write(traceback.format_exc())
