from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from . import services, utils
from .models import ScoreResponse, JobRoleInput, JobDescriptionResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="HR Assistant API",
    description="This API provides tools for HR tasks, including scoring resumes and creating job descriptions.",
)
# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/score_resume/", response_model=ScoreResponse, tags=["Resume Scoring"])
async def score_resume(
    job_description: str = Form(...),
    resume_file: UploadFile = File(...)
):
    """
    This endpoint scores a resume against a job description.

    - **job_description**: The job description text.
    - **resume_file**: The candidate's resume file (PDF or DOCX).
    """
    file_bytes, file_type = utils.get_text_from_resume(resume_file)
    resume_text = services.extract_resume_text(file_bytes, file_type)

    if not resume_text.strip():
        raise HTTPException(status_code=400, detail="Could not extract any text from the resume.")

    score_data = services.get_llm_score(resume_text, job_description)
    return ScoreResponse(**score_data)

@app.post("/create_job_description/", response_model=JobDescriptionResponse, tags=["Job Description"])
async def create_job_description(job_details: JobRoleInput):
    """
    Creates a professional job description from key details about a role.
    """
    generated_jd = services.generate_jd_from_llm(job_details)
    return JobDescriptionResponse(job_description=generated_jd)