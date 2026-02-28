# Project Structure

## High-Level Organization

```
/frontend          # React chat interface
/backend           # Lambda functions and API handlers
/ai-pipeline       # Content ingestion and embedding generation
/infrastructure    # CloudFormation/SAM templates
/shared            # Common utilities and types
```

## Frontend Structure

```
/frontend
  /components      # React components (ChatInterface, MessageBubble, VoiceInput)
  /hooks           # Custom React hooks (useChat, useVoiceInput)
  /services        # API clients (chatService, searchService)
  /utils           # Helper functions (i18n, formatting)
```

## Backend Structure

```
/backend
  /api             # API Gateway handlers
    /query         # Query processing endpoint
    /feedback      # User feedback collection
  /rag             # RAG pipeline logic
    /retrieval     # OpenSearch vector search
    /generation    # Bedrock LLM integration
    /citation      # Source attribution logic
  /personalize     # Personalize integration
  /auth            # Authentication/authorization
```

## AI Pipeline Structure

```
/ai-pipeline
  /ingestion       # Content upload and preprocessing
    /transcribe    # Audio/video transcription
    /tag           # Rekognition tagging
    /chunk         # Content chunking (500-token segments)
  /embeddings      # Embedding generation and indexing
  /search          # OpenSearch index management
```

## Infrastructure Structure

```
/infrastructure
  /cloudformation  # IaC templates
  /lambda-layers   # Shared Lambda dependencies
  /policies        # IAM policies and roles
```

## Key Architectural Patterns

### RAG Pipeline
1. User query → Embedding generation
2. OpenSearch vector similarity search (Top-5 chunks)
3. Bedrock LLM synthesis with retrieved context
4. Source citation extraction (URLs + timestamps)
5. Follow-up question generation

### Content Ingestion Pipeline
1. Upload to S3 → Trigger Lambda
2. Transcribe/Rekognition processing
3. Chunking (500 tokens) + embedding generation
4. Index to OpenSearch with metadata

### Personalization Pipeline
1. User interactions → Kinesis stream
2. Firehose → DynamoDB + Personalize dataset
3. Real-time ranking of follow-up content
4. Context-aware response customization

## Data Flow

- **Content**: S3 → Lambda → OpenSearch (embeddings)
- **Queries**: API Gateway → Lambda → OpenSearch + Bedrock → Response
- **Events**: Frontend → Kinesis → DynamoDB + Personalize
- **Voice**: Transcribe (input) → Query Pipeline → Polly (output)

## Naming Conventions

- Lambda functions: `ask-author-{service}-{action}` (e.g., `ask-author-rag-query`)
- S3 buckets: `ask-author-{env}-{purpose}` (e.g., `ask-author-prod-content`)
- DynamoDB tables: `AskAuthor{Entity}` (e.g., `AskAuthorUserProfiles`)
- OpenSearch indices: `content-{type}-{version}` (e.g., `content-articles-v1`)
