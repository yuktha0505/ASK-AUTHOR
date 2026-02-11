# Ask Author / Ask Channel - Design Document

## 1. System Architecture

### 1.1 High-Level Architecture

```
┌─────────────────┐   ┌──────────────────┐   ┌─────────────────┐
│  WhatsApp UX    │──▶│  API Gateway     │──▶│  Lambda Router  │
│  (React/Voice)  │   │  + Auth          │   │                 │
└─────────────────┘   └──────────────────┘   └────────┬────────┘
                                                       │
┌─────────────────┐                                   │
│  User Query     │◄────── Embed ──────┐              │
│ "GST repo Hindi"│                    │              │
└────────┬────────┘                    │              │
         │                             │              │
         ▼                             ▼              │
┌─────────────────┐          ┌─────────────────┐     │
│  OpenSearch     │          │  Bedrock LLM    │     │
│ (Vector Store)  │◄────────▶│ (RAG Synthesis) │     │
└─────────────────┘          └─────────────────┘     │
         ▲                            │               │
         │                            │               │
┌─────────────────┐                  ▼               │
│  S3 Content     │          ┌─────────────────┐     │
│  + Metadata     │◄────────▶│    Amazon       │◄────┘
└─────────────────┘          │  Personalize    │
                             │  (Next Cards)   │
                             └─────────────────┘
```

### 1.2 Component Overview

**Frontend Layer:**
- React-based WhatsApp-style chat interface
- Voice input/output integration (Transcribe/Polly)
- Real-time streaming response display
- Source citation rendering with timestamps

**API Layer:**
- API Gateway with authentication/authorization
- Lambda router for request distribution
- WebSocket support for streaming responses

**AI/ML Layer:**
- Amazon Bedrock (Claude/Titan) for RAG synthesis
- OpenSearch for vector similarity search
- Amazon Personalize for behavior-based recommendations
- Transcribe/Rekognition for content processing

**Storage Layer:**
- S3 for raw content and metadata
- OpenSearch for vector embeddings
- DynamoDB for user profiles and interaction history

**Event Processing:**
- EventBridge for content ingestion triggers
- Kinesis Firehose for user behavior streaming

## 2. Core Data Flows

### 2.1 Content Ingestion Pipeline (Event-Driven)

```
S3 Upload → EventBridge → Lambda Orchestrator
                              │
                              ├─▶ Transcribe (audio/video)
                              ├─▶ Rekognition (visual tagging)
                              │
                              ▼
                         Chunking Lambda (500 tokens)
                              │
                              ▼
                         Embedding Generation (Bedrock)
                              │
                              ▼
                         OpenSearch Indexing
```

**Implementation Details:**
- **Trigger:** S3 PutObject event → EventBridge rule
- **Orchestrator Lambda:** Determines content type, routes to appropriate processor
- **Transcribe Job:** Async job with callback to Lambda on completion
- **Chunking Strategy:** 500-token segments with 50-token overlap for context
- **Embedding Model:** Amazon Titan Embeddings (1536 dimensions)
- **Index Schema:** See Section 4.2

**Processing Time SLA:** <5 minutes for content up to 1 hour duration

### 2.2 Query Processing Pipeline (Real-Time)

```
User Query → API Gateway → Lambda Handler
                              │
                              ▼
                         Query Embedding (Bedrock)
                              │
                              ▼
                    OpenSearch Vector Search (k=5)
                              │
                              ▼
                    Bedrock LLM RAG Synthesis
                    ("Use only these sources: {chunks}")
                              │
                              ├─▶ Stream Response
                              ├─▶ Extract Citations
                              └─▶ Personalize Recommendations
                              │
                              ▼
                         Return to Client
```

**Implementation Details:**
- **Query Embedding:** Same model as content (Titan Embeddings)
- **Vector Search:** Cosine similarity, k=5, minimum score threshold 0.7
- **LLM Prompt:** See Section 3.1
- **Streaming:** Server-Sent Events (SSE) via API Gateway WebSocket
- **Citation Extraction:** Regex parsing of source URLs from LLM response
- **Personalize Call:** Async, non-blocking for follow-up cards

