# app/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Manages application settings and API keys.
    Loads variables from a .env file or environment variables.
    """
    MISTRAL_API_KEY: str = ""
    AZURE_ENDPOINT: str = ""
    AZURE_API_KEY: str = ""
    AZURE_API_VERSION: str = "2025-01-01-preview"
    AZURE_DEPLOYMENT: str = "gpt-4.1"
    AZURE_MODEL: str = "gpt-4.1"

    # OpenAI API Key for Interview Chatbot
    OPENAI_API_KEY: str = ""
    
    # Resend API Key (Deprecated/Optional if using SMTP)
    RESEND_API_KEY: str = ""

    # SMTP Email Settings
    EMAIL_SENDER: str = ""
    EMAIL_PASSWORD: str = ""

    # Azure Blob Storage Settings
    AZURE_STORAGE_CONNECTION_STRING: str = ""
    AZURE_CONTAINER_NAME: str = "resumes"

    # PostgreSQL Database URL (Neon)
    DATABASE_URL: str = ""

    # This tells Pydantic to load settings from a .env file
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding='utf-8', extra='ignore')

# Create a single instance of the settings to be used across the application
settings = Settings()


