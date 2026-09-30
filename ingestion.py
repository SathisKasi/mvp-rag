from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from fastapi import HTTPException, UploadFile

from web_app import upload_pdf


async def ingest_files(paths: list[Path]) -> None:
    for path in paths:
        if not path.is_file():
            print(f"Skipped {path}: file not found.")
            continue

        try:
            with path.open("rb") as source_file:
                uploaded_file = UploadFile(file=source_file, filename=path.name)
                result = await upload_pdf(uploaded_file)
            if result["duplicate"]:
                print(f"Skipped {path.name}: identical PDF is already indexed.")
            else:
                print(f"Indexed {path.name}: {result['inserted_chunks']} chunks added.")
        except HTTPException as error:
            print(f"Could not index {path.name}: {error.detail}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Index PDF files into the SATHIS RAG PostgreSQL database.")
    parser.add_argument("pdfs", nargs="*", type=Path, help="One or more PDF file paths")
    arguments = parser.parse_args()
    paths = arguments.pdfs or ([Path("SKS.pdf")] if Path("SKS.pdf").is_file() else [])
    if not paths:
        parser.error("provide one or more PDF paths")
    asyncio.run(ingest_files(paths))


if __name__ == "__main__":
    main()