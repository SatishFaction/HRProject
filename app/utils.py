# app/utils.py
import base64
import io
import docx
from fastapi import UploadFile, HTTPException

def encode_pdf_from_bytes(pdf_bytes: bytes) -> str:
    """Encode PDF bytes to a base64 string."""
    return base64.b64encode(pdf_bytes).decode('utf-8')

def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extracts text from a .docx file's bytes."""
    try:
        document = docx.Document(io.BytesIO(file_bytes))
        return "\n".join([paragraph.text for paragraph in document.paragraphs])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing DOCX file: {e}")

def get_text_from_resume(resume_file: UploadFile) -> tuple[bytes, str]:
    """
    Reads the uploaded file and determines its type.
    Returns the file content as bytes and the file extension.
    """
    file_bytes = resume_file.file.read()
    filename = resume_file.filename

    if filename.endswith(".pdf"):
        return file_bytes, "pdf"
    elif filename.endswith(".docx"):
        return file_bytes, "docx"
    else:
        raise HTTPException(status_code=400, detail="Unsupported file format. Please upload a .pdf or .docx file.")