# src/app.py
import uvicorn

from .order_service import app


def main():
    """Run the FastAPI server."""
    uvicorn.run(
        "src.order_service:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        workers=4,  # Multiple workers to expose threading issues
    )


if __name__ == "__main__":
    main()
