import os
from dotenv import load_dotenv

load_dotenv()

# The API key for the Gemini model, loaded by litellm
API_KEY = os.getenv("GOOGLE_API_KEY")

# The absolute path to the vault directory
VAULT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'vault'))

# --- CORRECTED MODEL NAMES ---
GEMINI_PRO_MODEL = "gemini/gemini-2.5-pro" # The primary reasoning model
GEMINI_FLASH_MODEL = "gemini/gemini-2.5-flash-preview-04-17" # For faster, less critical tasks

if not API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in .env file. Please add it.")