# IdeaOS

**An Operating System for Human Knowledge**

IdeaOS is an AI research-intelligence platform that studies how ideas are created, transformed, connected, and argued in documents.

## MVP

- PDF upload and text extraction
- Document metadata
- Basic concept extraction
- Initial Idea Genome scoring
- Knowledge graph foundation
- AI Copilot foundation

## Architecture

React + TypeScript frontend → FastAPI backend → document parser → analysis engines → graph/vector storage.

## Local development

### Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Backend: http://localhost:8000  
API docs: http://localhost:8000/docs
Frontend: http://localhost:5173
