import os
import time
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq
from pydantic import BaseModel,Field
from fastapi import FastAPI
from pypdf import PdfReader
from fastapi.responses import StreamingResponse
import json

load_dotenv()
my_api_key=os.getenv("GROQ_API_KEY")

if not my_api_key:
    raise ValueError("API key not found")

client=Groq(api_key=my_api_key)
model = "openai/gpt-oss-120b"


app=FastAPI()

class Experience(BaseModel):
    company: str | None = None
    role: str | None = None
    duration: str | None = None
    description: str | None = None
    skills_used: list[str] = []

class Resume(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None

    total_experience_years: float | None = None

    skills: list[str] = []
    experiences: list[Experience] = []
    education: list[str] = []
    projects: list[str] = []
    certifications: list[str] = []


resume_schema = Resume.model_json_schema()

class ChatRequest(BaseModel):
    question: str = Field(min_length=1)

def ask_candidate(question: str,resume: Resume):
    system_prompt = f"""
You are an AI assistant representing a job candidate.

Below is everything you know about the candidate.

{resume.model_dump_json(indent=2)}

Rules:

1.Answer only using this information.
2.Never hallucinate
3.If information is unavailable, just say
"I don't have enough information to answer that."
4.Be Professional.
5.Answer as if HR is interviewing this candidate.
6. Do not add opinions, assumptions, interpretations, or conclusions that are not explicitly supported by the candidate information.
7. Keep answers concise and directly answer the question.

"""
    response = client.chat.completions.create(
        model=model,
        messages=[

            {
                "role":"system",
                "content":system_prompt
            },

            {
                "role":"user",
                "content":question
            }
        ]
    )
    return response.choices[0].message.content

def ask_candidate_stream(question: str, resume: Resume):
    system_prompt = f"""
You are an AI assistant representing a job candidate.

Below is the candidate information:

{resume.model_dump_json(indent=2)}

Rules:

1. Answer only using the information provided above.
2. Never invent or assume information.
3. If the information is unavailable, say:
   "I don't have enough information to answer that."
4. Be professional.
5. Answer as if HR is interviewing this candidate.
6. Do not add opinions or conclusions that are not supported by the candidate information.
7. Keep answers concise and directly answer the question.
"""

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": question
            }
        ],
        stream=True
    )

    for chunk in response:
        content = chunk.choices[0].delta.content

        if content:
            yield content
#parsed resume
def parse_resume(resume_text):
    system_prompt = f"""
    You are an expert resume parser.

    Extract information from the resume based on its meaning,
    not only based on exact section headings.

    Different resumes may use different headings.

    For example:
    - Experience
    - Professional Experience
    - Work History
    - Employment
    - Internships

    These may all contain relevant experience.

    Skills may also appear in the skills section, work experience,
    internships or projects.

    Return ONLY valid JSON matching this schema:

    {resume_schema}

    Important rules:

    1. Do not invent information.
    2. If a value is not available, return null.
    3. If a list has no information, return an empty list.
    4. Include internships inside experiences.
    5. Extract skills mentioned across the entire resume.
    """
    user_prompt = f"""
    Parse the following resume:

    {resume_text}
    """
    message_system={
        "role" : "system",
        "content" : system_prompt
    }
    message_user={
        "role" : "user",
        "content" : user_prompt
    }
    messages=[message_system, message_user]
    response_format={
        "type": "json_object"
    }
    response=client.chat.completions.create(model=model, messages=messages, response_format=response_format)
    raw_output = response.choices[0].message.content
    data = json.loads(raw_output)
    resume = Resume(**data)
    return resume

#Pydantic object
#      ↓
#model_dump()
#      ↓
#Python dict
#      ↓
#json.dump()
#     ↓
#JSON file
def save_candidate(resume):
    candidate_data = resume.model_dump()
    #with open("candidate.json", "w") as file:
        #file.write(resume.model_dump_json(indent=2))
    with open("candidate.json", "w") as file:
        json.dump(candidate_data, file, indent=2)

#candidate.json
#     ↓
#json.load()
#     ↓
#Python dictionary
#     ↓
#Resume(**data)
#     ↓
#Pydantic Resume object
def load_candidate():
    candidate_path = Path("candidate.json")

    if not candidate_path.exists():
        raise FileNotFoundError("candidate.json not found")

    with open(candidate_path, "r") as file:
        data = json.load(file)

    return Resume(**data)

#pdf extraction
def read_pdf(file_path):
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text

@app.get("/")
def home():
    resume_text=read_pdf(Path("Resume_Shruti Shakya.pdf"))
    resume=parse_resume(resume_text)
    save_candidate(resume)
    return {
        "message" : "Candidate JSON created successfully"
    }

@app.post("/chat")
def chat(request: ChatRequest):
    resume = load_candidate()
    answer=ask_candidate(request.question,resume)
    return{
        "answer":answer
    }
@app.post("/chat/stream")
def chat_stream(request: ChatRequest):
    resume = load_candidate()

    return StreamingResponse(
        ask_candidate_stream(request.question, resume),
        media_type="text/plain"
    )
