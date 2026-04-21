from fastapi import APIRouter

from app.api.endpoints.ai_configs import router as ai_configs_router
from app.api.endpoints.admin_users import router as admin_users_router
from app.api.endpoints.admin_emails import router as admin_emails_router
from app.api.endpoints.auth import router as auth_router
from app.api.endpoints.health import router as health_router
from app.api.endpoints.practice import router as practice_router


api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(ai_configs_router)
api_router.include_router(admin_users_router)
api_router.include_router(admin_emails_router)
api_router.include_router(practice_router)
