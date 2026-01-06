from contextlib import asynccontextmanager
from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.staticfiles import StaticFiles
import os
import shutil
import uuid
from . import services, utils, database
from .models import (
    ScoreResponse, JobRoleInput, JobDescriptionResponse,
    LoginRequest, LoginResponse, RegisterRequest, RegisterResponse,
    User, UserRole, BatchScoreResponse,
    JobPostingCreate, JobPosting, JobPostingResponse, JobPostingsListResponse,
    JobApplication, JobApplicationResponse, JobApplicationsListResponse,
    BulkEmailRequest
)
from .config import settings
# import resend  # Removed in favor of SMTP
from .email_service import EmailService
from typing import List
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure database tables are created
    database.init_db()
    yield
    # Shutdown: nothing to clean up


app = FastAPI(
    title="HR Assistant API",
    description="This API provides tools for HR tasks, including scoring resumes and creating job descriptions.",
    lifespan=lifespan,
)

# Mount uploads directory
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Mount frontend directory
app.mount("/frontend", StaticFiles(directory="frontend", html=True), name="frontend")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== AUTHENTICATION ENDPOINTS ====================

@app.post("/auth/register/", response_model=RegisterResponse, tags=["Authentication"])
async def register(request: RegisterRequest):
    """
    Register a new user (HR or Candidate).
    
    - **email**: User's email address
    - **password**: Password (minimum 6 characters)
    - **full_name**: User's full name
    - **role**: Either 'hr' or 'candidate'
    """
    # Create user in database
    user_data = database.create_user(
        email=request.email,
        password=request.password,
        full_name=request.full_name,
        role=request.role.value,
        phone=request.phone,
        resume_url=request.resume_url
    )
    
    if user_data is None:
        return RegisterResponse(
            success=False,
            message="Email already registered"
        )
    
    user = User(**user_data)
    
    return RegisterResponse(
        success=True,
        message="Registration successful",
        user=user
    )

@app.post("/auth/login/", response_model=LoginResponse, tags=["Authentication"])
async def login(request: LoginRequest):
    """
    Login with email and password.
    Returns a token that should be used for subsequent requests.
    """
    # Verify credentials
    if not database.verify_password(request.email, request.password):
        return LoginResponse(
            success=False,
            message="Invalid email or password"
        )
    
    # Get user and create token
    user_data = database.get_user_by_email(request.email)
    token = database.create_token(request.email)
    
    # Remove password_hash from user data
    user_data.pop('password_hash', None)
    user = User(**user_data)
    
    return LoginResponse(
        success=True,
        message="Login successful",
        user=user,
        token=token
    )

@app.post("/auth/logout/", tags=["Authentication"])
async def logout(token: str = Form(...)):
    """
    Logout and invalidate the token.
    """
    if database.delete_token(token):
        return {"success": True, "message": "Logged out successfully"}
    return {"success": False, "message": "Invalid token"}

@app.get("/auth/me/", response_model=LoginResponse, tags=["Authentication"])
async def get_current_user(token: str):
    """
    Get the current user's information from their token.
    """
    user_data = database.get_user_by_token(token)
    
    if user_data is None:
        return LoginResponse(
            success=False,
            message="Invalid or expired token"
        )
    
    user = User(**user_data)
    
    return LoginResponse(
        success=True,
        message="User found",
        user=user,
        token=token
    )

# ==================== HR ENDPOINTS ====================

