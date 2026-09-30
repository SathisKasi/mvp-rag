import os

from langchain_groq import ChatGroq
from dotenv import load_dotenv
from langchain_google_genai.embeddings import GoogleGenerativeAIEmbeddings
from langchain_postgres import PGVector
from sqlalchemy import URL

from document_registry import DocumentRegistry

load_dotenv()

postgres_password = os.getenv("POSTGRES_PASSWORD")
if not postgres_password:
    raise RuntimeError("Set POSTGRES_PASSWORD in the local .env file before starting SATHIS RAG.")

database_url = URL.create(
    drivername="postgresql+psycopg",
    username=os.getenv("POSTGRES_USER", "postgres"),
    password=postgres_password,
    host=os.getenv("POSTGRES_HOST", "localhost"),
    port=int(os.getenv("POSTGRES_PORT", "5433")),
    database=os.getenv("POSTGRES_DB", "mvp-rag"),
)

llm = ChatGroq(model=os.getenv("GROQ_MODEL", "openai/gpt-oss-20b"))
embedding = GoogleGenerativeAIEmbeddings(model=os.getenv("GOOGLE_EMBEDDING_MODEL", "gemini-embedding-2"))
engine = PGVector(
    embeddings=embedding,
    connection=database_url.render_as_string(hide_password=False),
    collection_name="MVP_RAG",
    use_jsonb=True,
    create_extension=True,
)
document_registry = DocumentRegistry(database_url)