**Latency Target:** <3 seconds end-to-end (95th percentile)

### 2.3 Personalization Training Pipeline (Batch)

```
User Interactions → Kinesis Stream → Firehose
                                        │
                                        ▼
                                   S3 Staging
                                        │
                                        ▼
                              Personalize Dataset Import
                                        │
                                        ▶ Train Model (daily)
                                        │
                                        ▼
                              Personalize Campaign (API)
```

**Implementation Details:**
- **Event Types:** Query, click, watch-time, feedback
- **Kinesis Buffer:** 60 seconds or 1MB batch
- **Dataset Schema:** USER_ID, ITEM_ID, TIMESTAMP, EVENT_TYPE, EVENT_VALUE
- **Training Schedule:** Daily at 2 AM UTC
- **Cold Start:** Content-based filtering for new users (<10 interactions)

## 3. Prompt Engineering

### 3.1 RAG Prompt Template

```
Context: {retrieved_chunks}

Sources: {source_urls}

Instructions:
1. Answer using ONLY the provided context above
2. Cite sources inline using [Source N] format
3. If the answer is not in the context, respond: "I don't have that information in the available content"
4. Keep your response concise (200 words maximum)
5. Suggest 2-3 relevant follow-up questions at the end
6. Maintain the user's language preference (Hindi/English/Hinglish)

Query: {user_query}

Answer:
```

**Prompt Variables:**
- `{retrieved_chunks}`: Top-5 chunks from OpenSearch with metadata
- `{source_urls}`: List of source URLs with timestamps
- `{user_query}`: Original user query in their preferred language

**LLM Configuration:**
- Model: Claude 3 Sonnet (primary) or Titan Text G1 (fallback)
- Temperature: 0.3 (low for factual accuracy)
- Max Tokens: 500
- Stop Sequences: ["Human:", "Context:"]

### 3.2 Follow-Up Question Generation

```
Based on the answer provided and the user's query: "{user_query}", suggest 2-3 relevant follow-up questions that:
1. Explore related topics in the available content
2. Clarify or expand on the current answer
3. Are phrased naturally in {language}

Follow-up questions:
```

## 4. Data Models

### 4.1 Content Metadata (DynamoDB)

**Table:** `AskAuthorContent`

```json
{
  "contentId": "string (PK)",
  "publisherId": "string (GSI PK)",
  "contentType": "article | video | podcast",
  "title": "string",
  "sourceUrl": "string",
  "uploadTimestamp": "number",
  "duration": "number (seconds, for video/audio)",
  "language": "hi | en | mixed",
  "transcriptionStatus": "pending | completed | failed",
  "chunkCount": "number",
  "tags": ["string"],
  "metadata": {
    "author": "string",
    "publishDate": "string",
    "description": "string"
  }
}
```

### 4.2 OpenSearch Index Schema

**Index:** `content-chunks-v1`

```json
{
  "chunkId": "string",
  "contentId": "string",
  "publisherId": "string",
  "chunkIndex": "number",
  "text": "string",
  "embedding": [1536 floats],
  "contentType": "article | video | podcast",
  "sourceUrl": "string",
  "timestamp": "number (for video/audio)",
  "language": "hi | en | mixed",
  "metadata": {
    "title": "string",
    "tags": ["string"],
    "publishDate": "string"
  }
}
```

**Index Settings:**
- Shards: 3 (for 100K content assets)
- Replicas: 2 (for high availability)
- Refresh Interval: 5s
- Vector Engine: NMSLIB (cosine similarity)

### 4.3 User Profile (DynamoDB)

**Table:** `AskAuthorUserProfiles`

```json
{
  "userId": "string (PK)",
  "publisherId": "string (GSI PK)",
  "languagePreference": "hi | en | mixed",
  "interactionCount": "number",
  "lastActiveTimestamp": "number",
  "preferences": {
    "voiceEnabled": "boolean",
    "contentTypes": ["article", "video", "podcast"]
  },
  "personalizeUserId": "string"
}
```

### 4.4 Interaction Events (Kinesis → S3)

