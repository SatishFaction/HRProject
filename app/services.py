import json
from fastapi import HTTPException
from mistralai import Mistral
from langchain_openai import AzureChatOpenAI

from .config import settings
from .utils import encode_pdf_from_bytes, extract_text_from_docx
from .models import JobRoleInput

# Initialize clients once and reuse them
mistral_client = Mistral(api_key=settings.MISTRAL_API_KEY)
llm_client = AzureChatOpenAI(
    azure_endpoint=settings.AZURE_ENDPOINT,
    api_key=settings.AZURE_API_KEY,
    api_version=settings.AZURE_API_VERSION,
    azure_deployment=settings.AZURE_DEPLOYMENT,
    model=settings.AZURE_MODEL,
    temperature=0.7,
    max_tokens=1000
)

def extract_resume_text(file_bytes: bytes, file_type: str) -> str:
    """
    Extracts text from resume bytes using the appropriate service (OCR for PDF, text extraction for DOCX).
    """
    print(f"DEBUG: Attempting to extract text from a file of type: {file_type}")

    if file_type == "pdf":
        base64_pdf = encode_pdf_from_bytes(file_bytes)
        try:
            print("DEBUG: Sending PDF to Mistral OCR API...")
            pdf_response = mistral_client.ocr.process(
                model="mistral-ocr-latest",
                document={
                    "type": "document_url",
                    "document_url": f"data:application/pdf;base64,{base64_pdf}"
                }
            )
            response_dict = json.loads(pdf_response.model_dump_json())

            # --- CRUCIAL DEBUGGING STEP ---
            # Print the full response from the OCR API to see what it contains
            print("\n--- DEBUG: Full Mistral OCR API Response ---")
            print(json.dumps(response_dict, indent=2))
            print("------------------------------------------\n")

            extracted_text = " ".join(page.get('markdown', '') for page in response_dict.get('pages', []))
            
            print(f"DEBUG: Extracted {len(extracted_text)} characters from PDF.")
            if not extracted_text.strip():
                print("DEBUG: Warning - Extracted text is empty or only whitespace.")
            
            return extracted_text

        except Exception as e:
            # Log the actual error from the Mistral client
            print(f"ERROR: An unexpected error occurred during OCR processing: {e}")
            raise HTTPException(status_code=500, detail=f"OCR processing failed: {e}")

    elif file_type == "docx":
        print("DEBUG: Extracting text from DOCX file...")
        extracted_text = extract_text_from_docx(file_bytes)
        print(f"DEBUG: Extracted {len(extracted_text)} characters from DOCX.")
        if not extracted_text.strip():
            print("DEBUG: Warning - Extracted text is empty or only whitespace.")
        return extracted_text
        
    print("DEBUG: Warning - File type was not 'pdf' or 'docx', returning empty string.")
    return ""

def get_llm_score(resume_text: str, job_description: str) -> dict:
    """
    Gets a score and explanation from the LLM based on the resume and job description.
    """
    prompt = f"""
    You are an expert HR analyst. Your task is to evaluate a candidate's resume against a specific job description.
    Provide a score from 0 to 100, where 100 represents a perfect match.
    Also, provide a detailed explanation for your score, highlighting the candidate's strengths and weaknesses based *only* on the information in the resume and the requirements in the job description.

    **Job Description:**
    ---
    {job_description}
    ---

    **Candidate's Resume:**
    ---
    {resume_text}
    ---

    **Output Format:**
    Please return a single JSON object with two keys: "score" (a float) and "explanation" (a string).
    Example: {{"score": 85.5, "explanation": "The candidate is a strong fit because..."}}
    """
    try:
        llm_output = llm_client.invoke(prompt)
        return json.loads(llm_output.content)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="LLM returned a non-JSON response.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred with the LLM: {e}")

def generate_jd_from_llm(job_details: JobRoleInput) -> str:
    """
    Generates a job description using the LLM based on user-provided details.
    """
    responsibilities_list = "\n- ".join(job_details.key_responsibilities.replace(";", ",").split(","))
    skills_list = "\n- ".join(job_details.required_skills.replace(";", ",").split(","))

    prompt = f"""
    You are a professional HR copywriter. Your task is to create a comprehensive and engaging job description based on the following details.
    The tone should be professional but inviting. Structure the output with clear sections like "About Us", "Position Summary", "Key Responsibilities", "Qualifications", and "Benefits" (you can create a generic but appealing benefits section).

    **Job Title:** {job_details.job_title}
    **Company Name:** {job_details.company_name}
    **Location:** {job_details.location}
    **Experience Level:** {job_details.experience_level}

    **Key Responsibilities to include:**
    - {responsibilities_list}

    **Required Skills and Qualifications:**
    - {skills_list}

    **Additional Details from user:**
    {job_details.extra_details if job_details.extra_details else "N/A"}

    Please generate the full, well-formatted job description now.
    """
    try:
        llm_output = llm_client.invoke(prompt)
        return llm_output.content
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred while generating the job description with the LLM: {e}")