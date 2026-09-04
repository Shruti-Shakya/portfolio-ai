# Portfolio-AI

Portfolio-AI is an AI-powered portfolio assistant that represents a job candidate and answers HR/interviewer questions based on the candidate's resume.

## Current Features

- Extracts text from a resume PDF
- Uses an LLM to parse resume information
- Converts resume information into structured data using Pydantic
- Stores the parsed candidate information as JSON
- Provides a FastAPI backend
- Answers questions about the candidate using the stored resume information
- Supports streaming LLM responses

## Current Architecture


```text
Resume PDF
    │
    ▼
PDF Text Extraction
    │
    ▼
Groq LLM Resume Parsing
    │
    ▼
JSON Response
    │
    ▼
Pydantic Validation
    │
    ▼
Candidate JSON
    │
    ▼
FastAPI Backend
    │
    ├── /chat ──────────► AI Response
    │
    └── /chat/stream ──► Streaming AI Response
