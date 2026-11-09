import logging
import time
from collections import defaultdict, deque
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api import router
from app.config import settings
from app.database import Base, SessionLocal, engine
from app.seed import seed

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
app = FastAPI(title="PALS API", version="1.0.0", description="Adaptive DSA learning platform")
app.add_middleware(CORSMiddleware, allow_origins=settings.origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(router)
_requests: dict[str, deque[float]] = defaultdict(deque)

@app.middleware("http")
async def rate_limit(request: Request, call_next):
    if request.url.path.startswith("/api/"):
        key = request.client.host if request.client else "unknown"
        bucket = _requests[key]
        current = time.monotonic()
        while bucket and bucket[0] < current - 60: bucket.popleft()
        if len(bucket) >= 120:
            return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"}, headers={"Retry-After": "60"})
        bucket.append(current)
    return await call_next(request)

@app.on_event("startup")
def startup():
    Base.metadata.create_all(engine)
    with SessionLocal() as db: seed(db)

@app.exception_handler(Exception)
async def unhandled(request: Request, exc: Exception):
    logging.getLogger("pals").exception("Unhandled error on %s", request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})

@app.get("/health")
def health(): return {"status": "ok", "service": settings.app_name}
