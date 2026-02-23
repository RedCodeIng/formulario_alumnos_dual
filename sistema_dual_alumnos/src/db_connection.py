import os
import streamlit as st
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@st.cache_resource
def get_supabase_client() -> Client:
    """
    Returns a cached Supabase client instance.
    """
    # Try obtaining from st.secrets first (Cloud), then os.environ (Local)
    url = None
    key = None
    
    try:
        # Check if secrets property is available and has keys
        # Accessing st.secrets might throw FileNotFoundError if no secrets.toml exists
        if hasattr(st, "secrets") and st.secrets:
             if "SUPABASE_URL" in st.secrets:
                url = st.secrets["SUPABASE_URL"]
             if "SUPABASE_KEY" in st.secrets:
                key = st.secrets["SUPABASE_KEY"]
    except (FileNotFoundError, Exception):
        pass # Fallback to env

    if not url:
        url = os.environ.get("SUPABASE_URL")
    if not key:
        key = os.environ.get("SUPABASE_KEY")

    if not url or not key:
        st.error("Supabase credentials not found. Please set SUPABASE_URL and SUPABASE_KEY in .env or Streamlit Secrets.")
        st.stop()

    return create_client(url, key)
