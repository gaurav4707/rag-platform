import truststore
truststore.inject_into_ssl()

from contextlib import asynccontextmanager
from typing import cast
from fastapi import FastAPI, HTTPException
from starlette.types import ExceptionHandler
from api.chat import router as chat_router
from api.health import router as health_router
from api.upload import router as upload_router
from api.documents import router as documents_router
from api.errors import AppError, app_error_handler, http_error_handler
from rag.vector_store import _get_collection
from fastapi.middleware.cors import CORSMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    _get_collection()
    yield


app = FastAPI(title="RAG Platform", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(AppError, cast(ExceptionHandler, app_error_handler))
app.add_exception_handler(HTTPException, cast(ExceptionHandler, http_error_handler))

app.include_router(chat_router)
app.include_router(health_router)
app.include_router(upload_router)
app.include_router(documents_router)
