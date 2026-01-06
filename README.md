# TalentFlow AI - Intelligent HR Platform

TalentFlow AI is a comprehensive Human Resource Management (HRM) platform designed to modernize the recruitment lifecycle. By leveraging Artificial Intelligence, it streamlines complex tasks for HR professionals while providing a seamless, engaging experience for candidates.

From AI-powered resume scoring and automated job description generation to real-time voice interviews and bulk candidate communication, TalentFlow AI covers the entire hiring pipeline.

## 🚀 Features

### For HR Professionals

*   **📊 Smart Dashboard**: A centralized hub to view recruitment statistics, recent activities, and pipeline health at a glance.
*   **🧠 AI Resume Scoring**:
    *   **Single File**: Instantly score a candidate's resume against a job description with detailed match analysis and skill gap identification.
    *   **Batch Processing**: Upload and score multiple resumes simultaneously to quickly filter the best candidates.
*   **📝 Job Management**:
    *   **Job Creation**: Manually create job postings or use the **AI JD Generator** to draft professional descriptions from simple inputs.
    *   **Pipeline Management**: Track job statuses (Active, Closed, Draft) and manage the lifecycle of each opening.
*   **📧 Bulk Communication**: Send personalized email updates to multiple candidates at once using integrated SMTP support (e.g., for interview invites or rejection notices).
*   **👥 Candidate Management**:
    *   View all candidates and their application history.
    *   Update application statuses (Pending, Reviewed, Shortlisted, Rejected, Hired) with ease.

### For Candidates

*   **🔍 Job Discovery**: Browse active job openings with advanced filtering constraints.
*   **📄 Comprehensive Application**: 
    *   Easy-to-use application form capturing key details (Experience, CTC, Location, Notice Period, etc.).
    *   Resume upload (PDF/DOCX) support.
*   **📌 Application Tracking**: Monitor the real-time status of all submitted applications from a personal dashboard.
*   **🎤 AI Voice Interview**: Participate in automated, real-time voice interviews powered by OpenAI to showcase soft skills and technical expertise before the human round.

## 🛠️ Technology Stack

*   **Frontend**: 
    *   React 18 (Embedded via CDN/Babel for simplicity)
    *   Tailwind CSS (inferred) / Modern Custom CSS (Glassmorphism, Animations)
    *   Lucide React (Icons)
*   **Backend**: 
    *   Python 3.x
    *   FastAPI (High-performance web framework)
    *   SQLite (Lightweight, serverless database)
*   **AI & ML Services**:
    *   **OpenAI GPT-4**: For resume analysis, match scoring, and JD generation.
    *   **OpenAI Realtime API**: For zero-latency voice interview agents.
*   **Infrastructure**:
    *   SMTP (Gmail/Outlook): For transactional and bulk emails.

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

*   **Python 3.8+**
*   **Git**
*   An **OpenAI API Key** (Required for AI features)
*   A **Gmail/SMTP App Password** (Required for sending emails)

## ⚡ Installation & Setup

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/your-repo/HRProject.git
    cd HRProject
    ```

2.  **Create a Virtual Environment**
    ```bash
    # Windows
    python -m venv venv
    venv\Scripts\activate

    # macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Environment Configuration**
    Create a `.env` file in the root directory and add your credentials:
    ```env
    # AI Configuration
    OPENAI_API_KEY=sk-your-openai-api-key-here
    
    # Email Configuration (for Bulk Email feature)
    EMAIL_SENDER=your-email@gmail.com
    EMAIL_PASSWORD=your-app-specific-password
    ```

## 🏃‍♂️ Running the Application

Start the backend server with hot-reload enabled:

```bash
python -m uvicorn app.main:app --reload
```

Once the server is running, access the application at:

*   **Web Interface**: [http://localhost:8000/frontend/index.html](http://localhost:8000/frontend/index.html)
*   **API Documentation (Swagger UI)**: [http://localhost:8000/docs](http://localhost:8000/docs)

## 📂 Project Structure

```
HRProject/
├── app/
│   ├── main.py          # Application entry point & API endpoints
│   ├── models.py        # Pydantic models & Database schema
│   ├── database.py      # Database connection & CRUD operations
│   ├── services.py      # Business logic (AI scoring, JD generation)
│   ├── chat_service.py  # Real-time Voice Interview logic
│   ├── email_service.py # SMTP Email handling
│   ├── config.py        # Environment variable management
│   └── utils.py         # Utility functions (File parsing, etc.)
├── frontend/
│   └── index.html       # Main React application (Single Page App)
├── uploads/             # Storage for uploaded resumes
├── requirements.txt     # Python dependencies
└── README.md            # Project documentation
```

## 🔐 Authentication & Roles

The platform provides a secure authentication system with role-based access control (RBAC):

1.  **HR Role**:
    *   Full access to the Dashboard, Candidate Database, Job Postings, and Bulk Email tools.
    *   Can score resumes and manage the hiring pipeline.

2.  **Candidate Role**:
    *   Access to the Job Board and "My Applications" tracking.
    *   Can take AI Voice Interviews.

*To get started, simply register a new account on the login page and select your desired role.*
