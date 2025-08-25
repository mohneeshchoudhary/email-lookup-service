# Email Lookup Service

A Python-based FastAPI service that retrieves user emails by checking multiple sources in order: **HuggingFace → GitHub → Blog**. The first valid email found is stored in persistent storage and returned via a REST API.

## 🎯 Features

- **Multi-source Email Lookup**: Checks HuggingFace, GitHub, and Blog URLs in sequence
- **Smart Email Extraction**: Filters out system emails and targets relevant HTML elements
- **Caching**: Redis-based caching with in-memory fallback (12-hour TTL)
- **Rate Limiting**: Configurable per-IP rate limiting (60 req/min default)
- **Persistence**: SQLite database storage with async SQLAlchemy
- **Observability**: Prometheus metrics and structured logging
- **Retry Logic**: Exponential backoff with tenacity
- **Docker Support**: Complete containerization with docker-compose

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Redis (optional, for distributed caching)

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/ramsakalle45/email-lookup-service.git
   cd email-lookup-service/email-lookup-service/email-lookup-service
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Start the service**
   ```bash
   uvicorn app.main:app --reload --port 8080
   ```

The service will be available at `http://localhost:8080`

### Docker Deployment

```bash
# Build and run with Docker Compose
docker compose up --build

# Or build and run manually
docker build -t email-lookup-service .
docker run -p 8080:8080 email-lookup-service
```

## 📋 API Endpoints

### 1. Email Lookup
**POST** `/lookup`

Main endpoint to trigger email lookup across all sources.

**Request Body:**
```json
{
  "username": "john_doe",
  "huggingface": "john_doe",       // optional; defaults to "username"
  "github": "john_doe",            // optional; defaults to "username"
  "blog_url": "https://blog.example.com",  // optional
  "force_refresh": false           // optional; bypass cache
}
```

**Response:**
```json
{
  "key": "abc123...",
  "email": "john@example.com",
  "source": "huggingface"
}
```

### 2. Retrieve Stored Email
**GET** `/emails/{key}`

Fetch a previously stored email record by its key.

**Response:**
```json
{
  "key": "abc123...",
  "email": "john@example.com",
  "source": "huggingface"
}
```

### 3. Health Check
**GET** `/health`

Service health status.

**Response:**
```json
{
  "status": "ok"
}
```

### 4. Metrics
**GET** `/metrics`

Prometheus metrics for monitoring.

## 🔧 Configuration

Create a `.env` file in the project root:

```env
# Application
APP_NAME=Email Lookup Service
APP_ENV=dev
LOG_LEVEL=INFO
PORT=8080
ALLOWED_ORIGINS=*

# Database
DATABASE_URL=sqlite+aiosqlite:///./data/app.db

# Redis (optional)
REDIS_URL=redis://localhost:6379

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
CACHE_TTL_SECONDS=43200  # 12 hours

# API Tokens (optional, for higher rate limits)
GITHUB_TOKEN=your_github_token
HUGGINGFACE_TOKEN=your_huggingface_token

# Prometheus
PROMETHEUS_ENABLED=true
```

## 🧪 Usage Examples

### Basic Lookup
```bash
curl -X POST "http://localhost:8080/lookup" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "github": "testuser"
  }'
```

### Lookup with Blog URL
```bash
curl -X POST "http://localhost:8080/lookup" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "xkcd",
    "blog_url": "https://xkcd.com/about/"
  }'
```

### Force Refresh (Bypass Cache)
```bash
curl -X POST "http://localhost:8080/lookup" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "force_refresh": true
  }'
```

### Retrieve Stored Email
```bash
curl -X GET "http://localhost:8080/emails/abc123..."
```

## 🏗️ Architecture

### Components

1. **Providers**: Platform-specific email extraction
   - `HuggingFaceProvider`: Scrapes HuggingFace profiles
   - `GitHubProvider`: Uses GitHub API + HTML fallback
   - `BlogProvider`: Scrapes blog URLs and RSS feeds

2. **Email Extraction**: Smart filtering and validation
   - System email blacklisting (`git@hf.co`, `noreply@`, etc.)
   - Targeted HTML element extraction
   - Email validation and normalization

3. **Caching**: Multi-layer caching strategy
   - Redis for distributed caching
   - In-memory fallback when Redis unavailable
   - Configurable TTL

4. **Storage**: Persistent data storage
   - SQLite database with async SQLAlchemy
   - Alembic migrations
   - Unique key generation

### Lookup Flow

```
1. Check cache for existing result
2. Check database for stored record
3. If not found or force_refresh=true:
   a. Try HuggingFace provider
   b. Try GitHub provider  
   c. Try Blog provider
4. Store result in database
5. Cache positive results
6. Return first valid email found
```

## 🔍 Email Extraction Strategy

### System Email Filtering
The service filters out common system emails:
- `git@hf.co`, `noreply@`, `support@`, `help@`
- `admin@`, `webmaster@`, `postmaster@`
- `github@noreply.github.com`, `notifications@github.com`

### Targeted HTML Elements
Focuses on relevant HTML sections:
- Profile, bio, description, contact sections
- Author information, about pages
- Footer and sidebar contact info

### Fallback Strategy
1. Target specific HTML elements first
2. Fall back to full page extraction
3. Validate and normalize all found emails

## 📊 Monitoring

### Health Checks
- **Liveness**: `GET /health`
- **Readiness**: Service startup checks

### Metrics
- **Prometheus**: `GET /metrics`
- **Custom metrics**: Request counts, cache hits, provider success rates

### Logging
- **Structured logging** with Loguru
- **Configurable log levels**
- **Request/response logging**

## 🛡️ Security & Rate Limiting

### Rate Limiting
- **Default**: 60 requests per minute per IP
- **Configurable** via `RATE_LIMIT_PER_MINUTE`
- **Redis-based** for distributed environments
- **In-memory fallback** when Redis unavailable

### CORS
- **Configurable origins** via `ALLOWED_ORIGINS`
- **Default**: Allow all origins (`*`)

## 🧪 Testing

### Manual Testing
```bash
# Test health endpoint
curl http://localhost:8080/health

# Test metrics endpoint
curl http://localhost:8080/metrics

# Test email lookup
curl -X POST "http://localhost:8080/lookup" \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser"}'
```

### Known Working Examples
- **Blog**: `https://xkcd.com/about/` → `contact@xkcd.com`
- **Blog**: `https://www.smashingmagazine.com/contact/` → `advertising@smashingmagazine.com`
- **HuggingFace**: `huggingface` → `press@huggingface.co`

## 📝 Development

### Project Structure
```
email-lookup-service/
├── app/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration settings
│   ├── cache.py             # Caching logic
│   ├── rate_limit.py        # Rate limiting
│   ├── db.py                # Database setup
│   ├── repositories.py      # Data access layer
│   └── services/
│       ├── extractor.py     # Email extraction logic
│       └── providers/       # Platform-specific providers
│           ├── huggingface.py
│           ├── github.py
│           └── blog.py
├── data/                    # SQLite database
├── tests/                   # Test files
├── requirements.txt         # Python dependencies
├── Dockerfile              # Docker configuration
├── docker-compose.yml      # Docker Compose setup
└── README.md               # This file
```

### Adding New Providers
1. Create a new provider class in `app/services/providers/`
2. Implement the `lookup()` method
3. Add the provider to the `PROVIDERS` list in `main.py`
4. Update tests and documentation

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For issues and questions:
- Create an issue on GitHub
- Check the documentation
- Review the test examples

---

**Built with ❤️ using FastAPI, SQLAlchemy, and Redis**
