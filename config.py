# LLM Model, Embedding Model, and chroma engine configuration
from langchain_groq  import ChatGroq
from dotenv import load_dotenv
from langchain_google_genai.embeddings import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma

load_dotenv()

llm=ChatGroq(model="openai/gpt-oss-20b")
embedding =GoogleGenerativeAIEmbeddings(model="gemini-embedding-2")
print("Embedding model loaded successfully")
engine= Chroma(embedding_function=embedding, 
               collection_name="MVP_RAG", 
               persist_directory="chroma_db")
