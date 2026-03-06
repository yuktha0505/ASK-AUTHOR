# Design Document - Ask Author Platform

## System Architecture

### High-Level Architecture

```
┌─────────────┐
│   Browser   │
│  (Frontend) │
└──────┬──────┘
       │ HTTPS
       ▼
┌─────────────────┐
│  Amazon S3      │
│ Static Hosting  │
└─────────────────┘
       │
       │ REST API
       ▼
┌─────────────────┐
│  API Gateway    │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐      ┌──────────────┐
│  AWS Lambda     │─────▶│  Amazon S3   │
│  (Backend)      │      │  (Content)   │
└──────┬──────────┘      └──────────────┘
       │
       ▼
┌─────────────────┐
│ Amazon Bedrock  │
│  (Nova Lite)    │
└─────────────────┘
```

## Component Design

### 1. Frontend (index.html)

**Purpose**: Single-page chat interface for user interaction

**Key Components:**
- Chat container with message display
- Input field and send button
- Typing indicator
- Message rendering (user/bot)

**Styling:**
- Gradient background (#1f2937 to #111827)
- Blue theme (#2563eb)
- Rounded message bubbles
- Fade-in animations

**API Integration:**
- Endpoint: `https://4me8jhpnb4.execute-api.ap-south-1.amazonaws.com/ask`
- Method: POST
- Payload: `{ question, session_id }`
- Response: `{ answer, sources }`

### 2. Backend - Lambda Handler (app.py)

**Purpose**: API request handling and orchestration

**Responsibilities:**
- Parse Lambda event (API Gateway proxy format)
- Handle CORS preflight (OPTIONS)
- Validate input (non-empty question)
- Invoke RAG engine for retrieval
- Format response with sources
- Error handling and status codes

**Key Functions:**
- `lambda_handler(event, context)`: Main entry point
- `format_answer(results, question)`: Response formatting

**Response Structure:**
```python
{
    "statusCode": 200,
    "headers": {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Allow-Methods": "POST, OPTIONS"
    },
    "body": json.dumps({
        "answer": str,
        "sources": list[str]
    })
}
```

### 3. RAG Engine (rag.py)

**Purpose**: Document retrieval and relevance scoring

**Class: RAGEngine**

**Methods:**
- `__init__()`: Load documents from S3 on initialization
- `load_documents()`: Fetch JSON from S3 bucket
- `tokenize(text)`: Lowercase, remove punctuation, split into tokens
- `retrieve(query, top_k=2)`: Find most relevant documents

**Retrieval Algorithm:**
1. Tokenize query
2. For each document:
   - Tokenize content
   - Calculate token overlap (set intersection)
   - Score = number of overlapping tokens
3. Sort by score (descending)
4. Return top_k documents with score > 0

**Document Format:**
```json
[
    {
        "title": "Document Title",
        "content": "Full text content..."
    }
]
```

### 4. LLM Service (llm_service.py)

**Purpose**: Abstract LLM interaction with mode switching

**Modes:**

#### Local Mode
- Returns truncated content summary (500 chars)
- No external API calls
- Used for development/testing

#### Bedrock Mode
- Invokes Amazon Bedrock Nova Lite v1
- Structured prompt engineering
- Temperature: 0.2 (deterministic)
- Max tokens: 500
- Top-p: 0.9

**Prompt Template:**
```
You are an AI assistant for an Indian media platform.
Answer ONLY using the provided context.
If answer is not present, say:
"The information is not available in the content library."

Be clear, structured, and concise.
If question is in Hindi, respond in Hindi.

Context:
{context_text}

Question:
{question}
```

## Data Flow

### Request Flow
1. User types question → Frontend
2. Frontend sends POST to API Gateway
3. API Gateway triggers Lambda
4. Lambda validates input
5. RAG engine retrieves relevant documents from S3
6. LLM service generates answer (local or Bedrock)
7. Response formatted with sources
8. JSON returned through API Gateway
9. Frontend displays answer and sources

### Error Flow
- Empty question → 400 with validation message
- No relevant content → 200 with "No relevant content found"
- S3 error → 500 with error details
- Bedrock error → 500 with error details
- Network error → Frontend shows connection error

## Security Design

### CORS Configuration
- Allow-Origin: `*` (wildcard for public access)
- Allow-Headers: `Content-Type`
- Allow-Methods: `POST, OPTIONS`

### AWS IAM Permissions Required
- Lambda execution role:
  - `s3:GetObject` on content bucket
  - `bedrock:InvokeModel` for Nova Lite
  - CloudWatch Logs for monitoring

### Data Privacy
- No user authentication (public access)
- Session ID sent but not persisted
- No PII collection or storage

## Performance Optimization

### Cold Start Mitigation
- RAG engine initialized at module level (outside handler)
- Documents loaded once and cached in memory
- Subsequent invocations reuse loaded data

### Response Time Breakdown
- Document retrieval: ~50-100ms (S3 + tokenization)
- LLM inference (Bedrock): ~1-2s
- Total: ~2-3s typical

## Deployment Architecture

### Frontend Deployment
- Upload `index.html` to S3 bucket
- Enable static website hosting
- Configure bucket policy for public read
- Update API endpoint URL in JavaScript

### Backend Deployment
1. Package Lambda function:
   ```bash
   pip install -r requirements.txt -t package/
   cp backend/*.py package/
   cd package && zip -r ../lambda.zip .
   ```
2. Upload to Lambda
3. Configure environment variables (MODE, AWS_REGION)
4. Set Lambda timeout (30s recommended)
5. Attach IAM role with required permissions

### API Gateway Configuration
- Create REST API
- POST method on `/ask` resource
- Lambda proxy integration
- Enable CORS
- Deploy to stage

## Future Enhancements

### Potential Improvements
- Vector embeddings for better retrieval (e.g., Amazon Titan Embeddings)
- Conversation history with DynamoDB
- User authentication with Cognito
- Streaming responses for better UX
- Content management API
- Analytics dashboard
- Multi-language support expansion
- Caching layer (ElastiCache) for frequent queries

