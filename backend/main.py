from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routes.auth import router as auth_router
from backend.routes.analyze import router as analyze_router

app = FastAPI(
    title="DeepLens AI Backend",
    description="Backend API for DeepLense-AI",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5000",      # Local development
        "http://127.0.0.1:5000",      # Local development (IP)
        "https://deeplens-ai-frontend.onrender.com"  # Production
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(analyze_router)


@app.get("/health")
def health():
    """Lightweight runtime info to confirm what is deployed and how it is configured."""
    try:
        from backend.services.notice_processor import _get_provider as notice_provider
    except Exception as e:
        notice_provider = None
        notice_provider_error = f"{e.__class__.__name__}: {e}"
    else:
        notice_provider_error = None

    return {
        "service": "fastapi",
        "notice_provider": notice_provider() if notice_provider else None,
        "notice_provider_error": notice_provider_error,
        "env": {
            "AI_PROVIDER": __import__("os").getenv("AI_PROVIDER"),
            "has_gemini": bool((__import__("os").getenv("GEMINI_API_KEY") or "").strip()),
            "has_azure_content": bool(
                (__import__("os").getenv("ENDPOINT") or "").strip()
                and (__import__("os").getenv("ANALYZER") or "").strip()
            ),
        },
    }


@app.get("/")
def home():
    return {
        "message": "DeepLens-AI Backend is running!"
    }