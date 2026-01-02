"""
SQLite Database module for user authentication.
"""
import sqlite3
from datetime import datetime
from typing import Optional, List
import hashlib
import secrets
import os

# Database file path (in the app directory)
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'talentflow.db')

def get_connection():
    """Get a database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Enable dict-like access
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
            created_at TEXT NOT NULL
        )
    ''')
    
    # Migration: Add resume_path column if it doesn't exist
    try:
        cursor.execute("ALTER TABLE applications ADD COLUMN resume_path TEXT")
    except sqlite3.OperationalError:
        pass # Column already exists
    
    conn.commit()
    conn.close()
    print(f"Database initialized at: {DB_PATH}")

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
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
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
    conn.close()
    return row

def update_application_status(app_id: str, status: str) -> bool:
    """Update the status of an application."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("UPDATE applications SET status = ? WHERE id = ?", (status, app_id))
    updated = cursor.rowcount > 0
    
    conn.commit()
    conn.close()
    return updated

def get_all_applications() -> List[dict]:
    """Get all applications/scored resumes."""
    conn = get_connection()
    cursor = conn.cursor()
    
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
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
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
    except sqlite3.IntegrityError:
        # Email already exists
        return None
    finally:
        conn.close()

def get_user_by_email(email: str) -> Optional[dict]:
    """Get a user by their email address."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM users WHERE email = ?', (email.lower(),))
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
    cursor = conn.cursor()
    
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
        VALUES (?, ?, ?)
    ''', (token, user_email.lower(), created_at))
    
    conn.commit()
    conn.close()
    
    return token

def get_user_by_token(token: str) -> Optional[dict]:
    """Get a user by their session token."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT u.id, u.email, u.full_name, u.role, u.phone, u.resume_url, u.created_at
        FROM tokens t
        JOIN users u ON t.user_email = u.email
        WHERE t.token = ?
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
    
    cursor.execute('DELETE FROM tokens WHERE token = ?', (token,))
    deleted = cursor.rowcount > 0
    
    conn.commit()
    conn.close()
    
    return deleted

# Initialize the database when this module is imported
init_db()
