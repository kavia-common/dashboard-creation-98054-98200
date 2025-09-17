from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import APIRouter

from .config import get_settings
from .deps import openapi_tags
from .routers_auth import router as auth_router
from .routers_users import router as users_router
from .routers_reports import router as reports_router
from .routers_charts import router as charts_router

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESC,
    version=settings.APP_VERSION,
    openapi_tags=openapi_tags,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

health_router = APIRouter(tags=["Health"])

@health_router.get(
    "/",
    summary="Health Check",
    description="Service liveness endpoint.",
)
# PUBLIC_INTERFACE
def health_check():
    """Return service health status."""
    return {"message": "Healthy"}

@health_router.get(
    "/docs/auth",
    summary="Authentication usage help",
    description="How to authenticate: Obtain token via POST /auth/login and send 'Authorization: Bearer <token>' header.",
)
# PUBLIC_INTERFACE
def docs_auth_usage():
    """Provide help on using JWT authentication with this API."""
    return {
        "steps": [
            "POST /auth/login with JSON body {email, password}",
            "Receive access_token",
            "Use header Authorization: Bearer <access_token> for protected endpoints",
        ]
    }

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(reports_router)
app.include_router(charts_router)
