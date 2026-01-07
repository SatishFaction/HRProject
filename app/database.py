"""
PostgreSQL Database module for user authentication.
Uses Neon PostgreSQL cloud database.
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from typing import Optional, List
import hashlib
import secrets
from .config import settings

def get_connection():
    """Get a database connection."""
    conn = psycopg2.connect(settings.DATABASE_URL)
    return conn

def init_db():
    """Initialize the database with required tables."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('hr', 'candidate')),
            phone TEXT,
            resume_url TEXT,
            created_at TEXT NOT NULL
        )
    ''')
    
    # Create tokens table for session management
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tokens (
            token TEXT PRIMARY KEY,
            user_email TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_email) REFERENCES users(email)
        )
    ''') 
    
    # Create applications table for resume scores
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS applications (
            id TEXT PRIMARY KEY,
            candidate_name TEXT NOT NULL,
            candidate_email TEXT,
            job_role TEXT,
            score INTEGER,
            match_details TEXT,
            status TEXT DEFAULT 'pending',
            created_at TEXT NOT NULL,
            resume_path TEXT
        )
    ''')
    
    # Create job_postings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS job_postings (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            company_name TEXT NOT NULL,
            description TEXT NOT NULL,
            experience_level TEXT,
            location TEXT,
            responsibilities TEXT,
            skills TEXT,
            status TEXT DEFAULT 'active' CHECK(status IN ('active', 'closed', 'draft')),
            created_by TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (created_by) REFERENCES users(id)
        )
    ''')

    # Create job_applications table (for candidates applying to jobs)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS job_applications (
            id TEXT PRIMARY KEY,
            job_id TEXT NOT NULL,
            candidate_id TEXT NOT NULL,
            candidate_name TEXT NOT NULL,
            candidate_email TEXT NOT NULL,
            resume_path TEXT,
            cover_letter TEXT,
            status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'reviewed', 'shortlisted', 'rejected', 'hired')),
            created_at TEXT NOT NULL,
            relevant_experience TEXT,
            overall_experience TEXT,
            current_location TEXT,
            preferred_location TEXT,
            current_ctc TEXT,
            expected_ctc TEXT,
            current_company TEXT,
            notice_period TEXT,
            FOREIGN KEY (job_id) REFERENCES job_postings(id),
            FOREIGN KEY (candidate_id) REFERENCES users(id)
        )
    ''')

    conn.commit()
    conn.close()
    print(f"PostgreSQL Database initialized successfully!")

def hash_password(password: str) -> str:
    """Hash a password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()

def generate_token() -> str:
    """Generate a secure random token."""
    return secrets.token_urlsafe(32)

def generate_user_id() -> str:
    """Generate a unique user ID."""
    return secrets.token_urlsafe(16)

# ==================== APPLICATION OPERATIONS ====================

def create_application(candidate_name: str, score: int, match_details: str, 
                      job_role: str = "General", candidate_email: Optional[str] = None,
                      resume_path: Optional[str] = None) -> dict:
    """Save a resume score/application."""
    conn = get_connection()
    cursor = conn.cursor()
    
    app_id = generate_user_id()
    created_at = datetime.now().isoformat()
    
    cursor.execute('''
        INSERT INTO applications (id, candidate_name, candidate_email, job_role, score, match_details, created_at, resume_path)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    ''', (app_id, candidate_name, candidate_email, job_role, score, match_details, created_at, resume_path))
    
    conn.commit()
    
    row = {
        'id': app_id,
        'candidate_name': candidate_name,
        'candidate_email': candidate_email,
        'job_role': job_role,
        'score': score,
        'match_details': match_details,
        'status': 'pending',
        'created_at': created_at,
        'resume_path': resume_path
    }
    conn.close()
    return row

def update_application_status(app_id: str, status: str) -> bool:
    """Update the status of an application."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("UPDATE applications SET status = %s WHERE id = %s", (status, app_id))
    updated = cursor.rowcount > 0
    
    conn.commit()
    conn.close()
    return updated

def get_all_applications() -> List[dict]:
    """Get all applications/scored resumes."""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute("SELECT * FROM applications ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

def get_application_stats() -> dict:
    """Get dashboard statistics."""
    conn = get_connection()
    cursor = conn.cursor()
    
    stats = {
        'total': 0,
        'shortlisted': 0,
        'rejected': 0,
        'pending': 0,
        'avg_score': 0
    }
    
    cursor.execute("SELECT COUNT(*), AVG(score) FROM applications")
    row = cursor.fetchone()
    if row:
        stats['total'] = row[0] or 0
        stats['avg_score'] = int(row[1] or 0)
        
    cursor.execute("SELECT status, COUNT(*) FROM applications GROUP BY status")
    rows = cursor.fetchall()
    for status, count in rows:
        if status in stats:
            stats[status] = count
            
    conn.close()
    return stats

# ==================== USER OPERATIONS ====================

def create_user(email: str, password: str, full_name: str, role: str, 
                phone: Optional[str] = None, resume_url: Optional[str] = None) -> Optional[dict]:
    """
    Create a new user in the database.
    Returns the user dict if successful, None if email already exists.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        user_id = generate_user_id()
        password_hash = hash_password(password)
        created_at = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO users (id, email, password_hash, full_name, role, phone, resume_url, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ''', (user_id, email.lower(), password_hash, full_name, role, phone, resume_url, created_at))
        
        conn.commit()
        
        return {
            'id': user_id,
            'email': email.lower(),
            'full_name': full_name,
            'role': role,
            'phone': phone,
            'resume_url': resume_url,
            'created_at': created_at
        }
    except psycopg2.IntegrityError:
        # Email already exists
        conn.rollback()
        return None
    finally:
        conn.close()

