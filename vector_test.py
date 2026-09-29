from config import engine

search=engine.similarity_search("What is the purpose of this document?", k=3)

print(search)