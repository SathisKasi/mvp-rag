from __future__ import annotations

import hashlib
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pydantic import BaseModel, Field

from config import engine, llm

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
MAX_UPLOAD_BYTES = 25 * 1024 * 1024

app = FastAPI(title="SATHIS RAG")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


@app.get("/")
def home() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/api/upload")
async def upload_pdf(file: UploadFile = File(...)) -> dict[str, object]:
    filename = Path(file.filename or "document.pdf").name
    if Path(filename).suffix.lower() != ".pdf":
        raise HTTPException(status_code=400, detail="Please choose a PDF file.")

    contents = await file.read(MAX_UPLOAD_BYTES + 1)
    if not contents:
        raise HTTPException(status_code=400, detail="The selected PDF is empty.")
    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="PDFs must be 25 MB or smaller.")

    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temporary_file:
            temporary_path = Path(temporary_file.name)
            temporary_file.write(contents)

        documents = PyPDFLoader(str(temporary_path)).load()
    except Exception as error:
        raise HTTPException(
            status_code=422,
            detail="Could not read this PDF. Check that it is a valid, text-readable document.",
        ) from error
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)

    if not documents:
        raise HTTPException(status_code=422, detail="No readable pages were found in this PDF.")

    for document in documents:
        document.metadata["source"] = filename
        document.metadata["file_name"] = filename

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(documents)
    if not chunks:
        raise HTTPException(status_code=422, detail="No text could be extracted from this PDF.")

    file_digest = hashlib.sha256(contents).hexdigest()
    ids = [f"{file_digest}-{index}" for index in range(len(chunks))]
    try:
        engine.add_documents(chunks, ids=ids)
    except Exception as error:
        raise HTTPException(
            status_code=502,
            detail="The PDF was read, but could not be saved to the vector database. Check your embedding API key and try again.",
        ) from error

    return {"filename": filename, "pages": len(documents), "chunks": len(chunks)}


@app.post("/api/chat")
def chat(request: ChatRequest) -> dict[str, object]:
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Enter a question first.")

    try:
        matches = engine.similarity_search(question, k=4)
        if not matches:
            return {
                "answer": "I don't have any document content to search yet. Upload a PDF to get started.",
                "sources": [],
            }

        context_parts: list[str] = []
        sources: list[dict[str, object]] = []
        seen_sources: set[tuple[str, int | None]] = set()
        for document in matches:
            filename = str(document.metadata.get("file_name") or document.metadata.get("source") or "Uploaded document")
            page_index = document.metadata.get("page")
            page_number = page_index + 1 if isinstance(page_index, int) else None
            page_label = f", page {page_number}" if page_number is not None else ""
            context_parts.append(f"[Source: {filename}{page_label}]\n{document.page_content}")

            source_key = (filename, page_number)
            if source_key not in seen_sources:
                seen_sources.add(source_key)
                sources.append({
                    "filename": filename,
                    "page": page_number,
                    "snippet": document.page_content[:240],
                })

        result = llm.invoke([
            (
                "system",
                "You are a precise document assistant. Answer using only the supplied document excerpts. "
                "If the excerpts do not contain the answer, say that you could not find it in the uploaded documents. "
                "Do not invent facts or claim to have read content that is not present.",
            ),
            (
                "human",
                f"Question: {question}\n\nDocument excerpts:\n{chr(10).join(context_parts)}",
            ),
        ])
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(
            status_code=502,
            detail="The question could not be answered. Check your model API keys and connection, then try again.",
        ) from error

    answer = result.content
    if not isinstance(answer, str):
        answer = str(answer)
    return {"answer": answer, "sources": sources}
