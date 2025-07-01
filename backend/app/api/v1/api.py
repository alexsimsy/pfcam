from fastapi import APIRouter
from app.api.v1.endpoints import auth, events, cameras, settings, streams, users

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(events.router, prefix="/events", tags=["events"])
api_router.include_router(cameras.router, prefix="/cameras", tags=["cameras"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])
api_router.include_router(streams.router, prefix="/streams", tags=["streams"])
api_router.include_router(users.router, prefix="/users", tags=["users"]) 