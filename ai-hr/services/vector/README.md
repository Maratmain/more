# Vector Service

Vector database service using Qdrant for storing and searching CV embeddings in the AI-HR system.

## Features

- **Vector Storage**: Store CV embeddings with metadata
- **Semantic Search**: Find similar CVs using vector similarity
- **Metadata Filtering**: Filter results by CV attributes
- **Scalable**: Handle large volumes of CV data
- **Cloud Integration**: Support for Qdrant Cloud

## Configuration

### Environment Variables

```bash
# Qdrant Configuration
QDRANT_URL=https://your-cluster-id.eu-central-1.aws.cloud.qdrant.io:6333
QDRANT_API_KEY=your_qdrant_api_key
QDRANT_COLLECTION=cv_chunks

# Embedding Model
EMBEDDER_MODEL=sentence-transformers/all-MiniLM-L6-v2
CHUNK_SIZE=800
CHUNK_OVERLAP=100
```

### Qdrant Cloud Setup

1. **Create Account**: Sign up at [Qdrant Cloud](https://cloud.qdrant.io/)
2. **Create Cluster**: Choose region and configuration
3. **Get Credentials**: Copy cluster URL and API key
4. **Configure Collection**: Set up collection for CV chunks

#### Qdrant Cloud Free Tier

- **Storage**: 1 GB free
- **Capacity**: ~1 million vectors (768 dimensions)
- **Perfect for**: Prototype and development
- **Upgrade**: Available for production use

**Reference**: [Qdrant Cloud Documentation](https://qdrant.tech/documentation/cloud/)

## Collection Schema

### CV Chunks Collection

```python
collection_config = {
    "vectors": {
        "size": 384,  # all-MiniLM-L6-v2 embedding size
        "distance": "Cosine"
    },
    "payload_schema": {
        "cv_id": "string",
        "filename": "string", 
        "chunk_index": "integer",
        "chunk_text": "string",
        "text_length": "integer",
        "uploaded_at": "string",
        "file_type": "string",
        "candidate_name": "string"
    }
}
```

### Vector Dimensions

| Model | Dimensions | Speed | Quality | Use Case |
|-------|------------|-------|---------|----------|
| `all-MiniLM-L6-v2` | 384 | Fast | Good | Development |
| `all-mpnet-base-v2` | 768 | Medium | Better | Production |
| `all-MiniLM-L12-v2` | 384 | Medium | Better | Balanced |

## API Usage

### Create Collection

```python
from qdrant_client import QdrantClient

client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY
)

# Create collection
client.create_collection(
    collection_name=QDRANT_COLLECTION,
    vectors_config=models.VectorParams(
        size=384,
        distance=models.Distance.COSINE
    )
)
```

### Insert Vectors

```python
# Insert CV chunks
points = [
    models.PointStruct(
        id=str(uuid.uuid4()),
        vector=embedding.tolist(),
        payload={
            "cv_id": cv_id,
            "filename": filename,
            "chunk_index": i,
            "chunk_text": chunk_text,
            "uploaded_at": datetime.now().isoformat()
        }
    )
    for i, (chunk_text, embedding) in enumerate(zip(chunks, embeddings))
]

client.upsert(
    collection_name=QDRANT_COLLECTION,
    points=points
)
```

### Search Vectors

```python
# Semantic search
search_results = client.search(
    collection_name=QDRANT_COLLECTION,
    query_vector=query_embedding,
    limit=10,
    score_threshold=0.7
)

# Filtered search
search_results = client.search(
    collection_name=QDRANT_COLLECTION,
    query_vector=query_embedding,
    query_filter=models.Filter(
        must=[
            models.FieldCondition(
                key="file_type",
                match=models.MatchValue(value="pdf")
            )
        ]
    ),
    limit=5
)
```

## Service Integration

### CV Processing Pipeline

```python
async def process_cv(file_content: bytes, filename: str) -> str:
    # 1. Extract text
    text = extract_text_from_file(file_content, filename)
    
    # 2. Split into chunks
    chunks = chunk_text(text, CHUNK_SIZE, CHUNK_OVERLAP)
    
    # 3. Generate embeddings
    embeddings = embedder.encode(chunks)
    
    # 4. Store in Qdrant
    cv_id = str(uuid.uuid4())
    store_vectors(cv_id, filename, chunks, embeddings)
    
    return cv_id
```

### Search Interface

```python
async def search_cvs(query: str, limit: int = 5) -> List[SearchResult]:
    # 1. Generate query embedding
    query_embedding = embedder.encode([query])[0]
    
    # 2. Search in Qdrant
    results = client.search(
        collection_name=QDRANT_COLLECTION,
        query_vector=query_embedding.tolist(),
        limit=limit
    )
    
    # 3. Format results
    return [
        SearchResult(
            cv_id=result.payload["cv_id"],
            filename=result.payload["filename"],
            chunk_text=result.payload["chunk_text"],
            score=result.score
        )
        for result in results
    ]
```

## Development

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export QDRANT_URL=http://localhost:6333
export QDRANT_API_KEY=your_key

# Run service
uvicorn main:app --port 8009
```

### Local Qdrant (Docker)

```bash
# Run local Qdrant instance
docker run -p 6333:6333 qdrant/qdrant:latest

# Or with Docker Compose
docker compose up qdrant
```

### Testing

```bash
# Test vector operations
curl -X POST "http://localhost:8009/vectors/insert" \
  -H "Content-Type: application/json" \
  -d '{"cv_id": "test", "chunks": ["test chunk"]}'

# Test search
curl -X POST "http://localhost:8009/vectors/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "python developer", "limit": 5}'

# Check health
curl "http://localhost:8009/health"
```

## Performance Optimization

### Embedding Model Selection

```python
# Fast model for development
EMBEDDER_MODEL = "sentence-transformers/all-MiniLM-L6-v2"  # 384d, ~80MB

# Better quality for production
EMBEDDER_MODEL = "sentence-transformers/all-mpnet-base-v2"  # 768d, ~420MB
```

### Chunking Strategy

```python
# Optimal chunk size for CVs
CHUNK_SIZE = 800      # Characters per chunk
CHUNK_OVERLAP = 100   # Overlap between chunks

# Benefits:
# - Captures complete sentences
# - Maintains context across chunks
# - Balances search precision and recall
```

### Indexing Optimization

```python
# Create HNSW index for faster search
client.update_collection(
    collection_name=QDRANT_COLLECTION,
    hnsw_config=models.HnswConfigDiff(
        m=16,           # Number of bi-directional links
        ef_construct=100 # Size of dynamic candidate list
    )
)
```

## Monitoring

### Metrics

- **Collection Size**: Number of vectors stored
- **Search Performance**: Query latency and throughput
- **Memory Usage**: RAM consumption by embeddings
- **Storage Usage**: Disk space used by vectors
- **Error Rate**: Failed operations percentage

### Health Checks

```bash
# Service health
GET /health

# Collection status
GET /collections/status

# Storage usage
GET /collections/stats
```

## Troubleshooting

### Common Issues

1. **Connection Failed**:
   - Check Qdrant URL and port
   - Verify API key validity
   - Test network connectivity

2. **Collection Not Found**:
   - Ensure collection exists
   - Check collection name spelling
   - Verify API permissions

3. **Embedding Dimension Mismatch**:
   - Match model dimensions with collection
   - Recreate collection if needed
   - Check embedding model configuration

4. **Search Results Poor**:
   - Adjust score threshold
   - Try different embedding model
   - Optimize chunking strategy

### Debug Mode

```bash
# Enable debug logging
DEBUG=true
LOG_LEVEL=DEBUG

# View Qdrant logs
docker logs qdrant -f
```

### Performance Issues

1. **Slow Search**:
   - Optimize HNSW parameters
   - Use smaller embedding models
   - Implement result caching

2. **High Memory Usage**:
   - Use quantized models
   - Implement batch processing
   - Consider model offloading

3. **Storage Growth**:
   - Implement data retention policies
   - Use compression for payloads
   - Monitor collection size

## Security

- **API Key Management**: Secure storage and rotation
- **Network Security**: Use HTTPS for cloud connections
- **Access Control**: Implement proper authentication
- **Data Privacy**: Encrypt sensitive CV data
- **Audit Logging**: Track all vector operations

## Cost Management

### Qdrant Cloud Pricing

- **Free Tier**: 1GB storage, 1M vectors
- **Paid Plans**: Based on storage and compute
- **Optimization**: Use efficient embedding models

### Cost Optimization

```python
# Use smaller models for development
EMBEDDER_MODEL = "all-MiniLM-L6-v2"  # 384d vs 768d

# Implement caching
CACHE_SEARCH_RESULTS = True
CACHE_TTL = 3600  # 1 hour

# Batch operations
BATCH_SIZE = 100  # Process multiple vectors together
```
