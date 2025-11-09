# 🛠️ Development Guide

Development guide for Faceit AI Bot v0.2.2

**[Русская версия](DEVELOPMENT.md)**

## 📋 Requirements

- **Node.js**: 18.x or higher
- **Python**: 3.9 or higher
- **Docker**: 20.10+ (optional)
- **PostgreSQL**: 16+ (or via Docker)

## 🚀 Quick Start

### 1. Clone and Install

```bash
# Clone the repository
git clone https://github.com/pat1one/faceit-ai-bot.git
cd faceit-ai-bot

# Install Node.js dependencies
npm install

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Environment Setup

```bash
# Create .env file
cp .env.example .env

# Edit .env and set:
# - SECRET_KEY (minimum 32 characters)
# - DATABASE_URL
# - Payment API keys (optional)
```

### 3. Running

#### Via Docker (Recommended)

```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

Available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

#### Locally

```bash
# Terminal 1: Frontend
npm run dev

# Terminal 2: Backend
python main.py

# Terminal 3: Database (if not using Docker)
# Run PostgreSQL locally
```

## 📁 Project Structure

```text
faceit-ai-bot/
├── app/                    # Next.js 15 App Router
│   ├── layout.tsx         # Root layout
│   ├── page.tsx           # Home page
│   └── globals.css        # Global styles
├── src/
│   ├── components/        # React components
│   ├── config/           # Configuration (API endpoints)
│   ├── server/           # FastAPI backend
│   │   ├── features/     # Modular features
│   │   │   ├── demo_analyzer/
│   │   │   ├── payments/
│   │   │   ├── subscriptions/
│   │   │   └── teammates/
│   │   ├── models/       # Database models
│   │   ├── config/       # Settings
│   │   └── main.py       # FastAPI app
│   └── ai/              # AI/ML service
├── main.py              # Backend entry point
├── docker-compose.yml   # Docker orchestration
└── .env                # Environment variables
```

## 🔧 Main Commands

### NPM Scripts

```bash
# Development
npm run dev              # Run Next.js dev server
npm run build            # Production build
npm run start            # Production server

# Testing
npm run test             # Run tests
npm run type-check       # TypeScript check
npm run lint             # ESLint check

# Docker
npm run docker:build     # Build Docker images
npm run docker:up        # Start containers
npm run docker:down      # Stop containers
npm run docker:logs      # View logs
```

### Python Commands

```bash
# Testing
pytest tests/unit -v                    # Unit tests
pytest tests/integration -v             # Integration tests
pytest tests --cov=src/server          # With coverage

# Database migrations (when added)
alembic upgrade head                    # Apply migrations
alembic revision --autogenerate -m ""   # Create migration
```

## 🧪 Testing

### Frontend Tests

```bash
npm run test
```

### Backend Tests

```bash
# All tests
pytest tests -v

# With coverage
pytest tests --cov=src/server --cov-report=html

# Only unit tests
pytest tests/unit -v
```

## 📝 Code Style

### TypeScript/React

- **Strict mode** enabled
- **ESLint** for code checking
- **Prettier** for formatting
- Use **TypeScript** types everywhere

### Python

- **PEP 8** style guide
- **Type hints** required
- **Docstrings** for all public functions
- **Pydantic** for data validation

## 🔍 Debugging

### Frontend

```bash
# Next.js dev mode with detailed errors
npm run dev
```

### Backend

```bash
# FastAPI with auto-reload
uvicorn main:app --reload --log-level debug
```

### Docker

```bash
# Logs for specific service
docker-compose logs -f api
docker-compose logs -f web

# Enter container
docker-compose exec api bash
docker-compose exec web sh
```

## 🚢 Deployment

### Production Build

```bash
# Build all
npm run build:all

# Docker production
docker-compose -f docker-compose.prod.yml up -d
```

### Environment Variables

Required for production:

```env
NODE_ENV=production
SECRET_KEY=<strong-secret-key-min-32-chars>
DATABASE_URL=postgresql://user:password@host:5432/db
```

## 📚 API Documentation

Available after startup at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🤝 Contributing

1. Create a feature branch
2. Make changes
3. Write tests
4. Check linters: `npm run lint && npm run type-check`
5. Create a Pull Request

## 🐛 Troubleshooting

### Port already in use

```bash
# Find process on port 3000
lsof -i :3000
# Kill process
kill -9 <PID>
```

### Docker issues

```bash
# Rebuild without cache
docker-compose build --no-cache

# Clean everything
docker-compose down -v
docker system prune -a
```

### TypeScript errors

```bash
# Remove cache and rebuild
rm -rf .next node_modules
npm install
npm run build
```

## 📞 Support

- 📧 Email: support@pattmsc.online
- 💬 GitHub Issues: [Bug Tracker](https://github.com/pat1one/faceit-ai-bot/issues)
- 📖 Docs: [README.md](README.md)

---

Made with ❤️ for the CS2 community
