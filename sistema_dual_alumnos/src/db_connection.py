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
    url = st.secrets.get("SUPABASE_URL") if "SUPABASE_URL" in st.secrets else os.environ.get("SUPABASE_URL")
    key = st.secrets.get("SUPABASE_KEY") if "SUPABASE_KEY" in st.secrets else os.environ.get("SUPABASE_KEY")

    if not url or not key:
        st.error("Supabase credentials not found. Please set SUPABASE_URL and SUPABASE_KEY in .env or Streamlit Secrets.")
        st.stop()

    return create_client(url, key)
