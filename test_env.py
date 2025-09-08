import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent
ENV_PATH = BASE_DIR / ".env"
load_dotenv(dotenv_path=ENV_PATH, override=True)

print("Arquivo .env lido de:", ENV_PATH.resolve())
print("DB_USER =", os.getenv("DB_USER"))
print("DB_PASS =", os.getenv("DB_PASS"))
