"""
OpenAI Realtime Voice API Service.
Handles ephemeral token generation for secure client-side connections.
"""
import httpx
from .config import settings

# System prompt for the AI voice interviewer
INTERVIEW_INSTRUCTIONS = """You are an AI interviewer for TalentFlow, a professional HR platform. Your role is to conduct initial screening interviews with job candidates through voice conversation.

Your interview style should be:
- Professional but warm and welcoming
- Speak naturally and conversationally
- Ask one question at a time
- Listen carefully to responses and ask follow-up questions when appropriate
- Keep responses concise (2-3 sentences)
- Cover key areas: background, experience, skills, motivation, and career goals

Interview Flow:
1. Welcome the candidate warmly and ask them to introduce themselves
2. Ask about their relevant work experience
3. Inquire about their key skills and strengths
4. Ask about their interest in the role/company
5. Discuss their career goals
6. Ask if they have any questions
7. Thank them and explain that HR will follow up

Remember:
- Be encouraging and supportive
- If a candidate seems nervous, help them feel at ease
- Ask behavioral questions (e.g., "Tell me about a time when...")
- Don't ask multiple questions at once
- Acknowledge their responses before moving to the next question
- Speak at a moderate pace for clarity"""

async def get_ephemeral_token(candidate_name: str = "Candidate") -> dict:
    """
    Generate an ephemeral token for the OpenAI Realtime API.
    This allows secure client-side connections without exposing the API key.
    
    Args:
        candidate_name: Name of the candidate for personalization
        
    Returns:
        dict with client_secret token and other session info
    """
    if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "your-openai-api-key-here":
        raise ValueError("OpenAI API key not configured. Please add OPENAI_API_KEY to your .env file.")
    
    # Personalize the instructions with candidate name
    instructions = INTERVIEW_INSTRUCTIONS + f"\n\nThe candidate's name is {candidate_name}. Address them by name occasionally."
    
    async with httpx.AsyncClient() as client:
        print(f"Requesting ephemeral token with Key starting: {settings.OPENAI_API_KEY[:8]}...")
        try:
            response = await client.post(
                "https://api.openai.com/v1/realtime/sessions",
                headers={
                    "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "gpt-4o-realtime-preview-2024-12-17",
                    "voice": "alloy",
                    "instructions": instructions,
                },
                timeout=30.0
            )
            
            if response.status_code != 200:
                print(f"OpenAI Error ({response.status_code}): {response.text}")
                raise Exception(f"Failed to get ephemeral token (Status {response.status_code}): {response.text}")
            
            return response.json()
        except Exception as e:
            print(f"OpenAI Connection Exception: {e}")
            raise
