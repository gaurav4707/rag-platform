import truststore
truststore.inject_into_ssl()

from fastapi import FastAPI

from api.chat import router as chat_router
from api.health import router as health_router

app = FastAPI(title="RAG Platform")

app.include_router(chat_router)
app.include_router(health_router)
