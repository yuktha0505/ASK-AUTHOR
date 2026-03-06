# Project Structure

## Directory Layout

```
.
├── backend/              # Python Lambda backend
│   ├── app.py           # Lambda handler, API routing, CORS
│   ├── llm_service.py   # LLM integration (local/Bedrock modes)
│   ├── rag.py           # RAG engine, document retrieval
│   └── requirements.txt # Python dependencies
├── frontend/            # Static web frontend
│   └── index.html       # Single-page chat interface
├── .kiro/               # Kiro configuration
│   ├── specs/           # Feature specifications
│   └── steering/        # Project guidance documents
└── README.md            # Project documentation
```

## Architecture Patterns

### Backend Organization
- **app.py**: Entry point, handles Lambda events, CORS, request/response formatting
- **rag.py**: RAGEngine class - document loading, tokenization, retrieval logic
- **llm_service.py**: LLM abstraction layer supporting multiple modes

### Key Design Decisions
- **Stateless Lambda**: No persistent session storage (session_memory dict exists but unused)
- **Cold start optimization**: RAG engine initialized once at module level
- **Simple retrieval**: Token overlap scoring (no embeddings or vector search)
- **CORS enabled**: Wildcard origin for frontend access

### Response Format
All API responses include:
- `answer`: Generated or formatted response text
- `sources`: List of document titles used

### Error Handling
- 400: Missing/invalid question
- 500: Internal errors with error message in response
- All responses include CORS headers


