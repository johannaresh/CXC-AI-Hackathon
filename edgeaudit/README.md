# EdgeAudit

AI-powered quantitative strategy auditing platform. EdgeAudit analyzes trading strategies for overfitting risk, regime sensitivity, and statistical robustness using ensemble ML models, Monte Carlo simulations, and LLM-generated narrative reports.

## Architecture

```
Client (Backboard.io) ──REST API──▶ FastAPI Backend ──▶ ML Models + Snowflake + Gemini
```

- **Backend**: FastAPI serving audit endpoints
- **ML Models**: PyTorch strategy encoder, XGBoost overfit classifier, scikit-learn regime model (`backend/app/models/`)
- **Data Layer**: Snowflake for historical market data and strategy metadata
- **LLM**: Gemini API for generating human-readable audit narratives
- **Frontend**: Backboard.io connects via the REST API (`/audit`, `/health`)

## Quick Start

### 1. Install dependencies

```bash
cd edgeaudit
pip install -r backend/requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Fill in your Snowflake credentials, Gemini API key, etc.
```

### 3. Run the backend

```bash
uvicorn backend.app.main:app --reload
```

### 4. Verify

```bash
curl http://localhost:8000/health
# → {"status": "ok"}
```

## API Endpoints

| Method | Path    | Description                              |
|--------|---------|------------------------------------------|
| GET    | /health | Health check                             |
| POST   | /audit  | Submit a strategy payload for auditing   |

## Backboard.io Integration

Backboard connects to EdgeAudit as an external REST API consumer. Point your Backboard data source to `http://<host>:8000` and configure the `/audit` endpoint as a POST action with a JSON strategy payload.

## Project Structure

```
edgeaudit/
├── backend/          # FastAPI app, ML models, services
├── data/             # raw / processed / synthetic datasets
├── notebooks/        # Exploration and prototyping
├── scripts/          # Data seeding and utilities
├── .env.example      # Environment variable template
└── pyproject.toml    # Project metadata
```

## Testing

```bash
pytest backend/tests/
```
