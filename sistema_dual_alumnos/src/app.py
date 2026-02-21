
import streamlit as st
import sys
import os

# Fix for Streamlit Cloud path resolution
# Adds the parent directory of 'src' to sys.path so 'src.views' can be imported
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
from src.views.auth import render_login
from src.views.dashboard import render_dashboard
from src.views.student_dashboard import render_student_dashboard
from src.views.registro import render_registro
from src.views.mentor_dashboard import render_mentor_dashboard
from src.utils.ui import inject_custom_css, render_header

# Page Configuration (Must be first)
st.set_page_config(
    page_title="Sistema de Gestión DUAL",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': "Sistema de Gestión DUAL - EdoMex"
    }
)

def main():
    # 1. Inject Global CSS
    inject_custom_css()
    
    # 2. Render Header (Base64 Logos)
    # Only show header if logged in OR we can show it always. 
    # Usually better to show it always for branding.
    if "user" in st.session_state:
        render_header() 

    # 3. Routing
    if "user" not in st.session_state:
        # Login view handles its own specific styles if needed, or inherits global
        render_login()
    else:
        role = st.session_state.get("role")
        
        if role == "coordinator":
            render_dashboard()
        elif role == "student":
            render_student_dashboard()
        elif role == "student_register":
            render_registro()
        elif role == "mentor_ue":
            render_mentor_dashboard()
        else:
            st.error("Rol desconocido. Contacte al administrador.")

        # Logout Button (Optional placement in sidebar or main)
        with st.sidebar:
            st.write(f"Usuario: {st.session_state.get('user', {}).get('nombre_completo', 'Usuario')}")
            if st.button("Cerrar Sesión"):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()

if __name__ == "__main__":
    main()