```json
{
  "eventId": "string",
  "userId": "string",
  "publisherId": "string",
  "eventType": "query | click | watch | feedback",
  "timestamp": "number",
  "contentId": "string",
  "query": "string (for query events)",
  "watchDuration": "number (for watch events)",
  "feedbackScore": "number (for feedback events)"
}
```

## 5. API Design

### 5.1 Query Endpoint

**POST** `/api/v1/query`

**Request:**
```json
{
  "query": "string",
  "userId": "string",
  "publisherId": "string",
  "language": "hi | en | auto",
  "voiceInput": "boolean"
}
```

**Response (Streaming):**
```json
{
  "queryId": "string",
  "answer": "string (streamed)",
  "citations": [
    {
      "sourceUrl": "string",
      "title": "string",
      "timestamp": "number (optional)",
      "contentType": "article | video | podcast"
    }
  ],
  "followUpQuestions": ["string"],
  "recommendedContent": [
    {
      "contentId": "string",
      "title": "string",
      "sourceUrl": "string",
      "relevanceScore": "number"
    }
  ],
  "metadata": {
    "processingTime": "number (ms)",
    "aiGenerated": true
  }
}
```

### 5.2 Content Upload Endpoint

**POST** `/api/v1/content/upload`

**Request (Multipart):**
```
publisherId: string
contentType: article | video | podcast
file: binary
metadata: {
  title: string
  author: string
  publishDate: string
  description: string
}
```

**Response:**
```json
{
  "contentId": "string",
  "uploadUrl": "string (S3 presigned URL)",
  "status": "processing",
  "estimatedProcessingTime": "number (seconds)"
}
```

### 5.3 Feedback Endpoint

**POST** `/api/v1/feedback`

**Request:**
```json
{
  "queryId": "string",
  "userId": "string",
  "feedbackType": "helpful | not_helpful | incorrect",
  "comment": "string (optional)"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Feedback recorded"
}
```

## 6. Responsible AI Design

### 6.1 Grounded Generation Strategy

**Problem:** LLMs can hallucinate information not present in source material

**Solution:** RAG architecture with strict prompt constraints
- Retrieve Top-5 relevant chunks before generation
- Explicit instruction: "Use ONLY the provided context"
- Fallback response: "I don't have that information" when confidence is low
- Citation requirement enforced in prompt template

**Validation:**
- Post-processing check: Verify all facts in response exist in retrieved chunks
- Confidence scoring: Flag responses with low citation coverage

### 6.2 Mandatory Source Attribution

**Implementation:**
- LLM instructed to cite sources inline using [Source N] format
- Post-processing extracts source URLs and timestamps
- Frontend displays citations as clickable links
- Audit log records which chunks were used for each response

**Compliance:**
- India IT Rules 2026: All AI-generated content labeled "AI-Synthesized from publisher content"
- Frontend displays disclaimer on every response

### 6.3 Privacy and Data Isolation

**Publisher Data Silos:**
- User interactions scoped to publisherId
- Personalize models trained per publisher (no cross-publisher data)
- OpenSearch queries filtered by publisherId field
- DynamoDB access patterns enforce publisher isolation

**User Data Protection:**
- Encryption at rest: S3 (AES-256), DynamoDB (KMS)
- Encryption in transit: TLS 1.3 for all API calls
- Data retention: User interactions retained for 90 days, then archived
- Right to deletion: API endpoint to purge user data across all services

### 6.4 Audit Trail

**Logged Information:**
- Query text, retrieved chunks, generated response
- Source citations used in response
- User feedback on response quality
- Processing time and model version

**Storage:** CloudWatch Logs with 90-day retention

## 7. Performance Optimization

### 7.1 Caching Strategy

**API Gateway Cache:**
- TTL: 1 minute for popular queries
- Cache key: Hash of (query, publisherId, language)
- Invalidation: Manual via API or automatic on content update

**Lambda Layer Cache:**
- Embedding model loaded once per container (warm start optimization)
- OpenSearch connection pooling

**OpenSearch Query Cache:**
- Enabled for vector similarity queries
- Cache size: 10% of heap memory

