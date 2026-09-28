import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from .config import settings
from . import auth, cases, support, directories, analytics, portal

app = FastAPI(title='Badabee Support API', version='0.1.0', description='Modular monolith. All victim records require assignment or jurisdiction authorization. National access is aggregate-only.')
app.add_middleware(CORSMiddleware, allow_origins=settings().cors_origins,
                   allow_methods=['GET', 'POST', 'PATCH'], allow_headers=['Authorization', 'Content-Type', 'Idempotency-Key', 'X-Ingest-Key'])
for module in (auth, cases, support, directories, analytics, portal):
    app.include_router(module.router)


@app.middleware('http')
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers['Cache-Control'] = 'no-store'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    if response.status_code in (401, 403, 404) and request.url.path not in ('/favicon.ico',):
        # Separate transaction preserves denied-access audit entries after request rollback.
        from .db import SessionLocal
        from .models import AuditLog
        try:
            with SessionLocal.begin() as db:
                route = request.scope.get('route')
                db.add(AuditLog(actor_id=getattr(request.state, 'actor_id', None), action='ACCESS_DENIED',
                                resource_type='http', resource_id=getattr(route, 'path', None), outcome=str(response.status_code)))
        except Exception:
            logging.getLogger(__name__).error('Unable to persist denied-access audit entry')
    return response


@app.exception_handler(IntegrityError)
async def integrity_error(request: Request, exc: IntegrityError):
    return JSONResponse(status_code=409, content={'detail': 'Record conflicts with an existing record or reference'})


@app.exception_handler(Exception)
async def unexpected_error(request: Request, exc: Exception):
    logging.getLogger(__name__).error('Unhandled request failure: %s', type(exc).__name__)
    return JSONResponse(status_code=500, content={'detail': 'Unexpected server error'})


@app.get('/health', tags=['Operations'])
def health():
    return {'status': 'ok'}
