"""
Main API router that includes all endpoint routers.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, users, tenants, matters, transcripts, media, exports

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(tenants.router, prefix="/tenants", tags=["Tenants"])
api_router.include_router(matters.router, prefix="/matters", tags=["Matters"])
api_router.include_router(transcripts.router, prefix="/transcripts", tags=["Transcripts"])
api_router.include_router(media.router, prefix="/media", tags=["Media"])
api_router.include_router(exports.router, prefix="/exports", tags=["Exports"])