### 7.2 Cold Start Mitigation

**Lambda Provisioned Concurrency:**
- Query handler: 10 instances (warm)
- Embedding generator: 5 instances (warm)

**OpenSearch Serverless:**
- Auto-scales based on query load
- No cold start for search queries

### 7.3 Cost Optimization

**Bedrock Batch Processing:**
- Content embeddings generated in nightly batch (cheaper than on-demand)
- Query embeddings on-demand (latency-sensitive)

**Personalize On-Demand:**
- Campaign auto-scales with traffic
- Training scheduled during off-peak hours

**S3 Lifecycle Policies:**
- Raw content: Standard storage
- Processed transcripts: Infrequent Access after 30 days
- Archived interactions: Glacier after 90 days

## 8. Error Handling

### 8.1 No Results Found

**Scenario:** OpenSearch returns no chunks with score >0.7

**Response:**
```json
{
  "answer": "I couldn't find relevant information in the available content. Try rephrasing your question or browse the original articles.",
  "suggestions": [
    "Browse recent articles",
    "Try a more specific question",
    "Check spelling and language"
  ]
}
```

### 8.2 Low Confidence Response

**Scenario:** Retrieved chunks have conflicting information or low similarity scores (0.7-0.8)

**Response:**
```json
{
  "answer": "I found multiple interpretations. Here are the relevant sources:",
  "citations": [...],
  "confidence": "low",
  "suggestion": "Review the sources directly for complete context"
}
```

### 8.3 Timeout Handling

**Scenario:** Bedrock LLM takes >2 seconds to respond

**Progressive Disclosure:**
1. Display retrieved sources immediately (0.5s)
2. Stream partial answer as it generates (1-2s)
3. Load audio version asynchronously (2-3s)
4. Load personalized cards last (3-4s)

### 8.4 Service Failures

**Bedrock Unavailable:**
- Fallback: Return retrieved chunks with basic summarization
- User message: "AI synthesis temporarily unavailable, showing source excerpts"

**OpenSearch Unavailable:**
- Fallback: DynamoDB full-text search (slower, less accurate)
- User message: "Using basic search, results may be less relevant"

**Personalize Unavailable:**
- Fallback: Content-based recommendations (no user history)
- No user-facing error (graceful degradation)

## 9. Deployment Architecture

### 9.1 Infrastructure as Code

**Tool:** AWS CDK (TypeScript)

**Stacks:**
- `AskAuthorNetworkStack`: VPC, subnets, security groups
- `AskAuthorStorageStack`: S3 buckets, DynamoDB tables, OpenSearch domain
- `AskAuthorComputeStack`: Lambda functions, API Gateway, EventBridge rules
- `AskAuthorAIStack`: Bedrock model access, Personalize resources
- `AskAuthorMonitoringStack`: CloudWatch dashboards, alarms, X-Ray tracing

### 9.2 CI/CD Pipeline

**Tool:** AWS CodePipeline

**Stages:**
1. **Source:** GitHub webhook triggers pipeline
2. **Build:** CodeBuild compiles Lambda functions, runs unit tests
3. **Test:** Deploy to staging, run integration tests
4. **Approval:** Manual approval for production deployment
5. **Deploy:** CDK deploy to production, blue/green deployment for Lambdas
6. **Verify:** Smoke tests, rollback on failure

**Deployment Pattern:**
- Frontend: ECS Fargate with Application Load Balancer
- Backend: Lambda with versioning and aliases
- Infrastructure: CloudFormation change sets with manual review

### 9.3 Monitoring and Observability

**CloudWatch Dashboards:**
- Query latency (p50, p95, p99)
- Error rates by endpoint
- Bedrock token usage and cost
- OpenSearch query performance
- Personalize recommendation quality

**X-Ray Tracing:**
- End-to-end request tracing
- Service map visualization
- Bottleneck identification

**Alarms:**
- Query latency >3s (95th percentile)
- Error rate >1%
- Bedrock throttling
- OpenSearch cluster health

## 10. Testing Strategy

### 10.1 Unit Tests

**Coverage Target:** >80%

