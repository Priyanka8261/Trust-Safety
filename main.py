# at top of main.py (after imports)
import os
import streamlit as st
from pathlib import Path

try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None

# load .env only when available (local dev), prefer st.secrets on Streamlit Cloud
env_file = Path.cwd() / ".env"
if env_file.exists() and load_dotenv is not None:
    load_dotenv(dotenv_path=str(env_file), override=True)

# Prefer st.secrets when reading the OPENAI key later:
OPENAI_KEY = st.secrets.get("OPENAI_API_KEY") if hasattr(st, "secrets") and "OPENAI_API_KEY" in st.secrets else os.getenv("OPENAI_API_KEY")
