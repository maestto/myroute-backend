"""API v1 router."""

from fastapi import APIRouter

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.invites import router as invites_router
from app.api.v1.endpoints.trips import router as trips_router
from app.api.v1.endpoints.users import router as users_router

router = APIRouter()
router.include_router(health_router, tags=["health"])
router.include_router(auth_router, tags=["auth"])
router.include_router(users_router, tags=["users"])
router.include_router(trips_router, tags=["trips"])
router.include_router(invites_router, tags=["invites"])