**Test Cases:**
- Lambda function handlers (input validation, error handling)
- Prompt template rendering
- Citation extraction logic
- Chunking algorithm (500 tokens with overlap)
- Embedding generation (mock Bedrock calls)

**Framework:** Jest (TypeScript)

### 10.2 Integration Tests

**RAG Accuracy:**
- Ground truth dataset: 100 query-answer pairs
- Metrics: Precision@5, Recall@5, MRR (Mean Reciprocal Rank)
- Target: >85% answer relevance

**Personalize Offline Evaluation:**
- Historical interaction data split (80/20 train/test)
- Metrics: Precision@K, Coverage, Diversity
- Target: >40% content reuse rate

**End-to-End Latency:**
- Simulate 1000 concurrent queries
- Measure p95 latency
- Target: <3 seconds

### 10.3 E2E Tests

**User Journey:**
1. User submits query via WhatsApp-style interface
2. System returns streaming response with citations
3. User clicks on source citation
4. User provides feedback (helpful/not helpful)
5. System logs interaction to Kinesis
6. Personalize recommendations update

**Framework:** Playwright (browser automation)

### 10.4 Load Testing

**Tool:** Artillery

**Scenarios:**
- 10,000 concurrent users
- 100 queries/second sustained load
- Spike test: 1000 queries/second for 1 minute

**Metrics:**
- Latency degradation under load
- Error rate increase
- Auto-scaling behavior

## 11. Security Considerations

### 11.1 Authentication and Authorization

**User Authentication:**
- OAuth 2.0 / OpenID Connect (publisher-provided identity)
- JWT tokens with 1-hour expiration
- Refresh token rotation

**API Authorization:**
- API Gateway Lambda authorizer
- Scope-based access control (read, write, admin)
- Publisher-level isolation enforced

### 11.2 Input Validation

**Query Sanitization:**
- Max length: 500 characters
- Allowed characters: Alphanumeric, Hindi Unicode, punctuation
- SQL injection prevention (parameterized queries)
- XSS prevention (output encoding)

**Content Upload Validation:**
- File type whitelist: MP4, MOV, MP3, WAV, TXT, HTML
- Max file size: 1GB
- Virus scanning (ClamAV Lambda layer)

### 11.3 Rate Limiting

**API Gateway Throttling:**
- Per-user: 100 requests/minute
- Per-publisher: 10,000 requests/minute
- Burst: 200 requests

**Bedrock Quota Management:**
- Token limit: 1M tokens/day per publisher
- Alert at 80% usage
- Graceful degradation when quota exceeded

## 12. Scalability Considerations

### 12.1 Horizontal Scaling

**Lambda:**
- Concurrent execution limit: 1000 per function
- Auto-scales with request volume
- Reserved concurrency for critical functions

**OpenSearch:**
- Data nodes: 3 (initial), auto-scale to 10
- Master nodes: 3 (dedicated)
- Shard strategy: 1 shard per 50GB data

**DynamoDB:**
- On-demand capacity mode (auto-scaling)
- Global secondary indexes for query patterns

### 12.2 Data Partitioning

**OpenSearch Indices:**
- Partition by publisher: `content-{publisherId}-v1`
- Alias for cross-publisher search (admin only)

**DynamoDB:**
- Partition key: `userId` (high cardinality)
- Sort key: `timestamp` (for time-range queries)

### 12.3 Content Growth Strategy

**Current:** 100K content assets, 10K concurrent users

**Future (1M assets, 100K users):**
- OpenSearch: Increase to 10 data nodes, 10 shards
- Lambda: Increase reserved concurrency
- Bedrock: Request quota increase
- Cost projection: 10x increase (~$50K/month)

## 13. Compliance and Governance

### 13.1 India IT Rules 2026

**AI Content Labeling:**
- Every response includes: "AI-Synthesized from publisher content"
- Disclaimer visible in UI
- Metadata flag: `aiGenerated: true`

**User Consent:**
- Explicit opt-in for personalization
- Clear explanation of data usage
- Opt-out mechanism in user settings

### 13.2 GDPR / DPDP Act

