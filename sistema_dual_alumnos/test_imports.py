import sys
import os

# Get path to 'SISTEMA DUAL FINAL'
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root_dir)

try:
    from sistema_dual.src.utils.anexo_data import get_anexo_5_4_data
    from sistema_dual.src.utils.pdf_generator_docx import generate_pdf_from_docx
    from sistema_dual.src.utils.notifications import send_email
    print("SUCCESS")
except ImportError as e:
    print(f"FAILED: {e}")
