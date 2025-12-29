from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.staticfiles import StaticFiles
import os
import shutil
import uuid
from . import services, utils, database
from .models import (
    ScoreResponse, JobRoleInput, JobDescriptionResponse,
    LoginRequest, LoginResponse, RegisterRequest, RegisterResponse,
    User, UserRole
)
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="HR Assistant API",
    description="This API provides tools for HR tasks, including scoring resumes and creating job descriptions.",
)

# Mount uploads directory
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

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

@app.get("/dashboard/stats/", tags=["Dashboard"])
async def get_dashboard_stats():
    """
    Get dashboard statistics.
    **HR Only**
    """
    stats = database.get_application_stats()
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