**Data Subject Rights:**
- Right to access: API endpoint to export user data
- Right to deletion: Purge user data across all services
- Right to portability: JSON export of user interactions

**Data Processing Agreement:**
- Publisher is data controller
- Platform is data processor
- DPA signed before onboarding

### 13.3 Audit and Reporting

**Quarterly Reports:**
- AI accuracy metrics (precision, recall)
- User satisfaction scores
- Data breach incidents (if any)
- Compliance violations (if any)

**Audit Logs:**
- All data access logged to CloudWatch
- Immutable audit trail (WORM S3 bucket)
- Retention: 7 years

## 14. Future Enhancements

### 14.1 Multi-Modal Responses

**Vision:** Generate image/video clips in responses

**Implementation:**
- Rekognition to extract keyframes from videos
- Bedrock to select relevant frames for query
- Display inline with text response

### 14.2 Advanced Conversation Memory

**Vision:** Multi-turn conversations with context retention

**Implementation:**
- DynamoDB conversation history table
- Context window: Last 5 turns
- Prompt includes conversation history

### 14.3 Collaborative Filtering

**Vision:** "Users who asked X also asked Y"

**Implementation:**
- Personalize User-Personalization recipe
- Cold-start handling with content-based filtering

### 14.4 Content Recommendation Widgets

**Vision:** Embeddable widgets for publisher websites

**Implementation:**
- JavaScript SDK for easy integration
- Iframe-based widget with customizable styling
- Real-time recommendations via API

## 15. Correctness Properties

### 15.1 Grounded Generation Property

**Property:** Every fact in the generated answer must exist in at least one retrieved chunk

**Test Strategy:**
- Extract factual claims from LLM response using NLP
- Verify each claim against retrieved chunks using semantic similarity
- Flag responses with <90% claim coverage

**PBT Implementation:**
```typescript
property("all_facts_grounded_in_sources", () => {
  const query = generateRandomQuery();
  const chunks = retrieveChunks(query);
  const answer = generateAnswer(query, chunks);
  const claims = extractClaims(answer);
  
  return claims.every(claim => 
    chunks.some(chunk => semanticSimilarity(claim, chunk) > 0.8)
  );
});
```

### 15.2 Citation Completeness Property

**Property:** Every response with an answer must include at least one source citation

**Test Strategy:**
- Parse LLM response for citation markers
- Verify citation URLs are valid and accessible
- Ensure citations match retrieved chunks

**PBT Implementation:**
```typescript
property("all_answers_have_citations", () => {
  const query = generateRandomQuery();
  const response = processQuery(query);
  
  if (response.answer !== "I don't have that information") {
    return response.citations.length > 0 &&
           response.citations.every(c => isValidUrl(c.sourceUrl));
  }
  return true;
});
```

### 15.3 Publisher Isolation Property

**Property:** User queries must never return content from a different publisher

**Test Strategy:**
- Submit query with publisherId A
- Verify all returned chunks have publisherId A
- Verify no chunks from publisherId B appear

**PBT Implementation:**
```typescript
property("publisher_data_isolation", () => {
  const publisherId = generatePublisherId();
  const query = generateRandomQuery();
  const response = processQuery(query, publisherId);
  
  return response.citations.every(c => 
    getContentPublisherId(c.contentId) === publisherId
  );
});
```

### 15.4 Latency Property

**Property:** 95% of queries must complete within 3 seconds

**Test Strategy:**
- Generate 1000 random queries
- Measure end-to-end latency for each
- Calculate 95th percentile
- Assert p95 < 3000ms

**PBT Implementation:**
```typescript
property("query_latency_under_3s", () => {
  const queries = generateRandomQueries(1000);
  const latencies = queries.map(q => {
    const start = Date.now();
    processQuery(q);
    return Date.now() - start;
  });
  
  const p95 = percentile(latencies, 95);
  return p95 < 3000;
});
```

### 15.5 Personalization Consistency Property

**Property:** Recommended content must be relevant to user's interaction history

**Test Strategy:**
- Create user profile with known interaction history
- Request recommendations
- Verify recommendations match user's content type preferences
- Verify recommendations match user's language preference

