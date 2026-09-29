from langchain_community.document_loaders import PyPDFLoader

from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import engine

# Data load
loader = PyPDFLoader("SKS.pdf")
texts = loader.load()

print(len(texts))

#chunking recursive
data_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500, 
    chunk_overlap=20)

chunk = data_splitter.split_documents(texts)

engine.add_documents(chunk)