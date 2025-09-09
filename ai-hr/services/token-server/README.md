# Token Server Service

JWT token generation service for LiveKit authentication in the AI-HR system.

## Features

- **JWT Generation**: Create secure tokens for LiveKit sessions
- **Room Management**: Generate tokens for specific rooms
- **User Authentication**: Handle user identity and permissions
- **Token Validation**: Verify token integrity and expiration
- **LiveKit Integration**: Seamless integration with LiveKit server

## Configuration

### Environment Variables

```bash
# LiveKit Configuration
LIVEKIT_API_KEY=devkey
LIVEKIT_API_SECRET=secret
LIVEKIT_WS_URL=ws://livekit:7880

# JWT Configuration
JWT_SECRET=your_jwt_secret_here
JWT_EXPIRY_HOURS=24

# Development Settings
ENVIRONMENT=development
DEBUG=true
```

### LiveKit Setup

#### Development Mode

For development, LiveKit runs in `--dev` mode with default credentials:

```bash
# Default development credentials
LIVEKIT_API_KEY=devkey
LIVEKIT_API_SECRET=secret
LIVEKIT_WS_URL=ws://livekit:7880
```

**Reference**: [LiveKit Development Documentation](https://docs.livekit.io/realtime/server/development/)

#### Production Setup

For production, use proper API keys from LiveKit Cloud:

1. **Create Project**: Sign up at [LiveKit Cloud](https://cloud.livekit.io/)
2. **Get Credentials**: Copy API key and secret from dashboard
3. **Configure WebSocket URL**: Use your project's WebSocket endpoint

```bash
# Production credentials
LIVEKIT_API_KEY=your_production_api_key
LIVEKIT_API_SECRET=your_production_secret
LIVEKIT_WS_URL=wss://your-project.livekit.cloud
```

## API Usage

### Generate Room Token

```python
import requests

# Generate token for room access
response = requests.post("http://localhost:3001/token/room", json={
    "room_name": "interview_room_123",
    "participant_name": "candidate_john_doe",
    "participant_identity": "candidate_001",
    "permissions": {
        "can_publish": True,
        "can_subscribe": True,
        "can_publish_data": True
    }
})

token = response.json()["token"]
```

### Generate Join Token

```python
# Generate token for joining a room
response = requests.post("http://localhost:3001/token/join", json={
    "room_name": "interview_room_123",
    "participant_name": "Interviewer",
    "participant_identity": "interviewer_001",
    "permissions": {
        "can_publish": True,
        "can_subscribe": True,
        "can_publish_data": True,
        "can_update_metadata": True
    }
})
```

### Token Validation

```python
# Validate existing token
response = requests.post("http://localhost:3001/token/validate", json={
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
})

is_valid = response.json()["valid"]
```

## LiveKit Integration

### Room Configuration

```python
from livekit import api

# Create room
room = api.Room(
    name="interview_room_123",
    max_participants=10,
    metadata={
        "interview_type": "technical",
        "candidate_id": "candidate_001",
        "interviewer_id": "interviewer_001"
    }
)
```

### Participant Permissions

```python
# Define participant permissions
permissions = {
    "can_publish": True,           # Can publish audio/video
    "can_subscribe": True,         # Can subscribe to others
    "can_publish_data": True,      # Can send data messages
    "can_update_metadata": True,   # Can update room metadata
    "can_create_room": False,      # Cannot create new rooms
    "can_join_room": True          # Can join existing rooms
}
```

### Token Claims

```python
# JWT claims for LiveKit
claims = {
    "iss": LIVEKIT_API_KEY,
    "sub": participant_identity,
    "name": participant_name,
    "video": {
        "room": room_name,
        "roomJoin": True,
        "canPublish": True,
        "canSubscribe": True,
        "canPublishData": True
    },
    "exp": int(time.time()) + 3600  # 1 hour expiry
}
```

## Service Architecture

### Token Generation Flow

```
Client Request → Token Server → JWT Generation → LiveKit Validation → Client Response
```

### Authentication Process

1. **Client Request**: Send room and participant details
2. **Token Generation**: Create JWT with LiveKit claims
3. **Token Signing**: Sign with LiveKit API secret
4. **Client Response**: Return signed token
5. **LiveKit Connection**: Client uses token to connect

## Development

### Local Development

```bash
# Install dependencies
npm install

# Set environment variables
export LIVEKIT_API_KEY=devkey
export LIVEKIT_API_SECRET=secret
export LIVEKIT_WS_URL=ws://localhost:7880

# Run service
npm start
```

### LiveKit Server Setup

```bash
# Run LiveKit in development mode
docker run -p 7880:7880 livekit/livekit-server:latest \
  --dev \
  --bind 0.0.0.0

# Or with Docker Compose
docker compose up livekit
```

### Testing

```bash
# Test token generation
curl -X POST "http://localhost:3001/token/room" \
  -H "Content-Type: application/json" \
  -d '{
    "room_name": "test_room",
    "participant_name": "test_user",
    "participant_identity": "test_001"
  }'

# Test token validation
curl -X POST "http://localhost:3001/token/validate" \
  -H "Content-Type: application/json" \
  -d '{"token": "your_token_here"}'

# Check health
curl "http://localhost:3001/health"
```

## Security

### JWT Security

- **Secret Management**: Secure storage of API secrets
- **Token Expiry**: Short-lived tokens (1-24 hours)
- **Signature Validation**: Verify token integrity
- **Claims Validation**: Validate all token claims

### LiveKit Security

- **API Key Protection**: Never expose API keys to clients
- **Room Isolation**: Separate rooms for different interviews
- **Participant Identity**: Unique identity for each participant
- **Permission Control**: Granular permission management

## Monitoring

### Metrics

- **Token Generation**: Tokens created per minute
- **Token Validation**: Validation success rate
- **Error Rate**: Failed token operations
- **Response Time**: Token generation latency
- **Active Rooms**: Number of active interview rooms

### Health Checks

```bash
# Service health
GET /health

# LiveKit connection status
GET /livekit/status

# Token statistics
GET /stats
```

## Troubleshooting

### Common Issues

1. **Token Generation Failed**:
   - Check LiveKit API credentials
   - Verify JWT secret configuration
   - Check service connectivity

2. **LiveKit Connection Failed**:
   - Verify WebSocket URL
   - Check network connectivity
   - Ensure LiveKit server is running

3. **Token Validation Failed**:
   - Check token expiration
   - Verify token signature
   - Ensure proper claims structure

4. **Room Access Denied**:
   - Check participant permissions
   - Verify room name format
   - Ensure proper identity claims

### Debug Mode

```bash
# Enable debug logging
DEBUG=true
LOG_LEVEL=debug

# View service logs
docker logs ai-hr-token-server-1 -f

# Check LiveKit logs
docker logs livekit -f
```

### Token Debugging

```python
# Decode JWT token (for debugging)
import jwt

token = "your_jwt_token"
decoded = jwt.decode(token, options={"verify_signature": False})
print(decoded)
```

## Production Considerations

### Scaling

- **Load Balancing**: Multiple token server instances
- **Caching**: Cache frequently used tokens
- **Rate Limiting**: Prevent token abuse
- **Monitoring**: Comprehensive logging and metrics

### Security

- **HTTPS**: Use HTTPS for all communications
- **API Key Rotation**: Regular key rotation
- **Audit Logging**: Log all token operations
- **Access Control**: Implement proper authentication

### Performance

- **Token Caching**: Cache valid tokens
- **Connection Pooling**: Reuse LiveKit connections
- **Async Processing**: Handle multiple requests concurrently
- **Resource Limits**: Set appropriate memory and CPU limits
