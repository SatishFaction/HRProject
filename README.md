# TalentFlow AI - Intelligent HR Platform

TalentFlow AI is a cutting-edge Human Resource Management (HRM) platform designed to streamline the recruitment process using Artificial Intelligence. It connects HR professionals and candidates through a modern, responsive interface, offering advanced features like AI-powered resume scoring, automated job description generation, and real-time voice interviews.

## 🚀 Features

### For HR Professionals
*   **AI Resume Scoring**: Instantly score candidate resumes against job descriptions with detailed match explanations.
*   **Smart JD Generator**: Generate professional, detailed job descriptions from simple role inputs using AI.
*   **Job Management**: Create, update, and manage job postings with ease.
*   **Application Tracking**: Review candidate applications, update statuses (Reviewed, Shortlisted, Rejected, Hired), and manage the hiring pipeline.
*   **Candidate Database**: Access a centralized database of all candidates and their application history.
*   **Dashboard**: Get a bird's-eye view of recruitment stats and recent activities.

### For Candidates
*   **Job Discovery**: Browse and search for active job openings.
*   **Easy Application**: Apply to jobs with a comprehensive profile builder (Experience, CTC, Location, etc.) and resume upload.
*   **Application Tracking**: Monitor the status of all submitted applications in real-time.
*   **AI Voice Interview**: Participate in automated, real-time voice interviews to showcase soft skills and technical knowledge.

## 🛠️ Technology Stack

*   **Frontend**: 
    *   React 18 (Embedded)
    *   Modern CSS3 (Glassmorphism, Gradients, Animations)
    *   Babel (for runtime JSX compilation)
    *   Lucide React (Icons)
*   **Backend**: 
    *   Python 3.x
    *   FastAPI (High-performance web framework)
    *   SQLite (Lightweight database)
*   **AI & ML**:
    *   OpenAI API (GPT-4 for text processing)
    *   OpenAI Realtime API (for Voice Agent)
    *   PDF/DOCX Parsing (for Resume analysis)

## 📋 Prerequisites

*   Python 3.8 or higher
*   An OpenAI API Key (for AI features)

## ⚡ Installation & Setup

1.  **Clone the Repository**
    ```bash
    git clone <repository-url>
    cd HRProject
    ```

2.  **Create a Virtual Environment**
    ```bash
    python -m venv venv
    
    # Windows
    venv\Scripts\activate
    
    # macOS/Linux
    source venv/bin/activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Environment Configuration**
    Create a `.env` file in the root directory and add your API keys:
    ```env
    OPENAI_API_KEY=your_openai_api_key_here
    ```

## 🏃‍♂️ Running the Application

Start the backend server:

```bash
python -m uvicorn app.main:app --reload
```

The application will be available at:
*   **Frontend**: [http://localhost:8000/frontend/index.html](http://localhost:8000/frontend/index.html)
*   **API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)

## 📂 Project Structure

```
HRProject/
├── app/
│   ├── main.py          # Application entry point & API endpoints
│   ├── models.py        # Pydantic models & Database schema
│   ├── database.py      # Database connection & CRUD operations
│   ├── services.py      # Business logic (AI scoring, JD generation)
│   ├── chat_service.py  # Voice interview logic
│   └── utils.py         # Utility functions (File parsing, etc.)
├── frontend/
│   └── index.html       # Main React application
├── uploads/             # Directory for stored resumes
├── requirements.txt     # Python dependencies
└── README.md            # Project documentation
```

## 🔐 Authentication

The platform supports two distinct roles:
1.  **HR**: Access to all management tools.
2.  **Candidate**: Access to job board and personal application history.

You can register a new account on the login page by selecting your desired role.