**PBT Implementation:**
```typescript
property("personalization_matches_user_preferences", () => {
  const user = generateUserWithHistory();
  const recommendations = getRecommendations(user.userId);
  
  const preferredContentTypes = getMostFrequentContentTypes(user.history);
  const preferredLanguage = user.languagePreference;
  
  return recommendations.every(rec => 
    preferredContentTypes.includes(rec.contentType) &&
    rec.language === preferredLanguage
  );
});
```

## 16. Dependencies and Assumptions

### 16.1 External Dependencies

**AWS Services:**
- Amazon Bedrock (Claude 3 Sonnet, Titan Embeddings)
- Amazon Personalize
- Amazon Transcribe
- Amazon Rekognition
- Amazon Polly
- OpenSearch Service
- S3, DynamoDB, Lambda, API Gateway, EventBridge, Kinesis

**Third-Party Libraries:**
- React (frontend)
- AWS SDK v3 (backend)
- LangChain (RAG orchestration)
- tiktoken (token counting)

### 16.2 Assumptions

**Content Quality:**
- Publishers provide pre-moderated, appropriate content
- Content is in Hindi, English, or mix of both
- Content has sufficient text for meaningful embeddings (>100 words)

**User Behavior:**
- Users have stable internet connection (3G minimum)
- Users provide feedback on answer quality (for model improvement)
- Users consent to personalization and data collection

**AWS Service Availability:**
- Bedrock is available in deployment region (us-east-1 or ap-south-1)
- Personalize has sufficient quota for training
- OpenSearch cluster can scale to required size

### 16.3 Risks and Mitigations

**Risk:** Bedrock quota exhaustion during peak traffic  
**Mitigation:** Request quota increase, implement query throttling, cache popular queries

**Risk:** OpenSearch cluster overload  
**Mitigation:** Auto-scaling configuration, query optimization, read replicas

**Risk:** Poor personalization for new users (cold start)  
**Mitigation:** Content-based filtering fallback, popular content recommendations

**Risk:** Inaccurate transcription for low-quality audio  
**Mitigation:** Audio quality validation, manual transcription fallback, user-reported corrections

## 17. Success Criteria

### 17.1 Functional Success

- [ ] Content ingestion pipeline processes 100 assets without errors
- [ ] Query endpoint returns responses with citations for 100 test queries
- [ ] Personalization recommendations improve over time (A/B test)
- [ ] Voice input/output works for Hindi and English queries
- [ ] All AI-generated content is labeled per India IT Rules 2026

### 17.2 Performance Success

- [ ] Query latency <3s at 95th percentile (load test with 10K users)
- [ ] System handles 100K content assets without degradation
- [ ] Content ingestion completes within 5 minutes for 1-hour video
- [ ] OpenSearch query response time <500ms

### 17.3 Quality Success

- [ ] Query success rate >90% (user finds relevant answer)
- [ ] Answer relevance >85% (human evaluation)
- [ ] Hallucination rate <1% (grounded generation validation)
- [ ] Citation accuracy 100% (all citations valid and accessible)

### 17.4 Business Success

- [ ] Session length 3x increase vs traditional keyword search
- [ ] Content reuse rate >40% from archives
- [ ] User satisfaction score >4/5
- [ ] Cost per query <$0.10

## 18. Open Questions

1. **Multilingual Embeddings:** Should we use separate embedding models for Hindi and English, or a single multilingual model?
2. **Personalize Cold Start:** What's the minimum number of interactions before personalization becomes effective?
3. **Content Freshness:** How do we handle real-time content updates (e.g., breaking news)?
4. **Conversation Context:** Should we support multi-turn conversations with memory, or keep each query independent?
5. **Cost Optimization:** Can we reduce Bedrock costs by using smaller models for simple queries?
6. **Content Moderation:** Do we need additional content filtering beyond publisher pre-moderation?
7. **Accessibility:** What WCAG compliance level should we target for the chat interface?
8. **Internationalization:** Should we support additional languages beyond Hindi/English (e.g., Tamil, Telugu)?