@app.post("/score_resume/", response_model=ScoreResponse, tags=["Resume Scoring"])
async def score_resume(
    job_description: str = Form(...),
    resume_file: UploadFile = File(...),
    candidate_name: str = Form(None)
):
    """
    This endpoint scores a resume against a job description.
    **HR Only**

    - **job_description**: The job description text.
    - **resume_file**: The candidate's resume file (PDF or DOCX).
    - **candidate_name**: Optional name of the candidate.
    """
    file_bytes, file_type = utils.get_text_from_resume(resume_file)
    resume_text = services.extract_resume_text(file_bytes, file_type)

    if not resume_text.strip():
        raise HTTPException(status_code=400, detail="Could not extract any text from the resume.")

    score_data = services.get_llm_score(resume_text, job_description)
    
    # Save file to disk
    file_ext = os.path.splitext(resume_file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = f"uploads/{unique_filename}"
    
    with open(file_path, "wb") as f:
        f.write(file_bytes)

    # Save to database
    if not candidate_name:
        candidate_name = "Unknown Candidate" 
        
    database.create_application(
        candidate_name=candidate_name,
        score=score_data.get('score', 0),
        match_details=score_data.get('explanation', ''),
        job_role="Applicant", 
        candidate_email=None,
        resume_path=unique_filename # Save filename/path
    )
    
    return ScoreResponse(**score_data)

@app.post("/score_resumes_batch/", response_model=BatchScoreResponse, tags=["Resume Scoring"])
async def score_resumes_batch(
    job_description: str = Form(...),
    resume_files: List[UploadFile] = File(...),
):
    """
    Score multiple resumes against a job description in a batch.
    **HR Only**
    """
    results = []
    
    # Process up to 5 files
    for resume_file in resume_files[:5]:
        try:
            file_bytes, file_type = utils.get_text_from_resume(resume_file)
            resume_text = services.extract_resume_text(file_bytes, file_type)

            if not resume_text.strip():
                # Handle empty text case
                results.append(ScoreResponse(
                    score=0,
                    explanation="Could not extract text from this file.",
                    filename=resume_file.filename
                ))
                continue

            score_data = services.get_llm_score(resume_text, job_description)
            
            # Save file to disk
            file_ext = os.path.splitext(resume_file.filename)[1]
            unique_filename = f"{uuid.uuid4()}{file_ext}"
            file_path = f"uploads/{unique_filename}"
            
            with open(file_path, "wb") as f:
                f.write(file_bytes)

            # Save to database (Assuming candidate name is filename for now or "Unknown")
            candidate_name = os.path.splitext(resume_file.filename)[0]
            
            database.create_application(
                candidate_name=candidate_name,
                score=score_data.get('score', 0),
                match_details=score_data.get('explanation', ''),
                job_role="Applicant", 
                candidate_email=None,
                resume_path=unique_filename
            )
            
            results.append(ScoreResponse(
                score=score_data.get('score', 0),
                explanation=score_data.get('explanation', ''),
                filename=resume_file.filename
            ))
            
        except Exception as e:
            results.append(ScoreResponse(
                score=0, 
                explanation=f"Error processing file: {str(e)}", 
                filename=resume_file.filename
            ))

    return BatchScoreResponse(results=results)

@app.post("/create_job_description/", response_model=JobDescriptionResponse, tags=["Job Description"])
async def create_job_description(job_details: JobRoleInput):
    """
    Creates a professional job description from key details about a role.
    **HR Only**
    """
    generated_jd = services.generate_jd_from_llm(job_details)
    return JobDescriptionResponse(job_description=generated_jd)

# ==================== CANDIDATE ENDPOINTS ====================

from .models import CandidateApplication

@app.get("/candidates/", tags=["Candidates"])
async def get_all_candidates():
    """
    Get all scored candidates/applications.
    **HR Only**
    """
    apps_data = database.get_all_applications()
    candidates = []
    base_url = "http://localhost:8000/uploads/" # Should come from config
    
    for app in apps_data:
        app_dict = dict(app)
        if app_dict.get('resume_path'):
            app_dict['resume_url'] = f"{base_url}{app_dict['resume_path']}"
        candidates.append(CandidateApplication(**app_dict))
        
    return {"candidates": candidates}

@app.put("/candidates/{app_id}/status/", tags=["Candidates"])
async def update_candidate_status(app_id: str, status: str = Form(...)):
    """
    Update the status of a candidate application.
    **HR Only**
    """
    if status not in ['pending', 'shortlisted', 'rejected']:
        raise HTTPException(status_code=400, detail="Invalid status")
        
    success = database.update_application_status(app_id, status)
    if not success:
        raise HTTPException(status_code=404, detail="Application not found")
        
    return {"success": True, "message": f"Status updated to {status}"}

@app.get("/dashboard/stats/", tags=["Dashboard"])
async def get_dashboard_stats():
    """
    Get dashboard statistics.
    **HR Only**
    """
    stats = database.get_application_stats()
    return stats

# ==================== JOB POSTING ENDPOINTS ====================

@app.post("/jobs/", response_model=JobPostingResponse, tags=["Job Postings"])
async def create_job_posting(job: JobPostingCreate, token: str = Form(None)):
    """
    Create a new job posting.
    **HR Only**
    """
    # Get user from token if provided
    created_by = None
    if token:
        user_data = database.get_user_by_token(token)
        if user_data:
            created_by = user_data['id']

    job_data = database.create_job_posting(
        title=job.title,
        company_name=job.company_name,
        description=job.description,
        experience_level=job.experience_level,
        location=job.location,
        responsibilities=job.responsibilities,
        skills=job.skills,
        created_by=created_by
    )

    return JobPostingResponse(
        success=True,
        message="Job posting created successfully",
        job=JobPosting(**job_data)
    )

@app.post("/jobs/from-jd/", response_model=JobPostingResponse, tags=["Job Postings"])
async def create_job_posting_from_jd(
    title: str = Form(...),
    company_name: str = Form(...),
    description: str = Form(...),
    experience_level: str = Form(None),
    location: str = Form(None),
    responsibilities: str = Form(None),
    skills: str = Form(None),
    token: str = Form(None)
):
    """
    Create a new job posting from JD generator.
    **HR Only**
    """
    created_by = None
    if token:
        user_data = database.get_user_by_token(token)
        if user_data:
            created_by = user_data['id']

    job_data = database.create_job_posting(
        title=title,
        company_name=company_name,
        description=description,
        experience_level=experience_level,
        location=location,
        responsibilities=responsibilities,
        skills=skills,
        created_by=created_by
    )

    return JobPostingResponse(
        success=True,
        message="Job posting created successfully",
        job=JobPosting(**job_data)
    )

@app.get("/jobs/", response_model=JobPostingsListResponse, tags=["Job Postings"])
async def get_all_jobs(status: str = None):
    """
    Get all job postings, optionally filtered by status.
    Public endpoint for candidates to view active jobs.
    """
    jobs_data = database.get_all_job_postings(status=status)
    jobs = [JobPosting(**job) for job in jobs_data]
    return JobPostingsListResponse(jobs=jobs)

@app.get("/jobs/{job_id}", tags=["Job Postings"])
async def get_job(job_id: str):
    """
    Get a specific job posting by ID.
    """
    job_data = database.get_job_posting_by_id(job_id)
    if not job_data:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"success": True, "job": JobPosting(**job_data)}

