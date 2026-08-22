from typing import Annotated

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.services.document_intelligence import analyze_document_structure
from app.services.pdf_parser import extract_pdf_text

app = FastAPI(
    title="IdeaOS API",
    version="0.1.0",
    description="An Operating System for Human Knowledge",
)

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
    analysis["document"] = {
        "filename": file.filename,
        "preview": text[:4000],
}

    return analysis
