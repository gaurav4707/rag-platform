import truststore
truststore.inject_into_ssl()

from contextlib import asynccontextmanager
from fastapi import FastAPI
from api.chat import router as chat_router
from api.health import router as health_router
from api.upload import router as upload_router
from rag.vector_store import _get_collection


@asynccontextmanager
async def lifespan(app: FastAPI):
    _get_collection()
    yield


app = FastAPI(title="RAG Platform", lifespan=lifespan)

app.include_router(chat_router)
app.include_router(health_router)
app.include_router(upload_router)
