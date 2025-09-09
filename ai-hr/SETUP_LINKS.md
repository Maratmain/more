# AI-HR Setup Links & References

## Quick Setup Checklist

### 1. Environment Configuration
- [ ] Copy `.env.example` to `.env`
- [ ] Fill in required API keys
- [ ] Configure service URLs

### 2. Required Services

#### Telegram Bot
- **Bot Creation**: [@BotFather](https://t.me/BotFather)
- **Documentation**: [Telegram Bot API](https://core.telegram.org/bots/api)
- **File Limits**: [Bot API getFile](https://core.telegram.org/bots/api#getfile)
- **Local Bot API**: [Telegram Core](https://core.telegram.org/bots/api#using-a-local-bot-api-server)

#### OpenRouter (LLM)
- **Registration**: [OpenRouter](https://openrouter.ai/)
- **API Keys**: [OpenRouter Keys](https://openrouter.ai/keys)
- **Documentation**: [OpenRouter Docs](https://openrouter.ai/docs)
- **Models**: [Available Models](https://openrouter.ai/models)

#### Qdrant (Vector Database)
- **Cloud Signup**: [Qdrant Cloud](https://cloud.qdrant.io/)
- **Documentation**: [Qdrant Docs](https://qdrant.tech/documentation/)
- **Free Tier**: 1GB storage, ~1M vectors
- **Pricing**: [Qdrant Pricing](https://qdrant.tech/pricing/)

#### LiveKit (WebRTC)
- **Cloud**: [LiveKit Cloud](https://cloud.livekit.io/)
- **Documentation**: [LiveKit Docs](https://docs.livekit.io/)
- **Development**: [LiveKit Dev Mode](https://docs.livekit.io/realtime/server/development/)

## Service-Specific Documentation

### Core Services
- **Telegram Bot**: [`services/tg-bot/README.md`](services/tg-bot/README.md)
- **LLM Gateway**: [`services/llm-gw/README.md`](services/llm-gw/README.md)
- **Vector Service**: [`services/vector/README.md`](services/vector/README.md)
- **Token Server**: [`services/token-server/README.md`](services/token-server/README.md)

### AI Services
- **ASR Service**: [`services/asr/README.md`](services/asr/README.md)
- **TTS Service**: [`services/tts/README.md`](services/tts/README.md)
- **Dialog Manager**: [`services/dm/README.md`](services/dm/README.md)

### Processing Services
- **CV Processing**: [`services/cv/README.md`](services/cv/README.md)
- **Report Service**: [`services/report/README.md`](services/report/README.md)
- **Main API**: [`services/api/README.md`](services/api/README.md)

## Environment Variables Reference

### Required Variables
```bash
# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token

# OpenRouter
OPENROUTER_API_KEY=your_openrouter_key

# Qdrant
QDRANT_URL=https://your-cluster.qdrant.io:6333
QDRANT_API_KEY=your_qdrant_key

# LiveKit (development)
LIVEKIT_API_KEY=devkey
LIVEKIT_API_SECRET=secret
```

### Optional Variables
```bash
# LLM Model
LLM_MODEL=anthropic/claude-3.5-sonnet:beta

# File Limits
MAX_FILE_SIZE_MB=20

# Embedding Model
EMBEDDER_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

## Quick Commands

### Setup
```bash
# Clone and setup
git clone <repo-url>
cd ai-hr
cp .env.example .env
# Edit .env with your keys

# Start services
docker compose up -d
```

### Testing
```bash
# Check all services
docker compose ps

# Test CV upload
curl -F file=@test.pdf http://localhost:8007/ingest

# Test search
curl "http://localhost:8007/cvs/search?q=python&top_k=3"

# Run demo
python scripts/demo_e2e.py
```

### Monitoring
```bash
# View logs
docker compose logs -f

# Check health
curl http://localhost:8007/health
curl http://localhost:8005/health
curl http://localhost:8006/health
```

## Troubleshooting

### Common Issues
1. **Services not starting**: Check Docker and .env configuration
2. **API keys invalid**: Verify keys from respective services
3. **File upload fails**: Check file size limits and formats
4. **Search not working**: Verify Qdrant connection and collection

### Debug Commands
```bash
# Check service status
docker compose ps

# View specific service logs
docker logs ai-hr-cv-1 -f
docker logs ai-hr-tg-bot-1 -f

# Test API endpoints
curl http://localhost:8007/health
curl http://localhost:8005/health
```

## Support Resources

### Documentation
- **Main README**: [`README.md`](README.md)
- **Environment Setup**: [`.env.example`](.env.example)
- **Docker Compose**: [`docker-compose.yml`](docker-compose.yml)

### External Resources
- **Telegram Bot API**: [Core Documentation](https://core.telegram.org/bots/api)
- **OpenRouter**: [API Documentation](https://openrouter.ai/docs)
- **Qdrant**: [Cloud Documentation](https://qdrant.tech/documentation/cloud/)
- **LiveKit**: [Realtime Documentation](https://docs.livekit.io/realtime/)

### Community
- **Telegram**: [Bot API Support](https://t.me/BotSupport)
- **OpenRouter**: [Discord Community](https://discord.gg/openrouter)
- **Qdrant**: [GitHub Discussions](https://github.com/qdrant/qdrant/discussions)
- **LiveKit**: [Discord Community](https://discord.gg/livekit)