@app.put("/jobs/{job_id}/status/", tags=["Job Postings"])
async def update_job_status(job_id: str, status: str = Form(...)):
    """
    Update the status of a job posting.
    **HR Only**
    """
    if status not in ['active', 'closed', 'draft']:
        raise HTTPException(status_code=400, detail="Invalid status")

    success = database.update_job_posting_status(job_id, status)
    if not success:
        raise HTTPException(status_code=404, detail="Job not found")

    return {"success": True, "message": f"Job status updated to {status}"}

@app.delete("/jobs/{job_id}", tags=["Job Postings"])
async def delete_job(job_id: str):
    """
    Delete a job posting.
    **HR Only**
    """
    success = database.delete_job_posting(job_id)
    if not success:
        raise HTTPException(status_code=404, detail="Job not found")

    return {"success": True, "message": "Job deleted successfully"}

# ==================== JOB APPLICATION ENDPOINTS ====================

@app.post("/jobs/{job_id}/apply/", response_model=JobApplicationResponse, tags=["Job Applications"])
async def apply_to_job(
    job_id: str,
    token: str = Form(...),
    resume_file: UploadFile = File(None),
    cover_letter: str = Form(None),
    # New fields
    applicant_name: str = Form(None), # Optional override
    relevant_experience: str = Form(None),
    overall_experience: str = Form(None),
    current_location: str = Form(None),
    preferred_location: str = Form(None),
    current_ctc: str = Form(None),
    expected_ctc: str = Form(None),
    current_company: str = Form(None),
    notice_period: str = Form(None)
):
    """
    Apply to a job posting.
    **Candidate Only**
    """
    # Verify token and get user
    user_data = database.get_user_by_token(token)
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    # Check if job exists
    job_data = database.get_job_posting_by_id(job_id)
    if not job_data:
        raise HTTPException(status_code=404, detail="Job not found")

    if job_data['status'] != 'active':
        raise HTTPException(status_code=400, detail="This job is no longer accepting applications")

    # Check for existing application
    if database.check_existing_application(job_id, user_data['id']):
        raise HTTPException(status_code=400, detail="You have already applied to this job")

    # Save resume file if provided
    resume_path = None
    if resume_file and resume_file.filename:
        file_ext = os.path.splitext(resume_file.filename)[1]
        if file_ext.lower() not in ['.pdf', '.docx', '.doc']:
            raise HTTPException(status_code=400, detail="Only PDF and DOCX files are allowed")

        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = f"uploads/{unique_filename}"

        content = await resume_file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        resume_path = unique_filename

    # Create application
    # Use provided name or fallback to user profile name
    final_name = applicant_name if applicant_name else user_data['full_name']
    
    app_data = database.create_job_application(
        job_id=job_id,
        candidate_id=user_data['id'],
        candidate_name=final_name,
        candidate_email=user_data['email'],
        resume_path=resume_path,
        cover_letter=cover_letter,
        relevant_experience=relevant_experience,
        overall_experience=overall_experience,
        current_location=current_location,
        preferred_location=preferred_location,
        current_ctc=current_ctc,
        expected_ctc=expected_ctc,
        current_company=current_company,
        notice_period=notice_period
    )

    # Add resume URL if available
    if resume_path:
        app_data['resume_url'] = f"http://localhost:8000/uploads/{resume_path}"

    return JobApplicationResponse(
        success=True,
        message="Application submitted successfully",
        application=JobApplication(**app_data)
    )

