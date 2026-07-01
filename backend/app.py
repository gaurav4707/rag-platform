import truststore
truststore.inject_into_ssl()

from contextlib import asynccontextmanager
from fastapi import FastAPI
from rag.vector_store import index_documents
from api.chat import router as chat_router
from api.health import router as health_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    index_documents()
    yield


app = FastAPI(title="RAG Platform")

app.include_router(chat_router)
app.include_router(health_router)
