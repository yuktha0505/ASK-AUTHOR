# Tech Stack

## Architecture

**Frontend**: React (WhatsApp-style chat interface)  
**Backend**: AWS API Gateway + Lambda (serverless)  
**AI/ML Services**: Amazon Bedrock, Personalize, Transcribe, Rekognition  
**Storage**: S3, OpenSearch, DynamoDB  
**Streaming**: Kinesis Firehose

## AI Pipeline Components

### Content Ingestion
- **S3**: Raw content storage (articles/videos/podcasts)
- **Transcribe**: Auto-transcription for audio/video
- **Rekognition**: Auto-tagging and metadata extraction
- **Chunking**: 500-token segments for embedding generation
- **OpenSearch**: Vector embeddings storage for semantic search

### Query Processing
- **Bedrock LLM**: Claude/Titan for RAG-powered answer synthesis
- **OpenSearch**: Top-5 relevant chunk retrieval via vector similarity
- **Personalize**: Behavior-based ranking and recommendations
- **Polly**: Text-to-speech for voice responses

### Data Pipeline
- **Kinesis**: Query/click/watch-time event streaming
- **DynamoDB**: User profiles and interaction history
- **Personalize Dataset**: User behavior training data

## Common Commands

### Development
```bash
# Install dependencies
npm install

# Run local development
npm run dev

# Run tests
npm test
```

### Deployment
```bash
# Deploy backend infrastructure
aws cloudformation deploy --template-file template.yaml --stack-name ask-author

# Deploy Lambda functions
sam build && sam deploy

# Update OpenSearch index
npm run index:update
```

### AI Model Management
```bash
# Test Bedrock integration
npm run test:bedrock

# Retrain Personalize model
npm run personalize:train

# Update embeddings
npm run embeddings:generate
```

## Performance Requirements

- Query latency: <3 seconds (95th percentile)
- Real-time streaming responses
- Scale: 10K concurrent users, 100K content assets

## Compliance

- AI content labeling (India IT Rules 2026)
- GDPR/DPDP Act compliant data handling
- User data siloed per publisher (no cross-publisher training)