@app.get("/job-applications/", response_model=JobApplicationsListResponse, tags=["Job Applications"])
async def get_all_job_applications(job_id: str = None):
    """
    Get all job applications.
    **HR Only**
    """
    apps_data = database.get_all_job_applications(job_id=job_id)
    base_url = "http://localhost:8000/uploads/"

    applications = []
    for app in apps_data:
        app_dict = dict(app)
        if app_dict.get('resume_path'):
            app_dict['resume_url'] = f"{base_url}{app_dict['resume_path']}"
        applications.append(JobApplication(**app_dict))

    return JobApplicationsListResponse(applications=applications)

@app.get("/job-applications/my/", response_model=JobApplicationsListResponse, tags=["Job Applications"])
async def get_my_applications(token: str):
    """
    Get current user's job applications.
    **Candidate Only**
    """
    user_data = database.get_user_by_token(token)
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    apps_data = database.get_job_applications_by_candidate(user_data['id'])
    base_url = "http://localhost:8000/uploads/"

    applications = []
    for app in apps_data:
        app_dict = dict(app)
        if app_dict.get('resume_path'):
            app_dict['resume_url'] = f"{base_url}{app_dict['resume_path']}"
        applications.append(JobApplication(**app_dict))

    return JobApplicationsListResponse(applications=applications)