def get_user_by_email(email: str) -> Optional[dict]:
    """Get a user by their email address."""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute('SELECT * FROM users WHERE email = %s', (email.lower(),))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None

def verify_password(email: str, password: str) -> bool:
    """Verify a user's password."""
    user = get_user_by_email(email)
    if not user:
        return False
    return user['password_hash'] == hash_password(password)

def get_all_candidates() -> List[dict]:
    """Get all users with role='candidate'."""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute("SELECT id, email, full_name, role, phone, resume_url, created_at FROM users WHERE role = 'candidate'")
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

# ==================== TOKEN OPERATIONS ====================

def create_token(user_email: str) -> str:
    """Create a new session token for a user."""
    conn = get_connection()
    cursor = conn.cursor()
    
    token = generate_token()
    created_at = datetime.now().isoformat()
    
    cursor.execute('''
        INSERT INTO tokens (token, user_email, created_at)
        VALUES (%s, %s, %s)
    ''', (token, user_email.lower(), created_at))
    
    conn.commit()
    conn.close()
    
    return token

def get_user_by_token(token: str) -> Optional[dict]:
    """Get a user by their session token."""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute('''
        SELECT u.id, u.email, u.full_name, u.role, u.phone, u.resume_url, u.created_at
        FROM tokens t
        JOIN users u ON t.user_email = u.email
        WHERE t.token = %s
    ''', (token,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None

def delete_token(token: str) -> bool:
    """Delete a session token (logout)."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM tokens WHERE token = %s', (token,))
    deleted = cursor.rowcount > 0
    
    conn.commit()
    conn.close()
    
    return deleted

# ==================== JOB POSTING OPERATIONS ====================

def create_job_posting(title: str, company_name: str, description: str,
                       experience_level: Optional[str] = None, location: Optional[str] = None,
                       responsibilities: Optional[str] = None, skills: Optional[str] = None,
                       created_by: Optional[str] = None, status: str = 'active') -> dict:
    """Create a new job posting."""
    conn = get_connection()
    cursor = conn.cursor()

    job_id = generate_user_id()
    created_at = datetime.now().isoformat()

    cursor.execute('''
        INSERT INTO job_postings (id, title, company_name, description, experience_level,
                                  location, responsibilities, skills, status, created_by, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ''', (job_id, title, company_name, description, experience_level, location,
          responsibilities, skills, status, created_by, created_at))

    conn.commit()
    conn.close()

    return {
        'id': job_id,
        'title': title,
        'company_name': company_name,
        'description': description,
        'experience_level': experience_level,
        'location': location,
        'responsibilities': responsibilities,
        'skills': skills,
        'status': status,
        'created_by': created_by,
        'created_at': created_at
    }

def get_all_job_postings(status: Optional[str] = None) -> List[dict]:
    """Get all job postings, optionally filtered by status."""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    if status:
        cursor.execute("SELECT * FROM job_postings WHERE status = %s ORDER BY created_at DESC", (status,))
    else:
        cursor.execute("SELECT * FROM job_postings ORDER BY created_at DESC")

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]

def get_job_posting_by_id(job_id: str) -> Optional[dict]:
    """Get a specific job posting by ID."""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("SELECT * FROM job_postings WHERE id = %s", (job_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return dict(row)
    return None

def update_job_posting_status(job_id: str, status: str) -> bool:
    """Update the status of a job posting."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("UPDATE job_postings SET status = %s WHERE id = %s", (status, job_id))
    updated = cursor.rowcount > 0

    conn.commit()
    conn.close()
    return updated

def delete_job_posting(job_id: str) -> bool:
    """Delete a job posting."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM job_postings WHERE id = %s", (job_id,))
    deleted = cursor.rowcount > 0

    conn.commit()
    conn.close()
    return deleted

# ==================== JOB APPLICATION OPERATIONS ====================

def create_job_application(job_id: str, candidate_id: str, candidate_name: str,
                           candidate_email: str, resume_path: Optional[str] = None,
                           cover_letter: Optional[str] = None,
                           relevant_experience: Optional[str] = None,
                           overall_experience: Optional[str] = None,
                           current_location: Optional[str] = None,
                           preferred_location: Optional[str] = None,
                           current_ctc: Optional[str] = None,
                           expected_ctc: Optional[str] = None,
                           current_company: Optional[str] = None,
                           notice_period: Optional[str] = None) -> dict:
    """Create a new job application."""
    conn = get_connection()
    cursor = conn.cursor()

    app_id = generate_user_id()
    created_at = datetime.now().isoformat()

    cursor.execute('''
        INSERT INTO job_applications (
            id, job_id, candidate_id, candidate_name, candidate_email,
            resume_path, cover_letter, status, created_at,
            relevant_experience, overall_experience, current_location,
            preferred_location, current_ctc, expected_ctc,
            current_company, notice_period
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, 'pending', %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ''', (
        app_id, job_id, candidate_id, candidate_name, candidate_email, 
        resume_path, cover_letter, created_at,
        relevant_experience, overall_experience, current_location,
        preferred_location, current_ctc, expected_ctc,
        current_company, notice_period
    ))

    conn.commit()
    conn.close()

    return {
        'id': app_id,
        'job_id': job_id,
        'candidate_id': candidate_id,
        'candidate_name': candidate_name,
        'candidate_email': candidate_email,
        'resume_path': resume_path,
        'cover_letter': cover_letter,
        'status': 'pending',
        'created_at': created_at,
        'relevant_experience': relevant_experience,
        'overall_experience': overall_experience,
        'current_location': current_location,
        'preferred_location': preferred_location,
        'current_ctc': current_ctc,
        'expected_ctc': expected_ctc,
        'current_company': current_company,
        'notice_period': notice_period
    }

def get_all_job_applications(job_id: Optional[str] = None) -> List[dict]:
    """Get all job applications, optionally filtered by job_id."""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    if job_id:
        cursor.execute("""
            SELECT ja.*, jp.title as job_title, jp.company_name
            FROM job_applications ja
            LEFT JOIN job_postings jp ON ja.job_id = jp.id
            WHERE ja.job_id = %s
            ORDER BY ja.created_at DESC
        """, (job_id,))
    else:
        cursor.execute("""
            SELECT ja.*, jp.title as job_title, jp.company_name
            FROM job_applications ja
            LEFT JOIN job_postings jp ON ja.job_id = jp.id
            ORDER BY ja.created_at DESC
        """)

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]

def get_job_applications_by_candidate(candidate_id: str) -> List[dict]:
    """Get all applications by a specific candidate."""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("""
        SELECT ja.*, jp.title as job_title, jp.company_name
        FROM job_applications ja
        LEFT JOIN job_postings jp ON ja.job_id = jp.id
        WHERE ja.candidate_id = %s
        ORDER BY ja.created_at DESC
    """, (candidate_id,))

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]

def get_job_application_by_id(app_id: str) -> Optional[dict]:
    """Get a specific job application by ID."""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("""
        SELECT ja.*, jp.title as job_title, jp.company_name
        FROM job_applications ja
        LEFT JOIN job_postings jp ON ja.job_id = jp.id
        WHERE ja.id = %s
    """, (app_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return dict(row)
    return None

def update_job_application_status(app_id: str, status: str) -> bool:
    """Update the status of a job application."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("UPDATE job_applications SET status = %s WHERE id = %s", (status, app_id))
    updated = cursor.rowcount > 0

    conn.commit()
    conn.close()
    return updated

def check_existing_application(job_id: str, candidate_id: str) -> bool:
    """Check if a candidate has already applied to a job."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id FROM job_applications
        WHERE job_id = %s AND candidate_id = %s
    """, (job_id, candidate_id))

    row = cursor.fetchone()
    conn.close()

    return row is not None

def get_job_application_stats() -> dict:
    """Get job application statistics."""
    conn = get_connection()
    cursor = conn.cursor()

    stats = {
        'total_applications': 0,
        'pending': 0,
        'reviewed': 0,
        'shortlisted': 0,
        'rejected': 0,
        'hired': 0,
        'total_jobs': 0,
        'active_jobs': 0
    }

    # Application stats
    cursor.execute("SELECT COUNT(*) FROM job_applications")
    row = cursor.fetchone()
    if row:
        stats['total_applications'] = row[0] or 0

    cursor.execute("SELECT status, COUNT(*) FROM job_applications GROUP BY status")
    rows = cursor.fetchall()
    for status, count in rows:
        if status in stats:
            stats[status] = count

    # Job posting stats
    cursor.execute("SELECT COUNT(*) FROM job_postings")
    row = cursor.fetchone()
    if row:
        stats['total_jobs'] = row[0] or 0

    cursor.execute("SELECT COUNT(*) FROM job_postings WHERE status = 'active'")
    row = cursor.fetchone()
    if row:
        stats['active_jobs'] = row[0] or 0

    conn.close()
    return stats

# Initialize the database when this module is imported
init_db()
