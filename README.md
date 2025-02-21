# News Analyzer API

A FastAPI-based news analysis service with PostgreSQL storage and Redis caching.

## Features

- RESTful API for news analysis
- JWT Authentication
- PostgreSQL database integration
- Redis caching layer
- Dockerized development
- Automated database migrations
- PgAdmin for database administration

## Prerequisites

Ensure you have the following installed:

- **Docker** 20.10+
- **Docker Compose** 2.0+
- **Python** 3.11+ (for local development)

## Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/Adam-445/news-project.git
cd news-analyzer
```

### 2. Set Up Environment Variables
Copy the example `.env` file and update credentials:
```bash
cp .env.example .env
```

### 3. Build and Start Services
```bash
docker-compose up -d --build
```

### 4. Seed the Database
```bash
docker-compose exec app python /app/app/db/seed.py
```

### 5. Access Services
- **API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **PgAdmin**: [http://localhost:5050](http://localhost:5050)
- **Redis CLI**: `docker-compose exec redis redis-cli -a ${REDIS_PASSWORD}`

## Configuration

See [docs/configuration.md](docs/configuration.md) for details on environment variables and settings.

## Database Management

- **PgAdmin setup:** [docs/database.md](docs/database.md)
- **Running Migrations:** [docs/database.md](docs/database.md)

## Development Workflow

- The application code is auto-reloaded in development mode.
- Logs are stored in the `logs/` directory.

## Security Best Practices

See [docs/security.md](docs/security.md) for security recommendations.

## License

This project is licensed under the [MIT License](LICENSE).
```

### **Additional Documentation Files**
#### **docs/configuration.md**
Contains detailed environment variable descriptions.

#### **docs/database.md**
Describes database management, migrations, and PgAdmin setup.

#### **docs/security.md**
Covers best practices for securing the API.