@app.get("/job-applications/{app_id}", tags=["Job Applications"])
async def get_job_application(app_id: str):
    """
    Get a specific job application by ID.
    """
    app_data = database.get_job_application_by_id(app_id)
    if not app_data:
        raise HTTPException(status_code=404, detail="Application not found")

    base_url = "http://localhost:8000/uploads/"
    if app_data.get('resume_path'):
        app_data['resume_url'] = f"{base_url}{app_data['resume_path']}"

    return {"success": True, "application": JobApplication(**app_data)}

@app.put("/job-applications/{app_id}/status/", tags=["Job Applications"])
async def update_job_application_status(app_id: str, status: str = Form(...)):
    """
    Update the status of a job application.
    **HR Only**
    """
    if status not in ['pending', 'reviewed', 'shortlisted', 'rejected', 'hired']:
        raise HTTPException(status_code=400, detail="Invalid status")

    success = database.update_job_application_status(app_id, status)
    if not success:
        raise HTTPException(status_code=404, detail="Application not found")

    return {"success": True, "message": f"Application status updated to {status}"}

@app.get("/job-applications/stats/", tags=["Job Applications"])
async def get_job_application_stats():
    """
    Get job application statistics.
    **HR Only**
    """
    stats = database.get_job_application_stats()
    return stats

# ==================== REALTIME VOICE INTERVIEW ENDPOINTS ====================

from . import chat_service

@app.post("/realtime/session/", tags=["Voice Interview"])
async def create_realtime_session(candidate_name: str = Form(...)):
    """
    Create a new Realtime API session for voice interview.
    Returns an ephemeral token for secure WebSocket connection.
    **Candidate Only**
    
    - **candidate_name**: Name of the candidate
    """
    try:
        session_data = await chat_service.get_ephemeral_token(candidate_name)
        
        return {
            "success": True,
            "message": "Session created",
            "session": session_data
        }
    except ValueError as e:
        return {
            "success": False,
            "message": str(e),
            "session": None
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "session": None
        }

# ==================== EMAIL ENDPOINTS ====================

@app.post("/email/bulk/", tags=["Email"])
def send_bulk_email(request: BulkEmailRequest):
    """
    Send bulk emails to candidates using Gmail SMTP.
    **HR Only**
    """
    # Determine credentials to use
    sender = request.sender_email or settings.EMAIL_SENDER
    password = request.app_password or settings.EMAIL_PASSWORD

    if not sender or not password:
         return {"success": False, "results": [], "error": "Email credentials not configured. Please provide them in settings or request."}

    # Initialize Email Service
    email_service = EmailService(sender, password)
    
    # Prepare recipients list
    recipients = []
    for email in request.candidate_emails:
        # We can add name if available, for now just email
        recipients.append({"email": email, "name": "Candidate"})
    
    # Process Content for Free Flowing Text
    # If the user provides plain text without HTML tags, we format it nicely.
    body_content = request.html_content
    if not ("<" in body_content and ">" in body_content):
        # Convert newlines to breaks
        formatted_text = body_content.replace("\n", "<br>")
        # Wrap in a nice template
        body_content = f"""
        <div style="font-family: Arial, sans-serif; font-size: 14px; color: #333; line-height: 1.6;">
            {formatted_text}
        </div>
        """

    # Send emails
    send_results = email_service.send_bulk(
        recipients=recipients,
        subject=request.subject,
        body_template=body_content,
        html=True
    )
    
    # Format results to match frontend expectation
    formatted_results = []
    for s in send_results["success"]:
        formatted_results.append({"email": s["email"], "status": "sent"})
    for f in send_results["failed"]:
        formatted_results.append({"email": f["email"], "status": "failed", "error": f["error"]})
            
    return {"success": True, "results": formatted_results}