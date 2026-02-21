import streamlit as st

# MUST BE THE FIRST STREAMLIT COMMAND
st.set_page_config(
    page_title="Portal Alumnos DUAL",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': "Portal Alumnos DUAL - EdoMex"
    }
)

import sys
import os

# Add 'src' to python path to allow imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Import the main app function
from src.app import main

if __name__ == "__main__":
    main()
