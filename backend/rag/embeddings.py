from langchain_google_genai import GoogleGenerativeAIEmbeddings
from config import EMBEDDING_MODEL

embeddings = GoogleGenerativeAIEmbeddings(
    model=EMBEDDING_MODEL
)