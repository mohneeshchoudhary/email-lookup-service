from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import hashlib

from .config import settings
from .logging_config import setup_logging
from .db import init_db
from .repositories import EmailRepo
from .cache import cache_get, cache_set
from .rate_limit import init_rate_limiter, limiter_dep
from .metrics import setup_metrics

from .services.providers.huggingface import HuggingFaceProvider
from .services.providers.github import GitHubProvider
from .services.providers.blog import BlogProvider

logger = setup_logging(settings.LOG_LEVEL)
app = FastAPI(title=settings.APP_NAME)

# CORS
origins = [o.strip() for o in settings.ALLOWED_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Register Prometheus middleware BEFORE startup so it can add middleware/routes
if settings.PROMETHEUS_ENABLED:
    setup_metrics(app)

# Providers (ordered per PRD)
PROVIDERS = [
    HuggingFaceProvider(),
    GitHubProvider(),
    BlogProvider(),
]

class LookupRequest(BaseModel):
    username: str
    huggingface: Optional[str] = None
    github: Optional[str] = None
    blog_url: Optional[str] = None
    force_refresh: bool = False

class LookupResponse(BaseModel):
    key: str
    email: Optional[str]
    source: Optional[str]

def make_key(hf: str, gh: str, blog: Optional[str]) -> str:
    base = f"hf={hf}|gh={gh}|blog={blog or ''}"
    return hashlib.sha1(base.encode("utf-8")).hexdigest()

@app.on_event("startup")
async def on_startup():
    await init_db()
    await init_rate_limiter(app)
    logger.info("Service started: {}", settings.APP_NAME)

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/lookup", response_model=LookupResponse, dependencies=[Depends(limiter_dep())])
async def lookup(req: LookupRequest):
    hf = (req.huggingface or req.username).strip()
    gh = (req.github or req.username).strip()
    key = make_key(hf, gh, req.blog_url)

    if not req.force_refresh:
        # 1) Cache check
        cached = await cache_get(f"email:{key}")
        if cached:
            email, source = cached.split("|", 1)
            return LookupResponse(key=key, email=(email or None), source=(source or None))
        # 2) DB check
        rec = await EmailRepo.get_by_key(key)
        if rec and rec.email:
            # also put into cache
            await cache_set(f"email:{key}", f"{rec.email}|{rec.source or ''}", settings.CACHE_TTL_SECONDS)
            return LookupResponse(key=key, email=rec.email, source=rec.source)

    # Do lookups in order
    found_email = None
    found_source = None
    for provider in PROVIDERS:
        try:
            if provider.__class__.__name__.startswith("Blog") and not req.blog_url:
                continue
            email = await provider.lookup(
                username=req.username,
                blog_url=req.blog_url,
                huggingface=hf,
                github=gh,
            )
            if email:
                found_email = email
                found_source = provider.name
                break
        except Exception as e:
            logger.warning("Provider {} failed: {}", provider.__class__.__name__, e)

    # Persist (email may be None if nothing found)
    rec = await EmailRepo.upsert(key=key, email=found_email, source=found_source)
    # Cache positive results
    if rec.email:
        await cache_set(f"email:{key}", f"{rec.email}|{rec.source or ''}", settings.CACHE_TTL_SECONDS)

    return LookupResponse(key=key, email=rec.email, source=rec.source)

@app.get("/emails/{key}", response_model=LookupResponse, dependencies=[Depends(limiter_dep())])
async def get_email(key: str):
    rec = await EmailRepo.get_by_key(key)
    if not rec:
        raise HTTPException(status_code=404, detail="Not found")
    return LookupResponse(key=key, email=rec.email, source=rec.source)
