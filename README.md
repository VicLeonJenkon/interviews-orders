# Dragonfly Live Debugging Exercise: Order Processing Service

You are given an order processing microservice that has two critical bugs affecting production reliability. Your task is to identify and fix these issues while discussing your debugging approach.

## System Overview

This is a FastAPI-based order processing service that:
- Accepts order requests via REST API
- Validates order amounts
- Deducts from customer account balances (via an external balance service)
- Tracks daily order statistics (revenue and order count)
- Supports both single orders and batch processing

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/orders` | POST | Process a single order |
| `/orders/batch` | POST | Process multiple orders |
| `/stats` | GET | Get daily statistics |
| `/balance/{customer_id}` | GET | Check customer balance |
| `/reset` | POST | Reset state (for testing) |

### Example Requests

```bash
# Create a single order
curl -X POST http://localhost:8000/orders \
  -H "Content-Type: application/json" \
  -d '{"id": 1, "customer_id": 1, "amount": 50.0, "priority": false}'

# Check customer balance
curl http://localhost:8000/balance/1

# Get statistics
curl http://localhost:8000/stats
```

## The Problem

Our QA team has reported intermittent issues in production:

1. **Statistics Discrepancy**: The daily revenue and order count in `/stats` sometimes shows lower numbers than expected. For example, processing 100 orders of $10 each sometimes reports only $800-900 in revenue instead of $1000.

2. **Customer Complaints**: Some customers report being charged twice for a single order, especially during periods of high load or network instability.

## Your Tasks

1. **Identify the bugs** — Review the code and explain the root cause of each issue.
2. **Propose fixes** — Describe how you would fix each bug.
3. **Implement the fixes** — Make the necessary code changes.
4. **Verify** — Ensure the tests pass after your fixes.

## Running the Project

### Using Docker (Recommended)

```bash
# Build and start the service
docker compose up --build

# In another terminal, run tests
docker compose run --rm app pytest -v

# Run type checking
docker compose run --rm app pyright
```

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Start the server
uvicorn src.order_service:app --host 0.0.0.0 --port 8000 --workers 4

# Run tests
pytest -v

# Run type checking
pyright
```

### Useful Test Commands

```bash
# Run all tests
pytest -v

# Run only concurrency tests (these expose the bugs)
pytest -v tests/test_api.py::TestConcurrency

# Run a specific test
pytest -v tests/test_api.py::TestConcurrency::test_concurrent_stats_update
```

## Session Guidelines

- We'll work through this together — feel free to think out loud and ask questions.
- You can use any debugging tools or techniques you normally would.
- Focus on understanding the issues before jumping to solutions.
- Consider both correctness and production-readiness in your fixes.

## Files of Interest

- `src/order_service.py` — Main FastAPI application and order processing logic
- `src/balance_service.py` — External customer balance service stub
- `tests/test_api.py` — Test suite including concurrency tests

Good luck!
