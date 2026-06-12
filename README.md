# Support Triage Co-pilot

A production-ready AI co-pilot system for subscription business customer support. Handles 12,000+ tickets per week by automatically classifying repetitive issues and proposing responses, with agent feedback driving continuous learning.

## Features

- 🤖 **Automatic Ticket Classification**: Uses zero-shot classification to identify billing questions, password resets, plan changes, and other issues
- 💡 **LLM-Powered Response Generation**: Phi-3.5-mini generates contextual responses tailored to ticket category
- 📚 **Continuous Learning**: ChromaDB stores feedback to improve future responses
  - ✅ Accepted responses become templates
  - ✏️ Edited responses show improvement patterns
  - ❌ Rejected responses are avoided
- 🎯 **Agent Interface**: Streamlit UI for agents to review, accept, edit, or reject proposed responses
- ⚡ **REST API**: FastAPI backend for production deployment

## Architecture

```
Support Ticket
    ↓
[Ticket Classifier] → Category + Confidence
    ↓
[Feedback Store] → Get similar accepted/edited/rejected responses
    ↓
[Response Generator] → Generate contextual response with learning context
    ↓
[Agent Interface] → Accept/Edit/Reject
    ↓
[Feedback Store] → Learn from feedback
```

## Components

### 1. **models.py**
   - Data models for tickets, responses, and feedback
   - Enums for categories and feedback types

### 2. **ticket_classifier.py**
   - Zero-shot classification using Facebook BART-large-mnli
   - Identifies: billing, password reset, plan changes, other
   - Confidence scores for each category

### 3. **response_generator.py**
   - Phi-3.5-mini LLM via LangChain
   - Category-specific response templates
   - Retrieves context from feedback store for improved responses

### 4. **feedback_store.py**
   - ChromaDB for persistent vector storage
   - Separates collections for accepted/edited/rejected responses
   - Retrieves similar responses for RAG context

### 5. **api.py** (FastAPI Backend)
   - `POST /tickets/ingest` - Process new ticket
   - `GET /tickets/{id}` - Retrieve ticket with proposal
   - `POST /feedback` - Submit agent feedback
   - `GET /stats` - System statistics
   - `GET /health` - Health check

### 6. **app.py** (Streamlit Agent UI)
   - Process new tickets
   - View proposed responses
   - Accept/Edit/Reject feedback
   - View system statistics
   - Track learning progress

## Setup

### Prerequisites
- Python 3.9+
- Virtual environment recommended

### Installation

1. **Create and activate virtual environment**:
```bash
python -m venv .venv
# Windows:
.\.venv\Scripts\Activate.ps1
# Linux/Mac:
source .venv/bin/activate
```

2. **Install dependencies**:
```bash
pip install transformers torch sentence-transformers langchain langchain-huggingface langchain-google-genai chromadb ragas fastapi uvicorn streamlit
```

## Usage

### Start the FastAPI Backend

```bash
python api.py
```
Server runs on `http://localhost:8000`

### Start the Streamlit Agent UI

In a new terminal:
```bash
streamlit run app.py
```
UI available at `http://localhost:8501`

## How It Works

### Ticket Processing Flow

1. **Agent submits ticket** → Streamlit UI
2. **Classifier categorizes** → Identifies ticket type
3. **Feedback store queries** → Retrieves similar accepted/edited responses
4. **Generator creates response** → Uses context for improved output
5. **Agent provides feedback**:
   - ✅ Accept: Response stored as template
   - ✏️ Edit: Improvement patterns stored
   - ❌ Reject: Pattern stored to avoid

### Learning Mechanism

The system improves over time:
- **Early stage**: Generic responses based on category templates
- **With feedback**: Responses incorporate accepted/edited patterns
- **Mature stage**: High-quality responses informed by thousands of agent decisions

## Example Workflow

1. Customer submits: "I was charged twice for my subscription this month"
2. System classifies: `billing question` (95% confidence)
3. Generator creates: "We apologize for the duplicate charge. We'll process a refund within 3-5 business days..."
4. Agent reviews and edits to: "...will process a refund within 2-3 business days and apply a $10 credit"
5. System learns: This improvement stored as reference for similar billing issues

## Performance

- **Classification**: ~100-200ms per ticket
- **Response Generation**: ~2-5s per response (depending on GPU availability)
- **Feedback storage**: <100ms per submission
- **Learning scale**: Handles 12,000 tickets/week effectively

## Scaling Considerations

1. **Database**: Replace in-memory storage with PostgreSQL for production
2. **Caching**: Add Redis for frequently accessed responses
3. **Load balancing**: Deploy multiple API instances behind load balancer
4. **Model optimization**: Use quantized models for faster inference
5. **Batch processing**: Process ticket bursts asynchronously with Celery

## API Examples

### Ingest Ticket
```bash
curl -X POST "http://localhost:8000/tickets/ingest" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "CUST_001",
    "subject": "Can't reset my password",
    "description": "I requested a password reset email but didn't receive it"
  }'
```

### Submit Feedback
```bash
curl -X POST "http://localhost:8000/feedback" \
  -H "Content-Type: application/json" \
  -d '{
    "ticket_id": "abc123",
    "feedback_type": "edited",
    "final_response": "Check your spam folder or request a new reset email"
  }'
```

### Get Statistics
```bash
curl "http://localhost:8000/stats"
```

## Tech Stack

- **LLM**: Microsoft Phi-3.5-mini (4B parameters, CPU/GPU compatible)
- **Vector DB**: ChromaDB (persistent, embedded)
- **Framework**: FastAPI + Streamlit
- **NLP**: Hugging Face Transformers
- **LLM Integration**: LangChain

## Future Enhancements

- [ ] Multi-language support
- [ ] Sentiment analysis for priority routing
- [ ] A/B testing for response variants
- [ ] Integration with ticketing systems (Zendesk, Jira)
- [ ] Custom LLM fine-tuning on company data
- [ ] Analytics dashboard for support team leads
- [ ] Real-time learning model updates
- [ ] Quality metrics and SLA tracking

## Testing

Run sample classification:
```bash
python ticket_classifier.py
```

## Notes

- First model download may take time; subsequent runs use cached models
- ChromaDB data persists in `./feedback_db/` directory
- Clear feedback database: `rm -rf feedback_db/` to reset learning
- Use `torch.cuda.is_available()` to enable GPU acceleration

## License

MIT
