import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add the root directory to path to support digital_twin imports
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from app.api.endpoints import api_router

def create_app() -> FastAPI:

    app = FastAPI(
        title="ICU Wearable Twin API",
        description="Phase 9 Refactored FastAPI Service",
        version="2.0.0"
    )

    # Allow CORS for Next.js frontend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router)

    return app

app = create_app()
