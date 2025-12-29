from pydantic import BaseModel, Field, EmailStr
from typing import Optional, Literal
from enum import Enum

# ==================== AUTHENTICATION MODELS ====================

class UserRole(str, Enum):
    HR = "hr"
    CANDIDATE = "candidate"

class RegisterRequest(BaseModel):
    """Request model for user registration."""
    email: str = Field(..., example="user@company.com")
    password: str = Field(..., min_length=6, example="securepassword123")
    full_name: str = Field(..., example="John Doe")
    role: UserRole = Field(..., example="hr")
    # Additional fields for candidates
    phone: Optional[str] = Field(None, example="+1234567890")
    resume_url: Optional[str] = Field(None, example="https://example.com/resume.pdf")

class LoginRequest(BaseModel):
    """Request model for user login."""
    email: str = Field(..., example="user@company.com")
    password: str = Field(..., example="securepassword123")

class User(BaseModel):
    """User model for database storage."""
    id: str
    email: str
    full_name: str
    role: UserRole
    phone: Optional[str] = None
    resume_url: Optional[str] = None
    created_at: str

class LoginResponse(BaseModel):
    """Response model for successful login."""
    success: bool
    message: str
    user: Optional[User] = None
    token: Optional[str] = None

class RegisterResponse(BaseModel):
    """Response model for successful registration."""
    success: bool
    message: str
    user: Optional[User] = None

class CandidateApplication(BaseModel):
    """Model for a scored candidate application."""
    id: str
    candidate_name: str
    candidate_email: Optional[str] = None
    job_role: Optional[str] = None
    score: int
    match_details: Optional[str] = None
    status: str
    created_at: str
    resume_url: Optional[str] = None

# ==================== EXISTING MODELS ====================

class ScoreResponse(BaseModel):
    """Defines the structure of the API response for scoring."""
    score: float
    explanation: str

class JobRoleInput(BaseModel):
    """Defines the structure for the job description creation request."""
    job_title: str = Field(..., example="Senior Python Developer")
    company_name: str = Field(..., example="Innovatech Solutions")
    key_responsibilities: str = Field(
        ...,
        example="Develop and maintain web applications using FastAPI; Design and implement RESTful APIs; Collaborate with front-end developers."
    )
    required_skills: str = Field(
        ...,
        example="5+ years of Python experience, FastAPI, Docker, PostgreSQL, AWS."
    )
    experience_level: str = Field(..., example="Senior Level (5-8 years)")
    location: str = Field(..., example="Remote")
    extra_details: Optional[str] = Field(
        None,
        example="The ideal candidate should also have experience with CI/CD pipelines and microservices architecture."
    )

class JobDescriptionResponse(BaseModel):
    """Defines the structure of the job description response."""
    job_description: str

# ==================== CHAT MODELS ====================

class ChatMessage(BaseModel):
    """A single chat message."""
    role: str = Field(..., example="user")  # 'user' or 'assistant'
    content: str = Field(..., example="Hello, I'm here for my interview.")

class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    messages: list[ChatMessage] = Field(..., description="List of conversation messages")
    candidate_name: str = Field(..., example="John Doe")

class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    success: bool
    message: str
    response: Optional[str] = None