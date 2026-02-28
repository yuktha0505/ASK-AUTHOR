# Ask Author / Ask Channel - Requirements Document

## 1. Overview

Ask Author/Ask Channel is an AI-powered content discovery platform that transforms passive multimedia archives (articles, videos, podcasts) into interactive knowledge bases. Users can query content through natural language conversations in Hindi, English, or transliteration, receiving synthesized answers with source citations.

## 2. User Stories

### 2.1 Content Discovery
**As a** content consumer  
**I want to** ask questions about topics in my preferred language (Hindi/English/transliteration)  
**So that** I can quickly find relevant information across articles, videos, and podcasts without manual searching

### 2.2 Contextual Answers
**As a** user seeking information  
**I want to** receive synthesized answers with source citations and timestamps  
**So that** I can verify the information and dive deeper into specific content

### 2.3 Personalized Experience
**As a** returning user  
**I want to** receive content recommendations based on my viewing history and preferences  
**So that** I discover relevant content tailored to my interests

### 2.4 Voice Interaction
**As a** mobile user  
**I want to** use voice input and receive audio responses  
**So that** I can interact with the platform hands-free

### 2.5 Content Publishing
**As a** content publisher  
**I want to** upload multimedia content that becomes automatically searchable  
**So that** my audience can discover and engage with my content library

## 3. Functional Requirements

### FR-1: Content Ingestion Pipeline
**Priority:** High  
**Description:** Automated pipeline to process and index multimedia content

#### Acceptance Criteria:
- 1.1 System accepts uploads of articles (text), videos (MP4/MOV), and podcasts (MP3/WAV) to S3
- 1.2 Audio/video content is automatically transcribed using AWS Transcribe with >95% accuracy
- 1.3 Visual content is tagged using AWS Rekognition for metadata extraction
- 1.4 Content is chunked into 500-token segments with overlap for context preservation
- 1.5 Each chunk generates vector embeddings and is indexed in OpenSearch
- 1.6 Metadata includes source URL, timestamps, content type, and publisher ID
- 1.7 Processing completes within 5 minutes for content up to 1 hour duration

### FR-2: Multilingual Semantic Search
**Priority:** High  
**Description:** Vector-based search supporting multiple languages and query formats

#### Acceptance Criteria:
- 2.1 System accepts queries in Hindi (Devanagari), English, and transliteration (Hinglish)
- 2.2 Query is converted to vector embedding using the same model as content chunks
- 2.3 OpenSearch returns Top-5 most relevant content chunks via cosine similarity
- 2.4 Results include video timestamps, article sections, and podcast chapter markers
- 2.5 Semantic understanding handles synonyms and contextual meaning (e.g., "GST repo rate" matches "goods and services tax repository rate")
- 2.6 Search latency is <500ms for vector similarity computation

### FR-3: RAG-Powered Q&A Generation
**Priority:** High  
**Description:** LLM-based answer synthesis grounded in retrieved content

#### Acceptance Criteria:
- 3.1 System uses Amazon Bedrock (Claude or Titan) to synthesize answers from Top-5 retrieved chunks
- 3.2 Generated answer is grounded exclusively in retrieved content (no hallucinations)
- 3.3 Every answer includes source citations with URLs and timestamps
- 3.4 System generates 2-3 contextually relevant follow-up questions
- 3.5 Responses are formatted for chat interface with proper markdown/formatting
- 3.6 Answer generation completes within 2 seconds after retrieval
- 3.7 System handles "no relevant content found" scenarios gracefully

### FR-4: Behavior-Based Personalization
**Priority:** Medium  
**Description:** User behavior tracking and personalized content ranking

#### Acceptance Criteria:
- 4.1 System logs user queries, clicks, and watch-time to Kinesis stream
- 4.2 Events are processed and stored in DynamoDB user profiles
- 4.3 Data feeds into Amazon Personalize dataset for model training
- 4.4 Follow-up content cards are ranked by user history + content similarity
- 4.5 System provides context-aware responses (e.g., "You prefer Hindi explainers")
- 4.6 User data is siloed per publisher (no cross-publisher training)
- 4.7 Personalization improves over time with minimum 10 interactions

### FR-5: WhatsApp-Style Chat UX
**Priority:** High  
**Description:** Real-time conversational interface with voice support

#### Acceptance Criteria:
- 5.1 Chat interface displays messages in WhatsApp-style bubbles (user right, AI left)
- 5.2 Responses stream in real-time with <3 second latency (95th percentile)
- 5.3 Voice input is transcribed using AWS Transcribe and processed as text query
- 5.4 Text responses are converted to audio using AWS Polly for voice output
- 5.5 All AI-generated content is labeled "AI-Synthesized" per India IT Rules 2026
- 5.6 Interface supports message history and conversation context
- 5.7 Loading states and error messages are user-friendly

## 4. Non-Functional Requirements

### NFR-1: Performance
**Priority:** High

#### Acceptance Criteria:
- 1.1 End-to-end query latency <3 seconds at 95th percentile
- 1.2 System supports 10,000 concurrent users without degradation
- 1.3 Content library scales to 100,000 assets (articles/videos/podcasts)
- 1.4 OpenSearch query response time <500ms
- 1.5 API Gateway + Lambda cold start <1 second
- 1.6 Real-time streaming responses with <100ms chunk delivery

### NFR-2: Responsible AI
**Priority:** High

