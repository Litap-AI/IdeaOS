from typing import Annotated

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.services.document_intelligence import (
    analyze_document_structure,
    get_relationship_evidence,
   )
from app.services.pdf_parser import extract_pdf_text

app = FastAPI(
    title="IdeaOS API",
    version="0.1.0",
    description="An Operating System for Human Knowledge",
)
document_graph_store = {}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "service": "ideaos-api", "version": "0.1.0"}


@app.post("/api/v1/documents/analyze")
async def analyze_document_endpoint(file: Annotated[UploadFile, File(...)]
):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Please upload a PDF file.")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    text = extract_pdf_text(content)
    analysis = analyze_document_structure(text)

    document_graph_store[file.filename] = analysis["graph"]

    analysis["document"] = {
        "filename": file.filename,
        "preview": text[:4000],
}

    return analysis


@app.get(
    "/api/v1/relationships/{filename}/{source_id}/{target_id}"
)
async def relationship_evidence(
    filename: str,
    source_id: str,
    target_id: str,
):
    graph = document_graph_store.get(filename)

    if not graph:
        raise HTTPException(
            status_code=404,
            detail="Document graph not found.",
        )

    return get_relationship_evidence(
        source_id,
        target_id,
        graph,
    )