#### Acceptance Criteria:
- 2.1 All answers are grounded in retrieved content (RAG prevents hallucinations)
- 2.2 Source attribution is mandatory for every response
- 2.3 User data is siloed per publisher (no cross-publisher model training)
- 2.4 System logs all AI interactions for audit trails
- 2.5 Content filtering prevents inappropriate or harmful responses
- 2.6 Bias monitoring and mitigation for multilingual content

### NFR-3: Compliance
**Priority:** High

#### Acceptance Criteria:
- 3.1 AI-generated content labeled per India IT Rules 2026
- 3.2 GDPR-compliant data handling (right to deletion, data portability)
- 3.3 DPDP Act (India) compliant user consent and data storage
- 3.4 User data encrypted at rest (S3, DynamoDB) and in transit (TLS 1.3)
- 3.5 Access logs retained for 90 days for compliance audits
- 3.6 Publisher data isolation enforced at infrastructure level

### NFR-4: Scalability
**Priority:** Medium

#### Acceptance Criteria:
- 4.1 Serverless architecture (Lambda) auto-scales with demand
- 4.2 OpenSearch cluster scales horizontally for increased load
- 4.3 S3 storage handles unlimited content growth
- 4.4 Kinesis stream handles 10,000 events/second
- 4.5 DynamoDB auto-scales read/write capacity

### NFR-5: Reliability
**Priority:** High

#### Acceptance Criteria:
- 5.1 System uptime >99.9% (excluding planned maintenance)
- 5.2 Graceful degradation when AI services are unavailable
- 5.3 Automatic retry logic for transient failures
- 5.4 Dead letter queues for failed event processing
- 5.5 Health checks and monitoring for all critical services

## 5. Technical Constraints

### 5.1 Technology Stack
- Frontend: React (WhatsApp-style chat interface)
- Backend: AWS API Gateway + Lambda (serverless)
- AI/ML: Amazon Bedrock, Personalize, Transcribe, Rekognition
- Storage: S3, OpenSearch, DynamoDB
- Streaming: Kinesis Firehose

### 5.2 AI Model Requirements
- Embedding model: Consistent across ingestion and query (e.g., Amazon Titan Embeddings)
- LLM: Amazon Bedrock (Claude 3 or Titan) for answer synthesis
- Chunk size: 500 tokens with 50-token overlap
- Vector dimensions: 1536 (standard for Titan Embeddings)

### 5.3 Data Requirements
- Content formats: MP4/MOV (video), MP3/WAV (audio), TXT/HTML (articles)
- Supported languages: Hindi (Devanagari), English, Hinglish (transliteration)
- Minimum content length: 100 words/1 minute for meaningful indexing

## 6. Success Metrics

### 6.1 User Engagement
- Query success rate: >90% (user finds relevant answer)
- Session length: 3x increase vs traditional keyword search
- Content reuse rate: >40% from archives (previously undiscovered content)

### 6.2 Performance
- Query latency: <3 seconds (95th percentile)
- System availability: >99.9%
- Concurrent users: 10,000 without degradation

### 6.3 AI Quality
- Answer relevance: >85% user satisfaction rating
- Source citation accuracy: 100% (all citations valid)
- Hallucination rate: <1% (grounded generation via RAG)

## 7. Out of Scope

### 7.1 Excluded Features
- Real-time live streaming content (only pre-recorded content)
- User-generated content moderation (assumes pre-moderated publisher content)
- Multi-turn conversation memory beyond current session
- Content creation or editing tools
- Social features (sharing, comments, likes)

### 7.2 Future Considerations
- Multi-modal responses (image/video generation)
- Advanced conversation memory across sessions
- Collaborative filtering for cold-start users
- Content recommendation widgets for publisher websites

## 8. Assumptions and Dependencies

### 8.1 Assumptions
- Publishers provide pre-moderated, appropriate content
- Users have stable internet connection (3G minimum)
- Content is in Hindi, English, or mix of both
- AWS services (Bedrock, Personalize) are available in deployment region

### 8.2 Dependencies
- AWS account with Bedrock access enabled
- OpenSearch cluster provisioned and configured
- Content publishers onboarded with S3 upload credentials
- Embedding model trained/selected before ingestion begins

## 9. Risks and Mitigations

### 9.1 AI Quality Risks
**Risk:** LLM generates inaccurate or hallucinated answers  
**Mitigation:** RAG architecture grounds all answers in retrieved content; mandatory source citations

### 9.2 Performance Risks
**Risk:** Query latency exceeds 3-second target under load  
**Mitigation:** Caching layer for frequent queries; OpenSearch optimization; Lambda concurrency limits

### 9.3 Compliance Risks
**Risk:** Non-compliance with India IT Rules 2026 or DPDP Act  
**Mitigation:** Legal review of AI labeling; data isolation architecture; audit logging

### 9.4 Cost Risks
**Risk:** Bedrock/Personalize costs exceed budget at scale  
**Mitigation:** Query throttling; caching; cost monitoring alerts; tiered pricing model

## 10. Glossary

- **RAG (Retrieval-Augmented Generation):** AI technique combining vector search with LLM generation to ground answers in actual content
- **Embedding:** Vector representation of text enabling semantic similarity search
- **Chunking:** Splitting content into smaller segments (500 tokens) for precise retrieval
- **Hinglish:** Transliteration of Hindi using Latin script (e.g., "kya haal hai")
- **Vector Similarity:** Mathematical measure of semantic closeness between embeddings
- **Grounded Generation:** LLM responses constrained to retrieved content (prevents hallucinations)
